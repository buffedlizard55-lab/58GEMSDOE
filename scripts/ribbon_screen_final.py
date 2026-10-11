#!/usr/bin/env python3
"""Screen the session-4 delivered raster against the restored public inventory.

Uses the one literal shared gate (``gems57.uniqueness.compare_array_to_registry``)
over ``registry/registry_v3_index.json`` (the 703-entry merged inventory, of which
694 byte-verified witnesses were restored into ``.cache/registry`` this session).
No curated subset, no density exemption, no reverse-overlap clearance.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

from gems57 import uniqueness as U57
from gems58w import grid as g58

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    tif = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "evidence" / "ribbon_v3" / "uniqueness.json"
    idx = json.loads((ROOT / "registry" / "registry_v3_index.json").read_text())
    fp = g58.footprint()
    with rasterio.open(tif) as src:
        arr = src.read(1)
    t0 = time.time()
    rep = U57.compare_array_to_registry(
        arr, idx, fp, progress=(lambda i, n, r: print(f"  {i}/{n}", flush=True)
                                if i % 50 == 0 else None))
    rep["seconds"] = round(time.time() - t0, 1)
    rows = rep.pop("rows", [])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, default=str))
    (out.with_name(out.stem + "_rows.json")).write_text(json.dumps(rows, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items()
                      if k in ("n_compared", "inventory_complete", "missing_or_invalid",
                               "byte_unique_among_checked", "pixel_unique_among_checked",
                               "worst_spearman_full_footprint", "worst_dot_overlap",
                               "worst_jaccard_dot_sets", "duplicate_count", "unique",
                               "verdict", "stop_required", "seconds")}, indent=1, default=str))


if __name__ == "__main__":
    main()
