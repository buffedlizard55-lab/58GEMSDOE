"""Session-7 deep-structure step-edge surfaces (hypothesis H7-A) and relief field (H7-B).

The detector is a first-derivative **step-edge** transform on the organizer's own
subsurface and magnetic-structure bands of the pinned 19-band stack
(``training_features.tif``, sha256 pinned in ``data/bridge/feature_stack_pins.json``):

* ``depth_to_base_surf`` — "Depth to basement surface - thickness of sedimentary cover"
* ``cond_surf``          — "Conductivity surface - electrical conductivity of subsurface"
* ``tc``                 — "Tilt angle or total curvature - magnetic field derivative for edge detection"

(band descriptions read from the file itself; ``tc`` is tilt/total curvature, NOT a
source-depth estimate — see docs/IRREGULARITIES.md IR-58-S7-01.)

Transform, preregistered before any measurement:

1. sentinel / non-finite cells (the stack uses -3.4028235e38 nodata) are masked out;
2. robust normalisation per band: (x - median) / IQR over valid cells;
3. Gaussian smoothing at scale s in {1.5, 3.0} px;
4. gradient-magnitude edge response  |∇(G_s * x)|;
5. non-maximum suppression along the gradient azimuth (1 px), giving a 1-px
   step-edge centreline whose strength is the retained gradient magnitude.

A fault juxtaposing basin fill against basement is a *step* in these surfaces: the
first-derivative maximum sits on the structure face, whereas a Hessian ridge of the
raw surface (``gems58w.ridges``) peaks at the step corner, 1-2 px off.  The relief
field (H7-B) is the 21-px IQR of ``det_elev``; it is a conditioning variable for the
ribbon width only and never gates detection.

No catalogue input is read anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems58w.paths import feature_stack

CACHE = Path.home() / ".cache" / "gems" / "gems61_surfaces.npz"

#: (name, band index 1-based in the organizer stack, family label)
EDGE_BANDS: tuple[tuple[str, int, str], ...] = (
    ("depth_to_base_surf", 15, "subsurface"),
    ("cond_surf", 17, "subsurface"),
    ("tc", 6, "magnetic"),
)
SCALES: tuple[float, ...] = (1.5, 3.0)
RELIEF_WINDOW = 21
SENTINEL = -1e30
MIN_SEG_PX = 8


@dataclass
class Surfaces:
    """Edge-strength field, its provenance codes, and the relief context."""

    strength: np.ndarray            # float32, max edge response over bands x scales
    fam_ix: np.ndarray              # uint8 index into families (band that won)
    scale_ix: np.ndarray            # uint8 index into SCALES
    relief: np.ndarray              # float32, 21-px IQR of det_elev (px of elevation)
    relief_class: np.ndarray        # uint8 tercile over footprint 0/1/2
    families: tuple[str, ...] = tuple(f"{f}:{b}" for b, _i, f in
                                      [(n, i, f) for n, i, f in EDGE_BANDS])
    valid: np.ndarray = field(default=None)  # bool footprint of finite stack cells


def _read_band(index: int) -> tuple[np.ndarray, np.ndarray]:
    import rasterio

    with rasterio.open(feature_stack()) as src:
        a = src.read(index).astype(np.float32)
    valid = np.isfinite(a) & (a > SENTINEL)
    x = np.where(valid, a, np.nan)
    med = np.nanmedian(x)
    iqr = np.nanpercentile(x, 75) - np.nanpercentile(x, 25)
    if not np.isfinite(iqr) or iqr <= 0:
        iqr = float(np.nanstd(x)) or 1.0
    z = (x - med) / iqr
    return np.where(valid, z, 0.0).astype(np.float32), valid


def _edge_response(z: np.ndarray, valid: np.ndarray, scale: float) -> np.ndarray:
    g = ndi.gaussian_filter(z, scale, mode="nearest")
    gy, gx = np.gradient(g)
    mag = np.hypot(gx, gy)
    # non-maximum suppression along the gradient azimuth
    norm = np.maximum(mag, 1e-12)
    ay, ax = gy / norm, gx / norm
    h, w = mag.shape
    out = np.zeros_like(mag)
    # sample 1 px ahead and behind along the gradient, bilinear
    for sign in (1.0, -1.0):
        yy = np.clip(np.arange(h)[:, None] + sign * ay, 0, h - 1)
        xx = np.clip(np.arange(w)[None, :] + sign * ax, 0, w - 1)
        y0 = np.floor(yy).astype(np.int32)
        x0 = np.floor(xx).astype(np.int32)
        y1 = np.minimum(y0 + 1, h - 1)
        x1 = np.minimum(x0 + 1, w - 1)
        fy = yy - y0
        fx = xx - x0
        nb = (mag[y0, x0] * (1 - fy) * (1 - fx) + mag[y1, x0] * fy * (1 - fx)
              + mag[y0, x1] * (1 - fy) * fx + mag[y1, x1] * fy * fx)
        out = np.maximum(out, nb)
    keep = (mag >= out) & valid
    return np.where(keep, mag, 0.0).astype(np.float32)


def _relief_field() -> tuple[np.ndarray, np.ndarray]:
    import rasterio

    with rasterio.open(feature_stack()) as src:
        a = src.read(12).astype(np.float32)  # det_elev
    valid = np.isfinite(a) & (a > SENTINEL)
    x = np.where(valid, a, 0.0).astype(np.float32)
    win = RELIEF_WINDOW
    # IQR proxy: p75-p25 via two rank filters is costly; use local std of a
    # high-pass (det_elev minus its 21-px median) — documented in the run card.
    med = ndi.median_filter(x, size=win, mode="nearest")
    hp = x - med
    relief = ndi.uniform_filter(hp * hp, size=win, mode="nearest")
    relief = np.sqrt(np.maximum(relief, 0.0))
    return relief.astype(np.float32), valid


def build(force: bool = False) -> Surfaces:
    if CACHE.exists() and not force:
        d = np.load(CACHE)
        return Surfaces(strength=d["strength"], fam_ix=d["fam_ix"],
                        scale_ix=d["scale_ix"], relief=d["relief"],
                        relief_class=d["relief_class"], valid=d["valid"])
    # one pass: keep the per-pixel winning (band, scale) edge response
    best = np.zeros((3730, 3292), np.float32)
    fam_ix = np.zeros(best.shape, np.int8)
    scale_ix = np.zeros(best.shape, np.int8)
    valid = None
    for bi, (_name, index, _fam) in enumerate(EDGE_BANDS):
        z, v = _read_band(index)
        valid = v if valid is None else (valid & v)
        for si, s in enumerate(SCALES):
            r = _edge_response(z, v, s)
            upd = r > best
            best = np.where(upd, r, best)
            fam_ix = np.where(upd, bi, fam_ix).astype(np.int8)
            scale_ix = np.where(upd, si, scale_ix).astype(np.int8)
    strength = best
    relief, rvalid = _relief_field()
    valid = valid & rvalid
    relief = np.where(valid, relief, 0.0).astype(np.float32)
    # terciles over footprint cells with any edge context: use all valid cells
    q1, q2 = np.quantile(relief[valid], [1 / 3, 2 / 3])
    relief_class = np.where(relief >= q2, 2, np.where(relief >= q1, 1, 0)).astype(np.uint8)
    np.savez_compressed(CACHE, strength=strength, fam_ix=fam_ix, scale_ix=scale_ix,
                        relief=relief, relief_class=relief_class, valid=valid)
    return Surfaces(strength=strength, fam_ix=fam_ix, scale_ix=scale_ix,
                    relief=relief, relief_class=relief_class, valid=valid)


@dataclass
class Segment:
    idx: np.ndarray          # (n, 2) pixel coords
    size: int
    family: str
    band: str
    scale: float
    strength: float          # mean edge strength over the segment
    relief_class: int        # modal relief class of the segment
    centroid: tuple[float, float]


def segments(surf: Surfaces, min_px: int = MIN_SEG_PX,
             keep: np.ndarray | None = None) -> list[Segment]:
    """8-connected step-edge segments above zero strength.

    ``keep`` optionally restricts support (e.g. the scored domain of a fold).
    """
    mask = (surf.strength > 0) if keep is None else ((surf.strength > 0) & keep)
    lab, n = ndi.label(mask, structure=np.ones((3, 3), int))
    if n == 0:
        return []
    objs = ndi.find_objects(lab)
    out: list[Segment] = []
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        sub = lab[sl] == i
        size = int(sub.sum())
        if size < min_px:
            continue
        ys, xs = np.nonzero(sub)
        ys = ys + sl[0].start
        xs = xs + sl[1].start
        idx = np.stack([ys, xs], axis=1)
        st = float(surf.strength[ys, xs].mean())
        fams, cnts = np.unique(surf.fam_ix[ys, xs], return_counts=True)
        fi = int(fams[cnts.argmax()])
        scales, scnts = np.unique(surf.scale_ix[ys, xs], return_counts=True)
        si = int(scales[scnts.argmax()])
        rcls, rcnts = np.unique(surf.relief_class[ys, xs], return_counts=True)
        out.append(Segment(idx=idx, size=size,
                           family=EDGE_BANDS[fi][2], band=EDGE_BANDS[fi][0],
                           scale=float(SCALES[si]), strength=st,
                           relief_class=int(rcls[rcnts.argmax()]),
                           centroid=(float(ys.mean()), float(xs.mean()))))
    return out
