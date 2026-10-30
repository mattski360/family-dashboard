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
import copy
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


# FSY topic -> emoji for the kid-friendly landscape cards (first keyword match wins)
FSY_TOPIC_EMOJI = [(("body", "health"), "\U0001F4AA"), (("sabbath", "temple", "worship"), "\u26EA"),
    (("media", "music", "phone", "screen"), "\U0001F4F1"), (("friend", "relationship", "dating"), "\U0001F91D"),
    (("language", "word", "speak"), "\U0001F5E3\uFE0F"), (("dress", "modest", "appearance"), "\U0001F455"),
    (("honest", "integrity"), "\u2705"), (("work", "self-reliance", "education"), "\U0001F6E0\uFE0F"),
    (("family",), "\U0001F3E1"), (("pray", "spirit", "jesus", "christ"), "\U0001F31F"),
    (("repent", "agency", "choose", "choice"), "\U0001F9ED")]


def fsy_emoji(topic: str) -> str:
    t = (topic or "").lower()
    return next((e for keys, e in FSY_TOPIC_EMOJI if any(k in t for k in keys)), "\U0001F31F")


def _em(s: str, on: bool) -> str:
    return f'<i class="em">{s}</i>' if on else ""


def _v3_prayer(m, emoji: bool = False) -> str:
    """'Prayer: <boy>' line. Rotates weekly (Sunday start) through meta.prayer_rotation.order from anchor_sunday;
    the iPad works out the current week client-side so it advances without a rebuild."""
    pr = (m.meta.get("prayer_rotation") or {})
    order = [k for k in (pr.get("order") or []) if k]
    if not order or not pr.get("anchor_sunday"):
        return ""
    names = {k.get("id"): k.get("name") for k in m.kids if isinstance(k, dict)}
    spans = "".join(f'<b class="pr-n p-{esc(k)}" data-i="{i}">{esc(names.get(k) or k.title())}</b>' for i, k in enumerate(order))
    return (f'<div class="prayer" data-anchor="{esc(pr["anchor_sunday"])}" data-n="{len(order)}">'
            f'<span class="pr-l">{_em("\U0001F64F", emoji)}Prayer:</span> {spans}</div>')


