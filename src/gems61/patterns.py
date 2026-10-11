"""Parallel dotted-line patterns and exact-metric U selection (session 7 ribbon lane).

Lane brief: "choose, per segment, the number and offset of parallel dotted lines
(spacing near the 3-px kernel radius) that maximize U = (1 - 0.2*DTI0)*TP -
0.2*DTI0*FP, evaluated with the exact metric. Use a single tight line where sigma
is under about 0.5 px and a ribbon about +-sigma wide where it is 2-3 px. Emit
included dots at exactly 1.0."

Pattern lattice for a stratum whose measured localization scale is ``sigma``
(preregistered; the single-line rule for sigma < 0.5 px is enforced by the
selection: P1 always exists and the ribbon patterns collapse to it at sigma 0):

    P1  offsets {0}                 single tight line
    P2  offsets {-w/2, +w/2}        two lines, spacing w
    P3  offsets {-w, 0, +w}         three lines, spacing w
    w = clip(sigma, 0.5, 3.0) px

Along-strike dots are placed every ``ALONG_PX`` = 3 px (the kernel radius) of
segment arclength.  Offsets are applied along the segment's local normal (PCA
direction of the segment pixels), rounded to the pixel lattice.

Selection is exact-metric and setwise: for a candidate pattern the *whole* dot set
of the stratum is scored with the shared ``gems57`` exact DTI on the inner holdout
cells, and

    U(P) = (1 - alpha*s0) * TP(P) - alpha*s0 * FP(P)

with ``s0`` the baseline DTI (documented linearization of
docs/research/metric.md; TP/FP include the metric's per-truth maxima, so
interacting dots do not sum).  A pattern is emitted only when its U > 0, which is
the lane's credit bar.  Model selection is nested: outer quadrant q is scored
only with patterns chosen on the other quadrants' cells.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ALPHA = 0.2
ALONG_PX = 3
SIGMA_MIN, SIGMA_MAX = 0.5, 3.0
U_TOL = 0.0


@dataclass(frozen=True)
class Pattern:
    name: str
    kind: str            # "single" | "pair" | "triple"

    def offsets(self, sigma: float) -> tuple[float, ...]:
        w = float(np.clip(sigma, SIGMA_MIN, SIGMA_MAX))
        if self.kind == "single" or sigma < SIGMA_MIN:
            return (0.0,)
        if self.kind == "pair":
            return (-w / 2.0, w / 2.0)
        return (-w, 0.0, w)


PATTERNS: tuple[Pattern, ...] = (
    Pattern("P1-single", "single"),
    Pattern("P2-pair", "pair"),
    Pattern("P3-triple", "triple"),
)


def segment_dots(seg, offsets: tuple[float, ...], shape: tuple[int, int],
                 along_px: int = ALONG_PX) -> np.ndarray:
    """Dotted parallel lines for one segment: (n, 2) int pixel coords."""
    idx = seg.idx.astype(np.float64)
    if idx.shape[0] < 2:
        pts = idx
        tangent = np.array([1.0, 0.0])
    else:
        c = idx.mean(axis=0)
        u, s, _vt = np.linalg.svd(idx - c, full_matrices=False)
        tangent = _vt[0]
        proj = (idx - c) @ tangent
        order = np.argsort(proj)
        pts = idx[order]
        # approximate arclength along the PCA axis
        arclen = proj[order]
    normal = np.array([-tangent[1], tangent[0]])
    if idx.shape[0] < 2:
        base = pts
    else:
        keep = [0]
        last = arclen[0]
        for i in range(1, pts.shape[0]):
            if arclen[i] - last >= along_px:
                keep.append(i)
                last = arclen[i]
        base = pts[keep] if keep else pts[:1]
    out = []
    h, w = shape
    for off in offsets:
        cand = base + off * normal
        rr = np.rint(cand[:, 0]).astype(int)
        cc = np.rint(cand[:, 1]).astype(int)
        ok = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        out.append(np.stack([rr[ok], cc[ok]], axis=1))
    if not out:
        return np.zeros((0, 2), int)
    dots = np.concatenate(out, axis=0)
    return np.unique(dots, axis=0)


def dots_to_mask(dots: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    m = np.zeros(shape, bool)
    if len(dots):
        m[dots[:, 0], dots[:, 1]] = True
    return m


def exact_terms(mask: np.ndarray, cell) -> dict:
    """Setwise exact DTI terms of a binary emission inside one holdout cell.

    Delegates to the shared template's ``gems57.holdout.score_cell`` (official
    triangular-kernel arithmetic lives in ``gems57.metric``).
    """
    from gems57.holdout import score_cell

    return score_cell(cell, mask)


def utility(tp: float, fp: float, s0: float, alpha: float = ALPHA) -> float:
    """U = (1 - alpha*s0) * TP - alpha*s0 * FP (exact-metric pattern-change rule)."""
    return (1.0 - alpha * s0) * tp - alpha * s0 * fp
