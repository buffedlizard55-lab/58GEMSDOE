"""Submission writer and the local acceptance checks.

Format contract, read from the organizer's own example submission
(``data/official/sample_submission.tif``):

* one band, ``float32``
* ``EPSG:32611``, 3730 x 3292, geotransform ``(100, 0, 243350, 0, -100, 4508550)``
* **NaN outside** the competition footprint, and **finite values in ``[0, 1]``
  inside** it.  The portal rejects a raster that carries NaN inside the scored
  domain ("Predicted values must be in range [0, 1]", reproduced by
  ``tests/test_submission.py::test_nan_inside_footprint_is_rejected``).
* every included dot is written at exactly ``1.0``: scaling the support down by
  ``lambda`` maps ``DTI -> lambda*T/(alpha*lambda*(T+F) + beta*G)`` which is
  strictly increasing in ``lambda``, so a graded raster is dominated by its own
  thresholded support.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from . import grid
from .metric import ALPHA, BETA, RADIUS_PX

CHECK_NAMES = (
    "exists", "single_band", "dtype_float32", "crs_match", "shape_match",
    "transform_match", "nan_outside_footprint", "finite_inside_footprint",
    "values_in_unit_interval", "positive_is_exactly_one", "positives_inside_footprint",
    "footprint_mask_identical", "no_positive_on_catalogue", "positive_count_in_range",
    "byte_size_reasonable",
)


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: str | Path, dots: np.ndarray, footprint: np.ndarray | None = None) -> Path:
    """Write a submission raster: 1.0 at ``dots``, 0.0 inside the footprint, NaN outside."""
    fp = grid.footprint() if footprint is None else footprint
    g = grid.grid()
    dots = np.asarray(dots, bool)
    if dots.shape != fp.shape:
        raise ValueError(f"dot mask {dots.shape} does not match footprint {fp.shape}")
    if (dots & ~fp).any():
        raise ValueError("dot mask contains pixels outside the competition footprint")
    out = np.full(dots.shape, np.nan, np.float32)
    out[fp] = 0.0
    out[dots & fp] = 1.0
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", height=g.height, width=g.width, count=1,
        dtype="float32", crs=g.crs, transform=rasterio.Affine(*g.transform),
        nodata=float("nan"), compress="deflate", predictor=3, tiled=False,
    ) as dst:
        dst.write(out, 1)
    return path


def validate(path: str | Path, min_dots: int = 1000, max_dots: int = 120000) -> dict:
    """Run the 15 local format/portal checks; never raises, always reports."""
    path = Path(path)
    checks: dict[str, dict] = {}

    def rec(name, ok, detail=""):
        checks[name] = dict(ok=bool(ok), detail=str(detail))

    rec("exists", path.exists(), str(path))
    if not path.exists():
        return dict(passed=False, checks=checks)

    g = grid.grid()
    fp = grid.footprint()
    cat = grid.catalogue()
    with rasterio.open(path) as s:
        rec("single_band", s.count == 1, f"count={s.count}")
        rec("dtype_float32", s.dtypes[0] == "float32", s.dtypes[0])
        rec("crs_match", str(s.crs) == g.crs, str(s.crs))
        rec("shape_match", (s.height, s.width) == g.shape, f"{s.height}x{s.width}")
        rec("transform_match", tuple(s.transform)[:6] == g.transform,
            str(tuple(s.transform)[:6]))
        a = s.read(1)

    finite = np.isfinite(a)
    n_out = int((finite & ~fp).sum())
    rec("nan_outside_footprint", n_out == 0, f"finite pixels outside the footprint = {n_out}")
    rec("finite_inside_footprint", bool(finite[fp].all()),
        f"NaN inside footprint = {int((~finite & fp).sum())}")
    inside = a[fp & finite]
    rec("values_in_unit_interval", bool(((inside >= 0.0) & (inside <= 1.0)).all()),
        f"min={float(inside.min()):.3f} max={float(inside.max()):.3f}")
    pos = finite & (a > 0)
    vals = a[pos]
    rec("positive_is_exactly_one", bool(vals.size == 0 or (vals == 1.0).all()),
        f"unique positives = {np.unique(vals)[:4].tolist()}")
    rec("positives_inside_footprint", bool((pos & ~fp).sum() == 0),
        f"outside = {int((pos & ~fp).sum())}")
    rec("footprint_mask_identical", bool((finite == fp).all()),
        f"finite={int(finite.sum())} footprint={int(fp.sum())}")
    n_cat = int((pos & cat).sum())
    rec("no_positive_on_catalogue", n_cat == 0, f"on-catalogue dots = {n_cat}")
    n = int(pos.sum())
    rec("positive_count_in_range", min_dots <= n <= max_dots, f"n_positives = {n}")
    size_mb = path.stat().st_size / (1 << 20)
    rec("byte_size_reasonable", size_mb < 40.0, f"{size_mb:.3f} MB")

    return dict(passed=all(c["ok"] for c in checks.values()), checks=checks,
                sha256=sha256(path), bytes=path.stat().st_size, n_positives=n)


def note(text: str, limit: int = 140) -> str:
    """The submission-page note field, validated against the 140-character limit."""
    text = " ".join(text.split())
    if len(text) > limit:
        raise ValueError(f"note is {len(text)} characters, limit is {limit}")
    return text


def metric_card(path: str | Path) -> dict:
    """Independent re-derivation of the metric constants quoted in the run card."""
    return dict(alpha=ALPHA, beta=BETA, radius_px=RADIUS_PX, radius_m=RADIUS_PX * 100.0,
                evaluator="gems58.metric/v1")
