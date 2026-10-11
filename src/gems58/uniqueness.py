"""Duplicate ("lane drift") checks against every registry raster, per the parallel-run protocol.

Two tests, both must pass for the candidate to be placed:
  1. Spearman rank correlation of values on the jointly-finite pixels < 0.90 (computed on a
     fixed random subsample of 1,000,000 pixels with a fixed seed, for speed).
  2. Share of candidate dots within 3 px of ANY single registry raster's dots must be <= 70%.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr


def rank_corr(cand: np.ndarray, reg: np.ndarray, n: int = 300_000, seed: int = 0) -> float:
    ok = np.isfinite(cand) & np.isfinite(reg)
    if ok.sum() < 100:
        return float("nan")
    idx = np.flatnonzero(ok.ravel())
    rng = np.random.default_rng(seed)
    if idx.size > n:
        idx = rng.choice(idx, n, replace=False)
    r = spearmanr(cand.ravel()[idx], reg.ravel()[idx]).statistic
    return float(r)


def dot_overlap_within(cand_dots: np.ndarray, reg_dots: np.ndarray, px: float = 3.0) -> float:
    """Fraction of candidate dot pixels with a registry dot within `px` pixels (exact, KD-tree)."""
    from scipy.spatial import cKDTree

    if cand_dots.sum() == 0 or reg_dots.sum() == 0:
        return 0.0
    cy, cx = np.nonzero(cand_dots)
    ry, rx = np.nonzero(reg_dots)
    d, _ = cKDTree(np.column_stack([ry, rx])).query(np.column_stack([cy, cx]), distance_upper_bound=px + 1e-9)
    return float(np.mean(np.isfinite(d) & (d <= px)))