def render_v3_spirit(m: Model, emoji: bool = False) -> str:
    """CFM: week's lesson title + reading, then TODAY's scripture/thought from come_follow_me.daily (one element per
    weekday with data-dow; JS shows the one matching the iPad's date). Falls back to the featured question when no
    daily queue is loaded. FSY: chapter + today's tip (large) and tomorrow's tip from daily_by_weekday.
    emoji=True (live landscape): kid-friendly emoji accents (mockup A) instead of the line-icon bubbles."""
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
    fallback = (f'<div class="sq">{_em("\U0001F4AC", emoji)}{" " if emoji else ""}{esc(q)}{f" <i>{esc(ref)}</i>" if ref else ""}</div>' if q else "")
    cfd = ""
    if daily:
        boxes = []
        for x in daily:
            quote = (x.get("quote") or "").strip()
            body = (f'<div class="cq">\u201c{esc(quote)}\u201d</div>' if quote else "") + \
                   (f'<div class="ct">{esc(x.get("thought"))}</div>' if x.get("thought") else "")
            sref = esc(x.get("scripture") or "")
            boxes.append(f'<div class="tbox cfd" data-dow="{esc(v3_dow(x["dow"]))}"><div class="tk">'
                         f'{_em("\u2728", emoji) + "Scripture of the day" if emoji else "Today"}'
                         f'{f" <span>{sref}</span>" if sref else ""}</div>{body}</div>')
        # no item for today's weekday -> show the featured question instead
        cfd = "".join(boxes) + (f'<div class="cfd-none">{fallback}</div>' if fallback else "")
    cfm_badge = _em("\U0001F4D6", emoji) or f'<span class="bub">{ic("book")}</span>'
    fsy_badge = _em("\U0001F6E1\uFE0F", emoji) or f'<span class="bub">{ic("star")}</span>'
    cfm_html = (f'<div class="sc cfm{" pending" if pending_cfm else ""}">'
                f'<div class="sk">{cfm_badge}Come, Follow Me{dates_s}</div>'
                f'<div class="stt">{esc(cfm.get("title") or CFM_WAIT)}</div>'
                + (f'<div class="srd">{_em("\U0001F4DA", emoji)}{esc(cfm.get("reading"))}</div>' if cfm.get("reading") else "")
                + _v3_prayer(m, emoji)
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
        tips = (f'<div class="tbox t-today"><div class="tk">{_em("\U0001F3AF", emoji)}Try today</div><div class="ft">{t0}</div></div>'
                f'<div class="sq t-tmrw"><b>{_em("\U0001F51C", emoji)}Tomorrow</b>{t0}</div>')
    elif fsy.get("daily_application"):
        tips = f'<div class="tbox"><div class="tk">{_em("\U0001F3AF", emoji)}Try today</div><div class="ft">{esc(fsy["daily_application"])}</div></div>'
    sub = " \u00b7 ".join(x for x in (chap, fsy.get("label")) if x)
    fsy_html = (f'<div class="sc fsy{" pending" if pending_fsy else ""}">'
                f'<div class="sk">{fsy_badge}Strength of Youth</div>'
                f'<div class="stt">{_em(fsy_emoji(topic), emoji and not pending_fsy)}{esc(topic)}</div>'
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


def byu_opp(g: dict) -> str:
    """Opponent name, with its current poll rank ("No. 6 Utah") for unplayed games when fetch_byu.py tagged one."""
    rk = g.get("opp_rank")
    return f'No. {int(rk)} {g["opponent"]}' if rk and not g.get("result") else g["opponent"]


def byu_matchup(g: dict) -> str:
    return f'{"@" if g.get("home_away") == "away" else "vs"} {byu_opp(g)}'


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


# ---------------------------------------------------------------- weekly adventure picks
ADV_DIR = HERE / "data" / "adventures"
ADV_LISTS = {"weekend": "weekend_adventures.csv", "evening": "evening_adventures.csv"}
ADV_HISTORY = 20
_MON = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_SEASON = {"spring": (3, 5), "summer": (6, 8), "fall": (9, 11), "autumn": (9, 11), "winter": (12, 2),
           "school year": (8, 5), "labor day": (8, 9)}


def hide_terms() -> list[str]:
    hp = HERE / "data" / "private_hide.txt"
    if not hp.exists():
        return []
    return [l.strip().lower() for l in hp.read_text().splitlines() if l.strip() and not l.startswith("#")]


def _mrange(a: int, b: int) -> set[int]:
    return {(a - 1 + k) % 12 + 1 for k in range((b - a) % 12 + 1)}


def season_months(text: str) -> set[int]:
    """'Jun-Oct', 'Nov-Mar' (wraps), 'Apr-Jun, Sep-Oct', 'Year-round', 'Summer', 'Fall-Spring', 'July', ...
    Parenthetical notes are ignored. Anything unparseable counts as year-round."""
    allm = set(range(1, 13))
    t = re.sub(r"\([^)]*\)", " ", (text or "").lower())
    if not t.strip() or "year-round" in t or "year round" in t:
        return allm
    out: set[int] = set()
    for part in re.split(r"[,/;&]| and ", t):
        toks = []  # (start, end) per recognised word, in order
        for mo in re.finditer(r"school year|labor day|spring|summer|fall|autumn|winter|[a-z]+", part):
            w = mo.group(0)
            if w in _SEASON:
                toks.append(_SEASON[w])
            elif w[:3] in _MON and (len(w) == 3 or w.startswith(("june", "july", "sept")) or w in (
                    "january", "february", "march", "april", "august", "september", "october", "november", "december")):
                toks.append((_MON[w[:3]], _MON[w[:3]]))
        if not toks:
            continue
        if len(toks) >= 2 and "-" in part:
            out |= _mrange(toks[0][0], toks[-1][1])
        else:
            for a, b in toks:
                out |= _mrange(a, b)
    return out or allm


def pick_adventures(data: dict, week_start: dt.date) -> dict | None:
    """One weekend + one evening adventure for the Sun-Sat week, in season, not on the hide list, not among the
    last ADV_HISTORY picks. Deterministic per week (seeded by week_start); re-running the same week keeps the picks.
    Stored in data['adventures']['this_week']; history in data['meta']['adventure_history']."""
    import csv, random
    terms = hide_terms()
    hidden = lambda row: any(t in json.dumps(row, ensure_ascii=False).lower() for t in terms)
    adv = data.setdefault("adventures", {})
    cur = adv.get("this_week") or {}
    hist = data.setdefault("meta", {}).setdefault("adventure_history", {})
    ws = week_start.isoformat()
    month_for = {"weekend": (week_start + dt.timedelta(days=6)).month,  # the Saturday
                 "evening": (week_start + dt.timedelta(days=3)).month}  # mid-week
    new = {"week_start": ws}
    for kind, fn in ADV_LISTS.items():
        f = ADV_DIR / fn
        if not f.exists():
            continue
        rows = [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f.open(newline=""))]
        keep = cur.get(kind) if cur.get("week_start") == ws else None
        if keep and not hidden(keep):
            new[kind] = keep
            continue
        h = hist.setdefault(kind, [])
        ok = [r for r in rows if r.get("Name") and not hidden(r)
              and month_for[kind] in season_months(r.get("Best Season(s)", ""))]
        cand = [r for r in ok if r["Name"] not in h] or ok
        if not cand:
            continue
        r = random.Random(f"{ws}:{kind}").choice(cand)
        new[kind] = r
        h.append(r["Name"])
        del h[:-ADV_HISTORY]
    adv["this_week"] = new
    return new


def _short_drive(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\bminutes?\b", "min", s)
    s = re.sub(r"\bhours?\b|\bhrs?\b", "hr", s)
    return s


def adventure_candidates() -> dict:
    """Rows for the on-page '🎲 idea' buttons: hide-filtered, minimal fields, months pre-parsed (m)."""
    import csv
    terms = hide_terms()
    out = {}
    for kind, fn in ADV_LISTS.items():
        f = ADV_DIR / fn
        rows = []
        if f.exists():
            for r in csv.DictReader(f.open(newline="")):
                r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
                if not r.get("Name") or any(t in json.dumps(r, ensure_ascii=False).lower() for t in terms):
                    continue
                rows.append({"n": r["Name"], "d": r.get("Description", ""), "l": r.get("Location", ""),
                             "t": _short_drive(r.get("Drive Time from Highland", "")), "c": r.get("Cost Tier", ""),
                             "s": r.get("Best Season(s)", ""), "x": r.get("Reservation / Fee / Notes", ""),
                             "m": sorted(season_months(r.get("Best Season(s)", "")))})
        out[kind] = rows
    return out


def render_meals(data: dict, today: dt.date) -> str:
    """Meal planner card (landscape); build_meals.block() fills it in and adds the planner popup."""
    return ('<button class="meal" id="mlcard" type="button" aria-label="Meal planner"><span class="me">\U0001F37D\uFE0F</span>'
            '<span class="mt"><b>Tonight: Tap to plan</b><small>Meal planner</small></span></button>')


def render_v3_adventures(m: Model) -> str:
    """Two buttons at the bottom of page 2; tapping one shows a random in-season idea in a popup (JS)."""
    data = adventure_candidates()
    if not any(data.values()):
        return ""
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    btn = lambda kind, lab: (f'<button class="ab {kind}" type="button" data-kind="{kind}"'
                             f'{"" if data.get(kind) else " disabled"}><span class="ae">\U0001F3B2</span>{lab}</button>')
    return ('<div class="adv" id="adv">' + btn("evening", "Evening idea") + btn("weekend", "Weekend idea") + "</div>"
            f'<script type="application/json" id="advdata">{js}</script>')


# ------------------------------------------------------------------ BYU easter-egg popup (tap the faded Y)
# Football + men's basketball only: record / polls / standing, recent results, next games. Data: sports.byu
# (fetch_byu.py, refreshed weekly by run.sh). Optional sports.byu.fight_song = {"src","title","credit"}: played on open
# and the popup stays up for the song; without it (or if play() is rejected) it auto-closes after 30 s.
def byu_live_polls(s: dict, gs: list[dict], today: dt.date) -> list[dict]:
    """BYU's poll ranks that are still current. A rank is dropped (no number shown, never guessed) when it is more than
    9 days old while the season is under way, or -- football, one game a week -- when the poll was published before
    BYU's latest game (it can't reflect that result yet; the new AP/Coaches poll comes out the next day).
    fetch_byu.py brings the number back as soon as the new poll is out. Unranked = no entry = no chip."""
    last = max((g["date"] for g in gs if g.get("result") and g.get("note") != "Exhibition"), default="")
    football = any(g.get("sport") == "football" for g in gs)
    out = []
    for p in s.get("polls") or []:
        rk = p.get("rank")
        if not isinstance(rk, int) or not 0 < rk <= 25:
            continue
        asof = p.get("as_of") or ""
        if football and last and (not asof or asof <= last):
            continue
        if last and asof and (today - d(asof)).days > 9:
            continue
        out.append(p)
    return out


def render_byu_pop(data: dict, now: dt.datetime) -> str:
    byu = (data.get("sports") or {}).get("byu") or {}
    games = byu.get("games") or []
    if not games:
        return ""
    today = now.astimezone(ZoneInfo("America/Denver")).date()
    summ = byu.get("summary") or {}

    def when(g):
        dd = d(g["date"])
        return f'{DOW[dd.weekday()][:3]} {dd:%b} {dd.day} · {fmt_time(g.get("start")) + " MT" if g.get("start") else "TBA"}'

    def opp(g):
        return ("vs " if g.get("home_away") == "home" else "at " if g.get("home_away") == "away" else "vs ") + byu_opp(g)

    def ha(g):
        return {"home": "Home", "away": "Away", "neutral": "Neutral"}.get(g.get("home_away"), "")

    cols = []
    for sp, name in (("football", "Football"), ("mbb", "Men's Basketball")):
        gs = [g for g in games if g.get("sport") == sp]
        past = [g for g in gs if g.get("result")][-3:][::-1]
        nxt = [g for g in gs if not g.get("result") and d(g["date"]) >= today][:4]
        s = summ.get(sp) or {}
        chips = [f'<span class="bp-chip">#{int(p["rank"])} {esc(p["poll"])}</span>' for p in byu_live_polls(s, gs, today)]
        facts = []
        if s.get("record"):
            facts.append(f'<b>{esc(s["record"])}</b>')
        if s.get("conf_record"):
            facts.append(f'{esc(s["conf_record"])} conf')
        if s.get("standing"):
            facts.append(esc(s["standing"]))
        if not s.get("record") and sp == "mbb" and not past:
            facts.append("Season opens soon")
        rows_p = "".join(
            f'<li><span class="bp-r {"w" if g["result"].startswith("W") else "l"}">{esc(g["result"])}</span>'
            f'<span class="bp-o">{esc(opp(g))}{" <i>Exh.</i>" if g.get("note") == "Exhibition" else ""}</span>'
            f'<span class="bp-d">{esc(DOW[d(g["date"]).weekday()][:3])} {d(g["date"]):%b} {d(g["date"]).day}</span></li>' for g in past)
        rows_n = "".join(
            f'<li><span class="bp-o">{esc(opp(g))}{" <i>Exh.</i>" if g.get("note") == "Exhibition" else ""}</span>'
            f'<span class="bp-d">{esc(when(g))}</span>'
            f'<span class="bp-m">{esc(ha(g))}{" · " + esc(g["tv"]) if g.get("tv") else ""}</span></li>' for g in nxt)
        cols.append(f'<section class="bp-col"><h3>{name}</h3>'
                    f'<div class="bp-facts">{" · ".join(facts)}</div>'
                    + (f'<div class="bp-chips">{"".join(chips)}</div>' if chips else "")
                    + (f'<h4>Recent</h4><ul class="bp-list">{rows_p}</ul>' if rows_p else "")
                    + (f'<h4>Up next</h4><ul class="bp-list nx">{rows_n}</ul>' if rows_n else "")
                    + '</section>')
    upd = byu.get("updated")
    upd_s = ""
    if upd:
        u = dt.datetime.fromisoformat(upd).astimezone(ZoneInfo("America/Denver"))
        upd_s = f'Updated {u:%b} {u.day}, {u.year}'
    song = byu.get("fight_song") or {}
    # cloudflare_only: the MP3 is gitignored and only uploaded by deploy_cloudflare.sh, which fills data-song from
    # data-song-cf in its staging copy; GitHub Pages gets data-song="" (30 s auto-close, no audio).
    src = "" if song.get("cloudflare_only") else (song.get("src") or "")
    cf_src = song.get("src") or "" if song.get("cloudflare_only") else ""
    return f'''<style>
#byupop{{position:fixed;inset:0;z-index:30;display:none;align-items:center;justify-content:center;padding:2.5vmin;background:rgba(0,20,45,.55)}}
#byupop.on{{display:flex}}
#byupop .bp-card{{position:relative;width:min(96vw,1240px);max-height:94vh;overflow:auto;background:#fff;border-radius:2vmin;box-shadow:0 1.5vmin 6vmin rgba(0,0,0,.4);
  font-family:inherit;color:#0B1F3A;font-size:clamp(16px,2.05vmin,26px);line-height:1.3;border-top:1.1vmin solid #0062B8}}
#byupop .bp-hd{{display:flex;align-items:center;gap:1.6vmin;background:#002E5D;color:#fff;padding:1.6vmin 2.4vmin;padding-right:9vmin}}
#byupop .bp-hd svg{{width:4.6vmin;height:4.6vmin;min-width:28px;min-height:28px;flex:none}}
#byupop .bp-hd b{{font-size:1.55em;font-weight:900;letter-spacing:.02em}}
#byupop .bp-hd span{{opacity:.85;font-size:.9em;margin-left:auto;white-space:nowrap}}
#byupop .bp-x{{position:absolute;top:.6vmin;right:.8vmin;width:max(48px,7vmin);height:max(48px,7vmin);border:0;border-radius:50%;background:#0062B8;color:#fff;
  font-size:max(26px,4vmin);line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center}}
#byupop .bp-body{{display:grid;grid-template-columns:1fr 1fr;gap:2.4vmin;padding:2vmin 2.4vmin 1.2vmin}}
#byupop .bp-col{{min-width:0}}
#byupop h3{{margin:0 0 .3em;font-size:1.3em;color:#002E5D;border-bottom:.35vmin solid #0062B8;padding-bottom:.2em}}
#byupop h4{{margin:.6em 0 .2em;font-size:max(12px,.8em);text-transform:uppercase;letter-spacing:.08em;color:#0062B8}}
#byupop .bp-facts{{font-size:1.05em}}
#byupop .bp-facts b{{font-size:1.25em;color:#002E5D}}
#byupop .bp-chips{{display:flex;flex-wrap:wrap;gap:.4em;margin-top:.4em}}
#byupop .bp-chip{{background:#002E5D;color:#fff;border-radius:1em;padding:.15em .7em;font-weight:800;font-size:.9em}}
#byupop .bp-list{{list-style:none;margin:0;padding:0}}
#byupop .bp-list li{{display:flex;flex-wrap:wrap;align-items:baseline;gap:0 .6em;padding:.32em 0;border-bottom:1px solid #E3EAF3}}
#byupop .bp-o{{font-weight:700;flex:1 1 auto;min-width:0}}
#byupop .bp-o i{{font-style:normal;font-weight:600;font-size:max(12px,.75em);color:#5A6B85}}
#byupop .bp-d{{color:#3A4A63;white-space:nowrap}}
#byupop .nx .bp-d{{flex-basis:100%;order:3;font-size:.92em}}
#byupop .bp-m{{color:#0062B8;font-weight:700;font-size:.9em;white-space:nowrap}}
#byupop .bp-r{{font-weight:900;min-width:4.6em}}
#byupop .bp-r.w{{color:#0062B8}} #byupop .bp-r.l{{color:#9A2B2B}}
#byupop .bp-ft{{padding:.6vmin 2.4vmin 1.6vmin;color:#5A6B85;font-size:.8em;display:flex;justify-content:space-between;gap:1em}}
@media (orientation:portrait){{#byupop .bp-card{{font-size:clamp(14px,2.6vmin,30px)}}#byupop .bp-body{{grid-template-columns:1fr}}}}
@media (max-height:620px) and (orientation:landscape){{#byupop .bp-card{{font-size:15px}}#byupop .nx li:nth-child(4){{display:none}}#byupop .bp-list li{{padding:.2em 0}}#byupop .bp-hd{{padding-top:1vmin;padding-bottom:1vmin}}}}
body.byupop-on #cougs{{z-index:40}}
</style>
<div id="byupop" aria-hidden="true" data-song="{esc(src)}" data-song-cf="{esc(cf_src)}"><div class="bp-card" role="dialog" aria-label="BYU Cougars">
<button class="bp-x" id="bpx" type="button" aria-label="Close">&times;</button>
<div class="bp-hd"><svg viewBox="0 0 32 32" aria-hidden="true"><path fill="#fff" d="M2 4h12v4.2h-2.6L16 15.6l4.6-7.4H18V4h12v4.2h-2.2L19.6 20v4h3v4H9.4v-4h3v-4L4.2 8.2H2z"/></svg><b>BYU Cougars</b><span>Go Cougs!</span></div>
<div class="bp-body">{"".join(cols)}</div>
<div class="bp-ft"><span>{esc(upd_s)}</span><span>{esc(song.get("credit") or "")}</span></div>
</div></div>
<script>(function(){{
  var pop=document.getElementById('byupop'),y=document.getElementById('yegg');if(!pop||!y)return;
  var t=0,au=null,src=pop.getAttribute('data-song');
  function close(){{pop.classList.remove('on');document.body.classList.remove('byupop-on');pop.setAttribute('aria-hidden','true');clearTimeout(t);
    if(au){{try{{au.pause();au.currentTime=0;}}catch(e){{}}}}}}
  function arm(ms){{clearTimeout(t);t=setTimeout(close,ms);}}
  function open(){{pop.classList.add('on');document.body.classList.add('byupop-on');pop.setAttribute('aria-hidden','false');pop.querySelector('.bp-card').scrollTop=0;arm(30000);
    if(src){{try{{au=au||new Audio(src);au.currentTime=0;
      au.onloadedmetadata=function(){{if(!au.paused&&isFinite(au.duration)&&au.duration>3)arm(au.duration*1000+1500);}};
      au.onended=function(){{arm(1500);}};au.onerror=function(){{arm(30000);}};
      var p=au.play();if(p&&p.then)p.then(function(){{if(isFinite(au.duration)&&au.duration>3)arm((au.duration-au.currentTime)*1000+1500);}},function(){{arm(30000);}});
    }}catch(e){{arm(30000);}}}}}}
  y.addEventListener('click',function(){{if(!pop.classList.contains('on'))open();}});
  document.getElementById('bpx').addEventListener('click',function(e){{e.stopPropagation();close();}});
  pop.addEventListener('click',function(e){{e.stopPropagation();if(e.target===pop)close();}});
  pop.addEventListener('pointerdown',function(e){{e.stopPropagation();}});
}})();</script>
'''


def build_v3(data: dict, now: dt.datetime, week_start: dt.date | None = None, template: str = "template_v3.html", features=True, themes=None) -> str:
    m = Model(data, now, week_start)
    meta = m.meta
    last = meta.get("last_updated") or now.isoformat(timespec="seconds")
    last_dt = dt.datetime.fromisoformat(last).astimezone(ZoneInfo(meta.get("timezone", "America/Denver")))
    last_label = f"{DOW[last_dt.weekday()]} {last_dt:%b} {last_dt.day} \u00b7 {fmt_time(last_dt.strftime('%H:%M'))}"
    yacts = youth_activities(m)
    tpl = (HERE / template).read_text()
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
        "SPIRIT": render_v3_spirit(m, emoji=(template == "template_landscape.html")),
        "TILES": "".join(v3_tile(m, day, yacts) for day in m.days()),
        "BYU_TODAY": render_v3_byu_line(m),
        "GRADES": render_v3_grades(m),
        "ADVENTURES": render_v3_adventures(m),
        "MEALS": render_meals(data, m.today),
        "ROTATE_SECONDS": esc(meta.get("v3_rotate_seconds", meta.get("v2_rotate_seconds", 30))),
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("{{" + k + "}}", str(v))
    if template == "template_landscape.html" and data.get("chores"):   # chores panel (mockup A), live landscape only
        import build_chores_mockups as _chores
        out = out.replace("</body>", _chores.block(data, "a", live=True) + "</body>", 1)
    if template == "template_landscape.html":   # meal planner v1 (live landscape only)
        import build_meals as _meals
        out = out.replace("</body>", _meals.block(data) + "</body>", 1)
    if template == "template_landscape.html":   # CFM / FSY study popups (live landscape only)
        import build_study as _study
        out = out.replace("</body>", _study.block(data) + "</body>", 1)
    if template == "template_landscape.html" and features:   # weather (p1+p2), trivia/joke (p2), gratitude board (p3)
        import build_features as _feat
        _fun = json.loads((HERE / "data" / "daily_fun.json").read_text())
        out = _feat.transform(out, _fun, prod=True)
    import build_theme as _theme
    if template in ("template_v3.html", "template_landscape.html") and (_theme.LIVE if themes is None else themes):
        out = _theme.apply(out)   # monthly colour theme, picked in the browser (off until Matt approves the 12 previews)
    if 'id="yegg"' in out:
        out = out.replace("</body>", render_byu_pop(data, now) + "</body>", 1)
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
    ap.add_argument("--no-landscape", action="store_true", help="skip landscape/ (final) and the landscape-a/ mockup")
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
    try:
        tw = pick_adventures(data, week_start)
        print(f"[build] adventures {week_start}: " + " | ".join(f"{k}={(tw or {}).get(k, {}).get('Name')}" for k in ADV_LISTS))
    except Exception as e:  # fail soft: keep last week's strip rather than breaking the build
        print(f"[build] WARNING: adventure picker failed: {e}", file=sys.stderr)
    if not args.no_stamp:
        data["meta"]["last_updated"] = now.isoformat(timespec="seconds")
    # always persist (week_start may change even with --no-stamp)
    if path:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)
    out3 = Path(args.out)
    data_pristine = copy.deepcopy(data)
    html3 = build_v3(data, now, week_start)
    leaks = private_leaks(html3)
    if leaks:
        print(f"[build] ERROR: v3 output mentions hidden terms {leaks}; not writing {out3}", file=sys.stderr)
        return 3
    # landscape mockups (1920x1080): same data, same hide-leak check; only written when --out is the default v3 path
    land = []
    if not args.no_landscape:
        # landscape/ is the final wall-display page; landscape-b/ is a static redirect to it (not rebuilt)
        for name, tpl in (("a", "template_landscape_a.html"), ("", "template_landscape.html")):
            if not (HERE / tpl).exists():
                continue
            h = build_v3(copy.deepcopy(data_pristine), now, week_start, template=tpl)
            lk = private_leaks(h)
            if lk:
                print(f"[build] ERROR: landscape{'-' + name if name else ''} output mentions hidden terms {lk}; not writing", file=sys.stderr)
                return 3
            land.append((HERE / ("landscape-" + name if name else "landscape") / "index.html", h))
    out3.parent.mkdir(parents=True, exist_ok=True)
    out3.write_text(html3)
    print(f"[build] wrote {out3} (last_updated {data['meta'].get('last_updated')})")
    for o, h in land:
        o.parent.mkdir(parents=True, exist_ok=True)
        o.write_text(h)
        print(f"[build] wrote {o}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
