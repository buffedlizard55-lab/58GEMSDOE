#!/usr/bin/env python3
"""Leakage canary: every feature tested ALONE against the withheld truth.

A single-feature AUC above 0.90 means the feature is a copy of the answer, not a
prediction of it, and every downstream number built on it is void until the leak
is named.  0.90 is the standing tripwire in the project prompt.

The AUC is the Mann-Whitney statistic, computed from the ranks of the feature
inside the fold's valid domain:

    AUC = (sum of positive ranks - n_pos (n_pos + 1) / 2) / (n_pos * n_neg)

which is exact, O(n log n) and needs no threshold.  Ties take average ranks.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems58w import holdout as g57        # noqa: E402
from gems58w import holdout as H58        # noqa: E402
from gems58w import extract as X58        # noqa: E402
from gems58w import features as F58        # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "evidence" / "ribbon_v3" / "leakage_canary.json"
LIMIT = 0.90


def auc(scores: np.ndarray, truth: np.ndarray) -> float:
    r = rankdata(scores)
    np_ = int(truth.sum())
    nn = int(truth.size - np_)
    if np_ == 0 or nn == 0:
        return float("nan")
    return float((r[truth].sum() - np_ * (np_ + 1) / 2.0) / (np_ * nn))


def main() -> None:
    t0 = time.time()
    bands = [b for b in F58.BANDS if b in set(F58.usable_bands())]
    stack = np.stack([np.asarray(F58.band(b), np.float32) for b in bands])
    print("bands tested:", len(bands), flush=True)
    field = X58.build()["mag"]
    print("feature stack", stack.shape, "belief field", field.shape, flush=True)

    rows = []
    worst = None
    n_leak = 0
    for fold in g57.folds():
        valid = fold.valid
        truth = fold.withhold & ~fold.known
        idx = np.flatnonzero(valid.reshape(-1))
        tv = truth.reshape(-1)[idx]
        np_ = int(tv.sum())
        for j in range(stack.shape[0]):
            v = stack[j].reshape(-1)[idx].astype(np.float64)
            v = np.where(np.isfinite(v), v, np.nan)
            good = np.isfinite(v)
            a = auc(v[good], tv[good].astype(bool))
            if np.isnan(a):
                continue
            rows.append(dict(protocol_fold=fold.name, feature=f"geodawn band {bands[j]}",
                             group="geodawn band", n=int(good.sum()), n_pos=np_, auc=round(a, 6)))
            worst = a if worst is None or a > worst else worst
            n_leak += int(a > LIMIT)
        v = field.reshape(-1)[idx].astype(np.float64)
        good = np.isfinite(v)
        a = auc(v[good], tv[good].astype(bool))
        rows.append(dict(protocol_fold=fold.name, feature="belief field h19-5", group="belief",
                         n=int(good.sum()), n_pos=np_, auc=round(a, 6)))
        worst = a if worst is None or a > worst else worst
        n_leak += int(a > LIMIT)
        print(f"  {fold.name}: worst so far {worst:.4f}", flush=True)

    leak = sorted(rows, key=lambda r: -r["auc"])
    rep = dict(
        evidence_class="HOLDOUT-DTI",
        evaluator_version="gems57-pooled-hide-v2",
        protocol="gems58-pooled-hide-v1",
        question="each feature tested alone against truth hidden by a 20 km physical block, "
                 "so a leak cannot be hidden by the model that uses it",
        n_features=stack.shape[0] + 1,
        n_folds=len(g57.folds()),
        leakage_limit=LIMIT,
        worst_auc=round(float(worst), 6) if worst is not None else None,
        n_leaking=n_leak,
        mean_auc=round(float(np.mean([r["auc"] for r in rows])), 6),
        leaks=[r for r in leak if r["auc"] > LIMIT],
        top10=leak[:10], seconds=round(time.time() - t0, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("n_features", "n_folds", "worst_auc", "n_leaking",
                                          "mean_auc", "seconds")}, indent=1))


if __name__ == "__main__":
    main()
