#!/usr/bin/env python3
"""Render v3/index.html (self-contained: inline CSS/JS, no external requests) from data/dashboard.json.

The weekly calendar is a fixed Sunday-Saturday week starting at meta.week_start. The page is rebuilt
Saturday night for the following week. By default week_start is the upcoming Sunday (or today if
today is Sunday); --week-start overrides it and the value used is written back to meta.week_start.
When the page is viewed before week_start, a small "Rest of this week" strip shows the remaining days.
The inline script highlights today and dims past days based on the viewing date (America/Denver).

Template: template_v3.html + v3_sprite.svg. v1 and v2 were retired (Oct 2026); the root index.html and
v2/index.html are static redirects to v3/ and are not touched by this script.
Exits 3 (without writing) if any term from data/private_hide.txt appears in the rendered HTML.

Usage: python3 build.py [--json data/dashboard.json] [--out v3/index.html] [--week-start YYYY-MM-DD]
                        [--no-stamp] [--now ISO]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
RANGE_DAYS = 24
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ------------------------------------------------------------------ helpers

def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def fmt_time(hhmm: str | None) -> str:
    if not hhmm:
        return ""
    h, m = map(int, hhmm.split(":"))
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ap}"


def covers(ev: dict, day: dt.date) -> bool:
    start = d(ev["date"])
    end = d(ev.get("end_date") or ev["date"])
    return start <= day <= end


# ------------------------------------------------------------------ model

def upcoming_sunday(day: dt.date) -> dt.date:
    """Sunday -> same day; Monday..Saturday -> the next Sunday."""
    return day + dt.timedelta(days=(6 - day.weekday()) % 7)


class Model:
    def __init__(self, data: dict, now: dt.datetime, week_start: dt.date | None = None):
        self.data = data
        # Private hide list (not committed): any event/todo mentioning a listed term is left off the pages.
        _hp = Path(__file__).resolve().parent / "data" / "private_hide.txt"
        _terms = [l.strip().lower() for l in _hp.read_text().splitlines() if l.strip() and not l.startswith("#")] if _hp.exists() else []
        if _terms:
            _hit = lambda o: any(t in json.dumps(o, ensure_ascii=False).lower() for t in _terms)
            data["events"] = [e for e in data.get("events", []) if not _hit(e)]
            data["todos"] = [t for t in data.get("todos", []) or [] if not _hit(t)]
            _y = data.get("youth") or {}
            if _y.get("activities"):
                _y["activities"] = [a for a in _y["activities"] if not _hit(a)]
            _b = (data.get("sports") or {}).get("byu") or {}
            if _b.get("games"):
                _b["games"] = [g for g in _b["games"] if not _hit({k: v for k, v in g.items() if k != "venue"})]  # venue is never shown
        self.now = now
        self.today = now.date()
        self.meta = data.get("meta", {})
        self.people = data.get("people", {})
        self.kids = data.get("kids", [])
        self.events = [e for e in data.get("events", []) if e.get("date")]
        self.week_start = week_start or upcoming_sunday(self.today)
        self.week_end = self.week_start + dt.timedelta(days=6)
        self.later_days = int(self.meta.get("later_days", 8))
        self.first = min(self.today, self.week_start) - dt.timedelta(days=1)
        self.last = max(self.today + dt.timedelta(days=RANGE_DAYS),
                        self.week_end + dt.timedelta(days=self.later_days + 7))

    def days(self):
        day = self.first
        while day <= self.last:
            yield day
            day += dt.timedelta(days=1)

    def events_on(self, day: dt.date) -> list[dict]:
        return [e for e in self.events if covers(e, day)]

    def flags_on(self, day: dt.date) -> dict[str, dict[str, str]]:
        """{flag: {kid: reason_title}} -- first reason wins per kid."""
        out: dict[str, dict[str, str]] = {"no_school": {}, "half_day": {}}
        for e in self.events_on(day):
            f = e.get("flag")
            if f in out:
                for w in e.get("who", []):
                    out[f].setdefault(w, e.get("title", ""))
        # a kid with no school isn't also on a half day
        for k in list(out["half_day"]):
            if k in out["no_school"]:
                del out["half_day"][k]
        return out

    def routine_items(self, day: dt.date) -> list[dict]:
        items = []
        flags = self.flags_on(day)
        for kid in self.kids:
            r = kid.get("routine")
            if not r or DOW[day.weekday()] not in r.get("days", []):
                continue
            if kid["id"] in flags["no_school"]:
                continue
            items.append({
                "id": f"routine-{kid['id']}-{day}", "date": day.isoformat(),
                "start": r.get("start"), "end": r.get("end"),
                "title": r.get("title", "In person"), "note": r.get("note", ""),
                "who": [kid["id"]], "kind": "routine", "priority": "normal",
            })
        return items

    def kid_status(self, kid: dict, day: dt.date) -> tuple[str, str]:
        """(css-class, text) describing the kid's school day."""
        flags = self.flags_on(day)
        kid_id = kid["id"]
        if kid_id in flags["no_school"]:
            reason = flags["no_school"][kid_id]
            reason = "" if reason.lower().startswith("no school") and "\u2014" not in reason else reason
            reason = re.sub(r"^no school\s*\u2014\s*", "", reason, flags=re.I)
            return "off", "No school" + (f" \u00b7 {reason}" if reason else "")
        if day.weekday() >= 5:
            return "weekend", "Weekend"
        if kid_id in flags["half_day"]:
            return "half", "Half day \u00b7 out at 12 PM"
        r = kid.get("routine")
        if r:
            if DOW[day.weekday()] in r.get("days", []):
                return "inperson", f"In person {fmt_time(r.get('start'))}\u2013{fmt_time(r.get('end'))}"
            return "online", r.get("online_title", "Online")
        return "school", "School day"


