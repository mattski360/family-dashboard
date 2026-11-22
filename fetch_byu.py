#!/usr/bin/env python3
"""Refresh BYU Cougars football + men's basketball schedules into data/dashboard.json -> sports.byu.

Primary source (official): byucougars.com schedule pages, which are server-rendered, so the current season's
games can be read straight from the HTML (date/time with UTC offset, TBA flag, vs./at, opponent, exhibition
flag, location, TV link):
  https://byucougars.com/sports/football/schedule
  https://byucougars.com/sports/mens-basketball/schedule
Fallback / results: ESPN's public site API team schedule JSON (BYU = team 252), regular season + postseason:
  https://site.api.espn.com/apis/site/v2/sports/{football/college-football|basketball/mens-college-basketball}/teams/252/schedule
Completed-game scores are always merged from ESPN when that API answers, even if the official page already
supplied the schedule (the official HTML can list a played game before the final is in the markup). A score is
kept only when ESPN marks the game final (status.type.completed / state=post) or, with no ESPN status, when
the official page has a result and the kickoff (America/Denver) is already in the past. Previous results are
kept only for those already-played games; a future or still-scheduled game never inherits a leftover score
(that is how a Baylor final was once copied onto the next game, Kansas). Nothing is invented: opponent,
home/away, start time and TV come from the source. Games without a set time are stored with start=null
(shown as TBA); "TV (TBA)" or no TV link is stored as tv=null.

Fail soft: for each sport the official page is tried first, then ESPN; if both fail (or return no games) the
previous games for that sport are kept and the script exits 2 (run.sh / build.py carry on and still build).
build.py calls refresh() on each normal build so midweek basketball finals and Tuesday CFP ranks are picked
up without waiting for the Saturday run.sh.

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


RANK_PREFIX = re.compile(r"^(?:No\.|#)\s*\d+\s+", re.I)


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
        name = RANK_PREFIX.sub("", _txt(opp.group(1)))   # "No. 17 Kansas" -> "Kansas" (the site's rank goes stale)
        g = {"id": f"byu-{sport}-{when.date().isoformat()}-{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')}",
             "sport": sport, "date": when.date().isoformat(), "start": None if tba else when.strftime("%H:%M"),
             "opponent": name, "home_away": ha, "tv": tv[0] if tv else None, "tv_all": tv,
             "venue": _txt(loc.group(1)) if loc else None,
             "note": "Exhibition" if "schedule-event-item__exhibition" in b else None}
        # Only this item's result section (not ads / "latest win" banners later in the card).
        chunk_m = re.search(r'schedule-event-item-result(?:\s|").*(?=schedule-event-item__dashboard|schedule-event-item-links|$)', b, re.S)
        chunk = chunk_m.group(0) if chunk_m else ""
        mo = re.search(r'schedule-event-item-result__(?:win|loss|tie)"[^>]*>\s*([WLT])\s*</strong>\s*(\d+\s*-\s*\d+)', chunk)
        if not mo:
            res = re.search(r'schedule-event-item-result__wrapper[^>]*>(.*?)</div>', chunk, re.S)
            res_t = _txt(res.group(1)) if res else ""
            mo = re.search(r'\b([WLT])\s*(\d+\s*-\s*\d+)', res_t)
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
    completed = bool(stype.get("completed")) or stype.get("state") == "post"
    g = {"id": f"byu-{sport}-{ev.get('id')}", "sport": sport, "date": date, "start": start,
         "opponent": opp_name(opp.get("team") or {}), "home_away": ha, "tv": tv[0] if tv else None,
         "tv_all": tv, "venue": (comp.get("venue") or {}).get("fullName"),
         "note": ((comp.get("notes") or [{}])[0] or {}).get("headline"),
         "postseason": season_type == 3, "status": stype.get("name"), "espn_utc": ev["date"],
         "espn_id": str(ev.get("id") or ""), "completed": completed}
    # Scores only for a true final — never treat pre/scheduled or a 0-0 placeholder as a result.
    if completed and stype.get("state") != "pre" and stype.get("name") not in ("STATUS_SCHEDULED", "STATUS_PRE"):
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


RANK_API = "https://site.api.espn.com/apis/site/v2/sports/{path}/rankings"
TEAM_API = "https://site.api.espn.com/apis/site/v2/sports/{path}/teams/" + TEAM


def fetch_polls(sport: str) -> list[dict]:
    """Current AP / Coaches / CFP polls from ESPN's rankings endpoint: [{poll, as_of, week, ranks:{team_id: (rank, names)}}]."""
    out = []
    for r in get(RANK_API.format(path=SPORTS[sport]["path"])).get("rankings") or []:
        nm = r.get("shortName") or r.get("name") or ""
        if not any(k in nm for k in ("AP", "Coaches", "Playoff", "CFP")) or "FCS" in nm or "Div" in nm:
            continue
        label = "CFP" if ("Playoff" in nm or "CFP" in nm) else ("AP" if "AP" in nm else "Coaches")
        ranks = {}
        for x in r.get("ranks") or []:
            t, cur = x.get("team") or {}, x.get("current")
            if t.get("id") and isinstance(cur, int) and 0 < cur <= 25:      # 0/99/missing = unranked
                names = {t.get(k, "").lower() for k in ("location", "nickname", "shortDisplayName", "displayName") if t.get(k)}
                ranks[t["id"]] = (cur, names)
        out.append({"poll": label, "as_of": (r.get("date") or "")[:10], "week": r.get("headline"), "ranks": ranks})
    return out


