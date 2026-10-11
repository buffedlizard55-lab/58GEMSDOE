"""Exact Distance-weighted Tversky Index (DTI) for the DOE GEMS Prize.

Transcribed from the official problem description (DrivenData page 967,
"Performance metric") which is reproduced verbatim in
``docs/research/metric.md`` and linked in ``registry/sources.json``:

    k(d)   = max(1 - d / R, 0),          R = 300 m = 3 pixels
    TP_w   = sum_{g in G}  max_{x: d(x,g) <= R} p(x) * k(d(x,g))
    FP_w   = sum_{x: p(x) > 0} p(x) * [1 - max_{g in G} k(d(x,g))]
    FN_w   = sum_{g in G}  [1 - max_{x: d(x,g) <= R} p(x) * k(d(x,g))]
    DTI    = TP_w / (TP_w + alpha * FP_w + beta * FN_w + eps),  alpha = 0.2, beta = 0.8

Because ``FN_w = |G| - TP_w`` the index collapses to

    DTI = TP_w / (alpha * (TP_w + FP_w) + beta * |G| + eps).            (A)

(A) is the form used everywhere in this repository; ``dti_bruteforce`` below is a
literal, unoptimised transcription of the three sums and the tests assert that
every fast path reproduces it to machine precision.

Two exact consequences drive the whole ribbon lane (proved in
``docs/research/ribbon-algebra.md`` and re-verified by
``scripts/verify_theorems.py``):

1. **Binary dominates soft.**  For the support-scaled family ``p_lambda = lambda * b``
   with ``b`` binary, ``DTI(lambda) = lambda*T / (alpha*lambda*(T+F) + beta*G)``
   which is strictly increasing in ``lambda`` on ``(0, 1]``.  A graded probability
   raster is therefore strictly dominated by its own thresholded support, and the
   emitted value must be exactly ``1.0``.
2. **Marginal inclusion.**  Adding an emitted pixel of own-credit ``k`` changes
   ``TP`` by ``k`` and ``FP`` by ``1 - k``.  Writing ``s = DTI_0``,

       DTI' >= s   <=>   k * (1 - alpha*s) >= alpha*s * (1 - k)
                   <=>   k >= alpha*s.

   So at ``s = 0.3195`` a dot pays for itself iff its kernel credit exceeds
   ``0.064``, i.e. iff it lands within 280.9 m of a scored truth pixel.  The
   emission rule is a *distance* filter, not a precision filter.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA: float = 0.2
BETA: float = 0.8
RADIUS_PX: float = 3.0
EPS: float = 1e-12

EVALUATOR_VERSION = "gems58.metric/v1 (exact triangular kernel, R=3 px, alpha=0.2, beta=0.8)"


def kernel(d, radius: float = RADIUS_PX) -> np.ndarray:
    """Triangular kernel ``k(d) = max(1 - d/R, 0)``, distances in pixels."""
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / radius, 0.0)


def offsets(radius: float = RADIUS_PX):
    r = int(np.ceil(radius))
    out = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            k = float(kernel(float(np.hypot(dy, dx)), radius))
            if k > 0.0:
                out.append((dy, dx, k))
    return tuple(out)


OFFSETS = offsets()


@dataclass
class DTI:
    tp: float
    fp: float
    fn: float
    n_truth: int
    dti: float
    coverage: float
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return dict(tp=self.tp, fp=self.fp, fn=self.fn, n_truth=self.n_truth,
                    dti=self.dti, coverage=self.coverage, **self.extra)


def _pack(pred, truth, valid, known):
    pred = np.asarray(pred)
    truth = np.asarray(truth)
    if pred.shape != truth.shape:
        raise ValueError("prediction and truth must be equal-shaped 2-D grids")
    if pred.ndim != 2:
        raise ValueError("prediction must be 2-D")
    valid = np.ones(pred.shape, bool) if valid is None else np.asarray(valid, bool)
    known = np.zeros(pred.shape, bool) if known is None else np.asarray(known, bool)
    if valid.shape != pred.shape or known.shape != pred.shape:
        raise ValueError("mask grid mismatch")
    active = valid & ~known
    vals = pred[active]
    if not np.isfinite(vals).all():
        raise ValueError("prediction inside the scored domain must be finite (no NaN in footprint)")
    if (vals < 0).any() or (vals > 1).any():
        raise ValueError("prediction inside the scored domain must lie in [0, 1]")
    p = np.where(active, pred, 0.0).astype(np.float64)
    g = active & (np.asarray(truth) > 0)
    return p, g


def dti_exact(pred, truth, valid=None, known=None, alpha=ALPHA, beta=BETA) -> DTI:
    """Exact DTI for an arbitrary soft or binary prediction in [0, 1]."""
    p, g = _pack(pred, truth, valid, known)
    H, W = p.shape
    yy, xx = np.nonzero(g)
    n = int(yy.size)
    if n == 0:
        return DTI(0.0, float(p.sum()), 0.0, 0, 0.0, 0.0)
    credit = np.zeros(n, dtype=np.float64)
    for dy, dx, k in OFFSETS:
        ny, nx = yy + dy, xx + dx
        ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
        credit[ok] = np.maximum(credit[ok], p[ny[ok], nx[ok]] * k)
    tp = float(credit.sum())
    fn = float(n) - tp
    d = distance_transform_edt(~g)
    fp = float((p * (1.0 - kernel(d))).sum())
    den = tp + alpha * fp + beta * fn + EPS
    return DTI(tp, fp, fn, n, tp / den, tp / n)


def dti_binary(pred_bool, truth, valid=None, known=None, alpha=ALPHA, beta=BETA) -> DTI:
    """Exact DTI for a binary {0, 1} prediction, via Euclidean distance transforms."""
    pred_bool = np.asarray(pred_bool, bool)
    truth = np.asarray(truth, bool)
    valid = np.ones(pred_bool.shape, bool) if valid is None else np.asarray(valid, bool)
    known = np.zeros(pred_bool.shape, bool) if known is None else np.asarray(known, bool)
    active = valid & ~known
    p = pred_bool & active
    g = truth & active
    n = int(g.sum())
    if n == 0:
        return DTI(0.0, float(p.sum()), 0.0, 0, 0.0, 0.0)
    if not p.any():
        return DTI(0.0, 0.0, float(n), n, 0.0, 0.0)
    dp = distance_transform_edt(~p)
    tp = float(kernel(dp[g]).sum())
    fn = float(n) - tp
    dg = distance_transform_edt(~g)
    fp = float((1.0 - kernel(dg[p])).sum())
    den = tp + alpha * fp + beta * fn + EPS
    return DTI(tp, fp, fn, n, tp / den, tp / n)


def dti_bruteforce(pred, truth, alpha=ALPHA, beta=BETA, radius=RADIUS_PX) -> DTI:
    """Literal O(|G| * |P|) transcription of the published equations. Test oracle."""
    pred = np.asarray(pred, float)
    truth = np.asarray(truth, bool)
    gs = np.argwhere(truth)
    xs = np.argwhere(pred > 0)
    n = int(gs.shape[0])
    if n == 0:
        return DTI(0.0, float(pred.sum()), 0.0, 0, 0.0, 0.0)
    tp = 0.0
    for g in gs:
        best = 0.0
        for x in xs:
            d = float(np.hypot(x[0] - g[0], x[1] - g[1]))
            best = max(best, float(pred[x[0], x[1]]) * float(kernel(d, radius)))
        tp += best
    fp = 0.0
    for x in xs:
        best = 0.0
        for g in gs:
            d = float(np.hypot(x[0] - g[0], x[1] - g[1]))
            best = max(best, float(kernel(d, radius)))
        fp += float(pred[x[0], x[1]]) * (1.0 - best)
    fn = float(n) - tp
    den = tp + alpha * fp + beta * fn + EPS
    return DTI(tp, fp, fn, n, tp / den, tp / n)


def marginal_inclusion_threshold(dti0: float, alpha: float = ALPHA) -> float:
    """Smallest own-credit ``k`` for which one more emitted pixel still pays at ``dti0``."""
    return alpha * dti0


def max_distance_for_credit(k: float, radius: float = RADIUS_PX) -> float:
    """Meters of slack a dot with required credit ``k`` may have (1 px = 100 m)."""
    return (1.0 - k) * radius * 100.0


def paired_bootstrap(a: np.ndarray, b: np.ndarray, n_boot: int = 2000, seed: int = 58,
                     alpha: float = 0.05) -> dict:
    """Percentile bootstrap CI for the paired mean difference ``a - b``."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.shape != b.shape:
        raise ValueError("paired bootstrap needs equal-length samples")
    d = a - b
    n = d.size
    if n == 0:
        return dict(mean_point=0.0, lo=0.0, hi=0.0, n=0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot = d[idx].mean(axis=1)
    return dict(mean_point=float(d.mean()),
                lo=float(np.quantile(boot, alpha / 2)),
                hi=float(np.quantile(boot, 1 - alpha / 2)),
                n=int(n))
