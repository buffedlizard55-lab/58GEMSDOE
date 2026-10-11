#!/usr/bin/env python3
"""Build a fail-closed status card and GitHub Pages UX from recorded evidence.

A local validator pass is never treated as uniqueness clearance, a score, or
organizer acceptance. Status can become OK_TO_SUBMIT only when current buffered
holdout evidence, both literal registry phases, a current inventory, and the
local format preflight all pass. The selector/weekly-slot step is always separate.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"
TIF_REL = "docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif"


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def fmt(value, digits=4):
    if value is None:
        return "not measured"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _receipt_for(uniq: dict) -> dict:
    candidate = uniq.get("my_file")
    if candidate:
        p = ROOT / candidate
        if p.suffix.lower() == ".tif":
            receipt = load_json(p.with_suffix(".json"))
            if receipt:
                return receipt
    receipts = sorted(DL.glob("*.json"))
    for p in receipts:
        d = load_json(p)
        if d.get("file", "").endswith(".tif") and "ribbon" in d.get("file", ""):
            return d
    return {}


def receipt_file_matches(receipt: dict) -> bool:
    name = receipt.get("file")
    expected_sha = receipt.get("sha256")
    if not name or not expected_sha:
        return False
    path = DL / Path(name).name
    try:
        return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha
    except OSError:
        return False


def validated_holdout_result(e2: dict) -> dict:
    """Return only a promotion-labelled score with the full reporting contract."""
    result = e2.get("promotion_grade_result", {})
    if not isinstance(result, dict):
        return {}
    ci95 = result.get("ci95")
    valid = (
        e2.get("promotion_grade") is True
        and result.get("evidence_class") == "HOLDOUT-DTI"
        and result.get("evaluator_version") == "gems57-pooled-hide-v2"
        and isinstance(result.get("ci_method"), str) and bool(result.get("ci_method"))
        and isinstance(result.get("withheld_positive_pixels"), int)
        and result.get("withheld_positive_pixels", 0) > 0
        and isinstance(result.get("dti"), (int, float))
        and math.isfinite(float(result.get("dti", float("nan"))))
        and 0 <= float(result.get("dti", -1)) <= 1
        and isinstance(ci95, (list, tuple)) and len(ci95) == 2
        and all(isinstance(v, (int, float)) and math.isfinite(float(v)) for v in ci95)
        and 0 <= float(ci95[0]) <= float(ci95[1]) <= 1
    )
    return result if valid else {}


def validated_sigma_table(e1: dict) -> list[dict]:
    """Return only a current buffered holdout sigma table with finite values."""
    rows = e1.get("promotion_grade_sigma_table")
    if (e1.get("promotion_grade") is not True
            or e1.get("buffered_whole_component_context_used") is not True
            or not isinstance(rows, list) or not rows):
        return []
    if any(not isinstance(row, dict) for row in rows):
        return []
    for row in rows:
        sigma = row.get("sigma_px")
        n_matched = row.get("n_matched")
        if (row.get("evidence_class") != "HOLDOUT-STRUCTURE"
                or not row.get("block") or not row.get("ridge_type")
                or not isinstance(sigma, (int, float)) or not math.isfinite(float(sigma)) or float(sigma) < 0
                or not isinstance(n_matched, int) or n_matched < 0):
            return []
    return rows


def validated_per_class_gains(e2: dict) -> dict:
    """Return per-class gains only with an exact evaluator, positive count and valid CI."""
    result = validated_holdout_result(e2)
    gains = result.get("per_class_gains", {})
    if not isinstance(gains, dict) or not gains or any(not isinstance(v, dict) for v in gains.values()):
        return {}
    for item in gains.values():
        ci95 = item.get("ci95")
        gain = item.get("gain")
        if (item.get("evidence_class") != "HOLDOUT-DTI"
                or item.get("evaluator_version") != "gems57-pooled-hide-v2"
                or not isinstance(item.get("ci_method"), str) or not item.get("ci_method")
                or not isinstance(item.get("withheld_positive_pixels"), int)
                or item.get("withheld_positive_pixels", 0) <= 0
                or not isinstance(gain, (int, float)) or not math.isfinite(float(gain)) or not -1 <= float(gain) <= 1
                or not isinstance(ci95, (list, tuple)) or len(ci95) != 2
                or not all(isinstance(v, (int, float)) and math.isfinite(float(v)) for v in ci95)
                or not -1 <= float(ci95[0]) <= float(ci95[1]) <= 1):
            return {}
    return gains


def qualification_gaps(e1: dict, e2: dict, uniq: dict,
                       freshness: dict, receipt: dict) -> list[str]:
    """Return explicit unmet gates; fail closed when evidence is absent/stale."""
    gaps = []
    holdout = validated_holdout_result(e2)
    if not holdout:
        gaps.append("No current promotion-grade outer-block HOLDOUT-DTI with the required evaluator version, withheld-positive count, and valid 95% CI; legacy E2 is an oracle/selection diagnostic.")
    if e1.get("promotion_grade") is True and not validated_sigma_table(e1):
        gaps.append("A current training-only, buffered HOLDOUT-STRUCTURE sigma table is not complete.")
    if holdout and not validated_per_class_gains(e2):
        gaps.append("Per-class HOLDOUT-DTI gains with evaluator, withheld-positive count, and valid 95% CIs are not recorded.")
    canary = e1.get("leakage_canary", {})
    if not isinstance(canary, dict):
        canary = {}
    canary_aucs = canary.get("max_auc_by_type", {})
    canary_values_valid = (
        isinstance(canary_aucs, dict) and bool(canary_aucs)
        and all(isinstance(v, (int, float)) and math.isfinite(float(v)) and 0 <= float(v) <= 1
                for v in canary_aucs.values())
    )
    if not canary_values_valid:
        gaps.append("The current feature-alone leakage canary is missing, non-finite, or lacks per-feature AUC values.")
    elif any(float(v) > 0.90 for v in canary_aucs.values()):
        gaps.append("At least one feature-alone leakage canary exceeds AUC 0.90; treat it as leakage until disproven.")
    if (e1.get("promotion_grade") is not True
            or e1.get("buffered_whole_component_context_used") is not True
            or not canary_values_valid):
        gaps.append("No current buffered-fold feature-alone leakage-canary record is marked promotion-grade.")
    if not freshness.get("fresh_current_inventory", False):
        gaps.append("Registry inventory is stale/incomplete for current public repository trees.")
    rho_limit = float(uniq.get("rho_limit", 0.90))
    overlap_limit = float(uniq.get("overlap_limit", 0.70))
    surface = uniq.get("preplacement_surface_gate", {})
    if not isinstance(surface, dict):
        surface = {}
    if surface.get("passed") is not True:
        gaps.append("The candidate-specific pre-placement surface gate has not passed on a current inventory.")
    final = uniq.get("final_dot_gate", {})
    if not isinstance(final, dict):
        final = {}
    phase_results = (("pre-placement surface", surface), ("final dots", final))
    for phase_name, phase in phase_results:
        rho = phase.get("worst_spearman_full_footprint", phase.get("worst_rho"))
        if rho is None and phase_name == "final dots":
            rho = uniq.get("worst_spearman_full_footprint")
        limit = float(phase.get("rho_limit", rho_limit))
        if rho is not None and float(rho) > limit:
            gaps.append(f"The {phase_name} rank-correlation gate fails literally: rho {float(rho):.3f} > {limit:.2f}.")
        overlap = phase.get("worst_dot_overlap", phase.get("worst_overlap"))
        if overlap is None and phase_name == "final dots":
            overlap = uniq.get("worst_dot_overlap")
        limit = float(phase.get("overlap_limit", overlap_limit))
        if overlap is not None and float(overlap) > limit:
            gaps.append(f"The {phase_name} literal-dot gate fails: overlap {float(overlap):.3f} > {limit:.2f}.")
    overlap = final.get("worst_dot_overlap", uniq.get("worst_dot_overlap"))
    limit = float(final.get("overlap_limit", overlap_limit))
    if final.get("passed") is not True and (overlap is None or float(overlap) <= limit):
        gaps.append("The final-dot gate has not passed on a current inventory.")
    if uniq.get("unique") is not True:
        gaps.append("The frozen registry audit is negative; a byte/pixel-unique file is not sufficient to clear the literal lane gates.")
    if receipt.get("promotion_grade") is not True:
        gaps.append("The current raster receipt is marked diagnostic/non-promotion-grade.")
    if not receipt_file_matches(receipt):
        gaps.append("The raster file is missing or its bytes do not match the recorded receipt SHA256.")
    submission_name = receipt.get("submission_name", "")
    if not submission_name or len(submission_name) > 140:
        gaps.append("A non-empty submission name within the 140-character limit is not recorded.")
    note = receipt.get("note", "")
    if not note or len(note) > 140:
        gaps.append("The saved submission note is missing or exceeds the 140-character platform limit.")
    validator = receipt.get("validator", {})
    if validator.get("all_checks_passed") is not True:
        gaps.append("The recorded local format/range preflight is missing or failed.")
    return gaps


def build_run_card() -> dict:
    e1 = load_json(EV / "ribbon_e1_sigma.json")
    e2 = load_json(EV / "ribbon_e2_arms.json")
    uniq = load_json(EV / "ribbon_uniqueness.json")
    freshness = load_json(EV / "registry_freshness_audit.json")
    receipt = _receipt_for(uniq)
    validator = receipt.get("validator", {})
    note = receipt.get("note", "")
    gaps = qualification_gaps(e1, e2, uniq, freshness, receipt)
    ok = not gaps
    current_dots = uniq.get("my_dots")
    holdout_result = validated_holdout_result(e2)
    if holdout_result:
        holdout = {
            "status": "MEASURED",
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": holdout_result["evaluator_version"],
            "withheld_positive_pixels": holdout_result["withheld_positive_pixels"],
            "dti": holdout_result["dti"],
            "ci95": holdout_result["ci95"],
            "ci_method": holdout_result.get("ci_method"),
        }
    else:
        holdout = {
            "status": "NOT MEASURED for the current buffered/nested instrument",
            "evidence_class": "NOT A HOLDOUT-DTI CLAIM",
            "evaluator_version_required": "gems57-pooled-hide-v2",
            "withheld_positive_pixels": None,
            "dti": None,
            "ci95": None,
            "legacy_evidence_files": ["evidence/ribbon_e1_sigma.json", "evidence/ribbon_e2_arms.json"],
            "legacy_caveat": "Prior E2 is same-cell truth-selected, unbuffered and has an invalid repeated-block bootstrap; do not report it as promotion-grade evidence.",
        }
    sigma_table = validated_sigma_table(e1)
    per_class_gains = validated_per_class_gains(e2)
    surface_gate = uniq.get("preplacement_surface_gate", {
        "status": "NOT_RUN_FOR_THIS_CANDIDATE",
        "passed": False,
        "legacy_surface_report_not_reusable": "registry/uniqueness_surface_pre-placement_summary.json",
    })
    final_gate = uniq.get("final_dot_gate", {
        "status": "FROZEN_SCAN_FAILURE_AND_CURRENT_SCOPE_INCOMPLETE",
        "passed": False,
        "worst_dot_overlap": uniq.get("worst_dot_overlap"),
        "overlap_limit": uniq.get("overlap_limit", 0.70),
        "witness": uniq.get("worst_overlap_submission"),
    })
    card = {
        "run_card_version": "2.0",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lane": "ribbon only — emission width matched to measured localization error",
        "submission_status": "OK_TO_SUBMIT" if ok else "NOT_OK_TO_SUBMIT",
        "human_readable_status": "OK TO SUBMIT — SELECTOR STILL SEPARATE" if ok else "NOT OK TO SUBMIT — DO NOT SUBMIT",
        "hypothesis": "Visible-only catalogue and independent mapped-fault ridge axes may locate uncatalogued faults with a measurable across-strike localization error; ribbon width is tied to that error.",
        "mechanism": "Fit sigma by source/block on training-only spatial blocks, then emit 1.0-valued dots in a parallel ribbon at 3-pixel along-axis stride; score with exact pooled DTI and promote only after nested outer-block validation.",
        "named_non_fault_process_that_could_mimic_it": "Digitizing error and map generalization; lithologic contacts and alluvial/graben edges; roads, drainage lineaments, or survey striping aligned with candidate ridges.",
        "holdout": holdout,
        "localization_sigma_table": {
            "evidence_class": "HOLDOUT-STRUCTURE",
            "status": "MEASURED on current buffered training blocks" if sigma_table else "NOT MEASURED for the current promotion-grade buffered/nested instrument",
            "rows": sigma_table or None,
            "legacy_evidence_file": "evidence/ribbon_e1_sigma.json",
            "legacy_values_reportable": False,
        },
        "per_class_holdout_gains": {
            "evidence_class": "HOLDOUT-DTI" if per_class_gains else "NOT A REPORTABLE HOLDOUT-DTI CLAIM",
            "status": "MEASURED" if per_class_gains else "NOT MEASURED for current promotion-grade nested outer blocks",
            "rows": per_class_gains or None,
            "legacy_evidence_file": "evidence/ribbon_e2_arms.json",
            "legacy_values_reportable": False,
        },
        "leakage_canary": {
            "status": "NOT CLEARED FOR CURRENT BUFFERED INSTRUMENT",
            "threshold_auc": 0.90,
            "current_evidence": None,
            "legacy_record": "evidence/ribbon_e1_sigma.json (not promotion-grade for the revised split)",
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT (frozen snapshot only)",
            "snapshot_generated_utc": freshness.get("frozen_snapshot_generated_utc"),
            "repositories_in_frozen_snapshot": freshness.get("frozen_repositories_scanned"),
            "rasters_in_frozen_snapshot": freshness.get("frozen_unique_raster_count"),
            "current_inventory_complete": freshness.get("fresh_current_inventory", False),
            "freshness_audit": "evidence/registry_freshness_audit.json",
            "rho_limit": uniq.get("rho_limit", 0.90),
            "worst_spearman_full_footprint": uniq.get("worst_spearman_full_footprint"),
            "literal_overlap_limit": uniq.get("overlap_limit", 0.70),
            "candidate_dots": current_dots,
            "frozen_worst_dot_overlap": uniq.get("worst_dot_overlap"),
            "frozen_overlap_witness": uniq.get("worst_overlap_submission"),
            "preplacement_surface_gate": surface_gate,
            "final_dot_gate": final_gate,
        },
        "raster_sha256": receipt.get("sha256", uniq.get("candidate_file_sha256")),
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-PREFLIGHT; NOT ORGANIZER-CONFIRMED",
            "all_checks_passed": validator.get("all_checks_passed"),
            "checks": validator.get("checks"),
            "meta": validator.get("meta"),
            "caveat": "Internal all-finite/zero-outside policy is not organizer acceptance; template nodata semantics remain an open issue.",
        },
        "submission_name": receipt.get("submission_name"),
        "submission_note": note,
        "submission_note_chars": len(note),
        "selector_action": "NOT RUN; no weekly slot selected",
        "qualification_gaps": gaps,
        "verdict": "promote" if ok else "negative",
        "verdict_note": "Qualified candidates still require the separate selector step; slots are never selected by this build script." if ok else "Negative: one or more explicit holdout, registry, or format gates is not cleared. Do not upload or select a slot.",
    }
    (EV / "run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (ROOT / "docs" / "RUN_CARD.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return card


def build_site(card: dict) -> None:
    uniq = load_json(EV / "ribbon_uniqueness.json")
    freshness = load_json(EV / "registry_freshness_audit.json")
    receipt = _receipt_for(uniq)
    e1 = load_json(EV / "ribbon_e1_sigma.json")
    e2 = load_json(EV / "ribbon_e2_arms.json")
    tif = Path(receipt.get("file", TIF_REL)).name
    zip_name = Path(receipt.get("zip_file", tif.replace(".tif", ".zip"))).name
    status = html.escape(card["human_readable_status"])
    reasons = "".join(f"<li>{html.escape(x)}</li>" for x in card["qualification_gaps"])
    note = html.escape(card.get("submission_note", ""))
    sha = html.escape(card.get("raster_sha256") or "not recorded")
    overlap = uniq.get("worst_dot_overlap")
    rho = uniq.get("worst_spearman_full_footprint")
    witness = html.escape(str(uniq.get("worst_overlap_submission", "not identified")))
    validator_ok = bool(receipt.get("validator", {}).get("all_checks_passed"))
    status_color = "#a11212" if card["submission_status"] != "OK_TO_SUBMIT" else "#0a7d33"
    local_validation = "PASS under the internal local format/range policy" if validator_ok else "NOT PASSED"
    current_scope = "NOT CURRENT / INCOMPLETE" if not freshness.get("fresh_current_inventory") else "current inventory recorded"
    withheld = e2.get("withheld_positive_pixels")
    legacy_n = "recorded, but invalid for promotion" if withheld is not None else "no buffered result yet"
    note_chars = card.get("submission_note_chars", 0)
    generated = html.escape(card["generated_utc"])
    ready = card["submission_status"] == "OK_TO_SUBMIT"
    artifact_heading = ("Qualified candidate — local gates clear; final selector remains separate"
                        if ready else "Research artifact — not a cleared submission")
    download_label = ("Download qualified GeoTIFF — final selection remains separate"
                      if ready else "Download diagnostic TIFF (NOT CLEARED — DO NOT SUBMIT)")
    zip_warning = ("The ZIP is an optional audit copy; the submission-page instructions control the upload format."
                   if ready else "Do not upload either file or use a scored slot.")
    instruction_title = ("Next steps — final selector remains separate"
                         if ready else "Submission instructions — do not execute while red")
    first_step = ("Local qualification is recorded; a registered competitor must review the rules and live portal before acting."
                  if ready else "Wait until this page explicitly says <b>OK TO SUBMIT</b>; right now it says DO NOT SUBMIT.")
    note_label = ("Recorded submission note" if ready else "Suggested diagnostic note")
    summary_warning = (
        "<b>Local qualification is recorded, but this page never selects a weekly slot or establishes organizer acceptance.</b> Review the full evidence and rules before deciding."
        if ready else
        "<b>Do not upload or use a weekly slot.</b> The available TIFF is a diagnostic artifact. Its final-dot overlap exceeds the literal stop threshold in the frozen registry scan, that scan is stale, the current pre-placement phase is not cleared, and no promotion-grade buffered outer holdout was run."
    )

    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>58GEMSDOE — submission status</title><link rel="stylesheet" href="assets/site.css"></head><body>
<header><h1>58GEMSDOE — GEMS competition #306</h1><p>Ribbon lane only · rigorous qualification status</p></header>
<section class="submit-box" style="border-color:{status_color}">
  <div class="badge" style="background:{status_color}">{status}</div>
  <h2>{html.escape(artifact_heading)}</h2>
  <p><a class="big-btn" style="background:{status_color}" href="downloads/{html.escape(tif)}" download>{html.escape(download_label)}</a></p>
  <p>Optional one-TIFF ZIP: <a href="downloads/{html.escape(zip_name)}">{html.escape(zip_name)}</a>. {html.escape(zip_warning)}</p>
  <p><b>Raster SHA256:</b> <code>{sha}</code><br><b>Internal local format check:</b> {local_validation}. This does not establish uniqueness or organizer acceptance.</p>
  <h3>Blocking reasons</h3><ol>{reasons}</ol>
</section>
<section>
<h2>Gate evidence</h2>
<table><tr><th>Gate</th><th>Recorded result</th><th>Interpretation</th></tr>
<tr><td>Frozen registry scope</td><td>{freshness.get('frozen_unique_raster_count','not recorded')} rasters / {freshness.get('frozen_repositories_scanned','not recorded')} pinned repositories; {current_scope}</td><td>Historical snapshot only; see <code>evidence/registry_freshness_audit.json</code>.</td></tr>
<tr><td>Final-dot overlap</td><td>{fmt(overlap,3)} (limit {fmt(uniq.get('overlap_limit',0.70),2)}); witness {witness}</td><td>REGISTRY-MEASUREMENT, frozen scan; literal stop failure.</td></tr>
<tr><td>Worst Spearman ρ</td><td>{fmt(rho,3)} (limit {fmt(uniq.get('rho_limit',0.90),2)})</td><td>Below the correlation limit, but does not override the overlap failure.</td></tr>
<tr><td>Pre-placement surface</td><td>NOT CLEARED for this TIFF/current inventory</td><td>The existing historical surface report is for another build and is not reusable.</td></tr>
<tr><td>Buffered outer holdout</td><td>NOT MEASURED for the current instrument</td><td>The {legacy_n} old E2 output is not promotion-grade; no DTI is shown here.</td></tr>
<tr><td>Local format/range</td><td>{local_validation}</td><td>Internal check only; sample nodata semantics and portal acceptance remain unconfirmed.</td></tr>
<tr><td>Organizer receipt</td><td>None</td><td>No organizer score exists.</td></tr></table>
</section>
<section>
<h2>{html.escape(instruction_title)}</h2>
<ol>
<li>{first_step}</li>
<li>A registered competitor can review the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData submission page</a> and live instructions. {"Upload only after independent review of the recorded gates." if ready else "Do not upload this file while the status is red."}</li>
<li>The official rules allow up to three feedback submissions per week, but require choosing one final submission for both prize rounds. This build never runs the separate selector or spends a slot.</li>
<li>Record any submission receipt. Only its score is <b>ORGANIZER-CONFIRMED</b>. Disclose any generative-AI use in the solution narrative as required by the official rules.</li>
</ol>
<p><b>Deadline discrepancy:</b> the public homepage says Dec. 3, 2026, 11:59 p.m. UTC; the Sept. 2026 rules say 5:00 p.m. ET. Use the earlier cutoff until the organizer clarifies.</p>
<p>{note_label} ({note_chars} characters; verify against the live portal): <code>{note}</code></p>
</section>
<section><h2>Review links</h2><ul>
<li><a href="SUBMISSION_GUIDE.md">Full submission guide</a></li><li><a href="SOURCES.md">Official sources and availability checks</a></li>
<li><a href="IRREGULARITIES.md">Irregularities / review flags</a></li><li><a href="research/hypotheses_new.md">Ranked untested hypotheses</a></li>
<li><a href="evidence.html">Evidence status</a></li><li><a href="sources.html">Short source register</a></li>
<li><a href="AI_USAGE.md">Generative-AI use log (rules disclosure reference)</a></li>
</ul></section>
<footer>Generated {generated}. This is a local evidence status page. The builder never selects a slot or uploads, and cannot create an organizer receipt.</footer>
</body></html>"""
    (ROOT / "docs" / "index.html").write_text(index, encoding="utf-8")

    summary = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Executive summary — current GEMS decision</title><link rel="stylesheet" href="assets/site.css"></head><body>
