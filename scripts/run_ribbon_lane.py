#!/usr/bin/env python3
"""DEPRECATED historical pipeline; command-line execution is disabled.

This copy uses an unbuffered component split, a local gems58 metric/uniqueness
implementation and a private submission path. It does not satisfy the current
shared-template protocol. Kept only for audit/history; do not use for a
submission or performance claim. Use the gems57 shared pipeline after all
current holdout and literal-registry gates clear.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata
from scipy.stats import t as tdist

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58 import ribbon as R  # noqa: E402
from gems58 import uniqueness as U  # noqa: E402
from gems58.metric import EPS, ALPHA, BETA, truth_weight_map, utility_U  # noqa: E402
from gems58.validate import validate  # noqa: E402

DATA = Path(os.environ.get("GEMS_DATA", Path.home() / ".cache/gems-data"))
REGISTRY = Path(os.environ.get("GEMS_REGISTRY", Path.home() / ".cache/gems-src"))
OUT_REG = ROOT / "registry"
OUT_DOCS = ROOT / "docs" / "downloads"
SUBMISSION_NAME = "58GEMSDOE-ribbon-lane-v1-20261011"
EVALUATOR = "gems58.metric (58GEMSDOE, verified vs rules worked example + brute force)"
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


NODATA_ABS = 1e30  # GeoTIFF float nodata (-3.4028e38) is finite, so test magnitude explicitly


def clean_band(x, valid):
    """Replace non-finite / nodata cells inside the footprint by the band median (finite cells only)."""
    x = x.astype(np.float32)
    good = valid & np.isfinite(x) & (np.abs(x) < NODATA_ABS)
    fill = float(np.median(x[good]))
    return np.where(good, x, fill).astype(np.float32)


def auc(pos, neg):
    n1, n0 = pos.size, neg.size
    r = rankdata(np.concatenate([pos, neg]))
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def setup():
    with rasterio.open(DATA / "sample_submission.tif") as s:
        ref = s.read(1)
        profile = s.profile.copy()
        shape = s.shape
    valid = np.isfinite(ref)
    with rasterio.open(DATA / "labels.tif") as s:
        lab = s.read(1)
    with rasterio.open(DATA / "gems-geodawn-numerical-features.tif") as s:
        desc = list(s.descriptions)
        feat_shape = s.shape
        feat_tf = tuple(s.transform)
    assert feat_shape == shape, "feature stack and sample grid differ"
    assert feat_tf[:6] == tuple(profile["transform"])[:6], "transform differs"
    cat = lab == 1
    label_valid = lab != -1
    checks = dict(labels_valid_equals_footprint=bool(np.array_equal(label_valid, valid)),
                  n_catalogue_px=int(cat.sum()), footprint_px=int(valid.sum()), shape=list(shape))
    # segments -> quadrant blocks (2x2) by centroid
    seg, nseg = ndi.label(cat, structure=np.ones((3, 3), int))
    cents = np.array(ndi.center_of_mass(cat, seg, range(1, nseg + 1)))
    mid_r, mid_c = shape[0] / 2.0, shape[1] / 2.0
    seg_block = (cents[:, 0] >= mid_r).astype(int) * 2 + (cents[:, 1] >= mid_c).astype(int)
    blk_lookup = np.concatenate([[-1], seg_block])
    block = blk_lookup[seg]
    folds = []
    for b in range(4):
        truth = cat & (block == b)
        visible = cat & ~truth
        active = valid & ~visible
        gy, gx = np.nonzero(truth & active)
        W = truth_weight_map(truth & active).astype(np.float32)
        folds.append(dict(id=b, truth=truth, visible=visible, active=active, gy=gy, gx=gx, W=W,
                          n_truth=int(gy.size), n_segments=int((seg_block == b).sum())))
    checks["folds"] = [dict(id=f["id"], n_truth=f["n_truth"], n_segments=f["n_segments"]) for f in folds]
    return ref, valid, lab, cat, folds, desc, profile, checks


def ridge_classes(valid, desc, cat, folds, canary_rows):
    """Return cands[(cls, frac)] (thinned ridge candidates) and append ridge-strength canary rows."""
    cands = {}
    neg_pool = valid & ~ndi.binary_dilation(cat, iterations=3)
    rng = np.random.default_rng(0)
    for rtype, band in R.RIDGE_TYPES.items():
        bi = R.band_index(desc, band)
        with rasterio.open(DATA / "gems-geodawn-numerical-features.tif") as s:
            x = s.read(bi).astype(np.float32)
        x = clean_band(x, valid)
        lo, hi = np.percentile(x[valid], [1, 99])  # robust clip: deq_n100a15 has heavy tails
        x = np.clip(x, lo, hi)
        mu, sd = float(x[valid].mean()), float(x[valid].std())
        z = np.where(valid, (x - mu) / (sd if sd > 0 else 1.0), 0.0).astype(np.float32)
        del x
        for rname, scale in R.RESOLUTIONS.items():
            cls = f"{rtype}-{rname}"
            st, vx, vy, keep = R.ridge_field(z, valid, scale)
            # canary (E1): ridge strength alone, per fold
            negs = np.flatnonzero(neg_pool)
            negs = rng.choice(negs, min(200_000, negs.size), replace=False)
            for f in folds:
                pos = st[f["gy"], f["gx"]]
                canary_rows.append(dict(feature=cls, kind="ridge_strength", fold=f["id"],
                                        auc=auc(pos.astype(float), st.ravel()[negs].astype(float))))
            for frac in R.FRACS:
                cands[(cls, frac)] = R.candidates_for(st, vx, vy, keep, valid, frac)
            del st, vx, vy, keep
            log("candidates", cls, {f: cands[(cls, f)]["ys"].size for f in R.FRACS})
        del z
    return cands


def band_canary(valid, desc, cat, folds, rows):
    rng = np.random.default_rng(1)
    neg_pool = valid & ~ndi.binary_dilation(cat, iterations=3)
    negs_all = np.flatnonzero(neg_pool)
    negs = rng.choice(negs_all, min(200_000, negs_all.size), replace=False)
    with rasterio.open(DATA / "gems-geodawn-numerical-features.tif") as s:
        for bi, d in enumerate(desc, start=1):
            name = d.split(" - ")[0].strip()
            x = s.read(bi).astype(np.float64)
            x[~np.isfinite(x) | (np.abs(x) > 1e30)] = np.nan  # -3.4e38 nodata inside footprint
            nv = x.ravel()[negs]
            nv = np.where(np.isfinite(nv), nv, np.nanmedian(nv))
            for f in folds:
                pv = x[f["gy"], f["gx"]]
                pv = np.where(np.isfinite(pv), pv, np.nanmedian(nv))
                a = auc(pv, nv)
                rows.append(dict(feature=name, kind="band_value", fold=f["id"], auc=a,
                                 auc_directional=max(a, 1 - a)))
    return rows


def sigma_table(cands, folds, valid):
    """Per (class, frac, block): matched localisation distances from withheld truth to candidates."""
    rows, dists = [], {}
    for (cls, frac), c in cands.items():
        m = np.zeros(valid.shape, bool)
        m[c["ys"], c["xs"]] = True
        dC = ndi.distance_transform_edt(~m)
        for f in folds:
            d = dC[f["gy"], f["gx"]]
            d = d[d <= 10.0]
            dists[(cls, frac, f["id"])] = d
            rows.append(dict(cls=cls, frac=frac, block=f["id"], n_matched=int(d.size),
                             median_d_px=float(np.median(d)) if d.size else float("nan"),
                             frac_within_3px=float((d <= 3).mean()) if d.size else float("nan"),
                             sigma_px=R.robust_sigma(d)))
    return rows, dists


def pooled_sigma(dists, cls, frac, blocks):
    d = np.concatenate([dists[(cls, frac, b)] for b in blocks]) if blocks else np.array([])
    return R.robust_sigma(d)


def mask_for(cands, cls, frac, config, valid):
    return R.emission_mask(cands[(cls, frac)], config, valid.shape, valid)


def union_L1(cands, valid, frac=0.005):
    m = np.zeros(valid.shape, bool)
    for (cls, f) in cands:
        if f == frac:
            m |= mask_for(cands, cls, f, "L1", valid)
    return m


def evaluate(P, fold):
    """Exact DTI components for binary emission P on one held-out fold (known = visible)."""
    act = fold["active"]
    tp = R.tp_credit(P & act, fold["gy"], fold["gx"])
    fp = float(fold["W"][P & act].sum(dtype=np.float64))
    return tp, fp, fold["n_truth"]


def pooled(tp, fp, n):
    return float(tp / (tp + ALPHA * fp + BETA * (n - tp) + EPS))


def main():
    OUT_REG.mkdir(exist_ok=True)
    (OUT_REG / "experiments").mkdir(exist_ok=True)
    ref, valid, lab, cat, folds, desc, profile, checks = setup()
    log("setup", checks["n_catalogue_px"], checks["footprint_px"], [f["n_truth"] for f in folds])

    # ---------------- E1 ----------------
    canary = []
    band_canary(valid, desc, cat, folds, canary)
    cands = ridge_classes(valid, desc, cat, folds, canary)
    sig_rows, dists = sigma_table(cands, folds, valid)
    log("E1 sigma done")
    # surface check (protocol §1, before placement): candidate surface vs registry
    surface = np.where(valid, union_L1(cands, valid, 0.005).astype(np.float32), np.nan).astype(np.float32)
    surface_check = None
    reg_dirs = [str(p) for p in sorted(REGISTRY.glob("*GEMSDOE*")) if p.is_dir()]
    if reg_dirs:
        surface_check = U.run(_tmp_surface(surface, profile), reg_dirs, valid,
                              OUT_REG / "uniqueness_surface_pre-placement.csv", "surface")
    log("E1 surface", surface_check)
    canary_max = {}
    for r in canary:
        canary_max.setdefault(r["feature"], []).append(r.get("auc_directional", r["auc"]))
    canary_summary = {k: dict(mean_auc=float(np.mean(v)), max_auc=float(np.max(v))) for k, v in canary_max.items()}
    leak = {k: v for k, v in canary_summary.items() if v["max_auc"] > 0.90}
    e1 = dict(experiment="E1", checks=checks, canary_summary=canary_summary,
              canary_leak_flags_gt_0p90=leak, sigma_rows=sig_rows, surface_check=surface_check,
              seconds=round(time.time() - T0, 1))
    (OUT_REG / "experiments" / "E1_canary_sigma_surface.json").write_text(json.dumps(e1, indent=2, default=float))
    write_csv(OUT_REG / "sigma_table.csv", sig_rows)
    write_csv(OUT_REG / "canary_auc.csv", canary)
    log("E1 written; leak flags:", list(leak))

    # ---------------- E2 ----------------
    classes = sorted({c for c, _ in cands})
    options = [(f, k) for f in R.FRACS for k in R.CONFIGS]
    TP = {}; FP = {}; NDOT = {}
    for cls in classes:
        for (f, k) in options:
            P = mask_for(cands, cls, f, k, valid)
            NDOT[(cls, f, k)] = int(P.sum())
            for fo in folds:
                tp, fp, _ = evaluate(P, fo)
                TP[(cls, f, k, fo["id"])] = tp
                FP[(cls, f, k, fo["id"])] = fp
        log("E2 options", cls)
    base_TP = {}; base_FP = {}
    Ubase = union_L1(cands, valid, 0.005)
    for fo in folds:
        base_TP[fo["id"]], base_FP[fo["id"]], _ = evaluate(Ubase, fo)
    nested = []
    chosen_all = {}
    for b in range(4):
        others = [f["id"] for f in folds if f["id"] != b]
        # D0 = pooled DTI of the L1 union on the other blocks (no information from block b)
        D0 = pooled(sum(base_TP[o] for o in others), sum(base_FP[o] for o in others),
                    sum(folds[o]["n_truth"] for o in others))
        sel = {}
        Pb = np.zeros(valid.shape, bool)
        for cls in classes:
            best, best_u, best_n = None, -np.inf, None
            for (f, k) in options:
                sig = pooled_sigma(dists, cls, f, others)
                if not R.sigma_rule(sig, k):
                    continue
                u = sum(utility_U(TP[(cls, f, k, o)], FP[(cls, f, k, o)], D0) for o in others)
                if u > best_u + 1e-12 or (abs(u - best_u) <= 1e-12 and best_n is not None and NDOT[(cls, f, k)] < best_n):
                    best, best_u, best_n = (f, k), u, NDOT[(cls, f, k)]
            sel[cls] = dict(frac=best[0], config=best[1], U_other_blocks=best_u,
                            sigma_other_blocks=pooled_sigma(dists, cls, best[0], others), n_dots=int(best_n))
            Pb |= mask_for(cands, cls, best[0], best[1], valid)
        tp, fp, n = evaluate(Pb, folds[b])
        nested.append(dict(block=b, TP=tp, FP=fp, n_truth=n, DTI0_other_blocks=D0, dti=pooled(tp, fp, n),
                           dots=int(Pb.sum()), selection=sel))
        log("E2 block", b, "dti", round(pooled(tp, fp, n), 5), "dots", int(Pb.sum()))
    TPs = sum(r["TP"] for r in nested); FPs = sum(r["FP"] for r in nested); Ns = sum(r["n_truth"] for r in nested)
    pooled_dti = pooled(TPs, FPs, Ns)
    jk = []
    for b in range(4):
        keep_ = [r for r in nested if r["block"] != b]
        jk.append(pooled(sum(r["TP"] for r in keep_), sum(r["FP"] for r in keep_), sum(r["n_truth"] for r in keep_)))
    jk = np.array(jk)
    n_b = len(jk)
    se = float(np.sqrt((n_b - 1) / n_b * np.sum((jk - jk.mean()) ** 2)))
    tcrit = float(tdist.ppf(0.975, n_b - 1))
    base_pooled = pooled(sum(base_TP.values()), sum(base_FP.values()), sum(f["n_truth"] for f in folds))
    e2 = dict(experiment="E2", evaluator=EVALUATOR,
              holdout_dti_nested_lobo=dict(value=pooled_dti, n_withheld_positives=int(Ns), n_blocks=4,
                                          jackknife_se=se, ci95_t=[pooled_dti - tcrit * se, pooled_dti + tcrit * se],
                                          tcrit_df3=tcrit, note="4 spatial blocks; CI is wide and low-power"),
              baseline_L1_union_frac0p005_pooled_dti=base_pooled,
              per_block=nested, seconds=round(time.time() - T0, 1))
    (OUT_REG / "experiments" / "E2_nested_holdout.json").write_text(json.dumps(e2, indent=2, default=float))
    log("E2 pooled nested DTI", pooled_dti, "baseline", base_pooled, "se", se)

    # ---------------- E3 ----------------
    blocks_all = [f["id"] for f in folds]
    D0_all = pooled(sum(base_TP.values()), sum(base_FP.values()), sum(f["n_truth"] for f in folds))
    final_sel = {}
    P = np.zeros(valid.shape, bool)
    for cls in classes:
        best, best_u, best_n = None, -np.inf, None
        for (f, k) in options:
            sig = pooled_sigma(dists, cls, f, blocks_all)
            if not R.sigma_rule(sig, k):
                continue
            u = sum(utility_U(TP[(cls, f, k, o)], FP[(cls, f, k, o)], D0_all) for o in blocks_all)
            if u > best_u + 1e-12 or (abs(u - best_u) <= 1e-12 and best_n is not None and NDOT[(cls, f, k)] < best_n):
                best, best_u, best_n = (f, k), u, NDOT[(cls, f, k)]
        sig = pooled_sigma(dists, cls, best[0], blocks_all)
        final_sel[cls] = dict(frac=best[0], config=best[1], sigma_px_all_blocks=sig,
                              sigma_rule_forced=bool(sig < 0.5 or 2.0 <= sig <= 3.0),
                              U_sum_all_blocks=best_u, n_dots_class=int(best_n))
        P |= mask_for(cands, cls, best[0], best[1], valid)
    dots = P & valid
    out = np.where(valid, dots.astype(np.float32), np.nan).astype(np.float32)
    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DOCS / f"{SUBMISSION_NAME}.tif"
    prof = dict(profile)
    prof.update(dtype="float32", count=1, nodata=np.nan, driver="GTiff")
    with rasterio.open(out_path, "w", **prof) as d:
        d.write(out, 1)
    report = validate(out_path, DATA / "sample_submission.tif")
    log("E3 validation pass:", report["all_pass"])
    # final-recipe in-sample check on all blocks (optimistic; reported, not a score)
    fin_tp = fin_fp = 0.0
    for fo in folds:
        tp, fp, _ = evaluate(P, fo)
        fin_tp += tp; fin_fp += fp
    in_sample = pooled(fin_tp, fin_fp, sum(f["n_truth"] for f in folds))
    uni = U.run(out_path, reg_dirs, valid, OUT_REG / f"uniqueness_final_{SUBMISSION_NAME}.csv",
                "final") if reg_dirs else None
    e3 = dict(experiment="E3", submission=str(out_path.relative_to(ROOT)), selection=final_sel,
              dots_total=int(dots.sum()), validator=report, uniqueness=uni,
              in_sample_holdout_dti_optimistic=in_sample,
              seconds=round(time.time() - T0, 1))
    (OUT_REG / "experiments" / "E3_final_emission.json").write_text(json.dumps(e3, indent=2, default=float))
    log("E3 done", out_path.name, "dots", int(dots.sum()), "uniq", uni and uni["verdict"])


def _tmp_surface(surface, profile):
    p = Path("/tmp/gems_surface.tif")
    prof = dict(profile); prof.update(dtype="float32", count=1, nodata=np.nan, driver="GTiff")
    with rasterio.open(p, "w", **prof) as d:
        d.write(surface, 1)
    return p


def write_csv(path, rows):
    import csv
    if not rows:
        return
    keys = sorted({k for r in rows for k in r})
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(
        "DEPRECATED/NO-GO: this legacy gems58 pipeline has an unbuffered split, "
        "a private metric/uniqueness path, and does not use the shared evaluator/writer. "
        "Do not run it for a submission; use the reviewed gems57 pipeline only after its gates clear."
    )
