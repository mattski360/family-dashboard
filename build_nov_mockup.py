#!/usr/bin/env python3
"""landscape-mock/ preview of the wall-page features (build_features.py) with MOCKUP pill, sample notes and the
gratitude board forced on. Copies the built landscape/index.html, so run after build.py. Exit 3 on a hidden-term leak.
NOTE: landscape/ now already contains the features (prod), so this applies them to template output only if missing."""
import html, json, sys
from pathlib import Path
from build_features import transform, HERE
OUT = HERE / "landscape-mock"

def leaks(h):
    p = HERE / "data" / "private_hide.txt"
    if not p.exists(): return []
    terms = [l.strip().lower() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
    t = h.lower(); t += "\n" + html.unescape(t)
    return [x for x in terms if x in t]

def main():
    src = (HERE / "landscape" / "index.html").read_text()
    if 'id="gcomp"' in src:   # live page already has the features: rebuild the plain page in memory
        import build as _b, copy, datetime as dt
        from zoneinfo import ZoneInfo
        data = json.loads((HERE / "data" / "dashboard.json").read_text())
        now = dt.datetime.now(ZoneInfo(data.get("meta", {}).get("timezone", "America/Denver")))
        src = _b.build_v3(data, now, dt.date.fromisoformat(data["meta"]["week_start"]), template="template_landscape.html", features=False)
    fun = json.loads((HERE / "data" / "daily_fun.json").read_text())
    out = transform(src, fun)
    bad = leaks(out)
    if bad:
        print(f"[nov] ERROR: mockup mentions {len(bad)} hidden term(s); not writing", file=sys.stderr); sys.exit(3)
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(out)
    (OUT / "manifest.webmanifest").write_text((HERE / "landscape" / "manifest.webmanifest").read_text())
    print(f"[nov] wrote {OUT / 'index.html'} ({len(out)} bytes)")

if __name__ == "__main__":
    main()
