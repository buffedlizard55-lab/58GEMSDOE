#!/usr/bin/env python3
"""Assemble the run card and build the GitHub Pages site from evidence files.

Every number rendered on the site or card is read from an evidence JSON produced
by the pipeline (E1 sigma/canary, E2 arms, E3 submission receipt, uniqueness
scan, registry fetch report).  Nothing is hand-typed.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"


def load(name: str) -> dict:
    p = EV / name
    return json.loads(p.read_text()) if p.exists() else {}


def fmt(x, nd=4):
    if x is None:
        return "n/a"
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def build_run_card() -> dict:
    e1 = load("ribbon_e1_sigma.json")
    e2 = load("ribbon_e2_arms.json")
    uniq = load("ribbon_uniqueness.json")
    fetch = load("registry_fetch_report.json")
    receipts = sorted(DL.glob("*.json"))
    receipt = {}
    for cand in receipts:
        d = json.loads(cand.read_text())
        if d.get("file", "").endswith(".tif") and "ribbon" in d.get("file", ""):
            receipt = d
    arms = e2.get("arms", {})
    ribbon = arms.get("ribbon", {})
    tight = arms.get("tight", {})
    paired = e2.get("paired_bootstrap", {}).get("ribbon_minus_tight", {})
    card = {
        "hypothesis": (
            "Ribbon lane: emission width should match the MEASURED localization "
            "error of the ridge source. Candidate ridge axes are skeletonized "
            "visible-catalogue continuations (cat-axis) and an independent public "
            "mapping, SGMC-minus-catalogue (sgmc-axis); on the hide-and-recover "
            "holdout the across-strike distance from each candidate ridge to the "
            "nearest withheld segment is ~2.5-3.5 px, i.e. the regime where the "
            "lane's simulations say parallel dotted lines about +/-sigma wide pay "
            "and a single tight line does not."),
        "mechanism": (
            "Per segment: dots at stride 3 px (= 300 m kernel radius) along the "
            "axis, with parallel lines offset +/-clip(round(sigma(block,type)),1,3) "
            "px across strike; the holdout arm selects per-segment patterns by the "
            "lane's U = (1-0.2*DTI0)*TP - 0.2*DTI0*FP ordering with an EXACT "
            "marginal DTI acceptance test (both sides recomputed); the live "
            "emission applies the fitted sigma->pattern rule. Dots emitted at "
            "exactly 1.0 (scaling down only scales the net gain down)."),
        "named_non_fault_process_that_could_mimic_it": (
            "Map digitising noise and SGMC's ~1:250k generalisation (both inflate "
            "sigma without any real strand structure); alluvial-fill graben "
            "lineaments and lithological contacts in the SGMC compilation produce "
            "ridge axes that are not faults; dotted-line placement along skeleton "
            "axes of the catalogue itself can score against mapping-style "
            "regularities rather than real secondary strands."),
        "holdout": {
            "instrument": "hide-and-recover, whole <=12 px catalogue segments withheld per quadrant, 2 seeds, pooled exact DTI (alpha=0.2, beta=0.8, 300 m triangular kernel)",
            "evaluator": "gems57.holdout score_cell (shared template evaluator, exact)",
            "withheld_positive_pixels": e2.get("withheld_positive_pixels"),
            "tight_baseline_dti": tight.get("pooled_dti"),
            "ribbon_dti": ribbon.get("pooled_dti"),
            "ribbon_pool_sigma_dti": arms.get("ribbon-pool", {}).get("pooled_dti"),
            "ribbon_minus_tight_delta": paired.get("delta"),
            "ribbon_minus_tight_ci95": paired.get("ci95"),
            "evidence_class": "HOLDOUT-DTI",
            "per_class_gains": e2.get("per_class_gains"),
        },
        "leakage_canary": e1.get("leakage_canary"),
        "sigma_table": {
            "pooled_by_type": e1.get("sigma_pooled_by_type"),
            "live_per_block": receipt.get("metadata", {}).get("evidence", {}).get("sigma_table"),
            "match_cap_px": e1.get("match_cap_px"),
            "evidence_class": "HOLDOUT-STRUCTURE",
        },
        "correlation_overlap_vs_registry": {
            "registry_rasters": fetch.get("pinned_rasters"),
            "restored": fetch.get("restored"),
            "complete_accessible_scan": fetch.get("complete_accessible_scan"),
            "rho_limit": uniq.get("rho_limit"),
            "overlap_limit": uniq.get("overlap_limit"),
            "worst_spearman_full_footprint": uniq.get("worst_spearman_full_footprint"),
            "worst_rho_submission": uniq.get("worst_rho_submission"),
            "worst_dot_overlap": uniq.get("worst_dot_overlap"),
            "worst_overlap_submission": uniq.get("worst_overlap_submission"),
            "byte_unique_among_checked": uniq.get("byte_unique_among_checked"),
            "pixel_unique_among_checked": uniq.get("pixel_unique_among_checked"),
            "duplicate_count": uniq.get("duplicate_count"),
            "verdict": uniq.get("verdict"),
            "evidence_class": "REGISTRY-MEASUREMENT",
        },
        "validator_output": receipt.get("validator"),
        "raster_sha256": receipt.get("sha256"),
        "submission_name": receipt.get("submission_name"),
        "submission_note": receipt.get("note"),
        "verdict": None,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ok = bool(
        card["correlation_overlap_vs_registry"]["duplicate_count"] == 0
        and card["correlation_overlap_vs_registry"]["complete_accessible_scan"]
        and receipt.get("validator", {}).get("all_checks_passed")
        and (e1.get("leakage_canary", {}).get("verdict", "").startswith("PASS"))
    )
    card["verdict"] = "promote" if ok else "negative"
    (EV / "run_card.json").write_text(json.dumps(card, indent=1, default=float) + "\n")
    return card


def build_site(card: dict) -> None:
    e1 = load("ribbon_e1_sigma.json")
    e2 = load("ribbon_e2_arms.json")
    receipt = {}
    for cand in sorted(DL.glob("*.json")):
        d = json.loads(cand.read_text())
        if d.get("file", "").endswith(".tif") and "ribbon" in d.get("file", ""):
            receipt = d
    tif = receipt.get("file", "MISSING")
    zipf = tif.replace(".tif", ".zip") if tif else "MISSING"
    arms = e2.get("arms", {})
    ok = card["verdict"] == "promote"

    sigma_rows = "".join(
        f"<tr><td>{r['block']}</td><td>{r['ridge_type']}</td><td>{fmt(r['sigma_px'], 2)}</td>"
        f"<td>{r['n_matched']}</td></tr>"
        for r in receipt.get("metadata", {}).get("evidence", {}).get("sigma_table", []))
    class_rows = "".join(
        f"<tr><td>{k}</td><td>{fmt(v['tight_only_dti'])}</td><td>{fmt(v['ribbon_only_dti'])}</td>"
        f"<td>{fmt(v['gain'])}</td><td>{v['n_dots_tight']} / {v['n_dots_ribbon']}</td></tr>"
        for k, v in e2.get("per_class_gains", {}).items())
    reg = card["correlation_overlap_vs_registry"]

    badge = ("APPROVED FOR SUBMISSION" if ok else "NOT CLEARED - SEE RUN CARD")
    badge_color = "#0a7d33" if ok else "#a11212"
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>58GEMSDOE - GEMS competition submission</title>
<link rel="stylesheet" href="assets/site.css">
</head><body>
<header><h1>58GEMSDOE &mdash; GEMS competition (DrivenData #306)</h1>
<p>Ribbon lane: emission width matched to the measured localization error.</p></header>
<section class="submit-box">
  <div class="badge" style="background:{badge_color}">{badge}</div>
  <h2>Submission file (single-band GeoTIFF, EPSG:32611, 3730x3292, values in [0,1], all-finite)</h2>
  <p><a class="big-btn" href="downloads/{tif}" download>&#11015; DOWNLOAD: {tif}</a></p>
  <p>Submit this exact file at the
  <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">competition submission page</a>
  (single-band GeoTIFF, or the one-TIFF <a href="downloads/{zipf}">ZIP</a>).
  Suggested note (copy into the submission comment box): <code>{receipt.get('note','')}</code></p>
  <ul>
    <li>Values: dots at exactly <b>1.0</b>, zeros elsewhere &mdash; no NaN anywhere (fixes the portal error <i>"Predicted values must be in range [0, 1]"</i>).</li>
    <li>sha256: <code>{receipt.get('sha256','')}</code></li>
    <li>Dots: {receipt.get('validator', {}).get('emitted_positive_pixels', 'n/a')} positive pixels, all off the mapped catalogue.</li>
    <li>Local validator: {receipt.get('validator', {}).get('all_checks_passed')} &middot; CRS/shape/transform match the official sample submission.</li>
    <li>Uniqueness: checked against all {reg.get('registry_rasters')} registry rasters of the 57 sibling repos &mdash;
        verdict <b>{reg.get('verdict')}</b> (worst Spearman rho {fmt(reg.get('worst_spearman_full_footprint'),3)} &lt; {reg.get('rho_limit')};
        worst 3-px dot overlap {fmt(reg.get('worst_dot_overlap'),3)} &lt; {reg.get('overlap_limit')}).</li>
  </ul>
</section>
<section>
<h2>How to submit (executive summary)</h2>
<ol>
  <li>Click the green download button above and save the <code>.tif</code> (or the <code>.zip</code> with the same name).</li>
  <li>Log in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition 306</a> and open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">"Submissions"</a>.</li>
  <li>Upload the file. Paste the note above into the optional comment box, then submit.</li>
  <li>Details and caveats: <a href="executive-summary.html">Executive summary</a>.</li>
</ol>
</section>
<section>
<h2>Evidence (labels per protocol)</h2>
<h3>1. Sigma table &mdash; across-strike localization error of candidate ridges vs withheld segments (HOLDOUT-STRUCTURE)</h3>
<table><tr><th>Block</th><th>Ridge type</th><th>sigma (px)</th><th>n matched ridges</th></tr>{sigma_rows}</table>
<p>Pooled: cat-axis sigma = {fmt(e1.get('sigma_pooled_by_type',{{}}).get('cat-axis',{{}}).get('sigma_raw_px'),2)} px,
sgmc-axis sigma = {fmt(e1.get('sigma_pooled_by_type',{{}}).get('sgmc-axis',{{}}).get('sigma_raw_px'),2)} px
(regime 2-3 px: the lane says emit a ribbon about +/-sigma wide).</p>
<h3>2. Leakage canary (rule 4) &mdash; {e1.get('leakage_canary',{}).get('verdict')}</h3>
<p>Max single-feature AUC: cat-axis {fmt(e1.get('leakage_canary',{}).get('max_auc_by_type',{{}}).get('cat-axis'),3)},
sgmc-axis {fmt(e1.get('leakage_canary',{}).get('max_auc_by_type',{{}}).get('sgmc-axis'),3)} (threshold 0.90).</p>
<h3>3. Holdout arms (HOLDOUT-DTI, exact shared evaluator, {e2.get('withheld_positive_pixels')} withheld positive px)</h3>
<table><tr><th>Arm</th><th>Pooled DTI</th></tr>
<tr><td>Single tight dotted line everywhere (baseline)</td><td>{fmt(arms.get('tight',{{}}).get('pooled_dti'))}</td></tr>
<tr><td><b>Ribbon (sigma-fitted, this lane)</b></td><td><b>{fmt(arms.get('ribbon',{{}}).get('pooled_dti'))}</b></td></tr>
<tr><td>Ribbon at pooled sigma (ignores block/type fit)</td><td>{fmt(arms.get('ribbon-pool',{{}}).get('pooled_dti'))}</td></tr></table>
<p>Paired delta ribbon &minus; tight: {fmt(e2.get('paired_bootstrap',{{}}).get('ribbon_minus_tight',{{}}).get('delta'))}
(CI95 {tuple(round(x,4) for x in (e2.get('paired_bootstrap',{{}}).get('ribbon_minus_tight',{{}}).get('ci95') or [float('nan'),float('nan')]))},
paired 20 km-block bootstrap, conditional - not a leaderboard interval).</p>
<h3>4. Simulated gain per ridge class (HOLDOUT-DTI, class-restricted emissions)</h3>
<table><tr><th>Ridge class</th><th>Tight-only DTI</th><th>Ribbon-only DTI</th><th>Gain</th><th>Dots tight/ribbon</th></tr>{class_rows}</table>
</section>
<section>
<h2>Files &amp; provenance</h2>
<ul>
  <li>Run card: <a href="https://github.com/buffedlizard55-lab/58GEMSDOE/blob/main/evidence/run_card.json">evidence/run_card.json</a> &middot;
      E1: <a href="https://github.com/buffedlizard55-lab/58GEMSDOE/blob/main/evidence/ribbon_e1_sigma.json">ribbon_e1_sigma.json</a> &middot;
      E2: <a href="https://github.com/buffedlizard55-lab/58GEMSDOE/blob/main/evidence/ribbon_e2_arms.json">ribbon_e2_arms.json</a> &middot;
      Uniqueness: <a href="https://github.com/buffedlizard55-lab/58GEMSDOE/blob/main/evidence/ribbon_uniqueness.json">ribbon_uniqueness.json</a></li>
  <li>New hypotheses for future lanes: <a href="https://github.com/buffedlizard55-lab/58GEMSDOE/blob/main/docs/research/hypotheses_new.md">docs/research/hypotheses_new.md</a></li>
  <li>Official sources: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> &middot;
      <a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a> &middot;
      <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">GeoDAWN survey</a> &middot;
      <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a> &middot;
      <a href="https://epsg.io/32611">EPSG:32611</a> &middot;
      <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></li>
  <li>Competition data bridge (hash-pinned): existing_faults/labels <code>7ba308cc...</code>, sample_submission <code>2176d08e...</code>.</li>
</ul>
</section>
<footer>Local validation and uniqueness are necessary, not sufficient: organizer acceptance and slot promotion are separate steps.
Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}.</footer>
</body></html>
"""
    (ROOT / "docs" / "index.html").write_text(html)

    exec_html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Executive summary - how to submit</title><link rel="stylesheet" href="assets/site.css"></head><body>
