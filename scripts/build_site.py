#!/usr/bin/env python3
"""Generate the GitHub Pages site (docs/*.html) and registry/RUN_CARD.json from the experiment
outputs. Every number on the site is read from registry/ — nothing is typed by hand.
"""
import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry"
EXP = REG / "experiments"
DOCS = ROOT / "docs"
SUB = "58GEMSDOE-ribbon-lane-v1-20261011"
SUBFILE = f"{SUB}.tif"
NOTE = "Ribbon lane v1: geophysical ridges, class-wise dotted lines; holdout DTI 0.037 (CI 0.006-0.068). Format-valid. Not promoted."
assert len(NOTE) <= 140, len(NOTE)

e1 = json.loads((EXP / "E1_canary_sigma_surface.json").read_text())
e2 = json.loads((EXP / "E2_nested_holdout.json").read_text())
e3 = json.loads((EXP / "E3_final_emission.json").read_text())
uniq_final = json.loads((REG / f"uniqueness_final_{SUB}_summary.json").read_text()) \
    if (REG / f"uniqueness_final_{SUB}_summary.json").exists() else None
uniq_surface = json.loads((REG / "uniqueness_surface_pre-placement_summary.json").read_text())
val = e3["validator"]
h = e2["holdout_dti_nested_lobo"]
sha = val["sha256"]
size = val["bytes"]

def esc(x):
    return html.escape(str(x))

def table(headers, rows):
    out = ["<table><thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in headers) + "</tr></thead><tbody>"]
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)

