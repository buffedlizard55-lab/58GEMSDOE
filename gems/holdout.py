"""Hide-and-recover holdout for fault-probability maps.

Protocol (from the lane brief and the guide, sections 16-19):
  * Fault "segments" = 8-connected components of the known-fault raster.
  * For each fold, whole segments are withheld. Their pixels are removed from the visible
    catalogue, and a buffer around them is excluded from any visible-fault-derived feature.
  * Every catalogue-based feature must be computed from the VISIBLE faults only.
  * Scores are pooled over folds with a segment-level bootstrap for the 95% CI.
  * A single-feature leakage canary (AUC) must stay below 0.90 before a feature is trusted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from gems.metric import ALPHA, BETA, PIXEL_M, dti


@dataclass
class Fold:
    fold_id: int
    visible: np.ndarray      # bool, known faults still visible to the model
    withheld: np.ndarray     # bool, held-out fault pixels used for scoring
    buffer: np.ndarray       # bool, pixels within buffer_px of withheld faults
    n_segments_withheld: int


def fault_segments(labels: np.ndarray) -> tuple[np.ndarray, int]:
    """Label 8-connected components of the fault raster. Returns (segment_id, n)."""
    seg, n = ndimage.label(labels.astype(bool), structure=np.ones((3, 3), dtype=int))
    return seg, n


def make_folds(labels: np.ndarray, n_folds: int = 5, buffer_px: int = 3,
               seed: int = 0) -> list[Fold]:
    """Withhold whole fault segments, n_folds times, with a buffer around each withheld set.

    Segments are assigned to folds at random (seeded). A segment is never split between
    the visible and withheld sets of the same fold.
    """
    labels = labels.astype(bool)
    seg, n = fault_segments(labels)
    if n < n_folds:
        raise ValueError(f"only {n} fault segments; need at least n_folds={n_folds}")
    rng = np.random.default_rng(seed)
    assign = rng.permutation(n) % n_folds
    folds = []
    for f in range(n_folds):
        ids = np.where(assign == f)[0] + 1
        withheld = np.isin(seg, ids)
        dist_px = ndimage.distance_transform_edt(~withheld)
        buffer = (dist_px <= buffer_px) & ~withheld
        visible = labels & ~withheld
        folds.append(Fold(f, visible, withheld & labels, buffer, len(ids)))
    return folds


def visible_distance_m(visible: np.ndarray, pixel_m: float = PIXEL_M) -> np.ndarray:
    """Distance (m) to the nearest VISIBLE fault. The only catalogue-derived feature allowed."""
    if not visible.any():
        return np.full(visible.shape, np.inf)
    return ndimage.distance_transform_edt(~visible.astype(bool), sampling=pixel_m)


def pooled_dti(preds: list[np.ndarray], folds: list[Fold]) -> dict:
    """Pooled DTI over folds (parts summed, then ratio) plus per-fold scores."""
    per_fold = []
    tp = fp = fn = 0.0
    for pred, fold in zip(preds, folds):
        # Score each fold against its withheld faults only, with buffer pixels ignored.
        p = np.where(fold.buffer, np.nan, pred)
        s, parts = dti(p, fold.withheld, return_parts=True)
        per_fold.append(s)
        tp += parts["TP_w"]
        fp += parts["FP_w"]
        fn += parts["FN_w"]
    pooled = tp / (tp + ALPHA * fp + BETA * fn + 1e-9)
    return {"pooled_dti": pooled, "per_fold_dti": per_fold,
            "n_folds": len(folds), "n_withheld_pixels": int(sum(f.withheld.sum() for f in folds))}


def bootstrap_ci(per_fold: list[float], n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% percentile CI over folds (folds are the resampling unit)."""
    v = np.asarray(per_fold, dtype=float)
    rng = np.random.default_rng(seed)
    boots = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(n_boot)])
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def auc(scores: np.ndarray, positives: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney), no sklearn needed."""
    s = np.asarray(scores, dtype=float).ravel()
    y = np.asarray(positives).ravel().astype(bool)
    ok = np.isfinite(s)
    s, y = s[ok], y[ok]
    n_pos, n_neg = int(y.sum()), int((~y).sum())
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUC needs both positive and negative pixels")
    ranks = np.empty(len(s))
    order = np.argsort(s, kind="mergesort")
    ranks[order] = np.arange(1, len(s) + 1)
    # average tied ranks
    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=ranks)
    ranks = (sums / counts)[inv]
    return float((ranks[y].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def leakage_canary(feature: np.ndarray, target: np.ndarray, valid: np.ndarray,
                   threshold: float = 0.90) -> dict:
    """AUC of ONE feature alone against held-out fault pixels. AUC > threshold = leakage suspect."""
    m = valid & np.isfinite(feature)
    a = auc(feature[m], target[m])
    return {"auc": a, "threshold": threshold, "suspect_leakage": bool(a > threshold)}
