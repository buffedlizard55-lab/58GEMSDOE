#!/usr/bin/env python3
"""Re-derive the delivered candidate's HOLDOUT-DTI with the SHARED metric path.

``main`` declares ``src/gems58w/`` archived: the active shared tools are
``gems57.metric`` / ``gems57.evaluate_holdout`` / ``gems57.submission_writer``.
Session 3 measured its numbers with the exact metric inside ``gems58w``, so this
script answers the only question that matters for those receipts: **does the
shared implementation give the same number?**

Three comparisons, all on the bytes actually delivered:

1. per fold and pooled: ``gems58w.metric.dti_binary`` (what the receipt records)
   against ``gems57.metric.dti_binary`` and ``gems57.metric.dti_exact``;
2. the literal O(|G|*|P|) transcription ``gems57.metric.dti_bruteforce`` against
   the shared fast path on a bounded tile, which is the unit-test oracle for the
   published equations;
3. the recorded pooled value in ``evidence/ribbon/emission.json``.

Nothing is re-emitted and no slot is touched. Writes
``evidence/ribbon/shared_metric_crosscheck.json``.

    PYTHONPATH=src python3 scripts/crosscheck_shared_metric.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import metric as shared            # noqa: E402
from gems58w import grid, holdout              # noqa: E402
from gems58w import metric as lane             # noqa: E402

def _current_candidate() -> Path:
    """The candidate named by the current emission receipt, else the session-3 file."""
    try:
        rec = json.loads((ROOT / "evidence/ribbon/emission.json").read_text())
        p = ROOT / rec["file"]
        if p.is_file():
            return p
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    return ROOT / "docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif"


CANDIDATE = _current_candidate()
OUT = ROOT / "evidence/ribbon/shared_metric_crosscheck.json"
TOL = 1e-12


def pooled_from(terms: list[dict]) -> float:
    tp = sum(t["tp"] for t in terms)
    fp = sum(t["fp"] for t in terms)
    fn = sum(t["fn"] for t in terms)
    return float(tp / (tp + shared.ALPHA * fp + shared.BETA * fn + shared.EPS))


def tile_oracle(dots: np.ndarray, fold, side: int = 120) -> dict:
    """Brute-force vs fast path on a bounded tile that actually contains truth."""
    ys, xs = np.nonzero(fold.withhold & fold.valid & ~fold.known)
    if ys.size == 0:
        return {"skipped": "no withheld truth in this fold"}
    cy, cx = int(np.median(ys)), int(np.median(xs))
    y0, y1 = max(0, cy - side // 2), min(dots.shape[0], cy + side // 2)
    x0, x1 = max(0, cx - side // 2), min(dots.shape[1], cx + side // 2)
    sl = (slice(y0, y1), slice(x0, x1))
    pred = np.where(dots[sl] > 0, 1.0, 0.0)
    truth = fold.withhold[sl] & fold.valid[sl] & ~fold.known[sl]
    fast = shared.dti_exact(pred, truth)
    slow = shared.dti_bruteforce(pred, truth)
    return dict(window=[int(y0), int(y1), int(x0), int(x1)],
                n_truth=int(truth.sum()), n_dots=int((pred > 0).sum()),
                fast_dti=fast["dti"], bruteforce_dti=slow["dti"],
                abs_delta=abs(fast["dti"] - slow["dti"]),
                tp_delta=abs(fast["tp"] - slow["tp"]),
                fp_delta=abs(fast["fp"] - slow["fp"]),
                fn_delta=abs(fast["fn"] - slow["fn"]))


def main() -> int:
    with rasterio.open(CANDIDATE) as src:
        band = src.read(1)
    fp = grid.footprint() if callable(grid.footprint) else grid.footprint
    dots = np.where(np.isfinite(band) & fp, np.nan_to_num(band, nan=0.0), 0.0) > 0
    folds = holdout.all_folds()

    rows, lane_terms, shared_terms, exact_terms = [], [], [], []
    for f in folds:
        a = lane.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        b = shared.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        c = shared.dti_exact(np.where(dots, 1.0, 0.0), f.withhold, valid=f.valid, known=f.known)
        lane_terms.append(dict(tp=a.tp, fp=a.fp, fn=a.fn))
        shared_terms.append(dict(tp=b["tp"], fp=b["fp"], fn=b["fn"]))
        exact_terms.append(dict(tp=c["tp"], fp=c["fp"], fn=c["fn"]))
        rows.append(dict(fold=f.name, lane_gems58w=a.dti, shared_gems57_binary=b["dti"],
                         shared_gems57_exact=c["dti"],
                         abs_delta_binary=abs(a.dti - b["dti"]),
                         abs_delta_exact=abs(a.dti - c["dti"]),
                         n_truth=a.n_truth, n_dots=int((dots & f.valid & ~f.known).sum()),
                         tile_oracle=tile_oracle(dots, f)))

    pooled_lane = pooled_from(lane_terms)
    pooled_shared = pooled_from(shared_terms)
    pooled_exact = pooled_from(exact_terms)

    recorded = {}
    try:
        recorded = json.loads((ROOT / "evidence/ribbon/emission.json").read_text())
    except (OSError, json.JSONDecodeError):
        pass
    rec_ho = recorded.get("holdout_dti", {}) or {}
    rec_pooled = rec_ho.get("pooled")
    rec_per_fold = rec_ho.get("per_fold", {}) or {}

    deltas = [max(r["abs_delta_binary"], r["abs_delta_exact"]) for r in rows]
    tile_deltas = [r["tile_oracle"].get("abs_delta", 0.0) for r in rows
                   if "abs_delta" in r["tile_oracle"]]
    receipt_delta = abs(pooled_shared - float(rec_pooled)) if rec_pooled is not None else None
    per_fold_receipt = {r["fold"]: abs(r["shared_gems57_binary"] - float(rec_per_fold[r["fold"]]))
                        for r in rows if r["fold"] in rec_per_fold}

    ok = (max(deltas) < TOL and pooled_delta_ok(pooled_lane, pooled_shared, pooled_exact)
          and max(tile_deltas, default=0.0) < 1e-9
          and (receipt_delta is None or receipt_delta < 1e-9)
          and all(v < 1e-9 for v in per_fold_receipt.values()))

    out = dict(
        evidence_class="HOLDOUT-DTI",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        purpose=("Re-derive the delivered candidate's HOLDOUT-DTI with the shared gems57 metric, "
                 "because main has archived the gems58w path that produced the original receipt."),
        candidate=str(CANDIDATE.relative_to(ROOT)),
        candidate_sha256=recorded.get("sha256"),
        n_dots=int(dots.sum()),
        protocol=holdout.PROTOCOL,
        lane_evaluator=lane.EVALUATOR_VERSION,
        shared_evaluator="gems57.metric (dti_binary, dti_exact, dti_bruteforce)",
        per_fold=rows,
        pooled=dict(lane_gems58w=pooled_lane, shared_gems57_binary=pooled_shared,
                    shared_gems57_exact=pooled_exact,
                    recorded_in_emission_json=rec_pooled,
                    abs_delta_lane_vs_shared=abs(pooled_lane - pooled_shared),
                    abs_delta_shared_vs_recorded=receipt_delta,
                    per_fold_abs_delta_vs_recorded=per_fold_receipt),
        tolerance=TOL,
        verdict=("AGREE" if ok else "DISAGREE"),
        interpretation=(
            "The shared gems57 implementation reproduces the archived gems58w numbers to within "
            f"{max(deltas):.3e} per fold and {abs(pooled_lane - pooled_shared):.3e} pooled, and the "
            "literal brute-force transcription of the published equations reproduces the shared fast "
            f"path to within {max(tile_deltas, default=0.0):.3e} on a bounded tile. The reported "
            "HOLDOUT-DTI is therefore a property of the official metric, not of the archived copy "
            "that computed it. This says nothing about whether the number is a good forecast: the "
            "withheld truth is catalogue truth (IR-58-02) and no organizer receipt exists."
            if ok else
            "The shared and archived implementations disagree; every HOLDOUT-DTI published from the "
            "gems58w path must be treated as unverified until this is resolved."),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"[crosscheck] verdict {out['verdict']}")
    for r in rows:
        print(f"  fold {r['fold']}: gems58w {r['lane_gems58w']:.9f} | gems57 {r['shared_gems57_binary']:.9f}"
              f" | delta {r['abs_delta_binary']:.2e} | tile oracle delta "
              f"{r['tile_oracle'].get('abs_delta', float('nan')):.2e}")
    print(f"  pooled: gems58w {pooled_lane:.9f} | gems57 {pooled_shared:.9f} | recorded {rec_pooled}"
          f" | delta {abs(pooled_lane - pooled_shared):.2e}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0 if ok else 2


def pooled_delta_ok(a: float, b: float, c: float) -> bool:
    return max(abs(a - b), abs(a - c), abs(b - c)) < TOL


if __name__ == "__main__":
    raise SystemExit(main())
