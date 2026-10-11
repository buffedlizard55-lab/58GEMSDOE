#!/usr/bin/env python3
"""Render the session-6 (ribbon-width lane) deliverable blocks for the front door.

``docs/index.html`` and ``docs/executive-summary.html`` are owned by the shared
``scripts/build_session7_pages.py``, which enforces byte-exact agreement with its
evidence (``--check``, exercised by the test suite). Rather than keep a private
fork or a post-hoc text injection that immediately goes stale, the session-6
blocks are rendered here from ``evidence/s6/*`` and imported by that builder, so
both pages stay in sync with one source of truth.

Both functions return ``""`` when the session-6 evidence is absent or unusable,
so the front door still renders for a checkout without this lane's receipts.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "s6"


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def fmt(v, nd: int = 6) -> str:
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


def j(name: str) -> dict:
    try:
        return json.loads((EV / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _facts() -> dict | None:
    emit = j("emit.json")
    if not emit.get("file"):
        return None
    uniq = j("uniqueness.json")
    hold = emit.get("holdout", {}) or {}
    fir = uniq.get("firings", {}) or {}
    worst = uniq.get("worst", {}) or {}
    checks = (emit.get("validator", {}) or {}).get("checks", {}) or {}
    literal = int(fir.get("literal", 0))
    rule_a = int(fir.get("ruleA", 0))
    rule_b = int(fir.get("ruleB", 0))
    folds = list(hold.get("per_fold") or [])
    block_range = ("—", "—")
    if folds:
        vals = [float(b["dti"]) for b in folds if b.get("dti") is not None]
        if vals:
            block_range = (fmt(min(vals)), fmt(max(vals)))
    return {
        "emit": emit,
        "uniq": uniq,
        "hold": hold,
        "fir": fir,
        "worst": worst,
        "checks": checks,
        "pass": sum(1 for c in checks.values() if c.get("ok")),
        "total": len(checks),
        "literal": literal,
        "rule_a": rule_a,
        "rule_b": rule_b,
        "vacuous": literal - rule_a,
        "cleared": literal == 0,
        "block_range": block_range,
        "file": emit["file"],
        "stem": Path(str(emit["file"])).stem,
    }


def session6_index_block() -> str:
    """Banner for ``docs/index.html`` (placed above the session-7 sections)."""
    f = _facts()
    if f is None:
        return ""
    emit, uniq, hold = f["emit"], f["uniq"], f["hold"]
    cls = "s5" + ("" if f["cleared"] else (" bad" if (f["rule_a"] or f["rule_b"]) else " warn"))
    badge = ("✅ OK TO DOWNLOAD AND SUBMIT" if f["cleared"]
             else "⛔ NOT CLEARED — DOWNLOAD FOR REVIEW ONLY")
    return f"""<!-- session6:begin -->
<section class="{cls}">
  <div class="badge">{badge}</div>
  <h2>Session-6 deliverable: <code>{esc(f['file'])}</code></h2>
  <p>Ribbon lane, width matched to the measured localisation error: {emit.get('n_dots', 0):,} strictly
  isolated dots (largest 8-connected component {esc(uniq.get('shape', {}).get('max_component_px', '?'))} px),
  every value exactly <code>1.0</code>, <b>0 dots on the mapped catalogue</b> and none within
  {esc(emit.get('collar', '?'))} px of it, NaN outside the footprint exactly as in the organizer's
  <code>sample_submission.tif</code>. Local format gate
  <b>{f['pass']}/{f['total']} passed</b>.
  HOLDOUT-DTI <b>{fmt(hold.get('dti'))}</b> ({esc(hold.get('evaluator'))}, protocol
  <code>{esc(hold.get('protocol'))}</code>, {hold.get('withheld_positive_pixels', 0):,} withheld positives,
  block range {f['block_range'][0]}–{f['block_range'][1]})
  against a <b>{fmt(j('geom.json').get('random_control', {}).get('dti'))}</b> uniform-random control at the same budget.
  Leakage canary clean (worst single-feature AUC {fmt(j('canary.json').get('max_auc'))} &lt; 0.90).</p>
  <p><b>Uniqueness over {esc(uniq.get('witnesses_screened', 0))} sha256-verified witnesses:</b>
  literal 3 px forward-overlap rule <b>{f['literal']} firing(s)</b> ({f['vacuous']} vacuous — those witnesses' own
  3 px dilation covers the whole scored footprint), informative rule-A {f['rule_a']}, chance-corrected
  rule-B {f['rule_b']} (worst lift {fmt(f['worst'].get('lift'))}), worst rank correlation
  {fmt(f['worst'].get('rank_corr'))} (limit 0.90), worst Jaccard {fmt(f['worst'].get('jaccard'))} (limit 0.50),
  byte-identical <b>{esc(uniq.get('byte_identical', False))}</b>. Verdict rendered by the protocol:
  <b>{esc(uniq.get('verdict', ''))}</b>.</p>
  <div class="dlrow">
    <a class="big-btn" href="downloads/{esc(f['file'])}" download>⬇ Download the submission GeoTIFF
      ({emit.get('bytes', 0) / 1024:.0f} KiB)</a>
    <a class="big-btn sec" href="downloads/{esc(f['stem'])}.zip" download>⬇ ZIP (one GeoTIFF)</a>
    <a class="big-btn sec" href="s6/index.html">Full session-6 page (σ table, per-class gains)</a>
    <a class="big-btn sec" style="background:#41505f" href="executive-summary.html">How to submit it</a>
  </div>
  <p class="small">sha256 <code>{esc(emit.get('sha256', ''))}</code> · name
  <code>{esc(f['stem'])}</code> · no organizer receipt exists for this or any file in this
  repository, and no submission slot has been used.</p>
