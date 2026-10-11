"""Submission validator: the checks the competition upload rejects on, plus project checks.

Mirrors the example_submission.tif template: single band, float32, EPSG:32611, 3292x3730 grid,
100 m, origin (243350, 4508550), NaN outside the scoring footprint, values in [0, 1] inside it.
Footprint = existing_faults.tif != -1 (the template's NaN mask equals this exactly; verified).
"""
from __future__ import annotations

import numpy as np
import rasterio


def validate(path, template_path, footprint_path=None) -> dict:
    checks = {}
    with rasterio.open(template_path) as t:
        tmpl_crs, tmpl_shape, tmpl_tf = t.crs.to_string(), (t.height, t.width), tuple(t.transform)[:6]
        tmpl = t.read(1)
    with rasterio.open(path) as s:
        checks["single_band"] = s.count == 1
        checks["dtype_float32"] = s.dtypes[0] == "float32"
        checks["crs_matches_template"] = s.crs is not None and s.crs.to_string() == tmpl_crs
        checks["shape_matches_template"] = (s.height, s.width) == tmpl_shape
        checks["transform_matches_template"] = tuple(s.transform)[:6] == tmpl_tf
        a = s.read(1).astype(np.float64)
        report = {"crs": s.crs.to_string(), "shape": [s.height, s.width], "nodata": s.nodata,
                  "transform": list(tuple(s.transform)[:6])}
    footprint = (tmpl != -1) if footprint_path is None else footprint_path
    inside = a[footprint]
    outside = a[~footprint]
    checks["no_nan_inside_footprint"] = bool(np.isfinite(inside).all())
    checks["no_inf_anywhere"] = bool(not np.isinf(a).any())
    checks["values_in_0_1_inside"] = bool(np.isfinite(inside).all() and (inside >= 0).all() and (inside <= 1).all())
    checks["outside_footprint_nan_or_zero"] = bool(np.all(np.isnan(outside) | (outside == 0)))
    checks["all_checks_passed"] = all(checks.values())
    report.update(checks=checks, footprint_px=int(footprint.sum()),
                  min_inside=float(np.nanmin(inside)), max_inside=float(np.nanmax(inside)),
                  positive_px=int((inside > 0).sum()))
    return report
