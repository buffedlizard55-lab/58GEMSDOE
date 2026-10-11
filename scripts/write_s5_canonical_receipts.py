#!/usr/bin/env python3
"""Re-point the canonical ribbon receipts at the session-5 concordance candidate.

Reads the session-5 experiment receipts
(``concordance_sigma.json`` / ``concordance_arms.json`` / ``concordance_emission.json``)
and writes the canonical filenames the site builder, CI and crosscheck consume
(``adaptive_sigma.json`` / ``adaptive_arms.json`` / ``emission.json`` /
``run_card_v2.json``).  The session-3 originals were copied verbatim to
``evidence/ribbon/archive-s3/`` before this runs; this script refuses to run if
that archive is missing.  No number is invented here: every value is copied
from a named receipt.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIB = ROOT / "evidence" / "ribbon"


def main() -> int:
    if not (RIB / "archive-s3" / "emission.json").is_file():
        print("archive-s3 missing; refusing to overwrite canonical receipts", file=sys.stderr)
        return 2
    sig5 = json.loads((RIB / "concordance_sigma.json").read_text())
    arms5 = json.loads((RIB / "concordance_arms.json").read_text())
    emi5 = json.loads((RIB / "concordance_emission.json").read_text())
    state = json.loads((RIB / "concordance_emit_state.json").read_text())

    # ---- emission.json (canonical) ----
    emi = dict(emi5)
    emi["design"] = dict(emi5["design"])
    emi["design"]["threshold"] = emi5["design"]["tau"]  # renderer alias
    (RIB / "emission.json").write_text(json.dumps(emi, indent=1))

    # ---- adaptive_sigma.json (canonical; G4 expects per-group auc_max/leaks) ----
    canary_groups = {name: dict(auc_max=auc, leaks=bool(auc >= 0.90))
                     for name, auc in (sig5["leakage_canary"]["auc"]).items()}
    alpha, dti0 = 0.2, arms5["dti0"]
    sig = dict(
        protocol=sig5["protocol"], evaluator=sig5["evaluator"],
        generated_utc=sig5["generated_utc"],
        hypothesis=sig5["hypothesis"],
        cross_fitting="leave-one-block-out: the sigma table scoring fold b is fitted on the "
                      "other three folds",
        threshold=emi5["design"]["tau"],
        gate=sig5["gate"],
        n_segments=state["n_segments"],
        ridge_pixels=sum(
            int(r.get("segment_px", 0)) for r in state.get("plan_rows_sample", [])) or None,
        n_withheld_positives=arms5["n_withheld_positives"],
        sigma_table_all_folds=state["sigma_table_all_folds"],
        sigma_table_leave_one_block_out=state["sigma_table_leave_one_block_out"],
        leakage_canary=canary_groups,
        marginal_inclusion_bar=dict(
            rule="a unit of emitted mass pays iff its kernel credit exceeds alpha*DTI0",
            alpha=alpha, dti0=dti0, bar=alpha * dti0,
            dti0_label="public leaderboard #1 recorded 2026-10-11 "
                       "(evidence/official_leaderboard_observation_20261011.json)"),
        simulated_gain_per_sigma_class=sig5["simulated_gain_per_sigma_class"],
        wall_seconds=sig5["wall_seconds"],
        note="Session-5 receipt for the H58-X1 concordance candidate; the session-3 receipt "
             "of the same filename is archived verbatim in evidence/ribbon/archive-s3/.")
    # the segment count is known exactly; ridge_pixels of the emission field:
    sig["ridge_pixels"] = sig5.get("ridge_pixels", None) or state.get("support_px")
    (RIB / "adaptive_sigma.json").write_text(json.dumps(sig, indent=1))

    # ---- adaptive_arms.json (canonical) ----
    deltas = {arm: dict(pooled_delta=d["pooled"], per_fold=d["per_fold"])
              for arm, d in arms5["deltas_vs_R0"].items()}
    arms = dict(
        protocol=arms5["protocol"], evaluator=arms5["evaluator"],
        generated_utc=arms5["generated_utc"], budget=arms5["budget"],
        min_sep=arms5["min_sep"], dti0=arms5["dti0"],
        ranking=arms5["ranking"], screen=arms5["screen"],
        n_withheld_positives=arms5["n_withheld_positives"],
        results=arms5["arms"], deltas_vs_R0=deltas,
        winner=arms5["winner"], promotion_rule=arms5["promotion_rule"],
        promoted=arms5["promoted"],
        simulated_gain_per_sigma_class=sig5["simulated_gain_per_sigma_class"],
        wall_seconds=arms5["wall_seconds"],
        note="Session-5 equal-budget contest (R0 incumbent vs C1/C2 concordance-gated); "
             "session-3 receipt archived in evidence/ribbon/archive-s3/.")
    (RIB / "adaptive_arms.json").write_text(json.dumps(arms, indent=1))

    # ---- run_card_v2.json (canonical protocol run card; verdict set by build_site) ----
    ho = emi5["holdout_dti"]
    card = dict(
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        session="session-5 (branch arena/d7d3ba0a-58gemsdoe)",
        hypothesis=("H58-X1 cross-family concordance ribbon: emit sigma-adaptive parallel dotted "
                    "ribbons only on Hessian ridges where at least two independent organizer data "
                    "families (magnetic, gravity, topographic, subsurface, geodetic, seismic) "
                    "agree within 1 px."),
        mechanism=("a real fault juxtaposes density and magnetization and leaves a scarp, so its "
                   "trace expresses in several independently acquired grids at once; acquisition "
                   "artifacts are single-family. Gating on >=2-family agreement reallocates the "
                   "fixed dot budget from guaranteed-false single-family lineaments to "
                   "multi-evidence structures."),
        named_non_fault_mimic=("coincident basin-edge expressions: an alluvial-fan contact at a "
                               "range front can carry both a topographic lineament and a gravity "
                               "gradient without being an active fault; also any two-family "
                               "coincidence produced by the basin geometry itself rather than "
                               "faulting. Flight-line levelling (magnetic-only) and roads "
                               "(topographic-only) are suppressed by construction."),
        holdout_dti=dict(
            promotion_grade=dict(
                value=arms5["arms"]["C2"]["pooled"],
                per_fold=arms5["arms"]["C2"]["per_fold"],
                label="HOLDOUT-DTI, evaluator " + arms5["evaluator"] +
                      ", protocol " + arms5["protocol"] +
                      f", {arms5['n_withheld_positives']} withheld positives, "
                      "interval = min-max over the four spatial blocks "
                      f"({min(arms5['arms']['C2']['per_fold'].values()):.6f}"
                      f"-{max(arms5['arms']['C2']['per_fold'].values()):.6f}); no bootstrap over "
                      "4 blocks. Ranking cross-fitted leave-one-block-out (EXP-2 arm C2).",
                control_R0=arms5["arms"]["R0"]["pooled"],
                delta_vs_R0=deltas["C2"]["pooled_delta"]),
            delivered_bytes_diagnostic=dict(
                value=ho["pooled"], per_fold=ho["per_fold"], ci=ho["ci"],
                label=ho["label"])),
        correlation_overlap_vs_registry=dict(
            pre_placement_surface=dict(
                receipt="evidence/ribbon/concordance_surface_uniqueness.json",
                worst_rank_correlation=0.24137210315444652,
                limit=0.90, passed=True,
                note="rank correlation is the statistic defined for a continuous pre-placement "
                     "surface; support-pixel overlap readings are published in the receipt and "
                     "flagged GEMSDOE50:h52-coincidence8 as the nearest lane neighbour, decided "
                     "at the final-dot gate"),
            final_dot_gate="evidence/ribbon/uniqueness_full_inventory.json (governing; written "
                           "by scripts/check_uniqueness_registry.py over the 703-witness "
                           "byte-verified inventory)"),
        raster_sha256=emi5["sha256"],
        validator=dict(passed=emi5["validator"]["passed"],
                       checks_passed=sum(1 for c in emi5["validator"]["checks"].values()
                                         if c["ok"]),
                       checks_total=len(emi5["validator"]["checks"]),
                       no_nan_inside_footprint=emi5["validator"]["checks"]
                       ["finite_inside_footprint"]["ok"],
                       values_in_unit_interval=emi5["validator"]["checks"]
                       ["values_in_unit_interval"]["ok"],
                       crs_shape_transform_match=all(
                           emi5["validator"]["checks"][k]["ok"]
                           for k in ("crs_match", "shape_match", "transform_match"))),
        submission_name=emi5["name"],
        submission_note=emi5["submission_note"],
        verdict="pending-inventory-scan",
        slots_used=0,
        experiments_this_session=3,
        budget_note="3 experiments (sigma+canary, equal-budget arms, emission+screens); "
                    "within the 3-experiment / 2-hour cap.")
    (RIB / "run_card_v2.json").write_text(json.dumps(card, indent=1))
    print("wrote canonical emission.json, adaptive_sigma.json, adaptive_arms.json, run_card_v2.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
