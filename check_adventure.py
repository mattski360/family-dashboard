#!/usr/bin/env python3
"""Playwright (chromium) check of the page-2 random adventure buttons: popup shows a real row, Pick again, x closes,
no page flip / pause while open. Saves preview-adventure.png. Run: /workspace/.venv-shot/bin/python check_adventure.py"""
import shutil, csv, json
from pathlib import Path
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parent
names={k:{r["Name"] for r in csv.DictReader(open(H/f"data/adventures/{k}_adventures.csv"))} for k in ("evening","weekend")}
ok=True
def chk(c,m):
    global ok; ok&=bool(c); print("ok " if c else "FAIL", m)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"),args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":820,"height":1180},device_scale_factor=2,timezone_id="America/Denver")
    pg.add_init_script("if(!sessionStorage.s){sessionStorage.s=1;localStorage.setItem('dash-v3-rot', JSON.stringify({i:1,t:Date.now(),p:0}));}")
    pg.goto((H/"v3/index.html").as_uri()); pg.wait_for_timeout(700)
    st=lambda: pg.evaluate("[document.querySelector('.page.on').id, JSON.parse(localStorage.getItem('dash-v3-rot')), document.body.classList.contains('paused')]")
    for k in ("evening","weekend"):
        bx=pg.locator(f"#adv .ab.{k}").bounding_box(); chk(bx["height"]>=44 and bx["width"]>=44, f"{k} button {bx['width']:.0f}x{bx['height']:.0f}")
        s0=st(); pg.click(f"#adv .ab.{k}"); pg.wait_for_timeout(300)
        n=pg.inner_text("#advn"); chk(pg.is_visible("#advpop") and n in names[k], f"{k} popup shows real row: {n}")
        chk(pg.inner_text("#advc").count("\n")>=2 or len(pg.inner_text("#advc"))>10, "chips: "+pg.inner_text("#advc").replace("\n"," | "))
        if k=="weekend": pg.screenshot(path=str(H/"preview-adventure.png"))
        pg.click("#advagain"); pg.wait_for_timeout(200); n2=pg.inner_text("#advn"); chk(n2 in names[k] and n2!=n, f"pick again -> {n2}")
        pg.wait_for_timeout(1200); s1=st()
        chk(s1[0]==s0[0] and s1[1]["p"]==s0[1]["p"]==0 and not s1[2], f"while open: page {s1[0]}, not paused")
        pg.click("#advx"); pg.wait_for_timeout(300); s2=st()
        chk(not pg.is_visible("#advpop") and s2[0]==s0[0] and s2[1]["p"]==0 and not s2[2], f"closed: page {s2[0]}, p={s2[1]['p']}, paused={s2[2]}")
        chk(abs((s2[1]["t"]-s0[1]["t"]) - 1900) < 900, f"rotation timer shifted by hold ({s2[1]['t']-s0[1]['t']} ms)")
    rec=pg.evaluate("[localStorage.getItem('adv-recent-evening'),localStorage.getItem('adv-recent-weekend')]"); chk(all(rec), "recent lists stored")
    # normal tap elsewhere still flips + pauses
    pg.mouse.click(400,600); pg.wait_for_timeout(300); s3=st(); chk(s3[0]=="p1" and s3[2], f"normal tap flips to {s3[0]}, paused")
    b.close()
print("PASS" if ok else "FAIL")