def fetch_summary(sport: str, polls: list[dict]) -> dict:
    """Record, conference standing and BYU's current poll ranks (omitted when unknown or unranked; never guessed)."""
    path = SPORTS[sport]["path"]
    out: dict = {}
    t = get(TEAM_API.format(path=path)).get("team") or {}
    for it in (t.get("record") or {}).get("items") or []:
        if it.get("type") == "total" and it.get("summary"):
            out["record"] = it["summary"]
            st = {x["name"]: x.get("value") for x in it.get("stats") or []}
            lw, ll = st.get("leagueWins"), st.get("leagueLosses")
            if lw is not None and ll is not None and (lw or ll):
                out["conf_record"] = f"{int(lw)}-{int(ll)}"
    if t.get("standingSummary"):
        out["standing"] = t["standingSummary"]
    poll_order = {"AP": 0, "Coaches": 1, "CFP": 2}
    out["polls"] = sorted(
        [{"poll": p["poll"], "rank": p["ranks"][TEAM][0], "as_of": p["as_of"], "week": p["week"]}
         for p in polls if TEAM in p["ranks"]],
        key=lambda p: poll_order.get(p["poll"], 9))
    # every poll that was checked, so the page can tell "unranked this week" from "not checked"
    out["polls_checked"] = [{"poll": p["poll"], "as_of": p["as_of"], "week": p["week"]} for p in polls]
    out["checked"] = dt.datetime.now(DEN).isoformat(timespec="seconds")
    return out


def tag_opp_ranks(games: list[dict], sport: str, polls: list[dict], today: dt.date) -> None:
    """Upcoming games get opp_rank = the opponent's CURRENT AP rank (CFP once it is out); played/unranked games get none."""
    poll = next((p for p in polls if p["poll"] == "CFP"), None) or next((p for p in polls if p["poll"] == "AP"), None)
    for g in games:
        if g.get("sport") != sport:
            continue
        g.pop("opp_rank", None)
        g.pop("opp_rank_poll", None)
        g["opponent"] = RANK_PREFIX.sub("", g.get("opponent") or "")
        if not poll or g.get("result") or g.get("date", "") < today.isoformat():
            continue
        o = g["opponent"].lower()
        hit = [rk for tid, (rk, names) in poll["ranks"].items() if tid != TEAM and o in names]
        if len(hit) == 1:
            g["opp_rank"], g["opp_rank_poll"] = hit[0], poll["poll"]


def _opp_tokens(name: str) -> set[str]:
    s = RANK_PREFIX.sub("", name or "")
    s = re.sub(r"[^a-z0-9\s]+", " ", s.lower())
    stop = {"university", "univ", "the", "college", "of", "at", "and"}
    return {t for t in s.split() if t and t not in stop and len(t) > 1}


def same_game(a: dict, b: dict) -> bool:
    """Same BYU game: ESPN event id when both have one, otherwise sport + date + opponent-token overlap."""
    if a.get("sport") != b.get("sport"):
        return False
    aid, bid = str(a.get("espn_id") or ""), str(b.get("espn_id") or "")
    if aid and bid:
        return aid == bid
    if a.get("date") != b.get("date"):
        return False
    ta, tb = _opp_tokens(a.get("opponent") or ""), _opp_tokens(b.get("opponent") or "")
    if not ta or not tb:
        return False  # never match on date alone (empty/TBD names are not a unique game)
    return bool(ta & tb)


def find_match(games: list[dict], g: dict) -> dict | None:
    hits = [x for x in games if x is not g and same_game(x, g)]
    return hits[0] if len(hits) == 1 else (hits[0] if hits else None)


