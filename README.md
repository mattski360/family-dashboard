# Jensen Family wall dashboard

A static page (`index.html`, with CSS and JS inline and no external requests) for a wall-mounted iPad. It is portrait-first (820×1180) and also works in landscape (1180×820).
To publish, put `index.html` and `assets/` on GitHub Pages.

There are three versions, all rendered by `build.py` from the same `data/dashboard.json`, so the weekly `run.sh` rebuild updates all of them:
* **v1** – `index.html` (template `template.html`): everything on one screen. Live at https://mattski360.github.io/family-dashboard/
* **v2** – `v2/index.html` (template `template_v2.html`): two full-screen pages that crossfade every 30 seconds, with larger text. Live at https://mattski360.github.io/family-dashboard/v2/ (see "Version 2" below).
* **v3** – `v3/index.html` (template `template_v3.html` + icon sprite `v3_sprite.svg`): "two soft pages", pastel rounded cards with big icons. Live at https://mattski360.github.io/family-dashboard/v3/ (see "Version 3" below).

```
./run.sh                 # fetch_school.py (AHS ICS) + fetch_youth.py (ward site, fallback) → data/dashboard.json, then build.py → index.html + v2/index.html + v3/index.html
python3 build.py [--week-start 2026-10-18]   # re-render only (stamps meta.last_updated, sets meta.week_start)
python3 build.py --no-stamp
python3 build.py --no-v2 --no-v3              # v1 only (--out-v2 / --out-v3 PATH to write them elsewhere)
python3 fetch_school.py --dry-run [--days 21] [--today 2026-10-08]
/workspace/.venv-shot/bin/python shot.py   # preview.png (portrait) + preview-landscape.png
/workspace/.venv-shot/bin/python shot_v2.py [--at 2026-10-14T07:00:00-06:00] [--landscape]   # preview-v2-p1.png + preview-v2-p2.png
/workspace/.venv-shot/bin/python shot_v3.py [--at 2026-10-08T07:20:00-06:00] [--landscape]   # preview-v3-p1.png + preview-v3-p2.png
```
Requirements: Python 3.9+ standard library only (zoneinfo). Screenshots use playwright with the system Chrome.

## How it behaves
* **Fixed Sunday-to-Saturday week.** The calendar shows `meta.week_start` through week_start + 6. The page is meant to be rebuilt every Saturday at 9 PM MT for the week that starts the next day.
  * build.py works out week_start as the upcoming Sunday: Mon–Sat give the next Sunday, and a Sunday gives that same day.
  * `--week-start YYYY-MM-DD` overrides it. Either way, the value used is written back to `meta.week_start`.
