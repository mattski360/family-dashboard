#!/usr/bin/env python3
"""Seed a sample dinner plan, shoot page 2 (day tiles) at 1920x1080 and 1280x800, check meal lines fit."""
import json, shutil, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
URL = (HERE / "landscape" / "index.html").as_uri()
lib = [m["name"] for m in json.load(open(HERE / "data/dashboard.json"))["meals"]["library"]]
t = datetime.datetime.now(ZoneInfo("America/Denver")).date()
plan = {}
for i in range(10):
    if i in (3, 8): continue  # leave some days empty
    d = t + datetime.timedelta(days=i); plan.setdefault((d - datetime.timedelta(days=(d.weekday()+1) % 7)).isoformat(), {})[d.isoformat()] = lib[i % len(lib)]
seed = "".join(f"localStorage.setItem('dash-meals:{w}',{json.dumps(json.dumps(p))});" for w, p in plan.items())
CHK = """() => { const out=[]; document.querySelectorAll('.day.on').forEach(d=>{const r=d.getBoundingClientRect(), x=d.querySelector('.dml');
  const kids=[...d.querySelectorAll('*')].filter(e=>e.offsetParent&&e.getBoundingClientRect().height);
  const cut=kids.filter(e=>{const b=e.getBoundingClientRect();return b.bottom>r.bottom+1||b.right>r.right+1}).length;
  let ov=0; if(x){const xb=x.getBoundingClientRect(); ov=[...d.children].filter(e=>e!==x&&e.offsetParent).filter(e=>{const b=e.getBoundingClientRect();return b.top<xb.bottom-1&&xb.top<b.bottom-1}).length}
  out.push([d.dataset.date, x?x.innerText:'', cut, ov])}); return out }"""
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=shutil.which("google-chrome"), args=["--no-sandbox"])
    for w, h in ((1920, 1080), (1280, 800)):
        ctx = br.new_context(viewport={"width": w, "height": h}, timezone_id="America/Denver")
        pg = ctx.new_page(); pg.add_init_script("if(!sessionStorage.x){localStorage.clear();sessionStorage.x=1;" + seed + "}localStorage.setItem('dash-land-rot', JSON.stringify({i:1,t:Date.now(),p:Date.now()+9e5}))")
        pg.goto(URL); pg.wait_for_timeout(1500)
        for r in pg.evaluate(CHK): print(w, h, r)
        pg.screenshot(path=str(HERE / f"preview-cal-meals-{w}x{h}.png"))
        # live update check
        pg.evaluate(f"()=>{{const k='dash-meals:{(t-datetime.timedelta(days=(t.weekday()+1)%7)).isoformat()}';const o=JSON.parse(localStorage.getItem(k)||'{{}}');o['{t}']='Live Test';localStorage.setItem(k,JSON.stringify(o));window.dashMealTiles()}}")
        print("  live:", pg.inner_text(f".day[data-date='{t}'] .dml")); ctx.close()