def game_kickoff(g: dict) -> dt.datetime | None:
    """America/Denver kickoff, or None when the time is TBA."""
    try:
        day = dt.date.fromisoformat(g.get("date") or "")
    except ValueError:
        return None
    if not g.get("start"):
        return None
    h, m = map(int, g["start"].split(":"))
    return dt.datetime(day.year, day.month, day.day, h, m, tzinfo=DEN)


def game_is_future(g: dict, now: dt.datetime) -> bool:
    """True when this game has not started yet in America/Denver (TBA on today or later counts as future)."""
    kick = game_kickoff(g)
    if kick is not None:
        return kick > now
    try:
        day = dt.date.fromisoformat(g.get("date") or "")
    except ValueError:
        return False
    return day >= now.astimezone(DEN).date()


def espn_says_final(g: dict) -> bool | None:
    """True/False when ESPN status is known; None if this record has no ESPN status."""
    if g.get("completed") is True or g.get("status") == "STATUS_FINAL" or g.get("state") == "post":
        if g.get("status") in ("STATUS_SCHEDULED", "STATUS_PRE") or g.get("state") == "pre":
            return False
        return True
    if g.get("completed") is False or g.get("status") in ("STATUS_SCHEDULED", "STATUS_PRE") or g.get("state") == "pre":
        return False
    return None


def apply_results(dest: list[dict], src: list[dict], overwrite: bool = False, now: dt.datetime | None = None) -> int:
    """Copy finals (and missing TV/start) from src onto matching dest games. Never invents a score.
    If src is ESPN and the game is not final, any existing result on dest is cleared."""
    now = now or dt.datetime.now(DEN)
    n = 0
    for g in dest:
        s = find_match(src, g)
        if not s:
            continue
        if s.get("espn_id"):
            g["espn_id"] = s["espn_id"]
        if overwrite:                       # only fresh sources set status; stored (previous) data must not override it
            if s.get("status"):
                g["status"] = s["status"]
            if "completed" in s:
                g["completed"] = s["completed"]
        src_final = espn_says_final(s) if overwrite else None
        if src_final is False:
            if g.get("result"):
                print(f"[fetch_byu] {g.get('sport')} {g.get('date')} {g.get('opponent')}: "
                      f"dropping result {g['result']} (ESPN has not made this game final)", file=sys.stderr)
                g.pop("result", None)
                n += 1
        elif s.get("result") and src_final is not False and not game_is_future(s, now) and not game_is_future(g, now):
            if overwrite or not g.get("result"):
                if g.get("result") and g["result"] != s["result"]:
                    print(f"[fetch_byu] {g.get('sport')} {g.get('date')} {g.get('opponent')}: "
                          f"result {g['result']} -> {s['result']}", file=sys.stderr)
                g["result"] = s["result"]
                g["completed"] = True
                n += 1
        if not g.get("tv") and s.get("tv"):
            g["tv"], g["tv_all"] = s["tv"], s.get("tv_all") or [s["tv"]]
        if g.get("start") is None and s.get("start"):
            g["start"] = s["start"]
    return n


def add_missing(dest: list[dict], src: list[dict]) -> int:
    n = 0
    for g in src:
        if not find_match(dest, g):
            dest.append(g)
            n += 1
    return n


def drop_invalid_results(games: list[dict], now: dt.datetime | None = None) -> list[dict]:
    """Remove a result from any game that is still in the future or that ESPN says is not final.
    Returns the dropped records (for logging). Mutates games in place."""
    now = now or dt.datetime.now(DEN)
    dropped = []
    for g in games:
        if not g.get("result"):
            continue
        why = None
        if espn_says_final(g) is False:
            why = "ESPN status is not final"
        elif game_is_future(g, now):
            why = "game is still in the future"
        if why:
            dropped.append({**g, "_drop_reason": why})
            print(f"[fetch_byu] dropping result {g['result']} on {g.get('sport')} {g.get('date')} "
                  f"{g.get('opponent')} ({why})", file=sys.stderr)
            g.pop("result", None)
            g["completed"] = False
    return dropped


