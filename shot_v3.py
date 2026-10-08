#!/usr/bin/env python3
"""Screenshot both pages of the v3 "two soft pages" dashboard (portrait 820x1180) with headless Chrome.

Usage: /workspace/.venv-shot/bin/python shot_v3.py [--prefix preview-v3] [--at 2026-10-08T07:20:00-06:00] [--landscape]
Writes <prefix>-p1.png (Today) and <prefix>-p2.png (This week); prints the fitted base font per page and
how many elements end up outside the visible area (should be 0).
"""
import argparse, datetime, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="preview-v3")
ap.add_argument("--at", help="simulate this local time (ISO with offset)")
ap.add_argument("--landscape", action="store_true")
ap.add_argument("--scale", type=float, default=2)
a = ap.parse_args()
w, h = (1180, 820) if a.landscape else (820, 1180)
exe = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
CHECK = """() => { const pg = document.querySelector('.page.on'), r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect();
    return r.width && r.height && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1 || r.left < r0.left - 1); });
  return [document.body.dataset.fs, pg.id + ' ' + pg.scrollHeight + '/' + pg.clientHeight, 'outside:' + out.length]; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=a.scale, timezone_id="America/Denver")
    if a.at:
        pg.clock.install(time=datetime.datetime.fromisoformat(a.at))
    pg.add_init_script("localStorage.removeItem('dash-v3-rot')")
    pg.goto((HERE / "v3" / "index.html").as_uri())
    pg.wait_for_timeout(1500)
    print(pg.evaluate(CHECK))
    pg.screenshot(path=str(HERE / f"{a.prefix}-p1.png"))
    # page 2 as it looks mid-rotation (not paused): seed the rotation state and reload
    pg2 = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=a.scale, timezone_id="America/Denver")
    if a.at:
        pg2.clock.install(time=datetime.datetime.fromisoformat(a.at))
    pg2.add_init_script("localStorage.setItem('dash-v3-rot', JSON.stringify({i:1,t:Date.now(),p:0}))")
    pg2.goto((HERE / "v3" / "index.html").as_uri())
    pg2.wait_for_timeout(1500)
    print(pg2.evaluate(CHECK))
    pg2.screenshot(path=str(HERE / f"{a.prefix}-p2.png"))
    b.close()
