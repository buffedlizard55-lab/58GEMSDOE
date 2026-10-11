"""Shared-template tests for ``gems57.exact_emission``.

The module is a *proposer*; its numbers must agree with the shared metric, not
with its own algebra.  Every test therefore checks the ledger or the greedy
against :func:`gems57.metric.dti_binary` / :func:`gems57.metric.dti_bruteforce`.
"""

from __future__ import annotations

import numpy as np

from gems57 import exact_emission as EE
from gems57 import metric


def _random_case(seed: int, h: int = 41, w: int = 37, n_truth: int = 60,
                 n_dots: int = 120):
    rng = np.random.default_rng(seed)
    active = np.ones((h, w), bool)
    truth = np.zeros((h, w), bool)
    idx = rng.choice(h * w, size=n_truth, replace=False)
    truth.flat[idx] = True
    dots = np.zeros((h, w), bool)
    didx = rng.choice(h * w, size=n_dots, replace=False)
    dots.flat[didx] = True
    return active, truth, dots


def test_ledger_reproduces_shared_binary_metric():
    for seed in range(6):
        active, truth, dots = _random_case(seed)
        ref = metric.dti_binary(dots, truth, valid=active)
        led = EE.DotLedger(truth, active)
        rows, cols = np.nonzero(dots)
        dT, kself = led.delta(rows, cols)
        led.apply(rows, cols, dT, np.maximum(kself, 0.0))
        tp, fp, fn, K = led.terms()
        assert K == ref["n_truth"]
        assert abs(tp - ref["tp"]) < 1e-9, (tp, ref["tp"])
        assert abs(fp - ref["fp"]) < 1e-9, (fp, ref["fp"])
        assert abs(fn - ref["fn"]) < 1e-9, (fn, ref["fn"])
        assert abs(led.dti() - ref["dti"]) < 1e-12


def test_ledger_incremental_matches_batch():
    active, truth, dots = _random_case(11, n_dots=200)
    rows, cols = np.nonzero(dots)
    # batch
    a = EE.DotLedger(truth, active)
    dT, ks = a.delta(rows, cols)
    a.apply(rows, cols, dT, np.maximum(ks, 0.0))
    # one at a time
    b = EE.DotLedger(truth, active)
    for r, c in zip(rows, cols):
        rr = np.array([r])
        cc = np.array([c])
        dT, ks = b.delta(rr, cc)
        b.apply(rr, cc, dT, np.maximum(ks, 0.0))
    assert abs(a.T - b.T) < 1e-9
    assert abs(a.M - b.M) < 1e-9
    assert abs(a.dti() - b.dti()) < 1e-12


def test_delta_is_zero_when_truth_already_covered():
    active = np.ones((21, 21), bool)
    truth = np.zeros((21, 21), bool)
    truth[10, :] = True                      # a straight east-west fault
    led = EE.DotLedger(truth, active)
    r, c = np.array([10]), np.array([5])
    dT, ks = led.delta(r, c)
    led.apply(r, c, dT, np.maximum(ks, 0.0))
    dT2, _ = led.delta(r, c)                 # the same dot again
    assert abs(dT2.sum()) < 1e-12
    dT3, _ = led.delta(np.array([10]), np.array([6]))
    assert dT3.sum() > 0.0                   # a neighbouring cell still earns


def test_accept_bar_matches_isolated_dot_rule():
    """A non-redundant dot is accepted exactly when k > alpha*DTI."""
    active = np.ones((31, 31), bool)
    truth = np.zeros((31, 31), bool)
    truth[15, :] = True
    led = EE.DotLedger(truth, active)
    for _ in range(4):
        r, c = np.array([15]), np.array([3])
        dT, ks = led.delta(r, c)
        led.apply(r, c, dT, np.maximum(ks, 0.0))
        r, c = np.array([15]), np.array([9])
        dT, ks = led.delta(r, c)
        led.apply(r, c, dT, np.maximum(ks, 0.0))
    s = led.dti()
    # a dot 2 px from the truth at an uncovered spot has k = 1/3
    r, c = np.array([17]), np.array([20])
    dT, ks = led.delta(r, c)
    assert abs(ks.sum() - (1.0 - 2.0 / 3.0)) < 1e-12
    expected = ks.sum() > metric.ALPHA * s
    assert led.accept(float(dT.sum()), float(ks.sum())) == bool(expected)


def test_greedy_arms_never_lowers_dti():
    rng = np.random.default_rng(7)
    h = w = 25
    active = np.ones((h, w), bool)
    truth = np.zeros((h, w), bool)
    truth[12, :] = True
    truth[:, 12] = True
    led0 = EE.DotLedger(truth, active)
    arms, keys = [], []
    for k in range(24):
        rows = np.full(w, k, dtype=np.int64)
        cols = np.arange(w, dtype=np.int64)
        xy = np.stack([rows, cols], axis=1)
        rng.shuffle(xy)
        arms.append(xy[:14])
        keys.append((k, 0.0))
    led = EE.DotLedger(truth, active)
    steps = EE.greedy_arms(led, arms, keys)
    base = led0.dti()
    assert led.dti() >= base - 1e-12
    for st in steps:
        assert st.dti_after >= st.dti_before - 1e-12
        assert st.dT >= 0.0
    # the greedy result must equal the shared metric on the emitted support
    emitted = np.zeros((h, w), bool)
    for st in steps:
        a = np.asarray(arms[[i for i, k in enumerate(keys)
                             if k[0] == st.seg_id and k[1] == st.offset_px][0]])
        emitted[a[:, 0], a[:, 1]] = True
    ref = metric.dti_binary(emitted, truth, valid=active)
    tp, fp, fn, K = led.terms()
    assert abs(tp - ref["tp"]) < 1e-9
    assert abs(led.dti() - ref["dti"]) < 1e-12
