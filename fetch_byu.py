#!/usr/bin/env python3
"""Refresh BYU Cougars football + men's basketball schedules into data/dashboard.json -> sports.byu.

Primary source (official): byucougars.com schedule pages, which are server-rendered, so the current season's
games can be read straight from the HTML (date/time with UTC offset, TBA flag, vs./at, opponent, exhibition
flag, location, TV link):
  https://byucougars.com/sports/football/schedule
  https://byucougars.com/sports/mens-basketball/schedule
Fallback: ESPN's public site API team schedule JSON (BYU = team 252), regular season + postseason:
  https://site.api.espn.com/apis/site/v2/sports/{football/college-football|basketball/mens-college-basketball}/teams/252/schedule
Nothing is invented: opponent, home/away, start time and TV come from the source. Games without a set time are
stored with start=null (shown as TBA); "TV (TBA)" or no TV link is stored as tv=null.

Fail soft: for each sport the official page is tried first, then ESPN; if both fail (or return no games) the
previous games for that sport are kept and the script exits 2 (run.sh carries on and still builds).

Usage: python3 fetch_byu.py [--json data/dashboard.json] [--today YYYY-MM-DD] [--dry-run] [--source official|espn]
ESPN details: TBA games (timeValid=false) are stored on their Eastern-time calendar date (ESPN's midnight-ET
placeholder). Seasons for ESPN: football = the fall's calendar year; basketball = the year the season ends
(Oct 2026 -> 2027, the 2026-27 season).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
DEN, NYC, UTC = ZoneInfo("America/Denver"), ZoneInfo("America/New_York"), dt.timezone.utc
TEAM = "252"
API = "https://site.api.espn.com/apis/site/v2/sports/{path}/teams/" + TEAM + "/schedule?season={season}&seasontype={st}"
SPORTS = {
    "football": {"path": "football/college-football", "label": "Football",
                 "official": "https://byucougars.com/sports/football/schedule"},
    "mbb": {"path": "basketball/mens-college-basketball", "label": "Men's basketball",
            "official": "https://byucougars.com/sports/mens-basketball/schedule"},
}
TV_RE = re.compile(r"^(ESPN(2|U|NEWS|\+)?|ABC|FOX|Fox|FS1|FS2|CBS|CBSSN|CBS Sports Network|NBC|NBCSN|Peacock|TNT|truTV|"
                   r"MW\+|Big 12 Now.*|BYUtv|ACC ?Network|ACCN|SEC ?Network|SECN|Big Ten Network|BTN|The CW|CW|Disney\+|"
                   r"Max|HBO Max|Paramount\+|Pac-12 Network|Prime Video|Netflix|TV \(TBA\))$")


def seasons(today: dt.date) -> dict[str, int]:
    return {"football": today.year if today.month >= 3 else today.year - 1,
            "mbb": today.year + 1 if today.month >= 7 else today.year}


def get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (family-dashboard; +github.com/mattski360/family-dashboard)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def get(url: str) -> dict:
    return json.loads(get_text(url))


def _txt(x: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def fetch_official(sport: str) -> list[dict]:
    """Parse the list view of the official schedule page (one <div class="schedule-event-item"> per game)."""
    page = ""
    for _ in range(3):                         # the site occasionally serves a stripped shell page; retry
        page = get_text(SPORTS[sport]["official"])
        if "schedule-event-item__opponent-name" in page:
            break
    page = page.split("<table")[0]             # the table view repeats every game
    out = []
    for b in re.split(r'<div class="schedule-event-item(?: item)?"', page)[1:]:
        tm = re.search(r'<time datetime="([^"]+)"', b)
        opp = re.search(r'schedule-event-item__opponent-name">(.*?)</strong>', b, re.S)
        if not tm or not opp:
            continue
        head = b[:800]
        when = dt.datetime.fromisoformat(tm.group(1).replace("Z", "+00:00")).astimezone(DEN)
        tba = "schedule-event-date--time-tba" in head
        venue = (re.search(r"schedule-event-date--venue-(\w+)", head) or [None, ""])[1]
        div = _txt((re.search(r'schedule-event-item__divider">(.*?)</strong>', b, re.S) or [None, ""])[1]).lower()
        ha = "neutral" if venue == "neutral" else ("away" if div.startswith("at") or venue == "away" else "home")
        links = [_txt(x) for x in re.findall(r'schedule-event-item-links__title">(.*?)</span>', b, re.S)]
        tv = [x for x in links if TV_RE.match(x) and x != "TV (TBA)"]
        loc = re.search(r'schedule-event-location">(.*?)</span>', b, re.S)
        res = re.search(r'schedule-event-item-result__wrapper[^>]*>(.*?)</div>', b, re.S)
        res_t = _txt(res.group(1)) if res else ""
        g = {"id": f"byu-{sport}-{when.date().isoformat()}-{re.sub(r'[^a-z0-9]+', '-', _txt(opp.group(1)).lower()).strip('-')}",
             "sport": sport, "date": when.date().isoformat(), "start": None if tba else when.strftime("%H:%M"),
             "opponent": _txt(opp.group(1)), "home_away": ha, "tv": tv[0] if tv else None, "tv_all": tv,
             "venue": _txt(loc.group(1)) if loc else None,
             "note": "Exhibition" if "schedule-event-item__exhibition" in b else None}
        mo = re.match(r"^([WLT])\s*(\d+\s*-\s*\d+)", res_t)
        if mo:
            g["result"] = f"{mo.group(1)} {mo.group(2).replace(' ', '')}"
        out.append(g)
    return sorted(out, key=lambda g: (g["date"], g["start"] or "99"))


def opp_name(team: dict) -> str:
    loc = team.get("location") or team.get("shortDisplayName") or team.get("displayName") or "TBD"
    return team.get("shortDisplayName") or loc if len(loc) > 14 else loc


def parse(sport: str, ev: dict, season_type: int) -> dict | None:
    comp = (ev.get("competitions") or [{}])[0]
    teams = comp.get("competitors") or []
    me = next((c for c in teams if (c.get("team") or {}).get("id") == TEAM), None)
    opp = next((c for c in teams if c is not me), None)
    if not me or not opp or not ev.get("date"):
        return None
    when = dt.datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(UTC)
    if comp.get("timeValid", True):
        loc = when.astimezone(DEN)
        date, start = loc.date().isoformat(), loc.strftime("%H:%M")
    else:                                   # TBA: ESPN parks it at midnight Eastern on the game's date
        date, start = when.astimezone(NYC).date().isoformat(), None
    ha = "neutral" if comp.get("neutralSite") else me.get("homeAway", "home")
    tv = [((b.get("media") or {}).get("shortName") or "").strip() for b in comp.get("broadcasts") or []]
    tv = [t for t in tv if t]
    stype = ((comp.get("status") or {}).get("type") or {})
    g = {"id": f"byu-{sport}-{ev.get('id')}", "sport": sport, "date": date, "start": start,
         "opponent": opp_name(opp.get("team") or {}), "home_away": ha, "tv": tv[0] if tv else None,
         "tv_all": tv, "venue": (comp.get("venue") or {}).get("fullName"),
         "note": ((comp.get("notes") or [{}])[0] or {}).get("headline"),
         "postseason": season_type == 3, "status": stype.get("name"), "espn_utc": ev["date"]}
    if stype.get("completed"):
        try:
            ms, os_ = float((me.get("score") or {}).get("value")), float((opp.get("score") or {}).get("value"))
            g["result"] = f'{"W" if ms > os_ else "L" if ms < os_ else "T"} {int(ms)}-{int(os_)}'
        except (TypeError, ValueError):
            pass
    return g


def fetch_espn(sport: str, season: int) -> list[dict]:
    games: dict[str, dict] = {}
    for st in (2, 3):
        url = API.format(path=SPORTS[sport]["path"], season=season, st=st)
        try:
            data = get(url)
        except Exception as e:  # noqa: BLE001
            if st == 2:
                raise
            print(f"[fetch_byu] {sport} postseason fetch failed ({e}); skipping postseason", file=sys.stderr)
            continue
        for ev in data.get("events") or []:
            g = parse(sport, ev, st)
            if g:
                games[g["id"]] = g
    return sorted(games.values(), key=lambda g: (g["date"], g["start"] or "99"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--today", help="pretend today is YYYY-MM-DD (picks the seasons)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--source", choices=["official", "espn"], help="force one source (default: official, then ESPN)")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(DEN).date()
    path = Path(a.json)
    data = json.loads(path.read_text())
    byu = (data.setdefault("sports", {})).setdefault("byu", {})
    old = byu.get("games") or []
    out, failed, seas = [], [], seasons(today)
    used = {}
    for sport, season in seas.items():
        games, errs = [], []
        tries = [("official", lambda: fetch_official(sport)), ("espn", lambda: fetch_espn(sport, season))]
        for name, fn in tries:
            if a.source and name != a.source:
                continue
            try:
                games = fn()
                if not games:
                    raise ValueError("no games found")
                used[sport] = name
                print(f"[fetch_byu] {sport}: {len(games)} games from {name}")
                break
            except Exception as e:  # noqa: BLE001
                errs.append(f"{name}: {e}")
                print(f"[fetch_byu] {sport}: {name} failed ({e})", file=sys.stderr)
        if games:
            out += games
        else:
            kept = [g for g in old if g.get("sport") == sport]
            print(f"[fetch_byu] {sport}: all sources failed; keeping {len(kept)} previous games", file=sys.stderr)
            out += kept
            failed.append(sport)
    out.sort(key=lambda g: (g["date"], g["start"] or "99"))
    if a.dry_run:
        for g in out:
            print(g["date"], g["start"] or "TBA ", g["sport"], g["home_away"], g["opponent"], g["tv"] or "", g.get("note") or "", g.get("result", ""))
        return 2 if failed else 0
    src = {"official": "byucougars.com schedule page", "espn": "ESPN site API team schedule (team 252)"}
    byu.update({"team": "BYU Cougars", "source": {k: src[v] for k, v in used.items()} or byu.get("source"),
                "seasons": {"football": str(seas["football"]), "mbb": f"{seas['mbb'] - 1}-{str(seas['mbb'])[2:]}"},
                "games": out})
    if len(failed) < len(SPORTS):
        byu["updated"] = dt.datetime.now(DEN).isoformat(timespec="seconds")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"[fetch_byu] stored {len(out)} BYU games")
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
