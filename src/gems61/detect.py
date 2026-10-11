"""Combined ridge field over the extended evidence set.

Reuses ``gems58w.ridges`` (Hessian line response, non-maximum suppression,
across-strike unit vector) unchanged; this module only *drives* it over the
extended band list from :mod:`gems61.layers` and stores the winning
(band, scale) code per pixel.

Per pixel the stored fields are

* ``mag``  -- ridge magnitude of the winning (band, scale), normalised by that
  band/scale's own 0.999 quantile of NMS responses (so bands with different
  units are comparable);
* ``code`` -- 1-based index into ``codes`` (band, family, scale, sign);
* ``ax``/``ay`` -- across-strike unit vector of the winning response.

The field is cacheable (``.cache/…`` outside git) because it costs ~80 Hessian
passes over a 12.3 M-pixel grid.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from gems58w.paths import cache_dir
from gems58w.ridges import hessian_ridge, nonmax_suppress

from . import layers

CACHE_NAME = "ridge_field_ext_v1.npz"
META_NAME = "ridge_field_ext_v1.json"
NORM_QUANTILE = 0.999


def jobs() -> list[tuple[str, float]]:
    out = []
    for b in layers.EXT_BANDS:
        scales = layers.SCALES_EXT if b in layers.MIRROR_BANDS or b == "dem100" else layers.SCALES_O19
        for s in scales:
            out.append((b, float(s)))
    return out


def _one(job: tuple[str, float]) -> dict | None:
    band, scale = job
    fp = layers._footprint()
    v = layers.band(band)
    r = hessian_ridge(v, scale, fp)
    mag = r["magnitude"]
    nms = nonmax_suppress(mag, r["ax"], r["ay"], fp) & fp
    vals = mag[nms]
    if vals.size == 0:
        return None
    q = float(np.quantile(vals, NORM_QUANTILE))
    if not np.isfinite(q) or q <= 0.0:
        return None
    curv_mean = float(np.mean(r["curv"][nms]))
    return dict(band=band, family=layers.family_of(band), scale=float(scale),
                sign=int(-1 if curv_mean < 0 else 1), q=q,
                mag=(mag / q).astype(np.float32), nms=nms,
                ax=r["ax"], ay=r["ay"])


def build(force: bool = False, workers: int | None = None) -> dict:
    cd = cache_dir()
    npz, meta = cd / CACHE_NAME, cd / META_NAME
    if npz.exists() and meta.exists() and not force:
        z = np.load(npz)
        return dict(mag=z["mag"], code=z["code"], ax=z["ax"], ay=z["ay"],
                    codes=json.loads(meta.read_text())["codes"],
                    cache=str(npz), cached=True)

    js = jobs()
    workers = workers or 1
    shape = layers._footprint().shape
    mag = np.zeros(shape, np.float32)
    code = np.zeros(shape, np.int16)
    ax = np.zeros(shape, np.float32)
    ay = np.zeros(shape, np.float32)
    codes: list[dict] = []
    it = map(_one, js) if workers == 1 else ProcessPoolExecutor(max_workers=workers).map(_one, js, chunksize=1)
    for res in it:
        if res is None:
            continue
        codes.append({k: res[k] for k in ("band", "family", "scale", "sign", "q")})
        n = len(codes)
        m = res["nms"] & (res["mag"] > mag)
        mag[m] = res["mag"][m]
        code[m] = n
        ax[m] = res["ax"][m]
        ay[m] = res["ay"][m]
    np.savez_compressed(npz, mag=mag, code=code, ax=ax, ay=ay)
    meta.write_text(json.dumps(dict(
        codes=codes, n_bands=len(layers.EXT_BANDS), n_jobs=len(js),
        normalise="mag / quantile(0.999 of that band/scale NMS response)",
        scales_organizer=list(layers.SCALES_O19), scales_extended=list(layers.SCALES_EXT),
        families={k: list(v) for k, v in layers.EXT_FAMILIES.items()},
    ), indent=1))
    return dict(mag=mag, code=code, ax=ax, ay=ay, codes=codes, cache=str(npz), cached=False)


def class_mask(field: dict, *, family: str | None = None, scale: float | None = None,
               sign: int | None = None, threshold: float = 0.0) -> np.ndarray:
    """Boolean mask of ridge pixels of one class at or above ``threshold``."""
    sel = np.zeros(len(field["codes"]) + 1, bool)
    for i, c in enumerate(field["codes"], start=1):
        if family is not None and c["family"] != family:
            continue
        if scale is not None and abs(c["scale"] - scale) > 1e-9:
            continue
        if sign is not None and c["sign"] != sign:
            continue
        sel[i] = True
    return sel[field["code"]] & (field["mag"] >= threshold)


def family_thresholds(field: dict, q: float, footprint_mask: np.ndarray | None = None) -> dict:
    """Per-family magnitude threshold keeping the top ``q`` fraction of the footprint.

    The stored field is winner-take-all, so a single global threshold lets the
    families with the largest absolute responses (radiometric, lidar) crowd out
    magnetics and gravity.  A per-family quantile rebalances the ridge set
    without touching the detector or the metric: within each family, pixels are
    still ranked by that family's own winning normalised magnitude.
    """
    fp = layers._footprint() if footprint_mask is None else footprint_mask
    mag, code = field["mag"], field["code"]
    fam_of_code = {i: c["family"] for i, c in enumerate(field["codes"], start=1)}
    out = {}
    for fam in sorted(set(fam_of_code.values())):
        ids = [i for i, f in fam_of_code.items() if f == fam]
        if not ids:
            continue
        sel = fp & np.isin(code, ids)
        vals = mag[sel]
        out[fam] = (float(np.quantile(vals, 1.0 - q)) if vals.size else float("inf"), int(vals.size))
    return out


def classes(field: dict) -> list[dict]:
    """Enumerate the (family, scale, sign) classes present in the field."""
    seen, out = set(), []
    for c in field["codes"]:
        key = (c["family"], c["scale"], c["sign"])
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(family=key[0], scale=key[1], sign=key[2]))
    return sorted(out, key=lambda d: (d["family"], d["scale"], d["sign"]))
