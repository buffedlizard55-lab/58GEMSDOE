#!/usr/bin/env bash
# Restore the byte-verified public registry witnesses used by the uniqueness screens.
#
# Every raster is a git blob pinned by sha256 in evidence/registry_scan_index.json.
# The bytes are deliberately kept OUT of git (they are large and third-party); this
# script restores them into a cache directory so `scripts/gems60_screen.py` and
# `registry/uniqueness_full_inventory.json` can be reproduced exactly.
#
#   bash scripts/fetch_registry_witnesses.sh [cache_dir]
#
# Requires an authenticated `gh` (the blob API).  Blobs larger than MAX_BYTES are
# skipped and reported; their sha256 stays in the index for a future restore.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$HOME/.cache/gems/registry_witnesses}"
MAX_BYTES="${MAX_BYTES:-6000000}"
JOBS="${JOBS:-8}"
mkdir -p "$OUT" || exit 1

QUEUE="$(mktemp)"
python3 - "$ROOT" "$MAX_BYTES" > "$QUEUE" <<'PY'
import json, sys
root, max_bytes = sys.argv[1], int(sys.argv[2])
idx = json.load(open(f"{root}/evidence/registry_scan_index.json"))
for e in idx:
    if not e.get("blob") or not e.get("sha256"):
        continue
    if int(e.get("bytes") or 0) > max_bytes:
        continue
    print(f"{e['repo_first']}\t{e['blob']}\t{e['sha256']}")
PY

fetch_one() {
  local repo="$1" blob="$2" sha="$3"
  local f="$OUT/$sha.tif"
  [[ -s "$f" ]] && { echo "have $sha"; return; }
  local tmp="$f.b64"
  if timeout 180 gh api "repos/buffedlizard55-lab/$repo/git/blobs/$blob" --jq .content > "$tmp" 2>/dev/null && [[ -s "$tmp" ]]; then
    if base64 -d "$tmp" > "$f.part" 2>/dev/null; then
      local got; got="$(sha256sum "$f.part" | cut -d' ' -f1)"
      if [[ "$got" == "$sha" ]]; then mv "$f.part" "$f"; echo "ok   ${sha:0:12}"; else rm -f "$f.part"; echo "MISMATCH ${sha:0:12}"; fi
    else rm -f "$f.part"; echo "B64FAIL ${sha:0:12}"; fi
  else
    echo "FAIL ${sha:0:12}"
  fi
  rm -f "$tmp"
}
export -f fetch_one
export OUT

cut -f1-3 "$QUEUE" | xargs -P "$JOBS" -I{} bash -c 'IFS=$'"'"'\t'"'"' read -r a b c <<< "{}"; fetch_one "$a" "$b" "$c"'
rm -f "$QUEUE"
echo "---"
echo "cached: $(ls "$OUT"/*.tif 2>/dev/null | wc -l) rasters in $OUT"
du -sh "$OUT" 2>/dev/null
