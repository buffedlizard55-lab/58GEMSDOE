"""Build the combined multi-family / multi-scale ridge field (cached).

Output of :func:`build` is a dict of full-grid float32/int arrays:

``mag``   combined ridge magnitude, normalised so that 1.0 is the 99.9th
          percentile of the 8-neighbour non-maximum-suppressed response of the
          winning (band, scale) at that pixel;
``code``  int16 index into ``codes`` naming the winning (band, scale, family, sign);
``ax``/``ay``  unit across-strike vector at the winner.

The field is identical for every holdout fold: it is read only from the
organizer's geophysical stack, never from the catalogue, so withholding
catalogue segments cannot change it (asserted in ``tests/test_holdout.py``).
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from . import features as F
from . import grid
from .paths import cache_dir
from .ridges import SCALES, hessian_ridge, nonmax_suppress

CACHE_NAME = "ridge_field_v2.npz"
META_NAME = "ridge_field_v2.json"
NORM_QUANTILE = 0.999


def _jobs():
    usable = set(F.usable_bands())
    return [(b, s) for b in F.BANDS if b in usable for s in SCALES]


def _one(job):
    band, scale = job
    fp = grid.footprint()
    v = F.band(band)
    r = hessian_ridge(v, scale, fp)
    mag = r["magnitude"]
    nms = nonmax_suppress(mag, r["ax"], r["ay"], fp) & fp
    vals = mag[nms]
    q = float(np.quantile(vals, NORM_QUANTILE)) if vals.size else 0.0
    if not np.isfinite(q) or q <= 0.0:
        return None
    curv_mean = float(np.mean(r["curv"][nms])) if nms.any() else 0.0
    return dict(band=band, scale=float(scale), q=q,
                mag=(mag / q).astype(np.float32),
                nms=nms, ax=r["ax"], ay=r["ay"],
                sign=int(-1 if curv_mean < 0 else 1))


def build(force: bool = False, workers: int | None = None) -> dict:
    cd = cache_dir()
    npz, meta = cd / CACHE_NAME, cd / META_NAME
    if npz.exists() and meta.exists() and not force:
        z = np.load(npz)
        return dict(mag=z["mag"], code=z["code"], ax=z["ax"], ay=z["ay"],
                    codes=json.loads(meta.read_text())["codes"])

    jobs = _jobs()
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 1))
    shape = grid.footprint().shape
    mag = np.zeros(shape, np.float32)
    code = np.zeros(shape, np.int16)
    ax = np.zeros(shape, np.float32)
    ay = np.zeros(shape, np.float32)
    codes: list[dict] = []
    if workers == 1:
        results = map(_one, jobs)
    else:
        ex = ProcessPoolExecutor(max_workers=workers)
        results = ex.map(_one, jobs, chunksize=1)
    for res in results:
        if res is None:
            continue
        ncode = len(codes) + 1
        codes.append({k: res[k] for k in ("band", "scale", "sign", "q")})
        m = res["nms"] & (res["mag"] > mag)
        mag[m] = res["mag"][m]
        code[m] = ncode
        ax[m] = res["ax"][m]
        ay[m] = res["ay"][m]
    if workers != 1:
        ex.shutdown()
    np.savez_compressed(npz, mag=mag, code=code, ax=ax, ay=ay)
    meta.write_text(json.dumps(dict(codes=codes, scales=list(SCALES),
                                    normalise="mag / quantile(0.999 of NMS response)"),
                               indent=1))
    return dict(mag=mag, code=code, ax=ax, ay=ay, codes=codes)


def segments(field: dict, threshold: float, min_px: int = 6):
    """Connected ridge segments of the combined field above ``threshold``.

    Vectorised: one ``label`` pass, then an argsort grouping, so the cost is
    O(number of selected pixels) rather than O(components x grid).
    """
    from scipy.ndimage import label

    mask = field["mag"] >= threshold
    lab, n = label(mask, structure=np.ones((3, 3), int))
    if n == 0:
        return []
    sel = np.argwhere(lab > 0)
    if sel.size == 0:
        return []
    comp = lab[sel[:, 0], sel[:, 1]]
    order = np.argsort(comp, kind="stable")
    sel, comp = sel[order], comp[order]
    bounds = np.flatnonzero(np.diff(comp)) + 1
    starts = np.r_[0, bounds]
    ends = np.r_[bounds, comp.size]
    mags = field["mag"][sel[:, 0], sel[:, 1]]
    codes_grid = field["code"][sel[:, 0], sel[:, 1]]
    out = []
    for a, b in zip(starts, ends):
        if b - a < min_px:
            continue
        idx = sel[a:b]
        c = codes_grid[a:b]
        codes = [dict(field["codes"][k - 1]) for k in np.unique(c) if k > 0]
        out.append(dict(idx=idx, size=int(b - a), codes=codes,
                        mag=float(mags[a:b].mean())))
    return out
