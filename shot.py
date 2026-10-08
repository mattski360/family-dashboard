#!/usr/bin/env python3
"""Screenshot the dashboard at iPad sizes with headless Chrome (playwright driving system Chrome).

Usage: python shot.py [--page index.html] [--prefix preview] [--theme dark|light]
Writes <prefix>.png (portrait 820x1180, the primary wall layout) and <prefix>-landscape.png (1180x820).
"""
import argparse, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--page", default="index.html")
ap.add_argument("--prefix", default="preview")
ap.add_argument("--theme")
a = ap.parse_args()
exe = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    for suffix, w, h in (("", 820, 1180), ("-landscape", 1180, 820)):
        name = f"{a.prefix}{suffix}.png"
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2, timezone_id="America/Denver")
        if a.theme:
            pg.add_init_script(f"localStorage.setItem('dash-theme','{a.theme}')")
        pg.goto((HERE / a.page).as_uri())
        pg.wait_for_timeout(700)
        info = pg.evaluate("[document.body.dataset.fs, document.documentElement.scrollHeight, innerHeight]")
        pg.screenshot(path=str(HERE / name))
        print(name, info)
    b.close()
