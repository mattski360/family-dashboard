# Jensen Family wall dashboard

A static page (`v3/index.html`, with CSS and JS inline and no external requests) for a wall-mounted iPad, portrait-first (820×1180; landscape 1180×820 also fits). Published with GitHub Pages from `main`.

Live: https://mattski360.github.io/family-dashboard/v3/ (the iPad's URL).
The root URL (`index.html`) and the old `/v2/` URL (`v2/index.html`) are small static redirect pages to `v3/` (meta refresh + `location.replace`); they are committed as-is and not rebuilt. The earlier v1 and v2 layouts were retired in October 2026 (see git history).

`build.py` renders `v3/index.html` from `data/dashboard.json` using `template_v3.html` + the icon sprite `v3_sprite.svg`.

```
./run.sh                 # fetch_school.py (AHS ICS) + fetch_youth.py (ward site, fallback) + fetch_byu.py (BYU games) → data/dashboard.json, then build.py → v3/index.html
python3 build.py [--week-start 2026-10-18]   # re-render only (stamps meta.last_updated, sets meta.week_start)
python3 build.py --no-stamp [--out PATH]
python3 fetch_school.py --dry-run [--days 21] [--today 2026-10-08]
python3 fetch_byu.py --dry-run [--source official|espn]   # list BYU football + men's basketball games without saving
/workspace/.venv-shot/bin/python shot_v3.py [--at 2026-10-08T07:20:00-06:00] [--landscape]   # preview-v3-p1.png + preview-v3-p2.png
/workspace/.venv-shot/bin/python check_grades.py   # hidden grades card test (exit 1 on failure) + preview-grades.png
EGG_ANSWERS=a,b,c /workspace/.venv-shot/bin/python check_egg.py   # hidden $20 riddle test (answers passed in, never stored)
```
Requirements: Python 3.9+ standard library only (zoneinfo). Screenshots use playwright with the system Chrome.
`run.sh` exits 1 if a fetch failed (page still rebuilt) and 2 if the build failed, including when build.py refuses to write because of the surprise guard (build.py itself exits 3).

## Week and dates
* `meta.week_start` is the Sunday of the week being prepared. The page is meant to be rebuilt every Saturday at 9 PM MT. build.py sets it to the upcoming Sunday (Mon–Sat give the next Sunday, a Sunday gives that same day); `--week-start YYYY-MM-DD` overrides it. Either way the value is written back to `meta.week_start`.
* Items are rendered for a range around the build date, and the page's script picks today, tomorrow and the ten day tiles from the iPad's date (America/Denver), so the page keeps rolling between rebuilds.

## The page (`v3/index.html`, two soft pages)
Portrait 820×1180 is the target; light white theme, rounded type (SF Pro Rounded on iPad). Both pages share the same header: "Jensen Family" + motto on the left; clock, a large date ("**Thursday**, October 8", weekday in amber) and a small "Updated …" line on the right (amber "needs refresh" when stale). The header uses the smaller of the two pages' fitted sizes so it looks identical on both.

**Page 1 – Today**
* One pastel card per kid (Luke blue, Wyatt green, Tanner orange) with name, grade and quorum. Today's items each get an icon bubble: school status (school day / no school with reason / half day with "Term N ends" folded in / Wyatt's Lehi campus day with times plus his packing note / online day), the kid's own and shared events (time and note on a small line), and youth activities with a **YM** tag (quorum / all YM) or an **All youth** tag. The same tag is repeated in the **Tomorrow** box. Weekends with nothing show "Free day". There is no separate Young Men card; that space goes to larger kid cards and the scripture boxes.
* A slim lavender **Parents** strip appears only when parents-only items (flights, away days) fall today or tomorrow.
* **Come, Follow Me**: dates, lesson title and reading, then a larger white **Today** box with today's scripture reference, a short quote and a thought from `come_follow_me.daily`. **Strength of Youth**: chapter title, "Ch. N · label", today's tip large in a white box, tomorrow's tip underneath.
* No Heads-up section (to-dos stay in the JSON only).

