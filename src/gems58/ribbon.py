"""Ribbon-lane method: ridge candidates -> per-class localisation sigma -> dotted/ribbon emission.

Lane (from the session prompt, "Ribbon lane"): match emission width to the measured localisation
error; use one tight line where sigma < 0.5 px, a ribbon of about +/-sigma where sigma is 2-3 px,
and parallel dotted lines (spacing ~ 3 px kernel radius) where location is uncertain; choose the
number/offset of lines by maximising U = (1 - a*DTI0) TP - a*DTI0 FP; emit included dots at 1.0.

Everything in this module uses ONLY geophysical layers from the official feature stack. No
catalogue (label) information enters a candidate, a sigma, or an emission parameter, except:
  (a) the withheld truth of the held-out block, which defines sigma/score for that block, and
  (b) the visible catalogue, which is masked from scoring (organizer rule).
Selection for held-out block b uses only blocks != b (leave-one-block-out, nested).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .metric import ALPHA, BETA, EPS, RADIUS_PX, _OFFS, kernel, truth_weight_map, utility_U

# ridge type -> official feature band (names from the GeoTIFF band descriptions)
RIDGE_TYPES = {"mag": "tmi_hg", "grav": "iso_grav_anom_hg", "topo": "det_elev_slope"}
# feature resolution -> Hessian scale in px (1 px = 100 m)
RESOLUTIONS = {"fine100m": 1.0, "coarse200m": 2.0}
FRACS = (0.002, 0.005, 0.01)  # fraction of footprint px kept as ridge candidates (top quantile)
MIN_COMPONENT_PX = 12
DOT_SPACING_PX = 3.0
CONFIGS = ["L1", "R1", "R2", "R3"] + [f"D{n}o{o:+d}" for n in (1, 2, 3) for o in (-1, 0, 1)]


def band_index(descriptions, name):
    for i, d in enumerate(descriptions, start=1):
        if d and d.split(" - ")[0].strip() == name:
            return i
    raise KeyError(name)


def ridge_field(z: np.ndarray, valid: np.ndarray, scale: float):
    """Bright-ridge strength, unit normal and NMS mask from Hessian eigen-analysis.

    z must be finite inside `valid` (zeros elsewhere). Returns (strength, nx, ny, nms_keep).
    Coordinates: arrays are [row=y, col=x]; normal (nx, ny) is in (col, row) order.
    """
    z = z.astype(np.float32)
    Hyy = ndi.gaussian_filter(z, scale, order=(2, 0), mode="nearest")
    Hxx = ndi.gaussian_filter(z, scale, order=(0, 2), mode="nearest")
    Hxy = ndi.gaussian_filter(z, scale, order=(1, 1), mode="nearest")
    tr = 0.5 * (Hxx + Hyy)
    disc = np.sqrt((0.5 * (Hxx - Hyy)) ** 2 + Hxy ** 2)
    lam = tr - disc  # most negative eigenvalue -> bright ridge across-direction
    strength = (np.maximum(-lam, 0.0) * scale ** 2).astype(np.float32)
    strength[~valid] = 0.0
    vx = Hxy.astype(np.float32)
    vy = (lam - Hxx).astype(np.float32)
    nrm = np.hypot(vx, vy)
    bad = nrm < 1e-9
    vx = np.where(bad, 1.0, vx / np.maximum(nrm, 1e-9)).astype(np.float32)
    vy = np.where(bad, 0.0, vy / np.maximum(nrm, 1e-9)).astype(np.float32)
    # non-maximum suppression across the ridge (bilinear sampling of strength at +/- normal)
    ys, xs = np.nonzero(valid & (strength > 0))
    sp = ndi.map_coordinates(strength, [ys + vy[ys, xs], xs + vx[ys, xs]], order=1, mode="nearest")
    sm = ndi.map_coordinates(strength, [ys - vy[ys, xs], xs - vx[ys, xs]], order=1, mode="nearest")
    keep = np.zeros(valid.shape, bool)
    keep[ys, xs] = (strength[ys, xs] >= sp) & (strength[ys, xs] >= sm)
    return strength, vx, vy, keep


def candidates_for(strength, vx, vy, keep, valid, frac):
    """Thin, thresholded ridge candidates. Returns dict of sparse arrays."""
    thr = np.quantile(strength[valid], 1.0 - frac)
    m = keep & (strength >= thr) & (strength > 0) & valid
    lab, n = ndi.label(m, structure=np.ones((3, 3), int))
    if n:
        sizes = ndi.sum(m, lab, index=np.arange(1, n + 1))
        good = np.zeros(n + 1, bool)
        good[1:] = sizes >= MIN_COMPONENT_PX
        m = good[lab]
        lab, n = ndi.label(m, structure=np.ones((3, 3), int))
    ys, xs = np.nonzero(m)
    return dict(ys=ys, xs=xs, nx=vx[ys, xs], ny=vy[ys, xs], comp=lab[ys, xs], n_comp=int(n))


def _positions(cand, config: str):
    """Pixel positions (rows, cols) emitted for one candidate set under one configuration."""
    ys, xs, nx, ny, comp = cand["ys"], cand["xs"], cand["nx"], cand["ny"], cand["comp"]
    if config == "L1":
        return ys, xs
    if config.startswith("R"):
        w = int(config[1:])
        rr, cc = [], []
        for o in range(-w, w + 1):
            rr.append(np.round(ys + o * ny))
            cc.append(np.round(xs + o * nx))
        return np.concatenate(rr).astype(int), np.concatenate(cc).astype(int)
    # dotted: D{n}o{offset}
    n = int(config[1])
    off_shift = int(config.split("o")[1])
    # decimate the skeleton to one point per DOT_SPACING_PX along the tangent, per component
    tx, ty = -ny, nx
    u = tx * xs + ty * ys
    bins = np.floor(u / DOT_SPACING_PX).astype(np.int64)
    key = np.stack([comp.astype(np.int64), bins], axis=1)
    _, first = np.unique(key, axis=0, return_index=True)
    ys, xs, nx, ny = ys[first], xs[first], nx[first], ny[first]
    rr, cc = [], []
    for i in range(n):
        off = (i - (n - 1) / 2.0) * DOT_SPACING_PX + off_shift
        rr.append(np.round(ys + off * ny))
        cc.append(np.round(xs + off * nx))
    return np.concatenate(rr).astype(int), np.concatenate(cc).astype(int)


def emission_mask(cand, config: str, shape, valid):
    rows, cols = _positions(cand, config)
    m = np.zeros(shape, bool)
    ok = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    m[rows[ok], cols[ok]] = True
    return m & valid


def tp_credit(p_bool: np.ndarray, gy: np.ndarray, gx: np.ndarray) -> float:
    """sum_g max_x p(x) k(d(x,g)) for binary p (exact metric TP term)."""
    H, W = p_bool.shape
    credit = np.zeros(gy.size)
    pf = p_bool.astype(np.float64)
    for dy, dx, k in _OFFS:
        ny_, nx_ = gy + dy, gx + dx
        ok = (ny_ >= 0) & (ny_ < H) & (nx_ >= 0) & (nx_ < W)
        credit[ok] = np.maximum(credit[ok], pf[ny_[ok], nx_[ok]] * k)
    return float(credit.sum())


def robust_sigma(d: np.ndarray) -> float:
    """1.4826 * MAD of matched localisation distances (px)."""
    if d.size < 5:
        return float("nan")
    med = np.median(d)
    return float(1.4826 * np.median(np.abs(d - med)))


def sigma_rule(sigma: float, config: str) -> bool:
    """Lane rule: sigma < 0.5 -> single tight line; sigma in [2,3] -> ribbon +/-round(sigma);
    otherwise every configuration is admissible and U decides."""
    if not np.isfinite(sigma):
        return True
    if sigma < 0.5:
        return config == "L1"
    if 2.0 <= sigma <= 3.0:
        return config == f"R{int(round(sigma))}"
    return True
