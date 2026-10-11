#!/usr/bin/env python3
"""Render current session-7 status pages from the artifact-specific audit and run card.

This deliberately replaces stale session-5/session-6 front-page narratives. It
renders the negative result and never produces a TIFF, score, slot, or clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD_PATH = ROOT / "evidence/58gemsdoe_unique_ribbon/run_card.json"
AUDIT_PATH = ROOT / "evidence/58gemsdoe_unique_ribbon/audit.json"
CSS_PATH = DOCS / "assets/site.css"


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read required current evidence {path.relative_to(ROOT)}: {exc}")


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_data() -> tuple[dict, dict, Path]:
    card = load(CARD_PATH)
    audit = load(AUDIT_PATH)
    artifact = card.get("artifact_file")
    if not artifact:
        raise SystemExit("current session-7 run card has no artifact_file")
    tif = (ROOT / str(artifact)).resolve()
    if not tif.is_file():
        raise SystemExit(f"current review-only TIFF is missing: {artifact}")
    actual_sha = sha256_file(tif)
    if actual_sha != card.get("raster_sha256") or actual_sha != audit.get("artifact_sha256"):
        raise SystemExit(f"current TIFF SHA-256 does not match the run card and audit: {actual_sha}")
    final = (((audit.get("correlation_overlap_vs_registry") or {}).get("final_dots") or {})
             .get("witness_measurement", {}) or {})
    if final.get("direct_current_file_measurement") is not True:
        raise SystemExit("direct current-file witness measurement is absent; refusing to render an inferred overlap as measured")
    if card.get("verdict") != "negative" or card.get("stop_required") is not True:
        raise SystemExit("current session-7 card no longer records the required negative stop")
    return card, audit, tif


def gate_rows(card: dict, audit: dict) -> list[dict]:
    overlap = ((audit.get("correlation_overlap_vs_registry") or {}).get("final_dots") or {})
    final = overlap.get("witness_measurement", {}) or {}
    fmt_ok = audit.get("format_pass") is True
    pre_status = ((audit.get("correlation_overlap_vs_registry") or {})
                  .get("preplacement_surface", {}) or {}).get("status", "NOT MEASURED")
    freshness = ((card.get("correlation_overlap_vs_registry") or {})
                 .get("inventory", {}) or {}).get("current_inventory_freshness", "BLOCKED")
    holdout = card.get("holdout_dti", {}) or {}
    validator = card.get("validator", {}) or {}
    leakage = card.get("leakage_canary", {}) or {}
    measured = final.get("observed_candidate_dot_overlap_within_3_px")
    measured_text = f"{float(measured):.4f}" if measured is not None else "NOT MEASURED"
    threshold = final.get("literal_overlap_threshold")
    threshold_text = f"{float(threshold):.2f}" if threshold is not None else "not recorded"
    return [
        {"id": "FORMAT", "name": "Local format/range audit", "ok": fmt_ok,
         "status": f"{audit.get('format_checks_passed')}/{audit.get('format_checks_total')} LOCAL-FILE-AUDIT checks pass; nodata metadata differs from sample"},
        {"id": "PREPLACEMENT", "name": "Pre-placement surface uniqueness", "ok": False,
         "status": pre_status},
        {"id": "FINAL_DOTS", "name": "Literal final-dot overlap within 3 px", "ok": False,
         "status": f"FAIL — overlap {measured_text} exceeds literal threshold {threshold_text}; stop required"},
        {"id": "INVENTORY", "name": "Fresh complete registry", "ok": False,
         "status": freshness},
        {"id": "G4", "name": "G4 — Promotion-grade feature-alone leakage canary", "ok": False,
         "status": leakage.get("status", "NOT RUN")},
        {"id": "G5", "name": "G5 — Buffered spatial HOLDOUT-DTI with defensible 95% CI", "ok": False,
         "status": holdout.get("status", "NOT MEASURED")},
        {"id": "SIGMA", "name": "Artifact-specific σ table and simulated class gain", "ok": False,
         "status": f"σ: {card.get('sigma_table', 'NOT MEASURED')}; gain: {card.get('simulated_gain_per_class', 'NOT MEASURED')}"},
        {"id": "PORTAL", "name": "Organizer/portal acceptance and score receipt", "ok": False,
         "status": f"{validator.get('portal_acceptance', 'NOT CONFIRMED')}; no hash-bound organizer receipt"},
    ]


def page(title: str, body: str, css_href: str = "assets/site.css") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — 58GEMSDOE</title>
<link rel="stylesheet" href="{esc(css_href)}">
<style>
.s7-alert{{border:2px solid #9d1515;border-left-width:9px;background:#fff4f4;border-radius:10px;padding:18px 20px;margin:18px 0}}
.s7-alert h2{{margin:.15rem 0 .55rem;color:#811010}}
.s7-badge{{display:inline-block;background:#a11212;color:white;font-weight:800;padding:.35rem .8rem;border-radius:999px}}
.s7-btn{{display:inline-block;background:#a11212;color:white;text-decoration:none;font-weight:700;padding:12px 18px;border-radius:8px;margin:5px 8px 5px 0}}
.s7-btn.secondary{{background:#41505f}}
.s7-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.s7-card{{border:1px solid #d4dce3;border-radius:9px;padding:14px;background:white}}
.s7-fail{{color:#a11212;font-weight:700}} .s7-pass{{color:#12703f;font-weight:700}}
.s7-small{{font-size:.9rem;color:#465360}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}} th,td{{border:1px solid #d7dee5;padding:8px;vertical-align:top;text-align:left}}
th{{background:#eef2f6}}
</style></head><body><main class="wrap">
<header><p><a href="index.html">58GEMSDOE current status</a> ·
<a href="downloads/index.html">all downloads</a> ·
<a href="IRREGULARITIES.md">irregularities</a> · <a href="SOURCES.md">sources</a></p>
<h1>{esc(title)}</h1></header>
{body}
<footer><hr><p class="s7-small">Rendered from the session-7 artifact audit and run card by
<code>scripts/build_session7_pages.py</code>. This page is a local project record, not an organizer decision.</p></footer>
</main></body></html>
"""


