"""Uniqueness / lane-drift check against every registry raster (protocol §1 and §2).

Registry = every GeoTIFF committed in the user's public GEMSDOE* repositories (buffedlizard55-lab).
A raster is flagged DUPLICATE if Spearman rank correlation with any registry raster > 0.90,
or if > 70% of its dots (value == 1) fall within 3 px of one registry raster's dots
(registry dots := value >= 0.5).
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

RHO_MAX = 0.90
# Competition-provided inputs are not earlier submissions; excluded and listed in the CSV.
COMPETITION_INPUTS = {"labels.tif", "existing_faults.tif", "sample_submission.tif",
                      "example_submission.tif", "gems-geodawn-numerical-features.tif"}
DOT_OVERLAP_MAX = 0.70
RADIUS = 3.0
DENSE_FRAC = 0.10  # registry 'dot' sets covering >10% of the footprint are treated as dense maps


def _dist_to(mask: np.ndarray) -> np.ndarray:
    return ndi.distance_transform_edt(~mask)


def compare(cand: np.ndarray, other: np.ndarray, valid: np.ndarray, rng, n_sample=100_000):
    both = valid & np.isfinite(cand) & np.isfinite(other)
    idx = np.flatnonzero(both)
    if idx.size == 0:
        return dict(rho=float("nan"), dot_overlap=float("nan"), n_cand_dots=0, n_reg_dots=0, dense_registry=False)
    take = idx if idx.size <= n_sample else rng.choice(idx, n_sample, replace=False)
    rho = float(spearmanr(cand.ravel()[take], other.ravel()[take]).correlation)
    cdots = (cand == 1.0) & both
    rdots = (other >= 0.5) & both
    dense = bool(rdots.sum() > DENSE_FRAC * both.sum())
    if cdots.sum() == 0 or rdots.sum() == 0:
        ov = 0.0
    elif dense:
        # Dense registry maps (e.g. probability surfaces where >=0.5 covers most of the footprint)
        # have no meaningful 'dots'; a 3-px test against them is trivially satisfied. Excluded here,
        # still tested by Spearman. Fix recorded in README (uniqueness tool, 2026-10-11).
        ov = float("nan")
    else:
        # exact nearest-registry-dot distance via KD-tree (same quantity as the EDT threshold)
        tree = cKDTree(np.argwhere(rdots))
        dist, _ = tree.query(np.argwhere(cdots), k=1)
        ov = float((dist <= RADIUS).mean())
    return dict(rho=rho, dot_overlap=ov, n_cand_dots=int(cdots.sum()), n_reg_dots=int(rdots.sum()), dense_registry=dense)


def run(cand_path, registry_dirs, valid, out_csv, label, seed=0):
    import rasterio
    rng = np.random.default_rng(seed)
    with rasterio.open(cand_path) as s:
        cand = s.read(1).astype(np.float32)
        shape = s.shape
    rows = []
    seen: dict[str, str] = {}  # sha256 -> first path; byte-identical copies are compared once
    for rd in registry_dirs:
        for tif in sorted(Path(rd).rglob("*.tif")):
            if ".git" in tif.parts:
                continue
            if tif.name in COMPETITION_INPUTS:
                rows.append(dict(registry_file=str(tif), excluded="competition-provided input, not a submission"))
                continue
            digest = hashlib.sha256(tif.read_bytes()).hexdigest()
            if digest in seen:
                rows.append(dict(registry_file=str(tif), excluded=f"byte-identical duplicate of {seen[digest]}"))
                continue
            seen[digest] = str(tif)
            try:
                with rasterio.open(tif) as r:
                    if r.shape != shape or r.count < 1:
                        continue
                    other = r.read(1).astype(np.float32)
            except Exception as e:  # unreadable registry file -> recorded, not silently skipped
                rows.append(dict(registry_file=str(tif), error=str(e)))
                continue
            res = compare(cand, other, valid, rng)
            res.update(registry_file=str(tif), label=label, sha256=digest)
            res["flag_rho"] = bool(res["rho"] > RHO_MAX) if np.isfinite(res["rho"]) else False
            res["flag_overlap"] = bool(np.isfinite(res["dot_overlap"]) and res["dot_overlap"] > DOT_OVERLAP_MAX)
            rows.append(res)
    keys = sorted({k for r in rows for k in r})
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    flagged = [r for r in rows if r.get("flag_rho") or r.get("flag_overlap")]
    ok_rows = [r for r in rows if "rho" in r]
    best = max(ok_rows, key=lambda r: r["rho"] if np.isfinite(r["rho"]) else -9.0) if ok_rows else None
    summary = dict(label=label, n_registry_compared=len(ok_rows), n_flagged=len(flagged),
                   max_rho=max((r["rho"] for r in ok_rows if np.isfinite(r["rho"])), default=float("nan")),
                   max_dot_overlap=max((r["dot_overlap"] for r in ok_rows if np.isfinite(r["dot_overlap"])), default=float("nan")),
                   n_dense_registry_excluded_from_overlap=sum(1 for r in ok_rows if r.get("dense_registry")),
                   argmax_rho_file=best["registry_file"] if best else None,
                   thresholds=dict(rho_max=RHO_MAX, dot_overlap_max=DOT_OVERLAP_MAX, radius_px=RADIUS),
                   verdict="DUPLICATE_OR_DRIFT" if flagged else "UNIQUE_PASS")
    return summary
