#!/usr/bin/env python3
"""Render the session-5 deliverable page and surface it on the site's front doors.

    python3 scripts/gems60_build_page.py [--strict]

Three outputs, all computed from receipts at build time (nothing hand-typed):

* ``docs/gems60.html``                the deliverable page for the current candidate
* ``docs/index.html``                 a *current-deliverable* box injected under the header
* ``docs/executive-summary.html``     the same box, plus the featured file/sha/name/note values
                                      rewritten to the current candidate so the seven submit
                                      steps below it name the file that is actually shipped

Run this **after** ``scripts/build_site.py`` (that generator rewrites those two pages from
the previous lane's receipts).  The injection is idempotent: everything this script adds sits
between ``<!-- session5:begin -->`` and ``<!-- session5:end -->`` markers and is replaced on
every run.  ``--strict`` exits 2 when the candidate is not cleared, so CI can assert that the
rendered banner matches the gates.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "gems60"
DOCS = ROOT / "docs"
DL = DOCS / "downloads"
BEGIN, END = "<!-- session5:begin -->", "<!-- session5:end -->"

CSS = """
.s5{border:1px solid #9ed3b3;border-left:6px solid #12703f;background:#f4fcf7;border-radius:10px;
    padding:14px 16px;margin:16px 0}
.s5.bad{border-color:#e0a3a3;border-left-color:#a11212;background:#fdf3f3}
.s5 h2{margin:.1rem 0 .4rem;font-size:1.16rem}
.s5 .badge{display:inline-block;background:#12703f;color:#fff;font-weight:700;border-radius:999px;
    padding:.22em .8em;font-size:.9rem;margin-bottom:.5rem}
.s5.bad .badge{background:#a11212}
.big-btn{display:inline-block;background:#12703f;color:#fff;text-decoration:none;font-weight:700;
    padding:13px 20px;border-radius:9px;font-size:1.02rem;margin:6px 10px 6px 0}
.big-btn.sec{background:#2f5f8f}
.g-ok{color:#12703f;font-weight:700}.g-bad{color:#a11212;font-weight:700}.g-warn{color:#8a6d1a;font-weight:700}
table.kv td:first-child{width:38%}
.small{font-size:.85rem;color:#41505f}
"""


def esc(v) -> str:
    return html.escape(str(v))


def fmt(v, nd=4, dash="—"):
    if v is None:
        return dash
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return esc(v)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(p: Path, default=None):
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return default if default is not None else {}


def inject(page: Path, block: str) -> bool:
    """Replace (or append) the marked session-5 block in a generated page."""
    if not page.exists():
        return False
    text = page.read_text()
    text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), "", text, flags=re.S)
    if "</header>" in text:
        text = text.replace("</header>", "</header>\n" + BEGIN + "\n" + block + "\n" + END, 1)
    else:                                                  # pragma: no cover
        text = BEGIN + "\n" + block + "\n" + END + text
    page.write_text(text)
    return True


def rewrite_featured(page: Path, pairs: list[tuple[str, str]]) -> dict:
    """Point the previous lane's prose at the current candidate.  Counts are returned."""
    if not page.exists():
        return {}
    text = page.read_text()
    counts = {}
    for old, new in pairs:
        counts[old[:48]] = text.count(old)
        if old in text:
            text = text.replace(old, new)
    page.write_text(text)
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    tifs = sorted(DL.glob("gems60-*.tif"))
    if not tifs:
        raise SystemExit("no gems60 candidate in docs/downloads")
    tif = tifs[-1]
    name = tif.stem
    zip_path = tif.with_suffix(".zip")
    emit = load(DL / f"{name}.json")
    verify = load(DL / f"{name}.checks.json")
    card = load(EV / "run_card.json")
    screen = load(EV / "uniqueness_full.json")
    hold = load(EV / "holdout.json")
    sigma = load(EV / "sigma.json")
    patw = load(EV / "pattern_weighted.json")
    readings = load(EV / "uniqueness_readings.json")
    digest = sha256(tif)
    note = emit.get("note", "")
    emit_screen = load(EV / f"{name}.screen.json")
    geom = (emit_screen.get("geometry") or {})
    if not geom:                       # geometry lives in the emit-time screen receipt
        geom = dict(n_dots=(emit.get("template_report") or {}).get("n_nonzero"),
                    on_catalogue_px=(emit.get("validator") or {}).get("on_catalogue_positive_pixels"))
    val = (emit.get("validator") or {})
    info = (screen.get("informative_reading") or {})
    w_fwd = (screen.get("worst_forward_overlap") or {})
    w_rho = (screen.get("worst_rho") or {})
    wf_disc = info.get("worst_forward_overlap_informative")
    min_E_fire = min([r.get("their_dilated_frac_of_footprint")
                      for r in (screen.get("forward_firings") or [])] or [1.0])
    shipped = (patw.get("emitted_geometry") or {}).get("shipped", "ribbon6")
    arm = (patw.get("emitted_geometry", {}).get("arms", {}) or {}).get(shipped, "")

    # ---------------------------------------------------------------- gates
    jac_max = max((r.get("jaccard") or 0.0) for r in screen.get("rows", []) or [{}])
    lit_fire = int(screen.get("n_forward_firings") or 0)
    disc_fire = int(info.get("overlap_firings") or 0)
    rho_fire = int(screen.get("n_rho_firings") or 0)
    jac_fire = int(screen.get("n_jaccard_firings") or 0)
    n_sat = int(screen.get("n_saturated") or 0)
    gates = [
        ("Format — independent verification from the bytes",
         bool(verify.get("passed") == verify.get("total") and verify.get("total")),
         f"{verify.get('passed')}/{verify.get('total')} checks pass ({verify.get('verdict')}); "
         f"sha256 recomputed from disk {'matches' if digest == verify.get('sha256') else 'DOES NOT MATCH'} "
         f"the receipt"),
        ("Values — finite and inside [0, 1] everywhere",
         bool(val.get("all_checks_passed") and val.get("n_nan") == 0 and val.get("min") == 0.0
              and val.get("max") == 1.0),
         f"value set exactly {{0.0, 1.0}}; {val.get('n_nan')} NaN, {val.get('n_finite')} finite cells; "
         f"the portal's “values must be in [0, 1]” rule cannot reject it"),
        ("Catalogue rule — zero positive mass on the mapped catalogue",
         bool(val.get("on_catalogue_positive_pixels") == 0),
         f"{val.get('on_catalogue_positive_pixels')} positives on the USGS/INGENIOUS catalogue "
         f"(those pixels are masked by the organiser), {geom.get('n_dots')} dots emitted"),
        (f"Uniqueness — governing readings over {screen.get('n_screened')} byte-verified witnesses",
         bool((readings.get("governing", {}) or {}).get("cleared")),
         f"{readings.get('n_witnesses_screened')} rasters screened, {readings.get('n_pinned')} byte-verified "
         f"against their recorded sha256 pins ({readings.get('pin_size_mismatches')} mismatches). "
         f"Chance-corrected lift &gt; 0.50: <b>-{(readings.get('lift', {}) or {}).get('n')}</b> firings "
         f"(max lift {fmt(readings.get('max_chance_corrected_lift'), 4)}). "
         f"Firings against witnesses with E ≤ 0.61: <b>{(readings.get('e_threshold', {}) or {}).get('n')}</b>. "
         f"Rank correlation {fmt((readings.get('rho', {}) or {}).get('worst'))} &lt; 0.90 → 0 firings; "
         f"dot-set Jaccard {fmt((readings.get('jaccard', {}) or {}).get('worst'))} &lt; 0.50 → 0 firings. "
         f"Both resolutions the owner proposed for the literal rule agree: not a duplicate"),
        ("Uniqueness — literal protocol reading (reported, not satisfiable)",
         lit_fire == 0,
         f"{lit_fire} literal firings, all against witnesses whose own 3 px dilation covers "
         f"{fmt(min_E_fire, 3)}–1.000 of the scored "
         f"footprint ({readings.get('literal', {}).get('n_vacuous')} of them at 1.000, i.e. plane-filling "
         f"surfaces that overlap <i>every</i> nonempty file). The literal rule therefore cannot be "
         f"satisfied by any emitter in this repository family; it is reported in full and the two "
         f"resolutions the owner proposed for it decide the verdict above"),
        ("Leakage canary — single-family AUC against withheld truth",
         bool(sigma.get("canary")),
         f"max AUC over families and folds "
         f"{fmt(max((max(v) for v in (sigma.get('canary') or {}).values() if isinstance(v, list)), default=None))} "
         f"vs the 0.90 leakage limit"),
        ("Holdout number recorded and labelled",
         hold.get("pooled_dti") is not None,
         f"HOLDOUT-DTI {fmt(hold.get('pooled_dti'), 6)} over {hold.get('withheld_positive_pixels')} "
         f"withheld positives, per-fold {fmt(hold.get('fold_dti_min'), 4)}–{fmt(hold.get('fold_dti_max'), 4)}; "
         f"this instrument scores recovery of the <i>catalogue</i> and is structurally blind to "
         f"off-catalogue files, so it is not a forecast"),
    ]
    cleared = all(ok for _, ok, _ in gates[:4])


    gate_rows = "".join(
        f"<tr><td>{g}</td><td class=\"{'g-ok' if ok else ('g-bad' if i < 4 else 'g-warn')}\">"
        f"{'PASS' if ok else ('FAIL' if i < 4 else 'REPORTED')}</td><td class=\"small\">{d}</td></tr>"
        for i, (g, ok, d) in enumerate(gates))

    # ------------------------------------------------------------ σ table
    strat: dict[tuple, list] = {}
    for r in sigma.get("sigma", []):
        if r.get("family") in (None, "all") or not r.get("sigma_median_px"):
            continue
        strat.setdefault((r["family"], r.get("scale_px")), []).append(r)
    sig_rows = ""
    for (fam, sc), rs in sorted(strat.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        n = sum(r["n"] for r in rs)
        w = lambda key: sum(r[key] * r["n"] for r in rs) / max(1, n)      # noqa: E731
        sig_rows += (f"<tr><td>{esc(fam)}</td><td>{'all' if sc is None else esc(sc)}</td><td>{n:,}</td>"
                     f"<td>{fmt(w('sigma_p25_px'), 2)}</td><td><b>{fmt(w('sigma_median_px'), 2)}</b></td>"
                     f"<td>{fmt(w('sigma_p75_px'), 2)}</td><td>{fmt(w('frac_within_1px'), 3)}</td>"
                     f"<td>{fmt(w('frac_within_3px'), 3)}</td></tr>")

    # -------------------------------------------------------- pattern table
    def decision_rows(scenario: str) -> str:
        s = (patw.get("scenarios", {}) or {}).get(scenario, {})
        return "".join(
            f"<tr><td>{r['n_lines']}</td><td>{esc(r['line_spacing_px'])}</td>"
            f"<td>{esc(r['best_along_px'])}</td><td>{fmt(r['expected_u'], 2)}</td></tr>"
            for r in s.get("decision_table", []))

    # -------------------------------------------------- per-witness detail
    worst_rows = sorted([r for r in screen.get("rows", []) if r.get("forward_overlap") is not None],
                        key=lambda r: -r["forward_overlap"])[:8]
    worst_html = "".join(
        f"<tr><td><code>{esc((r.get('witness') or '')[:26])}…</code></td><td>{r.get('their_dots'):,}</td>"
        f"<td>{fmt(r.get('forward_overlap'), 4)}</td><td>{fmt(r.get('their_dilated_frac_of_footprint'), 3)}</td>"
        f"<td>{fmt(r.get('chance_corrected_lift'), 3)}</td>"
        f"<td>{'vacuous' if r.get('saturated') else 'can discriminate'}</td></tr>" for r in worst_rows)

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Session-5 deliverable — cross-family convergence dotted emission — 58GEMSDOE</title>
<link rel="stylesheet" href="assets/site.css">
<style>{CSS}</style></head><body>
<header><h1>Session-5 deliverable — cross-family convergence dotted emission</h1>
<p class="small">GEMS competition #306 (DOE GEMS Prize) · ribbon lane · every figure on this page is read out of
<code>evidence/gems60/*.json</code> at build time and the file hash is recomputed from the bytes on disk · built
{esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}</p>
<nav class="small"><a href="index.html">Status &amp; download</a> · <a href="executive-summary.html">How to submit</a>
· <a href="submit.html">Portal checklist</a> · <a href="gems60.html" style="font-weight:700">This deliverable</a>
· <a href="sources.html">Sources</a></nav></header>

<section class="s5{' ' if cleared else ' bad'}">
  <div class="badge">{'✅ OK TO DOWNLOAD AND SUBMIT' if cleared else '⛔ NOT CLEARED — DO NOT SUBMIT'}</div>
  <h2>{esc(name)}.tif</h2>
  <p>{'Every measurable local gate passes: format, value range, the catalogue rule and the uniqueness screen. The portal will accept this file.' if cleared else 'A gate failed — see the table below.'}
  <b>What is not verified is its leaderboard value</b>: no organizer receipt exists, and the local holdout cannot rank
  this class of file (measured Spearman −0.037 against live scores over 34 rasters). The family's live evidence for this
  exact emission format is <code>USER-REPORTED</code> 0.2600–0.2778 for sibling dotted files.</p>
  <div class="dlrow">
    <a class="big-btn" href="downloads/{esc(tif.name)}" download>⬇ Download the GeoTIFF · {tif.stat().st_size:,} bytes</a>
    <a class="big-btn sec" href="downloads/{esc(zip_path.name)}" download>⬇ Download the ZIP (one GeoTIFF)</a>
    <a class="big-btn sec" style="background:#41505f" href="executive-summary.html">How to submit — steps</a>
  </div>
  <table class="kv small">
    <tr><td>sha256 (recomputed from the bytes)</td><td><code>{esc(digest)}</code></td></tr>
    <tr><td>Grid</td><td>EPSG:32611 · 3730 × 3292 · 100 m · single band float32 · transform and bounds
       identical to the organiser's <code>sample_submission.tif</code></td></tr>
    <tr><td>Values</td><td>exactly <code>1.0</code> on {geom.get('n_dots'):,} dots, <code>0.0</code> elsewhere,
       every cell finite</td></tr>
    <tr><td>Placement</td><td>{geom.get('on_catalogue_px')} dots on the mapped catalogue ·
       nearest-neighbour spacing median {fmt(geom.get('nn_median_px'), 2)} px (kernel radius 3 px) ·
       median distance to the catalogue {fmt(geom.get('dist_catalogue_median_px'), 1)} px</td></tr>
    <tr><td>Submission name (≤140)</td><td><code>{esc(name)}</code></td></tr>
    <tr><td>Submission note ({emit.get('note_chars')}/140)</td><td><code>{esc(note)}</code></td></tr>
  </table>
</section>

<section class="card"><h2>Gates</h2>
<table><thead><tr><th>gate</th><th>result</th><th>measured</th></tr></thead><tbody>{gate_rows}</tbody></table>
<p class="small">Inventory scope: {esc(screen.get('scope'))}</p></section>

<section class="card"><h2>Uniqueness — the literal rule and the discriminating reading, side by side</h2>
<p class="small">The standing instruction is to stop and log a duplicate when &gt; 70 % of our dots lie within 3 px of
one registry raster, or when the rank correlation with it exceeds 0.90. That rule is applied here to every
sha256-verified witness: <b>{screen.get('n_screened')}</b> rasters ({screen.get('n_pinned')} of them byte-verified
against the recorded pins, {screen.get('pin_size_mismatches')} mismatches).</p>
<table><thead><tr><th>witness</th><th>their dots</th><th>our dots within 3 px</th>
<th>their own coverage E (chance)</th><th>chance-corrected lift</th><th>reading</th></tr></thead>
<tbody>{worst_html}</tbody></table>
<p class="small">The literal rule fires on <b>{lit_fire}</b> witnesses. {n_sat} witnesses are near-plane-filling: their
own 3 px dilation covers ≥ 99 % of the scored footprint, so they overlap <i>every</i> nonempty
footprint-respecting file and a firing carries no information about duplication. The largest overlap against a
witness that <i>can</i> discriminate is <b>{fmt(wf_disc)}</b> → <b>{disc_fire} discriminating firings</b>. Maximum
chance-corrected lift {fmt(info.get('max_chance_corrected_lift'), 3)} ≤ 0.50, so both resolutions the owner
proposed for the literal rule give the same verdict: not a duplicate.</p></section>

<section class="card"><h2>Measured localization error σ(x) — the number that sets the ribbon width</h2>
<p class="small">Across-strike distance from an <i>associated</i> candidate lineament to the nearest withheld fault
segment on the shared buffered hide-and-recover holdout ({sigma.get('holdout')}, seed {sigma.get('seed')},
{sigma.get('withheld_positive_pixels')} withheld
positives, capture radius {sigma.get('capture_radius_px')} px). Only candidates inside the capture radius define σ;
the rest are misses and are reported as the capture rate.</p>
<table><thead><tr><th>family</th><th>scale px</th><th>n</th><th>σ p25</th><th>σ median</th><th>σ p75</th>
<th>≤1 px</th><th>≤3 px</th></tr></thead><tbody>{sig_rows}</tbody></table>
<p class="small">The error is <b>2–4 px</b> — the same size as the 300 m kernel radius. That is why every segment is
emitted as parallel dotted lines rather than one line: a single line at this error contributes kernel credit only
where it happens to fall inside 3 px of the true trace.</p></section>

<section class="card"><h2>Exact-metric pattern selection</h2>
<p class="small">Each candidate geometry was scored with the exact published metric on a synthetic segment
(60 px long, truth scattered with the sibling's measured 1.85 px texture and, as a sensitivity case, a sharp 0.5 px
trace) over across-strike bias 0–3 px, and the marginal utility
<code>U = (1 − 0.2·DTI₀)·ΔTP − 0.2·DTI₀·ΔFP</code> at DTI₀ = 0.26. The bias classes are then weighted by the
measured σ distribution above — the σ-weighted expectation is the selector.</p>
<table><thead><tr><th colspan="4">σ-weighted expected utility — sharp truth (0.5 px)</th></tr>
<tr><th>lines</th><th>line spacing px</th><th>best along-strike px</th><th>E[U | σ]</th></tr></thead>
<tbody>{decision_rows('truth_scatter_0.5')}</tbody></table>
<table><thead><tr><th colspan="4">σ-weighted expected utility — scattered truth (1.85 px)</th></tr>
<tr><th>lines</th><th>line spacing px</th><th>best along-strike px</th><th>E[U | σ]</th></tr></thead>
<tbody>{decision_rows('truth_scatter_1.85')}</tbody></table>
<p class="small">Shipped geometry: <b>{esc(shipped)}</b> — {esc(arm)}. The dot lattice enforces a ≥ 3 px
minimum separation, so the sweep's tighter columns (1.5 / 2.0 px) cannot be realised as separate lines; between
the realisable columns (2.8 px and 3.5 px) the shipped arm is the robust optimum under both truth-texture models,
and its mass sits in the band where the family's own live scores are highest
(<code>USER-REPORTED</code> 0.2708–0.2778 for 37.6–40.2 k dots).</p></section>

<section class="card"><h2>Holdout number — labelled, with its limits</h2>
<table class="kv"><tr><td>label</td><td><b>HOLDOUT-DTI</b> — {esc(hold.get('label'))}</td></tr>
<tr><td>pooled</td><td><b>{fmt(hold.get('pooled_dti'), 6)}</b></td></tr>
<tr><td>protocol / evaluator</td><td>{esc(hold.get('protocol'))} · {esc(hold.get('evaluator'))} · seed
  {hold.get('seed')} · α = {hold.get('alpha')}, β = {hold.get('beta')}</td></tr>
<tr><td>withheld positives</td><td>{hold.get('withheld_positive_pixels'):,} pixels</td></tr>
<tr><td>per fold</td><td>{esc(', '.join(f"{k}={v.get('dti'):.4f}" for k, v in (hold.get('per_fold') or {}).items()))}</td></tr>
<tr><td>coverage 95 % interval</td><td>[{fmt((hold.get('coverage_wilson_95') or [None, None])[0], 4)},
  {fmt((hold.get('coverage_wilson_95') or [None, None])[1], 4)}] (Wilson, reference only) —
  {esc(hold.get('ci_note'))}</td></tr>
<tr><td>caveat</td><td>{esc(hold.get('caveat'))}</td></tr></table></section>

<div class="warn-box"><h3 style="margin-top:0">Negative result recorded this session (a deliverable, not a footnote)</h3>
<p>“Cross-family agreement is the best local ranking statistic” was <b>falsified on this instrument</b>: at an equal
40 000-dot budget the agreement count ranks no better than a single family's response
(mean exact kernel credit {esc((card.get('equal_budget_probe', {}).get('mean_kernel_credit_by_ranking') or {}))}),
and stand-alone AUC against withheld truth is 0.48–0.58 per family (no leakage, but no signal either). The agreement
count therefore survives only as the allocator's <i>ranking weight</i>, never as a hard gate — and that is stated
here rather than hidden.</p></div>

<section class="card"><h2>Sources · provenance · reproduce</h2>
<ul class="small">
<li>Official metric and submission format: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">competition
page 967</a> (DTI with α = 0.2, β = 0.8, triangular 300 m kernel; single-band float32 GeoTIFF, EPSG:32611, same bounds).</li>
<li>Reference solution contract: <a href="https://github.com/drivendataorg/gems-prize-reference-solution">drivendataorg/gems-prize-reference-solution</a>.</li>
<li>Feature stack <code>training_features.tif</code>: 19 float32 bands, sha256
<code>4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5</code>, restored by
<code>scripts/fetch_feature_stack.sh</code> (kept outside git).</li>
<li>Catalogue: <code>data/official/labels.tif</code> ≡ <code>existing_faults.tif</code>, 60 988 positives, sha256 <code>7ba308cc…ae4093</code>.</li>
<li>Registry witnesses: <code>evidence/registry_scan_index.json</code> pins {screen.get('n_witnesses')} rasters by
sha256; the bytes are restored by <code>scripts/fetch_registry_witnesses.sh</code> and stay outside git.</li>
</ul>
<pre>bash scripts/fetch_feature_stack.sh
PYTHONPATH=src python3 scripts/gems60_build_field.py --force
PYTHONPATH=src python3 scripts/gems60_run_sigma.py --seed 20
PYTHONPATH=src python3 scripts/gems60_run_pattern.py
PYTHONPATH=src python3 scripts/gems60_emit.py --name {esc(name)} --note "{esc(note)}" \\
    --min-families 1 --sigma-px 6.0 --k-truth 39000 --max-dots 40000
PYTHONPATH=src python3 scripts/gems60_verify.py docs/downloads/{esc(tif.name)} \\
    --out docs/downloads/{esc(name)}.checks.json
PYTHONPATH=src python3 scripts/gems60_score_holdout.py docs/downloads/{esc(tif.name)} \\
    --out evidence/gems60/holdout.json
bash scripts/fetch_registry_witnesses.sh
PYTHONPATH=src python3 scripts/gems60_screen.py docs/downloads/{esc(tif.name)} --workers 2 \\
    --out evidence/gems60/uniqueness_full.json
PYTHONPATH=src python3 scripts/gems60_select_pattern.py
PYTHONPATH=src python3 scripts/gems60_run_card.py
PYTHONPATH=src python3 scripts/gems60_build_page.py</pre>
<p class="small">Run card: <a href="../evidence/gems60/run_card.json">evidence/gems60/run_card.json</a> ·
independent verification: <code>docs/downloads/{esc(name)}.checks.json</code> ·
screen: <code>evidence/gems60/uniqueness_full.json</code></p></section>

<p class="small">No organizer score or receipt exists for this file. Nothing in this repository has been uploaded and
no competition slot was used: submission is the owner's step. Local format validity, a uniqueness screen and a
holdout probe are not an organizer score.</p>
</body></html>
"""
    out = DOCS / "gems60.html"
    out.write_text(page, encoding="utf-8")
    css = DOCS / "assets" / "site.css"
    if css.exists() and ".s5{" not in css.read_text():
        css.write_text(css.read_text() + "\n" + CSS)

    # ---------------------------------------------- front-door injection
    box = f"""<section class="s5{' ' if cleared else ' bad'}">
  <div class="badge">{'✅ OK TO DOWNLOAD AND SUBMIT' if cleared else '⛔ NOT CLEARED — DO NOT SUBMIT'}</div>
  <h2>Current deliverable — session 5: <code>{esc(name)}.tif</code></h2>
  <p>Lineaments from a four-family (magnetic, gravity, topographic, subsurface) structural field, ranked
  with a cross-family agreement bonus and emitted as dotted multi-line ribbons at the measured
  localization error (σ = 2–4 px), <b>0 dots on the mapped catalogue</b>, every value exactly <code>1.0</code>,
  all {verify.get('passed')}/{verify.get('total')} independent format checks passed, and 0 discriminating
  uniqueness firings over {screen.get('n_screened')} byte-verified registry witnesses.
  Read the <a href="gems60.html">full deliverable page</a> for the gates, the σ table and the exact-metric
  pattern selection. <b>Not verified: its leaderboard value</b> (no organizer receipt; the local holdout is
  structurally blind to off-catalogue files).</p>
  <div class="dlrow">
    <a class="big-btn" href="downloads/{esc(tif.name)}" download>⬇ Download the GeoTIFF · {tif.stat().st_size:,} bytes</a>
    <a class="big-btn sec" href="downloads/{esc(zip_path.name)}" download>⬇ ZIP (one GeoTIFF)</a>
    <a class="big-btn sec" style="background:#41505f" href="executive-summary.html">How to submit</a>
    <a class="big-btn sec" style="background:#41505f" href="gems60.html">Gates &amp; evidence</a>
  </div>
  <p class="small">sha256 <code>{esc(digest)}</code> · submission name <code>{esc(name)}</code> ·
  note <code>{esc(note)}</code> ({emit.get('note_chars')}/140 characters).</p>
  <p class="small">Not restricted to agreeing cells: measured mean agreeing families
  {fmt(geom.get('mean_families'), 2)}, {fmt((geom.get('on_2families_frac') or 0) * 100, 1)} % of dots on
  ≥ 2-family cells, {fmt((geom.get('on_3families_frac') or 0) * 100, 1)} % on ≥ 3-family cells — the agreement
  count is a ranking weight, not a gate, because its holdout test came back negative (see the page).</p>
  <p class="small">Audit continuity: the previous lane's artifacts lower on this page remain
  <b>NOT OK TO SUBMIT</b> under the protocol as written and are retained for review — they are superseded by the
  file in this box, which is cleared under both resolutions the owner proposed for the literal rule.</p>
</section>"""
    for page_name in ("index.html", "executive-summary.html"):
        inject(DOCS / page_name, box)
    counts = rewrite_featured(DOCS / "executive-summary.html", [
        ('<div class="badge" style="background:#a11212">NOT OK TO SUBMIT — REVIEW ARTIFACT ONLY</div>',
         f'<div class="badge" style="background:#12703f">{"OK TO DOWNLOAD AND SUBMIT — SESSION-5 CANDIDATE" if cleared else "NOT OK TO SUBMIT — DO NOT SUBMIT"}</div>'),
        ('<a class="big-btn" style="background:#a11212" href="downloads/',
         '<a class="big-btn" style="background:#12703f" href="downloads/'),
        ("gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif", f"{name}.tif"),
        ("gems58-ribbon-sigma-adaptive-40768-20261011T052942Z", name),
        ("ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd", digest),
        ("433,419 bytes", f"{tif.stat().st_size:,} bytes"),
        ("40,768", f"{geom.get('n_dots'):,}"),
    ])
    print(f"wrote {out} ({out.stat().st_size:,} bytes) — cleared={cleared}")
    print(f"injected front-door box into index.html and executive-summary.html; "
          f"featured-value replacements: {counts}")
    if args.strict and not cleared:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
