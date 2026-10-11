#!/usr/bin/env python3
"""Generate a unique ML-based submission.  Two-pass approach:
  Pass 1: compute and cache feature maps to disk (one band at a time)
  Pass 2: train on sampled pixels, predict from cached maps
"""
from __future__ import annotations
import gc, hashlib, json, os, sys, time, tempfile
import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter, uniform_filter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

SENTINEL = -1e30
HEIGHT, WIDTH = 3730, 3292
STACK = os.path.expanduser("~/.cache/gems/training_features.tif")
SAMPLE_TIF = os.path.join(REPO, "data", "bridge", "sample_submission.tif")
CAT_TIF = os.path.join(REPO, "data", "bridge", "existing_faults.tif")
CACHE_DIR = "/tmp/gems_feat_cache"


def load_band(idx, fp):
    with rasterio.open(STACK) as src:
        b = src.read(idx).astype(np.float32)
    b[b < SENTINEL] = 0.0
    b[~fp] = 0.0
    return np.nan_to_num(b, nan=0.0, posinf=0.0, neginf=0.0)


def gradient_mag(band, sigma=1.0):
    sm = gaussian_filter(band, sigma=sigma)
    gx = ndi.sobel(sm, axis=1)
    gy = ndi.sobel(sm, axis=0)
    return np.sqrt(gx**2 + gy**2).astype(np.float32)


def zscore_map(arr, fp):
    v = arr[fp]
    mu, sig = float(np.mean(v)), float(np.std(v))
    if sig > 1e-10:
        return np.clip((arr - mu) / sig, -3, 3).astype(np.float32)
    return np.zeros_like(arr, dtype=np.float32)


def save_feature(path, arr):
    np.save(path, arr.astype(np.float32))


def load_feature(path):
    return np.load(path + ".npy", mmap_mode='r')


