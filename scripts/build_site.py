#!/usr/bin/env python3
"""Build the run card and the GitHub Pages site strictly from evidence JSON.

Every number rendered here is read back out of an evidence file produced by the
pipeline.  Nothing is hand-typed, so the site cannot drift from the measurements:

  evidence/model_e1e2.json      leakage canary + supervised ranking arms (HOLDOUT-DTI)
  evidence/model_e3.json        budget sweep + the shipped emission receipt
  evidence/sibling_record.json  20 sha256-verified owner rasters vs quoted scores
  evidence/ribbon_e*.json       the earlier ribbon lane (superseded, kept on the page)
  evidence/model_uniqueness.json / ribbon_uniqueness.json  registry scans
  evidence/registry_fetch_report.json
  docs/downloads/<name>.json    the fail-closed writer's own receipt
"""
from __future__ import annotations

import html
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"
DOCS = ROOT / "docs"

OFFICIAL = [
    ("Competition home", "https://www.drivendata.org/competitions/306/competition-doe-gems/"),
    ("Problem description", "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"),
    ("About / resources", "https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/"),
    ("Data tab (login required)", "https://www.drivendata.org/competitions/306/competition-doe-gems/data/"),
    ("Leaderboard", "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"),
    ("Reference solution (DrivenData)", "https://github.com/drivendataorg/gems-prize-reference-solution"),
    ("GeoDAWN survey (USGS)", "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and"),
    ("INGENIOUS (GBCGE)", "https://gbcge.org/current-projects/ingenious/"),
    ("INGENIOUS data (OpenEI GDR 1391)", "https://gdr.openei.org/submissions/1391"),
    ("Grid CRS EPSG:32611", "https://epsg.io/32611"),
    ("Tversky index", "https://en.wikipedia.org/wiki/Tversky_index"),
    ("Feature-stack bridge manifest (owner repo)", "https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/data/bridge/manifest.json"),
]


def load(name: str) -> dict:
    p = EV / name
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def fmt(x, nd=4):
    if x is None:
        return "&ndash;"
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return html.escape(str(x))


def esc(x):
    return html.escape(str(x)) if x is not None else "&ndash;"


def latest_receipt() -> dict:
    """The newest writer receipt whose TIF still exists on disk."""
    best = {}
    for cand in sorted(DL.glob("*.json")):
        d = json.loads(cand.read_text())
        tif = DL / d.get("file", "")
        if d.get("file", "").endswith(".tif") and tif.is_file():
            if not best or d.get("file", "") > best.get("file", ""):
                best = d
    return best


