#!/usr/bin/env python3
"""E2b: score the EXACT live placement rule on the holdout (no accept test).

The live emission places ribbons blanket on all ridge segments (both types,
offsets +/-clip(round(sigma(block,type)),1,3), stride 3, dots at 1.0, masked to
the scored domain).  E2's arms used the exact accept test, which only a live
oracle could apply; this run scores the blanket rule the submission actually
uses, per fold cell, pooled exact DTI via the shared evaluator.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57.grid import load_grid
from gems57.holdout import FOLD_NAMES, build_holdout, quadrant_ids, score_cell
from gems57.metric import ALPHA, BETA, EPS

import ribbon_lane as rl


def pattern_for_sigma(sig: float) -> tuple[int, ...]:
    if not np.isfinite(sig) or sig < 0.5:
        return (0,)
    r = int(np.clip(round(float(sig)), 1, int(rl.MAX_SIGMA_PX)))
    return (-r, r) if r >= 1 else (0,)


def main() -> int:
    e1 = json.loads((ROOT / "evidence" / "ribbon_e1_sigma.json").read_text())
    grid = load_grid(ROOT / "data" / "bridge")
    sgmc = rl.sgmc_mask(ROOT, grid)
    ctx = build_holdout(grid, seeds=(20, 21), modes=("all",))
    quad = quadrant_ids(grid.footprint)

    sigma_live = {}
    for fold in range(4):
        for kind in rl.RIDGE_TYPES:
            vals = [row["per_type"][kind]["sigma_px"] for row in e1["sigma_by_cell"] if row["fold"] == fold]
            sigma_live[(fold, kind)] = float(np.mean(vals))

    H, W = grid.shape
    per_cell = {}
    tp = fp = fn = 0.0
    for cell in ctx.cells:
        visible = grid.catalogue & ~ctx.hidden_by_cell[cell.key]
        m = np.zeros(cell.k_dg.shape, bool)
        for kind in rl.RIDGE_TYPES:
            axes = rl.axis_mask_for_type(kind, visible, sgmc)
            for s in rl.axis_segments(kind, axes, cell.bbox):
                fold = int(np.bincount(quad[s.order[:, 0], s.order[:, 1]].clip(0, 3)).argmax())
                dots = rl._clip(rl.build_pattern_dots(s, pattern_for_sigma(sigma_live[(fold, kind)]),
                                                      rl.STRIDE_PX), cell.k_dg.shape[0], cell.k_dg.shape[1])
                if len(dots):
                    dots = dots[cell.active[dots[:, 0], dots[:, 1]]]
                if len(dots):
                    m[dots[:, 0], dots[:, 1]] = True
        r = score_cell(cell, m)
        per_cell[cell.key] = dict(dti=r["dti"], dots=int(r["n_emitted"]))
        tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
        print(f"E2b {cell.key}: dots={r['n_emitted']} dti={r['dti']:.4f}", flush=True)
    pooled = float(tp / (tp + ALPHA * fp + BETA * fn + EPS))
    out = dict(
        experiment="E2b-live-rule-blanket",
        evidence_class="HOLDOUT-DTI",
        evaluator="gems57.holdout score_cell (shared, exact)",
        withheld_positive_pixels=int(sum(c.n_truth for c in ctx.cells)),
        pooled_dti=pooled, pooled_tp=tp, pooled_fp=fp, pooled_fn=fn,
        per_cell=per_cell,
        rule=dict(offsets="+/-clip(round(sigma),1,3)", stride_px=rl.STRIDE_PX,
                  note="blanket on all ridge segments; no accept test (live has no truth)"),
    )
    (ROOT / "evidence" / "ribbon_e2b_liverule.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"E2b pooled HOLDOUT-DTI = {pooled:.4f} (blanket live rule)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
