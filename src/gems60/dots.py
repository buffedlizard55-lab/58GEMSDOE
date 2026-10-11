"""Turn a convergence surface into a belief surface, then into isolated dots.

Two steps, both metric-aware:

``skeleton``
    Non-maximum suppression **across strike** (along the tensor's largest
    eigenvector), the same reduction the family's ridge lanes used, so a
    lineament of width *w* becomes a 1-px line rather than *w* rows of equal
    score.  Suppression is done in C-order over the whole block at once.

``ribbon``
    The lane's localisation-error decision.  Given the across-strike error
    ``sigma`` (pixels) measured on the holdout for a feature class, a *single*
    tight line is emitted when ``sigma < SIGMA_SINGLE_PX``; otherwise the
    skeleton is replicated at offsets ``0, +-delta, ...`` up to ``+-sigma`` so
    that the truth -- which can lie anywhere inside that band -- is inside 1 px
    of a dotted line wherever it actually is.  The offsets are applied by integer
    translation of the skeleton mask along the local across-strike direction, so
    the pattern follows strike rather than sitting in a fixed frame.

The dot set itself is *not* chosen here: :func:`gems57.emit.allocate_by_marginal_bar`
does that with the exact two-sided metric test on the belief surface.  This
module only fixes the surface's shape, which is the part that must be calibrated
to the measured localization error.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from gems57.metric import kernel

SIGMA_SINGLE_PX = 0.5     # below this, a single tight line is optimal
RIBBON_LINE_SPACING_PX = 3.0   # the 300 m kernel radius: parallel lines at +-3 px


def skeleton(score: np.ndarray, ax: np.ndarray, ay: np.ndarray,
             valid: np.ndarray) -> np.ndarray:
    """Keep only pixels that are maximal along the across-strike direction.

    ``(ax, ay)`` is the unit across-strike vector of the winning family at each
    pixel.  A pixel survives when its score is >= that of its two integer
    neighbours along ``+-d`` for the 3-px kernel radius.  Because the neighbours
    are integer displacements, the result is a thinning toward the crest of the
    lineament rather than a mathematically exact ridge, which is all the emitter
    needs (it re-derives credit with the exact metric).
    """
    s = np.asarray(score, np.float32)
    v = np.asarray(valid, bool) & (s > 0)
    keep = np.zeros(s.shape, bool)
    # walk a small set of offsets so curved strike directions are handled
    for r in (1, 2, 3):
        dy = np.rint(r * np.asarray(ay, np.float32)).astype(np.int32)
        dx = np.rint(r * np.asarray(ax, np.float32)).astype(np.int32)
        y0 = np.arange(s.shape[0])[:, None] - dy
        x0 = np.arange(s.shape[1])[None, :] - dx
        y1 = np.arange(s.shape[0])[:, None] + dy
        x1 = np.arange(s.shape[1])[None, :] + dx
        ok0 = (y0 >= 0) & (y0 < s.shape[0]) & (x0 >= 0) & (x0 < s.shape[1])
        ok1 = (y1 >= 0) & (y1 < s.shape[0]) & (x1 >= 0) & (x1 < s.shape[1])
        n0 = np.where(ok0, s[np.clip(y0, 0, s.shape[0] - 1), np.clip(x0, 0, s.shape[1] - 1)], -1.0)
        n1 = np.where(ok1, s[np.clip(y1, 0, s.shape[0] - 1), np.clip(x1, 0, s.shape[1] - 1)], -1.0)
        keep |= (s >= n0) & (s >= n1)
        del y0, x0, y1, x1, ok0, ok1, n0, n1
    return keep & v


def _shift(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros_like(mask, bool)
    h, w = mask.shape
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    out[ys0:ys1, xs0:xs1] = mask[max(0, -dy):min(h, h - dy),
                                 max(0, -dx):min(w, w - dx)]
    return out


def ribbon(skel: np.ndarray, skel_ax: np.ndarray, skel_ay: np.ndarray,
           sigma_px: float, *, spacing_px: float = RIBBON_LINE_SPACING_PX) -> tuple[np.ndarray, list[int]]:
    """Replicate a skeleton at parallel offsets out to ``+-sigma_px``.

    Returns the union mask and the integer offsets (in *spacing* units) used, so
    the receipts can name the ribbon the lane asked for.  Offsets are applied
    along the skeleton's *local* across-strike direction, so the parallel lines
    follow strike rather than a fixed screen axis.
    """
    skel = np.asarray(skel, bool)
    if sigma_px < SIGMA_SINGLE_PX or spacing_px <= 0:
        return skel.copy(), [0]
    n_side = int(np.floor(sigma_px / spacing_px + 1e-9))
    n_side = max(n_side, 1)
    out = skel.copy()
    used = [0]
    yy, xx = np.nonzero(skel)
    if yy.size == 0:
        return out, used
    ax = np.asarray(skel_ax, np.float32)[yy, xx]
    ay = np.asarray(skel_ay, np.float32)[yy, xx]
    for j in range(1, n_side + 1):
        for sign in (+1, -1):
            dy = np.rint(sign * j * spacing_px * ay).astype(np.int32)
            dx = np.rint(sign * j * spacing_px * ax).astype(np.int32)
            oy = yy + dy
            ox = xx + dx
            ok = (oy >= 0) & (oy < skel.shape[0]) & (ox >= 0) & (ox < skel.shape[1])
            out[oy[ok], ox[ok]] = True
            used.append(sign * j)
    return out, sorted(set(used))


def thin(mask: np.ndarray, score: np.ndarray, *, min_sep_px: float = 3.0) -> np.ndarray:
    """Greedy minimum-separation thinning of a candidate mask.

    Walks candidates in descending ``score`` and keeps one whenever no kept
    candidate lies within ``min_sep_px`` (a disc of that radius is cleared around
    it).  The result is the dotted lattice the lane asks for: along a lineament
    the dots end up ~``min_sep_px`` apart, which is what kept the family's best
    files at a measured nearest-neighbour distance of 2.8-3.2 px, and no dot is
    closer than the kernel radius to another.
    """
    m = np.asarray(mask, bool).copy()
    sc = np.asarray(score, np.float32)
    r = int(np.ceil(min_sep_px))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = yy * yy + xx * xx <= min_sep_px * min_sep_px
    keep = np.zeros(m.shape, bool)
    flat_order = np.argsort(-sc[m], kind="stable")
    ys, xs = np.nonzero(m)
    for k in flat_order:
        y, x = int(ys[k]), int(xs[k])
        if not m[y, x]:
            continue
        keep[y, x] = True
        y0, y1 = y - r, y + r + 1
        x0, x1 = x - r, x + r + 1
        sy0, sx0 = max(0, -y0), max(0, -x0)
        sy1 = disk.shape[0] - max(0, y1 - m.shape[0])
        sx1 = disk.shape[1] - max(0, x1 - m.shape[1])
        m[max(0, y0):min(m.shape[0], y1), max(0, x0):min(m.shape[1], x1)] &= ~disk[sy0:sy1, sx0:sx1]
    return keep


def belief(skeleton_mask: np.ndarray, strength: np.ndarray, *, sharpen: float = 4.0,
           blur_px: float = 0.0) -> np.ndarray:
    """Belief surface ``p`` at the skeleton: strength normalised to a peak of 1.

    ``sharpen`` raises the *relative* contrast between strong and weak
    candidates (rank preservation, scale change), and ``blur_px`` optionally
    spreads mass by the residual measurement error.  The emitter re-derives the
    credit with the exact metric; this only sets the sampling density.
    """
    s = np.asarray(strength, np.float32).copy()
    s[~np.asarray(skeleton_mask, bool)] = 0.0
    m = float(np.nanmax(s)) if np.isfinite(s).any() else 0.0
    if m <= 0:
        return np.zeros_like(s)
    p = np.clip(s / m, 0.0, 1.0) ** float(sharpen)
    if blur_px and blur_px > 0:
        p = ndi.gaussian_filter(p, float(blur_px), mode="constant")
        m2 = float(p.max())
        if m2 > 0:
            p = (p / m2).astype(np.float32)
    return p.astype(np.float32)
