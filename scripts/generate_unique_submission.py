#!/usr/bin/env python3
"""Generate a unique structural-gradient submission for the DOE GEMS Prize Challenge.

Strategy: Multi-scale structural indicator from the19-band GeoDAWN feature stack,
computed in a memory-efficient band-by-band manner.  This produces a CONTINUOUS
probability field (not a dotted/ribbon pattern) — fundamentally different from
every earlier submission in this repository.

The metric DTI(alpha=0.2, beta=0.8) rewards coverage 4x more than it punishes
false positives.  A broad continuous probability map maximises TP_w by covering
structural lineaments that correspond to BOTH mapped AND unmapped faults.

Output: all-finite float32 GeoTIFF, EPSG:32611, 3730x3292, 100 m.
Values in [0, 1] everywhere (zero outside the footprint).
"""
from __future__ import annotations

import hashlib
import os
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

SENTINEL = -1e30
HEIGHT, WIDTH = 3730, 3292


def load_footprint(path: str = None) -> np.ndarray:
    path = path or os.path.join(REPO, "data", "bridge", "sample_submission.tif")
    with rasterio.open(path) as src:
        return np.isfinite(src.read(1))


def load_catalogue(path: str = None) -> np.ndarray:
    path = path or os.path.join(REPO, "data", "bridge", "existing_faults.tif")
    with rasterio.open(path) as src:
        cat = src.read(1)
    fp = load_footprint()
    return (cat > 0) & fp


def load_band(stack_path: str, band_idx: int, fp: np.ndarray) -> np.ndarray:
    """Load one band, replace sentinels with 0, zero outside footprint."""
    with rasterio.open(stack_path) as src:
        b = src.read(band_idx).astype(np.float32)
    b[b < SENTINEL] = 0.0
    b[~fp] = 0.0
    b = np.nan_to_num(b, nan=0.0, posinf=0.0, neginf=0.0)
    return b


