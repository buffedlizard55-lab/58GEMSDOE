import numpy as np
import pytest
rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin
from gems58.validate import validate


def _write(path, arr, nodata=np.nan, crs=32611):
    from rasterio.crs import CRS
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype="float32", crs=CRS.from_epsg(crs), transform=from_origin(0, 1000, 100, 100),
                       nodata=nodata) as d:
        d.write(arr.astype("float32"), 1)


def _ref(tmp_path):
    ref = np.full((10, 12), np.nan, np.float32)
    ref[2:8, 3:9] = 0.0
    p = tmp_path / "ref.tif"
    _write(p, ref)
    return p, ref


def test_good_file_passes(tmp_path):
    rp, ref = _ref(tmp_path)
    out = ref.copy()
    out[3, 4] = 1.0
    p = tmp_path / "ok.tif"
    _write(p, out)
    rep = validate(p, rp)
    assert rep["all_pass"], rep["checks"]


def test_value_above_one_fails(tmp_path):
    rp, ref = _ref(tmp_path)
    out = ref.copy()
    out[3, 4] = 1.5  # the exact error the organizer form reports
    p = tmp_path / "bad.tif"
    _write(p, out)
    rep = validate(p, rp)
    assert not rep["checks"]["values_in_0_1_inside_footprint"]


def test_nan_inside_footprint_fails(tmp_path):
    rp, ref = _ref(tmp_path)
    out = ref.copy()
    out[4, 4] = np.nan
    p = tmp_path / "nan.tif"
    _write(p, out)
    assert not validate(p, rp)["checks"]["no_nan_inside_footprint"]


def test_wrong_crs_fails(tmp_path):
    rp, ref = _ref(tmp_path)
    p = tmp_path / "crs.tif"
    _write(p, ref, crs=4326)
    assert not validate(p, rp)["checks"]["crs_epsg_32611"]
