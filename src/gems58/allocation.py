"""Ribbon allocation: how many parallel dotted lines, and at what offsets.

Given a candidate ridge segment and a localisation-error scale ``sigma`` (pixels,
from ``sigma.py``), the emitter places ``n`` dotted lines parallel to the ridge
at perpendicular offsets ``o_1 .. o_n``.  The lane protocol fixes the two
decision rules:

**Offsets.**  Line spacing is the kernel radius ``R = 3`` px, because two
parallel lines closer than ``R`` compete for the same truth pixels: the metric
credits a truth pixel with the *maximum* kernel value over predictions, so two
dots 1 px apart covering one truth pixel buy ``max(k1, k2) ~ 1`` for a cost of
``0.4`` instead of ``0.2``.  Offsets are therefore drawn from the lattice
``{0, +-R, +-2R, ...}`` and the ribbon is symmetric about the ridge.

**How many.**  Exactly the number that maximises

    U(sigma) = (1 - alpha * DTI0) * dTP - alpha * DTI0 * dFP

evaluated with the exact metric.  For one extra line at offset ``o`` the
expected per-dot contributions under a Normal(0, sigma^2) across-strike offset
model are

    dTP_o = E[ max(0, 1 - |delta - o| / R) ] - E[ max(0, 1 - |delta| / R) ]_already
    dFP_o = 1 - dTP_o / (credit of that line alone if it were the only line)

and both are evaluated **exactly on the holdout** in
``scripts/run_holdout_eval.py``, which is the arbiter.  This module supplies the
deterministic geometry and the closed-form Normal expectation used for the
pre-registered decision rule.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import label
from scipy.special import erf

from .metric import ALPHA, RADIUS_PX

#: Absolute tolerance on the marginal U, so that quadrature dust (|U| ~ 1e-15) in the
#: far tail of the Normal model cannot justify an extra line.
U_TOL: float = 1e-6

#: A pair of extra lines is only added when its marginal value exceeds this
#: fraction of the first (central) line's expected credit.  Without it the
#: quadrature tail of a Normal(0, 0.5^2) model reports ~1e-4 gains that are far
#: below the model's own validity, and the "single tight line below sigma 0.5 px"
#: rule of the lane protocol would never trigger.
MATERIALITY: float = 1e-3

#: Along-strike dot spacings (px) considered for the "dotted" variants.
ALONG_SPACINGS: tuple[int, ...] = (1, 2, 3)


def normal_credit(mu: float, sigma: float, radius: float = RADIUS_PX,
                  n_grid: int = 2401, half: float = 12.0) -> float:
    """E[ max(0, 1 - |delta - mu| / R) ] for delta ~ N(0, sigma^2), by quadrature."""
    if sigma <= 1e-9:
        return max(0.0, 1.0 - abs(mu) / radius)
    x = np.linspace(-half, half, n_grid)
    pdf = np.exp(-0.5 * (x / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))
    pdf /= pdf.sum() * (x[1] - x[0]) or 1.0
    k = np.maximum(0.0, 1.0 - np.abs(x - mu) / radius)
    return float((k * pdf).sum() * (x[1] - x[0]))


def cdf(x: float, sigma: float) -> float:
    if sigma <= 1e-9:
        return 1.0 if x >= 0 else 0.0
    return 0.5 * (1.0 + erf(x / (sigma * np.sqrt(2.0))))


@dataclass
class RibbonPlan:
    n_lines: int
    offsets: tuple[float, ...]
    dTP_per_dot: float
    dFP_per_dot: float
    U: float
    u_tolerance: float = 1e-6


def plan(sigma: float, dti0: float, max_k: int = 3, alpha: float = ALPHA) -> RibbonPlan:
    """Symmetric ribbon plan for one segment with localisation scale ``sigma``.

    The ribbon is symmetric about the ridge and its offsets are the lattice
    ``{0, +-R, +-2R, ...}``: a *half-width* ``k`` places ``2k+1`` parallel dotted
    lines at offsets ``0, +-R, ..., +-kR``.  ``k`` grows while the marginal value
    of the next +-pair is positive, i.e. while

        U = (1 - alpha*DTI0) * dTP - alpha*DTI0 * dFP  >  0

    with ``dTP`` the *additional* truth credit the pair captures beyond what the
    already-chosen lines capture (the metric takes per-truth maxima, so lines
    overlap rather than add) and ``dFP`` the mass the pair spends on truth it does
    not reach.
    """
    base_credit = normal_credit(0.0, sigma)
    floor = MATERIALITY * max(base_credit, 1e-12)
    # the lane prescribes a ribbon "about +-sigma wide": never reach beyond the
    # smallest lattice offset that covers sigma
    k_target = max(1, int(np.ceil(sigma / RADIUS_PX)))
    chosen: list[float] = [0.0]
    d_tp = d_fp = 0.0
    for k in range(1, min(max_k, k_target) + 1):
        o = k * RADIUS_PX
        dTP, dFP = _marginal_pair(chosen, o, sigma)
        U = (1.0 - alpha * dti0) * dTP - alpha * dti0 * dFP
        if U <= max(U_TOL, floor):
            break
        chosen.extend([-o, o])
        d_tp += dTP
        d_fp += dFP
    return RibbonPlan(n_lines=len(chosen), offsets=tuple(sorted(chosen)),
                      dTP_per_dot=float(d_tp), dFP_per_dot=float(d_fp),
                      U=float((1 - alpha * dti0) * d_tp - alpha * dti0 * d_fp),
                      u_tolerance=U_TOL)


def _marginal_pair(prev: list[float], o: float, sigma: float,
                   radius: float = RADIUS_PX, half: float = 12.0,
                   n: int = 2401) -> tuple[float, float]:
    """(dTP, dFP) of adding the symmetric pair +-``o`` to the lines in ``prev``.

    Both dots of the pair cover the same truth pixels, so they are costed once
    each but credited once together: ``dTP`` is the extra truth credit the pair
    captures over ``prev``, and ``dFP`` is the mass that reaches no truth at all.
    """
    x = np.linspace(-half, half, n)
    dx = x[1] - x[0]
    pdf = np.exp(-0.5 * (x / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))
    pdf = pdf / (pdf.sum() * dx)
    k_pair = np.maximum(0.0, 1.0 - np.abs(np.abs(x) - o) / radius)
    if prev:
        k_old = np.max(np.stack([np.maximum(0.0, 1.0 - np.abs(x - p) / radius)
                                 for p in prev]), axis=0)
    else:
        k_old = np.zeros_like(x)
    dTP = float((np.maximum(k_pair - k_old, 0.0) * pdf).sum() * dx)
    uncovered = (k_old <= 0.0).astype(float)
    dFP = 2.0 * float(((1.0 - k_pair) * pdf * uncovered).sum() * dx)
    return dTP, dFP


def ridge_pixel_neighbours(idx: np.ndarray, offsets_px: tuple[int, ...] | None = None):
    """Pixel offsets used to expand a ridge pixel across strike (8-neighbourhood)."""
    if offsets_px is not None:
        return offsets_px
    return (-3, -2, -1, 0, 1, 2, 3)


def ribbon_mask(field: dict, segs, sigma_of, along_spacing: int = 1,
                max_lines: int = 3, allowed: np.ndarray | None = None,
                dti0: float = 0.0) -> dict:
    """Rasterise the ribbon emission for a list of ridge segments.

    ``sigma_of(segment) -> float`` returns the localisation scale in pixels for
    that segment (from the held-out sigma table).  Lines are offset along the
    segment's own across-strike vector, in whole pixels, with spacing R = 3 px.
    """
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    plans: list[dict] = []
    for s in segs:
        idx = s["idx"]
        if along_spacing > 1:
            axis = np.argmax(np.var(idx.astype(float), axis=0))
            order = np.argsort(idx[:, axis])
            idx = idx[order][::along_spacing]
        sig = float(sigma_of(s))
        pl = plan(sig, dti0, max_lines=max_lines)
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        placed = 0
        for o in pl.offsets:
            rr = np.rint(idx[:, 0] + o * ay).astype(int)
            cc = np.rint(idx[:, 1] + o * ax).astype(int)
            ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
            rr, cc = rr[ok], cc[ok]
            fresh = ~mask[rr, cc]
            mask[rr, cc] = True
            placed += int(fresh.sum())
        plans.append(dict(size=int(s["size"]), sigma=sig, n_lines=pl.n_lines,
                          offsets=list(pl.offsets), U=pl.U, dots_placed=placed,
                          codes=s["codes"][:1]))
    if allowed is not None:
        mask &= allowed
    return dict(mask=mask, plans=plans, n_dots=int(mask.sum()))


def dedupe_speckles(mask: np.ndarray, min_cluster: int = 1) -> np.ndarray:
    """Keep only dots whose 8-neighbourhood has fewer than ``min_cluster`` members.

    The metric pays a fixed ``alpha = 0.2`` per emitted pixel and credits a truth
    pixel with the maximum kernel value over predictions, so a cluster of *c*
    adjacent dots covering one truth pixel buys about one dot's worth of credit
    for ``0.2 * c``.  ``min_cluster=2`` removes any dot that touches another dot,
    which is the strongest available thinning.
    """
    if min_cluster <= 1:
        return mask
    k = np.ones((3, 3), int)
    k[1, 1] = 0
    from scipy.ndimage import convolve

    n = convolve(mask.astype(np.int32), k, mode="constant")
    return mask & (n < (min_cluster - 1))
