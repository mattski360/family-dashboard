# Jensen Family wall dashboard

A static page (`index.html`, with CSS and JS inline and no external requests) for a wall-mounted iPad. It is portrait-first (820×1180) and also works in landscape (1180×820).
To publish, put `index.html` and `assets/` on GitHub Pages.

```
./run.sh                 # fetch_school.py (AHS Veracross ICS → data/dashboard.json), then build.py → index.html
python3 build.py         # re-render only (stamps meta.last_updated)
python3 build.py --no-stamp
python3 fetch_school.py --dry-run [--days 21] [--today 2026-10-08]
/workspace/.venv-shot/bin/python shot.py   # preview.png (portrait) + preview-landscape.png
```
Requirements: Python 3.9+ standard library only (zoneinfo). Screenshots use playwright with the system Chrome.

## How it behaves
* `build.py` pre-renders every day from (build date − 1) to (build date + 24). The inline JS shows **today + the next 6 days** (`meta.schedule_days`). It also shows a compact "Later" list of key items for the following `meta.later_days`. All of this is computed in America/Denver time, so a page built once a week stays correct every day. JS also highlights today and labels tomorrow, and hides heads-up items and tests whose dates have passed.
* The page reloads every 30 minutes through `<meta http-equiv=refresh content=1800>`. A JS fallback reloads at about 30.3 minutes with a cache-busting `?r=` query.
* "Last updated" comes from `meta.last_updated`. It turns amber and shows "Needs refresh" when it is older than `meta.stale_after_days` (8).
* The page uses as large a font as still fits on one screen without scrolling.
* Tap the moon button to switch between dark and light. The choice is saved per device. The default comes from `meta.theme`.

## data/dashboard.json
| key | what |
|---|---|
| `meta` | `family_name`, `timezone`, `tz_label`, `theme` (`dark`/`light`), `schedule_days` (7), `later_days` (8), `stale_after_days` (8), `last_updated` (set by build.py), `school_feed_synced` and `school_feed_window` (set by fetch_school.py) |
| `people` | chip id → `{label, color}`: `luke`, `wyatt`, `tanner`, `parents`, `family` |
| `kids[]` | `id, name, grade, school, school_short, campus, division, in_person_days, in_person_summary`. `routine` (Wyatt only): `{days:["Tue","Thu"], start, end, title, note, online_title}` adds the "In person at Lehi campus" line automatically on those days unless Wyatt has no school |
| `events[]` | calendar items (see below) |
| `todos[]` | `{id, text, detail, who[], due, hide_after, priority, done}`. Items are hidden after `hide_after` or when `done: true` |
| `spiritual` | see below |
| `academics` | `updated` (ISO), `kids.<id>.courses[] {name, percent, letter}`, `missing_count` (int or null), `upcoming_tests[] {date, course, title}` (hidden once past), `note`. With empty courses the page shows "Grades coming soon" |
| `screen_time` | `enabled` (bool), `updated`, `kids.<id> {today_minutes, daily_avg_minutes, limit_minutes}`. Null values show "coming soon" |

### Adding a calendar event
```json
{"id": "fam-20261025-dinner", "date": "2026-10-25", "end_date": null,
 "start": "18:00", "end": "19:30",
 "title": "Ward Trunk-or-Treat", "note": "Church parking lot",
 "who": ["family"], "priority": "high", "kind": "event", "source": "family"}
```
* `date` / `end_date`: YYYY-MM-DD. `end_date` is inclusive and optional, for multi-day items. `start` / `end`: 24-hour `HH:MM` in MT. Leave them out for all-day items.
* `who`: any of `luke`, `wyatt`, `tanner`, `parents`, `family`.
* `flag`: `"no_school"` shows a red NO SCHOOL banner on that day for those kids. `"half_day"` shows an amber HALF DAY · out at 12 PM banner.
* `priority`: `high` items appear in each kid's "Next" line and in the Later list. `low` items render small and dim.
* `kind`: `event`, `flight` (adds a plane icon), `trip` (adds a location pill to every day it covers), or `school`.
* `source`: `ahs_feed` is reserved. **fetch_school.py replaces every `ahs_feed` event on each run.** Use any other source (`family`, `canyon_grove`, `ahs_manual`, …) for hand-entered items. Those are never touched.

### Spiritual focus (filled weekly by the research job)
```json
"spiritual": {
  "come_follow_me": {"status": "ready", "week_of": "2026-10-12", "dates_label": "Oct 12–18",
    "title": "…", "reading": "…", "summary": "…", "questions": ["…", "…", "…"], "source_url": "…"},
  "strength_of_youth": {"status": "ready", "topic": "…", "focus": "…",
    "daily_application": "…", "daily_by_weekday": {"Mon": "…", "Tue": "…"}, "source_url": "…"}
}
```
When `status` is `"pending"`, or there is no reading (CFM) or focus (FSY), the card shows the placeholder title in muted italics with a pulsing dot. `daily_by_weekday` (Mon to Sun) shows only today's entry. Without it, `daily_application` is shown.

## School feed filtering (fetch_school.py)
Kept: school-wide items (no school, half days, term start/end, grades posted, picture retakes), HS items for grade 9 (Luke), ES items for K-5, generic ES, or grade 5 (Tanner), spirit-apparel days (low priority), and parent events.
Dropped: middle school, other grades, kindergarten, clubs, rehearsals, athletics, senior nights, AP/ACT/PSAT for other grades, admissions, and faculty items.
No-school entries on weekends are skipped. When the band named in "No School K-8" or a similar phrase covers only some of the kids, the event is split into a no-school item for the kids it covers and a separate item for the others.
The default window is **21 days**, so a weekly run still fills the 7-day view plus the Later list all week. Use `--days 14` if you want a shorter window.
