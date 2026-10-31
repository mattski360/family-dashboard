# Jensen Family wall dashboard

A static page (`v3/index.html`, with CSS and JS inline; v3 makes no external requests, while the landscape wall page also fetches weather from Open-Meteo in the browser) for a wall-mounted iPad, portrait-first (820×1180; landscape 1180×820 also fits). Published with GitHub Pages from `main`.

Live: https://mattski360.github.io/family-dashboard/v3/ (the iPad's URL).
The root URL (`index.html`) and the old `/v2/` URL (`v2/index.html`) are small static redirect pages to `v3/` (meta refresh + `location.replace`); they are committed as-is and not rebuilt. The earlier v1 and v2 layouts were retired in October 2026 (see git history).

`build.py` renders `v3/index.html` from `data/dashboard.json` using `template_v3.html` + the icon sprite `v3_sprite.svg`.

```
./run.sh                 # fetch_school.py (AHS ICS) + fetch_youth.py (ward site, fallback) + fetch_byu.py (BYU games) → data/dashboard.json, then build.py → v3/index.html + landscape/index.html (+ landscape/ver.txt), then deploy_cloudflare.sh. Exit 0 = all OK, 1 = a fetch or the deploy failed (named in the log), 2 = hidden-term refusal
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

**Hidden $20 riddle challenge** – press and hold "Prayer:" on the Come, Follow Me card (page 1) for 3 seconds; nothing shows before that, and moving the finger more than ~10 px or lifting it cancels. It opens an intro card ("You found the secret $20 challenge!", the rules, a "keep it secret" note and a Start button), then three riddles in a row (Stage 1 of 3 … 3 of 3), each answered on a big on-screen keypad. **10 seconds per riddle**: a countdown (shrinking bar plus a big 10…0 number, turning red for the last 3 s) starts when each riddle is shown and restarts at 10 for every new stage; it stops as soon as Enter is pressed. One try per riddle: a wrong answer shows "Not quite! The challenge is locked. Try again tomorrow." and running out of time shows "Time's up! The challenge is locked. Try again tomorrow."; both set `localStorage` `egg20-lock-v2` (now + 24 h) and close the card after 4 s; while locked the long press does nothing at all. × at any point gives up, stops the timer and goes back to the intro without a lock. Solving all three shows a full-screen confetti "$20" win screen with the date/time won, which stays until tapped; `egg20-won-v2` is stored and later long presses just show "Already claimed on …". **Resetting it:** the state keys are versioned; to wipe a past win/lock on the wall display, bump the version in the templates (`egg20-lock-v3` / `egg20-won-v3`) and add the old keys to the remove list. Every load removes the retired keys (`egg20-lock`, `egg20-won`, `egg20-epoch`, Oct 30 2026 reset), so the next page load starts fresh. The egg is identical in `template_landscape.html`, `template_landscape_a.html`, `template_landscape_b.html` and `template_v3.html`. Only a salted SHA-256 per stage (different salt each) is in the page, checked with `crypto.subtle` (needs https, as on GitHub Pages); the answers are not in the page, the JSON, or the repo. The long press is handled by delegation on `document`: on iPad it uses touch events (touchstart is `preventDefault`'ed so iOS text selection / callout / `pointercancel` can't steal the gesture; ~10 px finger jitter is allowed), with pointer events only as the mouse fallback. The whole "Prayer:" line is the target, with an invisible hit area at least 48 px tall. The long press never flips/pauses the pages; a short tap on "Prayer:" is replayed as an ordinary page tap. `check_egg.py` (Playwright, fake clock; pass the answers as `EGG_ANSWERS=a,b,c`; without them only the answer-free checks run: old-key reset, intro text, the 10 s timer, × stopping it, time-out lock and +24 h unlock; `EGG_PAGE=landscape EGG_SIZES=1180x820,1920x1080` tests the wall page) covers the whole flow in portrait and landscape, in Chromium (mouse) and WebKit with iPad emulation and real touch events (`EGG_ENGINES=chromium,webkit`; WebKit needs `playwright install webkit` and `sudo playwright install-deps webkit`), and saves `preview-egg-intro.png`, `preview-egg-timeup.png`, `preview-egg-riddle.png`, `preview-egg-stage3.png`, `preview-egg-win.png`.

**Weekly adventure picks** – `data/adventures/weekend_adventures.csv` (150) and `evening_adventures.csv` (100) are the idea lists. Each build picks one weekend and one evening adventure for the Sun–Sat dashboard week: in season (`Best Season(s)` parsed as month ranges incl. wraparound like `Nov-Mar`, comma lists, seasons, `Year-round`; unparseable = year-round; weekend uses the Saturday's month, evening mid-week's), not matching any hide-list term, and not among the last 20 picks per list (`meta.adventure_history`). The choice is seeded by the week-start date, and rebuilding the same week keeps the picks. They are stored in `dashboard.json` as `adventures.this_week = {week_start, weekend:{row}, evening:{row}}` for the Saturday routine/email, (not shown on the page any more).

**Random adventure buttons** – the bottom of page 2 has two buttons, "🎲 Evening idea" and "🎲 Weekend idea". The build embeds both lists (hide-filtered, minimal fields, season months pre-parsed) as JSON in the page. A tap shows a random idea in a popup card: name, description, location, drive time, cost, best seasons, notes, "Pick again" and ×. It closes on its own after 60 s. Ideas in season for the iPad's current month (America/Denver) come first, and the last 8 shown per list are skipped (`localStorage` `adv-recent-<kind>`). Button and popup taps never flip pages or pause; rotation is frozen while the popup is open and resumes where it was. `check_adventure.py` (Playwright, Chromium) checks this and saves `preview-adventure.png`.

**Surprise guard** – `data/private_hide.txt` (git-ignored, never commit it) filters events, to-dos and youth items. build.py also checks the finished HTML for those terms and refuses to write `v3/index.html` (exit 3) if any slip through.

**New builds reach the iPad** – the page carries `data-ver` (a hash of the rendered page); every 10 minutes it fetches the published page with `cache: no-store` and reloads itself (with a `?r=` cache-buster) when the version differs, instead of waiting for the 30-minute reload.

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
| `grades` | Hidden grades card. `luke` / `wyatt` / `tanner`: `{connected: true, source: "canvas" | "veracross", as_of: "YYYY-MM-DD", courses[] {name, short, pct}, previous: {as_of, courses[]}, checked_at, check_status}` (`previous` = last snapshot, kept for future drop detection; not rendered yet). `as_of` moves only when that kid's grades change; `checked_at` (ISO) is stamped on every successful nightly check by `python3 grades_checked.py luke wyatt tanner` (`--status signin` records a failed check without moving it). Not rendered anywhere. a kid set to `{connected: false}` shows "Not connected yet" |
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

### Study popups (`deep_dive`, live landscape only) – fill on every Saturday refresh
Tapping the Come, Follow Me or Strength of Youth card on `landscape/` opens a big study popup (build_study.py). Rotation is held while open; closes with X, a tap outside, or 5 min idle. Test with `landscape/?study=cfm` or `?study=fsy`; screenshots: `python3 shot_study.py`.
Content comes **only** from the official pages (`source_url`). Copy scripture (KJV) and guide/manual quotes **verbatim**; never invent quotes. Kid-friendly explanations (ages ~10–15) are our own words.
* `spiritual.come_follow_me.deep_dive` – **replace every Saturday** with the next lesson (from the "Ideas for Learning at Home and at Church" and "Ideas for Teaching Children" sections). The popup is hidden if `deep_dive.week_of` ≠ `come_follow_me.week_of`.
  `{week_of, intro, scripture_blocks:[{ref, about}], principles:[{emoji, title (manual heading), ref, explain}] (3–5), key_verses:[{ref, text}] (3–5, verbatim KJV), quote:{text, by} (optional, verbatim from the lesson), questions:[…] (4–5 family discussion), activity:{title, steps} (from the children's section), source_url}`
* `spiritual.strength_of_youth.deep_dive` – **replace when `strength_of_youth.month` changes** (monthly chapter); hidden if its `month` ≠ `strength_of_youth.month`.
  `{month, chapter_title, scripture:{ref, text}, intro, teachings:[{emoji, title, explain}] (4–5, from Eternal Truths / Invitations), quotes:[…] (verbatim from the chapter), blessings, questions:[…] (questions to ponder), source_url}`

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
* **Poll ranks are data-driven, never hardcoded.** Every run reads ESPN's rankings endpoint
  (`site.api.espn.com/apis/site/v2/sports/{sport}/rankings`): BYU's current AP / Coaches (and CFP once released) rank goes to
  `sports.byu.summary.<sport>.polls[] {poll, rank, as_of, week}`; BYU missing from a poll (unranked, ESPN 0/99) = no entry = no
  number shown. Upcoming games get `opp_rank` / `opp_rank_poll` (opponent's current CFP-else-AP rank) and render as "No. 6 Utah";
  the "No. 17 Kansas" prefixes baked into the official schedule page go stale, so they are stripped.
* **Stale-rank guard (build.py `byu_live_polls`):** a poll chip is hidden if the poll is more than 9 days old in season, or
  (football) was published before BYU's latest game. The AP/Coaches polls come out Sunday, after the Saturday 8:55 PM run, so
  any nightly update should run `python3 fetch_byu.py` before `build.py` to pick up the new poll on Sunday.

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

## Landscape wall display (Apolosign 21.5", 1920×1080) – `landscape/`

Final URL: https://mattski360.github.io/family-dashboard/landscape/ (built from `template_landscape.html` by `build.py`, so `run.sh` regenerates it weekly with the same hidden-term leak check; `landscape-a/` and `landscape-b/` are static redirects to it; `template_landscape_a.html` is no longer built).
**Reloads (landscape)** – only two, both wait while the page is busy (typing on the gratitude board, any popup/panel open — chores, meals, study, BYU, grades, egg, ideas — or a touch in the last 2 min): every 10 min it fetches `landscape/ver.txt` (the 12-char `data-ver`, written by build.py) with `cache: no-store` and reloads on a new build (falls back to reading `data-ver` from the published page if ver.txt is missing), and a safety reload after the page has been up 90 min. There is no meta refresh on this page.
Auto-fits any 16:9-ish CSS viewport (1920×1080, 1920×1032 with system bars, 1280×800, 1280×720, 960×540) with no scrolling; sizes scale with the viewport so the physical size on the panel is the same at any devicePixelRatio. Touch-friendly (bigger nav/tap targets, no zoom), Screen Wake Lock with a muted-video fallback, `manifest.webmanifest` (fullscreen, landscape) for Chrome "Add to Home screen". Add `?info` to the URL to show the real viewport / devicePixelRatio / wake-lock status on the device.
`/workspace/.venv-shot/bin/python shot_landscape_final.py` writes `preview-land-final-<W>x<H>-p1/p2.png` and runs Android touch checks (tap-to-pause, resume, BYU Y, idea buttons, motto triple-tap, nav dots, 3 s hold on "Prayer:"); exits non-zero on any overflow or failed check.

### Weather, trivia/joke and gratitude board (live landscape only, `build_features.py`)
`build.py` applies `build_features.transform(..., prod=True)` to `landscape/index.html` only:
- **Weather (pages 1 and 2 headers)** – Highland, UT (40.43, -111.79): now plus today and the next 4 days from Open-Meteo (free, no key), fetched in the browser once and drawn in both headers. It is cached in localStorage `wx-highland-v1` and refreshed every 30 min and when the day changes. Readings older than 3 h show "as of"; with no data it shows "Weather unavailable right now · retrying".
- **Trivia + joke of the day (page 2, beside the idea buttons)** – picked by date from `data/daily_fun.json` (45 of each, kid-friendly). Tap to reveal the answer. Tapping doesn't flip the page.
- **Gratitude board (3rd rotating page)** – shown while the Denver date is between `GRAT_FROM` and `GRAT_TO` (`10-30`..`11-30`, set in `build_features.py`). Use `?grat=0` / `?grat=1` to force it off or on. Notes are kept in this browser's localStorage `grat-YYYY`, so they are not shared between devices. While someone is typing, rotation and both reloads pause.
- **Guest notes** – the composer has a 6th "Guest" button with an optional name field (24 characters max, works with the built-in keys). A note shows as "Name (guest)", or just "Guest" when the name is blank, in a neutral grey and is counted under "Guests". Check it with `shot_guest.py`.
- **Monthly colour themes (`build_theme.py`, live since Oct 30 2026, `LIVE = True`)** – 12 light pastel themes, picked in the browser by the Denver month, with `?theme=MM` to preview a month and `?theme=off` to turn them off. Set `LIVE = False` to turn them off. `build_theme_preview.py` writes a local preview copy and `shot_themes.py` saves `shots_theme/theme_01.png`..`theme_12.png`.
- `build_nov_mockup.py` writes the MOCKUP preview to `landscape-mock/`, deployed with `deploy_mockup_preview.sh` to the `mockup` branch alias. `shot_features.py` takes screenshots and runs a fit check of all 3 pages at 1920×1080 and 1180×820.

## BYU easter-egg popup
Tapping the faded BYU "Y" (nav corner, v3 / landscape) still plays the Go Cougs animation and also opens a
BYU-colored popup (football + men's basketball: record, standing, AP/Coaches/CFP ranks, last 3 results, next 4 games).
Data: `sports.byu.games` + `sports.byu.summary` + `sports.byu.updated` in data/dashboard.json, refreshed every week by
`fetch_byu.py` (run.sh, Sat 8:55 PM). Unknown items are omitted. Auto-closes after 30 s; X or tap outside closes.
Optional audio: set `sports.byu.fight_song = {"src": "../assets/<file>", "credit": "..."}` to a licensed file; the popup
then stays open for the song's length (30 s fallback if play() is rejected). None is set: "The Cougar Song" (Rise and
Shout) is still under copyright (registered 1947, renewed 1975; held by the Sandgren family/BYU), so no copy is in the repo.
