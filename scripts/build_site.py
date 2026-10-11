#!/usr/bin/env python3
"""Build the ribbon-lane status site from evidence, using fail-closed gates.

All eligibility decisions are delegated to ``scripts/qualification_gates.py``;
this module only renders receipts and explanatory status. It does not waive a
literal uniqueness trigger, score a TIFF, or infer portal acceptance from a
local format check. Numeric model results are displayed only when the current
qualification receipt clears the shared HOLDOUT-DTI/reportable-interval gate.

Evidence classes remain distinct:

    ORGANIZER-CONFIRMED          exact artifact tied to an organizer receipt/hash crosswalk
    PUBLIC-LEADERBOARD-SNAPSHOT   dated participant row; never an artifact score by itself
    HOLDOUT-DTI                   shared evaluator, version, protocol, count, defensible 95% CI
    USER-REPORTED-SCORE / PROJECTION  historical context only, never organizer confirmation

    python3 scripts/build_site.py [--strict]
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from . import qualification_gates as current_gates
else:  # direct invocation: python scripts/build_site.py
    import qualification_gates as current_gates

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
RIB = EV / "ribbon"
DOCS = ROOT / "docs"
DL = DOCS / "downloads"

LEADER_DTI = 0.4133       # PUBLIC-LEADERBOARD-SNAPSHOT, not an artifact score
LEADER_WHO = "xiaofanhu (public leaderboard rank 1, observed 2026-10-11)"
DARD_DTI = 0.3195          # PUBLIC-LEADERBOARD-SNAPSHOT, observed rank 9 on 2026-10-11

EXTRA_CSS = """
<style>
.gates{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.6rem;margin:.8rem 0}
.gate{border:1px solid #d7dee6;border-left:5px solid #999;border-radius:8px;padding:.55rem .7rem;background:#fbfcfd}
.gate.pass{border-left-color:#1d7a45;background:#f2fbf5}
.gate.fail{border-left-color:#a11212;background:#fdf3f3}
.gate.info{border-left-color:#2f5f8f;background:#f5f9fc}
.gate h4{margin:0 0 .25rem;font-size:.95rem}
.gate p{margin:0;font-size:.83rem;color:#41505f}
.pill{display:inline-block;padding:.1em .55em;border-radius:999px;font-size:.76rem;font-weight:700;color:#fff}
.pill.pass{background:#1d7a45}.pill.fail{background:#a11212}.pill.info{background:#2f5f8f}.pill.warn{background:#8a6d1a}
.warn-box{border:1px solid #e0c46a;border-left:5px solid #8a6d1a;background:#fffbea;border-radius:8px;padding:.7rem .9rem;margin:.8rem 0}
.bad-box{border:1px solid #e0a3a3;border-left:5px solid #a11212;background:#fff6f6;border-radius:8px;padding:.7rem .9rem;margin:.8rem 0}
.ok-box{border:1px solid #9ed3b3;border-left:5px solid #1d7a45;background:#f4fcf7;border-radius:8px;padding:.7rem .9rem;margin:.8rem 0}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1rem}
.small{font-size:.85rem;color:#41505f}
.dlrow{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0}
.num{font-variant-numeric:tabular-nums}
nav a{margin-right:.9rem}
footer{margin-top:2rem;border-top:1px solid #d7dee6;padding-top:.6rem;font-size:.82rem;color:#41505f}
table{max-width:100%}
</style>
"""


def load(path: Path) -> dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return d if isinstance(d, dict) else {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(v, digits=4, dash="not measured"):
    if v is None:
        return dash
    try:
        f = float(v)
    except (TypeError, ValueError):
        return html.escape(str(v))
    if f != f:  # NaN
        return "undefined"
    return f"{f:.{digits}f}"


def esc(v) -> str:
    return html.escape(str(v)) if v is not None else ""


def table(head: list[str], rows: list[list], cls: str = "num") -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def label(kind: str) -> str:
    cls = {"ORGANIZER-CONFIRMED": "pass", "PUBLIC-LEADERBOARD-SNAPSHOT": "warn",
           "HOLDOUT-DTI": "info", "USER-REPORTED-SCORE": "warn",
           "PROJECTION": "warn"}.get(kind, "info")
    return f'<span class="pill {cls}">{html.escape(kind)}</span>'


# ------------------------------------------------------------------------ gates
# One shared evaluator owns both emission eligibility and the public status page.
# Do not re-implement, relax, or infer qualification gates in this presentation layer.
RHO_LIMIT = current_gates.RHO_LIMIT
OVERLAP_LIMIT = current_gates.OVERLAP_LIMIT
CANARY_LIMIT = current_gates.CANARY_LIMIT
HOLDOUT_EVALUATOR = current_gates.HOLDOUT_EVALUATOR
HOLDOUT_VERSION = current_gates.HOLDOUT_VERSION
REQUIRED_GATES = current_gates.REQUIRED_GATES


def evaluate_gates(emi: dict, sig: dict, inv: dict, tif: Path,
                   xcheck: dict | None = None, qualification: dict | None = None,
                   freshness: dict | None = None, *,
                   inventory_index_sha256: str | None = None,
                   inventory_receipt_sha256: str | None = None,
                   freshness_receipt_sha256: str | None = None) -> tuple[list[dict], bool]:
    """Delegate status evaluation to the shared fail-closed qualification contract."""
    return current_gates.evaluate_gates(
        emi, sig, inv, tif, xcheck, qualification, freshness,
        inventory_index_sha256=inventory_index_sha256,
        inventory_receipt_sha256=inventory_receipt_sha256,
        freshness_receipt_sha256=freshness_receipt_sha256,
    )


def page(title: str, body: str, nav_active: str = "") -> str:
    nav = [("index.html", "Status &amp; review"), ("executive-summary.html", "Research review"),
           ("submit.html", "Local file QA"), ("deliverable/index.html", "Sibling-lane deliverable"),
           ("sources.html", "Sources"), ("evidence.html", "Evidence index"),
           ("ribbon/index.html", "Ribbon lane archive")]
    parts = []
    for href, name in nav:
        style = ' style="font-weight:700"' if href == nav_active else ""
        parts.append(f'<a href="{href}"{style}>{name}</a>')
    links = " · ".join(parts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — 58GEMSDOE (GEMS competition #306)</title>
<link rel="stylesheet" href="assets/site.css">{EXTRA_CSS}</head><body>
<header><h1>58GEMSDOE — DOE GEMS competition #306</h1>
<p>Geothermal fault detection, northwestern Great Basin (NV) · ribbon lane · every figure on this
site is rendered from <code>evidence/**.json</code> at build time</p>
<nav class="small">{links}</nav></header>
{body}
<footer>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} by
<code>scripts/build_site.py</code>. No artifact-specific organizer receipt/hash crosswalk exists for
the current candidate. Public participant rows are labelled PUBLIC-LEADERBOARD-SNAPSHOT; model
results require HOLDOUT-DTI with evaluator/version, protocol, withheld-positive count, and a defensible
95% CI.</footer>
</body></html>"""


def gates_html(gates: list[dict]) -> str:
    out = ['<div class="gates">']
    for g in gates:
        if g.get("informational"):
            cls, pill = "info", "INFO — NOT AN ELIGIBILITY GATE"
        else:
            cls = "pass" if g["ok"] else "fail"
            pill = "PASS" if g["ok"] else "FAIL — REQUIRED"
        out.append(f'<div class="gate {cls}"><h4>{g["id"]} · {g["name"]} '
                   f'<span class="pill {cls}">{pill}</span></h4><p>{g["detail"]}</p></div>')
    out.append("</div>")
    return "".join(out)


def build_index(emi, card, arms, sig, inv, fit, sib_dir, sib_inv, gates, ok,
                *, qualification=None, freshness=None) -> str:
    """Current decision page. Numeric holdout results appear only when G5 qualifies them."""
    qualification = qualification or {}
    freshness = freshness or {}
    name = str(emi.get("name", "unknown-candidate"))
    validator = emi.get("validator", {}) or {}
    checks = validator.get("checks", {}) or {}
    n_pass = sum(1 for c in checks.values() if isinstance(c, dict) and c.get("ok") is True)
    gmap = {g.get("id"): g for g in gates}
    info = inv.get("informative_reading", {}) or {}
    literal_firings = info.get("overlap_firings", inv.get("duplicate_count"))
    checked = inv.get("registry_rasters_checked", inv.get("n_compared"))
    holdout_ok = bool(gmap.get("G5", {}).get("ok"))
    holdout = qualification.get("promotion_grade_holdout", {}) or {}
    if holdout_ok:
        score = holdout.get("pooled_dti", holdout.get("dti"))
        ci = holdout.get("ci95", holdout.get("ci"))
        n_withheld = holdout.get("withheld_positive_pixels", holdout.get("n_withheld_positives"))
        holdout_summary = (f"HOLDOUT-DTI {fmt(score, 6)} · evaluator "
                           f"<code>{esc(holdout.get('evaluator'))}</code> / "
                           f"<code>{esc(holdout.get('evaluator_version'))}</code> · "
                           f"{esc(n_withheld)} withheld positives · 95% CI {esc(ci)} · "
                           f"protocol <code>{esc(holdout.get('protocol'))}</code>")
    else:
        holdout_summary = ("HOLDOUT-DTI: <b>NOT MEASURED</b> under the current reportable protocol; "
                           "no valid shared-evaluator receipt and defensible 95% CI are bound to this candidate.")

    snapshot = load(EV / "official_leaderboard_observation_20261011_review.json")
    board_rows = snapshot.get("rows", []) or []
    board_by_name = {str(r.get("participant")): r for r in board_rows if isinstance(r, dict)}
    leader = board_rows[0] if board_rows else {"rank": 1, "participant": LEADER_WHO, "score": LEADER_DTI}
    dard = board_by_name.get("DARD", {"rank": 9, "participant": "DARD", "score": DARD_DTI})
    extradr = board_by_name.get("extradr19", {"rank": 23, "participant": "extradr19", "score": 0.2778})
    board_observed = snapshot.get("retrieval_time_utc") or snapshot.get("observed_date_utc", "2026-10-11")
    freshness_decision = freshness.get("decision", "MISSING")
    fresh_text = "CURRENT / EXHAUSTIVE" if freshness.get("fresh_current_inventory") is True else "BLOCKED — NOT EXHAUSTIVE"
    inventory_checked = checked if checked is not None else "unknown"
    candidate_sha = str(emi.get("sha256", "not recorded"))
    positives = validator.get("n_positives", "not recorded")
    file_bytes = validator.get("bytes", "not recorded")
    local_state = "PASS" if gmap.get("G1", {}).get("ok") else "FAIL"
    overall = "OK TO SUBMIT" if ok else "NOT OK TO SUBMIT — DO NOT SUBMIT"
    status_cls = "ok" if ok else ""
    current_link = f"downloads/{esc(name)}.tif"
    zip_link = f"downloads/{esc(name)}.zip"
    overlap_text = (f"The recorded final-dot scan has <b>{esc(literal_firings)}</b> literal &gt;70% "
                    f"forward-overlap triggers in a scan of <b>{esc(inventory_checked)}</b> indexed rasters; "
                    "any such trigger is a stop. The scan is a saved public-inventory snapshot, not a "
                    "current exhaustive registry. Its independent freshness audit is "
                    f"<b>{esc(freshness_decision)}</b> ({fresh_text}).")

    body = f"""
<section class="banner {status_cls}" role="alert">
  <h2>{overall}</h2>
  <p>This page uses <code>scripts/qualification_gates.py</code>, the same fail-closed evaluator
  used by the emission contract. The current artifact is a review-only download. A green local
  format preflight is not promotion clearance or portal acceptance.</p>
</section>
<section>
<h2>Current ribbon artifact</h2>
<p><code>{esc(name)}.tif</code> · SHA-256 <code>{esc(candidate_sha)}</code> ·
{esc(positives)} positive pixels · {esc(file_bytes)} bytes.</p>
<p><b>Local format preflight:</b> {local_state} ({n_pass}/{len(checks)} checks in its receipt).
This says nothing about portal acceptance. The reported portal [0, 1] rejection remains unresolved;
this repository has no portal payload or receipt bound to these bytes.</p>
<p><a class="button review" href="{current_link}" download>Download for review only — DO NOT SUBMIT</a>
<a class="button" href="{zip_link}" download>Download ZIP for review only — DO NOT SUBMIT</a>
<a href="downloads/index.html">All downloadable artifacts (each labelled separately)</a></p>
<p class="small">The hash and local checks identify these exact bytes; they do not establish organizer
acceptance, a competition score, current uniqueness, or submission eligibility.</p>
</section>
<section>
<h2>Fail-closed qualification gates</h2>
{gates_html(gates)}
<p class="small">Only G1, G2P, G3, G4, and G5 jointly determine pre-submission eligibility.
Informational receipts (G2, G5i, G6) cannot turn a required failure into a pass.
Qualification receipt: <a href="../evidence/ribbon_qualification.json"><code>evidence/ribbon_qualification.json</code></a>
— {"present" if (EV / "ribbon_qualification.json").is_file() else "MISSING"}.</p>
</section>
<section>
<h2>Why this is a stop</h2>
<p>{overlap_text}</p>
<p>The current literal protocol is rank correlation &gt;0.90 <b>or</b> more than 70% of candidate
dots within 3 px of any one witness. A chance correction, saturated witness, alternative overlap
direction, or prior RATIFIED-UNIQ-v1 reading cannot waive a literal trigger. See
<a href="REMAINING_WORK.md">remaining work</a> and
<a href="research/hypotheses_new.md">ranked, untried width hypotheses</a>.</p>
<p>Inventory freshness receipt: <a href="../evidence/registry_freshness_audit.json"><code>evidence/registry_freshness_audit.json</code></a>.
The scan covers its recorded snapshot only; it is not an organizer-wide inventory.</p>
</section>
<section>
<h2>Current score attribution — public board only</h2>
<p>Official public leaderboard observation on {esc(board_observed)}:
{label("PUBLIC-LEADERBOARD-SNAPSHOT")} rank {esc(leader.get("rank"))},
<code>{esc(leader.get("participant"))}</code>, {esc(leader.get("score"))};
DARD rank {esc(dard.get("rank"))}, {esc(dard.get("score"))};
<code>extradr19</code> rank {esc(extradr.get("rank"))}, {esc(extradr.get("score"))}.
These rows are a {label('PUBLIC-LEADERBOARD-SNAPSHOT')}, not <code>ORGANIZER-CONFIRMED</code>
artifact scores. The board is dynamic and has no TIFF-hash crosswalk. The 0.2778 row belongs to
<code>extradr19</code>; no receipt or hash crosswalk identifies it as a GEMSDOE32 H33 score. The H33
artifact remains unscored in the owner-maintained record; the reason for any participant's score
cannot be established from a row without the submission artifact and organizer receipt. See
<a href="LEADERBOARD.md">attribution review</a> and the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">official live board</a>.</p>
<p><b>This ribbon candidate's current reportable result:</b> {holdout_summary}</p>
<p>No organizer-confirmed score exists for this repository's artifact. Public leaderboard values are
not scores for this TIFF.</p>
</section>
<section>
<h2>Research decision and next work</h2>
<p>No new TIFF, experiment, holdout run, submission, or slot selection was performed in this review.
The current candidate is a negative result. The lead untried hypothesis is
<b>H58-U1, relief-conditioned width around the existing topographic ridge surface</b>; it is not
implemented or validated. Its physical mechanism, non-fault mimics, comparison with existing code,
three alternatives, expected uncertainty, and estimated costs are documented in
<a href="research/hypotheses_new.md">the ranked hypothesis review</a> and
<a href="research/session7_review_20261011.md">this research/status review</a>.</p>
<ol>
<li>Refresh and audit the public raster inventory; stop on any stale or incomplete result.</li>
<li>Restore the pinned organizer-provided 19-band feature stack. Its GitHub mirror pin establishes
integrity against that mirror, not organizer provenance.</li>
<li>Before placement or emission, screen the frozen candidate surface against the fresh inventory.
Only after clearance may the top hypothesis proceed to feature-alone leakage checks and the shared,
buffered spatial holdout.</li>
<li>Report HOLDOUT-DTI only with the shared evaluator/version, withheld-positive count, protocol,
and defensible 95% CI. Re-scan final dots and keep every artifact review-only unless all required
gates pass.</li>
</ol>
<p>Experiment budget used: <b>0/3</b>; slot selections: <b>0</b>. No slot is selected or recommended.</p>
</section>
<section>
<h2>Trusted source links</h2>
<ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem, DTI, and submission-format requirements</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">DrivenData dataset and fault-mapping context</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData public leaderboard (dynamic participant rows)</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE GEMS Official Rules (September 2026)</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN survey release</a></li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference-solution repository</a></li>
</ul>
<p class="small">Full source register: <a href="SOURCES.md">docs/SOURCES.md</a>. Evidence card:
<a href="RUN_CARD.json">docs/RUN_CARD.json</a>.</p>
</section>
"""
    return page("Status and research review", body, "index.html")


def build_executive_summary(emi, card, arms, sig, inv, gates, ok,
                            *, qualification=None, freshness=None) -> str:
    """Research/decision summary; never republish legacy diagnostic scores as current results."""
    qualification = qualification or {}
    freshness = freshness or {}
    name = str(emi.get("name", "unknown-candidate"))
    validator = emi.get("validator", {}) or {}
    checks = validator.get("checks", {}) or {}
    n_pass = sum(1 for c in checks.values() if isinstance(c, dict) and c.get("ok") is True)
    gmap = {g.get("id"): g for g in gates}
    inv_info = inv.get("informative_reading", {}) or {}
    firings = inv_info.get("overlap_firings", inv.get("duplicate_count", "not recorded"))
    count = inv.get("registry_rasters_checked", inv.get("n_compared", "unknown"))
    qualification_file = EV / "ribbon_qualification.json"
    freshness_decision = freshness.get("decision", "MISSING")
    holdout = qualification.get("promotion_grade_holdout", {}) or {}
    if gmap.get("G5", {}).get("ok"):
        holdout_text = (f"HOLDOUT-DTI {fmt(holdout.get('pooled_dti', holdout.get('dti')), 6)} · evaluator "
                        f"<code>{esc(holdout.get('evaluator'))}</code> / "
                        f"<code>{esc(holdout.get('evaluator_version'))}</code> · protocol "
                        f"<code>{esc(holdout.get('protocol'))}</code> · "
                        f"{esc(holdout.get('withheld_positive_pixels', holdout.get('n_withheld_positives')))} "
                        f"withheld positives · 95% CI {esc(holdout.get('ci95', holdout.get('ci')))}")
    else:
        holdout_text = ("<b>NOT MEASURED</b> as a promotion-grade HOLDOUT-DTI. No shared-evaluator, "
                        "candidate- and inventory-bound reportable receipt with defensible 95% CI exists.")
    overall = "OK TO SUBMIT" if ok else "NOT OK TO SUBMIT — DO NOT SUBMIT"
    freshness_label = "fresh inventory verified" if freshness.get("fresh_current_inventory") is True else "BLOCKED_NOT_EXHAUSTIVE"
    snapshot = load(EV / "official_leaderboard_observation_20261011_review.json")
    rows = snapshot.get("rows", []) or []
    selected = [r for r in rows if r.get("participant") in {"xiaofanhu", "DARD", "extradr19"}]
    row_text = "; ".join(
        f"rank {esc(r.get('rank'))} {esc(r.get('participant'))}: {esc(r.get('score'))}"
        for r in selected
    ) if selected else "No verified leaderboard snapshot is loaded."
    if selected:
        row_text += f" ({label('PUBLIC-LEADERBOARD-SNAPSHOT')}, dated {esc(snapshot.get('observed_date_utc'))})"

    body = f"""
<section class="banner" role="alert"><h2>{overall}</h2>
<p>The exact current TIFF is a local review artifact, not a submission recommendation.
No new TIFF, holdout experiment, submission, or slot selection was made in this review.</p></section>
<section><h2>Decision in brief</h2><ul>
<li><b>Candidate:</b> <code>{esc(name)}.tif</code>, SHA-256 <code>{esc(emi.get('sha256'))}</code>,
{esc(validator.get('n_positives'))} positive pixels.</li>
<li><b>Local format:</b> {"PASS" if gmap.get("G1", {}).get("ok") else "FAIL"} ({n_pass}/{len(checks)} emission-receipt checks).
This does not establish portal acceptance; the reported portal [0, 1] rejection is unresolved.</li>
<li><b>Final-dot scan:</b> {esc(firings)} literal &gt;70% overlap triggers in the saved
{esc(count)}-raster snapshot. The literal trigger is a stop; this count is not a clearance scan.</li>
<li><b>Registry freshness:</b> {esc(freshness_decision)} — {freshness_label}. A stale/incomplete
inventory cannot clear either surface placement or emitted dots.</li>
<li><b>Promotion-grade HOLDOUT-DTI:</b> {holdout_text}</li>
<li><b>Qualification receipt:</b> {"present" if qualification_file.is_file() else "MISSING"};
G2P/G3/G4/G5 remain failed until fresh, hash-bound receipts exist.</li>
</ul></section>
<section>
<h2>H33 / 0.2778 attribution finding</h2>
<p>The 0.2778 {label('PUBLIC-LEADERBOARD-SNAPSHOT')} participant row belongs to
<code>extradr19</code> (rank 23 in the 2026-10-11 observation). It is not an
<code>ORGANIZER-CONFIRMED</code> artifact score for the GEMSDOE32 H33 TIFF. The GEMSDOE32
owner-maintained page identifies H33-2-B2 as unscored and describes 0.2747 as a projection; no
submission receipt or hash crosswalk links either value to H33. The current same-day public snapshot
records {row_text}; the board is dynamic.</p>
<p>Accordingly, the repository can resolve the <b>attribution</b> (the participant row is not H33),
but cannot scientifically explain why that participant obtained 0.2778. Without the scored artifact,
submission ID, hidden public subset and an organizer receipt, claims about that score's geology,
width, features, or metric components would be speculation. See
<a href="ANALYSIS_H33.md">the H33 evidence review</a>,
<a href="LEADERBOARD.md">dated board record</a>, and the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">official live board</a>.</p>
</section>
<section>
<h2>Scientific scope and next hypothesis</h2>
<p>This repository's lane adjusts ribbon width around an already-detected structure; width tuning
cannot recover a fault whose ridge surface entirely misses it. The ranked review documents four
specific, currently untried width-conditioning hypotheses. The top one is
<b>H58-U1: relief-conditioned width</b> using <code>det_elev</code> and
<code>det_elev_slope</code> around the fixed existing topographic ridge surface. It is not implemented
or validated. Expected benefit is qualitative and uncertain; there is no score forecast.</p>
<p>Named geological alternatives are not facts about a candidate: erosion, drainage, alluvial-fan
fronts, terrace margins, conductivity/lithology boundaries, and curved non-tectonic contacts can mimic
the target signatures. The proposed falsifiers and implementation differences from existing code are in
<a href="research/hypotheses_new.md">the ranked hypothesis register</a>.</p>
<p><b>Do not start the holdout yet.</b> First establish a fresh, exhaustive public raster inventory,
restore the pinned 19-band feature stack, and pass the candidate-specific pre-placement surface gate.
Only then may the top hypothesis enter a preregistered individual-feature canary and the shared
buffered spatial holdout. Use the exact marginal metric and report any number only with evaluator and
version, protocol, withheld-positive count, and a defensible 95% CI. Final dots require a separate
uniqueness scan. Maximum budget remains three experiments or two hours; no slot selection.</p>
<p><a href="research/session7_review_20261011.md">Full session review and evidence register</a> ·
<a href="research/hypotheses_new.md">Four ranked hypotheses</a> ·
<a href="IRREGULARITIES.md">Current blockers</a> ·
<a href="RUN_CARD.json">Machine-readable run card</a>.</p>
</section>
<section><h2>Required gates</h2>{gates_html(gates)}</section>
<section><h2>Trusted sources</h2><ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem statement, DTI, and submission format</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">DrivenData data and fault-mapping context</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData dynamic public leaderboard</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE GEMS Official Rules (September 2026)</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN survey release</a></li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference-solution repository</a></li>
</ul></section>
"""
    return page("Research review and qualification status", body, "executive-summary.html")


def build_submit(emi, card, gates, ok) -> str:
    """Local format evidence only; intentionally no upload instructions or permission language."""
    checks = (emi.get("validator", {}) or {}).get("checks", {}) or {}
    gmap = {g.get("id"): g for g in gates}
    local_ok = bool(gmap.get("G1", {}).get("ok"))
    local_cls = "pass" if local_ok else "fail"
    check_rows = [[f"<code>{esc(k)}</code>",
                   f'<span class="pill {local_cls}">{"PASS" if isinstance(c, dict) and c.get("ok") is True else "FAIL"}</span>',
                   esc(c.get("detail", "") if isinstance(c, dict) else c)]
                  for k, c in checks.items()]
    name = str(emi.get("name", "unknown-candidate"))
    candidate_status = "OK TO SUBMIT" if ok else "NOT OK TO SUBMIT — DO NOT SUBMIT"
    local_badge = "LOCAL FORMAT PREFLIGHT: PASS" if local_ok else "LOCAL FORMAT PREFLIGHT: FAIL"
    body = f"""
<section class="banner" role="alert"><h2>{candidate_status}</h2>
<p>The download below is an audit artifact for review and reproducibility only. Do not upload it,
select a competition slot, or infer eligibility from a local format check.</p>
<p><span class="pill {local_cls}">{local_badge}</span>
<span class="pill fail">OVERALL QUALIFICATION IS SEPARATE</span></p></section>
<section><h2>Exact artifact reviewed</h2>
<p><code>{esc(name)}.tif</code> · SHA-256 <code>{esc(emi.get('sha256'))}</code> ·
{esc((emi.get('validator', {}) or {}).get('bytes'))} bytes ·
{esc((emi.get('validator', {}) or {}).get('n_positives'))} positive pixels.</p>
<p><a class="button review" href="downloads/{esc(name)}.tif" download>Download for audit only — DO NOT SUBMIT</a>
<a href="downloads/index.html">See the individually labelled downloads index.</a></p></section>
<section><h2>What the local preflight checks</h2>
<p>The receipt was produced by the project's local validator and compared with the bytes on disk.
A local pass does not establish that DrivenData accepted the file or that its portal validator will
interpret the NoData mask the same way. The previously reported portal message
<code>Predicted values must be in range [0, 1]</code> is <b>unresolved</b>: this checkout has no
portal response payload or submission receipt bound to this SHA-256. Do not infer its cause from the
local minimum/maximum.</p>
{table(["local check", "result", "detail"], check_rows, "kv")}
<p class="small">Receipt-level checks passing: {sum(1 for c in checks.values() if isinstance(c, dict) and c.get("ok") is True)}/{len(checks)}.
These checks concern format/range only. They are not uniqueness, inventory freshness, leakage,
holdout, organizer acceptance, score attribution, or submit authorization.</p></section>
<section><h2>Official format references</h2><ul>
<li>DrivenData specifies a single-band float32 GeoTIFF (or ZIP with exactly one TIFF), EPSG:32611,
100 m, matching bounds, values in [0,1], and null/NaN outside the study area:
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official problem page</a>.</li>
<li>The <a href="https://github.com/drivendataorg/gems-prize-reference-solution">official reference-solution repository</a>
shows a writer that leaves no NaN inside the footprint. It does not resolve acceptance for this candidate.</li>
</ul><p>For the evidence-based decision, see <a href="index.html">current status and required gates</a>,
<a href="executive-summary.html">research review</a>, and <a href="RUN_CARD.json">the machine-readable run card</a>.</p></section>
"""
    return page("Local artifact QA — not submission clearance", body, "submit.html")


def build_evidence_index(emi, card, arms, sig, inv, fit) -> str:
    """Evidence inventory with classifications that do not upgrade historical diagnostics."""
    curated = [
        ("evidence/ribbon/emission.json", "LOCAL-ARTIFACT-RECEIPT",
         "Exact candidate metadata and local-format checks. Not portal acceptance or eligibility."),
        ("evidence/ribbon/file_audit.json", "LOCAL-FORMAT-AUDIT",
         "Independent on-disk raster/ZIP checks and decoded-pixel hash; format only."),
        ("evidence/ribbon/uniqueness_full_inventory.json", "REGISTRY-MEASUREMENT — SNAPSHOT",
         "Final-dot comparison on its saved inventory snapshot; 83 literal triggers. Not a current complete inventory."),
        ("evidence/registry_freshness_audit.json", "REGISTRY-FRESHNESS-AUDIT",
         "Current decision is BLOCKED_NOT_EXHAUSTIVE; a frozen snapshot cannot clear uniqueness."),
        ("evidence/ribbon/concordance_surface_uniqueness.json", "REGISTRY-MEASUREMENT — HISTORICAL",
         "Earlier candidate-surface comparison; not a fresh, hash-bound pre-placement qualification."),
        ("evidence/ribbon_qualification.json", "QUALIFICATION-RECEIPT",
         "Required hash-bound qualification receipt. Missing means G2P/G3/G4/G5 fail closed."),
        ("evidence/ribbon/run_card_v2.json", "LEGACY-DIAGNOSTIC-ONLY",
         "Historical evaluator/split and old protocol. Stored DTI/AUC/clearance values are not current promotion evidence."),
        ("evidence/ribbon/shared_metric_crosscheck.json", "LEGACY-ARITHMETIC-CHECK",
         "Checks arithmetic for a historical result; does not upgrade its split, selection procedure, or confidence interval."),
        ("registry/registry_merged.json", "REGISTRY-INDEX — FROZEN SNAPSHOT",
         "Indexed public raster paths for the recorded scan. Freshness remains blocked; this is not organizer-wide."),
        ("evidence/official_leaderboard_observation_20261011_review.json", "PUBLIC-LEADERBOARD-SNAPSHOT",
         "Dated public participant rows only. No TIFF hash or organizer submission receipt crosswalk."),
        ("evidence/organizer_confirmed.json", "OFFICIAL-SOURCE-FACTS",
         "Official task/format/metric facts and sourced statements. Despite the historical filename, it is not an artifact score receipt."),
        ("evidence/session7_review_run_card.json", "REVIEW-RUN-CARD",
         "This review: hypothesis proposed, no experiment or candidate emitted, holdout NOT MEASURED, verdict negative."),
    ]
    rows = []
    for rel, kind, what in curated:
        path = ROOT / rel
        exists = path.is_file()
        data = load(path) if exists and path.suffix == ".json" else {}
        stamp = data.get("checked_utc", data.get("generated_utc", data.get("observed_date_utc", "")))
        state = '<span class="pill pass">present</span>' if exists else '<span class="pill fail">MISSING</span>'
        rows.append([f"<code>{esc(rel)}</code>", state,
                     f"{path.stat().st_size:,} B" if exists else "—",
                     esc(stamp), label(kind), esc(what)])
    body = f"""
<section class="banner" role="alert"><h2>Evidence is classified; legacy values are not promoted</h2>
<p>The public status page reads the same fail-closed qualification evaluator as the emission contract.
A local audit, frozen registry scan, public leaderboard row, or historical holdout cannot substitute
for the missing hash-bound qualification receipt.</p></section>
<section><h2>Decision-critical evidence</h2>
{table(["receipt", "state", "size", "recorded time", "evidence class", "what it establishes"], rows, "kv")}
<p><b>Current HOLDOUT-DTI:</b> NOT MEASURED. No current candidate-bound shared-evaluator result,
withheld-positive count, protocol and defensible 95% CI is available. Legacy scores remain in their
original receipts for audit but are not repeated here as a current result.</p>
<p><b>Organizer-confirmed artifact scores:</b> none. A public leaderboard participant row is only a
PUBLIC-LEADERBOARD-SNAPSHOT unless an organizer receipt/hash crosswalk identifies the exact file.</p></section>
<section><h2>Safe future sequence (currently blocked)</h2><ol>
<li>Refresh the current public repository trees and raster index; run the freshness audit and stop if
it is stale, incomplete, or has source errors.</li>
<li>Use the literal pre-placement uniqueness gate before placement/emission. Rank correlation &gt;0.90
or &gt;70% of candidate dots within 3 px of any one witness is a stop; do not use chance correction to
waive a trigger.</li>
<li>Restore the hash-pinned organizer-provided feature stack. Mirror-pin integrity is not independent
organizer provenance. No new external layer is proposed for H58-U1.</li>
<li>Only after surface clearance: preregister H58-U1, run individual feature-alone leakage checks,
then use the shared buffered spatial holdout and exact marginal DTI. Report a number only if its
shared evaluator/version, protocol, withheld-positive count and defensible 95% CI are present.</li>
<li>Only after holdout clearance: use the shared writer, hash-bind its output, and independently
re-check final-dot uniqueness. Never choose a slot here.</li>
<li>Run tests and <code>python3 scripts/build_site.py --strict</code>. A strict exit 2 is the correct
result while any required gate is open.</li></ol>
<p>Feature-stack restore helper: <code>scripts/fetch_feature_stack.sh</code>. Registry refresh helpers:
<code>scripts/fetch_registry_sparse.py</code> and <code>scripts/registry_delta_inventory.py</code>.
The local feature raster is not present in this checkout, and no experiment was run.</p></section>
<section><h2>Trusted sources</h2><ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Competition task, metric, and format</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">Competition data and fault-mapping context</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official dynamic public leaderboard</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE GEMS Official Rules</a></li>
</ul><p>Source register: <a href="SOURCES.md">docs/SOURCES.md</a> · hypothesis review:
<a href="research/hypotheses_new.md">docs/research/hypotheses_new.md</a> · current run card:
<a href="RUN_CARD.json">docs/RUN_CARD.json</a>.</p></section>
"""
    return page("Evidence and provenance", body, "evidence.html")


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 unless all required qualification gates pass")
    strict = ap.parse_args(argv).strict

    emi = load(RIB / "emission.json")
    source_card = load(RIB / "run_card_v2.json")
    arms = load(RIB / "adaptive_arms.json")
    sig = load(RIB / "adaptive_sigma.json")
    inv = load(RIB / "uniqueness_full_inventory.json")
    fit = load(EV / "live_evidence_fit.json")
    xcheck = load(RIB / "shared_metric_crosscheck.json")
    sib_dir = load(RIB / "sibling_direction_check.json")
    sib_inv = load(RIB / "sibling_full_inventory.json")
    qualification_path = EV / "ribbon_qualification.json"
    freshness_path = EV / "registry_freshness_audit.json"
    index_path = ROOT / "registry/registry_merged.json"
    inventory_path = RIB / "uniqueness_full_inventory.json"
    qualification = load(qualification_path)
    freshness = load(freshness_path)
    if not emi or not source_card:
        print("evidence/ribbon/emission.json or run_card_v2.json is missing; "
              "cannot render a candidate status", file=sys.stderr)
        return 1

    raw_tif = Path(str(emi.get("file", "")))
    tif = raw_tif if raw_tif.is_absolute() else ROOT / raw_tif

    def hash_if_present(path: Path) -> str | None:
        return sha256(path) if path.is_file() else None

    gates, eligible = evaluate_gates(
        emi, sig, inv, tif, xcheck, qualification, freshness,
        inventory_index_sha256=hash_if_present(index_path),
        inventory_receipt_sha256=hash_if_present(inventory_path),
        freshness_receipt_sha256=hash_if_present(freshness_path),
    )
    gate_map = {g["id"]: g for g in gates}
    open_required = [g for g in gates if g.get("id") in REQUIRED_GATES and not g.get("ok")]
    print(f"site verdict: {'OK TO SUBMIT' if eligible else 'NOT OK TO SUBMIT — DO NOT SUBMIT'}")
    for gate in gates:
        state = ("INFO" if gate.get("informational") else "PASS" if gate.get("ok") else "FAIL")
        print(f"  {gate['id']} {state} — {gate['name']}")

    overall = "OK_TO_SUBMIT" if eligible else "NOT_OK_TO_SUBMIT"
    run_card = {
        "evidence_class": "REVIEW-RUN-CARD",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidate_file": str(emi.get("file", "")),
        "candidate_file_sha256": emi.get("sha256"),
        "candidate_decoded_sha256": emi.get("decoded_prediction_sha256"),
        "raster_sha256": emi.get("sha256"),
        "submission_name": str(emi.get("name", "")),
        "submission_note": str(source_card.get("submission_note", "")),
        "submission_note_status": "IDENTIFICATION ONLY — NOT FOR SUBMISSION",
        "submission_status": overall,
        "promote_or_negative": "promote" if eligible else "negative",
        "verdict": "promote" if eligible else "negative",
        "verdict_reason": ("All required qualification gates pass. This is not an organizer score or a "
                           "slot selection." if eligible else
                           "Required gates open: " + ", ".join(g.get("id", "?") for g in open_required)
                           + ". See site_gates and current receipts; do not submit."),
        "site_verdict": overall,
        "site_gates": gates,
        "hypothesis": {
            "id": "H58-U1",
            "title": "Relief-conditioned width around the existing topographic ridge surface",
            "status": "PROPOSED — NOT IMPLEMENTED OR VALIDATED",
            "candidate_output_emitted": False,
            "candidate_output_sha256": None,
            "layers": ["det_elev", "det_elev_slope"],
            "mechanism": ("Localization error may vary with relief/scarp expression; only a wider "
                          "ribbon near an already-detected ridge could cover positional uncertainty "
                          "for a nearby unmapped trace. This cannot recover a fault the fixed ridge "
                          "surface entirely misses."),
            "named_non_fault_mimic": ("drainage channels, alluvial-fan fronts, terrace margins, "
                                      "road cuts, and erosional scarps"),
            "expected_benefit": "Low to moderate potential; high uncertainty; no numeric forecast.",
            "implementation_cost_estimate": "1–2 engineering hours; estimate only.",
            "untried_audit": "Specific relief-conditioned ribbon-width rule not found in this checkout; see docs/research/hypotheses_new.md.",
        },
        "reviewed_artifact": {
            "file": str(emi.get("file", "")),
            "hypothesis_id": "H58-X1 — legacy cross-family concordance artifact",
            "sha256": emi.get("sha256"),
            "positive_pixels": (emi.get("validator", {}) or {}).get("n_positives"),
            "new_file_emitted_this_review": False,
            "not_the_output_of_hypothesis": "H58-U1",
        },
        "holdout": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "REPORTABLE" if gate_map.get("G5", {}).get("ok") else "NOT MEASURED",
            "evaluator": (qualification.get("promotion_grade_holdout", {}) or {}).get("evaluator")
                         if gate_map.get("G5", {}).get("ok") else None,
            "evaluator_version": (qualification.get("promotion_grade_holdout", {}) or {}).get("evaluator_version")
                                 if gate_map.get("G5", {}).get("ok") else HOLDOUT_VERSION,
            "protocol": (qualification.get("promotion_grade_holdout", {}) or {}).get("protocol")
                        if gate_map.get("G5", {}).get("ok") else None,
            "withheld_positive_pixels": ((qualification.get("promotion_grade_holdout", {}) or {}).get(
                "withheld_positive_pixels", (qualification.get("promotion_grade_holdout", {}) or {}).get(
                    "n_withheld_positives")) if gate_map.get("G5", {}).get("ok") else None),
            "ci95": (qualification.get("promotion_grade_holdout", {}) or {}).get("ci95")
                    if gate_map.get("G5", {}).get("ok") else None,
            "reason": ("No candidate-, inventory-, evaluator-, and protocol-bound reportable result "
                       "with a defensible 95% CI is available." if not gate_map.get("G5", {}).get("ok")
                       else "See the hash-bound qualification receipt."),
            "legacy_diagnostic_receipts": [
                "evidence/ribbon/run_card_v2.json",
                "evidence/ribbon/adaptive_arms.json",
                "evidence/ribbon/shared_metric_crosscheck.json",
            ],
            "legacy_values_are_not_current_holdout": True,
        },
        "registry": {
            "literal_rule": "PARALLEL-RUN-LITERAL-70%-v1",
            "rule_statement": ("Stop if rank correlation >0.90 OR if >70% of candidate dots are within "
                               "3 px of any one witness. Any literal trigger is a stop; do not waive "
                               "with chance correction or saturated-witness reasoning."),
            "freshness_decision": freshness.get("decision", "MISSING"),
            "fresh_current_inventory": freshness.get("fresh_current_inventory"),
            "freshness_receipt": "evidence/registry_freshness_audit.json",
            "final_dot_scan_status": "STOP — SNAPSHOT ONLY; NOT CURRENT CLEARANCE",
            "final_dot_scan_receipt": "evidence/ribbon/uniqueness_full_inventory.json",
            "rasters_checked_in_saved_scan": inv.get("registry_rasters_checked", inv.get("n_compared")),
            "literal_overlap_firings": (inv.get("informative_reading", {}) or {}).get(
                "overlap_firings", inv.get("duplicate_count")),
            "worst_literal_forward_overlap": inv.get("worst_dot_overlap"),
            "worst_rank_correlation": inv.get("worst_spearman_full_footprint"),
            "stop_required_in_saved_scan": inv.get("stop_required"),
            "preplacement_surface_status": "NOT CLEARED AGAINST A FRESH EXHAUSTIVE INVENTORY",
            "preplacement_receipt": "evidence/ribbon/concordance_surface_uniqueness.json",
        },
        "local_validator": {
            "all_checks_passed": bool((emi.get("validator", {}) or {}).get("passed")),
            "checks_passed": sum(1 for c in ((emi.get("validator", {}) or {}).get("checks", {}) or {}).values()
                                  if isinstance(c, dict) and c.get("ok") is True),
            "checks_total": len((emi.get("validator", {}) or {}).get("checks", {}) or {}),
            "scope": "Local format/range only; not portal acceptance.",
            "reported_portal_range_error": "UNRESOLVED — no response payload or hash-bound receipt.",
        },
        "experiment_budget": {"experiments_used": 0, "maximum_experiments": 3,
                              "time_limit_hours": 2, "slot_selections": 0},
        "next_action": ("Refresh and verify the current public inventory, then pass the pre-placement "
                        "surface gate before any H58-U1 experiment or new emission."),
        "archived_prior_run_card": "evidence/ribbon/run_card_v2.json",
        "slots_used": 0,
    }

    DOCS.mkdir(parents=True, exist_ok=True)
    DL.mkdir(parents=True, exist_ok=True)
    card_text = json.dumps(run_card, indent=2, ensure_ascii=False, default=float) + "\n"
    (EV / "session7_review_run_card.json").write_text(card_text, encoding="utf-8")
    (DOCS / "index.html").write_text(
        build_index(emi, source_card, arms, sig, inv, fit, sib_dir, sib_inv, gates, eligible,
                    qualification=qualification, freshness=freshness), encoding="utf-8")
    (DOCS / "executive-summary.html").write_text(
        build_executive_summary(emi, source_card, arms, sig, inv, gates, eligible,
                                qualification=qualification, freshness=freshness), encoding="utf-8")
    (DOCS / "submit.html").write_text(build_submit(emi, source_card, gates, eligible), encoding="utf-8")
    (DOCS / "evidence.html").write_text(build_evidence_index(emi, source_card, arms, sig, inv, fit),
                                        encoding="utf-8")

    card_text = json.dumps(run_card, indent=2, ensure_ascii=False, default=float) + "\n"
    (DOCS / "RUN_CARD.json").write_text(card_text, encoding="utf-8")
    (RIB / "run_card_final.json").write_text(card_text, encoding="utf-8")
    (EV / "session7_review_run_card.json").write_text(card_text, encoding="utf-8")
    checks_json = DL / f"{run_card['submission_name']}.checks.json"
    checks_json.write_text(json.dumps({"run_card": run_card, "site_gates": gates,
                                       "site_verdict": overall}, indent=2, ensure_ascii=False,
                                      default=float) + "\n", encoding="utf-8")
    print(f"wrote current fail-closed status pages and run cards for {tif.name}")
    if strict and not eligible:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
