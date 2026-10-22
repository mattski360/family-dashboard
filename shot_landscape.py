#!/usr/bin/env python3
"""Screenshot the landscape mockups at 1920x1080 (and optionally 1280x720).
Usage: /workspace/.venv-shot/bin/python shot_landscape.py [--w 1920 --h 1080] [--suffix ""]
Writes preview-land-a.png, preview-land-b1.png, preview-land-b2.png; prints fit info + elements outside the page (should be 0)."""
import argparse, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("--w", type=int, default=1920); ap.add_argument("--h", type=int, default=1080)
ap.add_argument("--suffix", default=""); a = ap.parse_args()
exe = shutil.which("google-chrome") or shutil.which("chromium")
CHECK = """() => { const pg = document.querySelector('.page.on'), r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect();
    return r.width && r.height && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1 || r.left < r0.left - 1); });
  return [document.body.dataset.fs, pg.id + ' ' + pg.scrollHeight + '/' + pg.clientHeight, 'outside:' + out.length, pg.classList.contains('scroll')]; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    for name, mode, i in (("a", "a", 0), ("b1", "b", 0), ("b2", "b", 1)):
        pg = b.new_page(viewport={"width": a.w, "height": a.h}, timezone_id="America/Denver")
        pg.add_init_script(f"localStorage.setItem('dash-land{mode}-rot', JSON.stringify({{i:{i},t:Date.now(),p:0}}))")
        pg.goto((HERE / f"landscape-{mode}" / "index.html").as_uri()); pg.wait_for_timeout(1500)
        print(name, pg.evaluate(CHECK))
        pg.screenshot(path=str(HERE / f"preview-land-{name}{a.suffix}.png"))
    b.close()
