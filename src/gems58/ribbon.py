"""Ribbon lane: candidate ridges from geophysical bands only, across-strike error scale, parallel dots.

Nothing in this module reads the fault catalogue. The catalogue is used only by the holdout
(hide-and-recover) in scripts/run_ribbon_lane.py, which withholds whole segments.

Ridge types (band numbers are 1-based as in the GeoDAWN stack, see data/README.md):
  topo : band 12 "Detrended elevation" (Sato ridge filter, bright ridges)
  edge : band 3  "Total magnetic intensity horizontal gradient" (ridge filter on the edge response)
Feature resolution:
  native : Sato sigmas 1-2 px on the 100 m grid
  coarse : 3 px Gaussian pre-smoothing (~300 m effective scale), Sato sigmas 3-4 px
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.ndimage import distance_transform_edt
from skimage.filters import sato
from skimage.morphology import remove_small_objects, skeletonize

BAND = {"topo": 12, "edge": 3}
SIGMAS = {"native": [1.0, 2.0], "coarse": [3.0, 4.0]}


def fill_band(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """NaN/nodata -> band median inside footprint; outside footprint -> 0. Documented, see README."""
    a = arr.astype(np.float64).copy()
    bad = ~np.isfinite(a) | (a < -1e38)
    med = np.nanmedian(np.where(bad, np.nan, a)[footprint])
    a[bad] = med
    a[~footprint] = 0.0
    return a


def ridge_score(band: np.ndarray, footprint: np.ndarray, ridge_type: str, resolution: str) -> np.ndarray:
    b = fill_band(band, footprint)
    if ridge_type == "edge":
        b = ndi.gaussian_gradient_magnitude(b, 1.0)  # edge response of the magnetic gradient band
    if resolution == "coarse":
        b = ndi.gaussian_filter(b, 3.0)
    b = (b - b[footprint].mean()) / (b[footprint].std() + 1e-12)
    s = sato(b, sigmas=SIGMAS[resolution], black_ridges=False)
    s[~footprint] = 0.0
    return s


def candidate_ridges(score: np.ndarray, footprint: np.ndarray, top_frac: float = 0.03,
                     min_len: int = 10):
    """Skeleton of the top `top_frac` ridge-score pixels (inside footprint). Returns bool skeleton."""
    thr = np.quantile(score[footprint], 1.0 - top_frac)
    m = (score >= thr) & footprint
    m = remove_small_objects(m, max_size=min_len - 1, connectivity=2)
    return skeletonize(m)


def across_strike_normals(score: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit across-ridge direction (nx, ny) from the Hessian eigenvector of largest |eigenvalue|."""
    s = ndi.gaussian_filter(score, 1.0)
    gy, gx = np.gradient(s)
    gyy, _ = np.gradient(gy)
    gyx, gxx = np.gradient(gx)
    H = np.stack([np.stack([gyy, gyx], -1), np.stack([gyx, gxx], -1)], -2)  # (H,W,2,2)
    w, v = np.linalg.eigh(H)
    idx = np.argmax(np.abs(w), axis=-1)
    vec = np.take_along_axis(v, idx[..., None, None], axis=-1)[..., 0]  # (H,W,2) in (y,x)
    ny, nx = vec[..., 0], vec[..., 1]
    nx[~footprint] = 0.0
    ny[~footprint] = 0.0
    return nx, ny


def emit_parallel(skel: np.ndarray, nx: np.ndarray, ny: np.ndarray, offsets, footprint: np.ndarray,
                  known: np.ndarray | None = None) -> np.ndarray:
    """Dots at every skeleton pixel shifted by each offset (pixels) along the across-ridge normal."""
    H, W = skel.shape
    yy, xx = np.nonzero(skel)
    out = np.zeros((H, W), bool)
    for o in offsets:
        py = np.rint(yy + o * ny[yy, xx]).astype(int)
        px = np.rint(xx + o * nx[yy, xx]).astype(int)
        ok = (py >= 0) & (py < H) & (px >= 0) & (px < W)
        out[py[ok], px[ok]] = True
    out &= footprint
    if known is not None:
        out &= ~known
    return out


def across_strike_offsets(withheld: np.ndarray, seg_id: np.ndarray, cand: np.ndarray,
                          footprint: np.ndarray, max_dist: float = 10.0):
    """Signed across-strike offsets (px) from each candidate pixel to its nearest withheld segment.

    Strike = principal axis of the segment's pixel cloud; normal = perpendicular to it.
    Only candidates within `max_dist` px of a withheld pixel are used.
    Returns (offsets, distances).
    """
    if withheld.sum() == 0:
        return np.array([]), np.array([])
    d, (iy, ix) = distance_transform_edt(~withheld, return_indices=True)
    cy, cx = np.nonzero(cand & footprint)
    dd = d[cy, cx]
    keep = dd <= max_dist
    cy, cx, dd = cy[keep], cx[keep], dd[keep]
    sy, sx = iy[cy, cx], ix[cy, cx]
    # per-segment normal from PCA of pixel coordinates (bounding-box slices keep this O(total px))
    ids = seg_id[sy, sx]
    nseg = int(seg_id.max()) + 1
    normals = np.zeros((nseg, 2))
    normals[:, 1] = 1.0
    for sid, sl in enumerate(ndi.find_objects(seg_id), start=1):
        if sl is None:
            continue
        sub = seg_id[sl] == sid
        yy, xx = np.nonzero(sub)
        if yy.size < 3:
            continue
        yy = yy + sl[0].start
        xx = xx + sl[1].start
        c = np.cov(np.vstack([yy, xx]))
        w, v = np.linalg.eigh(c)
        strike = v[:, np.argmax(w)]
        normals[sid] = (-strike[1], strike[0])  # perpendicular to strike, as (ny, nx)
    ny_n = normals[ids, 0]
    nx_n = normals[ids, 1]
    off = (cy - sy) * ny_n + (cx - sx) * nx_n
    return off, dd
