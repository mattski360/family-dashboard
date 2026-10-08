#!/usr/bin/env python3
"""Screenshot both pages of the v2 rotating dashboard (portrait 820x1180) with headless Chrome.

Usage: python shot_v2.py [--prefix preview-v2] [--at 2026-10-08T10:00:00-06:00] [--landscape]
Writes <prefix>-p1.png (Today) and <prefix>-p2.png (This week); prints the fitted base font per page.
"""
import argparse, datetime, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="preview-v2")
ap.add_argument("--at", help="simulate this local time (ISO with offset)")
ap.add_argument("--landscape", action="store_true")
ap.add_argument("--scale", type=float, default=2)
a = ap.parse_args()
w, h = (1180, 820) if a.landscape else (820, 1180)
exe = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=a.scale, timezone_id="America/Denver")
    if a.at:
        pg.clock.install(time=datetime.datetime.fromisoformat(a.at))
    pg.add_init_script("localStorage.removeItem('dash-v2-rot')")
    pg.goto((HERE / "v2" / "index.html").as_uri())
    pg.wait_for_timeout(1200)
    info = pg.evaluate("""() => [document.body.dataset.fs,
        ...['#p1','#p2'].map(s => { const e = document.querySelector(s); return s + ' ' + e.scrollHeight + '/' + e.clientHeight; })]""")
    print(info)
    pg.screenshot(path=str(HERE / f"{a.prefix}-p1.png"))
    pg.click("#nav .dot[data-i='1']")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(HERE / f"{a.prefix}-p2.png"))
    b.close()