**Daily spiritual items** – `spiritual.come_follow_me.daily` is a Mon–Sun list (`{"dow": "Mon", "scripture": "Isaiah 58:6–7", "quote": "…", "thought": "…"}`) for the CFM week in `week_of`; `strength_of_youth.daily_by_weekday` has one tip per weekday. All seven of each are rendered with `data-dow` and the page's `applyDay()` shows the one matching the iPad's date (America/Denver), so they advance each morning without a rebuild. If no CFM item matches today, the featured question is shown instead. **Replace `daily` on every Saturday refresh** with the next lesson's queue (and `daily_by_weekday` when the FSY chapter changes monthly).

**Page 2 – This week**
* Ten colourful day tiles starting today (Thu Oct 8 → Sat Oct 17 style), now using the full page height. Youth activities are calendar items on their day, tagged **YM** (one boy) or **All youth** (shared), kid-coloured or yellow with dots. Each item gets an icon and a short label: kid-coloured when it's one kid, yellow with kid-colour dots when shared. No-school and half-day show as red / yellow items with dots; a weekday when every kid is on a break becomes a big mint "Fall break" tile. Up to 6 items per tile, then "+N more". Away days carry a lavender state tag (trip titles are reduced to "Arizona" / "California").

**Rotation & fitting** – crossfade every `meta.v3_rotate_seconds` (falls back to `v2_rotate_seconds`, default 30); tap switches page and pauses 2 minutes with a "Paused (m:ss) · tap to resume" pill; progress bar; state in `localStorage` (`dash-v3-rot`). Sizes are authored in rem (1rem = 1/18 of the mockup's px) and auto-fit per page between 15px and 21px (portrait), and page 2 also stops growing before a tile label's longest word would be wider than its tile; `body[data-fs]` reports the result. The top padding clears the iPad status bar and the page-dot footer is a solid white strip, so nothing sits under it.

**BYU games** – BYU football and men's basketball games (`sports.byu.games`) are low-key items with a navy **BYU** pill and a ball icon, e.g. "BYU vs Iowa State · 8:15 PM · ESPN" ("@" for away games, "TBA" when no time is set, "Exh." for exhibitions). On page 2 they are listed after every family/school/YM item in a tile, so the 6-item cap drops them first; on a full-break tile they sit under the big "Fall break" mark. On page 1 a slim line under the motto shows today's ("Today"/"Tonight") and tomorrow's games; today's game drops off about 3½ hours after its start time.

**Easter egg** – a faded BYU-navy "Y" (a self-drawn SVG, not the official logo file) sits in the bottom-right corner of the page-dot bar. Tapping it spins the Y, pops a "Go Cougs!" bubble and sends a few little Ys flying for ~2.5 s. It lives outside the page area and stops the tap, so it never flips pages or pauses rotation.

**Hidden grades card** – not shown on the normal page and no hint anywhere. Three quick taps on the family motto (page 1 or page 2 header; each tap < 400 ms after the previous, all three within 700 ms) open a dimmed overlay with a "Grades" card: one pastel column per kid in his colour. Courses are listed by percent, highest first, colour-coded (green ≥ 90, amber 80–89, red < 80), with the source and date underneath (Luke: "Canvas · as of Oct 8", Wyatt: "Canvas · as of Oct 9", Tanner: "Veracross · as of Oct 9"); a kid without data would show "Not connected yet" in a narrower column. Long course names wrap rather than truncate. Percents are shown as the school reports them (100%, 98.2%, 97.71%). A 30 s countdown bar runs along the bottom and the card closes itself after 30 s (or on the × / a tap on the backdrop). Motto taps never reach the page-flip handler; a single (or double) motto tap still flips the page like any other tap once the 400 ms window has passed. The card is outside the page area, so its taps never rotate or pause the dashboard, and it is separate from the BYU Y. The grade data is in the public page source (accepted). `check_grades.py` (Playwright, fake clock) verifies open/auto-close/rotation state in portrait and landscape and saves `preview-grades.png`.

**Hidden $20 riddle challenge** – press and hold "Prayer:" on the Come, Follow Me card (page 1) for 3 seconds; nothing shows before that, and moving or lifting the finger cancels. It opens an intro card ("You found the secret $20 challenge!", the rules, a "keep it secret" note and a Start button), then three riddles in a row (Stage 1 of 3 … 3 of 3), each answered on a big on-screen keypad. One try per riddle: a wrong answer shows "Not quite! The challenge is locked. Try again tomorrow." and sets `localStorage` `egg20-lock` (now + 24 h); while locked the long press does nothing at all. × at any point gives up and goes back to the intro without a lock. Solving all three shows a full-screen confetti "$20" win screen with the date/time won, which stays until tapped; `egg20-won` is stored and later long presses just show "Already claimed on …". Only a salted SHA-256 per stage (different salt each) is in the page, checked with `crypto.subtle` (needs https, as on GitHub Pages); the answers are not in the page, the JSON, or the repo. The long press never flips/pauses the pages (the click that ends it is swallowed); a short tap on "Prayer:" is an ordinary page tap. `check_egg.py` (Playwright, fake clock; pass the answers as `EGG_ANSWERS=a,b,c`) covers the whole flow in portrait and landscape and saves `preview-egg-intro.png`, `preview-egg-riddle.png`, `preview-egg-stage3.png`, `preview-egg-win.png`.

**Surprise guard** – `data/private_hide.txt` (git-ignored, never commit it) filters events, to-dos and youth items. build.py also checks the finished HTML for those terms and refuses to write `v3/index.html` (exit 3) if any slip through.

**Refresh & staleness** – `<meta http-equiv=refresh content=1800>` reloads every 30 minutes. "Updated …" comes from `meta.last_updated` and turns amber ("needs refresh") when older than `meta.stale_after_days` (8).

## data/dashboard.json
| key | what |
|---|---|
| `meta` | `family_name`, `timezone`, `tz_label`, `week_start` (Sunday, written by build.py), `later_days` (8, widens the rendered date range), `motto`, `v3_rotate_seconds`, `prayer_rotation` `{order[], anchor_sunday}`, `stale_after_days` (8), `last_updated` (set by build.py), `school_feed_synced` and `school_feed_window` (set by fetch_school.py) |
| `people` | chip id → `{label, color}`: `luke`, `wyatt`, `tanner`, `parents`, `family` |
| `kids[]` | `id, name, grade, school, school_short, campus, division, in_person_days, in_person_summary`, and optionally `glance_line`, which overrides the school line in the kids card. `routine` (Wyatt only): `{days:["Tue","Thu"], start, end, title, note, online_title}` adds the "In person at Lehi campus" line automatically on those days unless Wyatt has no school |
| `events[]` | calendar items (see below) |
| `youth` | Young Men activities (see below), tagged YM / All youth on the boy's Today and Tomorrow lines and on the week tile for that day |
| `todos[]` | `{id, text, detail, who[], due, hide_after, priority, done}`. Kept in the JSON but not rendered (v3 has no Heads-up section) |
| `spiritual` | see below |
| `grades` | Hidden grades card. `luke` / `wyatt` / `tanner`: `{connected: true, source: "canvas" | "veracross", as_of: "YYYY-MM-DD", courses[] {name, short, pct}, previous: {as_of, courses[]}}` (`previous` = last snapshot, kept for future drop detection; not rendered yet). a kid set to `{connected: false}` shows "Not connected yet" |
| `academics` | `updated` (ISO), `kids.<id>.courses[] {name, percent, letter}`, `missing_count` (int or null), `upcoming_tests[] {date, course, title}` (hidden once past), `note`. Legacy, not rendered (superseded by `grades`) |
| `sports.byu` | Written by `fetch_byu.py`: `team`, `source` (per sport), `seasons`, `updated`, `games[] {id, sport (football/mbb), date, start (HH:MM MT or null = TBA), opponent, home_away (home/away/neutral), tv (first network or null), tv_all[], venue, note ("Exhibition"/null), result ("W 63-7", past games)}` |
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
* `flag`: `"no_school"` shows a red No school item for those kids (a weekday when every kid is off becomes a mint "Fall break"-style tile). `"half_day"` shows a yellow Half day · out at 12 PM item.
* `priority`: `low` items are **not rendered**. A same-day "Term N ends" note is folded into the Half day item when it covers the same kids.
* `kind`: `event`, `flight` (plane icon), `trip` (a lavender state tag on every day it covers, e.g. "Arizona"), or `school`. Icons are otherwise picked from the title (see `V3_ICON_RULES` in build.py).
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

**Rendered:** CFM shows dates, title, reading, the prayer rotation line and today's `daily` box (falls back to the featured question: `featured_question`, a 0-based index into `questions`, default 0). FSY shows the chapter, `label`, and today's / tomorrow's `daily_by_weekday` tip (else `daily_application`). `summary`, the other questions, `focus`, `quote` and `previous` stay in the JSON but are not rendered.

When `status` is `"pending"`, or there is no reading (CFM) or topic (FSY), the card shows a placeholder title.

## School feed filtering (fetch_school.py)
Kept: school-wide items (no school, half days, term start/end, grades posted, picture retakes), HS items for grade 9 (Luke), ES items for K-5, generic ES, or grade 5 (Tanner), spirit-apparel days (low priority), and parent events.
Dropped: middle school, other grades, kindergarten, clubs, rehearsals, athletics, senior nights, AP/ACT/PSAT for other grades, admissions, and faculty items.
No-school entries on weekends are skipped. When the band named in "No School K-8" or a similar phrase covers only some of the kids, the event is split into a no-school item for the kids it covers and a separate item for the others.
The default window is **21 days**, so a weekly run still fills the ten day tiles all week. Use `--days 14` if you want a shorter window.

## BYU games (fetch_byu.py)
* **Source:** the official byucougars.com schedule pages (`/sports/football/schedule`, `/sports/mens-basketball/schedule`), read from the server-rendered HTML: date and time (with UTC offset, converted to America/Denver), TBA flag, vs./at, opponent, exhibition flag, location and the TV link. If a page can't be read, ESPN's public site API team schedule JSON (BYU = team 252, regular season + postseason) is used for that sport instead.
* Runs on every `run.sh`, so the Saturday refresh picks up new kickoff/tipoff times, TV networks and added games (bowl games, tournament opponents) automatically. Nothing is invented: unset times are stored as `null` (TBA) and "TV (TBA)" as no network.
* **Fail soft:** if both sources fail for a sport, its previous games are kept and the script exits 2; run.sh logs it and still builds.
* The official pages show the current season, so the dashboard rolls into the next football / basketball season on its own.

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
* There is no separate Young Men card: activities appear on the boys' Today/Tomorrow lines and on the week tiles. Past entries hide automatically based on the viewing date.
* Precedence: items with `source` `sheet` or `manual` (the ward Google Sheet, refreshed separately) always win. `fetch_youth.py` parses the ward site's "<Month> Youth Activities" list for this month and next and stores the results as `source: "site"`. Each run replaces only the earlier `site` items. build.py shows a site item only on dates that have no sheet or manual items, and only if its title doesn't repeat a sheet item within 3 weeks. If the fetch fails or nothing parses, the JSON is left unchanged and the build continues.
* Raw sheet exports (`data/youth_sheet*`) are git-ignored, so they are never published.