# ------------------------------------------------------------------ rendering helpers

ABSORB_RE = re.compile(r"^(term|quarter|q)\s*\d+\s+ends$", re.I)


# trims for compact labels: drop parenthetical/after-comma detail
SHORT_RE = re.compile(r"\s*(\(.*?\)|,.*)$")


YOUTH_GROUP_ORDER = {"all_youth": 0, "all_ym": 1, "teachers": 2, "deacons": 3, "priests": 4, "yw": 5}


def youth_activities(m: Model) -> list[dict]:
    """Effective youth list: sheet/manual items win; ward-site items only fill dates the sheet doesn't cover
    (and never duplicate a sheet title within 3 weeks). Each item gets a 'who' list of our boys."""
    y = m.data.get("youth", {}) or {}
    quorums = y.get("quorums") or {"luke": "teachers", "wyatt": "deacons"}
    acts = [a for a in (y.get("activities") or []) if a.get("date")]
    primary = [a for a in acts if a.get("source") != "site"]
    site = [a for a in acts if a.get("source") == "site"]
    pdates = {a["date"] for a in primary}
    norm = lambda t: re.sub(r"[^a-z0-9]", "", (t or "").lower())
    out = list(primary)
    for a in site:
        if a["date"] in pdates:
            continue
        if any(norm(a.get("title")) == norm(p.get("title")) and abs((d(a["date"]) - d(p["date"])).days) <= 21
               for p in primary):
            continue
        out.append(a)
    res = []
    for a in out:
        g = a.get("group", "all_youth")
        if g in ("all_youth", "all_ym"):
            who = [k for k in quorums]                       # both boys
        else:
            who = [k for k, q in quorums.items() if q == g]
        if not who:
            continue                                         # priests / YW: not our boys
        res.append(dict(a, who=who))
    res.sort(key=lambda a: (a["date"], YOUTH_GROUP_ORDER.get(a.get("group"), 9), a.get("start") or ""))
    return res


def rem_to_var(css: str) -> str:
    """Sizes are authored in rem; turn them into per-page units so each page can auto-fit on its own."""
    return re.sub(r"(-?\d*\.?\d+)rem\b", lambda mo: f"calc(var(--fs) * {mo.group(1)})", css)


# ------------------------------------------------------------------ v3 (two soft pages)
# v3/index.html: pastel rounded cards, bigger icons, less chrome. Page 1 "Today" = a colour-coded card per kid
# (today's items + a small Tomorrow box; youth folded in and tagged YM / All youth), parents strip,
# Come Follow Me (today's scripture from come_follow_me.daily) + Strength of Youth (today's tip).
# No standalone Young Men card. Page 2 "This week" = 10 large day tiles starting today
# (up to 6 items each, youth included and tagged). Everything is rendered for the
# whole date range and the inline script picks today/tomorrow/the 10 tiles from the viewing date
# (America/Denver).

V3_ICON_RULES = [
    (r"\bno school\b|cancel", "x"), (r"\bbreak\b", "leaf"), (r"half day", "clock"),
    (r"pre-?ride", "mtn"), (r"race|final|tournament|championship|\bgame\b|\bmeet\b", "trophy"),
    (r"\bmtb\b|bike|cycling", "bike"), (r"\bact\b|pre-act|test|exam|quiz", "pencil"),
    (r"service|help", "heart"), (r"flight|\bfly\b|airport", "plane"),
    (r"lunch|dinner|breakfast|meal|treat", "food"),
    (r"read|assembly|book|fireside|devotional|scripture|seminary|church|sacrament", "book"),
    (r"conference|youth|festival|party|dance|activity", "users"),
    (r"campus|in person|tour|mtc|temple|visit", "pin"), (r"term|quarter|semester|grades", "cap"),
    (r"online", "laptop"), (r"apparel|shirt|uniform|dress", "shirt"), (r"picture|photo|retake", "spark"),
]


def v3_icon(text: str, default: str = "spark") -> str:
    t = (text or "").lower()
    for rx, name in V3_ICON_RULES:
        if re.search(rx, t):
            return name
    return default


