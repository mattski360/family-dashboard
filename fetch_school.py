#!/usr/bin/env python3
"""Pull American Heritage School (AHS) Veracross ICS feeds and merge the events
that matter for Luke (grade 9, High School) and Tanner (grade 5, Elementary)
into data/dashboard.json.

* No third-party dependencies (ICS is parsed by hand; time zones via zoneinfo).
* Every run replaces all events with source == "ahs_feed"; hand-entered events
  (family, canyon_grove, ahs_manual, ...) are never touched.
* If a feed can't be downloaded, existing feed events are kept and the script
  exits non-zero (run.sh still builds the page).

Usage: python3 fetch_school.py [--days 21] [--json data/dashboard.json] [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Denver")
HERE = Path(__file__).resolve().parent

FEEDS = {
    # no-school days, terms, grades posted, picture retakes ...
    "campus": "https://api.veracross.com/AHS/v2/events.ics?campus=1&event_types=5,146,171,190,169,4,5,6,90,91",
    # general ES / MS / HS calendar
    "general": "https://api.veracross.com/AHS/v2/events.ics?campus=1&event_types=8,147,159,167,155,129,152,153,157,188,181,183,149,164,161,198,205,206",
}

LUKE_GRADE, TANNER_GRADE = 9, 5

# --------------------------------------------------------------------------- ICS

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "jensen-family-dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def unescape(v: str) -> str:
    return (v.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
             .replace("\\;", ";").replace("\\\\", "\\")).strip()


def parse_dt(params: str, value: str):
    """Return (date, datetime|None) in America/Denver."""
    value = value.strip()
    if "VALUE=DATE" in params.upper() and "T" not in value:
        return dt.datetime.strptime(value[:8], "%Y%m%d").date(), None
    m = re.search(r"TZID=([^;:]+)", params)
    if value.endswith("Z"):
        t = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
    else:
        t = dt.datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
        t = t.replace(tzinfo=ZoneInfo(m.group(1)) if m else TZ)
    t = t.astimezone(TZ)
    return t.date(), t


def parse_ics(text: str) -> list[dict]:
    text = re.sub(r"\r?\n[ \t]", "", text.replace("\r\n", "\n"))  # unfold
    out = []
    for block in text.split("BEGIN:VEVENT")[1:]:
        block = block.split("END:VEVENT")[0]
        props: dict[str, tuple[str, str]] = {}
        for line in block.split("\n"):
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            name, _, params = key.partition(";")
            props.setdefault(name.upper(), (params, val))
        if "DTSTART" not in props:
            continue
        sd, st = parse_dt(*props["DTSTART"])
        ed, et = (None, None)
        if "DTEND" in props:
            ed, et = parse_dt(*props["DTEND"])
            if et is None:            # all-day DTEND is exclusive
                ed = ed - dt.timedelta(days=1)
        out.append({
            "uid": props.get("UID", ("", ""))[1],
            "summary": unescape(props.get("SUMMARY", ("", ""))[1]),
            "description": unescape(props.get("DESCRIPTION", ("", ""))[1]),
            "location": unescape(props.get("LOCATION", ("", ""))[1]),
            "date": sd, "start": st, "end_date": ed, "end": et,
        })
    return out

# ---------------------------------------------------------------- classification

SKIP_ALWAYS = re.compile(
    r"\bADM\b|\(AF\)|enrollment|open house|assessment day|faculty|facilities|piano|setup|set up|"
    r"rehears|practice|\bclub\b|book group|studio|boot camp|act prep|act registration|\bACT testing|psat|"
    r"\bAP\b.*exam|senior thesis|senior dinner|commenc|alumni|\bPSO\b|pizza|alternate location|"
    r"team dinner|appreciation|new teacher|training|focus group|pop up shop|uniform resale|"
    r"exp\.? learning$|space simulator|kinder|devo\.? practice|improv",
    re.I)

NO_SCHOOL = re.compile(r"no school|fall break|thanksgiving|christmas holiday|spring break|winter break|"
                       r"holiday break|labor day|good friday", re.I)
HALF_DAY = re.compile(r"half day|ends? (at )?12|end at 12|classes end at 12", re.I)


def grades_in(text: str) -> set[int] | None:
    """Grades mentioned in text (K = 0). None if the text names no grade."""
    t = text.replace("–", "-")
    found: set[int] = set()
    for a, b in re.findall(r"\b(K|\d{1,2})\s*-\s*(\d{1,2})\b", t):
        lo = 0 if a == "K" else int(a)
        found |= set(range(lo, int(b) + 1))
    for g in re.findall(r"\b(\d{1,2})(?:st|nd|rd|th)\b", t):
        found.add(int(g))
    m = re.search(r"grades? ((?:\d{1,2}(?:,|\s|and|&)*)+)", t, re.I)
    if m:
        found |= {int(x) for x in re.findall(r"\d{1,2}", m.group(1))}
    if re.search(r"\bfourth\b", t, re.I): found.add(4)
    if re.search(r"\bfifth\b", t, re.I): found.add(5)
    if re.search(r"\bninth\b", t, re.I): found.add(9)
    if re.search(r"kinder", t, re.I): found.add(0)
    return found or None


def audience(summary: str, feed: str) -> set[str]:
    s = summary.strip()
    s_low = s.lower()
    # grade bands inside a "No School K-8" phrase describe who is off, not who the event is for
    grades = grades_in(re.sub(r"no school\s*\(?\s*(K|\d{1,2})\s*-\s*\d{1,2}\)?", "", s, flags=re.I))
    who: set[str] = set()

    # Explicit grade-band no-school statements first ("No School K-5", "No School 9-12")
    for a, b in re.findall(r"no school\s*\(?\s*(K|\d{1,2})\s*-\s*(\d{1,2})", s, re.I):
        rng = set(range(0 if a == "K" else int(a), int(b) + 1))
        if LUKE_GRADE in rng: who.add("luke")
        if TANNER_GRADE in rng: who.add("tanner")

    if re.match(r"^(K-12|school ends 12pm \(K-12\)|no school,|no school \(K-12\))", s, re.I) or "k-12" in s_low:
        who |= {"luke", "tanner"}
    elif re.match(r"^(ES\b|K-5\b|elementary\b|\d(?:st|nd|rd|th) grade|4th & 5th)", s, re.I):
        if grades is None or TANNER_GRADE in grades:
            who.add("tanner")
    elif re.match(r"^(HS\b|HS:|high school\b|grades 9-12|grades 6-12|9-12)", s, re.I):
        if grades is None or LUKE_GRADE in grades or re.search(r"pre-act \(9\)", s, re.I):
            who.add("luke")
    elif feed == "campus" and grades is None:
        who |= {"luke", "tanner"}           # campus feed = school-wide calendar
    # "6-12 Teacher In-Service ... No School K-5" -> no school for everyone
    if re.search(r"6-12 (teacher )?in-service", s, re.I):
        who.add("luke")
    if re.search(r"parent (lecture|mtg|meeting|orientation|foundations)|parent's night", s, re.I):
        return {"parents"}
    if who and re.search(r"w/ parents|with parents|parent teacher|parent mtg|parent meeting|family", s, re.I):
        who.add("parents")
    return who


def clean_title(s: str) -> str:
    t = s.strip()
    t = re.sub(r"^(HS:|HS|ES|FA|K-12)\s+", "", t)
    t = re.sub(r"^(HS|ES)\s+", "", t)
    t = re.sub(r"\s*[-–]\s*(girls|boys)[^,]*senior night", "", t, flags=re.I)
    t = re.sub(r"\s*[-–]\s*cross country senior night", "", t, flags=re.I)
    t = re.sub(r"\s*\(optional\)", " (optional)", t, flags=re.I)
    t = re.sub(r"\s+-\s+", " \u2014 ", t)
    t = re.sub(r"\s{2,}", " ", t)
    fixes = [
        (r"^teacher in-service, no school$", "No school \u2014 teacher in-service"),
        (r"^fall break \u2014 no school$", "Fall break"),
        (r"^term (\d) ends$", r"Term \1 ends"),
        (r"^term (\d) begins$", r"Term \1 begins"),
        (r"^T(\d) grades posted to veracross$", r"Term \1 grades posted"),
        (r"^standardized testing: pre-act \(9\), act \(10-11\)$", "Pre-ACT (grade 9)"),
        (r"^spirit apparel (uniform|day)( day)?\s*\u2014\s*half day$", "Half day \u00b7 spirit apparel"),
        (r"^spirit apparel (uniform|unform|day)( day)?$", "Spirit apparel day"),
        (r"^picture retakes$", "Picture retakes"),
        (r"^no school$", "No school"),
        (r"^on monday/friday bell schedule$", "Monday/Friday bell schedule"),
        (r"^K-5 service day, ES spirit apparel day, school ends at 12pm$", "K-5 Service Day \u00b7 spirit apparel"),
        (r"^lunch on the lawn w/ parents \(optional\)$", "Lunch on the Lawn with parents (optional)"),
        (r"^K-5 half day \(school ends at 12pm\)$", "K-5 half day"),
        (r"^K-5 no school\. K-5 in-service day, no meetings\. teacher workday$", "No school \u2014 K-5 in-service"),
        (r"^K-5 gathering generations day/grandparents day$", "Grandparents Day (Gathering Generations)"),
        (r"^reading challenge \"?creature chronicles\"? closing assembly$", "Reading Challenge closing assembly"),
    ]
    for pat, rep in fixes:
        if re.match(pat, t, re.I):
            t = re.sub(pat, rep, t, flags=re.I)
            break
    return t[:1].upper() + t[1:]


def band_no_school(summary: str) -> set[str] | None:
    """Kids covered by an explicit grade-band no-school phrase ("No School K-5"), else None."""
    hits = re.findall(r"no school\s*\(?\s*(K|\d{1,2})\s*-\s*(\d{1,2})", summary, re.I)
    if not hits:
        return None
    kids: set[str] = set()
    for a, b in hits:
        rng = set(range(0 if a == "K" else int(a), int(b) + 1))
        if LUKE_GRADE in rng: kids.add("luke")
        if TANNER_GRADE in rng: kids.add("tanner")
    if re.search(r"\b(6|9|K)-12 (teacher )?in-service", summary, re.I):
        kids.add("luke")                     # a 6-12 in-service day means no HS classes either
    return kids


def classify(ev: dict, feed: str) -> list[dict]:
    """Return 0..2 dashboard items for one feed event (split when no-school applies to only some kids)."""
    s = ev["summary"]
    if not s or SKIP_ALWAYS.search(s) and not NO_SCHOOL.search(s):
        return []
    who = audience(s, feed)
    if not who:
        return []
    is_weekend = ev["date"].weekday() >= 5
    low = s.lower()
    if re.search(r"term \d (ends|begins)|terms? ends|grades posted|pre-act|grandparents|picture|parent teacher|"
                 r"conferences|service day|lunch on the lawn|school resumes|school begins|required", low):
        priority = "high"
    elif re.search(r"spirit apparel|bell schedule|schedule|assembly", low):
        priority = "low"
    else:
        priority = "normal"
    title = clean_title(s)
    if re.match(r"^spirit appa?rel", title, re.I) and not NO_SCHOOL.search(s) and not HALF_DAY.search(s):
        title = "Spirit apparel day"

    if NO_SCHOOL.search(s):
        if is_weekend:
            return []                       # "fall break" on a Saturday is noise
        band = band_no_school(s)
        if band is not None and band != who:
            items = []
            off = who & band
            on = who - band
            if off:
                items.append({"who": sorted(off), "flag": "no_school", "priority": "high", "title": "No school"})
            if on:
                rest = re.sub(r"[,\s\u2014-]*no school\s*\(?\s*(K|\d{1,2})\s*-\s*\d{1,2}\)?", "", s, flags=re.I)
                rest_title = clean_title(rest) if rest.strip() else "School day"
                if re.match(r"^spirit appa?rel", rest_title, re.I):
                    rest_title = "Spirit apparel day"
                items.append({"who": sorted(on), "flag": None, "priority": "low", "title": rest_title})
            return items
        return [{"who": sorted(who), "flag": "no_school", "priority": "high", "title": title}]
    flag = "half_day" if HALF_DAY.search(s) else None
    if flag:
        priority = "high"
    return [{"who": sorted(who), "flag": flag, "priority": priority, "title": title}]


def hm(t: dt.datetime | None) -> str | None:
    return t.strftime("%H:%M") if t else None


def build_events(raw: dict[str, list[dict]], start: dt.date, end: dt.date) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for feed, events in raw.items():
        for ev in events:
            if not (start <= ev["date"] <= end):
                continue
            for c in classify(ev, feed):
                add_item(merged, ev, c)
    return finalize(merged)


def add_item(merged: dict, ev: dict, c: dict) -> None:
    if True:
        if True:
            title = c["title"]
            key = (ev["date"].isoformat(), re.sub(r"\W+", "", title.lower()))
            st, en = hm(ev["start"]), hm(ev["end"])
            if st == "00:00" and en in (None, "00:00"):
                st = en = None
            item = {
                "id": f"ahs-{ev['date']:%Y%m%d}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]}",
                "date": ev["date"].isoformat(),
                "start": st, "end": en,
                "title": title,
                "note": "",   # feed locations are campus room numbers -- not useful on a family wall
                "who": c["who"], "flag": c["flag"], "priority": c["priority"],
                "kind": "school", "source": "ahs_feed",
            }
            if ev["end_date"] and ev["start"] is None and ev["end_date"] > ev["date"]:
                item["end_date"] = ev["end_date"].isoformat()
            if key in merged:  # duplicate (e.g. "copied from previous year") -> merge audiences
                old = merged[key]
                old["who"] = sorted(set(old["who"]) | set(item["who"]))
                old["start"] = old["start"] or item["start"]
                old["end"] = old["end"] or item["end"]
            else:
                merged[key] = item


def finalize(merged: dict) -> list[dict]:
    # Drop routine noise that duplicates a stronger same-day item
    out = list(merged.values())
    by_day: dict[str, list[dict]] = {}
    for e in out:
        by_day.setdefault(e["date"], []).append(e)
    final = []
    for day, items in by_day.items():
        no_school = {w for e in items if e["flag"] == "no_school" for w in e["who"]}
        for e in items:
            # On a no-school day for a kid, drop that kid's non-flag school items
            if e["flag"] != "no_school" and set(e["who"]) <= no_school and e["priority"] != "high":
                continue
            final.append(e)
    final.sort(key=lambda e: (e["date"], e["start"] or "", e["title"]))
    return final


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--days", type=int, default=21,
                    help="days ahead to import (default 21 so a weekly refresh still covers a 10-day view all week)")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD) for testing")
    ap.add_argument("--dry-run", action="store_true", help="print events, don't write JSON")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(TZ).date()
    start, end = today - dt.timedelta(days=1), today + dt.timedelta(days=args.days)

    raw, failed = {}, []
    for name, url in FEEDS.items():
        try:
            raw[name] = parse_ics(fetch(url))
            print(f"[fetch_school] {name}: {len(raw[name])} events in feed")
        except Exception as exc:  # network/parse problem -> keep old data
            failed.append(name)
            print(f"[fetch_school] WARNING: could not load {name} feed: {exc}", file=sys.stderr)
    if failed:
        print("[fetch_school] keeping existing school events; nothing written", file=sys.stderr)
        return 2

    events = build_events(raw, start, end)
    if args.dry_run:
        for e in events:
            print(e["date"], e.get("start") or "     ", e["flag"] or "", "/".join(e["who"]), "|", e["title"], f"[{e['priority']}]")
        return 0

    path = Path(args.json)
    data = json.loads(path.read_text())
    kept = [e for e in data.get("events", []) if e.get("source") != "ahs_feed"]
    data["events"] = sorted(kept + events, key=lambda e: (e["date"], e.get("start") or "", e["title"]))
    data.setdefault("meta", {})["school_feed_synced"] = dt.datetime.now(TZ).isoformat(timespec="seconds")
    data["meta"]["school_feed_window"] = [start.isoformat(), end.isoformat()]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"[fetch_school] wrote {len(events)} AHS events ({start} \u2192 {end}); kept {len(kept)} other events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
