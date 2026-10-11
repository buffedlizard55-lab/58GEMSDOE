#!/usr/bin/env python3
"""E3: gated ribbon emission through the shared fail-closed writer.

The script refuses to build without a manually reviewed, machine-readable
``evidence/ribbon_qualification.json`` proving current buffered/nested holdout,
leakage canary, complete accessible registry scope, pre-placement surface gate,
final-dot literal gate, and the exact decoded prediction fingerprint. This
prevents an experiment-only or stale registry result from releasing a TIFF.
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
import build_site as gate_validation

MAX_NAME = 140


def main() -> int:
    t0 = time.time()
    qpath = ROOT / "evidence" / "ribbon_qualification.json"
    if not qpath.is_file():
        print("BLOCKED: evidence/ribbon_qualification.json is missing; no TIFF will be emitted.", file=sys.stderr)
        return 2
    qualification = json.loads(qpath.read_text())
    required_gates = {
        "promotion_grade_holdout": qualification.get("promotion_grade_holdout", {}).get("passed") is True,
        "leakage_canary": qualification.get("leakage_canary", {}).get("passed") is True,
        "fresh_current_inventory": qualification.get("registry", {}).get("fresh_current_inventory") is True,
        "preplacement_surface_gate": qualification.get("preplacement_surface_gate", {}).get("passed") is True,
        "final_dot_gate": qualification.get("final_dot_gate", {}).get("passed") is True,
    }
    if qualification.get("submission_status") != "OK_TO_SUBMIT" or not all(required_gates.values()):
        failed = [k for k, passed in required_gates.items() if not passed]
        print(f"BLOCKED: qualification status/gates are not all clear: {failed or ['submission_status']}", file=sys.stderr)
        return 2
    e1 = json.loads((ROOT / "evidence" / "ribbon_e1_sigma.json").read_text())
    e2 = json.loads((ROOT / "evidence" / "ribbon_e2_arms.json").read_text())
    canary_aucs = e1.get("leakage_canary", {}).get("max_auc_by_type", {})
    canary_clear = (isinstance(canary_aucs, dict) and bool(canary_aucs)
                    and all(isinstance(v, (int, float)) and np.isfinite(v) and 0 <= v <= 0.90
                            for v in canary_aucs.values()))
    if (e1.get("promotion_grade") is not True
            or e1.get("buffered_whole_component_context_used") is not True
            or not gate_validation.validated_sigma_table(e1)
            or not canary_clear
            or not gate_validation.validated_holdout_result(e2)
            or not gate_validation.validated_per_class_gains(e2)):
        print("BLOCKED: E1/E2 lack the full buffered holdout, sigma, canary, score/CI and per-class evidence contract; no TIFF will be emitted.", file=sys.stderr)
        return 2

    grid = load_grid(ROOT / "data" / "bridge")
    sgmc = rl.sgmc_mask(ROOT, grid)
    quad = quadrant_ids(grid.footprint)

    # Use only the promotion-grade sigma table that passed the shared run-card validator.
    sigma_live: dict[tuple[int, str], float] = {}
    sigma_table_rows = []
    qualified_sigma_rows = gate_validation.validated_sigma_table(e1)
    for fold, name in enumerate(FOLD_NAMES):
        for kind in rl.RIDGE_TYPES:
            rows = [row for row in qualified_sigma_rows
                    if row["block"] == name and row["ridge_type"] == kind]
            if not rows:
                print(f"BLOCKED: no promotion-grade sigma row for {name}/{kind}; no TIFF will be emitted.", file=sys.stderr)
                return 2
            vals = [float(row["sigma_px"]) for row in rows]
            s = float(np.mean(vals))
            sigma_live[(fold, kind)] = s
            sigma_table_rows.append(dict(evidence_class="HOLDOUT-STRUCTURE",
                                         block=name, ridge_type=kind,
                                         sigma_px=s,
                                         n_matched=sum(int(row["n_matched"]) for row in rows)))
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

    # The gate receipt must apply to this exact decoded array, not a prior build.
    decoded_sha256 = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()
    if qualification.get("candidate_decoded_sha256") != decoded_sha256:
        print("BLOCKED: qualification fingerprint does not match this emission; no TIFF will be emitted.", file=sys.stderr)
        return 2

    # deterministic short id from the decoded prediction
    sid = decoded_sha256[:8]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"gems58-ribbon-sigma-fitted-{stamp}-{sid}-zeros"
    assert len(name) <= MAX_NAME
    note = ("H58b ribbon; localization-error width; dots at 1.0; qualified evidence attached; "
            "selector and weekly-slot decision remain separate.")[:140]
    assert len(note) <= 140

    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = write_submission(out_dir / f"{name}.tif", pred, ROOT / "data" / "official" / "sample_submission.tif",
                               grid.footprint, note=note, name=name, catalogue=grid.catalogue,
                               metadata=dict(
                                   lane="ribbon (emission width = measured localization error)",
                                   diagnostic_only=False,
                                   promotion_grade=True,
                                   qualification_artifact="evidence/ribbon_qualification.json",
                                   selector_action="not run; weekly-slot decision remains separate",
                                   evidence=dict(
                                       localization_sigma_table=sigma_table_rows,
                                       holdout_dti=e2["promotion_grade_result"],
                                       per_class_holdout_gains=e2["promotion_grade_result"]["per_class_gains"]),
                                   dots=int(n_dots), dots_by_type=dot_counts, segments_by_type=seg_counts,
                                   pattern_counts=pattern_counts,
                                   pattern_rule=dict(stride_px=rl.STRIDE_PX,
                                                     offsets="tight if sigma<0.5 else +/-clip(round(sigma),1,3)"),
                               ))
    print(f"wrote {name}.tif | sha256 {receipt['sha256']} | validator all_checks_passed="
          f"{receipt['validator']['all_checks_passed']}", flush=True)
    print(f"E3 done in {time.time()-t0:.0f}s", flush=True)
    return 0


def pattern_for_sigma(sig: float) -> tuple[int, ...]:
    """The lane's fitted rule: tight line when sigma < ~0.5 px, else +/-sigma."""
    if not np.isfinite(sig) or sig < 0.5:
        return (0,)
    r = int(np.clip(round(float(sig)), 1, int(rl.MAX_SIGMA_PX)))
    return (-r, r) if r >= 1 else (0,)


if __name__ == "__main__":
    raise SystemExit(main())
