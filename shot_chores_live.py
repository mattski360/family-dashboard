#!/usr/bin/env python3
"""Live landscape Chores tests: button on both pages (same rect, no overlap with Y/content), panel fit, persistence across
reload and page flip, rotation held while open and resumed after close. Usage: shot_chores_live.py [--base URL]"""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None
URL = (BASE.rstrip("/") + "/landscape/") if BASE else (HERE / "landscape" / "index.html").as_uri()
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
GEOM = """() => { const r = e => { const b = document.querySelector(e).getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom].map(Math.round); };
  const btn = document.getElementById('chbtn').getBoundingClientRect(), hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  const pg = document.querySelector('.page.on');
  const over = [...pg.querySelectorAll('*'), ...document.querySelectorAll('#nav > *, .upd')].filter(e => { const b = e.getBoundingClientRect();
     return b.width && b.height && getComputedStyle(e).visibility !== 'hidden' && e.offsetParent !== null && !e.contains(document.getElementById('chbtn')) && hit(b, btn) && e.children.length === 0; }).map(e => e.id || e.className || e.tagName);
  return {page: pg.id, btn: r('#chbtn'), yegg: r('#yegg'), overlaps: over, onTop: document.elementFromPoint((btn.left + btn.right) / 2, (btn.top + btn.bottom) / 2).closest('#chbtn') !== null}; }"""
PANEL = """() => { const c = document.querySelector('#chp .cc'), b = document.querySelector('#chp .cb'), R = c.getBoundingClientRect();
  return {outside: [...c.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.bottom > R.bottom + 1 || r.right > R.right + 1); }).length,
    overflow: b.scrollHeight > b.clientHeight + 1, checked: c.querySelectorAll('.chk.on').length}; }"""
res = []
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for w, h, dpr in ((1920, 1080, 1), (1280, 800, 1.5)):
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA, timezone_id="America/Denver")
        pg = ctx.new_page(); pg.add_init_script("if(!sessionStorage.x){localStorage.clear();sessionStorage.x=1}localStorage.setItem('dash-land-rot', JSON.stringify({i:0,t:Date.now(),p:0}))")
        pg.goto(URL); pg.wait_for_timeout(1500)
        g1 = pg.evaluate(GEOM); pg.screenshot(path=str(HERE / f"preview-live-chores-p1-{w}x{h}.png"))
        pg.evaluate("document.querySelector('#nav .dot[data-i=\"1\"]').click()"); pg.wait_for_timeout(1500)
        g2 = pg.evaluate(GEOM); pg.screenshot(path=str(HERE / f"preview-live-chores-p2-{w}x{h}.png"))
        print(f"{w}x{h} p1", g1); print(f"{w}x{h} p2", g2, "same position:", g1["btn"] == g2["btn"])
        pg.evaluate("document.getElementById('resume').click()"); pg.wait_for_timeout(300)   # unpause, rotation running
        pg.tap("#chbtn"); pg.wait_for_timeout(300)
        els = pg.query_selector_all("#chp .chk")
        for i in (0, 5, 10): els[i].tap(); pg.wait_for_timeout(120); els = pg.query_selector_all("#chp .chk")
        p1 = pg.evaluate(PANEL); print("  panel", p1)
        pg.screenshot(path=str(HERE / f"preview-live-chores-panel-{w}x{h}.png"))
        page_before = pg.evaluate("document.querySelector('.page.on').id"); prog0 = pg.evaluate("document.getElementById('prog').style.width")
        pg.wait_for_timeout(32000)   # > rotation period (30 s): page must not flip while open
        held = pg.evaluate("document.querySelector('.page.on').id") == page_before
        print("  rotation held while open:", held, "prog", prog0, "->", pg.evaluate("document.getElementById('prog').style.width"))
        pg.tap("#chp .x"); pg.wait_for_timeout(500)
        a = pg.evaluate("document.getElementById('prog').style.width"); pg.wait_for_timeout(2000); b = pg.evaluate("document.getElementById('prog').style.width")
        pg.wait_for_timeout(30000); flipped = pg.evaluate("document.querySelector('.page.on').id") != page_before
        print("  after close prog", a, "->", b, "flipped within 32s:", flipped)
        pg.reload(); pg.wait_for_timeout(1200); pg.tap("#chbtn"); pg.wait_for_timeout(300)
        r = pg.evaluate(PANEL)["checked"]; pg.tap("#chp .x")
        pg.evaluate("document.querySelector('#nav .dot[data-i=\"0\"]').click()"); pg.wait_for_timeout(400); pg.tap("#chbtn"); pg.wait_for_timeout(300)
        f = pg.evaluate(PANEL)["checked"]
        print("  checked after reload:", r, "after page flip:", f, "button:", pg.inner_text("#chbtn").replace("\n", " "))
        ctx.close()
