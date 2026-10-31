#!/usr/bin/env python3
"""Stamp grades.<kid>.checked_at in data/dashboard.json after the nightly grades check, whether or not any grade changed.

`as_of` only moves when a kid's grades change, so on its own it can't tell "checked, nothing new" from "check didn't run".
`checked_at` (ISO, America/Denver) records every successful check; `check_status` says how the last check went.
Data only: nothing here is rendered on any page or in any email.

Usage: python3 grades_checked.py luke wyatt tanner              # all three checked fine just now
       python3 grades_checked.py tanner --status signin         # Veracross needed re-sign-in (checked_at not moved)
       python3 grades_checked.py luke --at 2026-10-29T20:12:10-06:00
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
KIDS = ("luke", "wyatt", "tanner")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kids", nargs="+", choices=KIDS)
    ap.add_argument("--status", default="ok", help="ok (default) | signin | error | any short note")
    ap.add_argument("--at", help="check time (ISO); default now")
    ap.add_argument("--json", default=str(HERE / "data" / "dashboard.json"))
    a = ap.parse_args()
    at = dt.datetime.fromisoformat(a.at) if a.at else dt.datetime.now(ZoneInfo("America/Denver"))
    path = Path(a.json)
    data = json.loads(path.read_text())
    grades = data.setdefault("grades", {})
    for k in a.kids:
        g = grades.setdefault(k, {"connected": False})
        g["check_status"] = a.status
        if a.status == "ok":
            g["checked_at"] = at.isoformat(timespec="seconds")
        else:
            g["check_failed_at"] = at.isoformat(timespec="seconds")
        print(f"[grades] {k}: status={a.status} checked_at={g.get('checked_at')} as_of={g.get('as_of')}")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