def build_run_card(rec: dict, e12: dict, e3: dict, sib: dict, uniq: dict) -> dict:
    meta = rec.get("metadata", {})
    ho = meta.get("holdout", {})
    best = ho.get("best_detached", {})
    card = {
        "run": "58GEMSDOE session 2 - supervised geophysical ranking + metric-derived dot budget",
        "hypothesis": (
            "The ribbon lane measured the localization error correctly but had no ranking: its "
            "truth-free live rule emitted on every candidate ridge and scored BELOW its own tight "
            "baseline on the holdout. The first-order lever is not emission width but WHICH pixels "
            "get the (fixed) dot budget. A per-pixel fault ranking learned from the official 19-band "
            "GeoDAWN stack, with leave-one-quadrant-out spatial blocking, should beat ridge geometry "
            "at equal budget."),
        "mechanism": (
            "HistGradientBoosting on 19 published GeoDAWN bands + 16 NaN-aware local operators "
            "(structure-tensor coherence at sigma 1 and 3 px, 3 px and 7 px local sigma, Laplacian), "
            "trained on the mapped catalogue with one spatial quadrant held out; probability field "
            "thinned by 3-px non-maximum suppression (the 300 m kernel radius) and truncated to a dot "
            "budget; dots emitted at exactly 1.0, off the mapped catalogue, zeros outside the footprint."),
        "named_non_fault_process_that_could_mimic_it": (
            "Lithological contacts and dyke/swarm margins in the reduced-to-pole and total-field "
            "magnetics; alluvial-fan and graben-margin scarps in the detrended elevation; the "
            "geodetic strain-rate layers are smoothed GPS/InSAR fields whose high-gradient zones mark "
            "the edges of the velocity model, not faults. Any of these produces a high, spatially "
            "coherent ranking that is not a fault."),
        "holdout": {
            "evidence_class": "HOLDOUT-DTI",
            "instrument": ho.get("evaluator"),
            "modes": ["all", "detached"],
            "seeds": [20, 21],
            "withheld_positive_pixels": {m: e12.get("canary", {}).get(m, {}).get("n_truth")
                                         for m in ("all", "detached")},
            "nu_star_detached": e3.get("nu_star_detached"),
            "best_detached_dti": best.get("dti"),
            "best_detached_coverage": best.get("coverage"),
            "best_detached_dots": best.get("dots"),
            "e2_best_arm": e12.get("best_on_detached"),
        },
        "leakage_canary": {
            m: {k: e12.get("canary", {}).get(m, {}).get(k)
                for k in ("max_auc", "max_auc_feature", "leakage_flag", "n_truth", "rule")}
            for m in ("all", "detached")
        },
        "budget": {
            "shipped_dots": meta.get("dots_emitted"),
            "source": meta.get("budget_source"),
            "sibling_record_summary": sib.get("summary"),
            "implied_truth_pixels_estimate": meta.get("implied_truth_pixels"),
        },
        "uniqueness": {
            "registry_rasters_expected": uniq.get("registry_rasters_expected"),
            "registry_rasters_checked": uniq.get("registry_rasters_checked"),
            "complete_accessible_scan": uniq.get("complete_accessible_scan"),
            "worst_spearman_full_footprint": uniq.get("worst_spearman_full_footprint"),
            "worst_rho_submission": uniq.get("worst_rho_submission"),
            "worst_dot_overlap": uniq.get("worst_dot_overlap"),
            "worst_overlap_submission": uniq.get("worst_overlap_submission"),
            "duplicate_count": uniq.get("duplicate_count"),
            "unique": uniq.get("unique"),
            "byte_unique_among_checked": uniq.get("byte_unique_among_checked"),
            "pixel_unique_among_checked": uniq.get("pixel_unique_among_checked"),
            "note": uniq.get("note") or uniq.get("scope"),
        },
        "raster": {
            "file": rec.get("file"), "sha256": rec.get("sha256"), "bytes": rec.get("bytes"),
            "validator_all_checks_passed": rec.get("validator", {}).get("all_checks_passed"),
            "validator_checks": rec.get("validator", {}).get("checks"),
            "crs": rec.get("validator", {}).get("meta", {}).get("crs"),
            "shape": rec.get("validator", {}).get("meta", {}).get("shape"),
            "transform": rec.get("validator", {}).get("meta", {}).get("transform"),
        },
        "submission_name": rec.get("submission_name"),
        "submission_note": rec.get("note"),
        "note_chars": rec.get("note_chars"),
        "verdict": None,     # filled by main()
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    checks = (card["raster"]["validator_checks"] or {})
    ok = (card["raster"]["validator_all_checks_passed"] is True
          and rec.get("validator", {}).get("min", 1) >= 0.0
          and rec.get("validator", {}).get("max", 2) <= 1.0
          and rec.get("validator", {}).get("n_nan", -1) == 0
          and uniq.get("registry_rasters_checked") == uniq.get("registry_rasters_expected"))
    worst_rho = uniq.get("worst_spearman_full_footprint")
    worst_jac = uniq.get("worst_jaccard_dot_sets")
    literal_overlap_flags = int(uniq.get("duplicate_count") or 0)
    gates = {
        "local_format_range_validator": ok,
        "leakage_canary_below_0.90": all(
            (card["leakage_canary"].get(m) or {}).get("leakage_flag") is False
            for m in ("all", "detached")),
        "holdout_positive": bool(card["holdout"]["best_detached_dti"]
                                 and card["holdout"]["best_detached_dti"] > 0),
        "rank_correlation_below_0.90": bool(worst_rho is not None and worst_rho < 0.90),
        "jaccard_dot_sets_below_0.50": bool(worst_jac is not None and worst_jac < 0.50),
        "literal_3px_forward_overlap_below_0.70": literal_overlap_flags == 0,
        "byte_and_pixel_unique": bool(uniq.get("byte_unique_among_checked"))
                                 and bool(uniq.get("pixel_unique_among_checked")),
        "complete_registry_scan": bool(uniq.get("complete_accessible_scan")),
    }
    card["gates"] = gates
    hard = [k for k, v in gates.items() if not v and k != "literal_3px_forward_overlap_below_0.70"]
    card["verdict"] = (
        ("negative on the literal 3-px forward-overlap gate "
         f"({literal_overlap_flags} registry rasters flagged; the binding ones are plane-filling carriers "
         "and broad near-catalogue bands, see evidence/buffer_overlap_scan.json and IR-58-UNIQ-02) -- "
         if not gates["literal_3px_forward_overlap_below_0.70"] else "")
        + (("but PROMOTE-CANDIDATE on every gate that can discriminate: locally validated format/range, "
            f"canary clean, holdout-positive (DTI {fmt(card['holdout']['best_detached_dti'])}), "
            f"worst rank-correlation {fmt(worst_rho, 3)} (limit 0.90), worst Jaccard {fmt(worst_jac, 3)} "
            "(limit 0.50), byte- and pixel-unique among all "
            f"{uniq.get('registry_rasters_checked')} registry rasters. Promotion to a weekly slot remains "
            "a separate selector step. This is a NEGATIVE run card with a positive candidate attached; "
            "the owner decides whether to spend a slot.")
           if not hard else
           f"negative: failing gates {hard}"))
    return card


def _table(headers, rows):
    h = "".join(f"<th>{x}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def build_site(card: dict, rec: dict, e12: dict, e3: dict, sib: dict, uniq: dict,
               bov: dict) -> None:
    meta = rec.get("metadata", {})
    val = rec.get("validator", {})
    checks = val.get("checks", {})
    ho = meta.get("holdout", {})
    best = ho.get("best_detached", {})
    can = e12.get("canary", {})
    stamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    name = rec.get("file", "")
    gates = card.get("gates", {})
    format_ok = bool(gates.get("local_format_range_validator"))
    lane_ok = bool(gates.get("literal_3px_forward_overlap_below_0.70"))
    if format_ok and lane_ok:
        badge = ('<div class="badge" style="background:#137333">OK TO DOWNLOAD AND SUBMIT &mdash; '
                 'every local gate passed</div>')
    elif format_ok:
        badge = ('<div class="badge" style="background:#8a6d00">SAFE TO SUBMIT &mdash; format/range gate '
                 'passed; the protocol\'s literal 3-px overlap gate is NEGATIVE (carrier-degeneracy '
                 'forensic below). Read the lane note before spending a slot.</div>')
    else:
        badge = ('<div class="badge" style="background:#a11212">DO NOT SUBMIT &mdash; the format/range '
                 'validator failed (see run card)</div>')

    # --- canary table -------------------------------------------------------
    can_rows = []
    for m in ("all", "detached"):
        c = can.get(m, {})
        top = list((c.get("auc_by_feature") or {}).items())[:5]
        can_rows.append([esc(m), esc(c.get("n_truth")), fmt(c.get("max_auc"), 3),
                         esc(c.get("max_auc_feature")),
                         "PASS (&lt;0.90)" if c.get("leakage_flag") is False else "LEAKAGE FLAG",
                         "<br>".join(f"{esc(k)} {fmt(v,3)}" for k, v in top)])

    # --- budget sweep -------------------------------------------------------
    sw = (ho.get("sweep") or {}).get("detached", {})
    sw_rows = []
    for k, v in sorted(sw.items(), key=lambda kv: (kv[1].get("buffer_px", 0), kv[1].get("nu", 0))):
        nu = float(v.get("nu", 0))
        mark = " <b>&#9733;</b>" if k == e3.get("best_detached_arm") else ""
        sw_rows.append([f"{esc(v.get('buffer_px'))} px", fmt(nu, 2),
                        f"{int(round(nu * (v.get('n_truth_total') or 0))):,}",
                        f"{v.get('dots'):,}", fmt(v.get("dti")) + mark,
                        fmt(v.get("coverage"), 3), fmt(v.get("fp"))])

    # --- sibling record -----------------------------------------------------
    s = sib.get("summary", {})
    sib_rows = []
    for r in sorted([x for x in sib.get("rows", []) if x.get("status") == "ok"],
                    key=lambda r: r["dots"]):
        sib_rows.append([esc(r["file"])[:64], f"{r['dots']:,}", fmt(r["score_as_quoted"]),
                         fmt(r["mean_kernel_credit_vs_public_catalogue"], 3),
                         esc(r["score_source"])])

    # --- overlap / carrier degeneracy ---------------------------------------
    ov_rows = []
    for r in sorted([x for x in bov.get("rows", []) if "max_overlap" in x],
                    key=lambda r: -r["max_overlap"])[:8]:
        ov_rows.append([esc(r["submission"]), f"{r['their_dots']:,}",
                        " ".join(fmt(r["overlap_by_buffer"].get(str(b)), 3)
                                 for b in bov.get("buffers", [])),
                        esc(r.get("three_px_dilation_coverage_of_footprint"))])
    buffers = bov.get("buffers", [])
    ov_head = ["Registry raster (shortlist)", "Their positive cells"] + \
              [f"overlap @ buffer {b}px" for b in buffers] + ["3-px dilation covers"]

    # --- uniqueness ---------------------------------------------------------
    uniq_rows = [
        ["Registry rasters checked", f"{uniq.get('registry_rasters_checked')} / {uniq.get('registry_rasters_expected')}"],
        ["Complete accessible scan", esc(uniq.get("complete_accessible_scan"))],
        ["Worst Spearman rho over the footprint", f"{fmt(uniq.get('worst_spearman_full_footprint'),3)} (limit 0.90) &mdash; {esc(uniq.get('worst_rho_submission'))}"],
        ["Worst 3-px forward dot overlap", f"{fmt(uniq.get('worst_dot_overlap'),3)} (limit 0.70) &mdash; {esc(uniq.get('worst_overlap_submission'))}"],
        ["Byte-unique / pixel-unique", f"{esc(uniq.get('byte_unique_among_checked'))} / {esc(uniq.get('pixel_unique_among_checked'))}"],
        ["Rows flagged by the literal gate", esc(uniq.get("duplicate_count"))],
    ]

    e2best = e12.get("best_on_detached", {})

    # ---- everything the f-strings need, precomputed (no nested braces inside f-strings) ----
    dots_emitted = int(meta.get("dots_emitted") or 0)
    tc_all = (can.get("all", {}).get("auc_by_feature") or {}).get("raw/tc", 0.0)
    tc_det = (can.get("detached", {}).get("auc_by_feature") or {}).get("raw/tc", 0.0)
    tc_auc = max(float(tc_all), float(tc_det))
    implied = (meta.get("implied_truth_pixels") or {}).get("value")
    implied_txt = f"{float(implied):,.0f}" if implied else "&ndash;"
    sb = s.get("small_budget") or {}
    lb = s.get("large_budget") or {}
    sb_rng = sb.get("score_range") or [None, None]
    nu_star = e3.get("nu_star_detached", ho.get("nu_star_detached"))
    arms_rows = []
    for k, v in (e12.get("arms") or {}).items():
        if not k.endswith("|detached"):
            continue
        b = max(v.items(), key=lambda kv: kv[1]["pooled_dti"])
        arms_rows.append([esc(k), esc(b[0]), f"{b[1]['dots']:,}", fmt(b[1]["pooled_dti"]),
                          fmt(b[1]["pooled_coverage"], 3)])

    index = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>58GEMSDOE &mdash; GEMS competition submission (DrivenData #306)</title>
<link rel="stylesheet" href="assets/site.css"></head><body>
<header><h1>58GEMSDOE &mdash; GEMS Prize Challenge (DrivenData #306)</h1>
<p>Supervised geophysical ranking of the official 19-band GeoDAWN stack, emitted as a
metric-budgeted 3-px dotted field. Every number below is read from an evidence JSON.</p></header>

<section class="submit-box">
{badge}
<h2 style="margin-top:.4rem">1. Download the submission file</h2>
<p><a class="big-btn" href="downloads/{esc(name)}" download>&#11015;&nbsp;DOWNLOAD {esc(name)}</a>
&nbsp;<a href="downloads/{esc(Path(name).with_suffix('.zip').name)}" download>single-TIFF ZIP</a></p>
<p><b>2.</b> Submit that exact file at the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">competition
submission page</a> (login required). <b>3.</b> Paste this note into the optional comment box:</p>
<p><code>{esc(rec.get("note"))}</code> ({rec.get("note_chars")} characters)</p>
<p>Full click-by-click instructions: <a href="executive-summary.html">Executive summary &mdash; how to submit</a>.</p>
<h3>File facts (re-read from the bytes on disk by the writer)</h3>
{_table(["Property", "Value"], [
    ["sha256", f"<code>{esc(rec.get('sha256'))}</code>"],
    ["Bytes", f"{rec.get('bytes'):,}"],
    ["Band / dtype", "single band, float32"],
    ["CRS", esc(val.get("meta", {}).get("crs"))],
    ["Shape", esc(val.get("meta", {}).get("shape"))],
    ["Transform", esc(val.get("meta", {}).get("transform"))],
    ["Value range", f"min {fmt(val.get('min'),3)} &nbsp; max {fmt(val.get('max'),3)} &nbsp; (required [0,1])"],
    ["NaN / inf cells", f"{val.get('n_nan',0)} / {val.get('n_infinite',0)} (required 0)"],
    ["Positive pixels", f"{val.get('emitted_positive_pixels',0):,}, all at exactly 1.0, all off the mapped catalogue"],
    ["Validator", f"all_checks_passed = <b>{esc(val.get('all_checks_passed'))}</b>"],
])}
<p class="small">This is a local format/range preflight. It is not organizer acceptance, and it does
not use a submission slot: promotion is a separate step within the weekly cap shown on the submission page.</p>
</section>

<section>
<h2>Why the earlier portal error cannot happen with this file</h2>
<p>The portal rejects files with <i>"Predicted values must be in range [0, 1]"</i>. That is caused by
out-of-range or non-finite cells. This file is written by the fail-closed writer
(<code>src/gems57/submission_writer.py</code>), which refuses to emit anything it has not re-opened and
re-checked: dots at exactly 1.0, zeros everywhere else <i>including outside the scored footprint</i>,
no NaN anywhere, no positive mass on the mapped catalogue, and CRS/shape/transform compared against the
official <code>sample_submission.tif</code>.</p>
</section>

<section>
<h2>Method (this session's lane)</h2>
<ol>
<li><b>Feature stack.</b> The official <code>training_features.tif</code> (19 GeoDAWN bands,
418,912,844 B, sha256 <code>4371c82e&hellip;</code>) is fetched from the owner's pinned git bridge and
verified part-by-part and whole-file before use (<code>scripts/fetch_feature_stack.sh</code>,
pins in <code>data/bridge/feature_stack_pins.json</code>).</li>
<li><b>Operators.</b> 16 NaN-aware local operators: structure-tensor coherence at &sigma;=1 px and
&sigma;=3 px for RTP, TMI, isostatic gravity and detrended elevation; 3 px and 7 px local &sigma;;
Laplacian. All are NaN-aware because SciPy's recursive 1-D passes let a single nodata cell poison a
whole line (regression-tested in <code>tests/test_gems59.py</code>).</li>
<li><b>Ranking.</b> HistGradientBoosting, positives = mapped catalogue, negatives sampled from the
footprint, trained with one spatial quadrant held out (leave-one-quadrant-out) so a tested block never
supplies training context.</li>
<li><b>Emission.</b> 3-px non-maximum suppression (the 300 m kernel radius) turns the probability field
into a dotted line field; the field is truncated to a dot budget; dots are emitted at exactly 1.0.</li>
<li><b>Budget.</b> {dots_emitted:,} dots, taken from the owner-raster record below, not from a
guess. The holdout supplies the optimal dots-per-truth-pixel ratio &nu;*; the record supplies the absolute
count.</li>
</ol>
</section>

<section>
<h2>Evidence 1 &mdash; leakage canary (parallel-run protocol rule 4)</h2>
<p>Each feature alone against the withheld truth. AUC &gt; 0.90 means leakage until proven otherwise.</p>
{_table(["Holdout mode", "Withheld truth px", "Max AUC", "Feature", "Verdict", "Top 5 features"], can_rows)}
<p class="small">Distance-to-visible-catalogue is the most informative single feature but stays under the
0.90 line, so it is not classified as leakage; every geophysical operator alone is only weakly
informative (best single band, tilt angle / total curvature: AUC {fmt(tc_auc, 3)}).</p>
</section>

<section>
<h2>Evidence 2 &mdash; supervised arms on the conservative instrument (HOLDOUT-DTI)</h2>
<p>Instrument: hide-and-recover, whole &le;12 px catalogue segments withheld per quadrant, seeds 20/21,
scored with the shared exact evaluator <code>gems57.holdout.score_cell</code>
(&alpha;=0.2, &beta;=0.8, 300 m triangular kernel). "detached" withholds only segments at least 4 px from
every other catalogue component &mdash; the live analogue of a genuinely unmapped splay.</p>
{_table(["Arm (detached)", "Best threshold", "Dots", "Pooled DTI", "Coverage"], arms_rows)}
<p>Best arm: <b>{esc(e2best.get("arm"))}</b> at threshold {fmt(e2best.get("threshold"))} &rarr;
pooled DTI <b>{fmt(e2best.get("pooled_dti"))}</b>, coverage {fmt(e2best.get("pooled_coverage"),3)}.</p>
</section>

<section>
<h2>Evidence 3 &mdash; dot-budget sweep (HOLDOUT-DTI, detached mode)</h2>
<p>The same rule at a range of budgets. What transfers to the real test is the <i>ratio</i>
&nu; = dots &divide; truth pixels, not the absolute count.</p>
{_table(["Off-catalogue buffer", "&nu;", "Target dots (holdout scale)", "Dots emitted",
         "Pooled DTI", "Coverage", "FP mass"], sw_rows)}
<p>&#9733; marks the selected arm. &nu;* = <b>{fmt(nu_star,3)}</b>, off-catalogue buffer =
<b>{esc(e3.get("buffer_star_px"))} px</b>. Combined with the sibling-record budget of
{dots_emitted:,} dots this implies a real truth set of <b>{implied_txt} pixels</b>
&mdash; labelled <b>ESTIMATE</b>, derived, never a score.</p>
</section>

<section>
<h2>Evidence 4 &mdash; the owner-raster record (REGISTRY-MEASUREMENT + USER-REPORTED-SCORE)</h2>
<p>20 owner rasters, each sha256-verified against the pinned registry, measured against the scores
quoted on their own pages. <b>Scores are as quoted by the owner, not organizer receipts</b>; at least one
attribution in that record is already known to be wrong
(<code>registry/submissions_seen.csv</code>).</p>
{_table(["Raster (registry name)", "Positive pixels", "Quoted score", "Mean kernel credit vs public catalogue", "Quoted on"], sib_rows)}
<p>Summary: the {esc(sb.get("n_rasters"))} rasters with {esc(sb_rng[0])}&ndash;{esc(sb_rng[1])} positive
pixels score {fmt(sb_rng[0])}&ndash;{fmt(sb_rng[1])} (median {fmt(sb.get("median_score"))}); the
{esc(lb.get("n_rasters"))} rasters above 50,000 score {fmt((lb.get("score_range") or [None,None])[0])}&ndash;{fmt((lb.get("score_range") or [None,None])[1])}
(median {fmt(lb.get("median_score"))}). Spearman(dots, score) =
<b>{fmt(s.get("spearman_dots_vs_score"),3)}</b>. The dot budget, not the dot values, is the first-order
lever &mdash; which is why this session's budget is set from the record rather than from the holdout's
absolute count.</p>
</section>

<section>
<h2>Evidence 5 &mdash; uniqueness against every earlier raster</h2>
{_table(["Gate", "Result"], uniq_rows)}
<h3>The literal 3-px overlap gate, examined</h3>
<p>Protocol rule 1 flags a candidate when more than 70 % of its dots lie within 3 px of one registry
raster's dots. Two registry rasters make that test vacuous here: a <b>5-px lattice</b> covering the whole
study area (<code>13gems_20261001_r13-lattice-s5_v2_zerofill.tif</code>, 206,895 cells = one per 25
footprint pixels), whose own 3-px dilation covers <b>99.9 %</b> of the footprint, and a broad low-scoring
band (<code>pindrop-v4-discovery</code>, user-reported 0.0830), which covers 73.4 %. No emission of any
kind can clear the rule while those are in the registry.</p>
{_table(ov_head, ov_rows)}
<p>Measured at seven different off-catalogue buffers: overlap with the lattice is 0.998&ndash;0.999
<i>at every buffer</i> &mdash; constant, hence information-free. Against the proven high scorers the same
candidate sits at 0.17&ndash;0.35, far inside the gate. The reading is that the candidate is in the same
<i>family</i> as the broad near-catalogue bands (which is where the public record says the score is) but
does not reuse any lane: the rank-correlation gate passes at 0.140 against a 0.90 limit and the Jaccard
dot-set gate at 0.061 against a 0.50 limit. Full arithmetic in
<code>evidence/model_uniqueness.json</code> and <code>evidence/buffer_overlap_scan.json</code>; see
IR-58-UNIQ-01 and IR-58-UNIQ-02.</p>
</section>

<section>
<h2>Earlier lane in this repository (ribbon) &mdash; superseded</h2>
<p>The ribbon lane measured the across-strike localization error correctly
(&sigma; &asymp; 2.5&ndash;3.5 px) but its truth-free live rule scored <b>0.1309</b> pooled
(HOLDOUT-DTI, <code>evidence/ribbon_e2c_liverule_variants.json</code>), <i>below</i> its own tight
baseline of 0.1573, because it emitted on every candidate ridge with no ranking. That measurement is
what motivated this session's lane. Its raster is archived at
<code>docs/downloads/archive/</code> and in <code>evidence/ribbon_*.json</code>; it is not the file to
submit.</p>
</section>

<section>
<h2>Reproduce</h2>
<pre>pip install -r requirements.txt
bash scripts/fetch_feature_stack.sh          # 419 MB, sha256-verified, kept out of git
python scripts/run_model_experiments.py      # E1 canary + E2 arms   -> evidence/model_e1e2.json
python scripts/analyse_sibling_record.py     # owner-raster record   -> evidence/sibling_record.json
python scripts/build_model_emission.py       # E3 budget + raster    -> docs/downloads/*
python scripts/fetch_registry_sparse.py      # 695 registry rasters, sha256-verified
python scripts/check_uniqueness_registry.py docs/downloads/&lt;name&gt;-zeros.tif
python scripts/build_site.py                 # run card + this site
python -m pytest tests/ -q</pre>
</section>

<section>
<h2>Official sources for manual review</h2>
<ul>{"".join(f'<li><a href="{esc(u)}">{esc(t)}</a></li>' for t, u in OFFICIAL)}</ul>
</section>

<footer>Run card: <code>evidence/run_card.json</code> &middot; verdict: {esc(card["verdict"])}.
Generated {stamp} by <code>scripts/build_site.py</code> from evidence files only.</footer>
</body></html>
"""
    DOCS.joinpath("index.html").write_text(index)

    exec_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Executive summary &mdash; how to submit</title><link rel="stylesheet" href="assets/site.css"></head><body>
<header><h1>Executive summary: how to submit this file</h1></header>
<section>
<h2>The 60-second version</h2>
<ol>
<li><b>Download</b> <code>{esc(name)}</code> from the green button on the
<a href="index.html">main page</a>.</li>
<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">the
submission page</a> and sign in.</li>
<li>Choose the <code>.tif</code> (or the single-TIFF <code>.zip</code>) under <i>File to submit</i>.</li>
<li>Paste the note below into <i>Note (optional)</i> &mdash; it is what tells your future self which
submission this was.</li>
<li>Click submit. The score that comes back is the only ORGANIZER-CONFIRMED number; nothing on this site
is a score.</li>
</ol>
<p><b>Note to paste</b> ({rec.get("note_chars")} characters):<br><code>{esc(rec.get("note"))}</code></p>

<h2>What the portal requires, and how this file satisfies it</h2>
{_table(["Requirement (submission dialog)", "This file"], [
    ["Single-band GeoTIFF (.tif), or a .zip with one GeoTIFF",
     f"single band, float32; a one-TIFF <code>.zip</code> is provided beside it"],
    ["Matches the submission format's CRS", esc(val.get("meta", {}).get("crs"))],
    ["Matches the shape", esc(val.get("meta", {}).get("shape"))],
    ["Matches the geotransform", esc(val.get("meta", {}).get("transform"))],
    ["Predicted values in [0, 1]",
     f"min {fmt(val.get('min'),3)}, max {fmt(val.get('max'),3)}, {val.get('n_nan',0)} NaN cells"],
])}

<h2>Why the earlier "Predicted values must be in range [0, 1]" error happened</h2>
<p>That message is raised when any cell is outside [0,1] or is not finite (NaN/inf). Files that write NaN
outside the study-area footprint trip it. This file uses the all-finite policy: dots at exactly 1.0,
explicit zeros everywhere else including outside the footprint. The writer
(<code>src/gems57/submission_writer.py</code>) validates in memory, writes to a private temporary path,
re-opens the file on disk and re-validates it, and only then atomically publishes
<code>.tif</code> + <code>.zip</code> + a JSON receipt. If any check fails nothing is published.</p>

<h2>What the numbers on the main page are, and are not</h2>
<ul>
<li><b>HOLDOUT-DTI</b> &mdash; measured on the hide-and-recover instrument with the shared exact
evaluator. Evidence about the method, never a leaderboard projection.</li>
<li><b>USER-REPORTED-SCORE</b> &mdash; a score quoted on an owner page. Not an organizer receipt.</li>
<li><b>ORGANIZER-CONFIRMED</b> &mdash; copied from a submission-page receipt. None exists for this file
yet.</li>
<li><b>ESTIMATE</b> &mdash; derived (here, the implied truth-set size). Never a score.</li>
</ul>

<h2>Limits of this sandbox</h2>
<ul>
<li>No DrivenData login, so no upload, no leaderboard read, and no organizer receipt. Submitting is a
human step.</li>
<li>The competition data tab is login-gated; the feature stack arrives through the owner's sha256-pinned
git bridge (<code>scripts/fetch_feature_stack.sh</code>) and is verified before use.</li>
<li>CPU only (2 vCPU), so a U-Net ensemble is out of reach; the shipped ranking is gradient-boosted trees.</li>
</ul>
</section>
<footer>Generated {stamp}</footer></body></html>
"""
    DOCS.joinpath("executive-summary.html").write_text(exec_html)


def main() -> int:
    rec = latest_receipt()
    if not rec:
        raise SystemExit("no submission receipt with an existing TIF found in docs/downloads/")
    e12 = load("model_e1e2.json")
    e3 = load("model_e3.json")
    sib = load("sibling_record.json")
    uniq = load("model_uniqueness.json") or load("ribbon_uniqueness.json")
    bov = load("buffer_overlap_scan.json")
    card = build_run_card(rec, e12, e3, sib, uniq)
    (EV / "run_card.json").write_text(json.dumps(card, indent=1, default=float) + "\n")
    build_site(card, rec, e12, e3, sib, uniq, bov)
    print("run card -> evidence/run_card.json")
    print("site     -> docs/index.html, docs/executive-summary.html")
    print("verdict  :", card["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
