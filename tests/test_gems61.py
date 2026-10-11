"""Session-7 lane tests: pattern geometry, sigma fallback, utility rule, screen equivalence."""
import numpy as np

from gems61.patterns import PATTERNS, segment_dots, utility
from gems61.sigma_fit import SegSigma, sigma_for, sigma_table
from gems61 import surfaces as SU


class _Seg:
    def __init__(self, idx):
        self.idx = np.asarray(idx, float)


def test_single_line_rule_for_sigma_under_half_pixel():
    (p1, p2, p3) = PATTERNS
    assert p1.offsets(0.3) == (0.0,)
    # ribbons collapse to the centre line exactly at the lane's 0.5 px rule
    assert p3.offsets(0.4) == (0.0,)
    assert p3.offsets(2.0) == (-2.0, 0.0, 2.0)
    assert p2.offsets(3.0) == (-1.5, 1.5)
    # sigma is capped at the kernel radius
    assert p3.offsets(9.0) == (-3.0, 0.0, 3.0)


def test_segment_dots_are_on_the_pixel_lattice_and_spaced_three_px():
    idx = np.stack([np.full(30, 100.0), np.arange(100.0, 130.0)], axis=1)
    dots = segment_dots(_Seg(idx), (0.0,), shape=(3730, 3292), along_px=3)
    assert dots.dtype.kind in "iu"
    assert len(dots) == 10  # every 3 px of 30-px arclength
    assert np.all(np.diff(np.sort(dots[:, 1])) >= 3)
    wide = segment_dots(_Seg(idx), (-2.0, 0.0, 2.0), shape=(3730, 3292), along_px=3)
    assert len(wide) == 30  # three parallel lines
    assert set(np.unique(wide[:, 0])) == {98, 100, 102}


def test_utility_reduces_to_k_minus_alpha_s_for_isolated_dot():
    # one isolated dot: TP = k, FP = 1 - k  =>  U = k - alpha*s
    k, s = 0.4, 0.27
    assert abs(utility(k, 1 - k, s) - (k - 0.2 * s)) < 1e-12


def test_sigma_for_falls_back_down_the_documented_chain():
    rows = []
    for b in ("NW", "NE", "SW", "SE"):
        for i in range(12):
            rows.append(SegSigma(block=b, seg_px=20, frac_within=0.9, sigma=2.0,
                                 truth_rms=1.5, family="subsurface",
                                 band="depth_to_base_surf", scale=1.5,
                                 relief_class=1, strength=3.0))
    # exact stratum (>= MIN_PAIRS rows) wins
    sig, src = sigma_for("subsurface", "depth_to_base_surf", 1.5, 1, "NW", rows)
    assert src["source"] == "band_scale_relief_block" and sig == 2.0
    # unknown band falls back to pooled
    sig, src = sigma_for("magnetic", "tc", 3.0, 0, "NW", rows)
    assert src["source"] == "pooled"
    # empty rows -> floor
    sig, src = sigma_for("magnetic", "tc", 3.0, 0, "NW", [])
    assert src["source"] == "floor"


def test_sigma_table_groups_by_required_strata():
    rows = [SegSigma(block="NW", seg_px=20, frac_within=0.9, sigma=2.0, truth_rms=1.5,
                     family="subsurface", band="cond_surf", scale=1.5, relief_class=0,
                     strength=1.0, frac_strict=0.8, strict_sigma=1.2)]
    t = sigma_table(rows)
    for key in ("by_block", "by_resolution", "by_ridge_type", "by_relief_class", "by_type_scale"):
        assert t[key], key
    assert t["by_relief_class"]["relief0"]["n_segments"] == 1


def test_edge_response_is_zero_off_support_and_localised():
    # smooth background + one step: the step face must dominate the response
    yy, xx = np.mgrid[0:64, 0:64]
    z = (0.01 * xx + 0.01 * yy).astype(np.float32)
    z[:, 32:] += 5.0     # a step edge at column 32
    valid = np.ones_like(z, bool)
    r = SU._edge_response(z, valid, scale=1.5)
    cols = r.sum(axis=0)
    assert cols[31:34].sum() > 0.85 * cols.sum()   # response concentrated at the step
