#!/usr/bin/env bash
# Push the built site to Cloudflare Pages.
#   ./deploy.sh --dry-run      print the plan, touch nothing
#   ./deploy.sh                build, check, upload
# Needs: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, PROJECT (default jacaranda-labs)
set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${PROJECT:-jacaranda-labs}"
TOKEN="${CLOUDFLARE_API_TOKEN:-}"
ACCOUNT="${CLOUDFLARE_ACCOUNT_ID:-}"
DRY=0
[[ "${1:-}" == "--dry-run" ]] && DRY=1

say() { printf '\033[1;35m▸\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; exit 1; }

say "building"
python3 build.py --check || die "build or check failed — not deploying"

say "size: $(du -sh dist | cut -f1), files: $(find dist -type f | wc -l | tr -d ' ')"

if [[ $DRY -eq 1 ]]; then
  say "dry run — would upload dist/ to Pages project '$PROJECT' in account '${ACCOUNT:-<unset>}'"
  say "command: npx --yes wrangler@4 pages deploy dist --project-name $PROJECT --commit-dirty=true"
  exit 0
fi

[[ -n "$TOKEN" ]] || die "CLOUDFLARE_API_TOKEN is not set"
[[ -n "$ACCOUNT" ]] || die "CLOUDFLARE_ACCOUNT_ID is not set"

export CLOUDFLARE_API_TOKEN="$TOKEN" CLOUDFLARE_ACCOUNT_ID="$ACCOUNT"
say "uploading to Pages project '$PROJECT'"
npx --yes wrangler@4 pages deploy dist --project-name "$PROJECT" --commit-dirty=true
say "done — check the deployment URL above"
