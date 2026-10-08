#!/usr/bin/env python3
"""Render index.html (self-contained: inline CSS/JS, no external requests) from data/dashboard.json.

The weekly calendar is a fixed Sunday-Saturday week starting at meta.week_start. The page is rebuilt
Saturday night for the following week. By default week_start is the upcoming Sunday (or today if
today is Sunday); --week-start overrides it and the value used is written back to meta.week_start.
When the page is viewed before week_start, a small "Rest of this week" strip shows the remaining days.
The inline script highlights today and dims past days based on the viewing date (America/Denver).

Usage: python3 build.py [--json data/dashboard.json] [--out index.html] [--week-start YYYY-MM-DD]
                        [--no-stamp] [--now ISO]
"""
from __future__ import annotations

import argparse
import datetime as dt
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


def fmt_day(day: dt.date) -> str:
    return f"{DOW[day.weekday()]}, {day:%b} {day.day}"


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def darken(h: str, f: float = 0.42) -> str:
    r, g, b = hex_rgb(h)
    return "#%02x%02x%02x" % tuple(int(c * (1 - f)) for c in (r, g, b))


def covers(ev: dict, day: dt.date) -> bool:
    start = d(ev["date"])
    end = d(ev.get("end_date") or ev["date"])
    return start <= day <= end


ICONS = {
    "plane": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15.5v-1.7l-8-5V3.5a1.5 1.5 0 0 0-3 0v5.3l-8 5v1.7l8-2.5v5.2l-2 1.5V21l3.5-1 3.5 1v-1.3l-2-1.5V13l8 2.5z" fill="currentColor"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" fill="currentColor"/></svg>',
    "book": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5a1.5 1.5 0 0 0 0 3H20v-1" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "check": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "theme": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" fill="currentColor"/></svg>',
    "star": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4 6.7 19.4l1.2-6L3.4 9.3l6-.7z" fill="currentColor"/></svg>',
    "bell": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22a2.5 2.5 0 0 0 2.4-2h-4.8a2.5 2.5 0 0 0 2.4 2zm7-6V11a7 7 0 0 0-5.5-6.8V3.5a1.5 1.5 0 0 0-3 0v.7A7 7 0 0 0 5 11v5l-2 2v1h18v-1z" fill="currentColor"/></svg>',
    "cal": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 2v2H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2V2h-2v2H9V2zM5 9h14v10H5z" fill="currentColor"/></svg>',
    "kids": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zm8.5 0a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM8 13c-3.3 0-6 1.7-6 3.8V19h12v-2.2C14 14.7 11.3 13 8 13zm8.5.5c-.7 0-1.4.1-2 .3 1 .8 1.5 1.8 1.5 3V19h6v-2c0-1.9-2.5-3.5-5.5-3.5z" fill="currentColor"/></svg>',
    "cap": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3L1 9l11 6 9-4.9V17h2V9zM5 13.2v4L12 21l7-3.8v-4L12 17z" fill="currentColor"/></svg>',
}

# ------------------------------------------------------------------ model

def upcoming_sunday(day: dt.date) -> dt.date:
    """Sunday -> same day; Monday..Saturday -> the next Sunday."""
    return day + dt.timedelta(days=(6 - day.weekday()) % 7)


def week_label(start: dt.date) -> str:
    end = start + dt.timedelta(days=6)
    if start.month == end.month:
        return f"Week of {start:%b} {start.day}\u2013{end.day}"
    return f"Week of {start:%b} {start.day} \u2013 {end:%b} {end.day}"


class Model:
    def __init__(self, data: dict, now: dt.datetime, week_start: dt.date | None = None):
        self.data = data
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

    def key_dates(self, kid: dict) -> list[tuple[dt.date, str]]:
        """Upcoming 'key dates' for one kid: high-priority events, grouped by day."""
        out = []
        for day in self.days():
            titles = []
            for e in sorted(self.events_on(day), key=lambda e: (e.get("flag") is None, e.get("start") or "")):
                if e.get("kind") == "trip" or e.get("priority") != "high":
                    continue
                who = set(e.get("who", []))
                if kid["id"] not in who and "family" not in who:
                    continue
                if d(e["date"]) != day:      # only the first day of multi-day items
                    continue
                t = e.get("title", "")
                if e.get("flag") == "no_school" and "no school" not in t.lower():
                    t += " (no school)"
                elif e.get("flag") == "half_day" and "half day" not in t.lower():
                    t += " (half day)"
                if t not in titles:
                    titles.append(t)
            if titles:
                titles = [re.sub(r"\s*\u00b7\s*spirit apparel", "", t, flags=re.I) for t in titles]
                out.append((day, " \u00b7 ".join(titles[:2])))
        return out

# ------------------------------------------------------------------ rendering

def chips(m: Model, who: list[str]) -> str:
    out = []
    for w in who:
        p = m.people.get(w, {"label": w.title()})
        out.append(f'<span class="chip p-{esc(w)}">{esc(p.get("label", w))}</span>')
    return "".join(out)


