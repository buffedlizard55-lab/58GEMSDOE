#!/usr/bin/env python3
"""EXP-B: equal-budget geometry test — along-strike dot spacing vs across-strike width.

The lane prompt asks for the number *and offset* of parallel dotted lines that
maximise ``U = (1 - 0.2*DTI0)*TP - 0.2*DTI0*FP``, evaluated with the exact
metric.  Two knobs are in play and they trade against each other:

* **across-strike width** (``n_lines``): more parallel lines raise the kernel
  credit of truth that sits off the detected ridge;
* **along-strike spacing** (keep every Nth ridge pixel): a dot line at spacing
  ``s`` is ``s`` times cheaper per unit length, but the largest distance a truth
  pixel can be from the nearest dot becomes ``sqrt(R_perp^2 + (s/2)^2)``, so the
  perpendicular reach shrinks from R to ``sqrt(R^2 - (s/2)^2)``.

At a fixed budget ``S`` this is a pure geometry question and the exact metric
answers it.  This script emits every (spacing, budget) combination on the same
ridge field, screens the catalogue margin identically, keeps the strongest
isolated dots greedily to the budget, and scores each with the shared exact
evaluator on the hide-and-recover holdout.

Writes ``evidence/ribbon_v2/equal_budget.json``.

    PYTHONPATH=src GEMS58W_CACHE=... GEMS_FEATURE_STACK=... \
        python3 scripts/ribbon_run_equal_budget_v2.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems58w import extract, grid, holdout, metric, sigma  # noqa: E402
from gems58w.metric import paired_bootstrap  # noqa: E402

import ribbon_build_submission as RBS  # noqa: E402  (shared lane builder helpers)

EVID = ROOT / "evidence" / "ribbon_v2"
DTI0 = 0.26


def build_support(field, segs, table, dti0, along_spacing):
    mask, hist, rows = RBS.ribbon_support_adaptive(field, segs, table, dti0,
                                                   max_k=3, shift_of=None,
                                                   along_spacing=along_spacing)
    return mask, hist, rows


def score_folds(dots, folds):
    """Pooled exact DTI plus per-fold DTI at the same dots."""
    agg = dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0)
    per_fold = {}
    for f in folds:
        r = metric.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        for k in ("tp", "fp", "fn", "n_truth"):
            agg[k] += getattr(r, k)
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    return float(agg["tp"] / den), per_fold, agg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--min-px", type=int, default=8)
    ap.add_argument("--budgets", default="30000,38000,44090,50000,60000")
    ap.add_argument("--spacings", default="1,2,3")
    ap.add_argument("--cat-margin", type=float, default=3.0)
    args = ap.parse_args()
    t0 = time.time()

    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=args.min_px)
    print(f"segments {len(segs)}  ridge px {sum(s['size'] for s in segs)}", flush=True)

    items = []
    for f in holdout.all_folds():
        items.extend(sigma.measure(field, segs, f))
    table = sigma.sigma_table(items)
    p = table["pooled"]
    print(f"sigma pooled n={table['n_matched']} median={p['median']:.2f} rms={p['rms']:.2f} px",
          flush=True)

    cat_d = distance_transform_edt(~grid.catalogue()).astype(np.float32)
    folds = holdout.all_folds()
    budgets = [int(b) for b in args.budgets.split(",")]
    spacings = [int(s) for s in args.spacings.split(",")]

    out = dict(protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
               threshold=args.threshold, min_px=args.min_px, dti0=DTI0,
               cat_margin=args.cat_margin, budgets=budgets, spacings=spacings,
               sigma_pooled=p, n_segments=len(segs), runs=[], budgets_sweep=[])
    vectors = {}
    for sp in spacings:
        raw, hist, rows = build_support(field, segs, table, DTI0, sp)
        screened = raw & (cat_d >= args.cat_margin) & grid.footprint()
        rank = field["mag"]
        for b in budgets:
            dots = RBS.greedy_isolated(screened, rank, b, RBS.MIN_SEP)
            n = int(dots.sum())
            pooled, per_fold, agg = score_folds(dots, folds)
            out["runs"].append(dict(along_spacing=sp, budget=b, n_dots=n,
                                    raw_px=int(raw.sum()), screened_px=int(screened.sum()),
                                    holdout_dti=pooled, per_fold=per_fold,
                                    tp=agg["tp"], fp=agg["fp"], n_truth=agg["n_truth"],
                                    line_hist={str(k): v for k, v in hist.items()}))
            vectors[(sp, b)] = np.array([per_fold[k] for k in sorted(per_fold)])
            print(f"[spacing {sp}] budget {b:6d} -> {n:6d} dots | HOLDOUT-DTI {pooled:.6f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
        del raw, screened

    # paired block bootstrap between spacings at the largest common budget
    common = max(set(budgets))
    if len(spacings) >= 2:
        for a, b in zip(spacings, spacings[1:]):
            if (a, common) in vectors and (b, common) in vectors:
                out.setdefault("paired", []).append(
                    dict(a=f"spacing{a}", b=f"spacing{b}", budget=common,
                         **paired_bootstrap(vectors[(a, common)], vectors[(b, common)])))

    # marginal credit of the next dot, from the spacing-1 curve (the metric's own rule)
    s1 = sorted([r for r in out["runs"] if r["along_spacing"] == 1], key=lambda r: r["n_dots"])
    for prev, cur in zip(s1, s1[1:]):
        d_tp = cur["tp"] - prev["tp"]
        d_s = cur["n_dots"] - prev["n_dots"]
        if d_s > 0:
            out["budgets_sweep"].append(dict(from_dots=prev["n_dots"], to_dots=cur["n_dots"],
                                             marginal_credit=d_tp / d_s,
                                             break_even=metric.ALPHA * DTI0,
                                             at_dti=cur["holdout_dti"]))

    EVID.mkdir(parents=True, exist_ok=True)
    f = EVID / "equal_budget.json"
    f.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", f, f"({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
