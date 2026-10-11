"""Format validator for GEMS submission GeoTIFFs (rules: problem page 'Submission format').

Checks: single band; float32; EPSG:32611; 100 m; shape/transform/bounds identical to the
official sample submission; NaN (or nodata) outside the footprint; no NaN inside the
footprint; every footprint value finite and within [0, 1].
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

EXPECTED_EPSG = 32611
EXPECTED_RES = (100.0, 100.0)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(path, reference) -> dict:
    import rasterio

    checks: dict[str, bool] = {}
    notes: list[str] = []
    with rasterio.open(reference) as r:
        ref = r.read(1).astype(np.float32)
        ref_profile = dict(shape=(r.height, r.width), transform=tuple(r.transform),
                           bounds=tuple(r.bounds), crs=r.crs.to_epsg() if r.crs else None)
    footprint = np.isfinite(ref)
    with rasterio.open(path) as s:
        checks["single_band"] = s.count == 1
        checks["dtype_float32"] = s.dtypes[0] == "float32"
        checks["crs_epsg_32611"] = (s.crs is not None and s.crs.to_epsg() == EXPECTED_EPSG)
        checks["resolution_100m"] = tuple(abs(v) for v in s.res) == EXPECTED_RES
        checks["shape_matches_reference"] = (s.height, s.width) == ref_profile["shape"]
        checks["transform_matches_reference"] = tuple(s.transform)[:6] == ref_profile["transform"][:6]
        checks["bounds_match_reference"] = np.allclose(tuple(s.bounds), ref_profile["bounds"])
        arr = s.read(1).astype(np.float64)
        nodata = s.nodata
    if checks["shape_matches_reference"]:
        inside = arr[footprint]
        checks["no_nan_inside_footprint"] = bool(np.isfinite(inside).all())
        checks["values_in_0_1_inside_footprint"] = bool(np.isfinite(inside).all() and (inside >= 0).all() and (inside <= 1).all())
        outside = arr[~footprint]
        checks["nan_or_nodata_outside_footprint"] = bool(np.all(~np.isfinite(outside) | (outside == nodata if nodata is not None else False)))
        notes.append(f"footprint_px={int(footprint.sum())}")
    else:
        checks["no_nan_inside_footprint"] = False
        checks["values_in_0_1_inside_footprint"] = False
        checks["nan_or_nodata_outside_footprint"] = False
    report = dict(path=str(path), sha256=sha256_file(path), bytes=Path(path).stat().st_size,
                  checks=checks, all_pass=all(checks.values()), notes=notes,
                  reference=str(reference))
    if checks["shape_matches_reference"]:
        inside = arr[footprint]
        report["stats_inside_footprint"] = dict(
            min=float(np.nanmin(inside)), max=float(np.nanmax(inside)),
            n_ones=int((inside == 1.0).sum()), n_zeros=int((inside == 0.0).sum()),
            n_other=int(((inside != 0.0) & (inside != 1.0)).sum()))
    return report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("submission")
    ap.add_argument("--reference", required=True)
    a = ap.parse_args()
    rep = validate(a.submission, a.reference)
    print(json.dumps(rep, indent=2))
    raise SystemExit(0 if rep["all_pass"] else 1)