def common_banner(card: dict, audit: dict, tif: Path) -> str:
    artifact_rel = str(card["artifact_file"]).removeprefix("docs/")
    zip_rel = str(Path(artifact_rel).with_suffix(".zip"))
    overlap = (((audit.get("correlation_overlap_vs_registry") or {}).get("final_dots") or {})
               .get("witness_measurement", {}) or {})
    measured = overlap.get("observed_candidate_dot_overlap_within_3_px")
    measured_text = f"{float(measured):.4f}" if measured is not None else "NOT MEASURED"
    fmt_count = f"{audit.get('format_checks_passed')}/{audit.get('format_checks_total')}"
    return f"""<section class="s7-alert" role="alert" aria-labelledby="stop-title">
<span class="s7-badge">⛔ NOT OK TO SUBMIT — DO NOT SUBMIT</span>
<h2 id="stop-title">Review-only TIFF; literal uniqueness stop recorded</h2>
<p><code>{esc(tif.name)}</code> is available for local audit only. It is not a qualified or authorized
competition submission. Its final-dot overlap is <b>{esc(measured_text)}</b> within 3 px, above the active
literal 0.70 threshold. The pre-placement surface and current inventory clearance are not measured/
not cleared, and there is no HOLDOUT-DTI result for this artifact.</p>
<div>
<a class="s7-btn" href="{esc(artifact_rel)}" download>Download TIFF for audit only — DO NOT SUBMIT</a>
<a class="s7-btn secondary" href="{esc(zip_rel)}" download>Download one-TIFF ZIP — audit only</a>
<a class="s7-btn secondary" href="../evidence/58gemsdoe_unique_ribbon/audit.json">Audit receipt</a>
<a class="s7-btn secondary" href="../evidence/58gemsdoe_unique_ribbon/run_card.json">JSON run card</a>
</div>
<p class="s7-small">Raster SHA-256 <code>{esc(card.get('raster_sha256'))}</code> · {tif.stat().st_size:,} bytes ·
{esc(audit.get('positive_pixels_local_format_audit'))} positive pixels · {fmt_count} local checks pass only.</p>
</section>"""


