#!/usr/bin/env python3
"""Playwright check for the hidden 3-stage $20 riddle egg on v3 (press-and-hold "Prayer:" for 3 s).

Usage: EGG_ANSWERS=a,b,c /workspace/.venv-shot/bin/python check_egg.py
The answers are passed in (they are not stored in the repo); the page only holds a salted SHA-256 per stage.
Uses a paused fake clock so the 3 s hold, the 24 h lock and rotation are deterministic. In portrait 820x1180 and
landscape 1180x820 it checks: short tap / 2 s hold do nothing; a 3 s hold opens the intro (Start -> stage 1) without
touching rotation;
the card fits; x at any point gives up (back to the intro, no lock); a wrong answer at stage 3, 2 or 1 locks it
(a hold then shows nothing); +24 h it works again; all three right answers show the win screen (stays until
tapped) and store egg20-won; later holds only show "Already claimed"; the motto grades card and the Y egg don't
open it. Saves preview-egg-intro.png, preview-egg-riddle.png (stage 1), preview-egg-stage3.png and preview-egg-win.png (portrait).
"""
import datetime, hashlib, json, os, re, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGE = HERE / "v3" / "index.html"
exe = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
ANSWERS = [a.strip() for a in os.environ.get("EGG_ANSWERS", "").split(",") if a.strip()]
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
if len(ANSWERS) != 3:
    sys.exit("set EGG_ANSWERS=<stage1>,<stage2>,<stage3> to run the full check")
H = lambda st, a: hashlib.sha256((st["salt"] + a).encode()).hexdigest()
for i, (st, a) in enumerate(zip(stages, ANSWERS), 1):
    check(H(st, a) == st["hash"], f"stage {i}: answer matches its salted hash")
    check(not re.search(r"(?<![\w.])" + re.escape(a) + r"(?![\w.])", egg_js) and f"'{a}'" not in script and f'"{a}"' not in script,
          f"stage {i}: answer not in the egg code or as a quoted string in the page script")
WRONG = {1: "88", 2: "2002", 3: "44"}
for i, wv in WRONG.items():
    check(H(stages[i - 1], wv) != stages[i - 1]["hash"], f"stage {i}: {wv} is wrong")
check(H(stages[0], "53") != stages[0]["hash"], "stage 1: 53 is wrong")

STATE = "[document.querySelector('.page.on').id, document.body.classList.contains('paused'), JSON.parse(localStorage.getItem('dash-v3-rot')).p]"
RIDDLE = "document.getElementById('egg').classList.contains('on')"
INTRO = "document.getElementById('egg').classList.contains('on') && document.querySelector('#egg .ecard').classList.contains('intro')"
WIN = "document.getElementById('eggwin').classList.contains('on')"
LOCKED = "+(localStorage.getItem('egg20-lock')||0) > Date.now()"
T0 = datetime.datetime.fromisoformat("2026-10-09T13:00:00-06:00")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    for w, h in ((820, 1180), (1180, 820)):
        tag, portrait = f"{w}x{h}", w < h
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, timezone_id="America/Denver")
        # every load starts on page 1, just shown, not paused (t in the future = "now"; init scripts may see the real clock)
        ctx.add_init_script("localStorage.setItem('dash-v3-rot', JSON.stringify({i:0,t:9e15,p:0}))")
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
            pg.mouse.move(x, y)
            pg.mouse.down()
            pg.clock.run_for(ms)
            pg.mouse.up()
            pg.clock.run_for(300)

        def enter(val):
            for ch in val:
                pg.locator("#ekeys button", has_text=re.compile(rf"^{ch}$")).click()
            pg.locator("#ekeys .ek-e").click()
            pg.clock.run_for(100)
            pg.wait_for_timeout(150)                   # crypto.subtle promise
            pg.clock.run_for(100)

        def stage():
            return pg.inner_text("#estage") if pg.evaluate(RIDDLE) else ""

        def start():                                   # long press -> intro -> Start -> stage 1
            hold(3100)
            ok = pg.evaluate(INTRO)
            pg.locator("#estart").click(); pg.clock.run_for(100)
            return ok

        def advance():                                 # "Correct! Next one..." -> next stage after 1.2 s
            pg.clock.run_for(1300)

        fresh()
        pg.evaluate("localStorage.removeItem('egg20-won'); localStorage.removeItem('egg20-lock')")
        x, y = center()
        pg.mouse.click(x, y)                           # short tap = ordinary page tap
        pg.clock.run_for(300)
        check(not pg.evaluate(RIDDLE), f"{tag}: short tap does not open the riddle")
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
        pg.locator("#ex").click(); pg.clock.run_for(200)
        check(not pg.evaluate(RIDDLE) and not pg.evaluate(LOCKED), f"{tag}: x on the intro closes without a lock")
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
        advance()
        check(stage().upper() == "STAGE 2 OF 3", f"{tag}: moves on to stage 2")
        pg.locator("#ex").click(); pg.clock.run_for(200)
        check(not pg.evaluate(RIDDLE) and not pg.evaluate(LOCKED), f"{tag}: x mid-way closes without a lock")
        hold(3100)
        check(pg.evaluate(INTRO), f"{tag}: after x it starts again at the intro")
        pg.locator("#ex").click(); pg.clock.run_for(200)
        # other eggs don't open it
        pg.locator("#yegg").click(); pg.clock.run_for(300)
        mo = pg.locator(".page.on .motto").bounding_box()
        for _ in range(3):
            pg.mouse.click(mo["x"] + 20, mo["y"] + mo["height"] / 2); pg.clock.run_for(120)
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
        check(pg.evaluate(WIN) and not pg.evaluate(RIDDLE) and bool(pg.evaluate("localStorage.getItem('egg20-won')")),
              f"{tag}: all three right -> win screen + egg20-won")
        check("You won $20" in pg.inner_text("#eggwin") and "Won " in pg.inner_text("#ewhen"), f"{tag}: win text + time ({pg.inner_text('#ewhen')})")
        check(pg.evaluate(STATE) == base, f"{tag}: rotation untouched through the win")
        pg.clock.run_for(20000)
        check(pg.evaluate(WIN), f"{tag}: win screen stays (no auto close)")
        if portrait:
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(HERE / "preview-egg-win.png"))
        pg.mouse.click(w / 2, h - 120); pg.clock.run_for(200)
        check(not pg.evaluate(WIN), f"{tag}: tap closes the win screen")
        fresh()
        hold(3100)
        check(not pg.evaluate(RIDDLE) and "Already claimed on" in pg.inner_text("#etoast")
              and pg.evaluate("document.getElementById('etoast').classList.contains('on')"),
              f"{tag}: after a win a hold shows only '{pg.inner_text('#etoast')}'")
        ctx.close()
    b.close()
print("saved preview-egg-intro.png, preview-egg-riddle.png, preview-egg-stage3.png, preview-egg-win.png")
print("PASS" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
