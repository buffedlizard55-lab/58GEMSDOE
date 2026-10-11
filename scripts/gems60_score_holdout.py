#!/usr/bin/env python3
"""Score a delivered GeoTIFF on the shared buffered hide-and-recover holdout.

Instrument: ``gems57.holdout.build_buffered_holdout_context`` (seed 20, 20 % of the
catalogue withheld as whole components inside label-blind eroded quadrants, a 3 px
feature-context collar removed) scored with the shared exact DTI, alpha = 0.2,
beta = 0.8, 300 m triangular kernel.

What this number is *not*: the organiser scores the fault set that is **absent**
from the catalogue, while this instrument can only score recovery of the
*catalogue* itself.  The lane measured that proxy to be uncorrelated with live
leaderboard values (Spearman −0.037 over 34 score-bearing rasters), and this file
is deliberately off-catalogue, so the value belongs in the record as a labelled
HOLDOUT-DTI, never as a forecast.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import holdout as H            # noqa: E402
from gems57.grid import load_grid          # noqa: E402

EVALUATOR = "gems57-pooled-buffered-hide-v1 (holdout.build_buffered_holdout_context + holdout.evaluate)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tif")
    ap.add_argument("--seed", type=int, default=20)
    ap.add_argument("--hide-frac", type=float, default=0.20)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tif = Path(args.tif)
    t0 = time.time()
    grid = load_grid(ROOT / "data" / "bridge")
    ctx = H.build_buffered_holdout_context(grid, hide_frac=args.hide_frac, seeds=(args.seed,))
    with rasterio.open(tif) as src:
        arr = src.read(1).astype(np.float32)
    emitted = arr > args.threshold
    res = H.evaluate(emitted, ctx, cell_mode="all")

    n_truth = int(sum(c.n_truth for c in ctx.cells))
    folds = {k: dict(dti=float(v["dti"]), tp=float(v["tp"]), fp=float(v["fp"]),
                     fn=float(v["fn"]), n_truth=int(v["n_truth"]), n_emitted=int(v["n_emitted"]))
             for k, v in res["folds"].items()}
    dti_folds = [f["dti"] for f in folds.values()]
    lo, hi = H.wilson_ci(res["pooled_tp"], max(1e-9, n_truth))
    receipt = dict(
        evidence_class="HOLDOUT-DTI",
        label="HOLDOUT-DTI (catalogue recovery only; not a leaderboard forecast)",
        file=tif.name, sha256=None, generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        evaluator=EVALUATOR, protocol="buffered hide-and-recover, whole components, 3 px context collar",
        seed=args.seed, hide_frac=args.hide_frac, alpha=H.ALPHA, beta=H.BETA, kernel_radius_px=3.0,
        withheld_positive_pixels=n_truth,
        pooled_dti=float(res["pooled_dti"]),
        pooled_coverage=float(res["pooled_coverage"]),
        pooled_tp=float(res["pooled_tp"]), pooled_fp=float(res["pooled_fp"]), pooled_fn=float(res["pooled_fn"]),
        emitted_pixels=int(res["emitted_pixels"]),
        on_visible_catalogue=int(res["on_visible_catalogue"]),
        per_fold=folds,
        fold_dti_min=float(min(dti_folds)), fold_dti_max=float(max(dti_folds)),
        fold_dti_mean=float(np.mean(dti_folds)), fold_dti_sd=float(np.std(dti_folds)),
        coverage_wilson_95=[float(lo), float(hi)],
        ci_note=("a DTI is a ratio of kernel-weighted masses, not a binomial proportion, so no defensible "
                 "binomial CI exists for it; the four fold-level DTIs (this split contains one withhold per "
                 "quadrant) and the Wilson interval on the pooled coverage are reported instead"),
        caveat=("withheld truth is the mapped catalogue, while the competition scores the faults that are "
                "absent from the catalogue; this instrument is structurally blind to off-catalogue files "
                "(lane measurement: Spearman −0.037 between this proxy and live scores over 34 rasters)"),
        runtime_s=round(time.time() - t0, 1),
    )
    Path(args.out).write_text(json.dumps(receipt, indent=1) + "\n")
    print(f"file            : {tif.name}")
    print(f"withheld truth  : {n_truth} pixels")
    print(f"emitted         : {res['emitted_pixels']} pixels (on visible catalogue {res['on_visible_catalogue']})")
    print(f"pooled          : DTI {res['pooled_dti']:.6f}  coverage {res['pooled_coverage']:.6f}  "
          f"TPw {res['pooled_tp']:.1f}  FPw {res['pooled_fp']:.1f}  FNw {res['pooled_fn']:.1f}")
    print(f"per fold        : " + "  ".join(f"{k.split('_')[1]}={v['dti']:.4f}" for k, v in folds.items()))
    print(f"coverage 95% CI : [{lo:.4f}, {hi:.4f}] (Wilson, reference only)")
    print(f"wrote           : {args.out}  ({receipt['runtime_s']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
