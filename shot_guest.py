#!/usr/bin/env python3
"""Gratitude board Guest submitter check + screenshots.  /workspace/.venv-shot/bin/python shot_guest.py [URL]
Opens page 3, picks Guest, types a name with the built-in keys and a note, saves, and checks "Name (guest)" + the Guests tally.
Writes shots_live/guest_composer.png, guest_composer_1180x820.png, guest_board.png."""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
URL = sys.argv[1] if len(sys.argv) > 1 else (HERE / "landscape" / "index.html").as_uri()
OUT = HERE / "shots_live"; OUT.mkdir(exist_ok=True)
ok = True
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for (w, h, sfx) in [(1920, 1080, ""), (1180, 820, "_1180x820")]:
        ctx = b.new_context(viewport={"width": w, "height": h}, has_touch=True, timezone_id="America/Denver")
        pg = ctx.new_page(); pg.add_init_script("localStorage.setItem('dash-land-rot', JSON.stringify({i:2,t:Date.now(),p:0}));localStorage.removeItem('grat-2026')")
        pg.goto(URL); pg.wait_for_timeout(1500)
        pg.tap("#gadd"); pg.wait_for_timeout(300)
        pg.tap('#gnames button[data-n="Guest"]'); pg.wait_for_timeout(200)
        vis = pg.is_visible("#gguest"); foc = pg.evaluate("document.activeElement.id")
        pg.tap("#gkbt"); pg.wait_for_timeout(200)          # built-in keys type into the guest field first
        for k in "Grandma Jo":
            pg.tap(f'#gkeys button[data-k="{k.lower() if k != " " else " "}"]')
        pg.tap('#gkeys button[data-k="ok"]')                 # Add on the keys moves on to the note field
        for k in "yummy rolls":
            pg.tap(f'#gkeys button[data-k="{k}"]')
        st = pg.evaluate("[document.getElementById('gguest').value, document.getElementById('gin').value, document.getElementById('gsave').disabled]")
        r0 = pg.evaluate("(()=>{const c=document.querySelector('#gcomp .gcard').getBoundingClientRect();return [Math.round(c.top),Math.round(c.bottom),innerHeight]})()")
        pg.screenshot(path=str(OUT / f"guest_composer{sfx}.png"))
        pg.tap("#gsave"); pg.wait_for_timeout(2200)
        res = pg.evaluate("""[[...document.querySelectorAll('#gboard .gnote .gby')].map(e=>e.textContent),
            [...document.querySelectorAll('#gwho .gper')].map(e=>e.textContent), JSON.parse(localStorage.getItem('grat-2026'))]""")
        # second guest note with no name -> plain "Guest"
        pg.tap("#gadd"); pg.wait_for_timeout(300); pg.tap('#gnames button[data-n="Guest"]')
        if not pg.is_visible("#gkeys"): pg.tap("#gkbt")
        pg.tap('#gkeys button[data-k="ok"]')
        for k in "snow": pg.tap(f'#gkeys button[data-k="{k}"]')
        pg.tap('#gkeys button[data-k="ok"]'); pg.wait_for_timeout(2200)
        res2 = pg.evaluate("[[...document.querySelectorAll('#gboard .gnote .gby')].map(e=>e.textContent),[...document.querySelectorAll('#gwho .gper')].map(e=>e.textContent).pop(), document.querySelector('#gwho').scrollWidth<=document.querySelector('#gwho').clientWidth+1]")
        print(w, h, "guest field visible", vis, "focused", foc, "typed", st, "card", r0)
        print("  after save", res); print("  after blank guest", res2)
        good = vis and st[0] == "Grandma Jo" and st[1].lower() == "yummy rolls" and not st[2] and "Grandma Jo (guest)" in res[0][0] \
            and res[2][0].get("g") == "Grandma Jo" and res2[0][0].startswith("Guest") and res2[1].endswith("2") and res2[2] and r0[1] <= r0[2]
        ok &= good
        if not sfx: pg.screenshot(path=str(OUT / "guest_board.png"))
        ctx.close()
    b.close()
print("OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
