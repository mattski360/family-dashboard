#!/usr/bin/env python3
"""Best-effort FALLBACK parse of the ward site's youth activity lists ("<Month> Youth Activities" headings, or one
"Youth Activities" heading with a sub-heading per month)
(https://www.highland43.org/wardannouncements) into data/dashboard.json -> youth.activities.

* The ward Google Sheet (entered as source "sheet"/"manual") is the primary source. Site items are
  stored with source "site" and build.py only shows them on dates the sheet doesn't cover.
* Each successful run replaces the previous "site" items; "sheet"/"manual" items are never touched.
* If the page can't be fetched or nothing parses, the JSON is left unchanged and the script exits 2.

Usage: python3 fetch_youth.py [--json data/dashboard.json] [--today YYYY-MM-DD] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Denver")
HERE = Path(__file__).resolve().parent
URL = "https://www.highland43.org/wardannouncements"
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
FULL = ["January", "February", "March", "April", "May", "June", "July", "August",
        "September", "October", "November", "December"]
GROUPS = [   # checked in order; first match wins
    (r"\byw\b|young women|beehives?|mia maids?|laurels?", "yw"),
    (r"deacons?", "deacons"),
    (r"teachers?", "teachers"),
    (r"priests?", "priests"),
    (r"all\s*(ym|young men)|young men|\bym\b", "all_ym"),
    (r"youth", "all_youth"),
]
DATE_RE = re.compile(r"^(?P<mon>jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[a-z]*\.?\s+(?P<day>\d{1,2})"
                     r"(?:st|nd|rd|th)?\s*(?:\((?P<grp>[^)]*)\))?\s*:?\s*(?P<rest>.*)$", re.I)


def fetch(url: str, tries: int = 3) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (family-dashboard)"})
    for k in range(tries):   # the ward site occasionally drops the TLS connection; retry before giving up
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))
    raise RuntimeError("unreachable")


def to_lines(fragment: str) -> list[str]:
    fragment = re.sub(r"(?i)<br\s*/?>|</(p|li|h\d|div)>", "\n", fragment)
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment))
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]


def _group_one(label: str) -> str | None:
    for pat, code in GROUPS:
        if re.search(pat, label, re.I):
            return code
    return None


# a label naming several groups ("YW Sr. & Teachers", "Teachers & Priests") is filed under the one that involves our
# boys first, so a joint activity isn't dropped just because YW is named first
GROUP_PREF = ["teachers", "deacons", "all_ym", "all_youth", "priests", "yw"]


def group_of(label: str) -> str | None:
    if len(label) > 30:
        return None
    if re.search(r"\ball\s*groups\b", label, re.I):
        return "all_youth"
    codes = {c for c in (_group_one(x) for x in re.split(r"\s*(?:&|\band\b|,|/)\s*", label)) if c}
    if not codes:
        return None
    return min(codes, key=GROUP_PREF.index)


def split_group(text: str) -> tuple[str, str]:
    """'Deacons: Tour the MTC' -> ('deacons', 'Tour the MTC'); no prefix -> all_youth."""
    m = re.match(r"^([A-Za-z .&()/,]+?):\s*(.+)$", text)
    if m and group_of(m.group(1)):
        return group_of(m.group(1)), m.group(2).strip()
    return "all_youth", text.strip()


def year_for(month: int, today: dt.date) -> int:
    if month < today.month - 6:
        return today.year + 1
    if month > today.month + 6:
        return today.year - 1
    return today.year


def month_sections(page: str) -> list[tuple[str, str]]:
    """(month name, body html) for each month's youth-activity list. Two page layouts are understood:
    * one heading per month: "<h2>November Youth Activities</h2> ...list..."
    * one "<h2>Youth Activities</h2>" heading with a sub-heading per month: "<h3>November</h3> ...list..." (Oct 2026 layout)."""
    heads = []
    for m in re.finditer(r"(?is)<h([1-4])[^>]*>(.*?)</h\1>", page):
        t = to_lines(m.group(2))
        heads.append((int(m.group(1)), t[0] if t else "", m.start(), m.end()))
    out = []
    for k, (lvl, text, _s, end) in enumerate(heads):
        body_end = heads[k + 1][2] if k + 1 < len(heads) else len(page)
        hm = re.match(r"^(\w+)\s+youth activities", text, re.I)
        if hm and hm.group(1).lower() in [f.lower() for f in FULL]:
            out.append((hm.group(1), page[end:body_end]))
            continue
        if re.fullmatch(r"(?i)youth activities:?", text.strip()):
            for lvl2, text2, _s2, end2 in heads[k + 1:]:
                if lvl2 <= lvl:
                    break
                j = heads.index((lvl2, text2, _s2, end2))
                sub_end = heads[j + 1][2] if j + 1 < len(heads) else len(page)
                mm = re.fullmatch(r"(?i)(\w+):?", text2.strip())
                if mm and mm.group(1).lower() in [f.lower() for f in FULL]:
                    out.append((mm.group(1), page[end2:sub_end]))
    return out


AND_DATE_RE = re.compile(r"^(?:&|and)\s+(?P<mon>jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[a-z]*\.?\s+(?P<day>\d{1,2})"
                         r"(?:st|nd|rd|th)?\s*:?\s*(?P<rest>.*)$", re.I)


def parse(page: str, today: dt.date) -> list[dict]:
    wanted = {FULL[today.month - 1].lower(), FULL[today.month % 12].lower()}   # this month + next
    items: list[dict] = []
    for month, body in month_sections(page):
        if month.lower() not in wanted:
            continue
        cur: list[dt.date] = []
        cur_grp = None
        for line in to_lines(body):
            dm = DATE_RE.match(line)
            if dm:
                mon = MONTHS[dm.group("mon").lower()[:3]]
                cur = [dt.date(year_for(mon, today), mon, int(dm.group("day")))]
                cur_grp = group_of(dm.group("grp")) if dm.group("grp") else None
                rest = dm.group("rest").strip()
                am = AND_DATE_RE.match(rest)     # "December 24th & December 31st" -> both dates
                if am:
                    mon2 = MONTHS[am.group("mon").lower()[:3]]
                    cur.append(dt.date(year_for(mon2, today), mon2, int(am.group("day"))))
                    rest = am.group("rest").strip()
                if not rest:
                    continue
                line = rest
            if not cur:
                continue
            grp, title = split_group(line)
            if cur_grp and grp == "all_youth":
                grp = cur_grp
            none = bool(re.search(r"no activity|cancel", title, re.I))
            title = re.sub(r"\s*-\s*no activity", " \u2014 no activity", title, flags=re.I)
            title = re.sub(r"\s+sunday event$", "", title, flags=re.I)
            for d in cur:
                items.append({
                    "id": f"yth-site-{d:%Y%m%d}-{re.sub(r'[^a-z0-9]+', '-', (grp + '-' + title).lower()).strip('-')[:40]}",
                    "date": d.isoformat(), "title": title[:1].upper() + title[1:], "group": grp,
                    "kind": "none" if none else "activity", "source": "site",
                })
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--today")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(TZ).date()
    try:
        items = parse(fetch(URL), today)
    except Exception as exc:
        print(f"[fetch_youth] WARNING: could not load/parse ward page: {exc}; keeping existing data", file=sys.stderr)
        return 2
    # keep only groups that involve our boys (Luke = Teachers, Wyatt = Deacons)
    items = [it for it in items if it["group"] in ("all_youth", "all_ym", "deacons", "teachers")]
    if not items:
        print("[fetch_youth] WARNING: no youth activities parsed; keeping existing data", file=sys.stderr)
        return 2
    if args.dry_run:
        for it in items:
            print(it["date"], it["group"], it["kind"], "|", it["title"])
        return 0
    path = Path(args.json)
    data = json.loads(path.read_text())
    youth = data.setdefault("youth", {})
    kept = [a for a in youth.get("activities", []) if a.get("source") != "site"]
    youth["activities"] = sorted(kept + items, key=lambda a: (a["date"], a.get("start") or "", a["title"]))
    youth["site_synced"] = dt.datetime.now(TZ).isoformat(timespec="seconds")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"[fetch_youth] stored {len(items)} site items (fallback); kept {len(kept)} sheet/manual items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
