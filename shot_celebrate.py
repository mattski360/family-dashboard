#!/usr/bin/env python3
"""Celebration test: serve repo over HTTP, check one kid's boxes; the last check must request one /assets/celebrate/NN.mp3 and
call play() exactly once; reload must not play. Screenshot toast -> preview-celebrate-1920x1080.png. Usage: shot_celebrate.py [--base URL]"""
import shutil, sys, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None
srv = None
if not BASE:
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    BASE = "http://127.0.0.1:8765"
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
SPY = "window.__plays=[];const _p=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){window.__plays.push(this.src);return _p.call(this)};"
ok = True
try:
  with sync_playwright() as p:
    br = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox", "--autoplay-policy=user-gesture-required"])
    ctx = br.new_context(viewport={"width": 1920, "height": 1080}, has_touch=True, is_mobile=True, user_agent=UA, timezone_id="America/Denver")
    pg = ctx.new_page(); pg.add_init_script(SPY)
    reqs = []; pg.on("request", lambda r: "/celebrate/" in r.url and reqs.append(r.url))
    pg.goto(BASE + "/landscape/"); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.tap("#chbtn"); pg.wait_for_timeout(500)
    boxes = pg.locator("#chp .col").first.locator(".chk"); n = boxes.count()
    for i in range(n - 1): boxes.nth(i).tap(); pg.wait_for_timeout(150)
    before = pg.evaluate("window.__plays.length"); print(f"{n} boxes; plays after {n-1} checks:", before)
    boxes.nth(n - 1).tap(); pg.wait_for_timeout(700)
    plays = pg.evaluate("window.__plays"); print("plays after last check:", plays)
    pg.screenshot(path=str(HERE / "preview-celebrate-1920x1080.png"))
    played = [u for u in reqs if u.split("/")[-1] == plays[-1].split("/")[-1]] if plays else []
    print("sound requested:", bool(played), "| total celebrate requests (incl. preload):", len(reqs))
    ok &= before == 0 and len(plays) == 1 and bool(played) and pg.locator("#celt").count() == 1
    # uncheck + recheck -> plays again, different sound
    boxes.nth(n - 1).tap(); pg.wait_for_timeout(150); boxes.nth(n - 1).tap(); pg.wait_for_timeout(300)
    p2 = pg.evaluate("window.__plays"); print("after uncheck/recheck:", p2); ok &= len(p2) == 2 and p2[0] != p2[1]
    pg.reload(); pg.wait_for_timeout(2000); pg.tap("#chbtn"); pg.wait_for_timeout(800)
    r = pg.evaluate("window.__plays.length"); print("plays after reload+open:", r, "| checked kept:", pg.locator("#chp .chk.on").count())
    ok &= r == 0 and pg.locator("#celt").count() == 0
finally:
    if srv: srv.terminate()
print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
