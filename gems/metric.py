"""Distance-weighted Tversky index (DTI) for the GEMS fault-probability task.

STATUS: APPROXIMATION - NOT VERIFIED AGAINST THE OFFICIAL SCORER.
The formula is taken from the third-party guide `GEMS_Prize_Challenge_Project_Guide.md`
(aggregated at github.com/Aayushk333/gems-prize-challenge), which cites the DrivenData
page. The official metric page could not be fetched from this sandbox, and the official
worked example (score ~0.60, per that guide) is not available here. Until both are
checked, every DTI number produced by this module must be labelled HOLDOUT-DTI with
"approximate implementation, unverified" and must not be presented as an organizer score.

Formula used (guide, section 17):
    DTI = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps),  alpha=0.2, beta=0.8
    kernel k(d) = max(1 - d/R, 0),  R = 300 m, pixel = 100 m

Our reading of the tolerance (ASSUMPTION, to be confirmed against the official code):
    precision side : w_p = k(distance from prediction pixel p to nearest labelled fault)
                     TP_w += P(p) * w_p ;  FP_w += P(p) * (1 - w_p)
    recall side    : r_l = max over pixels p of P(p) * k(d(l, p))  for each labelled pixel l
                     FN_w += 1 - r_l
Pixels with NaN predictions are outside the scored footprint and contribute nothing.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

ALPHA = 0.2
BETA = 0.8
RADIUS_M = 300.0
PIXEL_M = 100.0
EPS = 1e-9


def triangular_kernel(d_m: np.ndarray | float, radius_m: float = RADIUS_M) -> np.ndarray:
    """k(d) = max(1 - d/R, 0)."""
    return np.clip(1.0 - np.asarray(d_m, dtype=np.float64) / radius_m, 0.0, None)


def _nearest_label_distance_m(labels: np.ndarray, pixel_m: float) -> np.ndarray:
    """Distance (m) from every pixel centre to the nearest labelled pixel centre."""
    if not labels.any():
        return np.full(labels.shape, np.inf)
    return ndimage.distance_transform_edt(~labels, sampling=pixel_m)


def dti(
    pred: np.ndarray,
    labels: np.ndarray,
    *,
    alpha: float = ALPHA,
    beta: float = BETA,
    radius_m: float = RADIUS_M,
    pixel_m: float = PIXEL_M,
    return_parts: bool = False,
):
    """Pooled distance-weighted Tversky index on one raster.

    pred   : float array, values in [0,1]; NaN = outside the scored footprint.
    labels : boolean/0-1 array of labelled fault pixels (same shape).
    """
    pred = np.asarray(pred, dtype=np.float64)
    labels = np.asarray(labels).astype(bool)
    if pred.shape != labels.shape:
        raise ValueError(f"shape mismatch: pred {pred.shape} vs labels {labels.shape}")
    inside = np.isfinite(pred)
    p = np.where(inside, pred, 0.0)
    if np.any((p < 0) | (p > 1)):
        raise ValueError("predictions must lie in [0, 1] where finite")
    labels = labels & inside  # labels outside the footprint cannot be scored

    # precision side
    d_near = _nearest_label_distance_m(labels, pixel_m)
    w_p = triangular_kernel(d_near, radius_m)
    tp_w = float(np.sum(p * w_p))
    fp_w = float(np.sum(p * (1.0 - w_p) * inside))

    # recall side: best nearby prediction for each labelled pixel
    fn_w = 0.0
    if labels.any():
        m = int(math.ceil(radius_m / pixel_m))
        pad = np.pad(p, m, mode="constant", constant_values=0.0)
        lab_idx = np.argwhere(labels)
        best = np.zeros(len(lab_idx))
        for dy in range(-m, m + 1):
            for dx in range(-m, m + 1):
                k = float(triangular_kernel(math.hypot(dy, dx) * pixel_m, radius_m))
                if k <= 0.0:
                    continue
                vals = pad[lab_idx[:, 0] + m + dy, lab_idx[:, 1] + m + dx]
                best = np.maximum(best, vals * k)
        fn_w = float(np.sum(1.0 - best))

    score = tp_w / (tp_w + alpha * fp_w + beta * fn_w + EPS)
    if return_parts:
        return score, {"TP_w": tp_w, "FP_w": fp_w, "FN_w": fn_w,
                       "n_labelled": int(labels.sum()), "n_scored": int(inside.sum())}
    return score


def utility(dti0: float, tp: float, fp: float, alpha: float = ALPHA) -> float:
    """U = (1 - alpha*DTI0)*TP - alpha*DTI0*FP, the per-segment utility from the lane brief."""
    return (1.0 - alpha * dti0) * tp - alpha * dti0 * fp
