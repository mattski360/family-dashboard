#!/usr/bin/env bash
# Weekly refresh: pull AHS school events, then render index.html.
# A failed school fetch keeps the previous school events and still rebuilds the page.
set -uo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
status=0
"$PY" fetch_school.py "$@" || { echo "[run] fetch_school.py failed (exit $?); building with existing data" >&2; status=1; }
"$PY" build.py || exit 2
exit $status
