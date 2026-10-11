"""The shared validator/writer must match the official sample's nodata mask."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from gems57.grid import load_grid
from gems57.validate import validate

ROOT = Path(__file__).resolve().parents[1]
SPARSE_DIAGNOSTIC = ROOT / "docs" / "downloads" / (
    "58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif"
)


def test_existing_sparse_diagnostic_is_not_official_format_cleared():
    """Its internal zeros-outside preflight is not the official NaN template contract."""
    assert SPARSE_DIAGNOSTIC.is_file()
    g = load_grid()
    receipt = validate(SPARSE_DIAGNOSTIC, footprint=g.footprint, catalogue=g.catalogue)
    assert receipt["checks"]["outside_footprint_nan"] is False
    assert receipt["checks"]["nodata_nan"] is False
    assert receipt["all_checks_passed"] is False
    assert receipt["emitted_positive_pixels"] == 15000
    assert receipt["on_catalogue_positive_pixels"] == 0
