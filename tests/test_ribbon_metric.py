"""The metric must be the literal transcription of the published equations."""

from __future__ import annotations

import numpy as np
import pytest

from gems58w.metric import (ALPHA, BETA, EPS, RADIUS_PX, marginal_inclusion_threshold,
                           max_distance_for_credit, dti_binary, dti_bruteforce, dti_exact, kernel)


def test_kernel_is_triangular_and_truncates_at_R():
    assert kernel(0.0) == pytest.approx(1.0)
    assert kernel(1.5) == pytest.approx(0.5)
    assert kernel(3.0) == pytest.approx(0.0)
    assert kernel(3.0001) == pytest.approx(0.0)
    assert kernel(100.0) == pytest.approx(0.0)


def _random_case(seed: int, h: int = 40, w: int = 44):
    rng = np.random.default_rng(seed)
    truth = rng.random((h, w)) < 0.05
    dots = rng.random((h, w)) < 0.03
    return dots, truth


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_binary_matches_bruteforce(seed):
    dots, truth = _random_case(seed)
    fast = dti_binary(dots, truth)
    slow = dti_bruteforce(dots.astype(float), truth)
    assert fast.tp == pytest.approx(slow.tp, abs=1e-9)
    assert fast.fp == pytest.approx(slow.fp, abs=1e-9)
    assert fast.dti == pytest.approx(slow.dti, abs=1e-12)


@pytest.mark.parametrize("seed", [11, 12])
def test_soft_matches_bruteforce(seed):
    rng = np.random.default_rng(seed)
    truth = rng.random((24, 26)) < 0.06
    pred = np.where(rng.random(truth.shape) < 0.2, rng.random(truth.shape), 0.0).astype(float)
    fast = dti_exact(pred, truth)
    slow = dti_bruteforce(pred, truth)
    assert fast.tp == pytest.approx(slow.tp, abs=1e-8)
    assert fast.fp == pytest.approx(slow.fp, abs=1e-8)
    assert fast.dti == pytest.approx(slow.dti, abs=1e-10)


def test_denominator_identity_FN_equals_G_minus_TP():
    dots, truth = _random_case(7)
    r = dti_binary(dots, truth)
    assert r.fn == pytest.approx(r.n_truth - r.tp, abs=1e-9)
    den = r.tp + ALPHA * r.fp + BETA * r.fn
    assert r.dti == pytest.approx(r.tp / (den + EPS), abs=1e-15)


def test_binary_dominates_its_own_scaled_support():
    """DTI(lambda*b) is strictly increasing in lambda on (0, 1] for binary b."""
    dots, truth = _random_case(9)
    vals = [dti_exact(dots.astype(float) * lam, truth).dti for lam in (0.05, 0.25, 0.5, 0.75, 1.0)]
    assert all(b > a for a, b in zip(vals, vals[1:])), vals


def test_marginal_rule_matches_the_derivative():
    """Deterministic: one dot added to a *fresh* truth pixel, sign vs the rule."""
    n = 61
    truth = np.zeros((n, n), bool)
    a, b = (10, 10), (50, 50)
    truth[a] = True
    truth[b] = True
    base = np.zeros((n, n), bool)
    base[a[0], a[1] + 1] = True                 # credit 2/3 on truth a
    s = dti_binary(base, truth).dti
    k_min = marginal_inclusion_threshold(s)
    assert k_min == pytest.approx(ALPHA * s)
    for dy, dx in ((0, 1), (1, 1), (0, 2), (1, 2), (2, 2), (0, 3)):
        d = float(np.hypot(dy, dx))
        k = max(0.0, 1.0 - d / RADIUS_PX)
        test = base.copy()
        test[b[0] + dy, b[1] + dx] = True
        improved = dti_binary(test, truth).dti > s
        assert improved == (k >= k_min), (dy, dx, k, k_min, improved)


def test_max_distance_for_threshold_credit():
    # at the current public leader 0.3195 the required credit is 0.0639 and the
    # implied slack is just under one pixel
    k = marginal_inclusion_threshold(0.3195)
    assert k == pytest.approx(0.0639, abs=1e-4)
    assert max_distance_for_credit(k) == pytest.approx(280.83, abs=0.5)


def test_known_mask_removes_mass_from_both_sides():
    rng = np.random.default_rng(21)
    truth = np.zeros((20, 20), bool)
    truth[5, 5] = True
    dots = np.zeros((20, 20), bool)
    dots[5, 5] = True
    known = np.zeros((20, 20), bool)
    assert dti_binary(dots, truth).tp == pytest.approx(1.0)
    known[5, 5] = True
    r = dti_binary(dots, truth, known=known)
    assert r.tp == 0.0 and r.n_truth == 0


def test_nan_and_out_of_range_are_rejected():
    truth = np.zeros((10, 10), bool)
    truth[2, 2] = True
    fp = np.ones((10, 10), bool)
    bad = np.zeros((10, 10), float)
    bad[3, 3] = np.nan
    with pytest.raises(ValueError, match="finite"):
        dti_exact(bad, truth, valid=fp)
    bad2 = np.zeros((10, 10), float)
    bad2[3, 3] = 1.5
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        dti_exact(bad2, truth, valid=fp)