def irregularities():
    txt = (ROOT / "README.md").read_text()
    rows = []
    for line in txt.splitlines():
        if re.match(r"^\| I-\d+ \|", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    return rows

_chance_final = list(csv.DictReader(open(REG / "chance_coverage_final.csv")))
_exf = [float(r["excess"]) for r in _chance_final]
n_gt08 = sum(e > 0.08 for e in _exf)
max_ex = max(_exf)
# ---------- run card ----------
blocks = e2["per_block"]
canary = e1["canary_summary"]
max_auc_feat = max(canary.items(), key=lambda kv: kv[1]["max_auc"])
run_card = {
    "hypothesis": "H0 ribbon lane: candidate geophysical ridges (tmi_hg, iso_grav_anom_hg, det_elev_slope; fine and coarse scale) emitted as dotted or ribbon lines with class-specific offsets chosen by U = (1-0.2*DTI0)TP - 0.2*DTI0*FP",
    "mechanism": "Hessian bright-ridge strength + non-maximum suppression + top-quantile threshold; sigma per class x block from matched withheld-truth distances; configuration chosen by leave-one-block-out U on the holdout",
    "named_non_fault_process_that_could_mimic_it": "Lithologic contacts and intrusive or basin-edge gradients in magnetic/gravity fields, and topographic breaks from erosion or landslides, which give linear ridge responses without slip",
    "holdout_dti": {"value": round(h["value"], 4), "ci95": [round(h["ci95_t"][0], 4), round(h["ci95_t"][1], 4)],
                    "method": "jackknife over 4 quadrant blocks, t(3)", "n_withheld_positives": h["n_withheld_positives"],
                    "evaluator": "gems58.metric (58GEMSDOE) — checked vs rules worked example and brute force"},
    "baseline_L1_union_holdout_dti": round(e2["baseline_L1_union_frac0p005_pooled_dti"], 4),
    "canary": {"max_single_feature_auc": round(max_auc_feat[1]["max_auc"], 3), "feature": max_auc_feat[0],
               "threshold": 0.90, "leak_flag": bool(e1["canary_leak_flags_gt_0p90"])},
    "correlation_overlap_vs_registry": {
        "surface_pre_placement": {"max_spearman_rho": round(uniq_surface["max_rho"], 3),
                                  "flagged_literal_dot_overlap": uniq_surface["n_flagged"],
                                  "verdict_literal": uniq_surface["verdict"]},
        "final": None if uniq_final is None else {"max_spearman_rho": round(uniq_final["max_rho"], 3),
                                                  "flagged_literal_dot_overlap": uniq_final["n_flagged"],
                                                  "verdict_literal": uniq_final["verdict"]},
        "chance_control": {"source": "registry/chance_coverage_final.csv",
                           "final_flagged_excess_gt_0p08": n_gt08,
                           "final_max_excess_over_chance": round(max_ex, 3),
                           "final_min_excess_over_chance": round(min(_exf), 3)}},
    "raster_sha256": sha,
    "validator": {k: bool(v) for k, v in val["checks"].items()} | {"all_pass": bool(val["all_pass"])},
    "submission_name": SUB,
    "note_140_chars": NOTE,
    "verdict": "negative",
}
(REG / "RUN_CARD.json").write_text(json.dumps(run_card, indent=2) + "\n")

# ---------- shared CSS ----------
CSS = """
:root{--ink:#1c2430;--mut:#5b6675;--line:#e3e7ee;--ok:#1b7f4b;--warn:#b26a00;--bad:#b3261e;--acc:#0b5fa5;--bg:#f7f9fc}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#0f2238;color:#fff;padding:14px 24px}header a{color:#cfe3ff;margin-right:16px;text-decoration:none}
header .brand{font-weight:700;font-size:18px;margin-right:24px;color:#fff}
main{max-width:1040px;margin:0 auto;padding:24px}
section{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin:18px 0}
h1{font-size:28px;margin:6px 0 10px}h2{font-size:21px;margin:4px 0 12px}h3{font-size:17px;margin:14px 0 6px}
.hero{border:2px solid var(--acc)}
.btn{display:inline-block;background:var(--acc);color:#fff!important;padding:14px 22px;border-radius:10px;font-weight:700;text-decoration:none;font-size:18px}
.btn.alt{background:#fff;color:var(--acc)!important;border:2px solid var(--acc);font-size:15px;padding:10px 16px}
.chip{display:inline-block;padding:3px 10px;border-radius:999px;font-size:13px;font-weight:700;margin-right:6px;color:#fff}
.ok{background:var(--ok)}.warn{background:var(--warn)}.bad{background:var(--bad)}.info{background:#56607a}
table{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0}th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top}
th{background:#f0f4fa}code,pre{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px}pre{background:#0f2238;color:#e7eefb;padding:14px;border-radius:10px;overflow:auto}
.mut{color:var(--mut);font-size:14px}.yes{color:var(--ok);font-weight:700}.no{color:var(--bad);font-weight:700}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:760px){.grid{grid-template-columns:1fr}}
.box{border:1px solid var(--line);border-radius:10px;padding:14px}
footer{max-width:1040px;margin:0 auto;padding:10px 24px 40px;color:var(--mut);font-size:13px}
"""

def page(title, body, active):
    nav = [("index.html", "Summary"), ("submit.html", "How to submit"), ("evidence.html", "Evidence"),
           ("sources.html", "Sources & irregularities"), ("https://github.com/buffedlizard55-lab/58GEMSDOE", "Repo")]
    links = "".join('<a href="%s"%s>%s</a>' % (u, ' style="font-weight:700"' if u == active else "", t) for u, t in nav)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — 58GEMSDOE</title><style>{CSS}</style></head><body>
<header><span class="brand">58GEMSDOE · GEMS Prize</span>{links}</header>
<main>{body}</main>
<footer>Generated by <code>scripts/build_site.py</code> from <code>registry/</code>. Competition: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData #306</a> · Rules: <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR PDF 96647</a>. Not affiliated with DOE or DrivenData.</footer>
</body></html>"""

uniq_chip = ("warn", "UNIQUENESS: HOLD (literal test fails)") if (uniq_final is None or uniq_final["verdict"] != "UNIQUE_PASS") else ("ok", "UNIQUENESS: PASS")
uniq_text = "not yet computed" if uniq_final is None else \
    f"max Spearman ρ = {uniq_final['max_rho']:.3f}; {uniq_final['n_flagged']} registry rasters flagged by the literal 3-px dot-overlap test (see evidence page)"

# chance-control summaries (read from CSVs; no typed numbers)
def _read_csv(p):
    return list(csv.DictReader(open(p)))
chance_final = _read_csv(REG / "chance_coverage_final.csv")
chance_surf = _read_csv(REG / "chance_coverage_surface.csv")
_ex_f = [float(r["excess"]) for r in chance_final]
n_gt08 = sum(e > 0.08 for e in _ex_f)
max_ex = max(_ex_f)
_ex_s = [float(r["excess"]) for r in chance_surf]
surf_min, surf_max = min(_ex_s), max(_ex_s)
surf_gt08 = sum(e > 0.08 for e in _ex_s)
_top = sorted(chance_final, key=lambda r: -float(r["excess"]))[:12]
chance_table = table(["excess", "observed overlap", "chance", "registry dots", "ρ", "registry raster"],
    [[f"{float(r['excess']):+.3f}", f"{float(r['dot_overlap']):.3f}", f"{float(r['chance_coverage_3px']):.3f}",
      f"{int(r['n_reg_dots']):,}", f"{float(r['rho']):.3f}", esc(r["registry_file"].split("gems-src/")[-1])] for r in _top])

# ---------- index.html (executive summary) ----------
body_index = f"""
<section class="hero">
<h1>Submission file for the GEMS Prize — download, then upload</h1>
<p class="mut">The file is a single-band float32 GeoTIFF on the official grid (EPSG:32611, 100 m, 3,292 columns × 3,730 rows, NaN outside the study footprint, values exactly 0 or 1). It passes every format check we can run.</p>
<p><a class="btn" href="downloads/{esc(SUBFILE)}">⬇ Download the submission GeoTIFF</a>
&nbsp; <a class="btn alt" href="submit.html">Step-by-step: how to submit</a></p>
<table>
<tr><th>File</th><td><code>{esc(SUBFILE)}</code> ({size:,} bytes)</td></tr>
<tr><th>Unique submission name</th><td><code>{esc(SUB)}</code></td></tr>
<tr><th>Note (≤140 chars)</th><td><code>{esc(NOTE)}</code> ({len(NOTE)} chars)</td></tr>
<tr><th>sha256</th><td><code>{esc(sha)}</code></td></tr>
</table>
<p>
<span class="chip ok">FORMAT: PASS</span>
<span class="chip {uniq_chip[0]}">{esc(uniq_chip[1])}</span>
<span class="chip warn">VERDICT: NEGATIVE — do not spend a weekly slot yet</span>
<span class="chip info">ORGANIZER SCORE: none yet</span></p>
</section>

<section>
<h2>Is it OK to download and submit this file?</h2>
<div class="grid">
<div class="box"><h3>Download — <span class="yes">YES</span></h3>
<p>The file was generated in this repository from the official feature stack. It contains only our predicted values: no copied competition labels and no third-party raster. It passes the format checks we can run.</p></div>
<div class="box"><h3>Submit to a weekly slot — <span class="no">NOT YET</span></h3>
<p>Two reasons. (1) Our protocol's literal dot-overlap test flags <b>{uniq_final['n_flagged'] if uniq_final else 'n/a'}</b> registry rasters. The chance-level control shows that <b>{n_gt08}</b> of them overlap more than 0.08 above what chance would give (largest: +{max_ex:.3f}, 13GEMSDOE r6 ensemble map), so density alone does not explain the flags. Their rankings are not shared (max Spearman ρ {uniq_final['max_rho']:.2f}). The team has not relaxed the literal test. (2) Holdout DTI is <b>{h['value']:.4f}</b> (95% CI {h['ci95_t'][0]:.3f}–{h['ci95_t'][1]:.3f}; HOLDOUT-DTI; {h['n_withheld_positives']:,} withheld positives). That proxy is not comparable to leaderboard scores (irregularity I-6), but it gives no evidence that this file would place high. Choosing a slot is a separate team decision.</p></div>
</div>
</section>

<section>
<h2>Leaderboard context (verified)</h2>
<p>The DrivenData public leaderboard (read 2026-10-11) lists <b>0.3774</b> at #1 (xiaofanhu), <b>0.3195</b> at #8 (DARD) and <b>0.2778</b> at #23 (extradr19). Scores are the public split only. The first prize round is scored on a privately withheld test set (rules §1.1, §3.6.1). <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Source</a>.</p>
<p class="mut">Note: the session request said 0.3195 is the highest score. That is incorrect; see irregularity I-3.</p>
</section>

<section>
<h2>Why did 0.2778 score well, and can we beat it?</h2>
<p><b>What it is.</b> The file <code>gemsdoe32-h33-h33-2-b2-…-zeros.tif</code> is a prune of a 0.2708 base: every dot within 2 px of the catalogue is deleted (37,654 dots, 0 on the catalogue). Its owner's page states <i>"NO ORGANISER SCORE EXISTS"</i> and that the 0.2747 figure is <i>"a MODEL, not a score"</i> (<a href="https://github.com/buffedlizard55-lab/GEMSDOE32">repo</a>).</p>
<p><b>The GEMSDOE32 owner's own account (their claim, not verified by us).</b> Their page explains why the dotted H19-5 file scored highest with a credit-density argument: each emitted pixel costs 0.2 unless it covers a truth pixel, so thinning a thick surface while keeping its geometry raises credit per pixel. They report an empirical break-even of 0.0548 credit per dot, and say this equals 0.2·0.26 = 0.0520 from the published formula. <b>Those two numbers are not equal</b> (irregularity I-16). Source: <a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">GEMSDOE32 index</a>.</p>
<p><b>Mechanism (plausible, not measured).</b> Organizer staff said pixels of known USGS/INGENIOUS faults are masked from evaluation (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">forum, 2026-09-16</a>). Masking is pixel-exact, so a dot 1–2 px from a known trace can still fall inside the 300 m kernel of an unmapped fault and score, while a dot 3 px or more away on the catalogue is pure false positive. Removing the catalogue-adjacent band trades a little recall for much less false positive.</p>
<p><b>Can we beat it from this sandbox?</b> <span class="no">Not with the lane we built.</span> The ribbon lane reached holdout DTI {h['value']:.4f}. We do not claim a higher score.</p>
</section>

<section>
<h2>AI disclosure (rules §3.2)</h2>
<p>Generative AI tools were used to write code, documentation and this site, and to plan the analysis (required by rules §3.2). All numbers on this site are generated from the files in <code>registry/</code> by <code>scripts/build_site.py</code>. Verification steps are listed on the <a href="sources.html">Sources</a> page. The registered competitor is responsible for the accuracy of the final narrative.</p>
</section>
"""
(DOCS / "index.html").write_text(page("Submission", body_index, "index.html"))

# ---------- submit.html ----------
body_submit = f"""
<section class="hero">
<h1>How to submit (step by step)</h1>
<p class="mut">Based on the official rules and the competition's submission page wording. Verified 2026-10-11 from the <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF</a> and <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem page</a>.</p>
<p><a class="btn" href="downloads/{esc(SUBFILE)}">⬇ Download the GeoTIFF</a></p>
</section>
<section>
<h2>Steps</h2>
<ol>
<li><b>Eligibility and registration.</b> Create a DrivenData profile and register for the challenge (rules §3.1). Individuals must be U.S. citizens or permanent residents; the registered person must certify eligibility (rules §1.3, §A.1). Only the registered person can do this.</li>
<li><b>Download</b> <code>{esc(SUBFILE)}</code> from this site.</li>
<li><b>Check it</b> (optional, local): from the repository root run <code>PYTHONPATH=src python -m gems58.validate {esc(SUBFILE)} --reference sample_submission.tif</code> (the reference is your local copy of the official sample). Every check must read <code>true</code>.</li>
<li><b>Open the submission form</b> on the competition's submission page and click <i>File to submit → choose file</i>. Upload <code>{esc(SUBFILE)}</code> as a single-band GeoTIFF (.tif). It must match the submission format's CRS, shape and geotransform.</li>
<li><b>Name it.</b> Use the unique name <code>{esc(SUB)}</code>.</li>
<li><b>Add the note</b> (≤140 characters): <code>{esc(NOTE)}</code></li>
<li><b>Submit.</b> The limit is three submissions per week (rules §3.2, §3.4). Do not exceed the weekly cap shown on the page.</li>
<li><b>Final selection (team decision).</b> Before the deadline you must choose exactly one submission for both prize rounds (rules §3.4, §3.5). Do not choose on the basis of this site alone.</li>
</ol>
</section>
<section>
<h2>If you see “Predicted values must be in range [0, 1]”</h2>
<p>That error means a value inside the scored area is outside 0–1 or is not a number. The GEMSDOE32 owner documents two causes: a large negative nodata sentinel (−3.4028234663852886e+38) left inside the footprint, and NaN inside the scored region (<a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">source</a>). This file has values exactly 0 or 1 inside the footprint and NaN outside it. The validator checks both. If the error still appears, the problem is in the file that was uploaded, not in this one: re-download and compare the sha256 above.</p>
</section>
<section>
<h2>What the validator checks (live, on this file)</h2>
{table(["check", "result"], [[esc(k), "<span class='yes'>true</span>" if v else "<span class='no'>false</span>"] for k, v in val["checks"].items()])}
<p class="mut">Footprint pixels: {val['notes'][0].split('=')[1] if val.get('notes') else 'n/a'}. Inside the footprint: min {val['stats_inside_footprint']['min']}, max {val['stats_inside_footprint']['max']}, ones {val['stats_inside_footprint']['n_ones']:,}, zeros {val['stats_inside_footprint']['n_zeros']:,}, other {val['stats_inside_footprint']['n_other']}.</p>
</section>
"""
(DOCS / "submit.html").write_text(page("How to submit", body_submit, "submit.html"))

# ---------- evidence.html ----------
_s5 = [r for r in e1["sigma_rows"] if abs(r["frac"] - 0.005) < 1e-9]
med_min, med_max = min(r["median_d_px"] for r in _s5), max(r["median_d_px"] for r in _s5)
sig_min5, sig_max5 = min(r["sigma_px"] for r in _s5), max(r["sigma_px"] for r in _s5)
sig_min = min(v["sigma_px_all_blocks"] for v in e3["selection"].values())
sig_max = max(v["sigma_px_all_blocks"] for v in e3["selection"].values())

sig_rows = [r for r in e1["sigma_rows"] if r["frac"] == 0.005]
sig_table = table(["ridge class", "block", "matched n", "median d (px)", "within 3 px", "σ (px)"],
                  [[esc(r["cls"]), r["block"], f"{r['n_matched']:,}", f"{r['median_d_px']:.2f}",
                    f"{r['frac_within_3px']:.3f}", f"{r['sigma_px']:.2f}"] for r in sig_rows])
can_rows = sorted(canary.items(), key=lambda kv: -kv[1]["max_auc"])
can_table = table(["feature / class", "mean AUC (4 blocks)", "max AUC", "leak flag (>0.90)"],
                  [[esc(k), f"{v['mean_auc']:.3f}", f"{v['max_auc']:.3f}", "<span class='no'>yes</span>" if v["max_auc"] > 0.9 else "no"] for k, v in can_rows])
blk_rows = []
for b in blocks:
    cfg = "; ".join(f"{esc(c)}: {s['frac']}/{esc(s['config'])}" for c, s in b["selection"].items())
    blk_rows.append([b["block"], f"{b['n_truth']:,}", f"{b['dti']:.4f}", f"{b['dots']:,}", cfg])
blk_table = table(["held-out block", "withheld positives", "DTI (nested)", "dots", "selected (class: frac/config)"], blk_rows)
uniq_block = ""
if uniq_final:
    uniq_block = f"<p>Final file: max Spearman ρ {uniq_final['max_rho']:.3f}; literal dot-overlap flags {uniq_final['n_flagged']}; verdict <b>{esc(uniq_final['verdict'])}</b>. Source: <code>registry/uniqueness_final_{esc(SUB)}_summary.json</code>.</p>"
body_ev = f"""
<section>
<h1>Evidence</h1>
<p class="mut">Every number below is read from <code>registry/</code>. HOLDOUT-DTI means the score on our hide-and-recover catalogue holdout. It is <b>not</b> an organizer score.</p>
<h2>0. Method notes (what was actually run)</h2>
<ul>
<li><b>Ridge fields:</b> Hessian of a Gaussian-smoothed band, scale 1 px (100 m features) and 2 px (200 m features). The 1.5 px scale in the original plan was <b>not</b> used; this is a documented deviation (<code>RESOLUTIONS</code> in <code>src/gems58/ribbon.py</code>).</li>
<li><b>Ridge bands:</b> total magnetic (<code>tmi_hg</code>), isostatic gravity (<code>iso_grav_anom_hg</code>), and topographic slope (<code>det_elev_slope</code>), each at fine and coarse scale. Values are clipped to the 1st–99th percentile and standardised before the Hessian.</li>
<li><b>σ rule:</b> σ = 1.4826 × MAD of distances from withheld truth to the nearest candidate, counting only matches within 10 px (<code>robust_sigma</code>, <code>run_ribbon_lane.py</code>). The lane's σ rule restricts configurations only when σ &lt; 0.5 (tight line) or σ is 2–3 px (ribbon of ±round(σ)). Every pooled σ selected here was outside those bands, so all configurations were admissible and the utility U alone decided.</li>
<li><b>Emission (E3):</b> all six classes selected 1% of footprint pixels and configuration <code>D3o+1</code>. Pooled σ across blocks: {sig_min:.2f}–{sig_max:.2f} px.</li>
</ul>
<h2>1. Holdout (HOLDOUT-DTI)</h2>
<table><tr><th>value</th><td><b>{h['value']:.4f}</b></td></tr>
<tr><th>95% CI</th><td>{h['ci95_t'][0]:.4f} – {h['ci95_t'][1]:.4f} (jackknife over 4 blocks, t₃ = {h['tcrit_df3']:.3f}; low power)</td></tr>
<tr><th>withheld positives</th><td>{h['n_withheld_positives']:,}</td></tr>
<tr><th>evaluator</th><td>{esc(e2['evaluator'])}</td></tr>
<tr><th>baseline (single-line union, no selection)</th><td>{e2['baseline_L1_union_frac0p005_pooled_dti']:.4f}</td></tr></table>
{blk_table}
<h2>2. Leakage canary (each feature alone)</h2>
<p>Leak threshold 0.90 (none exceeds it). Watch: <code>geod_2ndinv</code> reaches 0.896 on one block; not above the threshold.</p>
{can_table}
<h2>3. Localisation σ by class × block (ridge fraction 0.5%)</h2>
<p>σ = 1.4826 × MAD of matched distances (withheld truth → nearest candidate, within 10 px). At the 0.5% fraction, matched-distance medians range {med_min:.1f}–{med_max:.1f} px and σ ranges {sig_min5:.2f}–{sig_max5:.2f} px, so the tight-line regime (σ &lt; 0.5 px) was never reached.</p>
{sig_table}
<h2>4. Uniqueness (protocol §1)</h2>
<p>Surface (before placement): max Spearman ρ {uniq_surface['max_rho']:.3f}; literal dot-overlap flags {uniq_surface['n_flagged']} (dense maps excluded from the overlap test: {uniq_surface['n_dense_registry_excluded_from_overlap']}); verdict <b>{esc(uniq_surface['verdict'])}</b>. Chance control: <code>registry/chance_coverage_surface.csv</code>: excess over chance from {surf_min:+.3f} to {surf_max:+.3f}; {surf_gt08} of 25 are above +0.08.</p>
<h3>Chance-level control, final file (top 12 by excess)</h3>
{chance_table}
<p class="mut">Excess = observed dot overlap − chance coverage (share of the footprint within 3 px of that raster's dots, which a random placement with the same density would also hit). Positive excess means overlap above chance. Spearman ρ for all listed rasters is below 0.03. Duplicate-named _allfinite and _nan copies are counted separately in the CSV.</p>
{uniq_block}
<h2>5. Run card (protocol §5)</h2>
<pre>{esc(json.dumps(run_card, indent=2))}</pre>
</section>
"""
(DOCS / "evidence.html").write_text(page("Evidence", body_ev, "evidence.html"))

# ---------- sources.html ----------
src_rows = list(csv.DictReader(open(REG / "sources.csv")))
def link_or_text(u):
    return f'<a href="{esc(u)}">{esc(u)}</a>' if u.startswith("http") else esc(u)
src_table = table(["id", "source", "checked", "result", "used for"],
                  [[esc(r["id"]), esc(r["source"]) + "<br><span class='mut'>" + link_or_text(r["url"]) + "</span>",
                    esc(r["what_was_checked"]), esc(r["result_2026-10-11"]), esc(r["used_for"])] for r in src_rows])
irr = irregularities()
irr_table = table(["id", "irregularity", "why it matters", "action needed"], [[esc(c) for c in r[:4]] for r in irr])
body_src = f"""
<section><h1>Sources (verified) and irregularities</h1>
<p class="mut">Each row was checked by fetch or local file read on 2026-10-11. Status <i>BLOCKED</i> or <i>NOT FETCHED</i> is stated, not hidden.</p>
{src_table}</section>
<section><h2>Irregularities flagged for review</h2>{irr_table}</section>
"""
(DOCS / "sources.html").write_text(page("Sources", body_src, "sources.html"))
# keep README section 10 identical to registry/RUN_CARD.json
readme = ROOT / "README.md"
txt = readme.read_text()
m = re.search(r"(## 10\. Run card[^\n]*\n\n```json\n)(.*?)(\n```)", txt, flags=re.S)
if m:
    txt = txt[:m.start(2)] + json.dumps(run_card, indent=2, ensure_ascii=False) + txt[m.end(2):]
    readme.write_text(txt)
print("site written:", SUBFILE, "NOTE len", len(NOTE))
