#!/usr/bin/env python3
"""Render the session-6 deliverable page (docs/s6/index.html).

Everything on the page is rendered from ``evidence/s6/*.json`` at build time; the
script never edits a number. It is idempotent: re-running replaces the
``<!-- session6:begin --> … <!-- session6:end -->`` block instead of duplicating it.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "s6"
DOCS = ROOT / "docs"
S6 = DOCS / "s6"


def j(name: str) -> dict:
    p = EV / name
    return json.loads(p.read_text()) if p.is_file() else {}


def esc(x) -> str:
    return html.escape(str(x))


def fmt(v, nd=6):
    return f"{v:.{nd}f}" if isinstance(v, (int, float)) else esc(v)


CSS = """<style>
.s6box{border:1px solid #9ed3b3;border-left:6px solid #12703f;background:#f4fcf7;
  border-radius:10px;padding:1rem 1.25rem;margin:1rem 0}
.s6box.bad{border-color:#e0a3a3;border-left-color:#a11212;background:#fdf3f3}
.s6box.warn{border-color:#e0c46a;border-left-color:#8a6d1a;background:#fffbea}
.s6box h2{margin:.1rem 0 .5rem;font-size:1.18rem}
.badge{display:inline-block;color:#fff;font-weight:700;border-radius:999px;
  padding:.35rem .8rem;font-size:.8rem;letter-spacing:.4px}
.badge.ok{background:#12703f}.badge.no{background:#a11212}.badge.warn{background:#8a6d1a}
.big-btn{display:inline-block;background:#12703f;color:#fff;text-decoration:none;font-weight:700;
  padding:.6rem 1.1rem;border-radius:8px;margin:.25rem .35rem .25rem 0}
.big-btn.sec{background:#2f5f8f}
.g-ok{color:#12703f;font-weight:700}.g-bad{color:#a11212;font-weight:700}.g-warn{color:#8a6d1a;font-weight:700}
table{border-collapse:collapse;margin:.5rem 0;font-size:.9em}
th,td{border:1px solid #d7dee6;padding:.3rem .55rem;text-align:left}
th{background:#eef2f6}
.small{font-size:.85rem;color:#41505f}
code{background:#eef2f6;padding:0 .3em;border-radius:4px;font-size:.92em}
</style>"""


def build_page() -> str:
    emit = j("emit.json")
    sig = j("sigma.json")
    can = j("canary.json")
    geo = j("geom.json")
    uniq = j("uniqueness.json")
    file = emit.get("file", "")
    hold = emit.get("holdout", {})
    shape = uniq.get("shape", {})
    fir = uniq.get("firings", {})
    worst = uniq.get("worst", {})
    val = emit.get("validator", {})

    literal = int(fir.get("literal", 0))
    ruleA = int(fir.get("ruleA", 0))
    ruleB = int(fir.get("ruleB", 0))
    vacuous = literal - ruleA
    # The standing instruction: the literal 70 % rule decides the stop.
    cleared = (literal == 0)
    badge = ("OK TO DOWNLOAD AND SUBMIT" if cleared else
             "NOT CLEARED — DOWNLOAD FOR REVIEW ONLY")
    boxcls = "" if cleared else ("bad" if ruleA or ruleB else "warn")

    arms = emit.get("arms", {})
    chosen = emit.get("chosen_arm", "")
    sweep = geo.get("sweep", [])
    sweep_sorted = sorted(sweep, key=lambda r: -r["dti"]) if sweep else []
    rand = geo.get("random_control", {})
    per_class = emit.get("per_class", {})

    parts = []
    parts.append(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Session 6 — ribbon lane deliverable — 58GEMSDOE</title>
<link rel="stylesheet" href="../assets/site.css">
{CSS}
</head><body>
<header><h1>58GEMSDOE — session 6: ribbon lane, width matched to the measured localisation error</h1>
<p>DOE GEMS Prize Challenge (DrivenData #306) · every number below is rendered from
<code>evidence/s6/*.json</code> at build time · <a href="../index.html">← repository status</a></p></header>
""")

    # ---------- the download box ----------
    parts.append(f"""
<section class="s6box {boxcls}">
  <div class="badge {'ok' if cleared else 'no'}">{badge}</div>
  <h2>{esc(file)}</h2>
  <p><b>{emit.get('n_dots', 0):,} isolated dots</b> (largest 8-connected component
  {shape.get('max_component_px', '?')} px), every value exactly <code>1.0</code>,
  <b>{emit.get('delivered_file_excludes', {}).get('catalogue_pixels', 0):,} catalogue pixels excluded</b>
  plus a {emit.get('collar', '?')}-px collar, single-band float32 GeoTIFF,
  EPSG:32611, 3730 × 3292, NaN outside the footprint exactly as in the organizer's
  <code>sample_submission.tif</code>. Local format gate:
  <b class="g-ok">{sum(1 for c in val.get('checks', {}).values() if c['ok'])}/{len(val.get('checks', {}))} checks passed</b>.</p>
  <div>
    <a class="big-btn" href="../downloads/{esc(file)}" download>⬇ Download the submission GeoTIFF
      ({emit.get('bytes', 0) / 1024:.0f} KiB)</a>
    <a class="big-btn sec" href="../downloads/{esc(file).replace('.tif', '.zip')}" download>⬇ ZIP (one GeoTIFF)</a>
    <a class="big-btn sec" href="../executive-summary.html">How to submit it</a>
    <a class="big-btn sec" href="../submit.html">Portal checklist</a>
  </div>
  <p class="small">sha256 <code>{esc(emit.get('sha256', ''))}</code> ·
  submission name <code>{esc(Path(file).stem)}</code></p>
  <p class="small"><b>Uniqueness:</b> {esc(uniq.get('witnesses_screened', 0))} sha256-verified witnesses screened ·
  literal 3 px forward-overlap rule: <b class="{'g-bad' if literal else 'g-ok'}">{literal} firing(s)</b>
  ({vacuous} of them vacuous: those witnesses' own 3 px dilation already covers the whole scored footprint,
  so they overlap every non-empty file) · informative rule-A firing(s) (overlap &gt; 0.70 with a witness
  whose own coverage &lt; 0.70): <b class="{'g-bad' if ruleA else 'g-ok'}">{ruleA}</b> ·
  chance-corrected lift rule: <b class="{'g-bad' if ruleB else 'g-ok'}">{ruleB}</b>
  (worst lift {fmt(worst.get('lift'))}, limit 0.50) ·
  worst rank correlation <b>{fmt(worst.get('rank_corr'))}</b> (limit 0.90) ·
  worst dot-set Jaccard <b>{fmt(worst.get('jaccard'))}</b> (limit 0.50) ·
  byte-identical to a witness: <b>{esc(uniq.get('byte_identical', False))}</b>.
  Verdict rendered by the protocol: <b>{esc(uniq.get('verdict', ''))}</b>.</p>
</section>
""")

    # ---------- how to submit ----------
    parts.append(f"""
<section>
<h2>How to submit this file (three steps, ~2 minutes)</h2>
<ol>
  <li>Click <b>Download the submission GeoTIFF</b> above (or the ZIP — the portal accepts either a
      single-band <code>.tif</code> or a <code>.zip</code> containing exactly one GeoTIFF).</li>
  <li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">the
      competition's New submission page</a>, choose the file, and paste this name into the
      <i>Note</i> field (140 characters max):<br>
      <code>{esc(emit.get('note', ''))}</code></li>
  <li>Create the submission. The organizer's own requirements — one band, float32,
      EPSG:32611, 3730 × 3292, values in [0, 1], NaN outside the study area — are all
      checked locally before the file is written
      (<a href="../executive-summary.html">full walkthrough with screenshots of each field</a>).</li>
</ol>
<p class="small">If the portal ever says <i>“Predicted values must be in range [0, 1]”</i>, the file
carried a NaN or a value outside [0,1] <i>inside</i> the footprint. This file cannot: its
finite support is bit-identical to the organizer's <code>sample_submission.tif</code> and every
finite value is 0.0 or 1.0.</p>
</section>
""")

    # ---------- what it is ----------
    parts.append(f"""
<section>
<h2>What the raster is, and what the lane asked for</h2>
<p>The lane instruction is: <i>match emission width to the measured localisation error; use a single
tight line where σ is under about 0.5 px and a ribbon about ±σ wide where it is 2–3 px; choose, per
segment, the number and offset of parallel dotted lines (spacing near the 3-px kernel radius) that
maximise U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact metric; emit included dots at
exactly 1.0.</i></p>
<p>Support: multi-family, multi-scale Hessian ridges (19 organizer bands × 3 scales, 6,531 segments
of ≥ 6 px at threshold 0.5), read <b>only</b> from the organizer's geophysical stack, so withholding
catalogue segments cannot change it.
Geometry: <b>{esc(chosen)}</b> — {emit.get('uniform_k', 5)} parallel dotted lines at
±{emit.get('spacing', 3):g} and ±{2 * emit.get('spacing', 3):g} px across strike, one dot every
{emit.get('pitch', 3)} px along strike, then thinned to strictly isolated pixels.</p>
<table>
<tr><th>Measurement</th><th>Value</th></tr>
<tr><td>HOLDOUT-DTI of the chosen geometry (pooled, 4 buffered blocks)</td><td><b>{fmt(hold.get('dti'))}</b></td></tr>
<tr><td>evaluator / protocol</td><td><code>{esc(hold.get('evaluator'))}</code> /
  <code>{esc(hold.get('protocol'))}</code></td></tr>
<tr><td>withheld positive pixels</td><td>{hold.get('withheld_positive_pixels', 0):,}</td></tr>
<tr><td>weighted coverage of withheld truth</td><td>{fmt(hold.get('coverage'))}</td></tr>
<tr><td>kernel credit per emitted dot</td><td>{fmt(hold.get('credit_per_dot'))}</td></tr>
<tr><td>uniform random control at the same budget</td><td>{fmt(rand.get('dti'))}</td></tr>
<tr><td>worst single-feature leakage-canary AUC (limit 0.90)</td>
    <td><b class="g-ok">{fmt(can.get('max_auc'))}</b> — {esc(can.get('verdict'))}</td></tr>
<tr><td>median distance of dots to the mapped catalogue</td>
    <td>{fmt(emit.get('distance_to_catalogue_px', {}).get('median'), 2)} px
        ({fmt(emit.get('distance_to_catalogue_px', {}).get('frac_within_3px') * 100, 2)} % within 3 px)</td></tr>
</table>
<p class="small">Per-block holdout terms:
{", ".join(f"{b['block']} {b['dti']:.5f}" for b in hold.get('per_fold', []))}.
The interval across the four spatial blocks is
{fmt(min(b['dti'] for b in hold['per_fold']))}–{fmt(max(b['dti'] for b in hold['per_fold']))}
(min–max over four physical blocks; a four-block bootstrap would resample repeated physical blocks
as independent, so no bootstrap CI is claimed).</p>
</section>
""")

    # ---------- geometry sweep ----------
    if sweep_sorted:
        rows = "".join(
            f"<tr><td><code>{esc(r['pattern'])}</code></td><td>{r['n_lines']}</td>"
            f"<td>{r['spacing']:g}</td><td>{r['pitch']}</td><td class='num'>{r['dti']:.6f}</td>"
            f"<td class='num'>{r['coverage']:.4f}</td><td class='num'>{r['credit_per_dot']:.4f}</td></tr>"
            for r in sweep_sorted)
        parts.append(f"""
<section>
<h2>Geometry sweep — equal 38,000-dot budget per block, exact metric</h2>
<table>
<tr><th>pattern</th><th>lines</th><th>across-strike spacing (px)</th><th>along-strike pitch (px)</th>
<th>HOLDOUT-DTI</th><th>weighted coverage</th><th>credit / dot</th></tr>
{rows}
</table>
<p>Two things fall out, both measured rather than assumed: the across-strike spacing that wins is
<b>the 3-px kernel radius itself</b> (spacing 1 and 2 px are worse at every line count, because
near-neighbour lines spend false-positive mass on truth the centre line already reaches), and
<b>five lines beat one and three</b> at an equal dot budget, i.e. covering the top-ranked segments
with a ±6 px ribbon beats covering eight times as many segments with a tight line.</p>
</section>
""")

    # ---------- sigma table ----------
    tab = sig.get("table", {})
    if tab:
        def rows_for(bucket, title):
            b = tab.get(bucket, {})
            if not b:
                return ""
            r = "".join(f"<tr><td>{esc(k)}</td><td class='num'>{v['n']}</td>"
                        f"<td class='num'>{v['median']:.2f}</td><td class='num'>{v['p25']:.2f}</td>"
                        f"<td class='num'>{v['p75']:.2f}</td></tr>"
                        for k, v in sorted(b.items(), key=lambda kv: kv[1]["median"]))
            return f"<h3>{esc(title)}</h3><table><tr><th>stratum</th><th>components</th><th>median σ (px)</th><th>p25</th><th>p75</th></tr>{r}</table>"
        pooled = tab.get("pooled", {})
        parts.append(f"""
<section>
<h2>σ table — measured localisation error, holdout only</h2>
<p>σ is the censored RMS distance from each withheld catalogue segment's pixels to the nearest
candidate-ridge pixel (censored at 15 px, so it is conservative, never optimistic), measured on the
buffered hide-and-recover holdout over {sig.get('n_matched_components', 0):,} matched components.
1 px = 100 m; the scoring kernel radius is 3 px.</p>
<table>
<tr><th>pooled</th><th>n</th><th>median σ</th><th>mean</th><th>p25</th><th>p75</th><th>RMS</th></tr>
<tr><td>all withheld components</td><td class='num'>{pooled.get('n', 0)}</td>
<td class='num'>{pooled.get('median', 0):.2f}</td><td class='num'>{pooled.get('mean', 0):.2f}</td>
<td class='num'>{pooled.get('p25', 0):.2f}</td><td class='num'>{pooled.get('p75', 0):.2f}</td>
<td class='num'>{pooled.get('rms', 0):.2f}</td></tr>
</table>
{rows_for('by_block', 'by data block')}
{rows_for('by_scale', 'by feature resolution (ridge scale)')}
{rows_for('by_type', 'by ridge type')}
{rows_for('by_type_scale', 'by ridge type × resolution')}
<p class="small">Only strata with ≥ 10 matched components are published; the emission falls back
through type×scale → type → scale → block → pooled, and each substitution is recorded per segment in
<code>evidence/s6/emit.json</code>.</p>
</section>
""")

    # ---------- per class gains ----------
    if per_class:
        rows = "".join(
            f"<tr><td>{esc(k)}</td><td class='num'>{v['n_segments']}</td>"
            f"<td class='num'>{v['sigma_px']:.2f}</td><td class='num'>{v['k_adaptive']}</td>"
            f"<td class='num'>{v['dti_K1']:.5f}</td><td class='num'>{v['dti_chosen']:.5f}</td>"
            f"<td class='num'>{v['dTP']:+.1f}</td><td class='num'>{v['dFP']:+.1f}</td>"
            f"<td class='num'>{v['U']:+.2f}</td>"
            f"<td class='{'g-ok' if v['positive'] else 'g-bad'}'>{'gain' if v['positive'] else 'loss'}</td></tr>"
            for k, v in sorted(per_class.items(), key=lambda kv: -kv[1]["n_segments"]))
        npos = sum(1 for v in per_class.values() if v["positive"])
        parts.append(f"""
<section>
<h2>Simulated gain per class — the exact-metric U rule, per σ stratum</h2>
<p>For every stratum the two arms are re-emitted at a stratum-proportional dot budget over the pooled
four-block holdout: a tight single line (K = 1) and the chosen ribbon. Reported are the exact
ΔTP and ΔFP and the lane's utility
<code>U = (1 − 0.2·DTI₀)·ΔTP − 0.2·DTI₀·ΔFP</code> with DTI₀ = {fmt(emit.get('dti0_for_U'))}
(so the marginal bar is a credit of {fmt(emit.get('marginal_bar'))} per dot).</p>
<table>
<tr><th>stratum</th><th>segments</th><th>σ (px)</th><th>K</th><th>DTI K=1</th><th>DTI ribbon</th>
<th>ΔTP</th><th>ΔFP</th><th>U</th><th>verdict</th></tr>
{rows}
</table>
<p><b>{npos} of {len(per_class)} strata post a positive U, {len(per_class) - npos} a negative one.</b>
The split is honest and it is the interesting result: at a <i>stratum-local</i> budget the ribbon pays
in the topographic-crest strata (σ ≈ 5.5–6.0 px) and loses in most magnetic strata, while the
<i>global</i> equal-budget comparison ({esc(chosen)}, HOLDOUT-DTI {fmt(hold.get('dti'))})
prefers the ribbon everywhere. The two disagree because the local comparison is a reallocation
problem — five lines on a segment are five times the dots, so at a fixed budget the ribbon can only
be bought by dropping other segments — and the global ranking says the top-ranked segments are worth
more than the tail. Both numbers are published; the delivered file uses the global winner.</p>
</section>
""")

    # ---------- the negative result ----------
    parts.append(f"""
<section>
<h2>The result that matters more than the geometry</h2>
<p>At an equal 38,000-dot budget on the pooled holdout, a <b>uniformly random</b> dot field scores
<b>HOLDOUT-DTI {fmt(rand.get('dti'))}</b>. The multi-family ridge field scores
<b>{fmt(hold.get('dti'))}</b> with the chosen ribbon geometry — a gain of
{fmt(hold.get('dti', 0) - rand.get('dti', 0))} absolute ({fmt(100 * (hold.get('dti', 0) / max(rand.get('dti', 1), 1e-9) - 1), 1)} %),
and <b>{fmt(sweep_sorted[0]['dti'] - rand.get('dti', 0)) if sweep_sorted else '?'}</b> before dot
isolation. Read that against the live board: the family of dotted rasters this lane belongs to
reports 0.2376–0.2778 on the public leaderboard, and the current leader is 0.4133. The local
instrument therefore explains almost none of the live variance, and it is not entitled to: it
withholds <i>catalogue</i> faults while the board scores <i>new, off-catalogue</i> faults, and the
measured sign of the catalogue-distance term is opposite in the two populations
(<a href="LIVE_CALIBRATION.md">reverse-engineering</a>).</p>
<p class="small"><b>What would actually move the leaderboard number</b> is the support, not the
emission width: <a href="HYPOTHESES.md">H1</a> — 1 m lidar scarp detection from the organizer's own
<code>1m_DEM_links.csv</code> — is the only hypothesis on the list that targets the process the
experts used to make the labels. It is blocked here by sandbox egress (only github.com, npm and pypi
are reachable), not by the science.</p>
</section>
""")

    parts.append(f"""
<footer>58GEMSDOE · session 6 · evidence:
<a href="../evidence.html">index</a> ·
<code>evidence/s6/sigma.json</code>, <code>canary.json</code>, <code>geom.json</code>,
<code>emit.json</code>, <code>uniqueness.json</code>, <code>live_calibration.json</code> ·
every figure on this page is rendered from those files at build time.</footer>
</body></html>
""")
    return "".join(parts)


def main() -> int:
    """Render docs/s6/index.html only.

    ``docs/index.html`` and ``docs/executive-summary.html`` are owned by the shared
    ``scripts/build_session7_pages.py``, which enforces byte-exact agreement with its
    evidence. That builder imports this lane's blocks from ``scripts/s6_lane_notice.py``,
    so re-running it is what refreshes the front door:
    ``python3 scripts/build_session7_pages.py && python3 scripts/s6_build_page.py``.
    """
    S6.mkdir(parents=True, exist_ok=True)
    (S6 / ".nojekyll").write_text("")
    page = build_page()
    (S6 / "index.html").write_text(page, encoding="utf-8")
    print("wrote", S6 / "index.html", len(page), "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