<header><h1>Executive summary — current GEMS decision</h1></header>
<section class="submit-box" style="border-color:{status_color}"><div class="badge" style="background:{status_color}">{status}</div>
<p>{summary_warning}</p>
<p><a href="index.html">Return to status page</a> · <a href="SUBMISSION_GUIDE.md">Full guide</a></p></section>
<h2>What the number labels mean</h2><ul><li><b>HOLDOUT-DTI</b> requires a named shared evaluator/version, withheld-positive count and defensible 95% CI. No such result exists for the revised instrument.</li>
<li><b>ORGANIZER-CONFIRMED</b> requires a DrivenData receipt. None exists.</li><li>Local format/uniqueness evidence is not a performance score.</li></ul>
<h2>Submission steps when—and only when—the status changes</h2><ol><li>Confirm a complete current accessible-raster inventory.</li><li>Pass the pre-placement surface and final-dot literal gates.</li><li>Pass the buffered, nested outer-block holdout and feature-alone canaries.</li><li>Read the official rules and disclose generative-AI use if applicable.</li><li>Use the platform separately; select only one final submission across prize rounds. Save the receipt.</li></ol>
<footer>Generated {generated}. No leaderboard claim or organizer receipt.</footer></body></html>"""
    (ROOT / "docs" / "executive-summary.html").write_text(summary, encoding="utf-8")
    (ROOT / "docs" / "submit.html").write_text(summary.replace("Executive summary — current GEMS decision", "Submission guide — current GEMS decision"), encoding="utf-8")
    evidence_summary = (
        "Recorded promotion-grade holdout and registry gates are clear in the local evidence, but this page does not select a slot, upload, or confirm organizer acceptance."
        if ready else
        "The only registered final-dot comparison is the frozen 695-raster result, which fails the literal overlap gate. Current registry coverage and the candidate-specific pre-placement surface phase are not cleared. No current promotion-grade HOLDOUT-DTI is measured."
    )
    evidence_page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Evidence status</title><link rel="stylesheet" href="assets/site.css"></head><body>
<header><h1>Evidence status</h1></header><section class="submit-box" style="border-color:{status_color}"><div class="badge" style="background:{status_color}">{status}</div><p>{html.escape(evidence_summary)}</p><p>Run card: <a href="RUN_CARD.json">download the JSON run card</a>. Details: <a href="IRREGULARITIES.md">IRREGULARITIES.md</a>.</p></section><footer>Generated {generated}.</footer></body></html>"""
    (ROOT / "docs" / "evidence.html").write_text(evidence_page, encoding="utf-8")


def main() -> int:
    card = build_run_card()
    build_site(card)
    print(card["human_readable_status"])
    print("run card: evidence/run_card.json; site: docs/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