def deep_edge_notice() -> str:
    """Session-7 deep-edge sigma-ribbon candidate (parallel lineage; evidence/gems61)."""
    card_path = ROOT / "evidence" / "gems61" / "run_card.json"
    if not card_path.is_file():
        return ""
    try:
        card = json.loads(card_path.read_text())
    except (OSError, json.JSONDecodeError):
        return ""
    tif = ROOT / str(card.get("raster", {}).get("path", ""))
    if not tif.is_file():
        return ""
    uni = card.get("uniqueness", {})
    readings = uni.get("readings_final") or uni.get("readings_pre_gap") or {}
    hold = card.get("holdout", {})
    a1 = (hold.get("A1_sigma_ribbon") or {}).get("dti")
    a0 = (hold.get("A0_single_line") or {}).get("dti")
    note = card.get("submission", {}).get("note", "")
    name = card.get("submission", {}).get("name", "")
    lit = readings.get("literal_overlap_firings", "?")
    return f"""<section class="s7-alert" role="alert">
<span class="s7-badge">⛔ NOT OK TO SUBMIT — DO NOT SUBMIT</span>
<h2>Parallel-lane session-7 candidate: <code>{esc(tif.name)}</code></h2>
<p>H7-A deep-edge sigma-ribbon (step edges on <code>depth_to_base_surf</code>/<code>cond_surf</code>/<code>tc</code>,
relief-conditioned σ ribbons). Unique geometry, format-clean (all-finite float32 [0,1], no nodata tag),
<span class="s7-fail">literal uniqueness stop</span>: {esc(lit)} forward-overlap firings vs 694 witnesses
(worst 1.0). Not proof of copying; decisive under the active rule. <b>Do not submit.</b></p>
<p>Measured evidence (labelled HOLDOUT-DTI, catalogue-recovery proxy, not a score): A1 σ-ribbon
{('%.5f' % a1) if a1 is not None else 'NOT MEASURED'} vs A0 single-line
{('%.5f' % a0) if a0 is not None else 'NOT MEASURED'}; canary CLEAN. Chance-corrected overlap
readings (rule A 0, rule B 0, rank correlation 0) are recorded beside the literal reading and do
not waive it.</p>
<div>
<a class="s7-btn" href="downloads/{esc(tif.name)}" download>Download TIFF for audit only — DO NOT SUBMIT</a>
<a class="s7-btn secondary" href="downloads/{esc(tif.with_suffix('.zip').name)}" download>One-TIFF ZIP — audit only</a>
<a class="s7-btn secondary" href="gems61.html">Deep-edge evidence page</a>
<a class="s7-btn secondary" href="downloads/gems61-run_card.json">JSON run card</a>
</div>
<p class="s7-small">Run-card verdict <b>{esc(card.get('verdict'))}</b> · name <code>{esc(name)}</code> ·
note <code>{esc(note)}</code> · slots used 0.</p>
</section>"""


def inherited_unreviewed_notice() -> str:
    """Warn if a separate artifact from a later base update is present."""
    name = "gems58-ml-binary-ridge-20261012T000000Z.tif"
    path = DOCS / "downloads" / name
    if not path.is_file():
        return ""
    return f"""<section class="s7-alert" role="alert">
<span class="s7-badge">⛔ UNREVIEWED ARTIFACT — NOT OK TO SUBMIT</span>
<p>A separate file, <code>{esc(name)}</code>, was added to the base branch after the session-7 review.
It was not generated, evaluated, or qualified in that review and is outside the fixed-surface ribbon-width
scope. Do not submit it or run its generation scripts. See the
<a href="downloads/index.html">per-file review-only index</a>.</p>
</section>"""


