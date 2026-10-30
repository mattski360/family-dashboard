#!/usr/bin/env python3
"""Monthly theme previews + fit check.  /workspace/.venv-shot/bin/python shot_themes.py [BASE_URL_of_landscape_index] [--all]
Writes shots_theme/theme_01.png..theme_12.png (page 1, 1920x1080, ?theme=MM) and checks that no override = October;
--all also fit-checks pages 1-3 of every month at both sizes. Exit 1 on overflow or a wrong theme."""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
a = sys.argv[1:]; ALL = "--all" in a; pos = [x for x in a if not x.startswith("--")]
URL = pos[0] if pos else "file:///tmp/themeprev/landscape/index.html"
OUT = HERE / "shots_theme"; OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CHECK = """(id) => { const pg = document.getElementById(id); if(!pg) return {missing:true}; const r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width && r.height && cs.visibility!=='hidden' && cs.position!=='absolute' && cs.position!=='fixed' && !e.closest('.gboard,.gdeco') && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1); });
  const fam = document.querySelector('#'+id+' .fam');
  return {on: pg.classList.contains('on'), theme: document.documentElement.dataset.theme || null, outside: out.length, scroll: pg.classList.contains('scroll'),
    fs: document.body.dataset.fs, famw: fam ? Math.round(fam.scrollWidth - fam.clientWidth) : null,
    acc: getComputedStyle(document.querySelector('.date b')).color}; }"""
fails = []
jobs = [(f"{m:02d}", f"{m:02d}", 0) for m in range(1, 13)] + [("", "10", 0)]
SHOTS = 12
if ALL: jobs += [(f"{m:02d}", f"{m:02d}", i) for m in range(1, 13) for i in (0, 1, 2)]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for n, (q, want, i) in enumerate(jobs):
        for (w, h, sfx) in [(1920, 1080, ""), (1180, 820, "_1180x820")]:
            ctx = b.new_context(viewport={"width": w, "height": h}, has_touch=True, user_agent=UA, timezone_id="America/Denver")
            pg = ctx.new_page(); pg.add_init_script(f"localStorage.setItem('dash-land-rot', JSON.stringify({{i:{i},t:Date.now(),p:0}}))")
            pg.goto(URL + (f"?theme={q}" if q else "")); pg.wait_for_timeout(1800)
            r = pg.evaluate(CHECK, f"p{i+1}")
            bad = r.get("missing") or not r["on"] or r["outside"] or r["scroll"] or r["theme"] != want or (r["famw"] or 0) > 0
            if n < SHOTS or bad: print(f"theme={q or '(current)'} {w}x{h} p{i+1}", r)
            if bad: fails.append((q, w, i, r))
            if n < SHOTS and not sfx: pg.screenshot(path=str(OUT / f"theme_{want}.png"))
            ctx.close()
    b.close()
print("FAIL" if fails else f"OK ({len(jobs)*2} views)", fails or "")
sys.exit(1 if fails else 0)
