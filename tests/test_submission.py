import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from gems.submission import read_grid, validate, write

H, W = 30, 40
T = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


@pytest.fixture()
def reference(tmp_path):
    """Synthetic stand-in for example_submission.tif: NaN outside a rectangle. NOT competition data."""
    ref = tmp_path / "reference.tif"
    arr = np.full((H, W), np.nan, np.float32)
    arr[5:25, 4:36] = 0.0
    with rasterio.open(ref, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32",
                       crs="EPSG:32611", transform=T, nodata=np.nan) as d:
        d.write(arr, 1)
    return ref


def test_write_then_validate_passes(tmp_path, reference):
    prob = np.random.default_rng(0).random((H, W))
    out = tmp_path / "sub.tif"
    rep = write(prob, out, reference)
    assert rep["passed"], rep["failed_checks"]
    assert rep["checks"]["nan_outside_footprint"] is True
    assert out.with_suffix(".validation.json").exists()
    assert json.loads(out.with_suffix(".validation.json").read_text())["passed"]


def test_write_rejects_out_of_range(tmp_path, reference):
    prob = np.full((H, W), 0.5)
    prob[10, 10] = 1.5
    with pytest.raises(ValueError):
        write(prob, tmp_path / "bad.tif", reference)


def test_write_rejects_nan_inside_footprint(tmp_path, reference):
    prob = np.full((H, W), 0.5)
    prob[10, 10] = np.nan
    with pytest.raises(ValueError):
        write(prob, tmp_path / "bad.tif", reference)


def test_validator_catches_wrong_crs_and_zero_outside(tmp_path, reference):
    bad = tmp_path / "bad.tif"
    with rasterio.open(bad, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32",
                       crs="EPSG:4326", transform=T) as d:
        d.write(np.zeros((H, W), np.float32), 1)
    rep = validate(bad, reference=reference)
    assert not rep["passed"]
    assert "crs_match" in rep["failed_checks"]
    assert "nan_outside_footprint" in rep["failed_checks"]


def test_validator_catches_value_out_of_range(tmp_path, reference):
    bad = tmp_path / "bad.tif"
    arr = np.full((H, W), np.nan, np.float32)
    arr[5:25, 4:36] = 1.0000001
    arr[5, 4] = -1.0
    with rasterio.open(bad, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32",
                       crs="EPSG:32611", transform=T, nodata=np.nan) as d:
        d.write(arr, 1)
    rep = validate(bad, reference=reference)
    assert "in_unit_interval" in rep["failed_checks"]


def test_read_grid_footprint(reference):
    g = read_grid(reference)
    assert g["shape"] == (H, W)
    assert g["valid"].sum() == 20 * 32
