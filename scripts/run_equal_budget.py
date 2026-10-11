#!/usr/bin/env python3
"""EXP-3: the decisive equal-budget test --- dense single chain vs parallel dotted ribbon.

Every arm emits **isolated dots** (no two 8-adjacent, ``min_sep = 1``) and every
arm is greedy-capped at the **same 38,000-dot budget**, so the only difference is
the geometry of the support:

* **width 1** --- one line along the ridge, dots every ~3 px of strike;
* **width 2** --- the ridge line plus one parallel line at +-3 px (kernel radius);
* **width 3** --- the ridge line plus parallel lines at +-3 px and -3 px;
* **width 4** --- plus lines at +-6 px.

Scored with the exact metric on the buffered hide-and-recover holdout
(``gems58-pooled-hide-v1``).  Reported per data block, with a paired bootstrap
over the four blocks, and stratified by the measured localisation scale sigma.

Writes ``evidence/equal_budget.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/run_equal_budget.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58 import extract, grid, holdout, metric  # noqa: E402
from gems58.paths import evidence_dir  # noqa: E402

BUDGET = 38000
MIN_SEP = 1


def greedy_topk(mask: np.ndarray, rank: np.ndarray, budget: int, min_sep: int):
    cand = np.argwhere(mask)
    if cand.shape[0] == 0:
        return np.zeros_like(mask), 0
    vals = rank[cand[:, 0], cand[:, 1]]
    cand = cand[np.argsort(-vals, kind="stable")]
    shape = mask.shape
    blocked = np.zeros(shape, bool)
    keep = np.zeros(shape, bool)
    n = 0
    k = max(0, min_sep)
    for r, c in cand:
        if blocked[r, c]:
            continue
        keep[r, c] = True
        n += 1
        blocked[max(0, r - k):r + k + 1, max(0, c - k):c + k + 1] = True
        if n >= budget:
            break
    return keep, n


def ribbon_support(field, segs, width: int, step: float = 3.0,
                   along: int = 1, seg_filter=None) -> np.ndarray:
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    for i, s in enumerate(segs):
        if seg_filter is not None and not seg_filter(i, s):
            continue
        idx = s["idx"]
        if along > 1:
            axis = np.argmax(np.var(idx.astype(float), axis=0))
            idx = idx[np.argsort(idx[:, axis])][::along]
        if idx.shape[0] == 0:
            continue
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        for j in range(width):
            o = j * step
            for sgn in ((1,) if o == 0 else (1, -1)):
                rr = np.rint(idx[:, 0] + sgn * o * ay).astype(int)
                cc = np.rint(idx[:, 1] + sgn * o * ax).astype(int)
                ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
                mask[rr[ok], cc[ok]] = True
    return mask


def evaluate(pred: np.ndarray, folds) -> dict:
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0, n_dots=0)
    for f in folds:
        r = metric.dti_binary(pred, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        for k in ("tp", "fp", "fn", "n_truth"):
            agg[k] += getattr(r, k)
        agg["n_dots"] += int((pred & f.valid & ~f.known).sum())
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    return dict(pooled=float(agg["tp"] / den), per_fold=per_fold, agg=agg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--step", type=float, default=3.0)
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=8)
    folds = holdout.all_folds()
    cat_d = distance_transform_edt(~grid.catalogue()).astype(np.float32)

    # ---------------- sigma table ----------------
    truth_all = np.vstack([np.argwhere(f.withhold) for f in folds]).astype(np.float64)
    pts_all = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    d_all, _ = cKDTree(pts_all).query(truth_all, k=1, workers=-1)
    sigma_pooled = float(np.sqrt((d_all[d_all <= 3] ** 2).mean()))
    sigma_strata = {}
    from gems58 import features as FEAT
    for fam, bands in FEAT.FAMILIES.items():
        for scale in extract.SCALES:
            sub = [s for s in segs
                   if any(c["band"] in bands and abs(c["scale"] - scale) < 1e-9 for c in s["codes"])]
            if not sub:
                continue
            pts = np.vstack([s["idx"] for s in sub]).astype(np.float64)
            d, _ = cKDTree(pts).query(truth_all, k=1, workers=-1)
            det = d <= 3
            sigma_strata[f"{fam}/{scale:g}px"] = dict(
                n_ridge_px=int(pts.shape[0]), detection_le3px=float(det.mean()),
                rms_detected=float(np.sqrt((d[det] ** 2).mean())) if det.any() else None)
    for b in holdout.BLOCKS:
        f = holdout.folds(b)[0]
        t = np.argwhere(f.withhold).astype(np.float64)
        d, _ = cKDTree(pts_all).query(t, k=1, workers=-1)
        det = d <= 3
        sigma_strata[f"block/{b}"] = dict(n_ridge_px=int(pts_all.shape[0]),
                                          detection_le3px=float(det.mean()),
                                          rms_detected=float(np.sqrt((d[det] ** 2).mean())) if det.any() else None)
    sigma_strata["pooled"] = dict(n_ridge_px=int(pts_all.shape[0]),
                                  detection_le3px=float((d_all <= 3).mean()),
                                  detection_le6px=float((d_all <= 6).mean()),
                                  rms_detected=sigma_pooled,
                                  n_truth=int(truth_all.shape[0]))

    # ---------------- equal-budget arms ----------------
    arms, results = {}, {}
    for width in (1, 2, 3, 4):
        raw = ribbon_support(field, segs, width, args.step, along=1)
        kept, n = greedy_topk(raw, field["mag"], args.budget, MIN_SEP)
        arms[width] = kept
        results[width] = evaluate(kept, folds)
        print(f"[arm] width={width} | raw {int(raw.sum()):7d} | kept {n:6d} | "
              f"HOLDOUT-DTI {results[width]['pooled']:.6f} "
              f"(tp {results[width]['agg']['tp']:7.1f}, fp {results[width]['agg']['fp']:7.1f})",
              flush=True)

    # catalogue-distance profile of each arm (a live-evidence covariate, not a
    # holdout score) so the reviewer can see how far from the catalogue each
    # arm's dots sit
    prof = {}
    for width, m in arms.items():
        v = cat_d[m]
        prof[width] = dict(median=float(np.median(v)), mean=float(v.mean()),
                           frac_le3px=float((v <= 3).mean()),
                           frac_le10px=float((v <= 10).mean()),
                           frac_le20px=float((v <= 20).mean()),
                           n=int(m.sum()))

    # sigma-stratified gain: width 1 vs width 3 restricted to sigma classes.
    # Segments are binned by the local sigma of the *withheld component* they
    # cover most, taken from the per-component measurement.
    base = results[1]
    deltas = {}
    for width in (2, 3, 4):
        a = np.array([results[width]["per_fold"][b] for b in holdout.BLOCKS])
        b_ = np.array([base["per_fold"][b] for b in holdout.BLOCKS])
        deltas[width] = dict(pooled_delta=float(results[width]["pooled"] - base["pooled"]),
                             per_fold_delta={k: float(results[width]["per_fold"][k] - base["per_fold"][k])
                                             for k in holdout.BLOCKS},
                             paired_bootstrap=metric.paired_bootstrap(a, b_, n_boot=8000, seed=58))

    # Simulated gain per measured-sigma class.
    #
    # Done *per fold* with that fold's own masking: a truth set pooled across
    # folds and scored under the union of every fold's known mask would be
    # entirely masked away (every catalogue pixel is visible in some fold), so
    # the pooled-truth version of this diagnostic reads n_truth = 0 by
    # construction -- the same obstruction the site documents as IR-58-02.
    class_gain = {}
    fold_rows = [np.argwhere(f.withhold).astype(np.float64) for f in folds]
    fold_dist = [cKDTree(pts_all).query(r, k=1, workers=-1)[0] for r in fold_rows]
    for lo, hi in ((0.0, 1.5), (1.5, 2.5), (2.5, 3.0), (3.0, 6.0)):
        cls = {}
        for width in (1, 2, 3, 4):
            tp = fp = 0.0
            g = 0
            for f, rows_f, d_f in zip(folds, fold_rows, fold_dist):
                sel = (d_f >= lo) & (d_f < hi)
                if not sel.any():
                    continue
                tm = np.zeros(field["mag"].shape, bool)
                tm[rows_f[sel, 0].astype(int), rows_f[sel, 1].astype(int)] = True
                r = metric.dti_binary(arms[width], tm, valid=grid.footprint(), known=f.known)
                tp += r.tp
                fp += r.fp
                g += r.n_truth
            den = tp + metric.ALPHA * fp + metric.BETA * (g - tp) + metric.EPS
            cls[str(width)] = dict(tp=tp, fp=fp, n_truth=g, dti=(tp / den if g else 0.0))
        class_gain[f"sigma-{lo:g}-{hi:g}px"] = cls
        if cls["1"]["n_truth"]:
            print(f"[class] sigma {lo:g}-{hi:g}px n={cls['1']['n_truth']:6d} | "
                  f"simulated DTI width1 {cls['1']['dti']:.6f} width3 {cls['3']['dti']:.6f} "
                  f"| gain {cls['3']['dti'] - cls['1']['dti']:+.6f}", flush=True)
        else:
            print(f"[class] sigma {lo:g}-{hi:g}px n=     0 (no withheld truth in class)", flush=True)

    out = dict(protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
               budget=args.budget, min_sep=MIN_SEP, threshold=args.threshold,
               line_step_px=args.step, n_withheld_positives=int(sum(f.n_truth for f in folds)),
               n_ridge_px=int(pts_all.shape[0]), sigma_pooled_detected=sigma_pooled,
               sigma_strata=sigma_strata, results={str(k): v for k, v in results.items()},
               deltas_vs_width1={str(k): v for k, v in deltas.items()},
               catalogue_distance_profile={str(k): v for k, v in prof.items()},
               simulated_gain_per_sigma_class=class_gain,
               wall_seconds=round(time.time() - t0, 2))
    p = evidence_dir() / "equal_budget.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", p, "in", out["wall_seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
