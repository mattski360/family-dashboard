#!/usr/bin/env python3
"""Playwright check for the hidden 3-stage $20 riddle egg on v3 (press-and-hold "Prayer:" for 3 s).

Usage: EGG_ANSWERS=a,b,c /workspace/.venv-shot/bin/python check_egg.py   (EGG_PAGE=landscape to test landscape/index.html)
The answers are passed in (they are not stored in the repo); the page only holds a salted SHA-256 per stage.
Without EGG_ANSWERS only the answer-free parts run: the static checks, the reset of the old (unversioned) state keys,
the intro text, the 10 s riddle timer (counts down, x stops it without a lock, running out = "Time's up!" + 24 h lock).
Uses a paused fake clock so the 3 s hold, the 24 h lock and rotation are deterministic. In portrait 820x1180 and
landscape 1180x820 it checks: short tap / 2 s hold do nothing; a 3 s hold opens the intro (Start -> stage 1) without
touching rotation;
the card fits; x at any point gives up (back to the intro, no lock); a wrong answer at stage 3, 2 or 1 locks it
(a hold then shows nothing); +24 h it works again; all three right answers show the win screen (stays until
tapped) and store egg20-won; later holds only show "Already claimed"; the motto grades card and the Y egg don't
open it; the 10 s timer restarts at 10 on each new stage. Saves preview-egg-intro.png, preview-egg-riddle.png (stage 1), preview-egg-stage3.png and preview-egg-win.png (portrait).
"""
import datetime, hashlib, json, os, re, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGE = HERE / os.environ.get("EGG_PAGE", "v3") / "index.html"
exe = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
ANSWERS = [a.strip() for a in os.environ.get("EGG_ANSWERS", "").split(",") if a.strip()]
ROTKEY = re.search(r"KEY='(dash-[a-z0-9-]*rot)'", PAGE.read_text()).group(1)   # dash-v3-rot / dash-land-rot
fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


src = PAGE.read_text()
script = src[src.index("<script>"):]
egg_js = script[script.index("// hidden $20 riddle egg"):script.index("function eCancel")]   # the egg's own code
stages = json.loads(re.search(r"var EGG_STAGES=(\[.*?\]), EGG_HOLD", src).group(1))
check(len(stages) == 3 and len({s["salt"] for s in stages}) == 3, "3 stages, each with its own salt")
check(not re.search(r"answer\s*[:=]", src, re.I), "no plain 'answer' constant in the page")
_js = (HERE / "data" / "dashboard.json").read_text().lower()
check(not any(k in _js for k in ["egg20", "jensen-egg"] + [s["hash"] for s in stages]), "nothing about the egg in dashboard.json")
check("egg20-lock-v2" in src and "egg20-won-v2" in src, "versioned state keys egg20-lock-v2 / egg20-won-v2")
HAVE = len(ANSWERS) == 3
if not HAVE:
    print("note: EGG_ANSWERS not set -> skipping the answer-dependent checks (right answers, stage 2/3, win)")
H = lambda st, a: hashlib.sha256((st["salt"] + a).encode()).hexdigest()
for i, (st, a) in enumerate(zip(stages, ANSWERS) if HAVE else (), 1):
    check(H(st, a) == st["hash"], f"stage {i}: answer matches its salted hash")
    check(not re.search(r"(?<![\w.])" + re.escape(a) + r"(?![\w.])", egg_js) and f"'{a}'" not in script and f'"{a}"' not in script,
          f"stage {i}: answer not in the egg code or as a quoted string in the page script")
WRONG = {1: "88", 2: "2002", 3: "44"}
for i, wv in WRONG.items():
    check(H(stages[i - 1], wv) != stages[i - 1]["hash"], f"stage {i}: {wv} is wrong")
check(H(stages[0], "53") != stages[0]["hash"], "stage 1: 53 is wrong")

STATE = "[document.querySelector('.page.on').id, document.body.classList.contains('paused'), JSON.parse(localStorage.getItem('%s')).p]" % ROTKEY
RIDDLE = "document.getElementById('egg').classList.contains('on')"
INTRO = "document.getElementById('egg').classList.contains('on') && document.querySelector('#egg .ecard').classList.contains('intro')"
WIN = "document.getElementById('eggwin').classList.contains('on')"
LOCKED = "+(localStorage.getItem('egg20-lock-v2')||0) > Date.now()"
TNUM = "document.getElementById('etnum').textContent"
TBAR = "parseFloat(document.getElementById('etfill').style.width)"
T0 = datetime.datetime.fromisoformat("2026-10-09T13:00:00-06:00")