def ic(name: str) -> str:
    return f'<svg class="ic"><use href="#i-{name}"/></svg>'


def v3_trip_label(title: str) -> str:
    """Away-day tag: just the state, e.g. 'Arizona' / 'California' (keeps hotel/park names off the wall)."""
    t = title or ""
    if re.search(r",\s*AZ\b|arizona|phoenix", t, re.I):
        return "Arizona"
    if re.search(r",\s*CA\b|california", t, re.I):
        return "California"
    return SHORT_RE.sub("", t)


def v3_short(title: str) -> str:
    t = re.sub(r"\s*\u00b7\s*spirit apparel( day)?$", "", title or "", flags=re.I)
    t = re.sub(r"^k-\d+\s+", "", t, flags=re.I)
    t = SHORT_RE.sub("", t)
    return t[:1].upper() + t[1:]


def short_time(hhmm: str | None) -> str:
    if not hhmm:
        return ""
    h, mi = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{mi:02d}"


def ordinal(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def v3_dots(m: Model, who: list[str]) -> str:
    order = [k["id"] for k in m.kids] + ["parents", "family"]
    who = sorted(set(who), key=lambda w: order.index(w) if w in order else 99)
    return '<span class="dots">' + "".join(f'<i class="p-{esc(w)}"></i>' for w in who) + "</span>"


def v3_events(m: Model, day: dt.date) -> list[dict]:
    """Calendar items for a day (no trips, no low priority, no no-school flags); half-day flags keep only
    their extra detail ('K-5 Service Day' -> 'Service Day'); 'Term N ends' folded into a same-day half day."""
    half = m.flags_on(day)["half_day"]
    out = []
    for e in m.events_on(day):
        if e.get("kind") == "trip" or e.get("flag") == "no_school" or e.get("priority") == "low":
            continue
        if e.get("flag") == "half_day":
            rest = re.sub(r"^(k-5 )?half day\s*(\u00b7|\u2014|-)?\s*", "", e.get("title", ""), flags=re.I)
            rest = re.sub(r"\s*\u00b7\s*spirit apparel( day)?$", "", rest, flags=re.I)
            if not rest or re.fullmatch(r"spirit apparel( day)?", rest, re.I):
                continue
            e = dict(e, title=rest[:1].upper() + rest[1:], flag=None)
        if ABSORB_RE.match(e.get("title", "")) and half and set(e.get("who", [])) <= set(half):
            continue
        out.append(e)
    out.sort(key=lambda e: (e.get("start") is not None, e.get("start") or "",
                            {"high": 0, "normal": 1, "low": 2}.get(e.get("priority", "normal"), 1)))
    return out


def v3_youth_on(yacts: list[dict], day: dt.date) -> list[dict]:
    return [a for a in yacts if a["date"] == day.isoformat() and a.get("kind") != "none"]


def v3_ym_label(a: dict) -> str:
    """Short tag so a youth item reads as Young Men (or all-youth), not a school event."""
    return "All youth" if a.get("group") == "all_youth" else "YM"


def v3_ym_tent(a: dict) -> str:
    title = a.get("title") or ""
    return "?" if a.get("tentative") and not title.endswith("?") else ""


def v3_it(icon: str, title: str, small: str = "", cls: str = "", tag: str = "") -> str:
    sm = f"<small>{esc(small)}</small>" if small else ""
    tag_html = f'<span class="ymtag">{esc(tag)}</span> ' if tag else ""
    return (f'<div class="it{(" " + cls) if cls else ""}"><span class="bub">{ic(icon)}</span>'
            f'<span class="itx"><span class="itt">{tag_html}{esc(title)}</span>{sm}</span></div>')


def v3_kid_today(m: Model, kid: dict, day: dt.date, yacts: list[dict]) -> str:
    kid_id, parts = kid["id"], []
    cls, text = m.kid_status(kid, day)
    r = kid.get("routine") or {}
    if cls == "off":
        reason = re.sub(r"^No school( \u00b7 )?", "", text)
        parts.append(v3_it("leaf" if "break" in reason.lower() else "x", "No school", reason, "st-off"))
    elif cls == "half":
        absorbed = [e["title"] for e in m.events_on(day) if not e.get("flag") and ABSORB_RE.match(e.get("title", ""))
                    and kid_id in e.get("who", [])]
        parts.append(v3_it("clock", "Half day", " \u00b7 ".join(["Out at 12 PM"] + absorbed), "st-half"))
    elif cls == "inperson":
        place = "Lehi campus" if "lehi" in (r.get("title", "") + kid.get("campus", "")).lower() else "In person"
        parts.append(v3_it("pin", place, f'{short_time(r.get("start"))} \u2013 {short_time(r.get("end"))}', "st-in"))
        note = r.get("note") or ""
        if note:
            a, _, b = note.partition(" + ")
            parts.append(v3_it(v3_icon(note, "pack"), a, f"+ {b}" if b else ""))
    elif cls == "online":
        parts.append(v3_it("laptop", "Online day", r.get("online_title", "")))
    elif cls == "school":
        parts.append(v3_it("pack", "School day"))
    for e in v3_events(m, day):
        who = e.get("who", [])
        if kid_id not in who and "family" not in who:
            continue
        title = e.get("title", "")
        mo = re.match(r"^(.*?)\s*\(([^()]*)\)$", title)
        small_bits = []
        if e.get("start"):
            small_bits.append(fmt_time(e["start"]))
        if mo:
            title = mo.group(1)
            small_bits.append(mo.group(2)[:1].upper() + mo.group(2)[1:])
        elif e.get("note"):
            small_bits.append(re.split(r"[;(]", e["note"])[0].strip())
        if e.get("end_date") and e["end_date"] != e["date"]:
            s, en = d(e["date"]), d(e["end_date"])
            small_bits.append(f"day {(day - s).days + 1} of {(en - s).days + 1}")
        title = re.sub(r"\s*\u00b7\s*spirit apparel( day)?$", "", title, flags=re.I)
        parts.append(v3_it("plane" if e.get("kind") == "flight" else v3_icon(title), title, " \u00b7 ".join(small_bits)))
    for a in v3_youth_on(yacts, day):
        if kid_id not in a.get("who", []):
            continue
        when = fmt_time(a["start"]) if a.get("start") else ""
        parts.append(v3_it(v3_icon(a.get("title"), "users"), (a.get("title") or "") + v3_ym_tent(a),
                           when, "yth", v3_ym_label(a)))
    if not parts:
        parts.append(v3_it("sun", "Free day", "Nothing scheduled", "free"))
    return "".join(parts)


def v3_kid_tomorrow(m: Model, kid: dict, day: dt.date, yacts: list[dict]) -> str:
    kid_id, bits = kid["id"], []
    cls, text = m.kid_status(kid, day)
    if cls == "off":
        bits.append('<span class="no">No school</span>')
    elif cls == "half":
        bits.append('<span class="hf">Half day</span>')
    elif cls == "inperson":
        bits.append("Lehi campus" if "lehi" in ((kid.get("routine") or {}).get("title", "")).lower() else "In person")
    elif cls == "online":
        bits.append("Online day")
    for e in v3_events(m, day):
        who = e.get("who", [])
        if kid_id in who or "family" in who:
            t = short_time(e.get("start"))
            bits.append(esc(v3_short(e.get("title", ""))) + (f" {t}" if t else ""))
    for a in v3_youth_on(yacts, day):
        if kid_id in a.get("who", []):
            bits.append(f'<span class="ymtag">{esc(v3_ym_label(a))}</span> {esc(v3_short(a.get("title") or "") + v3_ym_tent(a))}')
    if not bits:
        bits.append("School day" if cls == "school" else "Nothing scheduled")
    return " \u00b7 ".join(bits)


def render_v3_kids(m: Model) -> str:
    yacts = youth_activities(m)
    y = m.data.get("youth") or {}
    quorums = y.get("quorums") or {}
    cards = []
    for kid in m.kids:
        q = quorums.get(kid["id"])
        sub = f'{ordinal(kid.get("grade"))} \u00b7 {q.title()}' if q else f'{ordinal(kid.get("grade"))} grade'
        today = "".join(f'<div class="items" data-d0="{day.isoformat()}">{v3_kid_today(m, kid, day, yacts)}</div>'
                        for day in m.days())
        tmrw = "".join(f'<span class="tm" data-d1="{day.isoformat()}">{v3_kid_tomorrow(m, kid, day, yacts)}</span>'
                       for day in m.days())
        cards.append(f'<div class="kid p-{esc(kid["id"])}"><div class="top"><div class="av">{esc(kid["name"][:1])}</div>'
                     f'<div><div class="nm">{esc(kid["name"])}</div><div class="gr">{esc(sub)}</div></div></div>'
                     f'{today}<div class="tmrw"><b>Tomorrow</b>{tmrw}</div></div>')
    return "".join(cards)


def render_v3_parents(m: Model) -> str:
    """Slim lavender strip for parent/family-only items (flights, trips). Hidden by JS when today and tomorrow are empty."""
    kid_ids = {k["id"] for k in m.kids}
    out = []
    for day in m.days():
        bits, trips_key, only_trips = [], [], True
        for e in m.events_on(day):
            if e.get("kind") == "trip":
                trips_key.append(v3_trip_label(e.get("title")))
                bits.append(f'<span class="pb away">{ic("bag")}{esc(v3_trip_label(e.get("title")))}</span>')
        for e in v3_events(m, day):
            if set(e.get("who", [])) & kid_ids or "family" in e.get("who", []):
                continue
            t = fmt_time(e.get("start"))
            only_trips = False
            icon = "plane" if e.get("kind") == "flight" else v3_icon(e.get("title"), "cal")
            bits.append(f'<span class="pb">{ic(icon)}{esc(v3_short(e.get("title")))}{f"<small>{esc(t)}</small>" if t else ""}</span>')
        if bits:
            out.append(f'<span class="pday" data-date="{day.isoformat()}" data-trips="{esc("|".join(trips_key))}"'
                       f'{" data-only-trips" if only_trips else ""}><b class="pd"></b>{"".join(bits)}</span>')
    return "".join(out)


def v3_dow(k) -> str:
    return str(k or "")[:3].title()


def _v3_prayer(m) -> str:
    """'Prayer: <boy>' line. Rotates weekly (Sunday start) through meta.prayer_rotation.order from anchor_sunday;
    the iPad works out the current week client-side so it advances without a rebuild."""
    pr = (m.meta.get("prayer_rotation") or {})
    order = [k for k in (pr.get("order") or []) if k]
    if not order or not pr.get("anchor_sunday"):
        return ""
    names = {k.get("id"): k.get("name") for k in m.kids if isinstance(k, dict)}
    spans = "".join(f'<b class="pr-n p-{esc(k)}" data-i="{i}">{esc(names.get(k) or k.title())}</b>' for i, k in enumerate(order))
    return (f'<div class="prayer" data-anchor="{esc(pr["anchor_sunday"])}" data-n="{len(order)}">'
            f'<span class="pr-l">Prayer:</span> {spans}</div>')


def render_v3_spirit(m: Model) -> str:
    """CFM: week's lesson title + reading, then TODAY's scripture/thought from come_follow_me.daily (one element per
    weekday with data-dow; JS shows the one matching the iPad's date). Falls back to the featured question when no
    daily queue is loaded. FSY: chapter + today's tip (large) and tomorrow's tip from daily_by_weekday."""
    sp = m.data.get("spiritual", {}) or {}
    cfm = sp.get("come_follow_me", {}) or {}
    fsy = sp.get("strength_of_youth", {}) or {}
    pending_cfm = cfm.get("status") == "pending" or not cfm.get("reading")
    qs = cfm.get("questions") or []
    fi = cfm.get("featured_question", 0)
    q = qs[fi] if isinstance(fi, int) and 0 <= fi < len(qs) else (qs[0] if qs else "")
    ref = ""
    mo = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", q)
    if mo:
        q, ref = mo.group(1), mo.group(2)
    dates = cfm.get("dates_label") or ""
    dates_s = f" \u00b7 {esc(dates)}" if dates else ""
    daily = [x for x in (cfm.get("daily") or []) if isinstance(x, dict) and x.get("dow")] if not pending_cfm else []
    fallback = (f'<div class="sq">{esc(q)}{f" <i>{esc(ref)}</i>" if ref else ""}</div>' if q else "")
    cfd = ""
    if daily:
        boxes = []
        for x in daily:
            quote = (x.get("quote") or "").strip()
            body = (f'<div class="cq">\u201c{esc(quote)}\u201d</div>' if quote else "") + \
                   (f'<div class="ct">{esc(x.get("thought"))}</div>' if x.get("thought") else "")
            sref = esc(x.get("scripture") or "")
            boxes.append(f'<div class="tbox cfd" data-dow="{esc(v3_dow(x["dow"]))}"><div class="tk">Today'
                         f'{f" <span>{sref}</span>" if sref else ""}</div>{body}</div>')
        # no item for today's weekday -> show the featured question instead
        cfd = "".join(boxes) + (f'<div class="cfd-none">{fallback}</div>' if fallback else "")
    cfm_html = (f'<div class="sc cfm{" pending" if pending_cfm else ""}">'
                f'<div class="sk"><span class="bub">{ic("book")}</span>Come, Follow Me{dates_s}</div>'
                f'<div class="stt">{esc(cfm.get("title") or CFM_WAIT)}</div>'
                + (f'<div class="srd">{esc(cfm.get("reading"))}</div>' if cfm.get("reading") else "")
                + _v3_prayer(m)
                + (cfd or fallback) + "</div>")
    pending_fsy = fsy.get("status") == "pending" or not fsy.get("topic")
    topic = fsy.get("topic") or "This month\u2019s chapter is on its way"
    chap = ""
    mo = re.match(r"^(ch(?:apter)?\.?\s*\d+)\s*:\s*(.+)$", topic, re.I)
    if mo:
        chap, topic = mo.group(1), mo.group(2)
    tipmap = fsy.get("daily_by_weekday") or {}
    tips = ""
    if tipmap and not pending_fsy:
        t0 = "".join(f'<span class="tip" data-dow="{esc(v3_dow(k))}">{esc(v)}</span>' for k, v in tipmap.items())
        tips = (f'<div class="tbox t-today"><div class="tk">Try today</div><div class="ft">{t0}</div></div>'
                f'<div class="sq t-tmrw"><b>Tomorrow</b>{t0}</div>')
    elif fsy.get("daily_application"):
        tips = f'<div class="tbox"><div class="tk">Try today</div><div class="ft">{esc(fsy["daily_application"])}</div></div>'
    sub = " \u00b7 ".join(x for x in (chap, fsy.get("label")) if x)
    fsy_html = (f'<div class="sc fsy{" pending" if pending_fsy else ""}">'
                f'<div class="sk"><span class="bub">{ic("star")}</span>Strength of Youth</div>'
                f'<div class="stt">{esc(topic)}</div>'
                + (f'<div class="srd">{esc(sub)}</div>' if sub else "") + f'{tips}</div>')
    return cfm_html + fsy_html


def v3_tile(m: Model, day: dt.date, yacts: list[dict]) -> str:
    kid_ids = [k["id"] for k in m.kids]
    flags = m.flags_on(day)
    ents = []                                      # (sort key, html)
    big = None
    if day.weekday() < 5:
        groups: dict[str, list[str]] = {}
        for k, reason in flags["no_school"].items():
            groups.setdefault(reason, []).append(k)
        allbrk = set(flags["no_school"]) >= set(kid_ids) and any("break" in r.lower() for r in groups)
        for reason, kids in groups.items():
            brk = "break" in reason.lower()
            label = "Fall break" if brk and "fall" in reason.lower() else ("Break" if brk else "No school")
            if allbrk:
                big = label if brk else big
            ents.append(((0, ""), f'<div class="e {"p-leaf" if brk else "p-red"}"><span class="bub">{ic("leaf" if brk else "x")}</span>'
                                  f'<span class="et"><span class="el">{esc(label)}</span>{v3_dots(m, kids)}</span></div>'))
        if allbrk and big is None:
            big = "No school"
        if flags["half_day"]:
            ents.append(((0, ""), f'<div class="e p-all"><span class="bub">{ic("clock")}</span>'
                                  f'<span class="et"><span class="el">Half day</span>{v3_dots(m, list(flags["half_day"]))}</span></div>'))
    items = list(v3_events(m, day))
    items += m.routine_items(day)
    for e in items:
        who = e.get("who", [])
        if e.get("kind") == "routine":
            label = "Lehi day" if "lehi" in e.get("title", "").lower() else "In person"
            icon = "pin"
        else:
            label = v3_short(e.get("title", ""))
            icon = "plane" if e.get("kind") == "flight" else v3_icon(e.get("title"))
        small = short_time(e.get("start"))
        if not small and e.get("priority") == "high" and e.get("source") not in ("ahs_feed",) and e.get("note"):
            n = re.split(r"[;(,]", e["note"])[0].strip()
            small = re.sub(r"^starts moved\s+", "", n, flags=re.I)
        if len(who) == 1 and who[0] in kid_ids + ["parents"]:
            pc, dots = f"p-{who[0]}", ""
        else:
            pc, dots = "p-all", v3_dots(m, who)
        ents.append(((1, e.get("start") or ""), f'<div class="e {pc}"><span class="bub">{ic(icon)}</span><span class="et"><span class="el">{esc(label)}</span>'
                    f'{f"<small>{esc(small)}</small>" if small else ""}{dots}</span></div>'))
    for a in v3_youth_on(yacts, day):
        who = a.get("who", [])
        pc, dots = (f"p-{who[0]}", "") if len(who) == 1 else ("p-all", v3_dots(m, who))
        label = v3_short(a.get("title") or "") + v3_ym_tent(a)
        small = short_time(a.get("start"))
        tag = v3_ym_label(a)
        detail = " \u00b7 ".join(x for x in (tag, small) if x)
        ents.append(((1, a.get("start") or "99"), f'<div class="e {pc} yth"><span class="bub">{ic(v3_icon(a.get("title"), "users"))}</span>'
                    f'<span class="et"><span class="el">{esc(label)}</span>'
                    f'<small class="ymtag">{esc(detail)}</small>{dots}</span></div>'))
    ents.sort(key=lambda x: x[0])
    byu = v3_byu_tile_items(m, day)                # lowest priority: listed last, first to fall under "+N more"
    trips = [e for e in m.events_on(day) if e.get("kind") == "trip"]
    trips.sort(key=lambda e: e["date"])
    away = (f'<div class="away">{ic("bag")}{esc(v3_trip_label(trips[-1].get("title")))}</div>' if trips else "")
    cls = "day"
    if big and len(ents) <= 1:
        body = f'<div class="big {"p-leaf" if "break" in big.lower() else "p-red"}">{ic("leaf" if "break" in big.lower() else "x")}{esc(big)}</div>'
        if byu:
            body += f'<div class="ev byu-only">{"".join(h for _, h in byu)}</div>'
    elif ents or byu:
        ents += byu
        MAX = 6                                    # v3 page 2 tiles (youth included, tagged YM / All youth)
        hs = [h for _, h in ents]
        more = f'<div class="more">+{len(hs) - MAX} more</div>' if len(hs) > MAX else ""
        body = f'<div class="ev">{"".join(hs[:MAX if len(hs) > MAX else len(hs)])}{more}</div>'
    else:
        body = '<div class="quiet">Nothing yet</div>'
    if big:
        cls += " brk"
    if day.weekday() >= 5:
        cls += " wkend"
    return (f'<div class="{cls}" data-date="{day.isoformat()}"><div class="dw" data-dow="{DOW[day.weekday()]}">{DOW[day.weekday()]}</div>'
            f'<div class="dn">{day.day}</div>{body}{away}</div>')


# ------------------------------------------------------------------ BYU games (sports.byu.games, from fetch_byu.py)
# Low-key: a navy "BYU" pill + ball icon. Page 2 tiles list them after every family/school/YM item, so the
# "+N more" cap drops them first; page 1 shows today's/tomorrow's in a slim line under the motto.

BYU_ICON = {"football": "fball", "mbb": "bball"}


def byu_games_on(m: Model, day: dt.date) -> list[dict]:
    games = ((m.data.get("sports") or {}).get("byu") or {}).get("games") or []
    out = [g for g in games if g.get("date") == day.isoformat() and g.get("opponent")]
    return sorted(out, key=lambda g: g.get("start") or "99")


def byu_matchup(g: dict) -> str:
    return f'{"@" if g.get("home_away") == "away" else "vs"} {g["opponent"]}'


def byu_when(g: dict) -> str:
    bits = [fmt_time(g.get("start")) if g.get("start") else "TBA"]
    if g.get("tv"):
        bits.append(g["tv"])
    if g.get("note"):
        bits.append("Exh." if g["note"].lower().startswith("exhib") else g["note"])
    return " \u00b7 ".join(bits)


def v3_byu_tile_items(m: Model, day: dt.date) -> list[tuple]:
    out = []
    for g in byu_games_on(m, day):
        out.append(((2, g.get("start") or "99"),
                    f'<div class="e byu"><span class="bub">{ic(BYU_ICON.get(g.get("sport"), "trophy"))}</span><span class="et">'
                    f'<span class="el"><span class="byutag">BYU</span>{esc(byu_matchup(g))}</span>'
                    f'<small>{esc(byu_when(g))}</small></span></div>'))
    return out


def render_v3_byu_line(m: Model) -> str:
    """One chip per game for every rendered day; JS shows only today's and tomorrow's (label filled in by JS)."""
    tz = ZoneInfo(m.meta.get("timezone", "America/Denver"))
    out = []
    for day in m.days():
        for g in byu_games_on(m, day):
            attrs = f' data-date="{day.isoformat()}"'
            if g.get("start"):
                h, mi = map(int, g["start"].split(":"))
                st = dt.datetime.combine(day, dt.time(h, mi), tz)
                attrs += f' data-end="{(st + dt.timedelta(hours=3, minutes=30)).isoformat()}"'
                if h >= 17:
                    attrs += " data-night"
            out.append(f'<span class="bg"{attrs}>{ic(BYU_ICON.get(g.get("sport"), "trophy"))}<b class="bd"></b>'
                       f'<span class="byutag">BYU</span>{esc(byu_matchup(g))} <small>{esc(byu_when(g))}</small></span>')
    return "".join(out)


# ------------------------------------------------------------------ hidden grades card (data.grades)
# Not shown on the normal page: a display:none overlay opened by a quick triple-tap on the motto (see template JS).

def grade_cls(pct: float) -> str:
    return "ga" if pct >= 90 else ("gb" if pct >= 80 else "gc")


def pct_txt(pct: float) -> str:
    """As the school shows it: 100, 98.2, 97.71 (no padded zeros)."""
    return f"{pct:.2f}".rstrip("0").rstrip(".")


def render_v3_grades(m: Model) -> str:
    g = m.data.get("grades") or {}
    cols = []
    for kid in m.kids:
        k = g.get(kid["id"]) or {}
        courses = [c for c in (k.get("courses") or []) if isinstance(c.get("pct"), (int, float))]
        empty = k.get("connected") is False or not courses
        if empty:
            body = '<div class="gnone">Not connected yet</div>'
        else:
            courses.sort(key=lambda c: -c["pct"])
            rows = "".join(f'<div class="grow"><span class="gn">{esc(c.get("short") or c.get("name"))}</span>'
                           f'<span class="gp {grade_cls(c["pct"])}">{pct_txt(c["pct"])}%</span></div>' for c in courses)
            src = {"canvas": "Canvas", "veracross": "Veracross"}.get(k.get("source"), k.get("source") or "")
            asof = ""
            if k.get("as_of"):
                a = d(k["as_of"])
                asof = f"as of {a:%b} {a.day}"
            foot = " \u00b7 ".join(x for x in (src, asof) if x)
            body = f'<div class="glist">{rows}</div>' + (f'<div class="gsrc">{esc(foot)}</div>' if foot else "")
        cols.append(f'<div class="gcol{" gempty" if empty else ""} p-{esc(kid["id"])}"><div class="gk"><span class="av">{esc(kid["name"][:1])}</span>'
                    f'{esc(kid["name"])}</div>{body}</div>')
    return "".join(cols)


CFM_WAIT = "This week\u2019s lesson is on its way"
V3_SPRITE = HERE / "v3_sprite.svg"


def build_v3(data: dict, now: dt.datetime, week_start: dt.date | None = None) -> str:
    m = Model(data, now, week_start)
    meta = m.meta
    last = meta.get("last_updated") or now.isoformat(timespec="seconds")
    last_dt = dt.datetime.fromisoformat(last).astimezone(ZoneInfo(meta.get("timezone", "America/Denver")))
    last_label = f"{DOW[last_dt.weekday()]} {last_dt:%b} {last_dt.day} \u00b7 {fmt_time(last_dt.strftime('%H:%M'))}"
    yacts = youth_activities(m)
    tpl = (HERE / "template_v3.html").read_text()
    i, j = tpl.index("<style>"), tpl.index("</style>")
    tpl = tpl[:i] + rem_to_var(tpl[i:j]) + tpl[j:]
    repl = {
        "TITLE": esc(f'{meta.get("family_name", "Family")} \u00b7 Dashboard'),
        "FAMILY": esc(meta.get("family_name", "Family")),
        "MOTTO": (f'<div class="motto">{esc(meta.get("motto"))}</div>' if meta.get("motto") else ""),
        "TZ": esc(meta.get("timezone", "America/Denver")),
        "LAST_ISO": esc(last_dt.isoformat()),
        "LAST_LABEL": esc(last_label),
        "STALE_DAYS": esc(meta.get("stale_after_days", 8)),
        "WEEK_START": m.week_start.isoformat(),
        "BUILD_DATE": m.today.isoformat(),
        "SPRITE": V3_SPRITE.read_text().strip(),
        "KIDS": render_v3_kids(m),
        "PARENTS": render_v3_parents(m),
        "SPIRIT": render_v3_spirit(m),
        "TILES": "".join(v3_tile(m, day, yacts) for day in m.days()),
        "BYU_TODAY": render_v3_byu_line(m),
        "GRADES": render_v3_grades(m),
        "ROTATE_SECONDS": esc(meta.get("v3_rotate_seconds", meta.get("v2_rotate_seconds", 30))),
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("{{" + k + "}}", str(v))
    # page version = hash of everything else on the page; the iPad compares it with the published copy and reloads
    out = out.replace("{{VERSION}}", hashlib.sha256(out.encode()).hexdigest()[:12])
    left = re.findall(r"\{\{[A-Z_0-9]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled v3 template slots: {left}")
    return out


def private_leaks(text: str) -> list[str]:
    """Hide-list terms (data/private_hide.txt) that appear in rendered output -- must be empty before publishing."""
    hp = HERE / "data" / "private_hide.txt"
    if not hp.exists():
        return []
    terms = [l.strip().lower() for l in hp.read_text().splitlines() if l.strip() and not l.startswith("#")]
    import html as _html
    low = text.lower() + "\n" + _html.unescape(text).lower()
    return [t for t in terms if t in low]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--out", "--out-v3", dest="out", default=str(HERE / "v3" / "index.html"),
                    help="where to write the v3 dashboard")
    ap.add_argument("--no-stamp", action="store_true", help="don't update meta.last_updated")
    ap.add_argument("--now", help="override build time (ISO) for testing")
    ap.add_argument("--week-start", help="Sunday (YYYY-MM-DD) that starts the calendar week; default: upcoming Sunday")
    args = ap.parse_args()

    path = Path(args.json)
    data = json.loads(path.read_text())
    tz = ZoneInfo(data.get("meta", {}).get("timezone", "America/Denver"))
    now = dt.datetime.fromisoformat(args.now).astimezone(tz) if args.now else dt.datetime.now(tz)
    if args.week_start:
        week_start = dt.date.fromisoformat(args.week_start)
        if week_start.weekday() != 6:
            print(f"[build] WARNING: --week-start {week_start} is not a Sunday", file=sys.stderr)
    else:
        week_start = upcoming_sunday(now.date())
    data.setdefault("meta", {})["week_start"] = week_start.isoformat()
    if not args.no_stamp:
        data["meta"]["last_updated"] = now.isoformat(timespec="seconds")
    # always persist (week_start may change even with --no-stamp)
    if path:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)
    out3 = Path(args.out)
    html3 = build_v3(data, now, week_start)
    leaks = private_leaks(html3)
    if leaks:
        print(f"[build] ERROR: v3 output mentions hidden terms {leaks}; not writing {out3}", file=sys.stderr)
        return 3
    out3.parent.mkdir(parents=True, exist_ok=True)
    out3.write_text(html3)
    print(f"[build] wrote {out3} (last_updated {data['meta'].get('last_updated')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