def gradient_magnitude(band: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    smoothed = gaussian_filter(band, sigma=sigma)
    gx = ndi.sobel(smoothed, axis=1)
    gy = ndi.sobel(smoothed, axis=0)
    return np.sqrt(gx**2 + gy**2)


def normalise_zscore(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Z-score within footprint, clip to [-3, 3], map to [0, 1]."""
    vals = arr[fp]
    mu, sigma = float(np.mean(vals)), float(np.std(vals))
    if sigma < 1e-10:
        return np.full_like(arr, 0.5)
    z = (arr - mu) / sigma
    return np.clip(z, -3, 3) / 6.0 + 0.5


def main():
    t0 = time.time()
    stack_path = os.path.expanduser("~/.cache/gems/training_features.tif")

    fp = load_footprint()
    cat = load_catalogue()
    print(f"Footprint: {fp.sum()} px | Catalogue: {cat.sum()} px")

    # ---- Band-to-family mapping (0-indexed internally, 1-indexed for rasterio) ----
    # Band mapping (verified from competition page 967):
    # 1: surface conductivity    2: depth to conductive base
    # 3: detrended elevation     4: slope of detrended elevation
    # 5: dilatation rate         6: shear strain rate
    # 7: 2nd invariant strain    8: isostatic gravity anomaly
    # 9: slope gravity anomaly  10: RTP magnetic anomaly
    # 11: TMI                   12: vertical slope TMI
    # 13: horizontal slope TMI  14: top-of-crustal mag depth
    # 15: earthquake density    16-19: additional layers

    # 6 independent geophysical families
    families = {
        "magnetics":   [10, 11, 12, 13, 14],
        "gravity":     [8, 9],
        "conductivity": [1, 2],
        "topography":  [3, 4],
        "strain":      [5, 6, 7],
        "seismicity":  [15],
    }
    # Also include extra bands 16-19
    extra_bands = [16, 17, 18, 19]

    # ---- Compute family gradient scores ----
    family_scores = {}
    family_discrimination = {}

    for fam_name, band_ids in families.items():
        score = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for rid in band_ids:
            b = load_band(stack_path, rid, fp)
            for sigma in [1.0, 2.0, 3.0]:
                g = gradient_magnitude(b, sigma=sigma)
                g = normalise_zscore(g, fp)
                score += g
        score /= len(band_ids) * 3  # average over bands x scales
        family_scores[fam_name] = score

        at_f = float(score[cat].mean()) if cat.any() else 0
        away_f = float(score[fp & ~cat].mean())
        disc = max(at_f - away_f, 0.0001)
        family_discrimination[fam_name] = disc
        print(f"  {fam_name:14s}: at_fault={at_f:.4f} away={away_f:.4f} disc={disc:.4f}")

    # ---- Extra bands gradient ----
    extra_score = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    for rid in extra_bands:
        b = load_band(stack_path, rid, fp)
        for sigma in [1.5, 3.0]:
            g = gradient_magnitude(b, sigma=sigma)
            g = normalise_zscore(g, fp)
            extra_score += g
    extra_score /= len(extra_bands) * 2
    family_scores["extra_bands"] = extra_score
    at_f = float(extra_score[cat].mean()) if cat.any() else 0
    away_f = float(extra_score[fp & ~cat].mean())
    family_discrimination["extra_bands"] = max(at_f - away_f, 0.0001)
    print(f"  extra_bands   : at_fault={at_f:.4f} away={away_f:.4f} disc={family_discrimination['extra_bands']:.4f}")

    # ---- Cross-band coherence ----
    print("Computing cross-band coherence...")
    key_bands = [10, 8, 1, 3, 5, 15]  # one representative from each family
    coherence = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    for sigma in [1.5, 3.0]:
        directions = []
        for rid in key_bands:
            b = load_band(stack_path, rid, fp)
            sm = gaussian_filter(b, sigma=sigma)
            gx = ndi.sobel(sm, axis=1)
            gy = ndi.sobel(sm, axis=0)
            directions.append(np.arctan2(gy, gx))
        sin_s = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        cos_s = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for d in directions:
            sin_s += np.sin(2 * d)
            cos_s += np.cos(2 * d)
        coherence += np.sqrt(sin_s**2 + cos_s**2) / len(directions)
    coherence /= 2
    coherence = normalise_zscore(coherence, fp)
    family_scores["coherence"] = coherence
    at_c = float(coherence[cat].mean()) if cat.any() else 0
    away_c = float(coherence[fp & ~cat].mean())
    family_discrimination["coherence"] = max(at_c - away_c, 0.0001)
    print(f"  coherence     : at_fault={at_c:.4f} away={away_c:.4f} disc={family_discrimination['coherence']:.4f}")

    # ---- Weighted combination ----
    print("Combining family scores...")
    total_weight = sum(family_discrimination.values())
    composite = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    for name, score in family_scores.items():
        w = family_discrimination[name] / total_weight
        composite += score * w
        print(f"  {name:14s}: weight={w:.4f}")

    # ---- Non-linear enhancement ----
    print("Non-linear mapping...")
    vals = composite[fp]
    p25, p50, p75, p90 = [float(np.percentile(vals, p)) for p in [25, 50, 75, 90]]
    print(f"  percentiles: p25={p25:.4f} p50={p50:.4f} p75={p75:.4f} p90={p90:.4f}")

    # Sigmoid mapping — spreads probability mass more aggressively
    center = p50
    scale = (p75 - p25) + 1e-10
    prob = 1.0 / (1.0 + np.exp(-(composite - center) / (scale * 0.25)))

    # ---- Proximity boost near known faults ----
    print("Proximity boost...")
    cat_dil3 = ndi.binary_dilation(cat, iterations=3)   # 300m
    cat_dil8 = ndi.binary_dilation(cat, iterations=8)   # 800m
    cat_annulus = cat_dil8 & ~cat_dil3

    prob = np.where(cat_dil3, np.minimum(prob * 1.4, 1.0), prob)
    prob = np.where(cat_annulus, np.minimum(prob * 1.2, 1.0), prob)

    # ---- Topographic curvature boost ----
    # Faults often appear as ridges in detrended elevation
    print("Topographic ridge boost...")
    topo_band = load_band(stack_path, 3, fp)
    topo_smooth = gaussian_filter(topo_band, sigma=2.0)
    # Laplacian-of-Gaussian — positive LoG = local maxima (ridge)
    log = gaussian_filter(topo_smooth, sigma=1.5) - gaussian_filter(topo_smooth, sigma=3.0)
    log_z = normalise_zscore(log, fp)
    # Only boost where LoG is positive (ridges, not valleys)
    ridge_boost = np.where(log_z > 0.6, log_z, 0.0) * 0.3
    prob = np.minimum(prob + ridge_boost, 1.0)

    # ---- Final clipping and masking ----
    prob = np.clip(prob, 0.0, 1.0).astype(np.float32)
    prob[~fp] = 0.0
    assert prob.min() >= 0.0
    assert prob.max() <= 1.0
    assert np.isfinite(prob).all()

    pf = prob[fp]
    print(f"\nFinal stats (in footprint):")
    print(f"  min={pf.min():.6f} max={pf.max():.6f} mean={pf.mean():.6f}")
    print(f"  >0.1: {(pf > 0.1).sum()} >0.3: {(pf > 0.3).sum()} >0.5: {(pf > 0.5).sum()}")
    print(f"  at faults: {float(prob[cat].mean()):.6f}")
    print(f"  away from faults: {float(prob[fp & ~cat].mean()):.6f}")

    # ---- Write GeoTIFF ----
    out_dir = os.path.join(REPO, "docs", "downloads")
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir,
        "gems58-structural-gradient-20261011T193000Z.tif")

    from gems57.grid import write_geotiff
    result = write_geotiff(output_path, prob)
    print(f"\nWritten: {result['path']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Size: {os.path.getsize(output_path)} bytes")

    # ---- Create ZIP ----
    import zipfile
    zip_path = output_path.replace('.tif', '.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(output_path, os.path.basename(output_path))
    print(f"ZIP: {zip_path}")

    print(f"\nTotal time: {time.time()-t0:.1f}s")
    print("\n=== DONE — Unique continuous probability submission ready ===")


if __name__ == "__main__":
    main()