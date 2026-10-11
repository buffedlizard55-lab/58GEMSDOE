#!/usr/bin/env python3
"""Fast ML submission using Random Forest with minimal memory.
Peak memory < 800 MB.  Uses 10 key bands, 2 gradient scales each = 20 uint8 maps.
Training on 50K samples.  Prediction in chunks.
"""
from __future__ import annotations
import gc, hashlib, json, os, sys, time
import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

SENTINEL = -1e30
H, W = 3730, 3292
STACK = os.path.expanduser("~/.cache/gems/training_features.tif")
SAMPLE_TIF = os.path.join(REPO, "data", "bridge", "sample_submission.tif")
CAT_TIF = os.path.join(REPO, "data", "bridge", "existing_faults.tif")


def load_band(idx, fp):
    with rasterio.open(STACK) as src:
        b = src.read(idx).astype(np.float32)
    b[b < SENTINEL] = 0.0
    b[~fp] = 0.0
    return np.nan_to_num(b, nan=0.0, posinf=0.0, neginf=0.0)


def to_uint8(arr, fp):
    v = arr[fp]
    mu, sig = float(np.mean(v)), float(np.std(v))
    if sig < 1e-10:
        return np.zeros(arr.shape, dtype=np.uint8)
    z = np.clip((arr - mu) / sig, -3, 3)
    q = ((z + 3.0) / 6.0 * 255.0).astype(np.uint8)
    q[~fp] = 0
    return q


def main():
    t0 = time.time()

    with rasterio.open(SAMPLE_TIF) as src:
        fp = np.isfinite(src.read(1))
    with rasterio.open(CAT_TIF) as src:
        cat = (src.read(1) > 0) & fp
    fp_y, fp_x = np.where(fp)
    n_fp = len(fp_y)
    print(f"Footprint: {n_fp} | Catalogue: {cat.sum()}")

    # ---- Compute features: 10 key bands x 2 scales = 20 uint8 maps ----
    # Key structural bands for fault detection
    key_bands = [
        (1, "cond"), (3, "topo"), (8, "gravity"), (10, "mag_RTP"),
        (11, "TMI"), (14, "mag_depth"), (4, "slope"), (9, "grav_slope"),
        (12, "v_TMI"), (15, "quake")
    ]
    feat_maps = []
    feat_names = []
    
    for bidx, bname in key_bands:
        band = load_band(bidx, fp)
        for sigma in [1.5, 3.0]:
            sm = gaussian_filter(band, sigma=sigma)
            gx = ndi.sobel(sm, axis=1)
            gy = ndi.sobel(sm, axis=0)
            gmag = np.sqrt(gx**2 + gy**2).astype(np.float32)
            del sm, gx, gy
            feat_maps.append(to_uint8(gmag, fp))
            feat_names.append(f"{bname}_g{sigma}")
            del gmag
        del band
        gc.collect()
    
    n_feats = len(feat_names)
    print(f"Features: {n_feats} uint8 maps ({n_feats * H * W / 1e6:.1f} MB)")

    # ---- Sample 50K training pixels ----
    rng = np.random.default_rng(42)
    pos_y, pos_x = np.where(cat)
    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
        pos_y = np.concatenate([pos_y, np.clip(pos_y+dy, 0, H-1)])
        pos_x = np.concatenate([pos_x, np.clip(pos_x+dx, 0, W-1)])
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
    print(f"Training: {len(labels)} samples ({int(labels.sum())} pos / {int((1-labels).sum())} neg)")

    X = np.zeros((len(labels), n_feats), dtype=np.float32)
    for j, fmap in enumerate(feat_maps):
        X[:, j] = fmap[all_y, all_x].astype(np.float32) / 255.0

    # ---- Train RandomForest (fast, parallel) ----
    print("Training RandomForest...")
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score

    Xtr, Xv, ytr, yv = train_test_split(X, labels, test_size=0.2, random_state=42, stratify=labels)
    
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=8, max_features='sqrt',
        min_samples_leaf=100, n_jobs=-1, random_state=42, verbose=1
    )
    clf.fit(Xtr, ytr)
    vp = clf.predict_proba(Xv)[:, 1]
    auc = roc_auc_score(yv, vp)
    print(f"  Validation AUC: {auc:.4f}")
    
    del X, Xtr, Xv, ytr, yv, labels
    gc.collect()

    # ---- Predict ----
    print("Predicting...")
    proba = np.zeros((H, W), dtype=np.float32)
    chunk = 500000
    for start in range(0, n_fp, chunk):
        end = min(start + chunk, n_fp)
        cy, cx = fp_y[start:end], fp_x[start:end]
        Xc = np.zeros((len(cy), n_feats), dtype=np.float32)
        for j, fmap in enumerate(feat_maps):
            Xc[:, j] = fmap[cy, cx].astype(np.float32) / 255.0
        proba[cy, cx] = clf.predict_proba(Xc)[:, 1]
        del Xc
        print(f"  {end}/{n_fp}")

    vals = proba[fp]
    print(f"Range: [{vals.min():.4f}, {vals.max():.4f}] Mean: {vals.mean():.4f}")

    # ---- Threshold ----
    threshold = 0.30
    pred = proba.copy()
    pred[pred < threshold] = 0.0
    n_pos = (pred > 0).sum()
    print(f"Threshold {threshold} -> {n_pos} positives")

    if n_pos > 300000:
        threshold = float(np.percentile(vals[vals > 0.01], 75))
        pred = proba.copy()
        pred[pred < threshold] = 0.0
        n_pos = (pred > 0).sum()
        print(f"Adjusted: {threshold:.4f} -> {n_pos}")
    elif n_pos < 10000:
        threshold = 0.10
        pred = proba.copy()
        pred[pred < threshold] = 0.0
        n_pos = (pred > 0).sum()
        print(f"Adjusted: {threshold} -> {n_pos}")

    pred[~fp] = 0.0
    pred = np.clip(pred, 0.0, 1.0).astype(np.float32)
    assert pred.min() >= 0.0 and pred.max() <= 1.0 and np.isfinite(pred).all()

    pf = pred[fp]
    pv = pf[pf > 0]
    print(f"Final: {len(pv)} positives, mean={pv.mean():.4f}" if len(pv) > 0 else "Final: 0 positives")

    # ---- Write ----
    out_dir = os.path.join(REPO, "docs", "downloads")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gems58-ml-rf-v2-20261011T223000Z.tif")

    from gems57.grid import write_geotiff
    result = write_geotiff(out_path, pred)
    print(f"\nWritten: {out_path}")
    print(f"SHA256: {result['sha256']}")
    print(f"Size: {os.path.getsize(out_path)} bytes")

    import zipfile
    zp = out_path.replace('.tif', '.zip')
    with zipfile.ZipFile(zp, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(out_path, os.path.basename(out_path))

    evidence = {
        "hypothesis": "RandomForest on 20 geophysical gradient features detects unmapped structural faults",
        "features": n_feats,
        "validation_auc": float(auc),
        "positive_pixels": int(n_pos),
        "threshold": float(threshold),
        "file_sha256": result["sha256"],
    }
    with open(out_path.replace('.tif', '.evidence.json'), 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"\nTime: {time.time()-t0:.1f}s\n=== DONE ===")


if __name__ == "__main__":
    main()