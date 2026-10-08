#!/usr/bin/env python3
"""Render index.html (self-contained: inline CSS/JS, no external requests) from data/dashboard.json.

The page pre-renders every day from (build date - 1) through (build date + RANGE_DAYS) and a tiny
inline script shows only "today .. today + schedule_days - 1" (America/Denver), so a page built
once a week stays correct every day until the next build.

Usage: python3 build.py [--json data/dashboard.json] [--out index.html] [--no-stamp] [--now ISO]
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

class Model:
    def __init__(self, data: dict, now: dt.datetime):
        self.data = data
        self.now = now
        self.today = now.date()
        self.meta = data.get("meta", {})
        self.people = data.get("people", {})
        self.kids = data.get("kids", [])
        self.events = [e for e in data.get("events", []) if e.get("date")]
        self.first = self.today - dt.timedelta(days=1)
        self.last = self.today + dt.timedelta(days=RANGE_DAYS)

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


def render_item(m: Model, e: dict, day: dt.date) -> str:
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
    return (f'<li class="item k-{esc(kind)} pr-{esc(pri)}">'
            f'<div class="when">{time_html}</div>'
            f'<div class="what"><span class="title">{icon}{esc(e.get("title"))}</span>'
            f'{f"<span class=note>{esc(note)}</span>" if note else ""}</div>'
            f'<div class="who">{chips(m, e.get("who", []))}</div></li>')


def render_day(m: Model, day: dt.date) -> str:
    evs = m.events_on(day)
    trips = [e for e in evs if e.get("kind") == "trip"]
    flags = m.flags_on(day)
    # banners: group kids by flag + reason
    banners = []
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
                r = "Out at 12 PM"
            order = [k["id"] for k in m.kids]
            kids.sort(key=lambda k: order.index(k) if k in order else 99)
            banners.append(
                f'<div class="banner b-{flag}"><span class="bl">{label}</span>'
                f'<span class="br">{esc(r)}</span><span class="who">{chips(m, kids)}</span></div>')
    items = []
    for e in evs:
        if e.get("kind") == "trip":
            continue
        if e.get("flag") == "no_school":
            continue                                  # fully described by the banner
        if e.get("flag") == "half_day":
            rest = re.sub(r"^(k-5 )?half day\s*(\u00b7|\u2014|-)?\s*", "", e.get("title", ""), flags=re.I)
            if not rest:
                continue
            e = dict(e, title=rest[:1].upper() + rest[1:], flag=None,
                     priority="low" if re.match(r"spirit apparel", rest, re.I) else e.get("priority", "normal"))
        items.append(e)
    items += m.routine_items(day)
    items.sort(key=lambda e: (e.get("start") is not None, e.get("start") or "",
                              {"high": 0, "normal": 1, "low": 2}.get(e.get("priority", "normal"), 1)))
    trip_html = "".join(
        f'<span class="trip">{ICONS["pin"]}{esc(t["title"])}</span>' for t in trips)
    body = "".join(render_item(m, e, day) for e in items)
    wk = " weekend" if day.weekday() >= 5 else ""
    # no-JS fallback: pre-mark the initial window relative to the build date
    n_days = int(m.meta.get("schedule_days", 7))
    if m.today <= day < m.today + dt.timedelta(days=n_days):
        wk += " show"
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


def render_later(m: Model, day: dt.date) -> str:
    """One compact line per day for the 'Later' strip: only no-school/half-day + high-priority items."""
    flags = m.flags_on(day)
    parts = []
    if day.weekday() < 5:
        for flag, label in (("no_school", "No school"), ("half_day", "Half day")):
            groups: dict[str, list[str]] = {}
            for kid, reason in flags[flag].items():
                r = re.sub(r"^(no school|k-5 half day|half day)\s*(\u2014|\u00b7)?\s*", "", reason, flags=re.I)
                r = re.sub(r"\s*\u00b7\s*spirit apparel$", "", r)
                groups.setdefault(r if flag == "no_school" else "", []).append(kid)
            for r, kids in groups.items():
                txt = label + (f" \u00b7 {r}" if r else "")
                parts.append(f'<span class="li f-{flag}">{esc(txt)}{chips(m, kids)}</span>')
    for e in m.events_on(day):
        if e.get("flag") or e.get("kind") == "trip" or e.get("priority") != "high" or d(e["date"]) != day:
            continue
        parts.append(f'<span class="li">{esc(e.get("title"))}{chips(m, e.get("who", []))}</span>')
    if not parts:
        return ""
    return (f'<div class="later-row" data-date="{day.isoformat()}"><span class="ld">'
            f'{DOW[day.weekday()]} <b>{day:%b} {day.day}</b></span><span class="lis">{"".join(parts)}</span></div>')


def render_glance(m: Model, kid: dict) -> str:
    """'Kids at a glance' block for one kid: school, today/tomorrow status, next key dates."""
    statuses = []
    for day in m.days():
        cls, text = m.kid_status(kid, day)
        statuses.append(f'<span class="st st-{cls}" data-date="{day.isoformat()}">{esc(text)}</span>')
    st = "".join(statuses)
    keys = "".join(
        f'<div class="keyd" data-date="{day.isoformat()}"><b>{esc(fmt_day(day))}</b> {esc(txt)}</div>'
        for day, txt in m.key_dates(kid))
    keys = keys or '<div class="keyd none">No key dates on the calendar</div>'
    kin = f'<div class="kin">{esc(kid.get("in_person_summary", ""))}</div>' if kid.get("routine") else ""
    return (f'<div class="ksch">{esc(kid.get("school_short") or kid.get("school"))} \u00b7 {esc(kid.get("division"))}</div>'
            f'<div class="krow"><span class="lbl">Today</span><span class="stat today">{st}</span></div>'
            f'<div class="krow"><span class="lbl">Tmrw</span><span class="stat tmrw">{st}</span></div>'
            f'{kin}'
            f'<div class="krow next"><span class="lbl">Next</span><span class="keys">{keys}</span></div>')


def render_academics(m: Model) -> str:
    """Per-kid grades: courses (percent/letter), missing-work count, upcoming tests, optional screen time."""
    acad = m.data.get("academics", {}) or {}
    screen = m.data.get("screen_time", {}) or {}

    def mins(v):
        v = int(v)
        return f"{v // 60}h {v % 60:02d}m" if v >= 60 else f"{v}m"

    cols, any_data = [], False
    for kid in m.kids:
        kid_id = kid["id"]
        a = (acad.get("kids", {}) or {}).get(kid_id, {}) or {}
        courses = a.get("courses") or []
        tests = a.get("upcoming_tests") or []
        miss = a.get("missing_count")
        body = []
        if courses:
            any_data = True
            rows = []
            for c in courses:
                pct = c.get("percent")
                pct_s = f"{pct:.0f}%" if isinstance(pct, (int, float)) else ""
                letter = c.get("letter") or ""
                lc = "g-a" if letter[:1] == "A" else "g-b" if letter[:1] == "B" else "g-c" if letter[:1] == "C" else "g-d" if letter[:1] in "DF" and letter else ""
                rows.append(f'<div class="crs"><span class="cn">{esc(c.get("name"))}</span>'
                            f'<span class="cp">{esc(pct_s)}</span><span class="cl {lc}">{esc(letter)}</span></div>')
            body.append(f'<div class="courses">{"".join(rows)}</div>')
        else:
            body.append('<div class="soon">' + ICONS["cap"] + 'Grades coming soon</div>')
        if tests:
            any_data = True
            body.append('<div class="tests">' + "".join(
                f'<div class="test" data-until="{esc(t.get("date", ""))}"><b>{esc(fmt_day(d(t["date"])) if t.get("date") else "")}</b> '
                f'{esc(t.get("course", ""))}{": " if t.get("course") and t.get("title") else ""}{esc(t.get("title", ""))}</div>'
                for t in tests) + '</div>')
        if screen.get("enabled"):
            sdat = (screen.get("kids", {}) or {}).get(kid_id, {}) or {}
            parts = []
            if sdat.get("today_minutes") is not None:
                lim = f" / {mins(sdat['limit_minutes'])}" if sdat.get("limit_minutes") else ""
                parts.append(f"{mins(sdat['today_minutes'])}{lim} today")
            if sdat.get("daily_avg_minutes") is not None:
                parts.append(f"avg {mins(sdat['daily_avg_minutes'])}/day")
            if parts:
                any_data = True
                joined = esc(" \u00b7 ".join(parts))
                body.append(f'<div class="screen"><span class="lbl">Screen</span>{joined}</div>')
            elif courses:
                body.append('<div class="screen muted"><span class="lbl">Screen</span>coming soon</div>')
        miss_html = ""
        if miss is not None:
            any_data = True
            miss_html = f'<span class="miss {"ok" if not miss else "bad"}">{int(miss)} missing</span>'
        cols.append(f'<div class="acol p-{esc(kid_id)}"><div class="acol-h"><span class="aname">{esc(kid["name"])}</span>'
                    f'<span class="agrade">Grade {esc(kid.get("grade"))}</span>{miss_html}</div>'
                    f'{render_glance(m, kid)}<div class="agrades">{"".join(body)}</div></div>')
    upd = acad.get("updated")
    sub = ""
    if upd:
        try:
            u = dt.datetime.fromisoformat(upd)
            sub = f"as of {DOW[u.weekday()]} {u:%b} {u.day}"
        except ValueError:
            sub = esc(upd)
    elif not any_data:
        sub = "grades coming soon"
    return f'<div class="acols{"" if any_data else " nodata"}">{"".join(cols)}</div>', sub


def render_spiritual(m: Model) -> str:
    sp = m.data.get("spiritual", {}) or {}
    cfm = sp.get("come_follow_me", {}) or {}
    fsy = sp.get("strength_of_youth", {}) or {}
    pending_cfm = cfm.get("status") == "pending" or not cfm.get("reading")
    qs = "".join(f"<li>{esc(q)}</li>" for q in (cfm.get("questions") or [])[:3])
    cfm_html = f'''
<div class="sp-block{' pending' if pending_cfm else ''}">
  <div class="sp-k">{ICONS["book"]}Come, Follow Me{f' <span class="sp-wk">{esc(cfm.get("dates_label"))}</span>' if cfm.get("dates_label") else ''}</div>
  <div class="sp-title">{esc(cfm.get("title") or "This week's lesson is on its way")}</div>
  {f'<div class="sp-read"><span class="lbl">Read</span>{esc(cfm.get("reading"))}</div>' if cfm.get("reading") else ''}
  {f'<div class="sp-sum">{esc(cfm.get("summary"))}</div>' if cfm.get("summary") else ''}
  {f'<ol class="sp-q">{qs}</ol>' if qs else ('<div class="sp-wait">Reading &amp; discussion questions arrive with the weekly update.</div>' if pending_cfm else '')}
</div>'''
    pending_fsy = fsy.get("status") == "pending" or not fsy.get("focus")
    daily = fsy.get("daily_by_weekday") or {}
    daily_html = "".join(
        f'<div class="sp-daily-d" data-dow="{esc(k[:3].title())}"><span class="lbl">Today</span>{esc(v)}</div>'
        for k, v in daily.items())
    if fsy.get("daily_application"):
        daily_html += f'<div class="sp-daily-all"><span class="lbl">Try today</span>{esc(fsy["daily_application"])}</div>'
    fsy_html = f'''
<div class="sp-block{' pending' if pending_fsy else ''}">
  <div class="sp-k">{ICONS["star"]}For the Strength of Youth</div>
  <div class="sp-title">{esc(fsy.get("topic") or "This week's focus is on its way")}</div>
  {f'<div class="sp-sum">{esc(fsy.get("focus"))}</div>' if fsy.get("focus") else ''}
  {f'<div class="sp-daily">{daily_html}</div>' if daily_html else ('<div class="sp-wait">Daily application arrives with the weekly update.</div>' if pending_fsy else '')}
</div>'''
    return cfm_html + fsy_html


def render_todos(m: Model) -> str:
    rows = []
    for t in m.data.get("todos", []) or []:
        if t.get("done"):
            continue
        due = ""
        if t.get("due"):
            dd = d(t["due"])
            due = f'<span class="due">by {DOW[dd.weekday()]} {dd:%b} {dd.day}</span>'
        rows.append(
            f'<li class="todo pr-{esc(t.get("priority", "normal"))}" data-until="{esc(t.get("hide_after", ""))}">'
            f'<span class="box"></span><div class="tw"><div class="tt">{esc(t.get("text"))}</div>'
            f'<div class="td">{esc(t.get("detail", ""))}{due}</div></div>'
            f'<div class="who">{chips(m, t.get("who", []))}</div></li>')
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


def build(data: dict, now: dt.datetime) -> str:
    m = Model(data, now)
    meta = m.meta
    last = meta.get("last_updated") or now.isoformat(timespec="seconds")
    last_dt = dt.datetime.fromisoformat(last).astimezone(ZoneInfo(meta.get("timezone", "America/Denver")))
    last_label = f"{DOW[last_dt.weekday()]}, {last_dt:%b} {last_dt.day} \u00b7 {fmt_time(last_dt.strftime('%H:%M'))} {meta.get('tz_label', 'MT')}"
    days_html = "".join(render_day(m, day) for day in m.days())
    later_html = "".join(render_later(m, day) for day in m.days())
    acad_html, acad_sub = render_academics(m)
    tpl = (HERE / "template.html").read_text()
    repl = {
        "TITLE": esc(meta.get("family_name", "Family")),
        "FAMILY": esc(meta.get("family_name", "Family")),
        "THEME": esc(meta.get("theme", "dark")),
        "TZ": esc(meta.get("timezone", "America/Denver")),
        "TZLABEL": esc(meta.get("tz_label", "MT")),
        "LAST_ISO": esc(last),
        "LAST_LABEL": esc(last_label),
        "STALE_DAYS": esc(meta.get("stale_after_days", 8)),
        "SCHED_DAYS": esc(meta.get("schedule_days", 10)),
        "BUILD_DATE": m.today.isoformat(),
        "PERSON_CSS": person_css(m),
        "DAYS": days_html,
        "LATER": later_html,
        "LATER_DAYS": esc(meta.get("later_days", 7)),
        "ACADEMICS": acad_html,
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    ap.add_argument("--out", default=str(HERE / "index.html"))
    ap.add_argument("--no-stamp", action="store_true", help="don't update meta.last_updated")
    ap.add_argument("--now", help="override build time (ISO) for testing")
    args = ap.parse_args()

    path = Path(args.json)
    data = json.loads(path.read_text())
    tz = ZoneInfo(data.get("meta", {}).get("timezone", "America/Denver"))
    now = dt.datetime.fromisoformat(args.now).astimezone(tz) if args.now else dt.datetime.now(tz)
    if not args.no_stamp:
        data.setdefault("meta", {})["last_updated"] = now.isoformat(timespec="seconds")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)
    Path(args.out).write_text(build(data, now))
    print(f"[build] wrote {args.out} (last_updated {data['meta'].get('last_updated')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
