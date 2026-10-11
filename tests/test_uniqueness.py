"""The uniqueness screen must flag near-duplicates and clear distinct rasters."""

from __future__ import annotations

import numpy as np
import pytest
import rasterio

from gems58 import grid, uniqueness


@pytest.fixture(scope="module")
def reg(tmp_path_factory):
    d = tmp_path_factory.mktemp("reg")
    fp = grid.footprint()
    g = grid.grid()
    a = np.full(fp.shape, np.nan, np.float32)
    a[fp] = 0.0
    a[1000:1005, 1000:1005] = 1.0
    for name in ("a.tif", "b.tif"):
        with rasterio.open(d / name, "w", driver="GTiff", height=g.height, width=g.width,
                           count=1, dtype="float32", crs=g.crs,
                           transform=rasterio.Affine(*g.transform), nodata=float("nan")) as s:
            s.write(a, 1)
    return d


def test_identical_raster_triggers_both_legs(reg):
    fp = grid.footprint()
    dots = np.zeros(fp.shape, bool)
    dots[1000:1005, 1000:1005] = True
    rows, summary = uniqueness.screen_against(dots, reg)
    assert summary["n_checked"] == 2
    for r in rows:
        assert r.forward_overlap == pytest.approx(1.0)
        assert "forward_overlap" in r.triggers


def test_disjoint_raster_clears(reg):
    fp = grid.footprint()
    dots = np.zeros(fp.shape, bool)
    dots[3000:3005, 3000:3005] = True
    rows, summary = uniqueness.screen_against(dots, reg)
    for r in rows:
        assert r.forward_overlap == pytest.approx(0.0)
        assert r.triggers == ()
    assert summary["n_triggers"] == 0


def test_spearman_matches_scipy_definition():
    rng = np.random.default_rng(4)
    x = rng.normal(size=500)
    y = x * 0.7 + rng.normal(size=500)
    got = uniqueness.spearman(x, y)
    exp = np.corrcoef(uniqueness._ranks(x), uniqueness._ranks(y))[0, 1]
    assert got == pytest.approx(exp, abs=1e-9)
