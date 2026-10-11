#!/usr/bin/env bash
# Restore the extended evidence mirrors used by the gems61 ribbon lane.
#
# These are the official USGS/DOE GeoDAWN and 3DEP-derived products that the
# organizer's own 19-band stack does NOT contain (radioelement channels and the
# 1 m lidar scarp morphology), published as hash-pinned mirrors by the owner in
# the public repository buffedlizard55-lab/60GEMSDOE.
#
# Provenance (see data/external/gems61_extension_pins.json for the full record):
#   rad / extensions  USGS GeoDAWN airborne radiometric release        (public domain)
#   lidar scarp       derived from 706 USGS 3DEP 1 m DEM tiles         (public domain)
#   dem10 chi/knick   derived from USGS 3DEP 1/3 arc-second DEM        (public domain)
#   DEM mirror        GeoDAWN-area elevation reduced to the 100 m grid (USGS)
#
# Transport provenance only: these hashes authenticate the bytes that this
# repository ships, not an organizer signature.  The lane uses the 8-bit mirrors
# ordinal-only (see src/gems61/layers.py), because their physical scaling is not
# published in this checkout.
#
#   bash scripts/gems61_fetch_extended.sh [cache_dir]
#
# Default cache_dir = .cache/gems58/src60/data (outside git; .cache/ is ignored).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${1:-$ROOT/.cache/gems58}"
SRC="$CACHE/src60"
SRC_REPO="${SRC_REPO:-https://github.com/buffedlizard55-lab/60GEMSDOE.git}"
# The checkout is the mirror repository's default branch (`main`); the pins below are
# file hashes from its `data/restore_receipt.json`, verified byte-for-byte after fetch.
# (An earlier draft of this script carried the rad_u8 file hash in a COMMIT variable —
# that was never a commit id and is removed so it cannot be mistaken for one.)

mkdir -p "$CACHE"
if [ ! -d "$SRC/.git" ]; then
  rm -rf "$SRC"
  git clone --filter=blob:none --no-checkout --depth 1 "$SRC_REPO" "$SRC"
  git -C "$SRC" sparse-checkout init --no-cone
  git -C "$SRC" sparse-checkout set 'data/external/*' 'data/geodawn_dem_a2_100m.tif' 'data/*.json'
  git -C "$SRC" checkout main
fi

python3 - "$ROOT" "$SRC" <<'PY'
import hashlib, json, sys
from pathlib import Path

root, src = Path(sys.argv[1]), Path(sys.argv[2])
pins = json.loads((root / "data" / "external" / "gems61_extension_pins.json").read_text())
bad = 0
for rel, rec in pins["files"].items():
    p = src / rec["mirror_path"]
    if not p.exists():
        print(f"MISSING {rel}  ({rec['mirror_path']})")
        bad += 1
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    ok = h == rec["sha256"]
    print(f"{'OK  ' if ok else 'FAIL'} {rel:34s} {p.stat().st_size:>10d} B  {h[:16]}…")
    bad += 0 if ok else 1
print(f"--- {len(pins['files']) - bad}/{len(pins['files'])} mirrors verified against the published pins")
sys.exit(1 if bad else 0)
PY
