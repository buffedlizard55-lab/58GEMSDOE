#!/usr/bin/env python3
"""Chance-level control for the dot-overlap test: for each flagged registry raster, the fraction of
the footprint lying within 3 px of its dots. A random candidate with the same count of dots would
hit at roughly this rate, so overlap close to it is NOT evidence of shared placement."""
import csv
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
src, out = sys.argv[1], sys.argv[2]
with rasterio.open(Path.home() / ".cache/gems-data/sample_submission.tif") as r:
    valid = np.isfinite(r.read(1))
rows = []
for r_ in csv.DictReader(open(src)):
    if r_.get("flag_overlap") != "True":
        continue
    with rasterio.open(r_["registry_file"]) as s:
        reg = s.read(1).astype(np.float32)
    rdots = (reg >= 0.5) & valid
    cov = float((ndi.distance_transform_edt(~rdots) <= 3.0)[valid].mean())
    rows.append(dict(registry_file=r_["registry_file"], dot_overlap=float(r_["dot_overlap"]),
                     chance_coverage_3px=cov, excess=float(r_["dot_overlap"]) - cov,
                     n_reg_dots=int(r_["n_reg_dots"]), rho=float(r_["rho"])))
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["none"])
    w.writeheader(); w.writerows(rows)
for x in sorted(rows, key=lambda x: -x["excess"])[:30]:
    print(f"{x['dot_overlap']:.3f} chance={x['chance_coverage_3px']:.3f} excess={x['excess']:+.3f} n={x['n_reg_dots']} {x['registry_file'].split('gems-src/')[-1]}")
