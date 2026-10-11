#!/usr/bin/env python3
"""E3: build the live ribbon emission and package it with the fail-closed writer.

Live placement applies the holdout-fitted rule (E1 sigma table x E2 arm gains):
  - single tight dotted line where sigma < 0.5 px;
  - a parallel dotted ribbon about +/-sigma wide where sigma is 2-3 px
    (offsets +/-clip(round(sigma),1,3), along-line stride 3 px = kernel radius).
Ridge axes: skeleton of the FULL catalogue (cat-axis) and skeleton of
SGMC-minus-catalogue (sgmc-axis).  Dots are emitted at exactly 1.0, restricted
to the scored footprint and off the mapped catalogue (the writer refuses
positive mass on the catalogue).  Packaging: gems57.submission_writer
(validates in memory and on disk; .tif + .zip + .json receipt).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57.grid import load_grid
from gems57.holdout import FOLD_NAMES, quadrant_ids
from gems57.submission_writer import write_submission

import ribbon_lane as rl

MAX_NAME = 140


def main() -> int:
    t0 = time.time()
    e1 = json.loads((ROOT / "evidence" / "ribbon_e1_sigma.json").read_text())
    e2 = json.loads((ROOT / "evidence" / "ribbon_e2_arms.json").read_text())

    grid = load_grid(ROOT / "data" / "bridge")
    sgmc = rl.sgmc_mask(ROOT, grid)
    quad = quadrant_ids(grid.footprint)

    # fitted sigma per (fold, type): mean of the per-cell shrunk sigma over seeds
    sigma_live: dict[tuple[int, str], float] = {}
    sigma_table_rows = []
    for fold, name in enumerate(FOLD_NAMES):
        for kind in rl.RIDGE_TYPES:
            vals = [row["per_type"][kind]["sigma_px"] for row in e1["sigma_by_cell"] if row["fold"] == fold]
            s = float(np.mean(vals))
            sigma_live[(fold, kind)] = s
            sigma_table_rows.append(dict(block=name, ridge_type=kind,
                                         sigma_px=s,
                                         n_matched=sum(e1_sigma_n(row, kind) for row in e1["sigma_by_cell"] if row["fold"] == fold)))
    print("live sigma table:", {(FOLD_NAMES[f], k): round(v, 2) for (f, k), v in sigma_live.items()}, flush=True)

    # live ridge axes
    axes_cat = rl.clean_skeleton(grid.catalogue)
    axes_sgmc = rl.clean_skeleton(sgmc & ~grid.catalogue)
    H, W = grid.shape
    emitted = np.zeros(grid.shape, bool)
    seg_counts = {"cat-axis": 0, "sgmc-axis": 0}
    dot_counts = {"cat-axis": 0, "sgmc-axis": 0}
    pattern_counts: dict[str, int] = {}
    for kind, axes in (("cat-axis", axes_cat), ("sgmc-axis", axes_sgmc)):
        segs = rl.axis_segments(kind, axes, (slice(0, H), slice(0, W)))
        allowed = grid.footprint & ~grid.catalogue
        for s in segs:
            fold = int(np.bincount(quad[s.order[:, 0], s.order[:, 1]].clip(0, 3)).argmax())
            sig = sigma_live[(fold, kind)]
            offs = pattern_for_sigma(sig)
            dots = rl._clip(rl.build_pattern_dots(s, offs, rl.STRIDE_PX), H, W)
            if len(dots) == 0:
                continue
            dots = dots[allowed[dots[:, 0], dots[:, 1]]]
            if len(dots) == 0:
                continue
            emitted[dots[:, 0], dots[:, 1]] = True
            seg_counts[kind] += 1
            dot_counts[kind] += len(dots)
            name = "tight" if len(offs) == 1 else f"ribbon{len(offs)}o{max(abs(o) for o in offs)}"
            pattern_counts[f"{kind}|{name}"] = pattern_counts.get(f"{kind}|{name}", 0) + 1

    n_dots = int(emitted.sum())
    pred = np.where(emitted, 1.0, 0.0).astype(np.float32)
    print(f"emitted dots: {n_dots} ({dot_counts})", flush=True)

    # deterministic short id from the decoded prediction
    sid = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"gems58-ribbon-sigma-fitted-{stamp}-{sid}-zeros"
    assert len(name) <= MAX_NAME
    note = ("H58b ribbon lane: parallel dotted lines at fitted sigma 2.5-3.1 px; "
            "dots at 1.0; off-catalogue; holdout-validated vs tight baseline.")[:140]
    assert len(note) <= 140

    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = write_submission(out_dir / f"{name}.tif", pred, ROOT / "data" / "official" / "sample_submission.tif",
                               grid.footprint, note=note, name=name, catalogue=grid.catalogue,
                               metadata=dict(
                                   lane="ribbon (emission width = measured localization error)",
                                   evidence=dict(
                                       sigma_table=sigma_table_rows,
                                       e2_pooled=({a: e2["arms"][a]["pooled_dti"] for a in ("tight", "ribbon", "ribbon-pool")}),
                                       per_class_gains=e2["per_class_gains"],
                                       dti0_reference=e2["dti0_reference"]),
                                   dots=int(n_dots), dots_by_type=dot_counts, segments_by_type=seg_counts,
                                   pattern_counts=pattern_counts,
                                   pattern_rule=dict(stride_px=rl.STRIDE_PX,
                                                     offsets="tight if sigma<0.5 else +/-clip(round(sigma),1,3)"),
                               ))
    print(f"wrote {name}.tif | sha256 {receipt['sha256']} | validator all_checks_passed="
          f"{receipt['validator']['all_checks_passed']}", flush=True)
    print(f"E3 done in {time.time()-t0:.0f}s", flush=True)
    return 0


def e1_sigma_n(row: dict, kind: str) -> int:
    return int(row["per_type"][kind]["n_matched"])


def pattern_for_sigma(sig: float) -> tuple[int, ...]:
    """The lane's fitted rule: tight line when sigma < ~0.5 px, else +/-sigma."""
    if not np.isfinite(sig) or sig < 0.5:
        return (0,)
    r = int(np.clip(round(float(sig)), 1, int(rl.MAX_SIGMA_PX)))
    return (-r, r) if r >= 1 else (0,)


if __name__ == "__main__":
    raise SystemExit(main())
