#!/usr/bin/env python3
"""Place the official competition rasters into data/ (git-ignored), sha256-verified.

Source chain (see docs/sources.md): the official DrivenData Dropbox mirrors were copied into the
GEMSDOE repo's data/bridge/ (split into <=90 MiB parts) with pinned sha256 values in
data/bridge/manifest.json. This script sparse-clones only data/bridge from GitHub, reassembles
the feature stack, checks every part and whole-file hash, and writes the canonical names.
The hashes prove the bytes match the pins; they do NOT independently re-verify the DrivenData
origin (that site is unreachable from the sandbox).
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SRC = Path("/tmp/gemsdoe_bridge_src")
REPO = "https://github.com/buffedlizard55-lab/GEMSDOE"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not (SRC / "data" / "bridge" / "manifest.json").exists():
        if SRC.exists():
            shutil.rmtree(SRC)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", REPO, str(SRC)], check=True)
        subprocess.run(["git", "-C", str(SRC), "sparse-checkout", "set", "data/bridge"], check=True)
    bridge = SRC / "data" / "bridge"
    man = json.loads((bridge / "manifest.json").read_text())
    DATA.mkdir(exist_ok=True)
    feats = next(f for f in man["files"] if f["canonical"] == "training_features.tif")
    parts = [bridge / p["name"] for p in feats["parts"]]
    for part, meta in zip(parts, feats["parts"]):
        if sha256(part) != meta["sha256"]:
            print("PART HASH MISMATCH", part.name)
            return 1
    out = DATA / "training_features.tif"
    with open(out, "wb") as w:
        for part in parts:
            w.write(part.read_bytes())
    if sha256(out) != feats["sha256"]:
        print("WHOLE-FILE HASH MISMATCH for training_features.tif")
        return 1
    for f in man["files"]:
        if f["canonical"] == "training_features.tif":
            continue
        dst = DATA / f["canonical"]
        shutil.copyfile(bridge / f["name"], dst)
        if sha256(dst) != f["sha256"]:
            print("HASH MISMATCH", dst.name)
            return 1
    print("OK: data/ placed and sha256-verified")
    for f in man["files"]:
        print(f"  {f['canonical']}  sha256={f['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