def render_item(m: Model, e: dict, day: dt.date, inline_chips: bool = False) -> str:
    kind = e.get("kind", "event")
    pri = e.get("priority", "normal")
    t = fmt_time(e.get("start"))
    end = fmt_time(e.get("end"))
    multi = e.get("end_date") and e["end_date"] != e["date"]
    icon = ICONS["plane"] if kind == "flight" else ""
    note = e.get("note", "")
    if multi:
        s, en = d(e["date"]), d(e["end_date"])
        n, tot = (day - s).days + 1, (en - s).days + 1
        note = (note + " \u00b7 " if note else "") + f"day {n} of {tot}"
    time_html = (f'<span class="t">{esc(t)}</span>' + (f'<span class="t2">\u2013{esc(end)}</span>' if end else "")) if t else '<span class="t allday">All day</span>'
    if inline_chips:                                  # v2: chips flow right after the title text
        return (f'<li class="item k-{esc(kind)} pr-{esc(pri)} inl">'
                f'<div class="when">{time_html}</div>'
                f'<div class="what"><span class="title">{icon}{esc(e.get("title"))}'
                f'<span class="who in">{chips(m, e.get("who", []))}</span></span>'
                f'{f"<span class=note>{esc(note)}</span>" if note else ""}</div></li>')
    return (f'<li class="item k-{esc(kind)} pr-{esc(pri)}">'
            f'<div class="when">{time_html}</div>'
            f'<div class="what"><span class="title">{icon}{esc(e.get("title"))}</span>'
            f'{f"<span class=note>{esc(note)}</span>" if note else ""}</div>'
            f'<div class="who">{chips(m, e.get("who", []))}</div></li>')


HIDE_LOW = True
ABSORB_RE = re.compile(r"^(term|quarter|q)\s*\d+\s+ends$", re.I)


def render_day(m: Model, day: dt.date, inline_chips: bool = False) -> str:
    evs = m.events_on(day)
    trips = [e for e in evs if e.get("kind") == "trip"]
    flags = m.flags_on(day)
    # banners: group kids by flag + reason
    banners = []
    # short all-kid notes (e.g. "Term 1 ends") folded into a same-day half-day banner
    half_kids = set(flags["half_day"])
    absorbed = [e for e in evs if not e.get("flag") and e.get("kind") != "trip" and half_kids
                and ABSORB_RE.match(e.get("title", "")) and set(e.get("who", [])) <= half_kids]
    for flag, label in (("no_school", "No school"), ("half_day", "Half day")):
        if day.weekday() >= 5 and flag == "no_school":
            continue
        groups: dict[str, list[str]] = {}
        for kid, reason in flags[flag].items():
            groups.setdefault("" if flag == "half_day" else reason, []).append(kid)
        for reason, kids in groups.items():
            r = re.sub(r"^(no school|half day)\s*(\u2014|\u00b7)?\s*", "", reason, flags=re.I)
            r = re.sub(r"\s*\u00b7\s*spirit apparel$", "", r)
            if r.lower() in ("no school", "half day", "k-5 half day"):
                r = ""
            if flag == "half_day":
                r = " \u00b7 ".join(["Out at 12 PM"] + [a["title"] for a in absorbed])
            order = [k["id"] for k in m.kids]
            kids.sort(key=lambda k: order.index(k) if k in order else 99)
            banners.append(
                f'<div class="banner b-{flag}"><span class="bl">{label}</span>'
                f'<span class="br">{esc(r)}</span><span class="who">{chips(m, kids)}</span></div>')
    items = []
    for e in evs:
        if e.get("kind") == "trip" or e in absorbed:
            continue
        if e.get("priority") == "low" and HIDE_LOW:
            continue                                  # dimmed/low-priority items are dropped to keep one screen
        if e.get("flag") == "no_school":
            continue                                  # fully described by the banner
        if e.get("flag") == "half_day":
            rest = re.sub(r"^(k-5 )?half day\s*(\u00b7|\u2014|-)?\s*", "", e.get("title", ""), flags=re.I)
            if not rest:
                continue
            if re.fullmatch(r"spirit apparel( day)?", rest, re.I):
                continue                              # dress-code note on a half day: banner is enough
            e = dict(e, title=rest[:1].upper() + rest[1:], flag=None)
        items.append(e)
    items += m.routine_items(day)
    items.sort(key=lambda e: (e.get("start") is not None, e.get("start") or "",
                              {"high": 0, "normal": 1, "low": 2}.get(e.get("priority", "normal"), 1)))
    trip_html = "".join(
        f'<span class="trip">{ICONS["pin"]}{esc(t["title"])}</span>' for t in trips)
    body = "".join(render_item(m, e, day, inline_chips) for e in items)
    wk = " weekend" if day.weekday() >= 5 else ""
    # no-JS fallback: pre-mark the initial window relative to the build date
    if m.week_start <= day <= m.week_end:
        wk += " show"
    if day < m.today:
        wk += " past"
    if day == m.today:
        wk += " is-today"
    if not body and not banners:
        wk += " quiet"
        trip_html = '<span class="empty">Nothing scheduled</span>' + trip_html
    return (f'<section class="day{wk}" data-date="{day.isoformat()}">'
            f'<header class="dh"><span class="dname">{DOW[day.weekday()]}</span>'
            f'<span class="ddate">{day:%b} {day.day}</span><span class="rel"></span>'
            f'<span class="trips">{trip_html}</span></header>'
            f'{"".join(banners)}<ul class="items">{body}</ul></section>')


