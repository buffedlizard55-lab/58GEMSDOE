#!/usr/bin/env bash
# Reproduce the official competition feature stack in this sandbox and verify it.
#
# The DrivenData data tab (https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
# requires a login, so this sandbox cannot download it directly.  The same bytes
# ARE published, sha256-pinned, inside the owner's GEMSDOE repository as a
# five-part git bridge (GitHub's 100 MB blob limit forces the split):
#
#   manifest   https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/data/bridge/manifest.json
#   contract   https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/scripts/assemble_data_bridge.py
#
# Pins taken verbatim from that manifest (canonical name: training_features.tif):
#   whole file  418,912,844 B  sha256 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5
#   part-000     94,371,840 B  sha256 0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7
#   part-001     94,371,840 B  sha256 3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50
#   part-002     94,371,840 B  sha256 c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c
#   part-003     94,371,840 B  sha256 b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320
#   part-004     41,425,484 B  sha256 fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696
#
# The output is written OUTSIDE the repository (~/.cache/gems) because a 419 MB
# blob must never enter git.  Fail-closed: nothing downstream may read the stack
# unless every part pin AND the whole-file pin match.
set -euo pipefail

SRC_REPO="${SRC_REPO:-https://github.com/buffedlizard55-lab/GEMSDOE.git}"
WORK="${WORK:-$HOME/.cache/src/GEMSDOE}"
OUT_DIR="${OUT_DIR:-$HOME/.cache/gems}"
OUT="$OUT_DIR/training_features.tif"
WHOLE_SHA="4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
WHOLE_BYTES=418912844
PARTS=(
  "000 0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7"
  "001 3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50"
  "002 c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c"
  "003 b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320"
  "004 fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696"
)

mkdir -p "$OUT_DIR"
if [[ -f "$OUT" ]] && [[ "$(sha256sum "$OUT" | cut -d' ' -f1)" == "$WHOLE_SHA" ]]; then
  echo "OK   $OUT already in place with the pinned sha256 (untouched)"
  exit 0
fi

if [[ ! -d "$WORK/.git" ]]; then
  mkdir -p "$(dirname "$WORK")"
  rm -rf "$WORK"
  git clone --quiet --filter=blob:none --no-checkout --depth 1 "$SRC_REPO" "$WORK"
  git -C "$WORK" sparse-checkout init --no-cone
  git -C "$WORK" sparse-checkout set data/bridge
  git -C "$WORK" checkout main
fi

for entry in "${PARTS[@]}"; do
  idx="${entry%% *}"; want="${entry##* }"
  f="$WORK/data/bridge/gems-geodawn-numerical-features.tif.part-$idx"
  [[ -f "$f" ]] || { echo "FAIL missing $f"; exit 1; }
  got="$(sha256sum "$f" | cut -d' ' -f1)"
  [[ "$got" == "$want" ]] || { echo "FAIL part-$idx sha256 $got != $want"; exit 1; }
  echo "OK   part-$idx sha256 verified"
done

tmp="$OUT.part"
cat "$WORK/data/bridge/gems-geodawn-numerical-features.tif.part-00"{0,1,2,3,4} > "$tmp"
got="$(sha256sum "$tmp" | cut -d' ' -f1)"
size="$(stat -c%s "$tmp")"
if [[ "$got" != "$WHOLE_SHA" || "$size" != "$WHOLE_BYTES" ]]; then
  rm -f "$tmp"
  echo "FAIL reassembled stack $size B sha256 $got != pinned $WHOLE_BYTES B $WHOLE_SHA"
  exit 1
fi
mv "$tmp" "$OUT"
echo "OK   wrote $OUT ($size B, whole-file sha256 verified against the GEMSDOE bridge manifest)"
