#!/usr/bin/env bash
# Publish ONLY the November-features mockup (landscape-mock/) to a Cloudflare Pages PREVIEW branch
# (project family-dashboard, branch "mockup" -> https://mockup.<project>.pages.dev/landscape-mock/).
# Never touches the production branch (main) or the live landscape/ / v3/ pages. Same hidden-term guard (exit 3).
set -euo pipefail
cd "$(dirname "$0")"
ENV=${CF_ENV:-/home/box/.secrets/cloudflare.env}
TOOLS=${CF_TOOLS:-/home/box/cf-tools}
PROJECT=${CF_PROJECT:-family-dashboard}
BRANCH=${CF_BRANCH:-mockup}
[ "$BRANCH" != "main" ] || { echo "[mock] refusing to deploy the mockup to main" >&2; exit 1; }
[ -f landscape-mock/index.html ] || { echo "[mock] run build_nov_mockup.py first" >&2; exit 1; }
[ -f "$ENV" ] || { echo "[mock] no $ENV; skipping" >&2; exit 0; }
set -a; . "$ENV"; set +a
export PATH="$TOOLS/node_modules/.bin:$PATH"
STAGE=$(mktemp -d /tmp/fd-mock-XXXXXX); trap 'rm -rf "$STAGE"' EXIT
cp -r landscape-mock "$STAGE/"
mkdir -p "$STAGE/assets"; for f in assets/*; do case "$f" in *cougar-song.mp3) ;; *) cp -r "$f" "$STAGE/assets/";; esac; done
printf '<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=landscape-mock/"><a href="landscape-mock/">November features mockup</a>\n' > "$STAGE/index.html"
if [ -f data/private_hide.txt ]; then
  python3 - "$STAGE" <<'PY' || { echo "[mock] hidden term found in staged files; NOT deploying" >&2; exit 3; }
import html, pathlib, sys
terms = [l.strip().lower() for l in open("data/private_hide.txt") if l.strip() and not l.startswith("#")]
bad = []
for f in pathlib.Path(sys.argv[1]).rglob("*"):
    if f.is_file():
        t = f.read_bytes().decode("utf-8", "ignore").lower(); t += "\n" + html.unescape(t)
        bad += [f.name for x in terms if x in t]
sys.exit(1 if bad else 0)
PY
fi
cd "$TOOLS"
wrangler pages deploy "$STAGE" --project-name "$PROJECT" --branch "$BRANCH" --commit-dirty=true 2>&1 | grep -v -i "token"
