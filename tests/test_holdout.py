import math

import numpy as np

from gems.holdout import auc, bootstrap_ci, leakage_canary, make_folds, pooled_dti, visible_distance_m
from gems.metric import dti, triangular_kernel


def _brute_dti(pred, lab, pixel=100.0, R=300.0, a=0.2, b=0.8):
    """Naive O(N^2) reference of the same definition, for cross-checking dti()."""
    H, W = lab.shape
    ins = np.isfinite(pred)
    p = np.where(ins, pred, 0.0)
    L = np.argwhere(lab & ins)
    P = np.argwhere(ins)
    tp = fp = 0.0
    for (y, x) in P:
        if len(L):
            d = min(math.hypot(y - ly, x - lx) * pixel for ly, lx in L)
        else:
            d = np.inf
        w = float(triangular_kernel(d, R)) if np.isfinite(d) else 0.0
        tp += p[y, x] * w
        fp += p[y, x] * (1 - w)
    fn = 0.0
    for (ly, lx) in L:
        best = 0.0
        for (y, x) in P:
            k = float(triangular_kernel(math.hypot(y - ly, x - lx) * pixel, R))
            best = max(best, p[y, x] * k)
        fn += 1 - best
    return tp / (tp + a * fp + b * fn + 1e-9)


def test_vectorized_matches_bruteforce():
    rng = np.random.default_rng(3)
    for _ in range(3):
        lab = rng.random((12, 14)) < 0.08
        pred = rng.random((12, 14))
        pred[rng.random((12, 14)) < 0.2] = np.nan
        assert abs(dti(pred, lab) - _brute_dti(pred, lab)) < 1e-9


def _toy_labels(n=12, H=60, W=60):
    lab = np.zeros((H, W), bool)
    for i in range(n):
        r = 3 + (i * 4) % (H - 6)
        lab[r, 2:58] = True if i % 2 == 0 else False
        lab[r:r + 3, 30 + (i % 3)] = True
    return lab


def test_folds_withhold_whole_segments_and_never_leak():
    lab = _toy_labels()
    folds = make_folds(lab, n_folds=4, buffer_px=3, seed=1)
    assert len(folds) == 4
    for f in folds:
        assert not np.any(f.visible & f.withheld)           # disjoint
        assert not np.any(f.buffer & f.withheld)
        assert f.withheld.sum() > 0
        # every withheld pixel's whole segment is withheld: no partial segments visible
        assert np.all((f.visible | f.withheld)[lab] == True)  # noqa: E712
    union = np.zeros_like(lab)
    for f in folds:
        union |= f.withheld
    assert np.array_equal(union, lab)                         # each segment withheld in exactly one fold


def test_visible_distance_uses_visible_only():
    lab = _toy_labels()
    folds = make_folds(lab, n_folds=4, seed=1)
    d = visible_distance_m(folds[0].visible)
    hidden = folds[0].withheld
    # distance is computed from the visible catalogue, so it is large somewhere a hidden fault sits
    assert np.nanmax(d[hidden]) > 0


def test_pooled_dti_runs_and_ci_is_ordered():
    lab = _toy_labels()
    folds = make_folds(lab, n_folds=4, seed=1)
    preds = [f.withheld.astype(float) for f in folds]
    out = pooled_dti(preds, folds)
    assert out["pooled_dti"] > 0.9
    lo, hi = bootstrap_ci(out["per_fold_dti"], n_boot=200)
    assert lo <= hi


def test_auc_basic():
    assert auc(np.array([0.1, 0.2, 0.9, 0.95]), np.array([0, 0, 1, 1])) == 1.0
    assert abs(auc(np.array([0.5, 0.5, 0.5, 0.5]), np.array([0, 1, 0, 1])) - 0.5) < 1e-12


def test_canary_flags_leaky_feature_and_passes_noise():
    rng = np.random.default_rng(0)
    y = rng.random((50, 50)) < 0.1
    valid = np.ones_like(y)
    leaky = y.astype(float) + rng.normal(0, 0.01, y.shape)  # feature that IS the target
    noise = rng.random(y.shape)
    assert leakage_canary(leaky, y, valid)["suspect_leakage"] is True
    assert leakage_canary(noise, y, valid)["suspect_leakage"] is False
