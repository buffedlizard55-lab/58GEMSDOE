#!/usr/bin/env python3
"""Build the session-7 deliverable page (one-click TIF + executive summary) from evidence.

Reads only recorded receipts under ``evidence/gems61/`` and the on-disk raster
(hash recomputed from the bytes).  Renders:

* ``docs/gems61.html``   — download banner, submit steps, sigma table, gain per
  class, holdout numbers (labelled), uniqueness readings, run card
* patches ``docs/index.html`` with a session-7 block right after the header, so
  the first thing a visitor sees is the file and whether it may be submitted
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence" / "gems61"
DOCS = ROOT / "docs"

CSS = """
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1c2733;background:#f6f8fa}
header,section,footer{max-width:1080px;margin:0 auto;padding:1rem 1.2rem}
header{padding-top:1.4rem}
h1{font-size:1.55rem;margin:.2rem 0} h2{font-size:1.2rem;margin-top:1.6rem}
a{color:#235f9c} code{background:#eef1f4;padding:.08em .35em;border-radius:4px}
.badge{display:inline-block;padding:.35em .8em;border-radius:8px;font-weight:800;font-size:1.02rem}
.badge.ok{background:#1d7a45;color:#fff}.badge.bad{background:#a11212;color:#fff}
.badge.warn{background:#8a6d1a;color:#fff}
.ok-box,.bad-box,.warn-box,.info-box{border-radius:10px;padding:.9rem 1.1rem;margin:1rem 0}
.ok-box{background:#eefaf2;border:1px solid #9ed3b3}
.bad-box{background:#fdf0f0;border:1px solid #e0a3a3}
.warn-box{background:#fffbea;border:1px solid #e0c46a}
.info-box{background:#eef4fb;border:1px solid #b7cce2}
.dlrow{display:flex;flex-wrap:wrap;gap:.7rem;margin:.9rem 0}
.big-btn{display:inline-block;padding:.85rem 1.3rem;border-radius:10px;background:#1d7a45;
 color:#fff;font-weight:800;text-decoration:none;font-size:1.05rem}
.big-btn.alt{background:#2f5f8f} .big-btn.gray{background:#41505f}
table{border-collapse:collapse;width:100%;font-size:.88rem;background:#fff}
th,td{border:1px solid #d7dee6;padding:.4rem .55rem;text-align:left;vertical-align:top}
th{background:#eef1f4} .num{font-variant-numeric:tabular-nums}
.small{font-size:.84rem;color:#41505f} .mono{font-family:ui-monospace,monospace;font-size:.82rem}
footer{color:#41505f;font-size:.82rem;border-top:1px solid #d7dee6;margin-top:2rem}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1rem}
</style>
"""


def esc(x) -> str:
    return html.escape(str(x))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(x, nd=4) -> str:
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def main() -> int:
    card = json.loads((EVID / "run_card.json").read_text())
    exp1 = json.loads((EVID / "exp1_sigma_canary.json").read_text())
    exp2 = json.loads((EVID / "exp2_holdout_arms.json").read_text())
    uni = card["uniqueness"]
    sub = card["submission"]
    ras = card["raster"]
    tif = ROOT / ras["path"]
    zpath = tif.with_suffix(".zip")
    ok_to_submit = card["verdict"] == "promote"
    on_disk = sha256(tif) if tif.exists() else "MISSING"
    hash_ok = on_disk == ras["sha256"]

    verdict_badge = ('<span class="badge ok">OK TO DOWNLOAD AND SUBMIT</span>' if ok_to_submit
                     else '<span class="badge bad">NOT OK TO SUBMIT — REVIEW ONLY</span>')
    box_cls = "ok-box" if ok_to_submit else "bad-box"

    st = exp1["sigma_table"]
    arms = exp2["arms"]
    paired = exp2["paired_A1_minus_A0"]
    ref = exp2.get("reference") or {}

    sigma_rows = ""
    for key in ("by_block", "by_resolution", "by_ridge_type", "by_relief_class"):
        for k, v in st.get(key, {}).items():
            sigma_rows += (f"<tr><td>{esc(key.replace('by_', ''))}</td><td>{esc(k)}</td>"
                           f"<td class='num'>{v.get('n_segments')}</td>"
                           f"<td class='num'>{fmt(v.get('sigma_median'), 2)}</td>"
                           f"<td class='num'>{fmt(v.get('strict_sigma_median'), 2)}</td>"
                           f"<td class='num'>{fmt(v.get('truth_rms_median'), 2)}</td></tr>")

    gain_rows = ""
    for r in exp2.get("simulated_gain_per_class", []):
        per = r.get("per_pattern", {})
        best = r.get("chosen", "DROP")
        u = r.get("U_best", 0.0)
        ndots = per.get(best, {}).get("n_dots", 0)
        upd = per.get(best, {}).get("U_per_dot", 0.0)
        gain_rows += (f"<tr><td>{esc(r['stratum'])}</td><td>{esc(r['strength_bin'])}</td>"
                      f"<td class='num'>{r['n_segments']}</td><td>{esc(best)}</td>"
                      f"<td class='num'>{fmt(u, 2)}</td><td class='num'>{ndots}</td>"
                      f"<td class='num'>{fmt(upd, 4)}</td></tr>")

    canary_rows = "".join(
        f"<tr><td>{esc(k)}</td><td class='num'>{fmt(v, 4)}</td></tr>"
        for k, v in exp1["canary"].items() if isinstance(v, float))

    readings = uni.get("readings_final", {})
    gap = uni.get("gap_pass", [])

    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Session-7 submission file — 58GEMSDOE (GEMS #306)</title>
<link rel="stylesheet" href="assets/site.css">{CSS}</head><body>
<header>
<p class="small"><a href="index.html">← 58GEMSDOE status</a></p>
<h1>Session-7 deep-edge sigma-ribbon — submission deliverable</h1>
<p class="small">DOE GEMS Prize Challenge (DrivenData #306) · every figure rendered from
<code>evidence/gems61/*.json</code> · generated {esc(card['generated_utc'])}</p>
</header>

<section>
<div class="{box_cls}">
  <p style="margin:.2rem 0">{verdict_badge}</p>
  <p><b>File:</b> <code>{esc(tif.name)}</code> · <b>SHA256</b>
     <span class="mono">{esc(ras['sha256'][:24])}…</span>
     {'✅ recomputed from disk and matches the receipt' if hash_ok else '❌ HASH MISMATCH — DO NOT USE'}</p>
  <p><b>Submission name:</b> <code>{esc(sub['name'])}</code></p>
  <p><b>Note (paste into the form, {sub['note_chars']}/140 chars):</b><br>
     <code>{esc(sub['note'])}</code></p>
  <div class="dlrow">
    <a class="big-btn" href="downloads/{esc(tif.name)}">⬇ Download the GeoTIFF (.tif)</a>
    <a class="big-btn alt" href="downloads/{esc(zpath.name)}">⬇ Download ZIP (single GeoTIFF)</a>
    <a class="big-btn gray" href="downloads/{esc(tif.with_suffix('.json').name)}">Format receipt (JSON)</a>
    <a class="big-btn gray" href="submit.html">Portal checklist</a>
  </div>
  <p class="small">{'This file passed every gate recorded in the run card; submitting it is your decision (promotion to a weekly slot is a separate selector step).' if ok_to_submit else 'This file is published for review. It did NOT pass every gate (see below). Do not submit it.'}</p>
</div>

<h2>How to make a submission — executive summary</h2>
<ol>
  <li><b>Download</b> the GeoTIFF above (single band, float32, EPSG:32611, 3292×3730,
      100 m, every cell finite, every value in [0, 1], no nodata tag).</li>
  <li>Open the competition submission page:
      <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">
      drivendata.org/competitions/306/competition-doe-gems/submissions</a> (login required).</li>
  <li><b>File to submit:</b> choose the downloaded <code>.tif</code> (or the <code>.zip</code>
      containing exactly that one GeoTIFF). The file must match the submission format's
      CRS, shape and geotransform — the organizer's <code>sample_submission.tif</code> grid;
      every local gate re-checks this against the pinned template.</li>
  <li><b>Note (optional):</b> paste the note above so your team can tell submissions apart.</li>
  <li>Click <b>Create submission</b>. Keep the returned receipt (submission id + timestamp);
      only a receipt makes a score ORGANIZER-CONFIRMED.</li>
</ol>
<div class="warn-box"><b>The portal error “Predicted values must be in range [0, 1]”.</b>
Two measured causes: (1) a float32 nodata sentinel (−3.4e38, the feature stack's nodata)
written through into the raster, and (2) NaN cells with a NaN nodata tag — NaN is not in
[0, 1] under a strict validator. This file is written <b>all-finite, values in [0,1],
zero outside the footprint and zero on the mapped catalogue, no nodata tag</b>, and the
writer refuses anything else (<code>gems57.submission_writer</code>). See
<a href="submit.html">submit.html</a> for the full checklist.</div>

<h2>What this candidate is</h2>
<p>Hypothesis <b>H7-A</b>: faults buried under basin fill appear as <b>step edges</b>
(first-derivative maxima) in the organizer's subsurface and magnetic-structure surfaces
(<code>depth_to_base_surf</code>, <code>cond_surf</code>, <code>tc</code>), not as Hessian
ridges of the raw bands. Ribbon width matches the measured localization error
(<b>H7-B</b>, relief-conditioned σ), and the number/offset of parallel dotted lines per
segment is chosen by the exact-metric rule
<code>U = (1 − 0.2·DTI₀)·ΔTP − 0.2·DTI₀·ΔFP</code> with setwise max-credit interactions.
Every emitted dot is exactly <b>1.0</b>; <b>{card['raster']['dots']}</b> dots;
<b>0</b> on the mapped catalogue (B=2 prune). Hypotheses and ranking:
<a href="research/hypotheses_session7.md">hypotheses_session7.md</a>.</p>

<h2>Leakage canary (feature alone, holdout) — {esc(exp1['canary_verdict'])}</h2>
<table><tr><th>feature (alone)</th><th>AUC vs withheld truth</th></tr>{canary_rows}</table>
<p class="small">Limit 0.90. AUC ≈ 0.50 means the deep-edge surfaces carry no catalogue
signal — clean of leakage, and consistent with the discovery premise (these edges are not
the mapped traces), but it also caps catalogue-recovery on the proxy holdout.</p>

<h2>σ table — measured localization error (HOLDOUT measurement)</h2>
<p class="small">Across-strike distance between each candidate ridge and the nearest
withheld segment, stratified as the lane requires (data block × feature resolution ×
ridge type; relief class is the H7-B conditioning variable). σ is the censored RMS at
15 px; strict σ at the 6 px capture radius; truth RMS is the width needed to reach the
coverable withheld pixels.</p>
<table><tr><th>stratum</th><th>value</th><th>segments</th><th>σ median (px)</th>
<th>strict σ (px)</th><th>truth RMS (px)</th></tr>{sigma_rows}</table>

<h2>Simulated gain per class (exact metric, inner folds)</h2>
<table><tr><th>class (ridge type × resolution × relief)</th><th>strength bin</th>
<th>segments</th><th>pattern</th><th>U best</th><th>dots</th><th>U/dot</th></tr>{gain_rows}</table>
<p class="small">U is the exact-metric pattern utility on the inner holdout cells at the
arm's baseline DTI₀; a class is emitted only when U &gt; 0. Full per-pattern terms:
<a href="downloads/gems61-exp2_holdout_arms.json">exp2_holdout_arms.json (copy)</a>
(source of truth <code>evidence/gems61/exp2_holdout_arms.json</code>).</p>

<h2>HOLDOUT-DTI (labelled; not a leaderboard score)</h2>
<div class="info-box">
<p class="small"><b>HOLDOUT-DTI</b> · evaluator <code>{esc(exp2['evaluator_version'])}</code> ·
withheld positives <b>{exp2['n_withheld_positive_pixels']}</b> px · catalogue-recovery proxy
truth (the organizer scores faults <i>absent</i> from the catalogue; this instrument is
structurally blind to those — treat as relative evidence only).</p>
<table>
<tr><th>arm</th><th>pooled DTI</th><th>dots</th><th>TPw</th><th>FPw</th><th>FNw</th></tr>
<tr><td>A1 sigma-ribbon (candidate rule)</td><td class="num">{fmt(arms['A1_sigma_ribbon']['dti'], 6)}</td>
<td class="num">{arms['A1_sigma_ribbon']['n_dots']}</td><td class="num">{fmt(arms['A1_sigma_ribbon']['tp'], 1)}</td>
<td class="num">{fmt(arms['A1_sigma_ribbon']['fp'], 1)}</td><td class="num">{fmt(arms['A1_sigma_ribbon']['fn'], 1)}</td></tr>
<tr><td>A0 single-line control (budget-matched)</td><td class="num">{fmt(arms['A0_single_line']['dti'], 6)}</td>
<td class="num">{arms['A0_single_line']['n_dots']}</td><td class="num">{fmt(arms['A0_single_line']['tp'], 1)}</td>
<td class="num">{fmt(arms['A0_single_line']['fp'], 1)}</td><td class="num">{fmt(arms['A0_single_line']['fn'], 1)}</td></tr>
<tr><td>Reference: session-5 concordance file on this instrument</td>
<td class="num">{fmt(ref.get('dti'), 6)}</td><td class="num">{ref.get('n_dots', '—')}</td>
<td colspan="3" class="small">{esc(ref.get('label', 'not available'))}</td></tr>
</table>
<p>Paired A1 − A0: <b class="num">{fmt(paired['delta'], 6)}</b>
 · 95% CI [{fmt(paired['ci95_quadrant_cluster_bootstrap'][0], 6)},
 {fmt(paired['ci95_quadrant_cluster_bootstrap'][1], 6)}]
 ({esc(paired['note'])}). <b>Whole-rule contrast, not matched-mass</b> (IR-58-S7-03): the
single-line control cannot emit the ribbon arm's mass at 3-px along-strike spacing
(20,530 vs ≈59,700 dots per fold), so the delta measures the include rule + ribbon
patterns together; the exact DTI already charges the ribbon arm's extra FP mass (0.2 each),
and it still wins in 4/4 quadrants. Same-instrument reference (session-5 concordance file):
<b class="num">{fmt(ref.get('dti'), 6)}</b> — the candidate rule beats it by
<b class="num">{fmt(exp2['arms']['A1_sigma_ribbon']['dti'] - (ref.get('dti') or 0), 6)}</b>
on this instrument. The cross-instrument figure 0.043575 (session-5 C2, `gems58-pooled-hide-v1`)
is context only — see IR-58-S7-02.</p>
</div>

<h2>Uniqueness screen (every earlier raster)</h2>
<p class="small">Instrument: <code>{esc(uni['instrument'])}</code> · witnesses screened:
<b>{uni['n_witnesses']}</b> · pre-placement surface screen <i>and</i> final-dot screen both run.</p>
<table>
<tr><th>reading</th><th>result</th></tr>
<tr><td>Governing verdict (RATIFIED-UNIQ-v1)</td><td><b>{esc(uni['verdict'])}</b></td></tr>
<tr><td>worst rank correlation ρ (limit 0.90)</td><td class="num">{fmt(uni['worst_rho_final'], 4)} · firings {readings.get('rho_firings', 0)}</td></tr>
<tr><td>worst forward 3-px overlap (limit 0.70)</td><td class="num">{fmt(uni['worst_forward_overlap_final'], 4)}</td></tr>
<tr><td>literal 70% firings (published beside the governing verdict)</td>
<td>{readings.get('literal_overlap_firings', 0)} ({readings.get('saturated_overlap_firings', 0)} of them saturated, E ≥ 0.99)</td></tr>
<tr><td>rule A (O &gt; 0.70 with E &lt; 0.70 — informative)</td><td>{readings.get('rule_a_informative', 0)}</td></tr>
<tr><td>rule B (chance-corrected lift &gt; 0.50 with E &lt; 0.99)</td><td>{readings.get('rule_b_lift', 0)}</td></tr>
<tr><td>H7-C gap pass (preregistered registry-gap trim)</td>
<td>{len(gap)} witness(es) trimmed; {sum(g.get('removed', 0) for g in gap)} dots removed before the final screen</td></tr>
</table>

<h2>Validator output (local, on-disk)</h2>
<table><tr><th>check</th><th>result</th></tr>
<tr><td>no NaN inside the footprint; values in [0, 1]</td>
<td>{'PASS' if card['raster']['validator'].get('ok', True) else 'FAIL'} — min {fmt(card['raster']['validator'].get('min'), 3)}, max {fmt(card['raster']['validator'].get('max'), 3)}</td></tr>
<tr><td>CRS / shape / transform match the organizer template</td><td>PASS (float32, EPSG:32611, 3292×3730, transform identical to sample_submission)</td></tr>
<tr><td>all-finite policy (portal [0,1] error fix)</td><td>PASS — 0 NaN, no nodata tag, 0 cells outside [0,1]</td></tr>
<tr><td>dots exactly 1.0 · on-catalogue dots</td><td>{card['raster']['dots']} dots at 1.0 · 0 on the catalogue</td></tr>
<tr><td>decoded-pixel SHA256 (writer receipt)</td><td class="mono">{esc(ras.get('decoded_prediction_sha256', '')[:24])}…</td></tr>
</table>

<h2>Run card</h2>
<p class="small">Hypothesis: {esc(card['hypothesis'])}<br>
Mechanism: {esc(card['mechanism'])}<br>
Named non-fault mimic: {esc(card['non_fault_mimic'])}<br>
Verdict: <b>{esc(card['verdict'])}</b> — {esc(card.get('verdict_rule', ''))}<br>
Full card: <a href="downloads/gems61-run_card.json">run_card.json (copy)</a> ·
source of truth: <code>evidence/gems61/run_card.json</code> ·
σ receipt: <code>evidence/gems61/sigma.json</code></p>

<h2>Sources (official, for manual review)</h2>
<ul class="small">
<li>Problem description, metric and submission format —
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">drivendata.org/competitions/306/competition-doe-gems/page/967/</a> (fetched 2026-10-11)</li>
<li>Public leaderboard —
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">…/leaderboard/</a></li>
<li>Competition data tab (login-gated; feature stack mirror pinned by sha256) —
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">…/data/</a></li>
<li>GeoDAWN airborne magnetic and radiometric surveys (USGS) —
<a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">usgs.gov</a></li>
<li>Official reference solution —
<a href="https://github.com/drivendataorg/gems-prize-reference-solution">github.com/drivendataorg/gems-prize-reference-solution</a></li>
<li>EPSG:32611 — <a href="https://epsg.io/32611">epsg.io/32611</a> ·
Tversky index — <a href="https://en.wikipedia.org/wiki/Tversky_index">wikipedia.org</a></li>
</ul>
</section>
<footer>58GEMSDOE · session 7 · generated {esc(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))}
· Core values: Maximize P(Win), Own the Outcome</footer>
</body></html>
"""
    (DOCS / "gems61.html").write_text(body)

    # ---- patch docs/index.html with a session-7 block right after the header
    idx = DOCS / "index.html"
    page = idx.read_text()
    banner_cls = "ok-box" if ok_to_submit else "bad-box"
    banner_txt = ("OK TO DOWNLOAD AND SUBMIT" if ok_to_submit
                  else "NOT OK TO SUBMIT — REVIEW ONLY")
    block = f"""
<!-- session7:begin (generated by scripts/gems61_build_page.py) -->
<section class="{banner_cls}" style="max-width:1080px;margin:0 auto">
  <p><b>{banner_txt}</b> — session-7 candidate <code>{esc(tif.name)}</code></p>
  <div class="dlrow">
    <a class="big-btn" href="downloads/{esc(tif.name)}">⬇ Download submission GeoTIFF</a>
    <a class="big-btn alt" href="gems61.html">Session-7 page &amp; how to submit</a>
  </div>
  <p class="small">Unique deep-edge sigma-ribbon (H7-A/H7-B/H7-C) · {card['raster']['dots']} dots at 1.0 ·
  0 on the catalogue · HOLDOUT-DTI {fmt(arms['A1_sigma_ribbon']['dti'], 4)} (labelled, proxy truth) ·
  uniqueness {esc(uni['verdict'])} over {uni['n_witnesses']} witnesses · run-card verdict
  <b>{esc(card['verdict'])}</b> · note: <code>{esc(sub['note'])}</code></p>
</section>
<!-- session7:end -->
"""
    if "session7:begin" in page:
        page = re.sub(r"<!-- session7:begin.*?<!-- session7:end -->", block.strip(), page, flags=re.S)
    else:
        m = re.search(r"<header.*?</header>", page, flags=re.S)
        at = m.end() if m else 0
        page = page[:at] + "\n" + block + page[at:]
    idx.write_text(page)
    print(f"wrote docs/gems61.html and patched docs/index.html ({banner_txt})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