def build_index(card: dict, audit: dict, tif: Path) -> str:
    rows = []
    for gate in gate_rows(card, audit):
        state = "PASS — LOCAL ONLY" if gate["ok"] else "NOT CLEARED / FAILED"
        klass = "s7-pass" if gate["ok"] else "s7-fail"
        rows.append(f"<tr><td>{esc(gate['name'])}</td><td class=\"{klass}\">{state}</td><td>{esc(gate['status'])}</td></tr>")
    body = common_banner(card, audit, tif) + inherited_unreviewed_notice() + deep_edge_notice() + f"""
<section class="s7-grid">
<div class="s7-card"><h2>Current decision</h2><p><b>negative</b>. No experiment, slot, or upload
occurred in this review. A filename/download link is not permission to submit.</p>
<p>Current session guide: <a href="SUBMISSION_GUIDE.md">submission guide</a> ·
<a href="research/session7_review_20261011.md">full review</a>.</p></div>
<div class="s7-card"><h2>Top untested width hypothesis</h2><p>H58-U1: condition ribbon width on local relief around fixed existing topographic ridge
centerlines. Proposal only; not implemented, not measured. A width change cannot detect a fault that
the fixed ridge surface entirely missed.</p><p><a href="research/hypotheses_new.md">See ranked hypotheses and falsifiers</a>.</p></div>
<div class="s7-card"><h2>Reported 0.2778</h2><p><span class="s7-badge">PUBLIC-LEADERBOARD-SNAPSHOT</span>
The dated participant-row snapshot attributes 0.2778 to <code>extradr19</code>. It is not an
organizer-confirmed artifact score. No receipt/hash crosswalk ties it to GEMSDOE32 H33; its owner page
labels the H33 file unscored. The cause of the participant's result is unknown.</p><p><a href="research/why-02778.md">Attribution review</a> · <a href="LEADERBOARD.md">dated leaderboard record</a>.</p></div>
</section>
<h2>Current artifact gate matrix</h2>
<p>Evidence classes are kept separate: local validation, registry measurements, holdout evidence, and organizer results are not interchangeable.</p>
<table><thead><tr><th>Gate</th><th>Result</th><th>Evidence / limitation</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Key files</h2>
<ul>
<li><a href="SUBMISSION_GUIDE.md">Executive submission guide</a></li>
<li><a href="research/session7_review_20261011.md">Full session-7 review</a></li>
<li><a href="research/hypotheses_new.md">Ranked within-lane hypotheses</a></li>
<li><a href="SOURCES.md">Official/primary source register and limits</a></li>
<li><a href="IRREGULARITIES.md">Current blockers and corrections</a></li>
<li><a href="../FINAL_DELIVERABLE_SUMMARY.md">Final deliverable summary</a></li>
</ul>
<h2>Format audit scope</h2>
<p>The local 19/19 check covers one-band float32 encoding, sample-grid alignment, finite [0,1]
values, exact positive values, footprint/catalogue checks, and ZIP round trip. Candidate `nodata=null`
differs from sample `nodata=NaN`; its portal treatment is unconfirmed. This audit does not establish
unique status, holdout performance, score, or organizer acceptance.</p>
<p class="s7-small">Current witness comparison checked one hash-pinned raster directly. The earlier
703-raster inventory was complete only for its frozen scope and is not a current exhaustive
clearance. The literal stop is decisive; this page does not claim a fresh complete scan.</p>
"""
    return page("Current status — negative review", body)


def build_executive(card: dict, audit: dict, tif: Path) -> str:
    body = common_banner(card, audit, tif) + inherited_unreviewed_notice() + """
<h2>Executive decision</h2>
<p><b>Do not submit this TIFF.</b> The active literal rule stops it because more than 70% of its
positive pixels fall within 3 px of one prior registry raster. The observed current-file overlap is
1.0000. No chance-corrected exemption is used.</p>
<h2>What the 19/19 local format result means</h2>
<p>The local audit verified that the bytes on disk match the documented single-band float32 grid and
sample CRS/shape/transform, values are finite and in [0,1], positive values are exactly 1.0, and the
single-TIFF ZIP round trip succeeds. It did not check the portal. In particular the raster nodata
metadata is null while the sample metadata is NaN; organizer interpretation is unconfirmed.</p>
<h2>What is not known</h2>
<ul><li>Pre-placement surface uniqueness is NOT MEASURED.</li>
<li>Current registry freshness is BLOCKED_NOT_EXHAUSTIVE.</li>
<li><b>G4 — Promotion-grade feature-alone leakage canary:</b> FAIL / NOT RUN; no candidate-bound receipt exists.</li>
<li><b>G5 — Buffered spatial HOLDOUT-DTI with defensible 95% CI:</b> FAIL / NOT MEASURED; no evaluator, withheld-positive count, protocol, or reportable interval is bound to this raster.</li>
<li>σ and simulated class gain are NOT MEASURED.</li>
<li>No organizer score or portal acceptance receipt exists.</li></ul>
<h2>Before any future submission</h2>
<p>See the <a href="SUBMISSION_GUIDE.md">full submission guide</a>. The current literal stop means no
experiment or replacement candidate is authorized under this review. No slot has been selected.</p>
<h2>Attribution of 0.2778</h2>
<p><b>PUBLIC-LEADERBOARD-SNAPSHOT:</b> the dated participant-row observation ties 0.2778 to
<code>extradr19</code>. It is not an organizer-confirmed artifact score. No artifact hash or receipt
connects it to H33; the cause of the participant's result is unknown. See
<a href="research/why-02778.md">the attribution review</a>.</p>
"""
    return page("Executive review — not a submission approval", body)


