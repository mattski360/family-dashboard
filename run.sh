#!/usr/bin/env bash
# Weekly refresh: pull AHS school events, ward-site youth fallback and BYU football/basketball games, then render v3/index.html.
# fetch_byu.py also refreshes sports.byu.summary (record, Big 12 standing, AP/Coaches/CFP ranks) for the BYU "Y" easter-egg popup.
# (index.html and v2/index.html are static redirects to v3/ and are not rebuilt.)
# A failed fetch keeps the previous data and the page is still rebuilt.
# build.py exits 3 (and writes nothing) if a term from data/private_hide.txt would appear on the page; run.sh then exits 2.
set -uo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
status=0
"$PY" fetch_school.py "$@" || { echo "[run] fetch_school.py failed; building with existing school data" >&2; status=1; }
"$PY" fetch_youth.py      || { echo "[run] fetch_youth.py failed; keeping existing youth data" >&2; status=1; }
"$PY" fetch_byu.py        || { echo "[run] fetch_byu.py failed; keeping last good BYU games" >&2; status=1; }
"$PY" build.py || exit 2
# Also publish to Cloudflare Pages (family-dashboard-5rk.pages.dev) while GitHub Pages stays on; skipped if no credentials.
./deploy_cloudflare.sh || { echo "[run] Cloudflare deploy failed (GitHub copy still published by the push)" >&2; status=1; }
exit $status