def collect_sport(sport: str, season: int, old: list[dict], source: str | None,
                  now: dt.datetime | None = None) -> tuple[list[dict], str | None, list[str]]:
    """Official schedule when possible, merge ESPN finals, never keep a score on a future game."""
    now = now or dt.datetime.now(DEN)
    official, espn, errs = None, None, []
    tries = [("official", lambda: fetch_official(sport)), ("espn", lambda: fetch_espn(sport, season))]
    for name, fn in tries:
        if source and name != source:
            continue
        try:
            games = fn()
            if not games:
                raise ValueError("no games found")
            if name == "official":
                official = games
            else:
                espn = games
            print(f"[fetch_byu] {sport}: {len(games)} games from {name}")
        except Exception as e:  # noqa: BLE001
            errs.append(f"{name}: {e}")
            print(f"[fetch_byu] {sport}: {name} failed ({e})", file=sys.stderr)
    prev = [g for g in old if g.get("sport") == sport]
    if official:
        games, used = official, "official"
        if espn:
            n = apply_results(games, espn, overwrite=True, now=now)
            add_missing(games, espn)
            if n or any(g.get("result") for g in espn):
                used = "official+espn"
            print(f"[fetch_byu] {sport}: merged {n} ESPN result(s) into official schedule")
    elif espn:
        games, used = espn, "espn"
    else:
        drop_invalid_results(prev, now)
        return prev, None, errs
    # Keep earlier finals only for games already played; never copy a score onto a future game.
    n = apply_results(games, prev, overwrite=False, now=now)
    extra = add_missing(games, [g for g in prev if g.get("note") == "Exhibition"
                                or (g.get("result") and not game_is_future(g, now))])
    if n or extra:
        print(f"[fetch_byu] {sport}: kept {n} previous result(s) and {extra} previous-only game(s)")
    drop_invalid_results(games, now)
    games.sort(key=lambda g: (g["date"], g["start"] or "99"))
    return games, used, errs


SRC_LABEL = {
    "official": "byucougars.com schedule page",
    "espn": "ESPN site API team schedule (team 252)",
    "official+espn": "byucougars.com schedule page, results from ESPN site API (team 252)",
}


def refresh(json_path: str | Path, today: dt.date | None = None, source: str | None = None,
            dry_run: bool = False) -> int:
    """Update sports.byu in dashboard.json. Returns 0, or 2 if a source failed and previous data was kept."""
    now = dt.datetime.now(DEN)
    today = today or now.date()
    path = Path(json_path)
    data = json.loads(path.read_text())
    byu = (data.setdefault("sports", {})).setdefault("byu", {})
    old = byu.get("games") or []
    out, failed, seas, used = [], [], seasons(today), {}
    for sport, season in seas.items():
        games, src, _errs = collect_sport(sport, season, old, source, now=now)
        if src:
            used[sport] = src
            out += games
        else:
            print(f"[fetch_byu] {sport}: all sources failed; keeping {len(games)} previous games", file=sys.stderr)
            out += games
            failed.append(sport)
    out.sort(key=lambda g: (g["date"], g["start"] or "99"))
    dropped = drop_invalid_results(out, now)
    if dropped:
        print(f"[fetch_byu] removed {len(dropped)} invalid future/non-final result(s)", file=sys.stderr)
    if dry_run:
        for g in out:
            print(g["date"], g["start"] or "TBA ", g["sport"], g["home_away"], g["opponent"],
                  g["tv"] or "", g.get("note") or "", g.get("result", ""))
        return 2 if failed else 0
    byu.update({"team": "BYU Cougars", "source": {k: SRC_LABEL[v] for k, v in used.items()} or byu.get("source"),
                "seasons": {"football": str(seas["football"]), "mbb": f"{seas['mbb'] - 1}-{str(seas['mbb'])[2:]}"},
                "games": out})
    summ = byu.get("summary") or {}
    for sp in SPORTS:
        try:
            polls = fetch_polls(sp)
            summ[sp] = fetch_summary(sp, polls)
            tag_opp_ranks(out, sp, polls, today)
            print(f"[fetch_byu] {sp}: record {summ[sp].get('record', '?')}, polls "
                  + (", ".join(f"#{p['rank']} {p['poll']} ({p['as_of']})" for p in summ[sp]["polls"]) or "unranked"))
        except Exception as e:  # noqa: BLE001  keep last good summary (build.py hides poll ranks once they are stale)
            print(f"[fetch_byu] {sp}: summary/poll fetch failed ({e}); keeping previous", file=sys.stderr)
            tag_opp_ranks(out, sp, [], today)
            failed.append(sp + "-polls")
    byu["summary"] = summ
    if len([f for f in failed if f in SPORTS]) < len(SPORTS):
        byu["updated"] = dt.datetime.now(DEN).isoformat(timespec="seconds")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"[fetch_byu] stored {len(out)} BYU games")
    return 2 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--today", help="pretend today is YYYY-MM-DD (picks the seasons)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--source", choices=["official", "espn"], help="force one source (default: official + ESPN results)")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else None
    return refresh(a.json, today=today, source=a.source, dry_run=a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
