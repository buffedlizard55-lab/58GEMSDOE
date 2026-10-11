#!/usr/bin/env python3
"""EXP-1: measure the across-strike localisation error sigma(x) on the holdout.

Protocol ``gems58-pooled-hide-v1`` (see ``gems58w.holdout``).  Writes
``evidence/holdout_sigma.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/ribbon_run_holdout_sigma.py --threshold 0.8
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import extract, holdout, sigma  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402


def _n_components(mask):
    from scipy.ndimage import label as _label
    import numpy as _np
    _, n = _label(mask, structure=_np.ones((3, 3), int))
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--min-px", type=int, default=6)
    ap.add_argument("--fold", default=None)
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=args.min_px)
    folds = holdout.all_folds() if args.fold is None else holdout.folds(args.fold)
    per_fold, all_items = {}, []
    for f in folds:
        items = sigma.measure(field, segs, f)
        all_items.extend(items)
        tbl = sigma.sigma_table(items)
        per_fold[f.name] = dict(n_truth=f.n_truth, n_matched=tbl["n_matched"],
                                frac_withheld_components_matched=(
                                    tbl["n_matched"] / max(1, _n_components(f.withhold))),
                                pooled=tbl["pooled"], by_scale=tbl["by_scale"])
        med = tbl["pooled"]["median"] if tbl["pooled"] else float("nan")
        print(f"[{f.name}] withheld {f.n_truth:6d} px | matched components {tbl['n_matched']:4d} "
              f"| sigma median {med:.3f} px")

    table = sigma.sigma_table(all_items)
    print(json.dumps({k: table[k] for k in ("n_pairs", "pooled", "by_scale", "by_type")},
                     indent=1))
    out = dict(
        protocol=holdout.PROTOCOL, evaluator=holdout.EVALUATOR,
        threshold=args.threshold, scales=list(extract.SCALES), n_segments=len(segs),
        ridge_pixels=int(sum(s["size"] for s in segs)),
        n_withheld_positives_total=int(sum(f.n_truth for f in folds)),
        per_component=[i.as_dict() for i in all_items],
        folds=list(holdout.BLOCKS), per_fold=per_fold, table=table,
        wall_seconds=round(time.time() - t0, 2),
        note=("sigma is the RMS signed across-strike offset of a matched ridge "
              "segment from the withheld component's principal axis; HOLDOUT-DTI "
              "is reported separately in holdout_eval.json"),
    )
    p = evidence_dir() / "holdout_sigma.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
