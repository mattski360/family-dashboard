#!/usr/bin/env bash
# Weekly refresh: pull AHS school events + ward-site youth fallback, then render index.html.
# A failed fetch keeps the previous data and the page is still rebuilt.
set -uo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
status=0
"$PY" fetch_school.py "$@" || { echo "[run] fetch_school.py failed; building with existing school data" >&2; status=1; }
"$PY" fetch_youth.py      || { echo "[run] fetch_youth.py failed; keeping existing youth data" >&2; status=1; }
"$PY" build.py || exit 2
exit $status
