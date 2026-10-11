"""Distance-weighted Tversky index (DTI) for the DOE GEMS Prize.

Source of the definition (official, verified 2026-10-11):
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric
  Rules PDF, section 3.6.1: https://docs.nlr.gov/docs/fy26osti/96647.pdf
Known-fault masking (organizer staff reply, 2026-09-16):
  https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516

Definitions (R = 3 px = 300 m at 100 m resolution, alpha = 0.2, beta = 0.8):
  k(d)   = max(1 - d / R, 0)
  TP_w   = sum_{g in G} max_{x: d(x,g) <= R} p(x) k(d(x,g))
  FP_w   = sum_{x: p(x) > 0} p(x) [1 - max_{g in G} k(d(x,g))]
  FN_w   = sum_{g in G} [1 - max_{x: d(x,g) <= R} p(x) k(d(x,g))]
  DTI    = TP_w / (TP_w + alpha FP_w + beta FN_w + eps)

Masking: pixels flagged in `known` (catalogue faults already in the training labels)
are removed from the scored domain, as stated by the organizers. `valid` marks pixels
inside the GeoDAWN footprint; pixels outside it are ignored.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA: float = 0.2
BETA: float = 0.8
RADIUS_PX: float = 3.0  # 300 m / 100 m
EPS: float = 1e-12


def kernel(d, radius: float = RADIUS_PX):
    """Triangular kernel k(d) = max(1 - d/R, 0); d and radius in pixels."""
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / radius, 0.0)


def _offsets(radius: float = RADIUS_PX):
    r = int(np.ceil(radius))
    out = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            k = float(kernel(np.hypot(dy, dx), radius))
            if k > 0.0:
                out.append((dy, dx, k))
    return out


_OFFS = _offsets()


@dataclass
class DTIResult:
    tp: float
    fp: float
    fn: float
    n_truth: int
    dti: float

    def as_dict(self) -> dict:
        return dict(tp=self.tp, fp=self.fp, fn=self.fn, n_truth=self.n_truth, dti=self.dti)


def _domain(shape, valid, known):
    v = np.ones(shape, bool) if valid is None else np.asarray(valid, bool)
    k = np.zeros(shape, bool) if known is None else np.asarray(known, bool)
    return v & ~k


def truth_weight_map(truth_mask: np.ndarray) -> np.ndarray:
    """Return W = 1 - k(d(x, G)) on the whole grid (the FP weight of a unit prediction at x)."""
    g = np.asarray(truth_mask, bool)
    if not g.any():
        return np.ones(g.shape, np.float64)
    dg = distance_transform_edt(~g)
    return 1.0 - kernel(dg)


def dti_from_components(tp: float, fp: float, n_truth: int, alpha=ALPHA, beta=BETA) -> float:
    fn = float(n_truth) - tp
    return float(tp / (tp + alpha * fp + beta * fn + EPS))


def dti_soft(pred, truth, valid=None, known=None, alpha=ALPHA, beta=BETA) -> DTIResult:
    """Exact DTI for soft predictions p in [0, 1] (vectorised over truth pixels)."""
    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, bool)
    if pred.shape != truth.shape:
        raise ValueError("prediction and truth must have the same shape")
    active = _domain(pred.shape, valid, known)
    if not np.isfinite(pred[active]).all() or (pred[active] < 0).any() or (pred[active] > 1).any():
        raise ValueError("predictions inside the scored domain must be finite and in [0, 1]")
    p = np.where(active, pred, 0.0)
    g = truth & active
    yy, xx = np.nonzero(g)
    n = int(yy.size)
    if n == 0:
        fp = float((p * (p > 0)).sum())
        return DTIResult(0.0, fp, 0.0, 0, 0.0)
    H, W = p.shape
    credit = np.zeros(n)
    for dy, dx, k in _OFFS:
        ny, nx = yy + dy, xx + dx
        ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
        credit[ok] = np.maximum(credit[ok], p[ny[ok], nx[ok]] * k)
    tp = float(credit.sum())
    fp = float((p * truth_weight_map(g)).sum())
    return DTIResult(tp, fp, float(n) - tp, n, dti_from_components(tp, fp, n, alpha, beta))


def dti_binary(pred_bool, truth, valid=None, known=None, alpha=ALPHA, beta=BETA) -> DTIResult:
    """Exact DTI for binary predictions {0, 1} (the emission used by the ribbon lane)."""
    return dti_soft(np.asarray(pred_bool, bool).astype(np.float64), truth, valid, known, alpha, beta)


def dti_bruteforce(pred, truth, alpha=ALPHA, beta=BETA, radius=RADIUS_PX) -> dict:
    """Literal O(|G||X|) transcription of the published equations (test oracle only)."""
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
    """Linearised DTI gain used by the ribbon lane: U = (1 - a*DTI0) TP - a*DTI0 FP.

    Derivation (checked in tests): d(DTI) is proportional to (1 - a*DTI) dTP - a*DTI dFP
    at the current operating point, because d(alpha*(TP+FP) + beta*|G|) = alpha*(dTP+dFP).
    """
    return (1.0 - alpha * dti0) * tp - alpha * dti0 * fp