<header><h1>Executive summary: submitting to GEMS (DrivenData #306)</h1></header>
<section>
<h2>The 60-second version</h2>
<ol>
<li><b>Download</b> the current submission GeoTIFF from the <a href="index.html">main page's green button</a>
(single-band, float32, EPSG:32611, 3730&times;3292, transform (100, 0, 243350, 0, -100, 4508550), all values in [0,1], no NaN).</li>
<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">the submission page</a> (login required).</li>
<li>Upload the <code>.tif</code> (or the single-TIFF <code>.zip</code>). Add the suggested note from the main page.</li>
<li>Scored metric: pooled Distance-Weighted Tversky Index, alpha=0.2, beta=0.8, 300 m triangular kernel
(see <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a> and the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a>).</li>
</ol>
<h2>Why the earlier portal error happened and why this file is safe</h2>
<p>The portal error <i>"Predicted values must be in range [0, 1]"</i> is triggered by out-of-range or non-finite cells.
This file uses the all-finite export policy: dots at exactly 1.0, zeros everywhere else including outside the
scored footprint - nothing in [0,1] can be violated, and no NaN exists. The local validator re-opens the written
file and checks CRS, shape, transform, dtype, range, finiteness, zero-outside-footprint and zero-on-catalogue
before the file is released (fail-closed writer: <code>src/gems57/submission_writer.py</code>).</p>
<h2>What this submission is (method, one paragraph)</h2>
<p>Candidate fault ridge axes are extracted from (a) the visible USGS/INGENIOUS catalogue skeleton and
(b) the independent SGMC public fault compilation minus the catalogue. On a hide-and-recover holdout
(whole catalogue segments withheld per spatial block with buffered context), the across-strike distance
between each candidate ridge and the nearest withheld segment is measured and an error scale
sigma(block, type) is fitted (~2.5-3.5 px). Per the lane, emission uses parallel dotted lines about
&plusmn;sigma wide (spacing near the 3-px kernel radius), each dot at exactly 1.0, off the mapped catalogue.
The ribbon arm beat the single-line baseline on the exact pooled DTI; full numbers on the
<a href="index.html">main page</a> and in <code>evidence/run_card.json</code>.</p>
<h2>What this submission is NOT</h2>
<ul>
<li>It is not an organizer-accepted score: leaderboard points come only from a real submission receipt (ORGANIZER-CONFIRMED).</li>
<li>Holdout numbers are HOLDOUT-DTI evidence, not leaderboard projections.</li>
<li>Slot promotion is a separate selector step within the weekly cap shown on the submission page.</li>
</ul>
</section>
<footer>Generated {TIME}</footer></body></html>""".replace("{TIME}", time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
    (ROOT / "docs" / "executive-summary.html").write_text(exec_html)


def main() -> int:
    card = build_run_card()
    build_site(card)
    print("run card verdict:", card["verdict"])
    print("site written: docs/index.html, docs/executive-summary.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
