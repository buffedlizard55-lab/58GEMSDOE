#!/usr/bin/env bash
# Rebuild the local input cache (NOT committed) from the user's public GitHub mirror of the
# official competition rasters. Pins are read from the mirror's manifest.json and checked:
# every part first, then the reassembled file and the two label/sample rasters.
# Provenance caveat: the pins are self-reported by the mirror (README irregularity I-2).
set -euo pipefail
CACHE="${GEMS_CACHE:-$HOME/.cache}"
SRC="$CACHE/gems-src"
DATA="$CACHE/gems-data"
mkdir -p "$SRC" "$DATA"
if [ ! -d "$SRC/6GEMSDOE/.git" ] && [ ! -d "$SRC/6GEMSDOE/data/bridge" ]; then
  git clone --depth 1 https://github.com/buffedlizard55-lab/6GEMSDOE.git "$SRC/6GEMSDOE"
fi
B="$SRC/6GEMSDOE/data/bridge"
python3 - "$B" "$DATA" <<'PY'
import hashlib, json, pathlib, shutil, sys
bridge, data = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
m = json.loads((bridge / "manifest.json").read_text())
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()
def check(path, want):
    got = sha(path)
    if got != want:
        sys.exit(f"SHA MISMATCH {path}: got {got} want {want}")
    print("OK ", path.name)
for f in m["files"]:
    if "parts" in f:
        out = data / f["name"]
        with open(out, "wb") as dst:
            for p in f["parts"]:
                check(bridge / p["name"], p["sha256"])
                with open(bridge / p["name"], "rb") as src_:
                    shutil.copyfileobj(src_, dst, 1 << 24)
        check(out, f["sha256"])
    else:
        out = data / (f["canonical"])
        shutil.copyfile(bridge / f["name"], out)
        check(out, f["sha256"])
PY
echo "inputs ready in $DATA"
