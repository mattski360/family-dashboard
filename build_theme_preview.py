#!/usr/bin/env python3
"""Local-only preview of the monthly themes (build_theme.LIVE stays False for production).
Adds the theme layer to the built landscape/index.html and writes /tmp/themeprev/landscape/index.html; never deployed."""
import sys
from pathlib import Path
import build, build_theme
OUT = Path("/tmp/themeprev/landscape/index.html")
h = build_theme.apply((build.HERE / "landscape" / "index.html").read_text())
if build.private_leaks(h): sys.exit(3)
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(h); print("[theme-preview] wrote", OUT)
