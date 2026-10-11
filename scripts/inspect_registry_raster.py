#!/usr/bin/env python3
"""Structural facts for one restored registry raster (REGISTRY-MEASUREMENT).

Usage: inspect_registry_raster.py <sha256-prefix> [--out evidence/x.json]
Reports value set, positive-dot count inside the scored footprint, dots on the
mapped catalogue, and distance (m) from each positive dot to the nearest mapped
catalogue fault. No holdout labels are used; these are geometry facts only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems57.grid import load_grid  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("--out")
    a = ap.parse_args()
    reg = json.loads((ROOT / "registry" / "registry_refreshed.json").read_text())["rasters"]
    hits = [r for r in reg if r["sha256"].startswith(a.prefix)]
    if len(hits) != 1:
        raise SystemExit(f"prefix {a.prefix} matched {len(hits)} rasters")
    rec = hits[0]
    path = ROOT / ".cache" / "registry" / f"{rec['sha256']}.tif"
    g = load_grid(ROOT / "data" / "bridge")
    fp, cat = g.footprint, g.catalogue
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float64)
        crs, shape = str(src.crs), src.shape
    fin = np.isfinite(arr)
    dots = fin & (arr > 0)
    vals = np.unique(arr[fin & fp])
    dist = ndi.distance_transform_edt(~cat, sampling=100.0)
    d = dist[dots & fp]
    out = {
        "evidence_class": "REGISTRY-MEASUREMENT (geometry only, no holdout labels)",
        "sha256": rec["sha256"], "sources": rec["sources"], "crs": crs, "shape": list(shape),
        "values_in_footprint": [float(v) for v in vals[:10]], "n_values": int(vals.size),
        "footprint_cells": int(fp.sum()), "nan_inside_footprint": int((~fin & fp).sum()),
        "nonzero_outside_footprint": int(((arr != 0) & fin & ~fp).sum()),
        "positive_dots_in_footprint": int((dots & fp).sum()),
        "footprint_coverage_by_dots": float((dots & fp).sum() / fp.sum()),
        "positive_dots_on_catalogue": int((dots & cat).sum()),
        "dist_to_catalogue_m": {"median": float(np.median(d)) if d.size else None,
                                "p90": float(np.percentile(d, 90)) if d.size else None,
                                "frac_within_300m": float(np.mean(d <= 300)) if d.size else None},
    }
    txt = json.dumps(out, indent=1)
    print(txt)
    if a.out:
        Path(a.out).write_text(txt + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