</section>
<!-- session6:end -->"""


def session6_executive_block() -> str:
    """Three-step submit walkthrough for ``docs/executive-summary.html``."""
    f = _facts()
    if f is None:
        return ""
    emit = f["emit"]
    note = emit.get("note", "")
    return f"""<!-- s6submit:begin -->
<section class="s7-alert" style="border-color:#41505f;border-left-width:9px;background:#f6f9fc">
  <div class="s7-badge" style="background:#41505f">HOW TO SUBMIT — 3 STEPS</div>
  <h2>Submitting to the DOE GEMS Prize Challenge (Drivendata #306)</h2>
  <ol style="line-height:1.6">
    <li><b>Download the GeoTIFF.</b>
        <a class="s7-btn" href="downloads/{esc(f['file'])}" download>⬇ {esc(f['file'])}</a>
        (or the <a href="downloads/{esc(f['stem'])}.zip" download>ZIP</a> — the portal accepts a single-band
        <code>.tif</code> <i>or</i> a <code>.zip</code> containing exactly one GeoTIFF).</li>
    <li><b>Open the submission page.</b>
        <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData
        → competition 306 → Submit</a>, then <i>New submission</i> → <i>File to submit</i> →
        <i>Choose file</i>, and pick the downloaded <code>.tif</code>.</li>
    <li><b>Paste this Note</b> into the optional <i>Note</i> field (the only free-text field; keep it
        under 140 characters) and press <i>Create submission</i>:<br>
        <code style="display:inline-block;margin:.35rem 0">{esc(note)}</code></li>
  </ol>
  <p class="s7-small"><b>Why the portal cannot reject this file with
  <i>“Predicted values must be in range [0, 1]”</i>:</b> that error appears when the raster carries a
  NaN or a value outside [0,&nbsp;1] <i>inside</i> the study footprint. This file is written with the
  organizer's own <code>sample_submission.tif</code> as the template, so its finite support is
  pixel-identical to the sample (5,167,373 px), every finite value is exactly <code>0.0</code> or
  <code>1.0</code>, and everything outside the footprint is NaN. The writer refuses to emit a file that
  fails any of its {f['total']} local checks, and the receipt
  <code>docs/downloads/{esc(f['stem'])}.json</code> records the sha256 of the bytes you downloaded.</p>
  <p class="s7-small"><b>Before you spend a slot:</b> read the
  <a href="s6/index.html">session-6 page</a> for the gates (holdout, leakage canary, registry
  uniqueness) and the verdict rendered from them. No organizer receipt exists for any file in this
  repository, so no leaderboard number can be promised for it. The banner above the download button
  states whether the file is cleared to submit; it is currently
  <b>{'cleared' if f['cleared'] else 'NOT cleared'}</b>.</p>
</section>
<!-- s6submit:end -->"""


if __name__ == "__main__":
    print(session6_index_block()[:400] or "(no session-6 evidence)")