* **"Rest of this week" strip.** When the page is viewed before week_start (an off-cycle build, like Thu Oct 8 for the week of Oct 11), a one-line strip above the calendar shows the remaining days of the current week (low-priority items omitted, titles shortened).
* **Later list.** It covers the 8 days after the week (`meta.later_days`) and shows only key items.
* **Today.** JS highlights today, labels tomorrow and dims past days, all in America/Denver time. Heads-up items and tests hide once their dates pass.
* **Youth card.** It rolls with the viewing date: one line per boy (his quorum's items for today plus 6 days), one shared "Both" line for all-youth items, then a compact Later line for the next 14.
* **No grades section** (removed Oct 8, 2026 at Matt's request); the calendar and other cards use the space.
* **Heads-up.** At most 3 items (high priority first, then soonest due), one line each; the `detail` field is kept in JSON but not rendered.
* **Motto.** `meta.motto` renders as an italic tagline under the family name.
* **One screen.** Auto-fit picks the largest base font that fits (floor 13px portrait / 12.4px landscape); gentle auto-scroll only kicks in if content can't fit at the floor.
* **Refresh.** `<meta http-equiv=refresh content=1800>` reloads the page every 30 minutes. A JS fallback reloads with a cache-busting `?r=` query.
* **Last updated.** "Last updated" comes from `meta.last_updated`. It turns amber with "Needs refresh" when older than `meta.stale_after_days` (8).
* **Theme.** It defaults to a light theme on a white background (`meta.theme`: `light` or `dark`). The moon button toggles the theme, and the choice is saved per device.

## data/dashboard.json
| key | what |
|---|---|
| `meta` | `family_name`, `timezone`, `tz_label`, `theme` (`light`/`dark`), `week_start` (Sunday, written by build.py), `later_days` (8), `stale_after_days` (8), `last_updated` (set by build.py), `school_feed_synced` and `school_feed_window` (set by fetch_school.py) |
| `people` | chip id → `{label, color}`: `luke`, `wyatt`, `tanner`, `parents`, `family` |
| `kids[]` | `id, name, grade, school, school_short, campus, division, in_person_days, in_person_summary`, and optionally `glance_line`, which overrides the school line in the kids card. `routine` (Wyatt only): `{days:["Tue","Thu"], start, end, title, note, online_title}` adds the "In person at Lehi campus" line automatically on those days unless Wyatt has no school |
| `events[]` | calendar items (see below) |
| `youth` | Young Men activities (see below). v1/v2 show them only in the Young Men card, never in the weekly calendar. v3 tags them YM / All youth on the boy's Today and Tomorrow lines and on the week-tile for that day |
| `todos[]` | `{id, text, detail, who[], due, hide_after, priority, done}`. Items are hidden after `hide_after` or when `done: true` |
| `spiritual` | see below |
| `academics` | `updated` (ISO), `kids.<id>.courses[] {name, percent, letter}`, `missing_count` (int or null), `upcoming_tests[] {date, course, title}` (hidden once past), `note`. Not rendered on any page (grades section removed) |
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
* `priority`: `low` items are **not rendered** (keeps the portrait view on one screen; flip `HIDE_LOW` in build.py to show them). The Later list shows only no-school/half-day flags, `high` non-feed items, feed items about terms/quarters beginning or ending, and any event with `"major": true`. A same-day "Term N ends" note is folded into the HALF DAY banner when it covers the same kids.
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
Optional fields:
* `come_follow_me.previous`: `{show_before, dates_label, title, reading}` renders a one-line "Finishing …" note for the lesson still in progress. It hides automatically on or after `show_before`.
* `strength_of_youth.label`: for example "October chapter".
* `strength_of_youth.quote`: a short line quoted from the guide.

**Rendered (compact):** CFM shows the title, `dates_label · reading`, and ONE question (`featured_question`, a 0-based index into `questions`; default 0). FSY shows the `topic` plus today's `daily_by_weekday` tip. `summary`, the other questions, `focus`, `quote` and `previous` stay in the JSON but are not rendered.

When `status` is `"pending"`, or there is no reading (CFM) or focus (FSY), the card shows the placeholder title in muted italics with a pulsing dot. `daily_by_weekday` (Mon to Sun) shows only today's entry. Without it, `daily_application` is shown.

## School feed filtering (fetch_school.py)
Kept: school-wide items (no school, half days, term start/end, grades posted, picture retakes), HS items for grade 9 (Luke), ES items for K-5, generic ES, or grade 5 (Tanner), spirit-apparel days (low priority), and parent events.
Dropped: middle school, other grades, kindergarten, clubs, rehearsals, athletics, senior nights, AP/ACT/PSAT for other grades, admissions, and faculty items.
No-school entries on weekends are skipped. When the band named in "No School K-8" or a similar phrase covers only some of the kids, the event is split into a no-school item for the kids it covers and a separate item for the others.
The default window is **21 days**, so a weekly run still fills the 7-day view plus the Later list all week. Use `--days 14` if you want a shorter window.

## Young Men this week (`youth`)
```json
"youth": {"updated": "2026-10-07", "source": "H43 YW + YM Activities 2025 (Google Sheet, 2026 tab)",
  "note": "From the ward youth activities sheet; times/locations usually come by ward email/WhatsApp.",
  "quorums": {"luke": "teachers", "wyatt": "deacons"}, "days": 7, "later_days": 14,
  "activities": [{"id": "yth-20261029-teachers-mtc", "date": "2026-10-29", "start": null, "end": null,
     "title": "MTC tour?", "group": "teachers", "kind": "activity", "tentative": true,
     "location": null, "bring": null, "note": null, "source": "sheet"}]}
```
* `group` is one of `all_youth`, `all_ym`, `deacons`, `teachers`, `priests` or `yw`. `all_youth` and `all_ym` tag both boys, `teachers` tags Luke and `deacons` tags Wyatt. Priests and YW items are not shown.
* `kind: "none"` shows a muted line such as "Fall break — no activity" or "Nothing listed for Deacons". Items with no `start` show **Time TBA**.
* The card lists today plus the next 6 days, and a "Later" line for the following 14 days. Past entries hide automatically based on the viewing date.
* Precedence: items with `source` `sheet` or `manual` (the ward Google Sheet, refreshed separately) always win. `fetch_youth.py` parses the ward site's "<Month> Youth Activities" list for this month and next and stores the results as `source: "site"`. Each run replaces only the earlier `site` items. build.py shows a site item only on dates that have no sheet or manual items, and only if its title doesn't repeat a sheet item within 3 weeks. If the fetch fails or nothing parses, the JSON is left unchanged and the build continues.
* Raw sheet exports (`data/youth_sheet*`) are git-ignored, so they are never published.

## Fitting on screen
The page uses the largest text size that fits on one screen. It never goes below about 13px in portrait (820×1180) or 12.4px in landscape. If the content still doesn't fit at that size, the page scrolls vertically instead of shrinking further. On the wall it scrolls itself gently: it holds at the top for 40 seconds, glides down, holds for 20 seconds, then glides back. Any touch pauses this for 2 minutes.

## Version 2 (`v2/index.html`, rotating pages)
Portrait 820×1180 is the target. It uses the same light theme, colors and chips as v1, and the family motto (`meta.motto`) appears in the header of both pages.

**Page 1 – Today**
* Header: name, motto, large clock and date, last updated.
* **Today & tomorrow** grid with one row each for Luke, Wyatt, Tanner and Family & parents, and two columns: today (highlighted) and tomorrow, computed from the viewing date in America/Denver.
  * Kid rows show the school status on weekdays (no school / half day, with "Term N ends" folded in / in person at Lehi with times and the packing note / online / school day), then that kid's own events, each with a time and a note. A parenthetical in a title moves to the note line.
  * Youth activities for one boy are tagged "Young Men".
  * Anything involving two or more people (including all-youth activities), plus trips, goes in the Family row with chips.
  * Low-priority items are hidden, the same as in v1.
* **Spiritual focus, in full:**
  * Come, Follow Me: title, dates · reading, summary, and all questions.
  * Strength of Youth: chapter, focus, quote, and the daily tip for today and tomorrow.
* **Heads-up:** up to 5 open to-dos, each with its due date and detail line.

**Page 2 – This week**
* Compact header (name, motto, clock). The last-updated line appears here only when the data is stale.
* **Calendar:** the Sun–Sat week as an agenda, one full-width row per day with the date and trip pins in a left gutter and items in two columns.
  * Filtering is the same as v1: low-priority items are hidden, and no-school and half-day items become banners.
  * Chips flow right after each title.
  * Item notes show only for high-priority items.
  * The "Rest of this week" strip appears only before `week_start`, and the Later line is the same as v1.
* **Young Men:** one line per boy, a shared "Both" line, and Later.

**Rotation**
* Pages crossfade every `meta.v2_rotate_seconds` (default 30).
* The bottom bar shows page dots, a label such as "1 of 2 · Today", and a thin progress bar.
* Tapping anywhere switches pages and pauses rotation for 2 minutes (the bar turns amber and the label says "paused"). Tapping a dot jumps to that page.
* The current page, when it was shown, and the pause deadline are saved in `localStorage` (`dash-v2-rot`), so the 30-minute reload (meta refresh plus JS fallback) picks up where it left off.

**Fitting**
* CSS sizes are written in `rem`, and `build.py` rewrites them to `calc(var(--fs) * n)`. That lets each page auto-fit its own base size `--fs`, with a minimum of 16px in portrait (13px in landscape) and a maximum of 25px. Leftover height is spread evenly between the cards.
* A page that can't fit at the minimum scrolls on its own.
* `body[data-fs]` reports the result, for example `p1:18.11 p2:17.56 820x1180`.

## Version 3 (`v3/index.html`, two soft pages)
Built from mockup B. Portrait 820×1180 is the target; light white theme, rounded type (SF Pro Rounded on iPad). Both pages share the same header: "Jensen Family" + motto on the left; clock, a large date ("**Thursday**, October 8", weekday in amber) and a small "Updated …" line on the right (amber "needs refresh" when stale). The header uses the smaller of the two pages' fitted sizes so it looks identical on both.

**Page 1 – Today**
* One pastel card per kid (Luke blue, Wyatt green, Tanner orange) with name, grade and quorum. Today's items each get an icon bubble: school status (school day / no school with reason / half day with "Term N ends" folded in / Wyatt's Lehi campus day with times plus his packing note / online day), the kid's own and shared events (time and note on a small line), and youth activities with a **YM** tag (quorum / all YM) or an **All youth** tag. The same tag is repeated in the **Tomorrow** box. Weekends with nothing show "Free day". There is no separate Young Men card; that space goes to larger kid cards and the scripture boxes.
* A slim lavender **Parents** strip appears only when parents-only items (flights, away days) fall today or tomorrow.
* **Come, Follow Me**: dates, lesson title and reading, then a larger white **Today** box with today's scripture reference, a short quote and a thought from `come_follow_me.daily`. **Strength of Youth**: chapter title, "Ch. N · label", today's tip large in a white box, tomorrow's tip underneath.
* (No Heads-up section in v3; to-dos still show in v1 and v2.)

**Daily spiritual items** – `spiritual.come_follow_me.daily` is a Mon–Sun list (`{"dow": "Mon", "scripture": "Isaiah 58:6–7", "quote": "…", "thought": "…"}`) for the CFM week in `week_of`; `strength_of_youth.daily_by_weekday` has one tip per weekday. All seven of each are rendered with `data-dow` and the page's `applyDay()` shows the one matching the iPad's date (America/Denver), so they advance each morning without a rebuild. If no CFM item matches today, the featured question is shown instead. **Replace `daily` on every Saturday refresh** with the next lesson's queue (and `daily_by_weekday` when the FSY chapter changes monthly).

**Page 2 – This week**
* Ten colourful day tiles starting today (Thu Oct 8 → Sat Oct 17 style), now using the full page height. Youth activities are calendar items on their day, tagged **YM** (one boy) or **All youth** (shared), kid-coloured or yellow with dots. Each item gets an icon and a short label: kid-coloured when it's one kid, yellow with kid-colour dots when shared. No-school and half-day show as red / yellow items with dots; a weekday when every kid is on a break becomes a big mint "Fall break" tile. Up to 6 items per tile, then "+N more". Away days carry a lavender state tag (trip titles are reduced to "Arizona" / "California").

**Rotation & fitting** – same behaviour as v2: crossfade every `meta.v3_rotate_seconds` (falls back to `v2_rotate_seconds`, default 30); tap switches page and pauses 2 minutes with a "Paused (m:ss) · tap to resume" pill; progress bar; state in `localStorage` (`dash-v3-rot`). Sizes are authored in rem (1rem = 1/18 of the mockup's px) and auto-fit per page between 15px and 21px (portrait), and page 2 also stops growing before a tile label's longest word would be wider than its tile; `body[data-fs]` reports the result. The top padding clears the iPad status bar and the page-dot footer is a solid white strip, so nothing sits under it.

**Surprise guard** – `data/private_hide.txt` (git-ignored) filters events, to-dos and youth items for every version. v3 also checks its finished HTML for those terms and refuses to write `v3/index.html` (exit 3) if any slip through.

