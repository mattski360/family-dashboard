#!/usr/bin/env python3
"""Screenshots of the CFM / FSY study popups on landscape/ at 1920x1080 (open + scrolled to bottom)."""
import asyncio, pathlib
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).resolve().parent
URL = (HERE / "landscape" / "index.html").as_uri()
async def main():
    async with async_playwright() as p:
        import shutil; b = await p.chromium.launch(executable_path=shutil.which("google-chrome"), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1920, "height": 1080}, timezone_id="America/Denver")
        await pg.add_init_script("localStorage.setItem('dash-land-rot', JSON.stringify({i:0,t:Date.now(),p:0}))"); await pg.goto(URL); await pg.wait_for_timeout(800)
        await pg.screenshot(path=str(HERE / "shot_study_cards.png"))
        for k in ("cfm", "fsy"):
            await pg.click(f"#p1 .sc.{k}"); await pg.wait_for_timeout(400)
            info = await pg.evaluate(f"(()=>{{var b=document.querySelector('#{k}p .bd');return [b.scrollHeight,b.clientHeight,document.body.classList.contains('paused'),document.querySelector('#{k}p').classList.contains('on')]}})()")
            print(k, "scrollH/clientH/paused/open", info)
            await pg.screenshot(path=str(HERE / f"shot_{k}_popup.png"))
            await pg.evaluate(f"document.querySelector('#{k}p .bd').scrollTop=1e5"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=str(HERE / f"shot_{k}_popup_bottom.png"))
            await pg.mouse.click(5, 5); await pg.wait_for_timeout(200)
            print(k, "closed by outside tap:", not await pg.evaluate(f"document.querySelector('#{k}p').classList.contains('on')"))
        await b.close()
asyncio.run(main())
