#!/usr/bin/env python3
"""Screenshots + fit checks of the wall page with weather / trivia+joke / gratitude board.
Usage: /workspace/.venv-shot/bin/python shot_features.py [URL] [--mock] [--prefix live_]
Default URL: landscape/index.html (rotation key dash-land-rot); --mock uses landscape-mock/ (dash-mock-rot).
Writes <prefix>p1.png, <prefix>p2.png, <prefix>p3.png at 1920x1080 and *_1180x820.png. Exit 1 on overflow."""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
a = sys.argv[1:]; mock = "--mock" in a
prefix = a[a.index("--prefix") + 1] if "--prefix" in a else ("mock_" if mock else "live_")
pos = [x for x in a if not x.startswith("--") and (a.index(x) == 0 or a[a.index(x) - 1] != "--prefix")]
URL = pos[0] if pos else (HERE / ("landscape-mock" if mock else "landscape") / "index.html").as_uri()
KEY = "dash-mock-rot" if mock else "dash-land-rot"
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CHECK = """(id) => { const pg = document.getElementById(id); if(!pg) return {missing:true}; const r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width && r.height && cs.visibility!=='hidden' && cs.position!=='absolute' && cs.position!=='fixed' && !e.closest('.gboard,.gdeco') && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1); });
  return {on: pg.classList.contains('on'), fs: document.body.dataset.fs, scroll: pg.classList.contains('scroll'), outside: out.length,
    wx: [...document.querySelectorAll('.wx')].map(w=>w.querySelectorAll('.wd').length)}; }"""
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for (w, h, sfx) in [(1920, 1080, ""), (1180, 820, "_1180x820")]:
        for i in (0, 1, 2):
            ctx = b.new_context(viewport={"width": w, "height": h}, has_touch=True, user_agent=UA, timezone_id="America/Denver")
            reqs = []
            pg = ctx.new_page(); pg.on("request", lambda r: reqs.append(r.url) if "open-meteo" in r.url else None)
            pg.add_init_script(f"localStorage.setItem('{KEY}', JSON.stringify({{i:{i},t:Date.now(),p:0}}))")
            pg.goto(URL); pg.wait_for_timeout(2500)
            r = pg.evaluate(CHECK, f"p{i+1}"); r["weather_requests"] = len(reqs); print(f"{w}x{h} p{i+1}", r)
            if r.get("missing") or not r["on"] or r["outside"] or r["scroll"]: fails.append((w, h, i, r))
            pg.screenshot(path=str(HERE / f"{prefix}p{i+1}{sfx}.png")); ctx.close()
    b.close()
print("FAIL" if fails else "OK", fails or "")
sys.exit(1 if fails else 0)
