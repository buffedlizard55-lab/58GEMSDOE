"""Exact-metric simulation of dotted emission geometry vs localization error.

The lane question is: given a fault segment whose position we know only to
within a localization error ``sigma`` (across-strike), what *dot pattern* maximises
the official metric's marginal utility

    U = (1 - alpha*s) * dTP - alpha*s * dFP,      alpha = 0.2, s = current DTI

with ``dTP``/``dFP`` the **exact** marginal changes of the published
distance-weighted Tversky components (gems57.metric is the oracle; nothing here
re-implements it).

Everything is computed on an isolated synthetic segment, which is legitimate
because the official denominator is exactly additive over emitted dots and truth
cells:

    DTI = T / (alpha*(T + FP) + beta*|G|),   FP = sum_i (1 - k_i) over dots

so the marginal utility of a pattern is a function of that pattern's own
``dTP``, its dot count ``n`` and its self-credit sum ``sum k_i``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gems57.metric import ALPHA, dti_from_components


@dataclass(frozen=True)
class Segment:
    """Synthetic ground-truth segment: centreline + scatter."""

    length_px: int = 60
    truth_scatter_px: float = 1.85
    seed: int = 7


def truth_pixels(seg: Segment) -> np.ndarray:
    """Boolean truth mask on a ``(rows, cols)`` grid, centreline along columns."""
    rows = int(6 * seg.truth_scatter_px) + 12
    cols = seg.length_px + 24
    grid = np.zeros((rows, cols), bool)
    rng = np.random.default_rng(seg.seed)
    mid = rows // 2
    for x in range(6, 6 + seg.length_px):
        off = rng.normal(0.0, seg.truth_scatter_px)
        r = int(round(mid + off))
        if 0 <= r < rows:
            grid[r, x] = True
    # a rasterised fault trace is at least one pixel wide everywhere
    for x in range(6, 6 + seg.length_px):
        col = np.flatnonzero(grid[:, x])
        if col.size == 0:
            grid[mid, x] = True
    return grid


def pattern_dots(shape: tuple[int, int], seg: Segment, *, n_lines: int, spacing_px: float,
                 along_px: float, bias_px: float = 0.0,
                 truth_scatter_px: float | None = None) -> np.ndarray:
    """Dot pattern for a segment: ``n_lines`` parallel dotted lines.

    ``bias_px`` is the across-strike localization error of the whole estimate
    (the estimated centreline is ``bias_px`` away from the truth centreline).
    Lines are staggered in along-strike phase so the lattice stays uniform.
    """
    rows, cols = shape
    mid = rows // 2 + bias_px
    out = np.zeros(shape, bool)
    offsets = (np.arange(n_lines) - (n_lines - 1) / 2.0) * spacing_px
    for li, off in enumerate(offsets):
        r = mid + off
        phase = (li / max(1, n_lines)) * along_px     # staggered lattice
        x = 6.0 + phase
        while x < 6 + seg.length_px:
            rr = int(round(r))
            xx = int(round(x))
            if 0 <= rr < rows and 0 <= xx < cols:
                out[rr, xx] = True
            x += along_px
    return out


def exact_terms(dots: np.ndarray, truth: np.ndarray) -> dict:
    """Exact tp/fp/fn of a binary dot field against a binary truth mask.

    Uses the shared oracle: an isolated-dot distance transform is mathematically
    identical to ``gems57.metric.max_cover`` for binary predictions, and the
    identity is asserted against it in the unit tests.
    """
    from scipy import ndimage as ndi

    from gems57.metric import kernel

    d = np.asarray(dots, bool)
    g = np.asarray(truth, bool)
    n_truth = int(g.sum())
    if n_truth == 0 or not d.any():
        return dict(tp=0.0, fp=float(d.sum()), fn=float(n_truth), n_dots=int(d.sum()))
    dp = ndi.distance_transform_edt(~d)
    tp = float(kernel(dp[g]).sum())
    dg = ndi.distance_transform_edt(~g)
    fp = float((1.0 - kernel(dg[d])).sum())
    return dict(tp=tp, fp=fp, fn=float(n_truth) - tp, n_dots=int(d.sum()))


def utility(d_tp: float, d_fp: float, dti0: float, alpha: float = ALPHA) -> float:
    """The lane's exact marginal utility ``U = (1 - alpha*s) * dTP - alpha*s * dFP``."""
    return (1.0 - alpha * dti0) * d_tp - alpha * dti0 * d_fp


def evaluate_patterns(dti0: float, *, truth_scatter_px: float = 1.85,
                      biases=(0.0, 0.5, 1.0, 1.5, 2.0, 3.0),
                      line_counts=(1, 2, 3, 5), spacings=(1.5, 2.0, 2.8, 3.5),
                      alongs=(2.0, 2.8, 3.0, 4.0, 6.0), length_px: int = 60,
                      seed: int = 7) -> dict:
    """Sweep every (lines, line spacing, along-strike spacing) pattern per bias.

    Returns the receipts: for each bias class the best pattern by ``U``, the
    single-tight-line reference, and the simulated score of each.
    """
    seg = Segment(length_px=length_px, truth_scatter_px=truth_scatter_px, seed=seed)
    shape = (int(6 * truth_scatter_px) + 12, length_px + 24)
    truth = truth_pixels(seg)
    rows = []
    for bias in biases:
        for k in line_counts:
            for sp in spacings:
                for al in alongs:
                    if k == 1 and sp != spacings[0]:
                        continue
                    dots = pattern_dots(shape, seg, n_lines=k, spacing_px=sp,
                                        along_px=al, bias_px=bias)
                    t = exact_terms(dots, truth)
                    u = utility(t["tp"], t["fp"], dti0)
                    rows.append(dict(bias_px=float(bias), n_lines=int(k),
                                     line_spacing_px=float(sp), along_px=float(al),
                                     dots=t["n_dots"], tp=t["tp"], fp=t["fp"],
                                     coverage=t["tp"] / max(1, truth.sum()),
                                     u=u,
                                     dti_isolated=dti_from_components(
                                         t["tp"], t["fp"], t["fn"], 0.2, 0.8)))
    best_by_bias = {}
    for r in rows:
        b = r["bias_px"]
        if b not in best_by_bias or r["u"] > best_by_bias[b]["u"]:
            best_by_bias[b] = r
    ref = {}
    for r in rows:
        if r["n_lines"] == 1 and r["along_px"] == 3.0:
            ref[r["bias_px"]] = r
    return dict(truth_scatter_px=truth_scatter_px, seed=seed, dti0=dti0,
                alpha=ALPHA, n_patterns=len(rows), rows=rows,
                best_by_bias={str(k): v for k, v in sorted(best_by_bias.items())},
                single_tight_line_by_bias={str(k): v for k, v in sorted(ref.items())})
