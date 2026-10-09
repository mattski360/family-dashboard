#!/usr/bin/env python3
"""Playwright check for the hidden grades card on v3 (motto triple-tap).

Usage: /workspace/.venv-shot/bin/python check_grades.py [--shot preview-grades.png]
Checks (portrait 820x1180 and landscape 1180x820, fake clock):
  * the card is hidden on load; three quick motto taps (150 ms apart) open it
  * the taps leave the rotation state untouched (same page, not paused, localStorage dash-v3-rot unchanged)
  * the card is still open at 29 s and gone at 30.5 s, with rotation still un-paused
  * the card fits the viewport; the BYU Y easter egg does not open it; tapping the backdrop closes it
Exits 1 on any failure. Saves a screenshot of the open card (portrait).
"""
import argparse, datetime, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--shot", default=str(HERE / "preview-grades.png"))
a = ap.parse_args()
exe = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


STATE = "[document.querySelector('.page.on').id, document.body.classList.contains('paused'), localStorage.getItem('dash-v3-rot')]"
OPEN = "document.getElementById('grades').classList.contains('show')"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    for w, h in ((820, 1180), (1180, 820)):
        tag = f"{w}x{h}"
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2, timezone_id="America/Denver")
        pg.clock.install(time=datetime.datetime.fromisoformat("2026-10-09T09:00:00-06:00"))
        pg.add_init_script("localStorage.removeItem('dash-v3-rot')")
        pg.goto((HERE / "v3" / "index.html").as_uri())
        pg.wait_for_timeout(800)
        check(not pg.evaluate(OPEN) and not pg.locator("#grades").is_visible(), f"{tag}: card hidden on load")
        before = pg.evaluate(STATE)
        mo = pg.locator(".page.on .motto").bounding_box()
        x, y = mo["x"] + mo["width"] / 2, mo["y"] + mo["height"] / 2
        for i in range(3):
            pg.mouse.click(x, y)
            if i < 2:
                pg.wait_for_timeout(150)
        pg.wait_for_timeout(350)
        check(pg.evaluate(OPEN), f"{tag}: triple-tap opens the card")
        check(pg.evaluate(STATE) == before, f"{tag}: rotation state unchanged by the taps {pg.evaluate(STATE)}")
        card = pg.locator("#grades .gcard").bounding_box()
        check(card["x"] >= 0 and card["y"] >= 0 and card["x"] + card["width"] <= w and card["y"] + card["height"] <= h,
              f"{tag}: card fits the viewport ({card['width']:.0f}x{card['height']:.0f})")
        over = pg.evaluate("[...document.querySelectorAll('#grades .gcard *')].filter(e=>e.scrollWidth>e.clientWidth+1&&getComputedStyle(e).overflow!=='visible').length")
        check(over == 0, f"{tag}: no clipped text in the card")
        if w < h:
            pg.screenshot(path=a.shot)
            print(f"saved {a.shot}")
        pg.clock.run_for(29000)
        check(pg.evaluate(OPEN), f"{tag}: still open at 29 s")
        pg.clock.run_for(1500)
        pg.wait_for_timeout(400)
        check(not pg.locator("#grades").is_visible(), f"{tag}: auto-closed after 30 s")
        st = pg.evaluate(STATE)
        check(st[1] is False and '"p":0' in st[2], f"{tag}: rotation never paused {st}")
        # Y easter egg must not open the card; backdrop tap closes an open card without touching rotation
        pg.locator("#yegg").click()
        pg.wait_for_timeout(300)
        check(not pg.evaluate(OPEN), f"{tag}: Y egg does not open grades")
        pg.evaluate("window.__grades.open()")
        before = pg.evaluate(STATE)
        pg.mouse.click(8, h / 2)
        pg.wait_for_timeout(400)
        check(not pg.locator("#grades").is_visible() and pg.evaluate(STATE) == before, f"{tag}: backdrop tap closes, rotation untouched")
        # page 2 header has the motto too: the same triple-tap works there
        pg.close()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2, timezone_id="America/Denver")
        pg.clock.install(time=datetime.datetime.fromisoformat("2026-10-09T09:00:00-06:00"))
        pg.add_init_script("localStorage.setItem('dash-v3-rot', JSON.stringify({i:1,t:Date.now(),p:0}))")
        pg.goto((HERE / "v3" / "index.html").as_uri())
        pg.wait_for_timeout(800)
        before = pg.evaluate(STATE)
        mo = pg.locator(".page.on .motto").bounding_box()
        for i in range(3):
            pg.mouse.click(mo["x"] + mo["width"] / 2, mo["y"] + mo["height"] / 2)
            if i < 2:
                pg.wait_for_timeout(150)
        pg.wait_for_timeout(350)
        check(before[0] == "p2" and pg.evaluate(OPEN) and pg.evaluate(STATE) == before, f"{tag}: page-2 motto triple-tap opens, rotation untouched")
        pg.close()
    b.close()
print("PASS" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