def main():
    t0 = time.time()

    with rasterio.open(SAMPLE_TIF) as src:
        fp = np.isfinite(src.read(1))
    with rasterio.open(CAT_TIF) as src:
        cat = (src.read(1) > 0) & fp
    print(f"Footprint: {fp.sum()} | Catalogue: {cat.sum()}")

    os.makedirs(CACHE_DIR, exist_ok=True)

    # ---- Pass 1: Compute and cache feature maps ----
    print("=" * 60)
    print("PASS 1: Computing and caching feature maps...")
    print("=" * 60)

    feat_paths = []
    feat_names = []

    for bidx in range(1, 20):
        band = load_band(bidx, fp)

        # Raw z-scored
        p = os.path.join(CACHE_DIR, f"b{bidx:02d}_raw")
        save_feature(p, zscore_map(band, fp))
        feat_paths.append(p)
        feat_names.append(f"b{bidx:02d}_raw")

        # Gradient sigma=1
        g1 = gradient_mag(band, sigma=1.0)
        p = os.path.join(CACHE_DIR, f"b{bidx:02d}_g1")
        save_feature(p, zscore_map(g1, fp))
        feat_paths.append(p)
        feat_names.append(f"b{bidx:02d}_g1")
        del g1

        # Gradient sigma=3
        g3 = gradient_mag(band, sigma=3.0)
        p = os.path.join(CACHE_DIR, f"b{bidx:02d}_g3")
        save_feature(p, zscore_map(g3, fp))
        feat_paths.append(p)
        feat_names.append(f"b{bidx:02d}_g3")
        del g3

        # Local mean (5x5)
        lm = uniform_filter(band, size=5, mode='constant')
        p = os.path.join(CACHE_DIR, f"b{bidx:02d}_lm")
        save_feature(p, zscore_map(lm, fp))
        feat_paths.append(p)
        feat_names.append(f"b{bidx:02d}_lm")
        del lm, band

        if bidx % 5 == 0:
            gc.collect()
            print(f"  Bands 1-{bidx} done ({len(feat_names)} features)")

    # Coherence (gradient direction agreement)
    print("  Computing cross-band coherence...")
    key_bands = [10, 8, 1, 3, 5, 15]
    for sigma in [1.5, 3.0]:
        dirs = []
        for rid in key_bands:
            b = load_band(rid, fp)
            sm = gaussian_filter(b, sigma=sigma)
            gx = ndi.sobel(sm, axis=1)
            gy = ndi.sobel(sm, axis=0)
            dirs.append(np.arctan2(gy, gx).astype(np.float32))
            del b, sm, gx, gy
        sin_s = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        cos_s = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for d in dirs:
            sin_s += np.sin(2 * d)
            cos_s += np.cos(2 * d)
        coh = np.sqrt(sin_s**2 + cos_s**2) / len(dirs)
        del sin_s, cos_s, dirs
        p = os.path.join(CACHE_DIR, f"coh_s{int(sigma)}")
        save_feature(p, zscore_map(coh, fp))
        feat_paths.append(p)
        feat_names.append(f"coh_s{int(sigma)}")
        del coh

    # Family gradients (mag, grav, cond, topo, strain)
    families = [
        ("mag", [10, 11, 12, 13, 14]),
        ("grav", [8, 9]),
        ("cond", [1, 2]),
        ("topo", [3, 4]),
        ("strain", [5, 6, 7]),
    ]
    for fam_name, band_ids in families:
        fam = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for rid in band_ids:
            b = load_band(rid, fp)
            g = gradient_mag(b, sigma=2.0)
            fam += zscore_map(g, fp)
            del b, g
        fam /= len(band_ids)
        p = os.path.join(CACHE_DIR, f"fam_{fam_name}")
        save_feature(p, fam)
        feat_paths.append(p)
        feat_names.append(f"fam_{fam_name}")
        del fam
        gc.collect()

    n_feats = len(feat_names)
    print(f"Total cached features: {n_feats}")

    # ---- Pass 2a: Train ----
    print("=" * 60)
    print("PASS 2a: Training...")
    print("=" * 60)

    rng = np.random.default_rng(42)

    pos_y, pos_x = np.where(cat)
    # Jitter
    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
        jy = np.clip(pos_y + dy, 0, HEIGHT-1)
        jx = np.clip(pos_x + dx, 0, WIDTH-1)
        pos_y = np.concatenate([pos_y, jy])
        pos_x = np.concatenate([pos_x, jx])
    m = fp[pos_y, pos_x]
    pos_y, pos_x = pos_y[m], pos_x[m]

    cat_dil = ndi.binary_dilation(cat, iterations=4)
    neg_y, neg_x = np.where(fp & ~cat_dil)
    n_neg = min(len(pos_y) * 3, len(neg_y))
    idx = rng.choice(len(neg_y), size=n_neg, replace=False)
    neg_y, neg_x = neg_y[idx], neg_x[idx]

    all_y = np.concatenate([pos_y, neg_y])
    all_x = np.concatenate([pos_x, neg_x])
    labels = np.concatenate([np.ones(len(pos_y)), np.zeros(len(neg_y))])
    print(f"  Samples: {len(labels)} ({int(labels.sum())} pos / {int((1-labels).sum())} neg)")

    X = np.zeros((len(labels), n_feats), dtype=np.float32)
    for j, p in enumerate(feat_paths):
        fmap = load_feature(p)  # memory-mapped
        X[:, j] = fmap[all_y, all_x]
        del fmap

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    print(f"  Feature matrix: {X.shape}")

    # Top discriminators
    disc = []
    for j in range(n_feats):
        d = abs(X[:len(pos_y), j].mean() - X[len(pos_y):, j].mean())
        disc.append((d, feat_names[j]))
    disc.sort(reverse=True)
    print("  Top features:")
    for s, n in disc[:8]:
        print(f"    {n}: {s:.4f}")

    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score

    Xtr, Xv, ytr, yv = train_test_split(X, labels, test_size=0.2, random_state=42, stratify=labels)
    clf = GradientBoostingClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        subsample=0.8, max_features='sqrt', min_samples_leaf=50,
        random_state=42, verbose=1
    )
    clf.fit(Xtr, ytr)
    vp = clf.predict_proba(Xv)[:, 1]
    auc = roc_auc_score(yv, vp)
    print(f"  Validation AUC: {auc:.4f}")
    del X, Xtr, Xv, ytr, yv, labels
    gc.collect()

    # ---- Pass 2b: Predict ----
    print("=" * 60)
    print("PASS 2b: Predicting across footprint...")
    print("=" * 60)

    fp_y, fp_x = np.where(fp)
    n_fp = len(fp_y)
    proba = np.zeros((HEIGHT, WIDTH), dtype=np.float32)

    chunk = 200000
    for start in range(0, n_fp, chunk):
        end = min(start + chunk, n_fp)
        cy, cx = fp_y[start:end], fp_x[start:end]
        Xc = np.zeros((len(cy), n_feats), dtype=np.float32)
        for j, p in enumerate(feat_paths):
            fmap = load_feature(p)
            Xc[:, j] = fmap[cy, cx]
            del fmap
        Xc = np.nan_to_num(Xc, nan=0.0, posinf=0.0, neginf=0.0)
        proba[cy, cx] = clf.predict_proba(Xc)[:, 1]
        del Xc
        if (start // chunk) % 5 == 0:
            print(f"  {end}/{n_fp}")

    print(f"  Prediction range: [{proba[fp].min():.4f}, {proba[fp].max():.4f}]")
    print(f"  Mean: {proba[fp].mean():.4f}")

    # ---- Sparsify ----
    vals = proba[fp]
    threshold = 0.25
    pred = proba.copy()
    pred[pred < threshold] = 0.0
    n_pos = (pred > 0).sum()
    print(f"  Threshold: {threshold} -> {n_pos} positives")

    if n_pos > 500000:
        threshold = float(np.percentile(vals[vals > 0.01], 60))
        pred = proba.copy()
        pred[pred < threshold] = 0.0
        n_pos = (pred > 0).sum()
        print(f"  Adjusted: {threshold:.4f} -> {n_pos} positives")
    elif n_pos < 10000:
        threshold = 0.10
        pred = proba.copy()
        pred[pred < threshold] = 0.0
        n_pos = (pred > 0).sum()
        print(f"  Adjusted: {threshold} -> {n_pos} positives")

    pred[~fp] = 0.0
    pred = np.clip(pred, 0.0, 1.0).astype(np.float32)
    assert pred.min() >= 0.0 and pred.max() <= 1.0 and np.isfinite(pred).all()

    pf = pred[fp]
    pos_v = pf[pf > 0]
    print(f"\n  Positive pixels: {len(pos_v)}")
    if len(pos_v) > 0:
        print(f"  Mean (positive): {pos_v.mean():.4f}")

    # ---- Write ----
    out_dir = os.path.join(REPO, "docs", "downloads")
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, "gems58-ml-gb-structural-20261011T210000Z.tif")

    from gems57.grid import write_geotiff
    result = write_geotiff(output_path, pred)
    print(f"\nWritten: {result['path']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Size: {os.path.getsize(output_path)} bytes")

    import zipfile
    zp = output_path.replace('.tif', '.zip')
    with zipfile.ZipFile(zp, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(output_path, os.path.basename(output_path))

    evidence = {
        "hypothesis": "Supervised ML (GBM 200 trees) on 19-band GeoDAWN features detects unmapped structural faults",
        "mechanism": f"{n_feats}-feature vector per pixel",
        "validation_auc": float(auc),
        "positive_pixels": int(n_pos),
        "threshold": float(threshold),
        "file_sha256": result["sha256"],
        "format": "float32 EPSG:32611 3730x3292 100m [0,1] zero-outside all-finite",
    }
    with open(output_path.replace('.tif', '.evidence.json'), 'w') as f:
        json.dump(evidence, f, indent=2)

    # Cleanup cache
    import shutil
    shutil.rmtree(CACHE_DIR, ignore_errors=True)

    print(f"\nTotal time: {time.time()-t0:.1f}s")
    print("\n=== DONE ===")

if __name__ == "__main__":
    main()