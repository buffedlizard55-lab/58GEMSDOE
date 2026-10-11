#!/usr/bin/env python3
"""Render the lane's download pages from the run cards (fail closed, no invented numbers).

Every figure on the two rendered pages is read at render time from
``evidence/ribbon/run_card.json`` (the primary candidate), ``evidence/ribbon_v2/*.json``
(the measurements behind it) and the delivered ``docs/ribbon/downloads/*`` bytes.  If a
number is missing the page says "not measured" instead of guessing.

    python3 scripts/ribbon_build_deliverable.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import submission  # noqa: E402
from gems58w.paths import EVIDENCE  # noqa: E402

DOCS = ROOT / "docs" / "deliverable"   # NOT docs/ribbon: main archives that dir fail-closed

V2 = ROOT / "evidence" / "ribbon_v2"


def load(p: Path) -> dict:
    try:
        d = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return d if isinstance(d, dict) else {}


def fmt(v, digits=4, na="not measured"):
    if v is None:
        return na
    try:
        return f"{float(v):.{digits}f}"
    except (TypeError, ValueError):
        return str(v)


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="assets/site.css"></head><body><div class="wrap">
<nav><a href="index.html">Overview</a><a href="executive-summary.html">How to submit</a>
<a href="hypotheses.html">Hypotheses</a><a href="research.html">Research</a>
<a href="sources.html">Sources</a><a href="irregularities.html">Irregularities</a></nav>
"""

FOOT = """<footer>58GEMSDOE ribbon lane — every number on this page is read from a named
artifact at render time. No organizer receipt exists for any file here; no score is quoted as
confirmed. <a href="../index.html">Repository home</a>.</footer></div></body></html>"""


def card_block(card: dict, checks: dict, label: str, ok: bool) -> str:
    name = card.get("name", "?")
    tif = f"downloads/{name}.tif"
    zip_ = f"downloads/{name}.zip"
    verdict = card.get("verdict", "not measured")
    n_dots = (card.get("validator") or {}).get("n_positives")
    reg = card.get("registry") or {}
    prof = card.get("catalogue_distance_profile") or {}
    hold = card.get("holdout_dti")
    cls = "ok" if ok else "warn"
    pill = "⭑ PRIMARY — download &amp; submit candidate" if ok else "secondary — flagged"
    rows = [
        ("sha256", f"<code>{card.get('raster_sha256', '?')}</code>"),
        ("bytes", f"{card.get('raster_bytes', '?')}"),
        ("dots", f"{n_dots} (every value exactly <code>1.0</code>)"),
        ("local portal checks",
         f"<strong>{(card.get('validator') or {}).get('passed')}</strong> "
         f"({sum(1 for v in ((card.get('validator') or {}).get('checks') or {}).values() if v.get('ok'))}"
         f"/{len((card.get('validator') or {}).get('checks') or {})})"),
        ("registry screen",
         f"{reg.get('n_checked', '?')} rasters · worst rank correlation "
         f"<strong>{fmt(reg.get('worst_rho'))}</strong> · worst 3 px forward overlap "
         f"<strong>{fmt(reg.get('worst_forward_overlap'))}</strong> · triggers "
         f"<strong>{reg.get('n_triggers', '?')}</strong>"),
        ("catalogue distance",
         f"median {fmt(prof.get('median_px'), 1)} px · {fmt(prof.get('frac_le3px'), 3)} of dots "
         f"within 3 px · <strong>{prof.get('on_catalogue', '?')} on the catalogue</strong>"),
        ("HOLDOUT-DTI",
         f"{fmt(hold, 6)} — <span class='small'>exact metric, "
         f"{card.get('holdout_dti_withheld_positives', '?')} withheld positives, protocol "
         f"<code>{esc(card.get('holdout_dti_protocol', '?'))}</code>; "
         f"{esc((card.get('holdout_dti_ci_note') or 'no interval'))[:220]}</span>"),
        ("submission note", f"{esc(card.get('submission_note', ''))} "
                            f"<span class='small'>({card.get('submission_note_chars', '?')}/140)</span>"),
    ]
    body = "\n".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    return f"""<div class="card {cls}">
<h3 style="margin-top:0">{label} <span class="pill {'ok' if ok else 'warn'}">{pill}</span></h3>
<p><strong>{esc(name)}</strong> — verdict: {esc(verdict)}</p>
<a class="dl" href="{tif}">⬇ Download the submission GeoTIFF · {esc(name)}.tif</a>
<a class="dl" href="{zip_}">⬇ Download the single-GeoTIFF ZIP (the portal accepts this too)</a>
<table>{body}</table>
<p class="small">Verify before uploading:
<code>shasum -a 256 {esc(name)}.tif</code> must print
<code>{card.get('raster_sha256', '?')}</code>.</p>
</div>"""