def build_submit(card: dict, audit: dict, tif: Path) -> str:
    rows = []
    for gate in gate_rows(card, audit):
        rows.append(f"<tr><td>{esc(gate['name'])}</td><td class=\"s7-fail\">{esc('LOCAL PASS ONLY' if gate['ok'] else 'STOP / NOT CLEARED')}</td><td>{esc(gate['status'])}</td></tr>")
    body = common_banner(card, audit, tif) + inherited_unreviewed_notice() + f"""
<h2>Submission checklist — stopped</h2>
<p>The required qualification gates are not all satisfied. Do not choose a competition slot or
upload this artifact.</p>
<table><thead><tr><th>Required item</th><th>Decision</th><th>Record</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>A local format pass is not proof of a valid portal upload. Local format validation is not portal acceptance. There is no organizer receipt/hash crosswalk for this artifact. The reported portal `[0,1]` error has
no candidate-bound response or receipt in this repository, so its cause is unknown. Candidate nodata
metadata also differs from the sample and has not been tested at the portal.</p>
<h2>Evidence/reporting rules</h2>
<ul><li>Report a model number only as HOLDOUT-DTI with the shared evaluator/version, protocol,
withheld-positive count, and a defensible 95% CI.</li>
<li>Call a competition score ORGANIZER-CONFIRMED only when a receipt/hash crosswalk identifies this
exact raster.</li>
<li>Do not use a public participant-board row as this artifact's score.</li>
<li>Use shared <code>gems57.evaluate_holdout</code> and
<code>gems57.submission_writer</code>; do not fork them.</li></ul>
<p><b>It is not an organizer acceptance, and it is not a score.</b> No upload or slot selection is authorized by this guide.</p>
<p>Read the <a href="../PROMPT.md">standing prompt</a>,
<a href="research/session7_review_20261011.md">session-7 review</a>, and
<a href="SOURCES.md">source register</a>.</p>
"""
    return page("Submission checklist — blocked", body)


def build_evidence(card: dict, audit: dict, tif: Path) -> str:
    body = common_banner(card, audit, tif) + inherited_unreviewed_notice() + f"""
<h2>Bound evidence</h2>
<ul><li>Current run card: <a href="../evidence/58gemsdoe_unique_ribbon/run_card.json">JSON</a>.</li>
<li>Independent audit receipt: <a href="../evidence/58gemsdoe_unique_ribbon/audit.json">JSON</a>.</li>
<li>Feature-stack restoration/pin record: <a href="../evidence/feature_stack_restore_20261011.json">JSON</a>; owner mirror integrity only.</li>
<li>Download metadata: <a href="downloads/{esc(tif.with_suffix('.json').name)}">JSON</a>.</li></ul>
<p>Artifact size {tif.stat().st_size:,} bytes; raster SHA-256 <code>{esc(card.get('raster_sha256'))}</code>;
decoded pixel SHA-256 <code>{esc(card.get('decoded_prediction_sha256'))}</code>.</p>
<p>Verdict: <b>negative</b>; final-dot literal overlap stop: <b>1.0000 &gt; 0.70</b>; current inventory freshness
is blocked; holdout is not measured. No organizer score receipt exists.</p>
"""
    return page("Session-7 evidence index", body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail unless rendered files match the current evidence")
    args = ap.parse_args()
    card, audit, tif = audit_data()
    gates = gate_rows(card, audit)
    site_card = {
        "evidence_class": "SITE-STATUS-SUMMARY",
        "source_run_card": "evidence/58gemsdoe_unique_ribbon/run_card.json",
        "source_audit": "evidence/58gemsdoe_unique_ribbon/audit.json",
        "site_verdict": "NOT_OK_TO_SUBMIT",
        "verdict": "negative",
        "verdict_reason": "Literal final-dot overlap within 3 px is 1.0000, exceeding 0.70; stop required.",
        "artifact_file": card["artifact_file"],
        "submission_name": card.get("submission_name"),
        "raster_sha256": card.get("raster_sha256"),
        "slots_used": 0,
        "experiments_this_review": 0,
        "site_gates": gates,
    }
    outputs = {
        DOCS / "index.html": build_index(card, audit, tif),
        DOCS / "executive-summary.html": build_executive(card, audit, tif),
        DOCS / "submit.html": build_submit(card, audit, tif),
        DOCS / "evidence.html": build_evidence(card, audit, tif),
        DOCS / "RUN_CARD.json": json.dumps(site_card, indent=2) + "\n",
    }
    if args.check:
        errors = [str(path.relative_to(ROOT)) for path, content in outputs.items()
                  if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if errors:
            print("current session-7 site is stale: " + ", ".join(errors))
            return 1
        print("current session-7 pages match the negative run card")
        return 0
    DOCS.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print("Rendered current session-7 pages: docs/index.html, executive-summary.html, submit.html, evidence.html, RUN_CARD.json")
    print("Verdict: negative; no candidate is cleared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
