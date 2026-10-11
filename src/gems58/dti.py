"""Distance-weighted Tversky index (DTI) as used in this project.

Definition (competition page 967 / rules section 3.5; wording quoted from the GEMSDOE32 repo
docstring, which cites the DrivenData page -- NOT re-verified here, see docs/sources.md):
  kernel          k(d) = max(1 - d / R, 0), R = 3 px (300 m at 100 m resolution)
  TP_w            = sum_{g in G} max_{x: d(x,g)<=R} p(x) k(d(x,g))
  FP_w            = sum_{x: p(x)>0} p(x) [1 - max_{g in G} k(d(x,g))]
  FN_w            = |G| - TP_w
  DTI(a=0.2,b=0.8)= TP_w / (TP_w + a FP_w + b FN_w)  ==  TP_w / (0.2 (TP_w + FP_w) + 0.8 |G|)

Pixels in `known` (catalogue faults that are masked from scoring) and pixels outside `valid`
are excluded from both prediction and truth.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
R_PX = 3.0
EPS = 1e-12


def kernel(d, radius: float = R_PX):
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / radius, 0.0)


def dti_binary(pred, truth, valid=None, known=None, alpha: float = ALPHA, beta: float = BETA):
    """Exact DTI for {0,1} predictions via Euclidean distance transforms (fast path)."""
    pred = np.asarray(pred, bool)
    truth = np.asarray(truth, bool)
    shape = pred.shape
    valid_ = np.ones(shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(shape, bool) if known is None else np.asarray(known, bool)
    active = valid_ & ~known_
    p = pred & active
    g = truth & active
    n = int(g.sum())
    if n == 0:
        return dict(tp=0.0, fp=float(p.sum()), fn=0.0, n_truth=0, dti=0.0, coverage=0.0)
    if not p.any():
        return dict(tp=0.0, fp=0.0, fn=float(n), n_truth=n, dti=0.0, coverage=0.0)
    dp = distance_transform_edt(~p)
    tp = float(kernel(dp[g]).sum())
    fn = float(n) - tp
    dg = distance_transform_edt(~g)
    fp = float((1.0 - kernel(dg[p])).sum())
    dti = tp / (tp + alpha * fp + beta * fn + EPS)
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n, dti=float(dti), coverage=tp / n)


def dti_bruteforce(pred, truth, alpha: float = ALPHA, beta: float = BETA, radius: float = R_PX):
    """Literal O(|G||P|) transcription of the equations above; used only to test dti_binary."""
    pred = np.asarray(pred, float)
    truth = np.asarray(truth, bool)
    gs = np.argwhere(truth)
    xs = np.argwhere(pred > 0)
    tp = fn = 0.0
    for g in gs:
        best = 0.0
        for x in xs:
            d = float(np.hypot(*(x - g)))
            if d <= radius:
                best = max(best, pred[tuple(x)] * max(1.0 - d / radius, 0.0))
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for x in xs:
        kmax = 0.0
        for g in gs:
            kmax = max(kmax, max(1.0 - float(np.hypot(*(x - g))) / radius, 0.0))
        fp += pred[tuple(x)] * (1.0 - kmax)
    return dict(tp=tp, fp=fp, fn=fn, dti=tp / (tp + alpha * fp + beta * fn + EPS))


def utility_U(tp: float, fp: float, dti0: float, alpha: float = ALPHA) -> float:
    """Linearised marginal gain of adding mass: U = (1 - alpha*DTI0) TP - alpha*DTI0 FP (task spec)."""
    return (1.0 - alpha * dti0) * tp - alpha * dti0 * fp


def dti_components(pred, truth, valid=None, known=None, alpha: float = ALPHA, beta: float = BETA):
    """Per-pixel decomposition of the exact DTI, for tile-level bootstrap.

    Returns (tp_map, fp_map, g_map, summary): tp_map credit is attached to truth pixels,
    fp_map cost to predicted pixels, g_map marks scored truth pixels. Sums equal dti_binary's.
    """
    pred = np.asarray(pred, bool)
    truth = np.asarray(truth, bool)
    valid_ = np.ones(pred.shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(pred.shape, bool) if known is None else np.asarray(known, bool)
    active = valid_ & ~known_
    p = pred & active
    g = truth & active
    tp_map = np.zeros(pred.shape, np.float64)
    fp_map = np.zeros(pred.shape, np.float64)
    if p.any() and g.any():
        dp = distance_transform_edt(~p)
        tp_map[g] = kernel(dp[g])
        dg = distance_transform_edt(~g)
        fp_map[p] = 1.0 - kernel(dg[p])
    tp, fp, n = float(tp_map.sum()), float(fp_map.sum()), int(g.sum())
    fn = n - tp
    dti = tp / (tp + alpha * fp + beta * fn + EPS) if n else 0.0
    return tp_map, fp_map, g, dict(tp=tp, fp=fp, fn=fn, n_truth=n, dti=float(dti))
