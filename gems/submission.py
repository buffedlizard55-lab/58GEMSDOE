"""Write and validate GEMS submission GeoTIFFs.

Checks follow the third-party guide's validator list (section 53) and the organizer
reference notebook (cell 19: single band, CRS and transform copied from the fault labels).

Reference grid, from the organizer reference notebook (unet-mc-cv-reference-solution.ipynb):
    width 3292, height 3730, EPSG:32611, 100 m, float32 output.
Transform origin (243350, 4508550) comes ONLY from the third-party inventory
(data_inventory.json in Aayushk333/gems-prize-challenge). It is UNVERIFIED here. The
authoritative grid is the downloaded example_submission.tif, so `validate` and `write`
must be given that file as `reference` whenever it is available.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

EXPECTED_CRS = "EPSG:32611"
EXPECTED_SHAPE = (3730, 3292)  # (height, width)
SPEC_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)  # UNVERIFIED, see docstring


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_grid(reference: str | Path) -> dict:
    """Grid spec + valid footprint (finite cells) of an authoritative reference raster."""
    with rasterio.open(reference) as src:
        arr = src.read(1).astype(np.float64)
        nodata = src.nodata
        valid = np.isfinite(arr)
        if nodata is not None and np.isfinite(nodata):
            valid &= arr != nodata
        return {"crs": src.crs.to_string(), "transform": src.transform,
                "shape": (src.height, src.width), "valid": valid, "source": str(reference)}


def validate(path: str | Path, reference: str | Path | None = None) -> dict:
    """Return a report dict with `passed` plus per-check results. Never raises on bad content."""
    path = Path(path)
    checks: dict[str, bool] = {}
    notes: list[str] = []
    report: dict = {"file": str(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}

    if reference is not None:
        grid = read_grid(reference)
        report["grid_source"] = f"reference:{reference}"
    else:
        grid = {"crs": EXPECTED_CRS, "transform": SPEC_TRANSFORM, "shape": EXPECTED_SHAPE,
                "valid": None, "source": "spec-only"}
        notes.append("SPEC-ONLY VALIDATION: no example_submission.tif supplied. Transform and "
                     "valid footprint are unverified; do not upload without a reference check.")
        report["grid_source"] = "spec-only"

    with rasterio.open(path) as src:
        checks["one_band"] = src.count == 1
        checks["dtype_float32"] = src.dtypes[0] == "float32"
        checks["crs_match"] = src.crs is not None and src.crs.to_string() == grid["crs"]
        checks["transform_match"] = tuple(src.transform)[:6] == tuple(grid["transform"])[:6]
        checks["shape_match"] = (src.height, src.width) == tuple(grid["shape"])
        arr = src.read(1).astype(np.float64)

    if checks["shape_match"]:
        if grid["valid"] is not None:
            valid = grid["valid"]
            inside = arr[valid]
            outside = arr[~valid]
            checks["finite_inside_footprint"] = bool(np.all(np.isfinite(inside)))
            checks["nan_outside_footprint"] = bool(np.all(~np.isfinite(outside)))
            checks["in_unit_interval"] = bool(np.all((inside >= 0) & (inside <= 1)))
        else:
            fin = arr[np.isfinite(arr)]
            checks["in_unit_interval"] = bool(np.all((fin >= 0) & (fin <= 1)))
            checks["finite_inside_footprint"] = None
            checks["nan_outside_footprint"] = None
            notes.append("No footprint available, so NaN placement was not checked.")
        finite = arr[np.isfinite(arr)]
        checks["not_constant"] = bool(finite.size > 0 and finite.min() != finite.max())
        report["stats"] = {
            "min": float(finite.min()) if finite.size else None,
            "max": float(finite.max()) if finite.size else None,
            "mean": float(finite.mean()) if finite.size else None,
            "n_finite": int(finite.size),
            "n_nan": int(arr.size - finite.size),
        }

    hard = [k for k, v in checks.items() if v is False]
    report["checks"] = checks
    report["notes"] = notes
    report["failed_checks"] = hard
    report["passed"] = len(hard) == 0 and all(v is not None for v in checks.values()) \
        if reference is not None else len(hard) == 0
    return report


def write(prob: np.ndarray, out_path: str | Path, reference: str | Path,
          footprint: np.ndarray | None = None) -> dict:
    """Write a validated GeoTIFF with the reference CRS/transform.

    prob      : (H, W) probabilities. Must be finite and in [0,1] inside the footprint.
    footprint : bool (H, W); defaults to the reference footprint. Cells outside are written NaN.
    """
    grid = read_grid(reference)
    if prob.shape != grid["shape"]:
        raise ValueError(f"shape {prob.shape} != reference {grid['shape']}")
    fp = grid["valid"] if footprint is None else footprint.astype(bool)
    if fp is None:
        raise ValueError("no footprint: pass footprint= or a reference with valid cells")
    inside = prob[fp]
    if not np.all(np.isfinite(inside)):
        raise ValueError("non-finite predictions inside the footprint")
    if inside.min() < 0 or inside.max() > 1:
        raise ValueError(f"predictions outside [0,1]: min={inside.min()} max={inside.max()}")
    out = np.where(fp, prob, np.nan).astype(np.float32)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_path, "w", driver="GTiff", height=out.shape[0], width=out.shape[1], count=1,
        dtype="float32", crs=grid["crs"], transform=grid["transform"], nodata=np.nan,
        compress="deflate", tiled=True, blockxsize=256, blockysize=256,
    ) as dst:
        dst.write(out, 1)
    report = validate(out_path, reference=reference)
    report_path = out_path.with_suffix(".validation.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))
    return report
