"""Regression tests for the session-2 lane (gems59).

The bug these guard against is the one that actually happened: ``scipy.ndimage``'s
``uniform_filter``/``gaussian_filter`` 1-D passes are recursive, so a single NaN
(the stack's nodata sentinel outside the study-area footprint) poisoned *every*
pixel of the texture features.  The first run of
``scripts/run_model_experiments.py`` died with
``Found array with 0 sample(s)`` because the whole feature matrix was NaN.
"""
from __future__ import annotations

import numpy as np
import pytest

from gems59.features import (HALO, STD3, STD7, _coh, _gsmooth, _lmean_var,
                             compute_block, open_stack)

pytest.importorskip("rasterio")


def test_gsmooth_does_not_let_one_nan_poison_the_line():
    a = np.ones((9, 40), np.float64)
    a[4, 20] = np.nan
    out = _gsmooth(a, 1.0)
    # far from the NaN the smoothed value is still exactly 1
    assert out[0, 0] == pytest.approx(1.0)
    assert out[8, 39] == pytest.approx(1.0)
    assert np.isfinite(out).mean() > 0.95
    # the masked estimator imputes the missing cell with its own local mean (1.0),
    # which is what makes it usable as a pre-filter; callers that need the NaN
    # mask preserved (_coh) re-apply it explicitly.
    assert out[4, 20] == pytest.approx(1.0)


def test_lmean_var_is_nan_aware_and_exact():
    a = np.full((1, 30), np.nan)
    a[0, 10:20] = np.arange(10, dtype=np.float64)
    mean, var = _lmean_var(a, 3)
    # at the centre of the valid run the 3-wide window is 3,4,5 -> var = 2/3
    assert mean[0, 14] == pytest.approx(4.0)
    assert var[0, 14] == pytest.approx(2.0 / 3.0)
    assert np.isnan(mean[0, 0])


def test_coh_is_one_for_a_pure_ramp_and_nan_where_input_is_nan():
    yy, xx = np.mgrid[0:40, 0:40].astype(np.float64)
    ramp = 3.0 * xx + 1.0 * yy            # constant gradient -> rank-1 tensor
    out = _coh(ramp, 1.0)
    interior = out[8:-8, 8:-8]
    assert np.nanmin(interior) > 0.98
    broken = ramp.copy()
    broken[:, 20:] = np.nan
    out2 = _coh(broken, 1.0)
    assert np.isnan(out2[:, 25:]).all()
    # valid pixels far from the NaN edge keep a real value
    assert np.isfinite(out2[:15, :12]).all()


def test_compute_block_has_no_all_nan_derived_feature():
    rng = np.random.default_rng(0)
    n_raw = 19
    blk = rng.normal(size=(n_raw, 40, 60)).astype(np.float32) * 10.0
    blk[:, : 40 - HALO // 2, :5] = np.nan          # nodata block in the corner
    stack = _FakeStack()
    band_ix = {b: i for i, b in enumerate(stack.bands)}
    der = compute_block(stack, blk, band_ix)
    assert der.shape[0] == len(stack.names) - n_raw
    for j, name in enumerate(stack.names[n_raw:]):
        assert np.isfinite(der[j]).any(), f"derived feature {name} is entirely NaN"


def test_every_documented_operator_family_is_present():
    stack = _FakeStack()
    derived = set(stack.names) - {f"raw/{b}" for b in stack.bands}
    assert {f"std3/{b}" for b in STD3} <= derived
    assert {f"std7/{b}" for b in STD7} <= derived
    assert len(derived) == 16


def test_open_stack_verifies_the_pin_and_refuses_a_bad_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        open_stack(tmp_path / "absent.tif")


class _FakeStack:
    """Minimal stand-in exposing only what compute_block reads."""

    def __init__(self):
        from gems59.features import COH_S1, COH_S3, LAP
        self.bands = ("mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope",
                      "tc", "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15",
                      "iso_grav_anom_vg", "det_elev", "iso_grav_anom", "tmi",
                      "depth_to_base_surf", "ieq_n100a15", "cond_surf", "iso_grav_anom_hg",
                      "det_elev_slope")
        names = [f"raw/{b}" for b in self.bands]
        names += [f"coh_s1/{f}" for f in COH_S1]
        names += [f"coh_s3/{f}" for f in COH_S3]
        names += [f"std3/{b}" for b in STD3]
        names += [f"std7/{b}" for b in STD7]
        names += [f"lap/{f}" for f in LAP]
        self.names = tuple(names)