def render_mini_day(m: Model, day: dt.date) -> str:
    """One inline segment of the single-line 'Rest of this week' strip (days before week_start)."""
    flags = m.flags_on(day)
    parts = []
    if day.weekday() < 5:
        for flag, label in (("no_school", "No school"), ("half_day", "Half day")):
            kids = list(flags[flag])
            if kids:
                parts.append(f'<span class="mi f-{flag}">{label}{chips(m, kids)}</span>')
    evs = [e for e in m.events_on(day) if e.get("kind") != "trip" and e.get("flag") != "no_school"
           and e.get("priority") != "low"
           and not (e.get("flag") == "half_day" and re.match(r"^(k-5 )?half day", e.get("title", ""), re.I))]
    evs += m.routine_items(day)
    evs.sort(key=lambda e: (e.get("start") is not None, e.get("start") or ""))
    for e in evs:
        title = SHORT_RE.sub("", e.get("title") or "")
        parts.append(f'<span class="mi pr-{esc(e.get("priority", "normal"))}">{esc(title)}{chips(m, e.get("who", []))}</span>')
    if not parts:
        parts.append('<span class="mi empty">Nothing scheduled</span>')
    show = " show" if m.today <= day < m.week_start else ""
    return (f'<span class="rday{show}" data-date="{day.isoformat()}"><b class="rdh">{DOW[day.weekday()]} {day.day}</b>'
            f'{"".join(parts)}</span>')


# trims for compact one-line strips (rest-of-week): drop parenthetical/after-comma detail
SHORT_RE = re.compile(r"\s*(\(.*?\)|,.*)$")
LATER_MAJOR_RE = re.compile(r"\b(term|quarter|q[1-4]|semester)\b.*\b(begins|starts|ends)\b|\b(begins|starts)\b", re.I)


def render_later(m: Model, day: dt.date) -> str:
    """Inline 'Later' entry: only no-school/half-day flags and major items (family/manual highs, term starts)."""
    flags = m.flags_on(day)
    parts = []
    if day.weekday() < 5:
        for flag, label in (("no_school", "No school"), ("half_day", "Half day")):
            kids = list(flags[flag])
            if kids:
                order = [k["id"] for k in m.kids]
                kids.sort(key=lambda k: order.index(k) if k in order else 99)
                parts.append(f'<span class="li f-{flag}">{label}{chips(m, kids)}</span>')
    for e in m.events_on(day):
        if e.get("flag") or e.get("kind") == "trip" or d(e["date"]) != day:
            continue
        major = (e.get("priority") == "high" and e.get("source") != "ahs_feed") or \
                (e.get("source") == "ahs_feed" and LATER_MAJOR_RE.search(e.get("title", "")))
        if e.get("major"):
            major = True
        if not major:
            continue
        parts.append(f'<span class="li">{esc(e.get("title"))}{chips(m, e.get("who", []))}</span>')
    if not parts:
        return ""
    return (f'<span class="later-row" data-date="{day.isoformat()}"><b class="ld">'
            f'{DOW[day.weekday()]} {day:%b} {day.day}</b>{"".join(parts)}</span>')


def grades_line(m: Model, kid_id: str) -> tuple[str, bool]:
    """Single compact grades line for a kid. Returns (html, has_data). Never invents anything."""
    acad = m.data.get("academics", {}) or {}
    screen = m.data.get("screen_time", {}) or {}
    a = (acad.get("kids", {}) or {}).get(kid_id, {}) or {}
    courses = a.get("courses") or []
    miss = a.get("missing_count")
    tests = [t for t in (a.get("upcoming_tests") or []) if t.get("date") and d(t["date"]) >= m.today]
    bits = []
    if courses:
        pcts = [c["percent"] for c in courses if isinstance(c.get("percent"), (int, float))]
        if pcts:
            bits.append(f"avg {sum(pcts) / len(pcts):.0f}%")
        low = None
        for c in courses:
            if isinstance(c.get("percent"), (int, float)) and (low is None or c["percent"] < low["percent"]):
                low = c
        if low is not None and len(courses) > 1:
            bits.append(f'low: {low.get("name")} {low.get("letter") or ""}'.strip())
        elif not pcts:
            letters = " ".join(c.get("letter") for c in courses if c.get("letter"))
            if letters:
                bits.append(letters)
    if miss is not None:
        bits.append(f"{int(miss)} missing")
    if tests:
        t = sorted(tests, key=lambda t: t["date"])[0]
        bits.append(f'test {fmt_day(d(t["date"]))}')
    if screen.get("enabled"):
        sdat = (screen.get("kids", {}) or {}).get(kid_id, {}) or {}
        if sdat.get("today_minutes") is not None:
            v = int(sdat["today_minutes"])
            bits.append(f"screen {v // 60}h{v % 60:02d}" if v >= 60 else f"screen {v}m")
    if not bits:
        return f'<div class="gline soon">{ICONS["cap"]}Grades coming soon</div>', False
    bad = " bad" if miss else ""
    joined = esc(" \u00b7 ".join(bits))
    return f'<div class="gline{bad}">{ICONS["cap"]}{joined}</div>', True


