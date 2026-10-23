#!/usr/bin/env python3
"""Tap the faded BYU Y and screenshot the BYU popup. Usage: /workspace/.venv-shot/bin/python shot_byu_pop.py
Writes preview-byu-pop-<name>.png; prints overflow info (cardOverflowX must be False, fitsViewport True)."""
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CASES = [("land-1920x1080", "landscape", 1920, 1080, 1), ("land-1280x800", "landscape", 1280, 800, 1.5),
         ("land-960x540", "landscape", 960, 540, 2), ("v3-portrait", "v3", 1080, 1920, 1)]
CHECK = """() => { const c = document.querySelector('#byupop .bp-card'), r = c.getBoundingClientRect(), x = document.getElementById('bpx').getBoundingClientRect();
  return {open: document.getElementById('byupop').classList.contains('on'), fitsViewport: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
    cardOverflowY: c.scrollHeight > c.clientHeight + 1, cardOverflowX: c.scrollWidth > c.clientWidth + 1, xBtn: [Math.round(x.width), Math.round(x.height)],
    minFontPx: Math.min(...[...c.querySelectorAll('*')].filter(e => e.textContent.trim() && !e.children.length).map(e => parseFloat(getComputedStyle(e).fontSize)))}; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for name, page, w, h, dpr in CASES:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA, timezone_id="America/Denver")
        pg = ctx.new_page(); pg.goto((HERE / page / "index.html").as_uri()); pg.wait_for_timeout(1200)
        pg.tap("#yegg"); pg.wait_for_timeout(700)
        print(name, pg.evaluate(CHECK))
        pg.screenshot(path=str(HERE / f"preview-byu-pop-{name}.png"))
        pg.mouse.click(5, 5); pg.wait_for_timeout(200)
        print("  tap-outside closes:", not pg.evaluate("document.getElementById('byupop').classList.contains('on')"))
        ctx.close()
