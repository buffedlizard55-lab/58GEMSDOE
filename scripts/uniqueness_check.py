#!/usr/bin/env python3
"""Standalone uniqueness / lane-drift check of one candidate GeoTIFF against every registry raster.

Usage: python scripts/uniqueness_check.py <candidate.tif> <label> [--registry DIR]
Registry DIR (default ~/.cache/gems-src) holds shallow clones of the user's public GEMSDOE* repos.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems58 import uniqueness as U  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("candidate")
ap.add_argument("label")
ap.add_argument("--registry", default=str(Path.home() / ".cache/gems-src"))
ap.add_argument("--reference", default=str(Path.home() / ".cache/gems-data/sample_submission.tif"))
a = ap.parse_args()
with rasterio.open(a.reference) as r:
    valid = np.isfinite(r.read(1))
dirs = sorted(str(p) for p in Path(a.registry).glob("*GEMSDOE*") if p.is_dir())
out = ROOT / "registry" / f"uniqueness_{a.label}.csv"
summary = U.run(a.candidate, dirs, valid, out, a.label)
(ROOT / "registry" / f"uniqueness_{a.label}_summary.json").write_text(json.dumps(summary, indent=2, default=float))
print(json.dumps(summary, indent=2, default=float))
