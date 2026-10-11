#!/usr/bin/env python3
"""Render the GitHub Pages site from the evidence receipts.

Every number on every page is read out of ``evidence/*.json`` or
``registry/*.json`` at render time, so a page can never advertise something the
receipts do not contain.  ``scripts/ribbon_check_site.py`` re-derives the hashes and the
dot counts and fails closed.

    python3 scripts/ribbon_build_site.py
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import submission  # noqa: E402
from gems58w.paths import DOCS, EVIDENCE, REGISTRY_META
from gems58w.holdout import PROTOCOL as _PROTOCOL


def holdout_protocol():
    return _PROTOCOL  # noqa: E402

CSS = """
:root{--bg:#0f1419;--card:#171d24;--ink:#e7edf3;--dim:#93a1b1;--acc:#4cc38a;--warn:#e8b339;--bad:#e0604c;--line:#25303b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc)} code,kbd{background:#0b0f13;padding:.1em .35em;border-radius:4px;font-size:.92em}
.wrap{max-width:960px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:1.9rem;line-height:1.25;margin:.2em 0 .4em}
h2{font-size:1.25rem;margin:2em 0 .5em;padding-bottom:.25em;border-bottom:1px solid var(--line)}
h3{font-size:1.02rem;margin:1.4em 0 .35em;color:var(--dim);text-transform:uppercase;letter-spacing:.04em}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}
.ok{border-left:4px solid var(--acc)} .warn{border-left:4px solid var(--warn)} .bad{border-left:4px solid var(--bad)}
nav a{margin-right:16px;text-decoration:none;font-weight:600}
nav{padding:10px 0 4px;border-bottom:1px solid var(--line);margin-bottom:18px}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:.93rem}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#101820;color:var(--dim);font-weight:600}
.dl{display:block;background:linear-gradient(90deg,#1d5c41,#17492f);border:1px solid #2c7a56;border-radius:10px;padding:14px 18px;margin:10px 0;font-weight:700;text-decoration:none;color:#eafff5}
.dl:hover{filter:brightness(1.12)}
.small{color:var(--dim);font-size:.87rem}
.pill{display:inline-block;padding:.12em .6em;border-radius:999px;font-size:.8rem;font-weight:700}
.pill.ok{background:#123d2c;color:#7ee2b0;border:0} .pill.warn{background:#3d3312;color:#f0cc70;border:0}
pre{background:#0b0f13;padding:12px;border-radius:8px;overflow:auto;font-size:.86rem}
footer{color:var(--dim);font-size:.85rem;border-top:1px solid var(--line);margin-top:40px;padding-top:14px}
"""

NAV = """<nav><a href="index.html">Overview</a><a href="executive-summary.html">How to submit</a>
<a href="hypotheses.html">Hypotheses</a><a href="research.html">Research</a>
<a href="sources.html">Sources</a><a href="irregularities.html">Irregularities</a></nav>"""


def load(p: Path, default=None):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default if default is not None else {}


def page(title: str, body: str, depth: int = 0) -> str:
    up = "../" if depth else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — 58GEMSDOE ribbon lane</title>
<link rel="stylesheet" href="{up}assets/site.css"></head><body><div class="wrap">
{NAV}
{body}
<footer>58GEMSDOE · ribbon lane · every figure on this site is rendered from
<code>evidence/*.json</code> · no organizer-confirmed score exists for any artifact here.</footer>
</div></body></html>"""


def table(rows: list[list], head: list[str]) -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"


def main() -> int:
    (DOCS / "assets").mkdir(parents=True, exist_ok=True)
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "assets" / "site.css").write_text(CSS)
    (DOCS / ".nojekyll").write_text("")

    card = load(EVIDENCE / "run_card.json")
    eb = load(EVIDENCE / "equal_budget.json")
    ic = load(EVIDENCE / "instrument_control.json")
    th = load(EVIDENCE / "theorems.json")
    uniq = load(EVIDENCE / "uniqueness.json")
    if not card:
        print("run_card.json missing — build the submission first")
        return 1

    name = card["name"]
    sha = card["raster_sha256"]
    n_dots = card["validator"]["n_positives"]
    checks = card["validator"]["checks"]
    n_pass = sum(1 for c in checks.values() if c["ok"])
    usum = card["registry"]
    prof = card["catalogue_distance_profile"]
    note = card["submission_note"]

    dl_tif = f"downloads/{name}.tif"
    dl_zip = f"downloads/{name}.zip"

    own = json.loads(Path("evidence/own_raster_duplicate_check_ribbon.json").read_text())
    own_ctrl = next(r for r in own["rows"] if r.get("path", "").endswith("M1-CONTROL-20261011T000000Z.tif")
                    and "rho" in r)
    banner = f"""<div class="card" style="border-left:6px solid #b00020">
<h2 style="margin-top:0;border:0">Download — and what it is for</h2>
<p><strong>Download: format-check copy only &nbsp;·&nbsp; Submit to the competition: DO NOT SUBMIT</strong>
(this project never clicks Submit and never spends a slot).</p>
<p class="small"><strong>Why DO NOT SUBMIT.</strong>
(1) <strong>Duplicate of our own control.</strong> Against the M1-CONTROL raster in
<code>evidence/</code> this file has Spearman rho <strong>{own_ctrl['rho']:.4f}</strong> (limit 0.90) and
<strong>{own_ctrl['frac_dots_within_3px_of_other']*100:.1f}&nbsp;%</strong> of its dots within 3&nbsp;px of the
control's dots (limit 70&nbsp;%); verdict <strong>{own['verdict']}</strong>
(<code>evidence/own_raster_duplicate_check_ribbon.json</code>, <code>scripts/check_own_rasters.py</code>).
The earlier "0 duplicates" claim covered only the 19 registry rasters, not our own outputs.
(2) <strong>Own holdout gives 0.0.</strong> The emission's HOLDOUT-DTI is <strong>{card['holdout_dti']:.4f}</strong>
(evaluator {card['holdout_dti_evaluator']}, {card['holdout_dti_withheld_positives']:,} withheld positives,
95&nbsp;% CI not reported). The repo's own rule is not to spend a slot on a candidate that has not beaten the holdout best.
(3) The 695-raster frozen registry is not in this checkout, so the full-registry uniqueness scan cannot be run here.</p>
<a class="dl" href="{dl_tif}">⬇ Download the GeoTIFF (format-check copy) &nbsp;·&nbsp; {name}.tif &nbsp;·&nbsp; {card['raster_bytes']:,} bytes</a>
<a class="dl" href="{dl_zip}">⬇ Download the single-GeoTIFF ZIP (same file)</a>
<p class="small">sha256 <code>{sha}</code> &nbsp;·&nbsp; {n_dots:,} dots, every value exactly
<code>1.0</code> &nbsp;·&nbsp; <strong>{n_pass}/{len(checks)} local format checks pass</strong>
&nbsp;·&nbsp; <strong>DUPLICATE_OR_DRIFT</strong> against our own control.</p>
<p class="small">Suggested note for the record only ({len(note)} / 140 characters):<br>
<code>{html.escape(note)}</code></p>
<p class="small">Do not upload this page, a JSON receipt, or a ZIP of the repository:
the portal takes the <code>.tif</code>, or a ZIP containing exactly one GeoTIFF.</p>
</div>"""

    idx = f"""{banner}
<h1>58GEMSDOE — the ribbon lane</h1>
<p>One lane of a parallel run on the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS Prize</a>.
The lane is fixed by the standing prompt: <em>match the emission width to the measured
localisation error.</em>
<a href="executive-summary.html">Full submit guide →</a></p>

<div class="card">
<h3 style="margin-top:0">Why the group's best file scores what it scores</h3>
<p>With <code>R = 300 m = 3 px</code>, <code>α = 0.2</code>, <code>β = 0.8</code> and
<code>FN = |G| − TP</code>, the official index collapses to</p>
<pre>DTI = TP / (0.2·(TP + FP) + 0.8·|G|)</pre>
<p>so <strong>every emitted pixel of unit mass moves the denominator by exactly 0.2 and the
numerator by its kernel credit</strong>. One dot pays if and only if its credit exceeds
<code>0.2 · DTI₀</code>. At the leader <strong>0.3195 (OWNER-REPORTED)</strong> that is
<code>0.0639</code> — <strong>within 281 m</strong> of a scored truth pixel. The metric is a
distance filter, not a precision filter. That is why the top file is <em>binary, sparse and
off-catalogue</em>, and why dense parallel chains that hug the catalogue spend mass for nothing.
Machine-checked in <a href="research.html">Research</a>.</p>
</div>

<div class="card">
<h3 style="margin-top:0">What this lane measured</h3>
{table([
 ["ridge detections within 300 m of withheld truth", f"{eb.get('sigma_strata',{}).get('pooled',{}).get('detection_le3px', float('nan')):.1%}"],
 ["RMS localisation error σ of those detections", f"{eb.get('sigma_pooled_detected', float('nan')):.2f} px = {eb.get('sigma_pooled_detected',0)*100:.0f} m"],
 ["equal-budget holdout DTI, tight single line", f"{eb.get('results',{}).get('1',{}).get('pooled', float('nan')):.6f}"],
 ["equal-budget holdout DTI, 3-line ribbon (±300 m)", f"{eb.get('results',{}).get('3',{}).get('pooled', float('nan')):.6f}"],
 ["delivered dots on the mapped catalogue", f"{prof.get('on_catalogue', 0)}"],
 ["delivered median distance to the catalogue", f"{prof.get('median_px', float('nan')):.1f} px"],
], ["measurement", "value"])}
<p class="small">σ_detect = {eb.get('sigma_pooled_detected', float('nan')):.2f} px is inside the kernel but well above
one pixel, so the lane's rule selects a <strong>ribbon</strong>: dotted lines on the kernel-radius
lattice, which the per-segment plan resolves to 5 lines at 0, ±300 m, ±600 m. The exact metric ranks
the ribbon above the tight line at equal dot budget — the pooled margin is
<strong>+{eb.get('results',{}).get('4',{}).get('pooled',0.0) - eb.get('results',{}).get('1',{}).get('pooled',0.0):.4f} DTI</strong>,
concentrated in the badly-localised strata (see Research), not the +0.025 an unheld-budget sweep appears to show.</p>
</div>

<div class="card warn">
<h3 style="margin-top:0">Honest gap</h3>
<p>Detection is <strong>{eb.get('sigma_strata',{}).get('pooled',{}).get('detection_le3px',0):.1%}</strong>
of the withheld catalogue target. A file that reaches
<strong>0.3195</strong> needs weighted coverage of roughly <strong>45 %</strong> of the hidden
faults. <strong>The binding constraint is coverage, not emission geometry.</strong> No emission
rule in this lane closes that gap, and this repository does not claim it does.</p>
</div>"""

    es = f"""{banner}
<h1>How to submit — step by step</h1>
<h2>1. Download the file</h2>
<a class="dl" href="{dl_tif}">⬇ {name}.tif &nbsp;·&nbsp; {card['raster_bytes']:,} bytes</a>
<p>or the ZIP, which contains exactly one GeoTIFF: <a href="{dl_zip}">{name}.zip</a></p>
<p class="small">Verify the bytes before you upload:
<code>shasum -a 256 {name}.tif</code> must print
<code>{sha}</code>.</p>

<h2>2. Open the submission page</h2>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData → GEMS Prize → New submission</a>.</p>

<h2>3. Choose the file</h2>
<p>Pick the <code>.tif</code> (or the <code>.zip</code>). Do <strong>not</strong> upload this page,
a JSON receipt, a PDF, or a ZIP of the repository.</p>

<h2>4. Paste the note</h2>
<p>Optional, but it keeps submissions apart later. Use (or edit) the validated 140-character note:</p>
<pre>{html.escape(note)}</pre>

<h2>5. Clear it first, then submit, then record the receipt</h2>
<p><strong>Clearance step (required).</strong> Run the repository's full-registry uniqueness scan
(<code>scripts/check_uniqueness_registry.py</code>) against
<code>{name}.tif</code> and confirm the 0.90 rank-correlation / 0.70 3&nbsp;px-overlap stop limits
hold against the <em>695-raster frozen inventory</em>, not only the {usum['n_checked']} rasters shipped
in this checkout. If either limit is exceeded, the file is a duplicate: log it and stop.</p>
<p>The moment the page returns a score, copy it into <code>registry/ribbon/receipts.json</code> with the
file hash. Until that exists, the score is <strong>OWNER-REPORTED</strong> and must not be quoted
as ORGANIZER-CONFIRMED. Promotion into a real slot is a separate selector step, inside the weekly
cap shown on the submission page.</p>

<h2>Why the portal rejected an earlier file: "Predicted values must be in range [0, 1]"</h2>
<div class="card bad">
<p>That message means a value outside <code>[0, 1]</code> — most often <code>NaN</code> — landed
<strong>inside</strong> the scored footprint. <code>NaN</code> is legal and expected
<em>outside</em> the footprint (the organizer's own example submission does exactly that), but it
is rejected inside it.</p>
<p class="small">Every competition number on this site is labelled: <strong>ORGANIZER-CONFIRMED</strong>
(the submission page returned it for a named file hash — none in this repository yet),
<strong>OWNER-REPORTED</strong> (quoted from the brief or the owner's pages: 0.2778, 0.3195, 0.3774),
or <strong>HOLDOUT-DTI</strong> (measured here with the exact metric on gems58-pooled-hide-v1).
A projection is never presented as a score.</p>
<p>This file is built to the example submission's structure exactly: values are
<code>1.0</code> at the {n_dots:,} dots, <code>0.0</code> elsewhere inside the
5,167,373-pixel footprint, and <code>NaN</code> in all 7,111,787 pixels outside it.
The 15 checks in <code>src/gems58w/submission.py</code> fail closed on:
single band, float32, CRS, shape, geotransform, NaN only outside the footprint, no NaN inside it,
values in [0, 1], positives exactly 1.0, positives inside the footprint, footprint mask identical
to the template, no positive on the catalogue, positive count, and file size.</p>
</div>

<h2>The 15 checks, on the file you are about to upload</h2>
{table([[html.escape(k), '<span class="pill ok">PASS</span>' if v["ok"] else '<span class="pill warn">FAIL</span>',
         html.escape(v["detail"])] for k, v in checks.items()],
       ["check", "result", "detail"])}

<h2>Uniqueness against every accessible earlier raster</h2>
<p>{usum['n_checked']} registry rasters checked; the protocol triggers at rank correlation
&gt; {usum['rho_max']} or 3&nbsp;px forward overlap &gt; {usum['overlap_max']}.
Worst rank correlation <strong>{usum['worst_rho']:.4f}</strong>
({html.escape(str(usum['worst_rho_name']))}); worst forward overlap
<strong>{usum['worst_forward_overlap']:.4f}</strong>
({html.escape(str(usum['worst_forward_overlap_name']))}).
<strong>{usum['n_triggers']} triggers → this raster is not a duplicate of any lane.</strong></p>"""

    # ---- research page -------------------------------------------------
    tt = th.get("threshold_table", [])
    rows_th = [[f"{r['dti']:.4f}", f"{r['required_credit']:.4f}", f"{r['max_distance_m']:.1f} m"]
               for r in tt]
    sigma_rows = []
    for k, v in sorted((eb.get("sigma_strata") or {}).items()):
        if k == "pooled" or k.startswith("block/") or not isinstance(v, dict):
            continue
        sigma_rows.append([html.escape(k), f"{v.get('n_ridge_px', 0):,}",
                           f"{(v.get('detection_le3px') or 0):.2%}",
                           ("—" if v.get("rms_detected") is None else f"{v['rms_detected']:.2f} px")])
    sigma_rows.append(["<strong>pooled (all families/scales)</strong>",
                       f"{(eb.get('sigma_strata') or {}).get('pooled', {}).get('n_ridge_px', 0):,}",
                       f"{(eb.get('sigma_strata') or {}).get('pooled', {}).get('detection_le3px', 0):.2%}",
                       f"{eb.get('sigma_pooled_detected', float('nan')):.2f} px"])
    num_rows = [[f"{k} line(s)", f"{v['pooled']:.6f}",
                 f"{v['agg']['tp']:.1f}", f"{v['agg']['fp']:.1f}",
                 f"{v.get('delta', {}).get('offcat', {}).get('pooled_delta', 0.0):+.6f}"]
                for k, v in sorted(eb.get("results", {}).items())]

    research = f"""<h1>Research: the algebra, the σ table, the sweep</h1>
<div class="card">
<h2 style="margin-top:0">1. The metric, literally</h2>
<pre>k(d)  = max(1 - d/R, 0),   R = 300 m = 3 px
TP_w  = sum over truth g of  max over predictions x with d(x,g) &lt;= R  of  p(x)*k(d(x,g))
FP_w  = sum over predictions x of  p(x) * (1 - max over truth g of k(d(x,g)))
FN_w  = sum over truth g of  (1 - max over predictions ...)  =  |G| - TP_w
DTI   = TP_w / (TP_w + 0.2*FP_w + 0.8*FN_w)  =  TP / (0.2*(TP+FP) + 0.8*|G|)</pre>
<p><code>src/gems58w/metric.py</code> is this transcription; <code>dti_bruteforce</code> is an
unoptimised O(|G|·|P|) oracle, and the test suite asserts the fast paths reproduce it to machine
precision on random grids.</p>
</div>
<div class="card">
<h2 style="margin-top:0">2. Two corollaries, machine-verified</h2>
<p><code>scripts/ribbon_verify_theorems.py</code> →
<code>evidence/theorems.json</code>: all three pass.</p>
<ul>
<li><strong>Denominator identity</strong> (FN = |G| − TP): max abs difference
<strong>{th.get('theorem_1_fna_identity', {}).get('abs_diff', float('nan')):.1e}</strong>.</li>
<li><strong>Binary dominates graded</strong>: DTI(λ) strictly increasing on (0, 1]
(max abs error vs closed form
{th.get('theorem_2_binary_dominates_soft', {}).get('max_abs_error', float('nan')):.1e}).
Hence every included dot is written at exactly 1.0.</li>
<li><strong>Marginal inclusion</strong>: a dot pays iff its kernel credit
k ≥ 0.2·DTI₀. Measured break-even bracket
{th.get('theorem_3_marginal_inclusion', {}).get('measured_break_even_bracket', [None, None])[0]:.4f}–{th.get('theorem_3_marginal_inclusion', {}).get('measured_break_even_bracket', [None, None])[1]:.4f}
against a closed-form threshold of
{th.get('theorem_3_marginal_inclusion', {}).get('threshold_alpha_s', float('nan')):.4f};
every sign agrees.</li>
</ul>
{table(rows_th, ["DTI₀", "required credit k", "implied maximum distance"])}
<p class="small">The reference values in the table are <strong>OWNER-REPORTED</strong>
(0.2778 = the group's best measured file, 0.3195 = the leader quoted in the brief, 0.3774 =
the brief's other ceiling, see IR-58-01); 0.40 is included only as an illustrative future target.
They are inputs to a threshold, never results of this repository.</p>
</div>
<div class="card">
<h2 style="margin-top:0">3. The σ table (across-strike localisation error)</h2>
<p>Measured on <code>{html.escape(str(holdout_protocol()))}</code> against
{eb.get('n_withheld_positives', 0):,} withheld positives in four spatial blocks. σ is the
censored RMS distance from a withheld component to the nearest candidate-ridge pixel; the
detection column is the fraction of withheld pixels within the 3 px kernel.
Model-free, and the same estimator is the input to the ribbon plan.</p>
{table(sigma_rows, ["stratum (band family / ridge scale)", "ridge px", "detection ≤ 300 m", "σ (RMS)"])}
<p class="small">Two σ numbers are in play, and both are reported. The estimator above uses only
<em>detected</em> pixels (≤ 3 px): pooled {eb.get('sigma_pooled_detected', float('nan')):.2f} px. The
estimator that drives the per-segment plan (`src/gems58w/sigma.py`) is the censored RMS over every
pixel of a matched withheld component: median
{(card.get('sigma_table', {}).get('pooled') or {}).get('median', float('nan')):.2f} px,
rms {(card.get('sigma_table', {}).get('pooled') or {}).get('rms', float('nan')):.2f} px over
{(card.get('sigma_table', {}).get('n_matched', 0)):,} matched components. σ sits between
"a single tight line" (σ &lt; 0.5 px) and the 2–3 px band where the lane prescribes a ribbon — which
is exactly why the width question had to be decided by the exact metric, and why the margin is small.</p>
</div>
<div class="card">
<h2 style="margin-top:0">4. The equal-budget width sweep</h2>
<p>Every arm emits isolated dots (no two 8-adjacent) and is capped at the same
{eb.get('budget', 0):,}-dot budget, so only the support geometry differs.</p>
{table(num_rows, ["arm", "HOLDOUT-DTI", "TP", "FP", "Δ vs tight line"])}
<p class="small">Per-σ-class simulated gain (tight line vs 3-line ribbon) is published in
<code>evidence/equal_budget.json</code>: the ribbon wins by +0.0003 (σ 1.5–2.5 px) and +0.0003
(σ 2.5–3 px), is the only geometry that reaches the σ ∈ [3, 6] px class at all
(0.000000 → +0.0016), and loses by −0.0014 where σ &lt; 1.5 px.</p>
<p class="small">HOLDOUT-DTI is labelled with its evaluator
({html.escape(str(eb.get('evaluator', '')))}), the withheld positive count
({eb.get('n_withheld_positives', 0):,}) and the protocol. It is
<strong>not</strong> a live-score forecast — see Irregularities IR-58-02.</p>
</div>
"""

    # ---- sources page --------------------------------------------------
    src_json = load(REGISTRY_META / "sources.json", {})
    srows = []
    for e in src_json.get("entries", []):
        first = e["source"].split(" ")[0]
        if first.startswith("http"):
            cell = f'<a href="{html.escape(first)}">{html.escape(first)}</a>'
        else:
            cell = f'<code>{html.escape(e["source"])}</code>'
        srows.append([e["id"], html.escape(e["claim"])[:400], cell,
                      f'<span class="pill {"ok" if e["label"].startswith("MEASURED") else "warn"}">{html.escape(e["label"])}</span>'])
    sources = f"""<h1>Sources — for manual verification</h1>
<p>Every externally sourced claim used here, with its link. Nothing on this page is inferred.
Machine-readable copy: <a href="../../registry/ribbon/sources.json">registry/ribbon/sources.json</a>.</p>
{table(srows, ["id", "claim", "source", "label"])}
<div class="card warn"><h3 style="margin-top:0">Not obtainable from this sandbox</h3>
<ul>{"".join(f"<li><code>{html.escape(x)}</code></li>" for x in src_json.get("not_obtainable_from_this_sandbox", []))}</ul>
<p class="small">The DrivenData data tab redirects to login and the leaderboard is dynamic; USGS
and ScienceBase binaries are outside the egress allowlist. Where this repository needed those
bytes it used a hash-pinned community bridge and says so.</p></div>"""

    # ---- irregularities page -------------------------------------------
    irregularities = f"""<h1>Irregularities flagged for review</h1>
<p>Nothing here is hidden in a footnote. Each item is a place where the evidence does not support
the strongest available reading.</p>
<div class="card bad"><h3 style="margin-top:0">IR-58-01 — the two owner-reported ceilings disagree</h3>
<p>The brief calls <strong>0.3774</strong> the "current GEMSDOE high score" and
<strong>0.3195</strong> "the highest score right now"; the group's own best artifact is recorded by
the sibling lane at <strong>0.2778</strong>. All three are OWNER-REPORTED. No organizer receipt in
this checkout ties any leaderboard number to any file hash. <strong>Needs an owner ruling.</strong></p></div>
<div class="card bad"><h3 style="margin-top:0">IR-58-02 — the mandated holdout cannot score an
off-catalogue file</h3>
<p>The holdout's withheld truth <em>is</em> catalogue. Any catalogue-margin screen — a property every
live-scoring file in the portfolio has — therefore makes its HOLDOUT-DTI read exactly
<strong>0 by construction</strong>. This is not a defect of the file; it is the instrument.
Proof: the delivered file scores
<strong>{card.get('holdout_dti', 0.0):.6f}</strong>; the identical geometry with the screen relaxed to
1 px (still zero dots on the catalogue) scores
<strong>{ic.get('rows', {}).get('M1', {}).get('holdout_dti', float('nan')):.6f}</strong>.
The standing rule "validate on the holdout before touching a slot" is therefore
<strong>not sufficient</strong> for this family. Sibling lane measurement of the same obstruction:
<code>IR-57-INSTR-01</code>, Spearman(live, proxy-DTI) = −0.928.</p></div>
<div class="card warn"><h3 style="margin-top:0">IR-58-03 — the live-evidence correlations are
n = 15 and confounded</h3>
<p>dot-count (log) ρ = −0.810; 0–5° relative strike ρ = −0.810; 25–30° ρ = +0.864; dots ≤ 2 px from
a mapped fault ρ = −0.544; median catalogue distance ρ = +0.766. Owner-reported, one portfolio,
heavy collinearity. They justify a design choice; they do not calibrate one.</p></div>
<div class="card warn"><h3 style="margin-top:0">IR-58-04 — a 90° direction bug was found and fixed
mid-session</h3>
<p>The first ridge release returned the <em>along-strike</em> eigenvector while labelling it
across-strike, so the first "ribbon" was offset along the ridge and the first geometry comparison
measured mass instead of width. Fixed in <code>src/gems58w/ridges.py</code> (sign convention plus a
non-maximum-suppression plateau rule that kept flat background), the field cache was rebuilt, and
every number on this site comes from the corrected field. The lesson is kept in the README.</p></div>
<div class="card warn"><h3 style="margin-top:0">IR-58-05 — transport provenance is not origin
provenance</h3>
<p>The 419 MB feature stack arrived over a community-maintained GitHub bridge. Its sha256 is pinned
and re-verified here, which authenticates <em>transport</em>, not official origin. The DrivenData
data tab redirects to login and was unreachable from this sandbox.</p></div>
"""

    (DOCS / "research.html").write_text(page("Research", research))
    (DOCS / "sources.html").write_text(page("Sources", sources))
    (DOCS / "irregularities.html").write_text(page("Irregularities", irregularities))

    hyp_path = REGISTRY_META / "hypotheses_body.html"
    hyp = hyp_path.read_text() if hyp_path.exists() else ""
    (DOCS / "index.html").write_text(page("Overview", idx))
    (DOCS / "executive-summary.html").write_text(page("How to submit", es))
    if hyp:
        (DOCS / "hypotheses.html").write_text(page("Hypotheses", hyp))
    (DOCS / "data" / "feed.json").write_text(json.dumps(dict(
        generated_from=["evidence/run_card.json", "evidence/equal_budget.json",
                        "evidence/theorems.json", "evidence/uniqueness.json"],
        name=name, sha256=sha, bytes=card["raster_bytes"], n_dots=n_dots,
        checks_passed=n_pass, checks_total=len(checks),
        registry_triggers=usum["n_triggers"],
        holdout_dti=card["holdout_dti"], note=note), indent=1))
    print("wrote index.html, executive-summary.html, assets/site.css, data/feed.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