def render_academics(m: Model):
    """Kids & academics: name, grade, school, and ONE grades line per kid (no invented data)."""
    acad = m.data.get("academics", {}) or {}
    cols, any_data = [], False
    for kid in m.kids:
        gl, has = grades_line(m, kid["id"])
        any_data = any_data or has
        school = kid.get("school_short") or kid.get("school") or ""
        cols.append(f'<div class="acol p-{esc(kid["id"])}"><div class="acol-h"><span class="aname">{esc(kid["name"])}</span>'
                    f'<span class="agrade">Grade {esc(kid.get("grade"))}</span></div>'
                    f'<div class="ksch">{esc(school)}</div>{gl}</div>')
    upd = acad.get("updated")
    sub = ""
    if upd:
        try:
            u = dt.datetime.fromisoformat(upd)
            sub = f"as of {DOW[u.weekday()]} {u:%b} {u.day}"
        except ValueError:
            sub = esc(upd)
    return f'<div class="acols{"" if any_data else " nodata"}">{"".join(cols)}</div>', sub


YOUTH_GROUP_LABEL = {"all_youth": "All youth", "all_ym": "All YM", "deacons": "Deacons",
                     "teachers": "Teachers", "priests": "Priests", "yw": "YW"}
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


def render_youth(m: Model) -> str:
    """One line per boy (his quorum + all-youth items in the next N days) plus one compact Later line."""
    acts = [a for a in youth_activities(m) if m.first <= d(a["date"]) <= m.last]
    acts.sort(key=lambda a: (a["date"], a.get("start") or ""))
    order = [k["id"] for k in m.kids]
    boys = []
    for a in acts:
        for w in a.get("who", []):
            if w in order and w not in boys:
                boys.append(w)
    boys.sort(key=lambda k: order.index(k))
    quorum = {}
    for a in acts:
        if a.get("group") in ("deacons", "teachers", "priests") and len(a.get("who", [])) == 1:
            quorum.setdefault(a["who"][0], YOUTH_GROUP_LABEL.get(a["group"], ""))
    shared = len(boys) > 1
    def is_shared(a):
        return shared and set(boys) <= set(a.get("who", []))

    def row_items(sel):
        its = []
        for a in acts:
            if not sel(a):
                continue
            day = d(a["date"])
            none = a.get("kind") == "none"
            if none:
                when = ""
            elif a.get("start"):
                when = fmt_time(a["start"])
            else:
                when = "time TBA"
            tent = " ?" if a.get("tentative") and not a.get("title", "").endswith("?") else ""
            its.append(f'<span class="yit{" none" if none else ""}" data-date="{a["date"]}"><b>{DOW[day.weekday()]} {day.day}</b> '
                       f'{esc(a.get("title"))}{tent}{f"<i>{esc(when)}</i>" if when else ""}</span>')
        return "".join(its)

    rows = []
    for b in boys:
        kid = next((k for k in m.kids if k["id"] == b), {})
        name = kid.get("name", b.title())
        its = row_items(lambda a, b=b: b in a.get("who", []) and not is_shared(a))
        rows.append(f'<div class="yrow p-{esc(b)}"><span class="yname">{esc(name)}</span>'
                    f'<span class="yq">{esc(quorum.get(b, ""))}</span><span class="yits">{its}'
                    f'<span class="ynone">Nothing listed</span></span></div>')
    if shared:
        # activities for everyone (e.g. all-youth firesides) get one shared line instead of repeating per boy
        its = row_items(is_shared)
        rows.append(f'<div class="yrow both"><span class="yname">Both</span><span class="yq">All youth</span>'
                    f'<span class="yits">{its}<span class="ynone">Nothing listed</span></span></div>')
    # Later: one entry per (date, title), chips for who
    later, seen = [], set()
    for a in acts:
        key = (a["date"], a.get("title"))
        if key in seen:
            continue
        seen.add(key)
        day = d(a["date"])
        none = a.get("kind") == "none"
        if none and a.get("group") != "all_youth":
            continue
        short = esc(SHORT_RE.sub("", a.get("title") or ""))
        tent = " ?" if a.get("tentative") and not short.endswith("?") else ""
        who = a.get("who", [])
        later.append(f'<span class="yli{" none" if none else ""}" data-date="{a["date"]}"><b>{DOW[day.weekday()]} {day:%b} {day.day}</b> '
                     f'{short}{tent}{chips(m, who) if len(who) < len(boys) else ""}</span>')
    return (f'<div class="yrows">{"".join(rows)}</div>'
            f'<div class="ylater"><span class="lbl">Later</span>{"".join(later)}</div>')


