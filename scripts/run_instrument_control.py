#!/usr/bin/env python3
"""Instrument control: why the delivered file reads HOLDOUT-DTI 0, and proof the
geometry is sound.

The delivered file keeps every dot at least 3 px from *any* catalogue pixel.  The
hide-and-recover holdout scores only on catalogue pixels (its withheld truth *is*
catalogue), so that screen makes the holdout read exactly 0 **by construction**.
The number is a property of the screen, not of the geometry.

This script runs the same geometry with the screen relaxed to 1 px --- still
"zero dots on the mapped catalogue" --- and reports the exact HOLDOUT-DTI, so the
geometry has a non-zero holdout read-out.  It also re-scores the delivered file
with that read-out removed, to show the difference is the screen alone.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/run_instrument_control.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58 import extract, grid, holdout, metric, submission  # noqa: E402
from gems58.paths import evidence_dir, downloads_dir  # noqa: E402
from scripts.build_submission import greedy_isolated, ribbon_support  # noqa: E402

BUDGET = 38000
NAME = "gems58-ribbon-sigma168-w3-38000-M1-CONTROL-20261011T000000Z"


def score(dots, folds):
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0)
    for f in folds:
        r = metric.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        for k in ("tp", "fp", "fn", "n_truth"):
            agg[k] += getattr(r, k)
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    return float(agg["tp"] / den), per_fold, agg


def main() -> int:
    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, 0.6, min_px=8)
    cat_d = distance_transform_edt(~grid.catalogue()).astype(np.float32)
    fp = grid.footprint()
    ribbon = ribbon_support(field, segs, 3)

    rows = {}
    for margin in (0.0, 1.0, 3.0):
        screened = ribbon & (cat_d >= margin) & fp
        dots = greedy_isolated(screened, field["mag"], BUDGET, 1)
        pooled, per_fold, agg = score(dots, holdout.all_folds())
        v = cat_d[dots]
        rows[f"M{int(margin)}"] = dict(
            catalogue_margin_px=margin, n_dots=int(dots.sum()),
            on_catalogue=int((v <= 0.001).sum()),
            holdout_dti=pooled, holdout_dti_per_fold=per_fold,
            n_withheld_positives=int(agg["n_truth"]),
            tp=agg["tp"], fp=agg["fp"], fn=agg["fn"],
            catalogue_distance=dict(median_px=float(np.median(v)),
                                    frac_le3px=float((v <= 3).mean()),
                                    frac_le10px=float((v <= 10).mean())))
        print(f"[control] margin >= {margin:g}px | dots {int(dots.sum()):6d} | on-catalogue "
              f"{rows[f'M{int(margin)}']['on_catalogue']} | HOLDOUT-DTI {pooled:.6f}", flush=True)

    ctrl = rows["M1"]
    screened = ribbon & (cat_d >= 1.0) & fp
    dots = greedy_isolated(screened, field["mag"], BUDGET, 1)
    tif = downloads_dir() / f"{NAME}.tif"
    submission.write(tif, dots)
    val = submission.validate(tif)

    out = dict(
        purpose=("the delivered file's HOLDOUT-DTI is exactly 0 because its "
                 "catalogue-margin screen removes every dot from the holdout's "
                 "scoring domain; this control isolates the geometry"),
        delivered=None, rows=rows, control_file=str(tif),
        control_sha256=val["sha256"], control_validator_passed=val["passed"],
        control_n_positives=val["n_positives"],
        wall_seconds=round(time.time() - t0, 2),
    )
    card = json.loads((evidence_dir() / "run_card.json").read_text())
    out["delivered"] = dict(name=card["name"], sha256=card["raster_sha256"],
                            holdout_dti=card["holdout_dti"],
                            catalogue_margin_px=card["geometry"]["catalogue_margin_px"],
                            catalogue_distance_profile=card["catalogue_distance_profile"])
    (evidence_dir() / "instrument_control.json").write_text(json.dumps(out, indent=1, default=float))
    print("wrote evidence/instrument_control.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
