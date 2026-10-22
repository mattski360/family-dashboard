#!/usr/bin/env python3
"""Screenshot landscape/ (final wall page) at the Apolosign viewport candidates and run Android-touch checks.
Usage: /workspace/.venv-shot/bin/python shot_landscape_final.py [--no-touch]
Writes preview-land-final-<W>x<H>-p1.png / -p2.png. Prints fit info; 'outside' and 'scroll' must be 0/False."""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
URL = (HERE / "landscape" / "index.html").as_uri()
SIZES = [(1920, 1080, 1), (1920, 1032, 1), (1280, 800, 1.5), (1280, 720, 1.5), (960, 540, 2)]
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CHECK = """() => { const pg = document.querySelector('.page.on'), r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect();
    return r.width && r.height && getComputedStyle(e).visibility!=='hidden' && getComputedStyle(e).position!=='fixed' && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1 || r.left < r0.left - 1); });
  const fs = parseFloat(getComputedStyle(pg).getPropertyValue('--fs'));
  return {fs: document.body.dataset.fs, page: pg.id, outside: out.length, scroll: pg.classList.contains('scroll'),
    docScroll: document.documentElement.scrollHeight > innerHeight + 1, minFontPx: Math.min(...[...pg.querySelectorAll('*')].filter(e=>e.offsetParent&&e.textContent.trim()&&!e.children.length).map(e=>parseFloat(getComputedStyle(e).fontSize)))}; }"""
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for w, h, dpr in SIZES:
        for i in (0, 1):
            ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA, timezone_id="America/Denver")
            pg = ctx.new_page()
            pg.add_init_script(f"localStorage.setItem('dash-land-rot', JSON.stringify({{i:{i},t:Date.now(),p:0}}))")
            pg.goto(URL); pg.wait_for_timeout(1500)
            r = pg.evaluate(CHECK); print(f"{w}x{h}@{dpr} p{i+1}", r)
            if r["outside"] or r["scroll"] or r["docScroll"]: fails.append((w, h, i, r))
            pg.screenshot(path=str(HERE / f"preview-land-final-{w}x{h}-p{i+1}.png"))
            ctx.close()
    if "--no-touch" not in sys.argv:
        ctx = b.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=1.5, has_touch=True, is_mobile=True, user_agent=UA, timezone_id="America/Denver")
        pg = ctx.new_page(); pg.add_init_script("localStorage.clear();localStorage.setItem('dash-land-rot', JSON.stringify({i:0,t:Date.now(),p:0}))")
        pg.goto(URL); pg.wait_for_timeout(1200)
        cdp = ctx.new_cdp_session(pg)
        def touch(x, y, hold=0):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
            if hold: pg.wait_for_timeout(hold)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        def ctr(sel):
            bb = pg.locator(sel).first.bounding_box(); return bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        def cur(): return pg.evaluate("document.querySelector('.page.on').id")
        res = {}
        # tap-to-pause: tap on page flips to p2 and pauses
        x, y = ctr("#p1 .kids"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(400)
        res["tap flips+pauses"] = cur() == "p2" and pg.evaluate("document.body.classList.contains('paused')")
        x, y = ctr("#resume"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(300)
        res["resume button"] = not pg.evaluate("document.body.classList.contains('paused')")
        # BYU Y
        x, y = ctr("#yegg"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(300)
        res["BYU Y"] = pg.evaluate("document.getElementById('cougs').classList.contains('go')") and cur() == "p2"
        # idea buttons (page 2)
        x, y = ctr("#p2 #adv .ab"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(300)
        res["idea button"] = pg.evaluate("document.getElementById('advpop').classList.contains('on')") and cur() == "p2"
        x, y = ctr("#advx"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(300)
        res["idea close"] = not pg.evaluate("document.getElementById('advpop').classList.contains('on')")
        # triple tap motto -> grades
        x, y = ctr("#p2 .motto")
        for _ in range(3): pg.touchscreen.tap(x, y); pg.wait_for_timeout(120)
        pg.wait_for_timeout(500)
        res["motto triple-tap"] = pg.evaluate("document.getElementById('grades').classList.contains('on')") and cur() == "p2"
        pg.evaluate("window.__grades.close()"); pg.wait_for_timeout(400)
        # go to p1 via nav dot
        x, y = ctr("#nav .dot[data-i='0']"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(1200)
        res["nav dot"] = cur() == "p1"
        # 3 s hold on Prayer: (real CDP touch hold)
        x, y = ctr("#p1 .prayer"); touch(x, y, 1500); pg.wait_for_timeout(200)
        res["1.5s hold does nothing"] = not pg.evaluate("document.getElementById('egg').classList.contains('on')")
        pg.wait_for_timeout(1200)
        x, y = ctr("#nav .dot[data-i='0']"); pg.touchscreen.tap(x, y); pg.wait_for_timeout(1200)
        x, y = ctr("#p1 .prayer"); touch(x, y, 3300); pg.wait_for_timeout(300)
        res["3s hold opens egg"] = pg.evaluate("document.getElementById('egg').classList.contains('on')") and cur() == "p1"
        res["wake lock"] = pg.evaluate("'wakeLock' in navigator")
        print(res)
        if not all(v for k, v in res.items() if k != "wake lock"): fails.append(res)
        ctx.close()
    b.close()
print("FAIL" if fails else "OK", fails if fails else "")
sys.exit(1 if fails else 0)
