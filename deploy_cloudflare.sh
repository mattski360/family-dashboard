#!/usr/bin/env bash
# Publish the built pages to Cloudflare Pages (project family-dashboard, branch main).
# Stages ONLY public output (index.html, v2/, v3/, landscape/, assets/, and the landscape-a/ + landscape-b/ redirects)
# -- never data/, scripts, private_hide.txt or previews -- and refuses to deploy (exit 3) if a hidden term appears in any staged file.
# Needs /home/box/.secrets/cloudflare.env (CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID) and wrangler + Node 22 in
# /home/box/cf-tools (npm i node@22 wrangler). Exits 0 quietly-skipped (with a note) if the credentials are missing.
set -euo pipefail
cd "$(dirname "$0")"
ENV=${CF_ENV:-/home/box/.secrets/cloudflare.env}
TOOLS=${CF_TOOLS:-/home/box/cf-tools}
PROJECT=${CF_PROJECT:-family-dashboard}
[ -f "$ENV" ] || { echo "[cf] no $ENV; skipping Cloudflare deploy" >&2; exit 0; }
set -a; . "$ENV"; set +a
export PATH="$TOOLS/node_modules/.bin:$PATH"
STAGE=$(mktemp -d /tmp/fd-cf-XXXXXX); trap 'rm -rf "$STAGE"' EXIT
cp index.html "$STAGE/"
for d in v2 v3 landscape landscape-a landscape-b assets; do   # (old chores-*/cfm-* mockups no longer published)
  [ -d "$d" ] && cp -r "$d" "$STAGE/"; done
# fight song (gitignored, Cloudflare only): enable it in the staged pages
if [ -f "$STAGE/assets/cougar-song.mp3" ]; then
  for f in "$STAGE"/v3/index.html "$STAGE"/landscape/index.html; do
    [ -f "$f" ] && sed -i -E 's/data-song="" data-song-cf="([^"]+)"/data-song="\1" data-song-cf="\1"/' "$f"
  done
fi
# chore song (gitignored, Cloudflare only): enable it in every staged page that has the Chores panel
if [ -f "$STAGE/assets/chore-song.mp3" ]; then
  { grep -rl --include=index.html 'data-chsong=""' "$STAGE" || true; } | while read -r f; do
    sed -i -E 's/data-chsong="" data-chsong-cf="([^"]+)"/data-chsong="\1" data-chsong-cf="\1"/' "$f"
  done
fi
if [ -f data/private_hide.txt ]; then
  python3 - "$STAGE" <<'PY' || { echo "[cf] hidden term found in staged files; NOT deploying" >&2; exit 3; }
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
cd "$TOOLS"   # wrangler needs a writable node_modules cache
wrangler pages deploy "$STAGE" --project-name "$PROJECT" --branch main --commit-dirty=true 2>&1 | grep -v -i "token"