def run(p, engine, w, h):
    touch = engine == "webkit"                         # webkit = iPad Safari emulation with real touch events
    tag, portrait = f"{engine}{'+touch' if touch else ''} {w}x{h}", w < h
    opts = dict(p.devices["iPad (gen 7)"]) if touch else {}
    opts.update(viewport={"width": w, "height": h}, device_scale_factor=2, timezone_id="America/Denver")
    if touch:
        opts.update(screen={"width": w, "height": h}, has_touch=True, is_mobile=True)
    ctx = BROWSERS[engine].new_context(**opts)
    # every load starts on page 1, just shown, not paused (t in the future = "now"; init scripts may see the real clock)
    ctx.add_init_script("localStorage.setItem('%s', JSON.stringify({i:0,t:9e15,p:0}))" % ROTKEY)
    pg = ctx.new_page()
    pg.clock.install(time=T0)
    pg.clock.pause_at(T0)

    def fresh():                                   # (re)load; also absorbs the dashboard's own ?r= reload
        for _ in range(3):
            try:
                pg.goto(PAGE.as_uri())
                pg.wait_for_load_state()
                break
            except Exception:
                pg.wait_for_timeout(500)
        pg.clock.run_for(1000)

    def center():
        bb = pg.locator(".page.on .prayer").bounding_box()
        return bb["x"] + 30, bb["y"] + bb["height"] / 2     # on the "Prayer:" label

    def hold(ms):
        x, y = center()
        if touch:
            # real TouchEvents on the "Prayer:" label (handled by delegation), plus what iOS does during a long press:
            # a few px of finger jitter and a pointercancel -- neither may abort the hold
            sel = ".page.on .prayer .pr-l"
            t0 = {"identifier": 1, "clientX": x, "clientY": y}
            t1 = {"identifier": 1, "clientX": x + 4, "clientY": y + 3}
            pg.dispatch_event(sel, "touchstart", {"touches": [t0], "changedTouches": [t0], "targetTouches": [t0]})
            pg.clock.run_for(ms // 2)
            pg.dispatch_event(sel, "touchmove", {"touches": [t1], "changedTouches": [t1], "targetTouches": [t1]})
            pg.dispatch_event(sel, "pointercancel", {"pointerType": "touch", "isPrimary": True})
            pg.clock.run_for(ms - ms // 2)
            pg.dispatch_event(sel, "touchend", {"touches": [], "changedTouches": [t1], "targetTouches": []})
        else:
            pg.mouse.move(x, y)
            pg.mouse.down()
            pg.clock.run_for(ms)
            pg.mouse.up()
        pg.clock.run_for(300)

    def tap_xy(x, y):
        if touch:
            pg.touchscreen.tap(x, y)
        else:
            pg.mouse.click(x, y)

    def press(loc):
        loc.tap() if touch else loc.click()

    def enter(val):
        for ch in val:
            press(pg.locator("#ekeys button", has_text=re.compile(rf"^{ch}$")))
        press(pg.locator("#ekeys .ek-e"))
        pg.clock.run_for(100)
        pg.wait_for_timeout(150)                   # crypto.subtle promise
        pg.clock.run_for(100)

    def stage():
        return pg.inner_text("#estage") if pg.evaluate(RIDDLE) else ""

    def start():                                   # long press -> intro -> Start -> stage 1
        hold(3100)
        ok = pg.evaluate(INTRO)
        press(pg.locator("#estart")); pg.clock.run_for(100)
        return ok

    def advance():                                 # "Correct! Next one..." -> next stage after 1.2 s
        pg.clock.run_for(1300)

    # reset: old unversioned state (a past win + an active lock) is ignored and removed on load
    fresh()
    pg.evaluate("localStorage.setItem('egg20-won','2026-10-09T20:00:00Z'); localStorage.setItem('egg20-lock', String(Date.now()+20*3600*1000)); localStorage.setItem('egg20-epoch','x')")
    fresh()
    old = pg.evaluate("['egg20-won','egg20-lock','egg20-epoch'].map(k=>localStorage.getItem(k))")
    check(old == [None, None, None], f"{tag}: old egg20-won / egg20-lock / egg20-epoch removed on load {old}")
    hold(3100)
    check(pg.evaluate(INTRO), f"{tag}: with old win+lock keys present the challenge is fresh (intro opens)")
    press(pg.locator("#ex")); pg.clock.run_for(200)
    fresh()
    pg.evaluate("localStorage.removeItem('egg20-won-v2'); localStorage.removeItem('egg20-lock-v2')")
    x, y = center()
    tap_xy(x, y)                                   # short tap = ordinary page tap (flips once, pauses)
    pg.clock.run_for(300)
    st = pg.evaluate(STATE)
    check(not pg.evaluate(RIDDLE) and st[0] == "p2" and st[1], f"{tag}: short tap does not open the riddle, flips the page once {st}")
    fresh()
    # hold target: the whole line, at least 44 px tall (the ::before hit area), and hit-testing finds it
    bb = pg.locator(".page.on .prayer").bounding_box()
    hits = pg.evaluate("([x,y])=>[-22,-12,0,12,22].map(d=>{const e=document.elementFromPoint(x,y+d);return !!(e&&e.closest('.prayer'))})",
                       [bb["x"] + bb["width"] * 0.6, bb["y"] + bb["height"] / 2])
    check(all(hits[1:4]) and (bb["height"] >= 44 or all(hits)), f"{tag}: hold target >= 44 px tall incl. padding ({bb['height']:.0f}px box, hits {hits})")
    fresh()
    hold(2000)                                     # released early = ordinary tap
    check(not pg.evaluate(RIDDLE), f"{tag}: 2 s hold does not open the riddle")
    fresh()
    base = pg.evaluate(STATE)
    hold(3100)
    check(pg.evaluate(INTRO) and "secret $20 challenge" in pg.inner_text("#eintro"), f"{tag}: 3 s hold opens the intro")
    check(pg.evaluate(STATE) == base, f"{tag}: rotation untouched by the long press")
    pg.wait_for_timeout(500)                       # real-time pop-in animation
    card = pg.locator("#egg .ecard").bounding_box()
    check(card["x"] >= 0 and card["y"] >= 0 and card["x"] + card["width"] <= w and card["y"] + card["height"] <= h,
          f"{tag}: intro card fits ({card['width']:.0f}x{card['height']:.0f})")
    if portrait:
        pg.screenshot(path=str(HERE / "preview-egg-intro.png"))
    itxt = pg.inner_text("#eintro")
    check("10 seconds" in itxt and "running out of time" in itxt, f"{tag}: intro rules mention 10 seconds per riddle")
    press(pg.locator("#ex")); pg.clock.run_for(200)
    check(not pg.evaluate(RIDDLE) and not pg.evaluate(LOCKED), f"{tag}: x on the intro closes without a lock")
    # 10 s timer: counts down, x stops it (no lock), running out = wrong answer
    check(start() and stage().upper() == "STAGE 1 OF 3", f"{tag}: Start goes to stage 1")
    check(pg.evaluate(TNUM) == "10" and pg.evaluate(TBAR) > 95 and pg.locator("#etimer").is_visible(), f"{tag}: timer visible, starts at 10")
    card = pg.locator("#egg .ecard").bounding_box()
    check(card["y"] >= 0 and card["y"] + card["height"] <= h and card["x"] + card["width"] <= w
          and pg.evaluate("(()=>{const c=document.querySelector('#egg .ecard');return c.scrollHeight<=c.clientHeight+1})()"),
          f"{tag}: stage 1 card with timer fits ({card['width']:.0f}x{card['height']:.0f})")
    pg.clock.run_for(4000)
    n, b = pg.evaluate(TNUM), pg.evaluate(TBAR)
    check(n == "6" and 50 < b < 62, f"{tag}: after 4 s timer shows 6 and the bar shrank ({n}, {b:.0f}%)")
    press(pg.locator("#ex")); pg.clock.run_for(200)
    pg.clock.run_for(15000)
    check(not pg.evaluate(RIDDLE) and not pg.evaluate(LOCKED) and pg.evaluate("!localStorage.getItem('egg20-lock-v2')"),
          f"{tag}: x during a riddle stops the timer (15 s later: no lock)")
    fresh()                                        # (the dashboard may have rotated to page 2 meanwhile)
    hold(3100)
    check(pg.evaluate(INTRO), f"{tag}: after x mid-timer it opens at the intro again")
    press(pg.locator("#estart")); pg.clock.run_for(100)
    check(pg.evaluate(TNUM) == "10", f"{tag}: timer restarts at 10 on a new attempt")
    press(pg.locator("#ekeys button", has_text=re.compile(r"^7$")))   # typed but no Enter
    pg.clock.run_for(9500)
    check(pg.evaluate(RIDDLE) and not pg.evaluate(LOCKED) and pg.evaluate(TNUM) == "1", f"{tag}: at 9.6 s still open, shows 1, not locked")
    pg.clock.run_for(800)
    if portrait:
        pg.wait_for_timeout(400)                   # real-time bar transition
        pg.screenshot(path=str(HERE / "preview-egg-timeup.png"))
    check("Time\u2019s up! The challenge is locked. Try again tomorrow." in pg.inner_text("#emsg") and pg.evaluate(LOCKED)
          and pg.evaluate(TNUM) == "0" and pg.evaluate("document.querySelector('#ekeys .ek-e').disabled"),
          f"{tag}: at 10 s -> 'Time's up! The challenge is locked...' + 24 h lock, keypad off")
    pg.clock.run_for(4500)
    check(not pg.evaluate(RIDDLE), f"{tag}: time's-up card closes itself")
    hold(3100)
    check(not pg.evaluate(RIDDLE), f"{tag}: after time's up a hold shows nothing (locked)")
    pg.clock.fast_forward("24:05:00"); fresh()
    check(start() and stage().upper() == "STAGE 1 OF 3", f"{tag}: works again 24 h after a time-out")
    press(pg.locator("#ex")); pg.clock.run_for(200)
    if not HAVE:
        ctx.close()
        return
    check(start() and stage().upper() == "STAGE 1 OF 3", f"{tag}: Start goes to stage 1")
    check(pg.evaluate(STATE) == base, f"{tag}: rotation untouched by intro/Start")
    card = pg.locator("#egg .ecard").bounding_box()
    check(card["x"] >= 0 and card["y"] >= 0 and card["x"] + card["width"] <= w and card["y"] + card["height"] <= h
          and pg.evaluate("(()=>{const c=document.querySelector('#egg .ecard');return c.scrollHeight<=c.clientHeight+1})()"),
          f"{tag}: stage 1 card fits ({card['width']:.0f}x{card['height']:.0f})")
    if portrait:
        pg.screenshot(path=str(HERE / "preview-egg-riddle.png"))
    enter(ANSWERS[0])
    check("Correct" in pg.inner_text("#emsg"), f"{tag}: stage 1 right -> 'Correct!'")
    pg.clock.run_for(15000)                        # timer stopped once Enter was pressed: no time-out while "Correct!" shows
    check(not pg.evaluate(LOCKED), f"{tag}: no time-out after a right answer")
    advance()
    check(stage().upper() == "STAGE 2 OF 3", f"{tag}: moves on to stage 2")
    check(pg.evaluate(TNUM) == "10", f"{tag}: timer resets to 10 for stage 2")
    press(pg.locator("#ex")); pg.clock.run_for(200)
    check(not pg.evaluate(RIDDLE) and not pg.evaluate(LOCKED), f"{tag}: x mid-way closes without a lock")
    hold(3100)
    check(pg.evaluate(INTRO), f"{tag}: after x it starts again at the intro")
    press(pg.locator("#ex")); pg.clock.run_for(200)
    # other eggs don't open it
    press(pg.locator("#yegg")); pg.clock.run_for(300)
    mo = pg.locator(".page.on .motto").bounding_box()
    for _ in range(3):
        tap_xy(mo["x"] + 20, mo["y"] + mo["height"] / 2); pg.clock.run_for(120)
    check(pg.evaluate("document.getElementById('grades').classList.contains('on')") and not pg.evaluate(RIDDLE),
          f"{tag}: motto triple-tap opens grades, not the riddle")
    pg.evaluate("window.__grades.close()"); pg.clock.run_for(400)
    # wrong at stage 3 -> lock
    fresh()
    base = pg.evaluate(STATE)
    start(); enter(ANSWERS[0]); advance(); enter(ANSWERS[1]); advance()
    check(stage().upper() == "STAGE 3 OF 3", f"{tag}: two right answers reach stage 3")
    pg.wait_for_timeout(300)
    card = pg.locator("#egg .ecard").bounding_box()
    check(card["y"] >= 0 and card["y"] + card["height"] <= h, f"{tag}: stage 3 card fits ({card['width']:.0f}x{card['height']:.0f})")
    if portrait:
        pg.screenshot(path=str(HERE / "preview-egg-stage3.png"))
    enter(WRONG[3])
    check("Not quite! The challenge is locked. Try again tomorrow." in pg.inner_text("#emsg") and pg.evaluate(LOCKED),
          f"{tag}: wrong at stage 3 -> 'Not quite! The challenge is locked...' + 24 h lock")
    check(pg.evaluate(STATE) == base, f"{tag}: rotation untouched through the stages")
    pg.clock.run_for(4500)
    check(not pg.evaluate(RIDDLE), f"{tag}: wrong-answer card closes itself")
    hold(3100)
    check(not pg.evaluate(RIDDLE) and not pg.evaluate("document.getElementById('etoast').classList.contains('on')"),
          f"{tag}: while locked a hold shows nothing")
    pg.clock.fast_forward("23:00:00"); fresh()
    hold(3100)
    check(not pg.evaluate(RIDDLE), f"{tag}: still locked at +23 h")
    pg.clock.fast_forward("01:05:00"); fresh()
    check(start() and stage().upper() == "STAGE 1 OF 3", f"{tag}: works again after 24 h")
    # wrong at stage 2 -> lock
    enter(ANSWERS[0]); advance(); enter(WRONG[2])
    check("Not quite" in pg.inner_text("#emsg") and pg.evaluate(LOCKED), f"{tag}: wrong at stage 2 also locks")
    pg.clock.run_for(4500)
    hold(3100)
    check(not pg.evaluate(RIDDLE), f"{tag}: locked after the stage-2 miss (hold does nothing)")
    pg.clock.fast_forward("24:05:00"); fresh()
    # wrong at stage 1 -> lock
    start(); enter(WRONG[1])
    check("Not quite" in pg.inner_text("#emsg") and pg.evaluate(LOCKED), f"{tag}: wrong at stage 1 also locks")
    pg.clock.run_for(4500)
    hold(3100)
    check(not pg.evaluate(RIDDLE), f"{tag}: locked after the stage-1 miss (hold does nothing)")
    pg.clock.fast_forward("24:05:00"); fresh()
    base = pg.evaluate(STATE)
    start()
    enter(ANSWERS[0]); advance(); enter(ANSWERS[1]); advance(); enter(ANSWERS[2])
    check(pg.evaluate(WIN) and not pg.evaluate(RIDDLE) and bool(pg.evaluate("localStorage.getItem('egg20-won-v2')")),
          f"{tag}: all three right -> win screen + egg20-won")
    check("You won $20" in pg.inner_text("#eggwin") and "Won " in pg.inner_text("#ewhen"), f"{tag}: win text + time ({pg.inner_text('#ewhen')})")
    check(pg.evaluate(STATE) == base, f"{tag}: rotation untouched through the win")
    pg.clock.run_for(20000)
    check(pg.evaluate(WIN) and not pg.evaluate(LOCKED), f"{tag}: win screen stays (no auto close), timer cleared (no lock)")
    if portrait:
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(HERE / "preview-egg-win.png"))
    tap_xy(w / 2, h - 120); pg.clock.run_for(200)
    check(not pg.evaluate(WIN), f"{tag}: tap closes the win screen")
    fresh()
    hold(3100)
    check(not pg.evaluate(RIDDLE) and "Already claimed on" in pg.inner_text("#etoast")
          and pg.evaluate("document.getElementById('etoast').classList.contains('on')"),
          f"{tag}: after a win a hold shows only '{pg.inner_text('#etoast')}'")
    ctx.close()


# EGG_SIZES=1180x820,1920x1080 overrides the viewports (e.g. for EGG_PAGE=landscape, which is landscape-only)
SIZES = [tuple(int(v) for v in sz.split("x")) for sz in os.environ.get("EGG_SIZES", "820x1180,1180x820").split(",") if sz]
ENGINES = [e for e in os.environ.get("EGG_ENGINES", "chromium,webkit").split(",") if e]
BROWSERS = {}
with sync_playwright() as p:
    for engine in ENGINES:
        BROWSERS[engine] = p.webkit.launch() if engine == "webkit" else p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
        for w, h in SIZES:
            run(p, engine, w, h)
        BROWSERS[engine].close()
print("saved preview-egg-timeup.png, preview-egg-intro.png" + (", preview-egg-riddle.png, preview-egg-stage3.png, preview-egg-win.png" if HAVE else " (answer-dependent checks skipped: no EGG_ANSWERS)"))
print("PASS" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