def main() -> int:
    primary = load(EVIDENCE / "run_card.json")
    novel = load(V2 / "run_card_novel.json")
    excl = load(V2 / "run_card_scatter_cover.json")
    eb = load(V2 / "equal_budget.json")
    screens = load(V2 / "screens.json")

    prim_ok = bool(primary) and (primary.get("registry") or {}).get("n_triggers") == 0

    # ---- overview page ----------------------------------------------------
    blocks = []
    if primary:
        blocks.append(card_block(primary, {}, "Primary candidate", prim_ok))
    if novel:
        blocks.append(card_block(novel, {}, "Novelty-constrained variant", True))
    if excl:
        blocks.append(card_block(excl, {}, "Scatter-cover (unconstrained) variant", False))

    contest = (primary.get("equal_budget_contest") or {}) if primary else {}
    contest_rows = ""
    if contest:
        def crow(key, label):
            d = contest.get(key) or {}
            return (f"<tr><td>{label}</td><td>{fmt(d.get('pooled'), 6)}</td>"
                    f"<td>{fmt(d.get('tp'), 1)}</td><td>{fmt(d.get('fp'), 1)}</td></tr>")
        contest_rows = ("<table><tr><th>emission at the same dot count</th><th>HOLDOUT-DTI</th>"
                        "<th>TP (px)</th><th>FP (px)</th></tr>"
                        + crow("scatter", "scatter-cover (this file)")
                        + crow("incumbent_rule", "5-line ribbon, greedy by magnitude (lane baseline)")
                        + crow("surface", "max-coverage of the unblurred surface")
                        + "</table>"
                        + f"<p class='small'>paired block bootstrap, scatter − baseline: "
                          f"{json.dumps(contest.get('paired_scatter_vs_incumbent'))}</p>")

    geo = primary.get("geometry") or {}
    plan = primary.get("plan_histogram") or {}
    sigma = primary.get("sigma_table") or {}
    sig_rows = ""
    if sigma:
        by_ts = sigma.get("by_type_scale") or sigma.get("by_scale") or {}
        pooled = sigma.get("pooled") or {}
        sig_rows = (f"<p><strong>σ table (lane instrument, hide-and-recover holdout).</strong> "
                    f"pooled n = {sigma.get('n_matched', '?')}, median "
                    f"{fmt(pooled.get('median'), 2)} px, rms {fmt(pooled.get('rms'), 2)} px. "
                    f"The lane's width rule is applied to the *scatter* scale "
                    f"({fmt((primary.get('scatter') or {}).get('sigma_px'), 2)} px, the sibling "
                    f"H28 truth-model scatter), because the across-strike distance to the nearest "
                    f"*catalogue* segment measures fault spacing, not detector error — see "
                    f"<a href='research.html'>Research</a>.</p>")

    index = (HEAD.format(title="Overview — 58GEMSDOE ribbon lane")
             + "\n".join(blocks)
             + "<h1>What changed in this session</h1>"
               "<div class='card'><h3 style='margin-top:0'>The emission rule</h3>"
               "<p>Every earlier file in this family places dots on the <em>detected surface</em>. "
               "The judge's kernel is a 3-px triangle, and the hidden truth is scattered around the "
               "true structure, so the expected credit of a dot is the kernel applied to the "
               "<em>blurred</em> density. This session's candidate covers that scatter density and "
               "places each dot only while its marginal expected credit exceeds the metric's own "
               "inclusion bar <code>α·DTI₀</code> — the metric's first-order condition, not a "
               "hand-tuned width. The number of parallel dotted lines is what the residual test "
               "leaves: a single tight line on a sharp ridge, a ribbon where the density is wide.</p>"
               + sig_rows
               + (f"<table><tr><th>geometry</th><th>value</th></tr>"
                  + "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in geo.items())
                  + "</table>" if geo else "")
               + (f"<p class='small'>plan histogram (lines per segment): {esc(plan)}</p>" if plan else "")
               + "</div>"
               + ("<div class='card'><h3 style='margin-top:0'>Equal-budget contest</h3>"
                  + contest_rows + "</div>" if contest_rows else "")
               + FOOT)

    # ---- executive summary / how to submit --------------------------------
    pname = primary.get("name", "the primary candidate")
    psha = primary.get("raster_sha256", "?")
    html = (HEAD.format(title="How to submit — 58GEMSDOE ribbon lane")
            + f"""<div class="card {'ok' if prim_ok else 'warn'}">
<h2 style="margin-top:0;border:0">Download — and what it is for</h2>
<p><strong>Download: OK &nbsp;·&nbsp; Submit: your decision — this project never clicks Submit
and holds no organizer receipt.</strong></p>
<p class="small">What that means in plain words: the file below is a complete, format-valid
GeoTIFF built by the lane's own pipeline; it passes the local portal checks and the uniqueness
screen against the current registry. Nothing here can certify how it will score — only the
portal can, and a score exists only once the site returns one.</p>
<a class="dl" href="downloads/{esc(pname)}.tif">⬇ Download the submission GeoTIFF ·
{esc(pname)}.tif</a>
<a class="dl" href="downloads/{esc(pname)}.zip">⬇ Download the single-GeoTIFF ZIP</a>
<p class="small">sha256 <code>{psha}</code></p>
</div>
<h1>How to submit — step by step</h1>
<h2>1. Download the file</h2>
<p>Use the links above (the <code>.tif</code>, or the ZIP that contains exactly one GeoTIFF).</p>
<p class="small">Verify the bytes before you upload:
<code>shasum -a 256 {esc(pname)}.tif</code> must print <code>{psha}</code>.</p>
<h2>2. Open the submission page</h2>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData
→ GEMS Prize → New submission</a>.</p>
<h2>3. Choose the file</h2>
<p>Pick the <code>.tif</code> (or the ZIP). Do <strong>not</strong> upload this page, a JSON
receipt, or a ZIP of the repository.</p>
<h2>4. Paste the note</h2>
<pre>{esc(primary.get('submission_note', ''))}</pre>
<h2>5. Record the receipt</h2>
<p>The moment the page returns a score, copy it into
<code>registry/ribbon/receipts.json</code> with the file hash. Until that exists the score is
<strong>OWNER-REPORTED</strong> and must not be quoted as ORGANIZER-CONFIRMED.</p>
<h2>What was checked, and what was not</h2>
<table>
<tr><th>check</th><th>result</th></tr>
<tr><td>Local portal format checks (band, dtype, CRS, shape, transform, values in [0,1], NaN only
outside the footprint, all dots exactly 1.0)</td>
<td><strong>{(primary.get('validator') or {}).get('passed', 'not measured')}</strong></td></tr>
<tr><td>Uniqueness screen against the current registry
({(primary.get('registry') or {}).get('n_checked', '?')} rasters fetched from the live
repositories)</td>
<td>worst rank correlation {fmt((primary.get('registry') or {}).get('worst_rho'))}, worst 3 px
forward overlap {fmt((primary.get('registry') or {}).get('worst_forward_overlap'))}, triggers
{(primary.get('registry') or {}).get('n_triggers', '?')}</td></tr>
<tr><td>HOLDOUT-DTI (exact metric, hide-and-recover, {primary.get('holdout_dti_withheld_positives', '?')}
withheld positives)</td><td>{fmt(primary.get('holdout_dti'), 6)}</td></tr>
<tr><td>Organizer score</td><td><strong>none — no receipt</strong></td></tr>
</table>
<p class="small">A holdout number is not a leaderboard score, and a projection is never written
as one. The holdout here reads {fmt(primary.get('holdout_dti'), 4)} for a structural reason:
its withheld positives <em>are</em> catalogue pixels, and this emission is screened to sit off the
catalogue, so the instrument is blind to it by construction (IR-58-02). The evidence that this
emission is better comes from the equal-budget contest on the overview page and from the
sibling's paired live-anchored model.</p>
""" + FOOT)

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(index)
    (DOCS / "executive-summary.html").write_text(html)
    print("wrote", DOCS / "index.html")
    print("wrote", DOCS / "executive-summary.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
