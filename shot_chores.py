#!/usr/bin/env python3
"""Screenshot chores-a/b/c with the panel open at 1920x1080 and 1280x800 (local files or --base URL); taps a few boxes,
reloads to confirm persistence. Writes preview-chores-<v>-<W>x<H>.png. Usage: .venv-shot/bin/python shot_chores.py [--base URL]"""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CHK = """() => { const c = document.querySelector('#chp .cc'), b = document.querySelector('#chp .cb');
  const out = [...c.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(), R = c.getBoundingClientRect(); return r.width && (r.bottom > R.bottom + 1 || r.right > R.right + 1); }).length;
  const t = [...c.querySelectorAll('.chk:not([disabled]),.kid,.x')].map(e => e.getBoundingClientRect()).map(r => Math.min(r.width, r.height));
  return {outside: out, bodyOverflow: b.scrollHeight > b.clientHeight + 1 || b.scrollWidth > b.clientWidth + 1, minTarget: Math.round(Math.min(...t)),
    checked: c.querySelectorAll('.chk.on').length}; }"""
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for v in "abc":
        for w, h, dpr in ((1920, 1080, 1), (1280, 800, 1.5)):
            ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA, timezone_id="America/Denver")
            pg = ctx.new_page()
            url = (BASE.rstrip("/") + f"/chores-{v}/") if BASE else (HERE / f"chores-{v}" / "index.html").as_uri()
            pg.goto(url); pg.wait_for_timeout(1200)
            pg.tap("#chbtn"); pg.wait_for_timeout(300)
            for sel in ("#chp .chk:not([disabled])",) * 1:
                els = pg.query_selector_all(sel)
                for i in (0, 3, 5):
                    if i < len(els): els[i].tap(); pg.wait_for_timeout(120); els = pg.query_selector_all(sel)
            r1 = pg.evaluate(CHK)
            pg.reload(); pg.wait_for_timeout(1000); pg.tap("#chbtn"); pg.wait_for_timeout(300)
            r2 = pg.evaluate(CHK)
            print(v, f"{w}x{h}", r1, "after reload checked:", r2["checked"], "button:", pg.inner_text("#chbtn"))
            pg.screenshot(path=str(HERE / f"preview-chores-{v}-{w}x{h}.png")); ctx.close()
