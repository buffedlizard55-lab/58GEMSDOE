#!/usr/bin/env python3
"""Leakage canary: AUC of every single band against the withheld truth.

Protocol rule 4: test each feature alone on the holdout before trusting any result;
AUC above 0.90 means leakage until proven otherwise.  A feature that merely *is*
the withheld trace (or a smoothed copy of it) would show up here immediately.

Also runs the same test for the combined ridge field, which is what actually feeds
the emission.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/ribbon_run_leakage_canary.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import extract, features as F, grid, holdout  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402

THRESHOLD = 0.90


def auc(scores: np.ndarray, positive: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney), exact, with average ranks for ties."""
    order = np.argsort(scores, kind="stable")
    r = np.empty(scores.size, float)
    r[order] = np.arange(scores.size, dtype=float)
    s = scores[order]
    i = 0
    while i < s.size:
        j = i + 1
        while j < s.size and s[j] == s[i]:
            j += 1
        if j - i > 1:
            r[order[i:j]] = r[order[i:j]].mean()
        i = j
    n1 = int(positive.sum())
    n0 = int((~positive).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    return float((r[positive].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def main() -> int:
    fp = grid.footprint()
    folds = holdout.all_folds()
    rows = []
    for name in F.BANDS:
        a = F.band(name)
        aucs = []
        for f in folds:
            # sample to keep it cheap: the withheld truth and a random background
            rng = np.random.default_rng(58)
            pos = np.argwhere(f.withhold)
            bg = np.argwhere(fp & ~f.known & ~f.withhold)
            bg = bg[rng.choice(bg.shape[0], size=min(20000, bg.shape[0]), replace=False)]
            idx = np.vstack([pos, bg])
            v = a[idx[:, 0], idx[:, 1]]
            lbl = np.r_[np.ones(pos.shape[0], bool), np.zeros(bg.shape[0], bool)]
            ok = np.isfinite(v)
            aucs.append(auc(np.nan_to_num(v[ok]), lbl[ok]))
        m = float(np.nanmean(aucs))
        rows.append(dict(band=name, mean_auc=m, per_fold=[float(x) for x in aucs],
                         leaks=bool(m > THRESHOLD)))
        print(f"[canary] {name:22s} mean AUC {m:.4f} {'LEAK' if m > THRESHOLD else ''}", flush=True)

    field = extract.build()
    aucs = []
    for f in folds:
        rng = np.random.default_rng(58)
        pos = np.argwhere(f.withhold)
        bg = np.argwhere(fp & ~f.known & ~f.withhold)
        bg = bg[rng.choice(bg.shape[0], size=min(20000, bg.shape[0]), replace=False)]
        idx = np.vstack([pos, bg])
        v = field["mag"][idx[:, 0], idx[:, 1]]
        lbl = np.r_[np.ones(pos.shape[0], bool), np.zeros(bg.shape[0], bool)]
        aucs.append(auc(v, lbl))
    ridge_auc = float(np.nanmean(aucs))
    print(f"[canary] combined ridge field   mean AUC {ridge_auc:.4f} "
          f"{'LEAK' if ridge_auc > THRESHOLD else ''}", flush=True)

    out = dict(threshold=THRESHOLD, bands=rows, combined_ridge_field_auc=ridge_auc,
               combined_ridge_field_leaks=bool(ridge_auc > THRESHOLD),
               n_leaking_bands=sum(1 for r in rows if r["leaks"]),
               note=("AUC of a single band, or of the combined ridge field, at separating "
                     "withheld catalogue pixels from background. Values near 0.5 mean the "
                     "feature carries no withheld-trace information; values above 0.90 would "
                     "mean leakage until proven otherwise."))
    p = evidence_dir() / "leakage_canary.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
