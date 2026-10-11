#!/usr/bin/env python3
"""EXP-2: exact-metric comparison of tight lines vs parallel-dotted ribbons.

Everything is measured on the buffered hide-and-recover holdout
(``gems58-pooled-hide-v1``); the metric is ``gems58.metric/v1``, the literal
transcription of the official equations (cross-checked by
``scripts/verify_theorems.py`` against a brute-force oracle).

Writes ``evidence/holdout_eval.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/run_holdout_eval.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58 import allocation, extract, holdout, metric, sigma  # noqa: E402
from gems58.paths import evidence_dir  # noqa: E402

SIGMA_BINS = [(0.0, 0.5), (0.5, 1.5), (1.5, 2.5), (2.5, 3.0), (3.0, 1e9)]


def stratum_sigma(field, segs, fold) -> dict:
    """Per-stratum detection rate and conditional RMS localisation error."""
    truth = np.argwhere(fold.withhold).astype(np.float64)
    out = {}
    for fam, bands in __import__("gems58.features", fromlist=["x"]).FAMILIES.items():
        for scale in extract.SCALES:
            for sign in (-1, 1):
                sel = [s for s in segs
                       if any(c["band"] in bands and abs(c["scale"] - scale) < 1e-9
                              and c["sign"] == sign for c in s["codes"])]
                if not sel:
                    continue
                pts = np.vstack([s["idx"] for s in sel]).astype(np.float64)
                tree = cKDTree(pts)
                d, _ = tree.query(truth, k=1, workers=-1)
                key = f"{fam}/{'crest' if sign < 0 else 'trough'}/{scale:g}px"
                out[key] = dict(
                    n_ridge_px=int(pts.shape[0]),
                    detection_rate_le3px=float((d <= 3).mean()),
                    detection_rate_le6px=float((d <= 6).mean()),
                    rms_detected=float(np.sqrt((d[d <= 3] ** 2).mean())) if (d <= 3).any() else None,
                    n_detected=int((d <= 3).sum()),
                )
    # pooled over the whole field
    pts = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    d, _ = cKDTree(pts).query(truth, k=1, workers=-1)
    out["_pooled"] = dict(
        n_ridge_px=int(pts.shape[0]),
        detection_rate_le3px=float((d <= 3).mean()),
        detection_rate_le6px=float((d <= 6).mean()),
        rms_detected=float(np.sqrt((d[d <= 3] ** 2).mean())),
        n_detected=int((d <= 3).sum()),
    )
    return out


def evaluate(pred_bool, folds) -> dict:
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0, n_dots=0)
    for f in folds:
        r = metric.dti_binary(pred_bool, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        agg["tp"] += r.tp
        agg["fp"] += r.fp
        agg["fn"] += r.fn
        agg["n_truth"] += r.n_truth
        agg["n_dots"] += int((pred_bool & f.valid & ~f.known).sum())
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    pooled = agg["tp"] / den
    return dict(pooled=float(pooled), per_fold=per_fold, agg=agg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--min-px", type=int, default=8)
    ap.add_argument("--dti0", type=float, default=0.3195)
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=args.min_px)
    folds = holdout.all_folds()
    tf = metric.dti_binary  # aliased for brevity in the sweep below
    del tf

    # ---- sigma table (per stratum, detection based) -----------------------
    strat = {}
    for f in folds:
        s = stratum_sigma(field, segs, f)
        strat[f.name] = s
    pooled_strat = stratum_sigma(field, segs, folds[0])
    # pooled over all withheld pixels of all four folds
    truth_all = np.vstack([np.argwhere(f.withhold) for f in folds]).astype(np.float64)
    pts_all = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    d_all, _ = cKDTree(pts_all).query(truth_all, k=1, workers=-1)
    pooled_strat["_pooled_all_folds"] = dict(
        n_ridge_px=int(pts_all.shape[0]), n_truth=int(truth_all.shape[0]),
        detection_rate_le3px=float((d_all <= 3).mean()),
        detection_rate_le6px=float((d_all <= 6).mean()),
        rms_detected=float(np.sqrt((d_all[d_all <= 3] ** 2).mean())),
    )
    sigma_pooled = float(np.sqrt((d_all[d_all <= 3] ** 2).mean()))
    print(f"[sigma] pooled detection le3px {pooled_strat['_pooled_all_folds']['detection_rate_le3px']:.4f} "
          f"| RMS(detected) {sigma_pooled:.3f} px", flush=True)

    # ---- emission variants ------------------------------------------------
    allowed = np.ones(field["mag"].shape, bool)
    variants: dict[str, np.ndarray] = {}

    def add(name, mask):
        variants[name] = mask & allowed

    # V0: every ridge pixel, one tight line (the "all ridges" control)
    v0 = np.zeros(field["mag"].shape, bool)
    for s in segs:
        v0[s["idx"][:, 0], s["idx"][:, 1]] = True
    add("V0_tight_all", v0)
    add("V0_tight_all_thin", allocation.dedupe_speckles(v0, min_cluster=2))
    for sp in (2, 3):
        m = np.zeros(field["mag"].shape, bool)
        r = allocation.ribbon_mask(field, segs, lambda s: 0.0, along_spacing=sp,
                                   max_lines=1, allowed=allowed)
        m |= r["mask"]
        add(f"V0_tight_sp{sp}", m)

    # V1..V3: sigma-matched ribbons, line spacing 3 px, along-strike spacing 1..3
    plan_records = {}
    for sp in (1, 2, 3):
        r = allocation.ribbon_mask(field, segs, lambda s: sigma_pooled, along_spacing=sp,
                                   max_lines=3, allowed=allowed, dti0=args.dti0)
        add(f"V1_ribbon3_sp{sp}", r["mask"])
        plan_records[f"sp{sp}"] = r["plans"][:5]

    # V2: fixed half-width ribbons (sigma sweep) to locate the optimum
    for sig in (0.5, 1.0, 2.0, 3.0):
        r = allocation.ribbon_mask(field, segs, lambda s, s_=sig: s_, along_spacing=2,
                                   max_lines=3, allowed=allowed, dti0=args.dti0)
        add(f"V2_ribbon_sig{sig:g}", r["mask"])

    results = {}
    for name, m in variants.items():
        results[name] = evaluate(m, folds)
        print(f"[eval] {name:22s} pooled DTI {results[name]['pooled']:.6f} "
              f"dots {int(m.sum()):7d} tp {results[name]['agg']['tp']:8.1f}", flush=True)

    base = results["V0_tight_all"]
    deltas = {}
    for name, r in results.items():
        a = np.array([r["per_fold"][b] for b in holdout.BLOCKS])
        bl = np.array([base["per_fold"][b] for b in holdout.BLOCKS])
        deltas[name] = dict(pooled_delta=r["pooled"] - base["pooled"],
                            per_fold_delta={b: r["per_fold"][b] - base["per_fold"][b]
                                            for b in holdout.BLOCKS},
                            paired_bootstrap=metric.paired_bootstrap(a, bl, n_boot=4000, seed=58))

    out = dict(
        protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
        threshold=args.threshold, n_segments=len(segs),
        n_ridge_px=pooled_strat["_pooled_all_folds"]["n_ridge_px"],
        n_withheld_positives=int(truth_all.shape[0]),
        sigma_pooled_detected=sigma_pooled,
        dti0_reference=args.dti0,
        marginal_credit_threshold=metric.marginal_inclusion_threshold(args.dti0),
        max_distance_m=metric.max_distance_for_credit(
            metric.marginal_inclusion_threshold(args.dti0)),
        stratum=pooled_strat, per_fold_stratum=strat,
        results=results, deltas_vs_tight=deltas, plans=plan_records,
        wall_seconds=round(time.time() - t0, 2),
    )
    p = evidence_dir() / "holdout_eval.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", p, "in", out["wall_seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
