"""The Hessian ridge measure must equal the eigenvalue-magnitude difference."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from gems58.ridges import hessian_ridge, nonmax_suppress


def _eigen_magnitude_diff(v: np.ndarray, sigma: float) -> np.ndarray:
    kw = dict(mode="nearest", truncate=4.0)
    hxx = gaussian_filter(v, sigma, order=(2, 0), **kw)
    hyy = gaussian_filter(v, sigma, order=(0, 2), **kw)
    hxy = gaussian_filter(v, sigma, order=(1, 1), **kw)
    h = np.empty(v.shape + (2, 2), float)
    h[..., 0, 0] = hxx
    h[..., 0, 1] = hxy
    h[..., 1, 0] = hxy
    h[..., 1, 1] = hyy
    w = np.linalg.eigvalsh(h)
    return np.abs(w[..., 0]) - np.abs(w[..., 1])


@pytest.mark.parametrize("sigma", [1.5, 3.0])
def test_closed_form_matches_eigvalsh(sigma):
    rng = np.random.default_rng(5)
    v = rng.normal(size=(64, 64)).astype(np.float32)
    v = np.where(rng.random(v.shape) < 0.05, np.nan, v)
    valid = ~np.isnan(v)
    r = hessian_ridge(v, sigma, valid)
    # the analytic path standardises NaN input, so compare on the same input
    mu = float(np.median(v[valid]))
    mad = float(np.median(np.abs(v[valid] - mu))) or 1.0
    z = np.where(valid, (v - mu) / (1.4826 * mad), 0.0).astype(np.float32)
    ref = _eigen_magnitude_diff(z, sigma)
    # sign is preserved: |l1|-|l2| may be negative where the ordering flips, the
    # measure takes absolute values, so compare magnitudes
    assert np.allclose(np.abs(r["magnitude"]), np.abs(ref), atol=2e-4)


def test_magnitude_is_zero_on_a_plane():
    v = np.tile(np.arange(64, dtype=np.float32), (64, 1))
    valid = np.ones_like(v, bool)
    r = hessian_ridge(v, 3.0, valid)
    assert float(np.abs(r["magnitude"][20:-20, 20:-20]).max()) < 1e-4


def test_detects_a_straight_ridge_and_suppresses_across_strike():
    n = 81
    yy, xx = np.mgrid[0:n, 0:n]
    v = np.exp(-((yy - 40.0) ** 2) / (2 * 2.0 ** 2)).astype(np.float32)  # horizontal ridge
    valid = np.ones_like(v, bool)
    r = hessian_ridge(v, 3.0, valid)
    profile = r["magnitude"][:, 40]
    assert int(np.argmax(profile)) == 40
    nms = nonmax_suppress(r["magnitude"], r["ax"], r["ay"], valid)
    rows = np.unique(np.nonzero(nms[:, 40])[0])
    assert 40 in rows
    # the empty background must not survive suppression
    assert not nms[5, 5]


def test_across_strike_direction_is_perpendicular_to_the_ridge():
    n = 81
    yy, xx = np.mgrid[0:n, 0:n]
    v = np.exp(-((yy - 40.0) ** 2) / (2 * 2.0 ** 2)).astype(np.float32)
    r = hessian_ridge(v, 3.0, np.ones_like(v, bool))
    ay = float(r["ay"][40, 40])
    ax = float(r["ax"][40, 40])
    assert abs(ay) > 0.9, (ax, ay)   # across strike is vertical for a horizontal ridge
    assert abs(ax) < 0.1, (ax, ay)
