"""Multi-family, multi-scale ridge (lineament) extraction on the official stack.

Method
------
For a scalar band ``v`` and a ridge scale ``s`` (Gaussian sigma in pixels):

1. smooth: ``g = G_s * v``
2. Hessian: ``(Hxx, Hxy, Hyy) = (G_s d2/dx2, G_s d2/dxdy, G_s d2/dy2) * v``
3. the two eigenvalues of the symmetric 2x2 Hessian are ``tr/2 +- disc`` with
   ``tr = Hxx + Hyy`` and ``disc = sqrt(max(tr^2/4 - det, 0))``,
   ``det = Hxx*Hyy - Hxy^2``.
4. the **line/ridge magnitude** is the difference of the eigenvalue magnitudes,
   which has the closed form

       M = | |lambda_+| - |lambda_-| | = 2 * min(|tr| / 2, disc)

   (checked by ``tests/test_ridges.py`` against ``numpy.linalg.eigvalsh``).
   ``M`` is large exactly where the curvature across strike exceeds the
   curvature along strike, i.e. on curvilinear structure, and is independent of
   the sign of the structure (scarp or trough both count).
5. the **across-strike unit vector** is the eigenvector of the
   larger-|lambda| eigenvalue.  The eigenvector of ``lambda_max = tr/2 + disc``
   has angle ``theta = 0.5 * atan2(2*Hxy, Hxx - Hyy)``; the across-strike
   direction is ``theta`` when ``tr >= 0`` else ``theta + pi/2``.
6. non-maximum suppression of ``M`` along +- the across-strike direction thins
   the response to a 1-pixel centreline per ridge.
7. the signed across-strike curvature ``curv`` gives the ridge **sign**
   (negative = crest/bright ridge, positive = trough/dark ridge).

Ridge types are then ``(family, scale, sign)``: 19 bands grouped into 6
organizer families x 2-3 scales x 2 signs.

Nothing in this module reads the catalogue: extraction is entirely
feature-based, which is what makes the hide-and-recover measurement in
``holdout.py`` leakage-free.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter, label

from . import features as F

#: Ridge scales in pixels.  1.5 px = 150 m resolves single scarps; 3 px = 300 m
#: matches the scoring kernel; 6 px = 600 m resolves fault-zone envelopes.
SCALES: tuple[float, ...] = (1.5, 3.0, 6.0)

#: Standard deviation of the isotropic structure-tensor-free smoothing used only
#: to stabilise the sign field.
SIGN_SMOOTH: float = 0.0


@dataclass
class RidgeField:
    """Per-(band, scale, sign) detection output on the full grid."""

    band: str
    family: str
    scale: float
    sign: int          # -1 crest, +1 trough
    magnitude: np.ndarray   # float32, |lambda_max| - |lambda_min|
    nms: np.ndarray         # bool, thinned centreline candidates
    across_x: np.ndarray    # float32 unit across-strike x component
    across_y: np.ndarray    # float32 unit across-strike y component


def hessian_ridge(v: np.ndarray, sigma: float, valid: np.ndarray) -> dict:
    """Hessian ridge response for one smoothed field.  See module docstring."""
    vv = np.where(valid & np.isfinite(v), v, 0.0).astype(np.float32)
    if not np.isfinite(v).all():
        # Normalise by a robust scale inside the valid footprint so that a
        # nodata-replaced zero does not create a spurious step.
        w = valid & np.isfinite(v)
        mu = float(np.median(v[w]))
        mad = float(np.median(np.abs(v[w] - mu))) or 1.0
        vv = np.where(w, (v - mu) / (1.4826 * mad), 0.0).astype(np.float32)

    kw = dict(mode="nearest", truncate=4.0)
    g = gaussian_filter(vv, sigma, **kw)
    # Hessian in (x, y) = (axis 1, axis 0) coordinates.  Note the order swap:
    # gaussian_filter's `order` indexes (axis0, axis1) = (y, x).
    hyy = gaussian_filter(vv, sigma, order=(2, 0), **kw)   # d2/dy2
    hxx = gaussian_filter(vv, sigma, order=(0, 2), **kw)   # d2/dx2
    hxy = gaussian_filter(vv, sigma, order=(1, 1), **kw)   # d2/dxdy

    tr = hxx + hyy
    det = hxx * hyy - hxy * hxy
    disc = np.sqrt(np.maximum(tr * tr * 0.25 - det, 0.0))
    magnitude = (2.0 * np.minimum(np.abs(tr) * 0.5, disc)).astype(np.float32)

    curv = (tr * 0.5) + np.sign(tr) * disc          # eigenvalue of larger |.|
    theta = 0.5 * np.arctan2(2.0 * hxy, hxx - hyy)  # eigenvector of lambda_max, in (x, y)
    # the eigenvector of the larger-|lambda| eigenvalue is across strike
    across = np.where(tr >= 0.0, theta, theta + 0.5 * np.pi)
    ax = np.cos(across).astype(np.float32)
    ay = np.sin(across).astype(np.float32)
    _ = g  # the smoothed field is only needed for the scale; kept for parity
    return dict(magnitude=magnitude, curv=curv.astype(np.float32), ax=ax, ay=ay)


def nonmax_suppress(magnitude: np.ndarray, ax: np.ndarray, ay: np.ndarray,
                    valid: np.ndarray) -> np.ndarray:
    """Keep pixels that are the local maximum of ``magnitude`` across strike."""
    h, w = magnitude.shape
    xs = np.clip(ax, -1.0, 1.0)
    ys = np.clip(ay, -1.0, 1.0)
    # round the sub-pixel across-strike direction to the nearest of 8 offsets
    ang = np.arctan2(ys, xs)
    octant = np.round(ang / (np.pi / 4.0)).astype(np.int32) % 8
    offs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    keep = np.zeros(magnitude.shape, bool)
    strictly = np.zeros(magnitude.shape, bool)
    ii, jj = np.mgrid[0:h, 0:w]
    for o, (dx, dy) in enumerate(offs):
        m = (octant == o) & valid
        if not m.any():
            continue
        ge = np.ones(magnitude.shape, bool)
        for sgn in (+1, -1):
            ni = np.clip(ii + sgn * dy, 0, h - 1)
            nj = np.clip(jj + sgn * dx, 0, w - 1)
            nb = magnitude[ni, nj]
            ge &= (magnitude >= nb)
            strictly |= m & (magnitude > nb)
        keep |= m & ge
    # a pixel survives only if it is a local maximum in at least one direction and
    # never below a neighbour --- flat plateaus (including the empty background) drop out
    return keep & strictly


def detect(band: str, scale: float, valid: np.ndarray, min_sign: bool = True) -> RidgeField:
    """Ridge detection for one band and one scale."""
    v = F.band(band)
    r = hessian_ridge(v, scale, valid)
    mag = r["magnitude"]
    nms = nonmax_suppress(mag, r["ax"], r["ay"], valid)
    sign = -1 if float(np.mean(r["curv"][valid & nms])) < 0 else 1
    family = next((k for k, v2 in F.FAMILIES.items() if band in v2), "other")
    _ = min_sign
    return RidgeField(band=band, family=family, scale=float(scale), sign=int(sign),
                      magnitude=mag, nms=nms & valid, across_x=r["ax"], across_y=r["ay"])


def connected_segments(mask: np.ndarray, max_gap: int = 0) -> list[np.ndarray]:
    """Connected components of a boolean mask, returned as (n, 2) index arrays."""
    if max_gap > 0:
        m = mask.copy()
        for _ in range(max_gap):
            m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
        lab, n = label(m)
    else:
        lab, n = label(mask)
    out = []
    for i in range(1, n + 1):
        idx = np.argwhere(lab == i)
        if idx.size:
            out.append(idx)
    return out
