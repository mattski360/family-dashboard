#!/usr/bin/env python3
"""Monthly theme previews + fit + text-contrast check (themes are NOT live; run build_theme_preview.py first).
  /workspace/.venv-shot/bin/python shot_themes.py [URL]      default file:///tmp/themeprev/landscape/index.html
Writes shots_theme/theme_01.png..theme_12.png (page 1, 1920x1080, ?theme=MM), theme_10_p2.png/_11_/_12_ (page 2)
and theme_10_p3.png/_11_ (gratitude board). Checks pages 1-3 of every month at 1920x1080 and 1180x820: no overflow, the right
theme, and text contrast >= 4.5:1 (3:1 for large text) against its real background. Exit 1 on any failure."""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
pos = [x for x in sys.argv[1:] if not x.startswith("--")]
URL = pos[0] if pos else "file:///tmp/themeprev/landscape/index.html"
OUT = HERE / "shots_theme"; OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Linux; Android 15; FA21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CHECK = r"""(id) => {
  const pg = document.getElementById(id); if(!pg) return {missing:true}; const r0 = pg.getBoundingClientRect();
  const out = [...pg.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width && r.height && cs.visibility!=='hidden' && cs.position!=='absolute' && cs.position!=='fixed' && !e.closest('.gboard,.gdeco') && (r.bottom > r0.bottom + 1 || r.right > r0.right + 1); });
  const P = s => { const m = s.match(/rgba?\(([^)]+)\)/); if(!m) return null; const v = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [v[0],v[1],v[2],v.length>3?v[3]:1]; };
  const L = c => { const f = x => { x/=255; return x<=.03928? x/12.92 : Math.pow((x+.055)/1.055,2.4); }; return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2]); };
  const CR = (a,b) => { const x=L(a), y=L(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
  const body = P(getComputedStyle(document.documentElement).getPropertyValue('--th-bg1').trim().replace(/^#(..)(..)(..)$/, (m,a,b,c)=>`rgb(${parseInt(a,16)},${parseInt(b,16)},${parseInt(c,16)})`)) || [255,255,255,1];
  function bgOf(e){ const layers=[]; for(let n=e; n && n.nodeType===1; n=n.parentElement){ const cs=getComputedStyle(n);
      let c = P(cs.backgroundColor); if((!c||c[3]===0) && cs.backgroundImage.includes('gradient')) c = P(cs.backgroundImage.slice(cs.backgroundImage.indexOf('gradient')));
      if(c && c[3]>0){ layers.push(c); if(c[3]>=1) break; } }
    let base = body; for(let i=layers.length-1;i>=0;i--){ const c=layers[i], a=c[3]; base=[c[0]*a+base[0]*(1-a), c[1]*a+base[1]*(1-a), c[2]*a+base[2]*(1-a), 1]; } return base; }
  const bad = [];
  [...pg.querySelectorAll('*')].forEach(e => { if(![...e.childNodes].some(n => n.nodeType===3 && /[A-Za-z0-9]/.test(n.textContent))) return;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); if(!r.width || cs.visibility==='hidden' || +cs.opacity===0 || e.closest('.av,.byutag,#thdeco,.gdeco')) return;
    const fg = P(cs.color); const fs = parseFloat(cs.fontSize), w = +cs.fontWeight; const need = (fs>=24 || (fs>=18.66 && w>=700)) ? 3 : 4.5;
    const cr = CR(fg, bgOf(e)); if(cr < need) bad.push(`${e.className||e.tagName}:${e.textContent.trim().slice(0,18)}=${cr.toFixed(2)}`); });
  return {on: pg.classList.contains('on'), theme: document.documentElement.dataset.theme || null, outside: out.length, scroll: pg.classList.contains('scroll'),
    fs: document.body.dataset.fs, lowContrast: bad}; }"""
SHOTS = {(m, 0) for m in range(1, 13)} | {(10, 1), (11, 1), (12, 1), (10, 2), (11, 2)}
fails = []; views = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"), args=["--no-sandbox"])
    for m in range(1, 13):
        for i in (0, 1, 2):
            for (w, h, sfx) in [(1920, 1080, ""), (1180, 820, "_1180x820")]:
                ctx = b.new_context(viewport={"width": w, "height": h}, has_touch=True, user_agent=UA, timezone_id="America/Denver")
                pg = ctx.new_page(); pg.add_init_script(f"localStorage.setItem('dash-land-rot', JSON.stringify({{i:{i},t:Date.now(),p:0}}))")
                pg.goto(f"{URL}?theme={m:02d}"); pg.wait_for_timeout(1600)
                r = pg.evaluate(CHECK, f"p{i+1}"); views += 1
                bad = r.get("missing") or not r["on"] or r["outside"] or r["scroll"] or r["theme"] != f"{m:02d}" or r["lowContrast"]
                if bad: fails.append((m, i + 1, w, r)); print(f"theme={m:02d} p{i+1} {w}x{h}", r)
                if not sfx and (m, i) in SHOTS:
                    pg.screenshot(path=str(OUT / (f"theme_{m:02d}.png" if i == 0 else f"theme_{m:02d}_p{i+1}.png")))
                ctx.close()
        print(f"month {m:02d} checked", flush=True)
    b.close()
print("FAIL" if fails else f"OK ({views} views)", len(fails))
sys.exit(1 if fails else 0)
