#!/usr/bin/env python3
"""Screenshots of landscape-mock/ (November features mockup).
Usage: /workspace/.venv-shot/bin/python shot_nov_mockup.py [URL]
Writes mock_weather.png, mock_trivia_joke.png, mock_trivia_joke_revealed.png, mock_gratitude.png (+ _composer, 1180x820 variants)."""
import json, shutil, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
URL = sys.argv[1] if len(sys.argv) > 1 else (HERE / "landscape-mock" / "index.html").as_uri()
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
now = int(time.time() * 1000)
NOTES = [{"n": "Luke", "t": "Getting to pass the sacrament with my quorum", "ts": now - 9 * 864e5},
         {"n": "Tanner", "t": "Pancakes on Saturday mornings!", "ts": now - 8 * 864e5},
         {"n": "Sabrina", "t": "Boys who make me laugh every single day", "ts": now - 7 * 864e5},
         {"n": "Wyatt", "t": "BYU football wins", "ts": now - 6 * 864e5},
         {"n": "Matt", "t": "A warm house, a full pantry and a family who prays together", "ts": now - 5 * 864e5},
         {"n": "Tanner", "t": "My brothers playing catch with me after school", "ts": now - 4 * 864e5},
         {"n": "Luke", "t": "Snow days and sledding", "ts": now - 3 * 864e5},
         {"n": "Wyatt", "t": "My friends at school and my teachers", "ts": now - 2 * 864e5},
         {"n": "Sabrina", "t": "The temple being so close to home", "ts": now - 1 * 864e5},
         {"n": "Matt", "t": "Fall colors up American Fork Canyon", "ts": now - 3600e3}]
CHECK = """(id) => { const pg = document.getElementById(id), r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width && r.height && cs.visibility!=='hidden' && cs.position!=='absolute' && cs.position!=='fixed' && !e.closest('.gboard,.gdeco') && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1); });
  return {fs: document.body.dataset.fs, scroll: pg.classList.contains('scroll'), outside: out.map(e=>e.className).slice(0,5)}; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for (w, h, sfx) in [(1920, 1080, ""), (1180, 820, "_1180x820")]:
        def ctx_page(i, notes=None):
            ctx = b.new_context(viewport={"width": w, "height": h}, has_touch=True, user_agent=UA, timezone_id="America/Denver")
            pg = ctx.new_page()
            init = f"localStorage.setItem('dash-mock-rot', JSON.stringify({{i:{i},t:Date.now(),p:0}}));"
            if notes is not None: init += f"localStorage.setItem('grat-2026', {json.dumps(json.dumps(notes))});"
            pg.add_init_script(init); pg.goto(URL); pg.wait_for_timeout(2500)
            return ctx, pg
        ctx, pg = ctx_page(0); print(w, h, "p1", pg.evaluate(CHECK, "p1"))
        pg.screenshot(path=str(HERE / f"mock_weather{sfx}.png")); ctx.close()
        ctx, pg = ctx_page(1); print(w, h, "p2", pg.evaluate(CHECK, "p2"))
        pg.screenshot(path=str(HERE / f"mock_trivia_joke{sfx}.png"))
        pg.click("#ftr"); pg.click("#fjk"); pg.wait_for_timeout(600)
        print("  still p2 after taps:", pg.evaluate("document.querySelector('.page.on').id"))
        pg.screenshot(path=str(HERE / f"mock_trivia_joke_revealed{sfx}.png")); ctx.close()
        ctx, pg = ctx_page(2, NOTES); print(w, h, "p3", pg.evaluate(CHECK, "p3"))
        pg.screenshot(path=str(HERE / f"mock_gratitude{sfx}.png"))
        pg.click("#gadd"); pg.wait_for_timeout(300); pg.click("#gnames button[data-n='Wyatt']"); pg.fill("#gin", "Grandma's rolls at Thanksgiving")
        pg.wait_for_timeout(300)
        held = pg.evaluate("window.__composing===true")
        pg.screenshot(path=str(HERE / f"mock_gratitude_composer{sfx}.png"))
        pg.click("#gsave"); pg.wait_for_timeout(900)
        print("  composing froze rotation:", held, "| saved:", pg.evaluate("JSON.parse(localStorage.getItem('grat-2026')).length"), "| page:", pg.evaluate("document.querySelector('.page.on').id"))
        ctx.close()
    b.close()