def render_spiritual(m: Model) -> str:
    """Compact: CFM = title, dates · reading, ONE featured question. FSY = topic + today's tip.
    Extra JSON content (summary, other questions, focus, quote, previous lesson) is kept but not rendered."""
    sp = m.data.get("spiritual", {}) or {}
    cfm = sp.get("come_follow_me", {}) or {}
    fsy = sp.get("strength_of_youth", {}) or {}
    pending_cfm = cfm.get("status") == "pending" or not cfm.get("reading")
    qs = cfm.get("questions") or []
    fi = cfm.get("featured_question", 0)
    q = qs[fi] if isinstance(fi, int) and 0 <= fi < len(qs) else (qs[0] if qs else "")
    meta = " \u00b7 ".join(x for x in (cfm.get("dates_label"), cfm.get("reading")) if x)
    cfm_html = (f'<div class="sp-block{" pending" if pending_cfm else ""}">'
                f'<div class="sp-k">{ICONS["book"]}Come, Follow Me'
                f'{f"<span class=sp-wk>{esc(meta)}</span>" if meta else ""}</div>'
                f'<div class="sp-title">{esc(cfm.get("title") or "This week&#39;s lesson is on its way")}</div>'
                f'{f"<div class=sp-q1><span class=lbl>Discuss</span>{esc(q)}</div>" if q else ""}</div>')
    pending_fsy = fsy.get("status") == "pending" or not fsy.get("topic")
    daily = fsy.get("daily_by_weekday") or {}
    daily_html = "".join(
        f'<div class="sp-daily-d" data-dow="{esc(k[:3].title())}"><span class="lbl">Today</span>{esc(v)}</div>'
        for k, v in daily.items())
    if fsy.get("daily_application"):
        daily_html += f'<div class="sp-daily-all"><span class="lbl">Try today</span>{esc(fsy["daily_application"])}</div>'
    lbl = fsy.get("label") or ""
    fsy_html = (f'<div class="sp-block{" pending" if pending_fsy else ""}">'
                f'<div class="sp-k">{ICONS["star"]}Strength of Youth'
                f'{f"<span class=sp-wk>{esc(lbl)}</span>" if lbl else ""}</div>'
                f'<div class="sp-title">{esc(fsy.get("topic") or "This month&#39;s chapter is on its way")}</div>'
                f'{f"<div class=sp-daily>{daily_html}</div>" if daily_html else ""}</div>')
    return cfm_html + fsy_html


def render_todos(m: Model) -> str:
    """Heads-up: one line each, no detail; JS shows at most 3 (soonest due first)."""
    todos = [t for t in (m.data.get("todos", []) or []) if not t.get("done")]
    prio = {"high": 0, "normal": 1, "low": 2}
    todos.sort(key=lambda t: (prio.get(t.get("priority", "normal"), 1), t.get("due") or "9999"))
    rows = []
    for t in todos:
        due = ""
        if t.get("due"):
            dd = d(t["due"])
            due = f'<span class="due">by {DOW[dd.weekday()]} {dd:%b} {dd.day}</span>'
        rows.append(
            f'<li class="todo pr-{esc(t.get("priority", "normal"))}" data-until="{esc(t.get("hide_after", ""))}">'
            f'<span class="box"></span><span class="tt">{esc(t.get("text"))}</span>{due}'
            f'<span class="who">{chips(m, t.get("who", []))}</span></li>')
    if not rows:
        return '<li class="todo none">All clear \u2014 nothing pending.</li>'
    return "".join(rows) + '<li class="todo none hidden-default">All clear \u2014 nothing pending.</li>'


def person_css(m: Model) -> str:
    out = []
    for pid, p in m.people.items():
        c = p.get("color", "#999999")
        r, g, b = hex_rgb(c)
        out.append(f".p-{pid}{{--c:{c};--cbg:rgba({r},{g},{b},.17);--cdk:{darken(c)};--cbgl:rgba({r},{g},{b},.16)}}")
    return "\n".join(out)


