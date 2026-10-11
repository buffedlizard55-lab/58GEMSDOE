#!/usr/bin/env python3
"""EXP-2c: fixed-budget geometry sweep evaluated **off-catalogue**.

Two corrections to ``run_geometry_sweep.py``, both forced by measurement:

1. **Hard budget.**  The emitter greedy-keeps the strongest dots subject to a
   minimum separation until it hits exactly the 38,000-dot budget, so every row
   spends the same mass and only the geometry differs.
2. **Off-catalogue scoring.**  Dots on *any* catalogue pixel (visible or
   withheld) are removed before scoring.  Without this the holdout rewards
   copying the withheld catalogue trace --- the shortcut measured as
   ``IR-57-INSTR-01`` in the sibling lane --- and the comparison is meaningless.
   With it, the holdout asks the only question that matters for this
   competition: *can off-catalogue ridge dots reach faults the catalogue
   missed?*

Writes ``evidence/final_sweep.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/run_final_sweep.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, maximum_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58 import extract, grid, holdout, metric  # noqa: E402
from gems58.paths import evidence_dir  # noqa: E402

BUDGET = 38000
CAT_MARGIN = 3.0  # px: dots closer than this to ANY catalogue pixel are inert for the real task


def greedy_topk(mask: np.ndarray, rank: np.ndarray, budget: int, min_sep: int = 2) -> np.ndarray:
    """Take the strongest dots, no two within ``min_sep`` px, until ``budget`` is reached."""
    cand = np.argwhere(mask)
    if cand.shape[0] == 0:
        return np.zeros_like(mask)
    vals = rank[cand[:, 0], cand[:, 1]]
    order = np.argsort(-vals, kind="stable")
    cand = cand[order]
    shape = mask.shape
    blocked = np.zeros(shape, bool)
    keep = np.zeros(shape, bool)
    n = 0
    k = min_sep
    for r, c in cand:
        if blocked[r, c]:
            continue
        keep[r, c] = True
        n += 1
        r0, r1 = max(0, r - k), min(shape[0], r + k + 1)
        c0, c1 = max(0, c - k), min(shape[1], c + k + 1)
        blocked[r0:r1, c0:c1] = True
        if n >= budget:
            break
    return keep


def build_emission(field, segs, *, along_spacing, max_lines, line_step_px,
                   sigma_of) -> np.ndarray:
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    for s in segs:
        idx = s["idx"]
        if along_spacing > 1:
            axis = np.argmax(np.var(idx.astype(float), axis=0))
            idx = idx[np.argsort(idx[:, axis])][::along_spacing]
        if idx.shape[0] == 0:
            continue
        n_lines = int(sigma_of(s))
        if n_lines <= 0:
            continue
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        for o in np.arange(0, n_lines) * line_step_px:
            for sgn in ((1,) if o == 0 else (1, -1)):
                rr = np.rint(idx[:, 0] + sgn * o * ay).astype(int)
                cc = np.rint(idx[:, 1] + sgn * o * ax).astype(int)
                ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
                mask[rr[ok], cc[ok]] = True
    return mask


def evaluate(pred: np.ndarray, folds, cat_d: np.ndarray, offcat_only: bool) -> dict:
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0, n_dots=0)
    for f in folds:
        p = pred
        if offcat_only:
            # remove every dot within CAT_MARGIN of any catalogue pixel, exactly
            # as the organizer removes all known-fault pixels from scoring
            p = pred & (cat_d > CAT_MARGIN)
        r = metric.dti_binary(p, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        for k in ("tp", "fp", "fn", "n_truth"):
            agg[k] += getattr(r, k)
        agg["n_dots"] += int((p & f.valid & ~f.known).sum())
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    return dict(pooled=float(agg["tp"] / den), per_fold=per_fold, agg=agg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--min-sep", type=int, default=2)
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=8)
    folds = holdout.all_folds()
    cat_d = distance_transform_edt(~grid.catalogue()).astype(np.float32)

    rows = []
    for lines in (1, 2, 3, 4):
        for along in (2, 3):
            raw = build_emission(field, segs, along_spacing=along, max_lines=lines,
                                 line_step_px=3.0, sigma_of=lambda s, n=lines: n)
            kept = greedy_topk(raw, field["mag"], args.budget, args.min_sep)
            offcat = evaluate(kept, folds, cat_d, True)
            allpix = evaluate(kept, folds, cat_d, False)
            rows.append(dict(lines=lines, along=along, step=3.0, n_raw=int(raw.sum()),
                             n_dots=int(kept.sum()), offcat=offcat, allpix=allpix))
            print(f"[sweep] lines={lines} along={along} | kept {int(kept.sum()):6d} | "
                  f"OFFCAT DTI {offcat['pooled']:.6f} (tp {offcat['agg']['tp']:7.1f}) | "
                  f"all-pixel DTI {allpix['pooled']:.6f}", flush=True)

    base = next(r for r in rows if r["lines"] == 1 and r["along"] == 3)
    for r in rows:
        for key in ("offcat", "allpix"):
            a = np.array([r[key]["per_fold"][b] for b in holdout.BLOCKS])
            b_ = np.array([base[key]["per_fold"][b] for b in holdout.BLOCKS])
            r.setdefault("delta", {})[key] = dict(
                pooled_delta=float(r[key]["pooled"] - base[key]["pooled"]),
                per_fold_delta={f.name: r[key]["per_fold"][f.name] - base[key]["per_fold"][f.name]
                                for f in [type("F", (), {"name": b})() for b in holdout.BLOCKS]},
                paired_bootstrap=metric.paired_bootstrap(a, b_, n_boot=4000, seed=58))

    # ---- sigma-stratified gain -------------------------------------------------
    bins = [(0.0, 1.5), (1.5, 2.5), (2.5, 3.0), (3.0, 1e9)]
    strat = {}
    for lo, hi in bins:
        sel = [s for s in segs if lo <= 1.680 < hi]  # placeholder replaced below
        del sel
    pooled_sigma = None
    # pooled sigma from the whole field against all withheld truth
    truth_all = np.vstack([np.argwhere(f.withhold) for f in folds]).astype(np.float64)
    pts_all = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    from scipy.spatial import cKDTree

    d_all, _ = cKDTree(pts_all).query(truth_all, k=1, workers=-1)
    pooled_sigma = float(np.sqrt((d_all[d_all <= 3] ** 2).mean()))

    out = dict(protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
               budget=args.budget, threshold=args.threshold, min_sep=args.min_sep,
               catalogue_margin_px=CAT_MARGIN,
               n_withheld_positives=int(sum(f.n_truth for f in folds)),
               sigma_pooled_detected=pooled_sigma,
               n_truth_all=int(truth_all.shape[0]),
               detection_le3px=float((d_all <= 3).mean()),
               detection_le6px=float((d_all <= 6).mean()),
               rows=rows, sigma_strata=strat,
               wall_seconds=round(time.time() - t0, 2))
    p = evidence_dir() / "final_sweep.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", p, "in", out["wall_seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
