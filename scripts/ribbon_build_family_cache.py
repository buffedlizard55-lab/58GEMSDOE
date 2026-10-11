#!/usr/bin/env python3
"""Per-family NMS ridge maxima for the H58-X1 cross-family concordance gate.

Reuses the shared operators (``gems58w.ridges.hessian_ridge`` /
``nonmax_suppress``) and the shared per-(band, scale) normalisation rule of
``gems58w.extract`` (99.9th percentile of the NMS response), so the family
grids are measured in exactly the units of the incumbent combined field.
Output: ``.cache/gems58/family_ridge_v1.npz`` holding, for each organizer
family, the max over (band in family, scale) of the normalised NMS ridge
magnitude.  Catalogue-free by construction: only the sha256-pinned 19-band
stack is read, so the grids are identical in every holdout fold.

    PYTHONPATH=src GEMS_FEATURE_STACK=~/.cache/gems/training_features.tif \
        python3 scripts/ribbon_build_family_cache.py
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import features as F  # noqa: E402
from gems58w import grid  # noqa: E402
from gems58w.paths import cache_dir  # noqa: E402
from gems58w.ridges import SCALES, hessian_ridge, nonmax_suppress  # noqa: E402

CACHE_NAME = "family_ridge_v1.npz"
META_NAME = "family_ridge_v1.json"
NORM_QUANTILE = 0.999  # identical to gems58w.extract.NORM_QUANTILE


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
    out = np.zeros(mag.shape, np.float32)
    out[nms] = (mag[nms] / q).astype(np.float32)
    return band, float(scale), out


def build(force: bool = False, workers: int = 2) -> dict:
    cd = cache_dir()
    npz, meta = cd / CACHE_NAME, cd / META_NAME
    if npz.exists() and meta.exists() and not force:
        z = np.load(npz)
        return {k: z[k] for k in z.files}
    usable = set(F.usable_bands())
    jobs = [(b, s) for b in F.BANDS if b in usable for s in SCALES]
    fam_of = {b: next((k for k, v in F.FAMILIES.items() if b in v), "other")
              for b in F.BANDS}
    shape = grid.footprint().shape
    fams: dict[str, np.ndarray] = {}
    used: dict[str, list] = {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_one, jobs, chunksize=1):
            if res is None:
                continue
            band, scale, g = res
            fam = fam_of[band]
            if fam not in fams:
                fams[fam] = np.zeros(shape, np.float32)
            np.maximum(fams[fam], g, out=fams[fam])
            used.setdefault(fam, []).append([band, scale])
            print(f"[family] {band}@{scale} -> {fam} "
                  f"({time.time()-t0:.0f}s)", flush=True)
    np.savez_compressed(npz, **fams)
    meta.write_text(json.dumps(dict(
        families=sorted(fams), jobs_per_family=used,
        normalise="per-(band,scale) NMS response / its 99.9th percentile, as gems58w.extract",
        catalogue_free=True, wall_seconds=round(time.time() - t0, 1)), indent=1))
    print(f"[family] wrote {npz} families={sorted(fams)} wall={time.time()-t0:.1f}s",
          flush=True)
    return fams


if __name__ == "__main__":
    build(force="--force" in sys.argv)