def build(data: dict, now: dt.datetime, week_start: dt.date | None = None) -> str:
    m = Model(data, now, week_start)
    meta = m.meta
    last = meta.get("last_updated") or now.isoformat(timespec="seconds")
    last_dt = dt.datetime.fromisoformat(last).astimezone(ZoneInfo(meta.get("timezone", "America/Denver")))
    last_label = f"{DOW[last_dt.weekday()]}, {last_dt:%b} {last_dt.day} \u00b7 {fmt_time(last_dt.strftime('%H:%M'))} {meta.get('tz_label', 'MT')}"
    days_html = "".join(render_day(m, day) for day in m.days())
    later_html = "".join(render_later(m, day) for day in m.days() if day > m.week_end)
    rest_html = "".join(render_mini_day(m, day) for day in m.days() if day < m.week_start)
    acad_html, acad_sub = render_academics(m)
    tpl = (HERE / "template.html").read_text()
    repl = {
        "TITLE": esc(meta.get("family_name", "Family")),
        "FAMILY": esc(meta.get("family_name", "Family")),
        "THEME": esc(meta.get("theme", "light")),
        "TZ": esc(meta.get("timezone", "America/Denver")),
        "TZLABEL": esc(meta.get("tz_label", "MT")),
        "LAST_ISO": esc(last),
        "LAST_LABEL": esc(last_label),
        "STALE_DAYS": esc(meta.get("stale_after_days", 8)),
        "WEEK_START": m.week_start.isoformat(),
        "WEEK_END": m.week_end.isoformat(),
        "WEEK_LABEL": esc(week_label(m.week_start)),
        "MOTTO": (f'<div class="motto">{esc(meta.get("motto"))}</div>' if meta.get("motto") else ""),
        "REST": rest_html,
        "STATUS_BAR": "default" if meta.get("theme", "light") == "light" else "black-translucent",
        "THEME_COLOR": "#ffffff" if meta.get("theme", "light") == "light" else "#15120f",
        "BUILD_DATE": m.today.isoformat(),
        "PERSON_CSS": person_css(m),
        "DAYS": days_html,
        "LATER": later_html,
        "LATER_DAYS": esc(m.later_days),
        "ACADEMICS": acad_html,
        "YOUTH": render_youth(m),
        "YOUTH_NOTE": (f'<span class="ynote">{esc((m.data.get("youth") or {}).get("note", ""))}</span>'
                       if (m.data.get("youth") or {}).get("note") else ""),
        "YOUTH_DAYS": esc((m.data.get("youth") or {}).get("days", 7)),
        "YOUTH_LATER": esc((m.data.get("youth") or {}).get("later_days", 14)),
        "ACAD_SUB": acad_sub,
        "SPIRITUAL": render_spiritual(m),
        "TODOS": render_todos(m),
        "ICON_THEME": ICONS["theme"],
        "ICON_BELL": ICONS["bell"],
        "ICON_BOOK": ICONS["book"],
        "ICON_CAP": ICONS["cap"],
        "ICON_CAL": ICONS["cal"],
        "ICON_KIDS": ICONS["kids"],
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled template slots: {left}")
    return out


# ------------------------------------------------------------------ v2 (two rotating pages)
# v2/index.html: page 1 "Today" (today/tomorrow per person, full spiritual focus, heads-up) and
# page 2 "This week" (calendar, Young Men, grades). Same data, same helpers as v1.

V2_ROWS_FAMILY = ("parents", "family")


def _item_line(m: Model, e: dict, show_chips: bool, tag: str = "") -> str:
    t = fmt_time(e.get("start"))
    t2 = f"\u2013{fmt_time(e['end'])}" if e.get("end") and e.get("start") else ""
    when = (f'<span class="tw">{esc(t)}<small>{esc(t2)}</small></span>' if t
            else '<span class="tw allday">All day</span>')
    if e.get("kind") == "youth":
        when = (f'<span class="tw">{esc(t)}</span>' if t else '<span class="tw allday">TBA</span>')
    ic = ICONS["plane"] if e.get("kind") == "flight" else ""
    title, note_txt = e.get("title") or "", e.get("note") or ""
    mo = re.match(r"^(.*?)\s*\(([^()]*)\)$", title)
    if mo and e.get("kind") != "youth":         # "MTB pre-ride, Herriman (plates required)" -> title + note
        title = mo.group(1)
        note_txt = mo.group(2)[:1].upper() + mo.group(2)[1:] + (f" \u00b7 {note_txt}" if note_txt else "")
    note = f'<span class="tn">{esc(note_txt)}</span>' if note_txt else ""
    tg = f'<span class="ttag">{esc(tag)}</span>' if tag else ""
    ch = f'<span class="who in">{chips(m, e.get("who", []))}</span>' if show_chips else ""
    return (f'<div class="ti pr-{esc(e.get("priority", "normal"))}">{when}<span class="tx">'
            f'<span class="tt2">{ic}{esc(title)}{tg}{ch}</span>{note}</span></div>')


def v2_rows(m: Model) -> list[dict]:
    rows = [{"id": k["id"], "name": k["name"], "sub": f'Grade {k.get("grade")}', "kid": k} for k in m.kids]
    rows.append({"id": "family", "name": "Family", "sub": "& parents", "kid": None})
    return rows


def v2_items_for(m: Model, row: dict, day: dt.date, yacts: list[dict]) -> list[tuple[dict, bool, str]]:
    """Items for one row/day: kid rows get single-kid items; the family row gets everything shared."""
    kid_ids = [k["id"] for k in m.kids]
    out = []
    half = m.flags_on(day)["half_day"]
    for e in m.events_on(day):
        if e.get("kind") == "trip" or e.get("flag") == "no_school" or e.get("priority") == "low":
            continue
        who = e.get("who", [])
        if e.get("flag") == "half_day":
            rest = re.sub(r"^(k-5 )?half day\s*(\u00b7|\u2014|-)?\s*", "", e.get("title", ""), flags=re.I)
            rest = re.sub(r"\s*\u00b7\s*spirit apparel( day)?$", "", rest, flags=re.I)
            if not rest or re.fullmatch(r"spirit apparel( day)?", rest, re.I):
                continue
            e = dict(e, title=rest[:1].upper() + rest[1:], flag=None)
        if ABSORB_RE.match(e.get("title", "")) and half and set(who) <= set(half):
            continue                                   # "Term 1 ends" is folded into the half-day status
        single = len(who) == 1 and who[0] in kid_ids
        if row["kid"] is not None and single and who[0] == row["id"]:
            out.append((e, False, ""))
        elif row["kid"] is None and not single:
            out.append((e, True, ""))
    for a in yacts:
        if a["date"] != day.isoformat() or a.get("kind") == "none":
            continue
        ev = {"title": a.get("title") + (" (tentative)" if a.get("tentative") else ""), "start": a.get("start"),
              "who": a["who"], "kind": "youth", "priority": "normal"}
        if row["kid"] is not None and len(a["who"]) == 1 and a["who"][0] == row["id"]:
            out.append((ev, False, "Young Men"))
        elif row["kid"] is None and len(a["who"]) > 1:
            out.append((ev, True, "Young Men"))
    out.sort(key=lambda x: (x[0].get("start") is not None, x[0].get("start") or ""))
    return out


def v2_status(m: Model, kid: dict, day: dt.date) -> str:
    cls, text = m.kid_status(kid, day)
    note = ""
    r = kid.get("routine")
    if cls == "inperson" and r:
        text = r.get("title", "In person")
        note = " \u00b7 ".join(x for x in (f'{fmt_time(r.get("start"))}\u2013{fmt_time(r.get("end"))}', r.get("note")) if x)
    if cls == "half":
        absorbed = [e["title"] for e in m.events_on(day) if not e.get("flag") and ABSORB_RE.match(e.get("title", ""))
                    and kid["id"] in e.get("who", [])]
        if absorbed:
            text += " \u00b7 " + " \u00b7 ".join(absorbed)
    if cls == "weekend":
        text = "Sunday" if day.weekday() == 6 else "Saturday"
    n = f'<span class="sn">{esc(note)}</span>' if note else ""
    return f'<div class="ts st-{cls}">{esc(text)}{n}</div>'


def render_today_grid(m: Model) -> str:
    yacts = youth_activities(m)
    rows = []
    for row in v2_rows(m):
        cells = []
        for day in m.days():
            parts = []
            if row["kid"] is not None and day.weekday() < 5 or (
                    row["kid"] is not None and row["id"] in m.flags_on(day)["no_school"]):
                parts.append(v2_status(m, row["kid"], day))   # weekends: no status line, just events
            else:
                trips = [e for e in m.events_on(day) if e.get("kind") == "trip"]
                if trips:
                    parts.append('<div class="ttrips">' + "".join(
                        f'<span class="trip">{ICONS["pin"]}{esc(t["title"])}</span>' for t in trips) + '</div>')
            items = v2_items_for(m, row, day, yacts)
            parts += [_item_line(m, e, ch, tag) for e, ch, tag in items]
            if not items and (row["kid"] is None or not parts):
                parts.append('<div class="tnone">Nothing scheduled</div>')
            cells.append(f'<div class="tc" data-date="{day.isoformat()}">{"".join(parts)}</div>')
        allc = "".join(cells)
        cls = f'p-{row["id"]}' if row["kid"] is not None else "p-family fam"
        rows.append(f'<div class="trow {cls}"><div class="tname"><b>{esc(row["name"])}</b><small>{esc(row["sub"])}</small></div>'
                    f'<div class="tcol c-today">{allc}</div><div class="tcol c-tmrw">{allc}</div></div>')
    return "".join(rows)


def render_spiritual_full(m: Model) -> str:
    sp = m.data.get("spiritual", {}) or {}
    cfm = sp.get("come_follow_me", {}) or {}
    fsy = sp.get("strength_of_youth", {}) or {}
    pending_cfm = cfm.get("status") == "pending" or not cfm.get("reading")
    meta = " \u00b7 ".join(x for x in (cfm.get("dates_label"), cfm.get("reading")) if x)
    qs = "".join(f"<li>{esc(q)}</li>" for q in (cfm.get("questions") or [])[:3])
    summary = cfm.get("summary") or ""
    cfm_html = (f'<div class="sp-block cfm{" pending" if pending_cfm else ""}">'
                f'<div class="sp-k">{ICONS["book"]}Come, Follow Me<span class="sp-wk">{esc(meta)}</span></div>'
                f'<div class="sp-title">{esc(cfm.get("title") or "This week&#39;s lesson is on its way")}</div>'
                + (f'<div class="sp-sum">{esc(summary)}</div>' if summary else "")
                + (f'<ol class="sp-q">{qs}</ol>' if qs else "") + '</div>')
    pending_fsy = fsy.get("status") == "pending" or not fsy.get("topic")
    daily = fsy.get("daily_by_weekday") or {}
    tips = "".join(f'<span class="tip" data-dow="{esc(k[:3].title())}">{esc(v)}</span>' for k, v in daily.items())
    tip_html = ""
    if tips:
        tip_html = (f'<div class="sp-tip t-today"><span class="lbl">Today</span>{tips}</div>'
                    f'<div class="sp-tip t-tmrw"><span class="lbl">Tomorrow</span>{tips}</div>')
    elif fsy.get("daily_application"):
        tip_html = f'<div class="sp-tip"><span class="lbl">Try today</span>{esc(fsy["daily_application"])}</div>'
    lbl = fsy.get("label") or ""
    fsy_html = (f'<div class="sp-block fsy{" pending" if pending_fsy else ""}">'
                f'<div class="sp-k">{ICONS["star"]}Strength of Youth<span class="sp-wk">{esc(lbl)}</span></div>'
                f'<div class="sp-title">{esc(fsy.get("topic") or "This month&#39;s chapter is on its way")}</div>'
                + (f'<div class="sp-focus">{esc(fsy["focus"])}</div>' if fsy.get("focus") else "")
                + (f'<div class="sp-quote">{esc(fsy["quote"])}</div>' if fsy.get("quote") else "")
                + tip_html + '</div>')
    return cfm_html + fsy_html


def render_todos_v2(m: Model) -> str:
    """Heads-up for v2 page 1: up to 5 (JS cap), with due date and the detail line."""
    todos = [t for t in (m.data.get("todos", []) or []) if not t.get("done")]
    prio = {"high": 0, "normal": 1, "low": 2}
    todos.sort(key=lambda t: (prio.get(t.get("priority", "normal"), 1), t.get("due") or "9999"))
    rows = []
    for t in todos:
        due = ""
        if t.get("due"):
            dd = d(t["due"])
            due = f'<span class="due">by {DOW[dd.weekday()]} {dd:%b} {dd.day}</span>'
        det = f'<span class="td">{esc(t.get("detail"))}</span>' if t.get("detail") else ""
        rows.append(
            f'<li class="todo pr-{esc(t.get("priority", "normal"))}" data-until="{esc(t.get("hide_after", ""))}">'
            f'<span class="box"></span><span class="tbody"><span class="tline"><span class="tt">{esc(t.get("text"))}</span>{due}</span>{det}</span>'
            f'<span class="who">{chips(m, t.get("who", []))}</span></li>')
    if not rows:
        return '<li class="todo none">All clear \u2014 nothing pending.</li>'
    return "".join(rows) + '<li class="todo none hidden-default">All clear \u2014 nothing pending.</li>'


def rem_to_var(css: str) -> str:
    """v2 sizes are authored in rem; turn them into per-page units so each page can auto-fit on its own."""
    return re.sub(r"(-?\d*\.?\d+)rem\b", lambda mo: f"calc(var(--fs) * {mo.group(1)})", css)


def build_v2(data: dict, now: dt.datetime, week_start: dt.date | None = None) -> str:
    m = Model(data, now, week_start)
    meta = m.meta
    last = meta.get("last_updated") or now.isoformat(timespec="seconds")
    last_dt = dt.datetime.fromisoformat(last).astimezone(ZoneInfo(meta.get("timezone", "America/Denver")))
    last_label = f"{DOW[last_dt.weekday()]}, {last_dt:%b} {last_dt.day} \u00b7 {fmt_time(last_dt.strftime('%H:%M'))} {meta.get('tz_label', 'MT')}"
    acad_html, acad_sub = render_academics(m)
    if 'acols nodata' in acad_html and not acad_sub:
        acad_sub = "Grades coming soon"                # v2 shows this once in the card header
    tpl = (HERE / "template_v2.html").read_text()
    i, j = tpl.index("<style>"), tpl.index("</style>")
    tpl = tpl[:i] + rem_to_var(tpl[i:j]) + tpl[j:]
    y = m.data.get("youth") or {}
    repl = {
        "TITLE": esc(f'{meta.get("family_name", "Family")} \u00b7 Dashboard'),
        "FAMILY": esc(meta.get("family_name", "Family")),
        "MOTTO": (f'<div class="motto">{esc(meta.get("motto"))}</div>' if meta.get("motto") else ""),
        "THEME": esc(meta.get("theme", "light")),
        "TZ": esc(meta.get("timezone", "America/Denver")),
        "TZLABEL": esc(meta.get("tz_label", "MT")),
        "LAST_ISO": esc(last_dt.isoformat()),
        "LAST_LABEL": esc(last_label),
        "STALE_DAYS": esc(meta.get("stale_after_days", 8)),
        "WEEK_START": m.week_start.isoformat(),
        "WEEK_END": m.week_end.isoformat(),
        "WEEK_LABEL": esc(week_label(m.week_start)),
        "STATUS_BAR": "default" if meta.get("theme", "light") == "light" else "black-translucent",
        "THEME_COLOR": "#ffffff" if meta.get("theme", "light") == "light" else "#15120f",
        "BUILD_DATE": m.today.isoformat(),
        "PERSON_CSS": person_css(m),
        "TODAY_GRID": render_today_grid(m),
        "SPIRITUAL": render_spiritual_full(m),
        "TODOS": render_todos_v2(m),
        "DAYS": "".join(render_day(m, day, inline_chips=True) for day in m.days()),
        "LATER": "".join(render_later(m, day) for day in m.days() if day > m.week_end),
        "LATER_DAYS": esc(m.later_days),
        "REST": "".join(render_mini_day(m, day) for day in m.days() if day < m.week_start),
        "YOUTH": render_youth(m),
        "YOUTH_NOTE": (f'<span class="ynote">{esc(y.get("note", ""))}</span>' if y.get("note") else ""),
        "YOUTH_DAYS": esc(y.get("days", 7)),
        "YOUTH_LATER": esc(y.get("later_days", 14)),
        "ACADEMICS": acad_html,
        "ACAD_SUB": acad_sub,
        "ROTATE_SECONDS": esc(meta.get("v2_rotate_seconds", 30)),
        "ICON_THEME": ICONS["theme"],
        "ICON_BELL": ICONS["bell"],
        "ICON_BOOK": ICONS["book"],
        "ICON_CAP": ICONS["cap"],
        "ICON_CAL": ICONS["cal"],
        "ICON_KIDS": ICONS["kids"],
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled v2 template slots: {left}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--out", default=str(HERE / "index.html"))
    ap.add_argument("--out-v2", default=str(HERE / "v2" / "index.html"),
                    help="where to write the rotating two-page v2 dashboard")
    ap.add_argument("--no-v2", action="store_true", help="skip the v2 page")
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
    Path(args.out).write_text(build(data, now, week_start))
    print(f"[build] wrote {args.out} (last_updated {data['meta'].get('last_updated')})")
    if not args.no_v2:
        out2 = Path(args.out_v2)
        out2.parent.mkdir(parents=True, exist_ok=True)
        out2.write_text(build_v2(data, now, week_start))
        print(f"[build] wrote {out2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
