#!/usr/bin/env python3
"""Meal planner shots + geometry: main page card, open planner, open picker (local build)."""
import shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
URL = (HERE / "landscape" / "index.html").as_uri()
CHK = """() => { const R = e => { const b = e.getBoundingClientRect(); return [b.left,b.top,b.right,b.bottom].map(Math.round) };
 const pg=document.querySelector('.page.on'), W=innerWidth, H=innerHeight; const hit=(a,b)=>a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom;
 const btn=document.getElementById('chbtn').getBoundingClientRect();
 const leafs=[...pg.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent!==null&&e.getBoundingClientRect().width);
 const over=leafs.filter(e=>hit(e.getBoundingClientRect(),btn)).map(e=>e.className||e.tagName);
 const cut=leafs.filter(e=>{const b=e.getBoundingClientRect();return b.right>W+1||b.bottom>H+1||b.left<-1}).map(e=>e.className||e.tagName);
 const pr=pg.getBoundingClientRect(); const clipped=[...pg.children].filter(e=>e.getBoundingClientRect().bottom>pr.bottom+1).map(e=>e.className);
 const ml=document.getElementById('mlcard'); return {page:pg.id, chbtn:R(document.getElementById('chbtn')), meal: ml&&ml.offsetParent?R(ml):null, overlapChores:over, cut, clipped,
   mealVsChores: ml&&ml.offsetParent? hit(ml.getBoundingClientRect(),btn):null, chText: document.getElementById('chbtn').innerText.replace(/\\n/g,' ')} }"""
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=shutil.which("google-chrome"), args=["--no-sandbox"])
    for w, h in ((1920, 1080), (1280, 800)):
        ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, timezone_id="America/Denver")
        pg = ctx.new_page(); pg.add_init_script("if(!sessionStorage.x){localStorage.clear();sessionStorage.x=1}localStorage.setItem('dash-land-rot', JSON.stringify({i:0,t:Date.now(),p:0}))")
        pg.goto(URL); pg.wait_for_timeout(1500)
        print(w, h, pg.evaluate(CHK)); pg.screenshot(path=str(HERE / f"preview-v2-p1-{w}x{h}.png"))
        pg.evaluate("document.querySelector('#nav .dot[data-i=\"1\"]').click()"); pg.wait_for_timeout(1500)
        print(w, h, pg.evaluate(CHK)); pg.screenshot(path=str(HERE / f"preview-v2-p2-{w}x{h}.png"))
        pg.tap("#chbtn"); pg.wait_for_timeout(400); pg.screenshot(path=str(HERE / f"preview-v2-chores-{w}x{h}.png")); pg.tap("#chp .x")
        pg.evaluate("document.querySelector('#nav .dot[data-i=\"0\"]').click()"); pg.wait_for_timeout(1200)
        pg.tap("#mlcard"); pg.wait_for_timeout(300)
        pg.tap("#mlp .dt.today"); pg.wait_for_timeout(200); pg.tap("#mlk .mb >> nth=0"); pg.wait_for_timeout(200)
        pg.tap("#mlp .dt >> nth=2"); pg.wait_for_timeout(200)
        pg.tap("#mlk .chip[data-f=kids]"); pg.wait_for_timeout(200)
        pg.screenshot(path=str(HERE / f"preview-v2-picker-{w}x{h}.png"))
        pg.tap("#mlk [data-act=back]"); pg.tap("#mlp [data-act=fill]"); pg.wait_for_timeout(200)
        g = pg.evaluate("()=>{const c=document.querySelector('#mlp .mc').getBoundingClientRect();return {cut:[...document.querySelectorAll('#mlp .mc *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&e.offsetParent&&(r.bottom>c.bottom+1||r.right>c.right+1)}).length, held: !!document.querySelector('.pz') && getComputedStyle(document.querySelector('#nav .pz')).display}}")
        print("  planner", g); pg.screenshot(path=str(HERE / f"preview-v2-planner-{w}x{h}.png"))
        pg.tap("#mlp .x"); pg.wait_for_timeout(300); print("  card:", pg.inner_text("#mlcard").replace("\n", " | "))
        ctx.close()
