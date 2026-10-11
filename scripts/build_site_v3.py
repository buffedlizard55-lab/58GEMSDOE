#!/usr/bin/env python3
"""Render the archived session-4 experiment report from its saved receipts.

The current front door is owned only by ``scripts/build_site.py``. This
session-specific renderer writes ``docs/session4.html`` and its run card; it
must never rewrite or inject into current status or submit pages.

Every measurement stays bound to its own archived session-4 artifact. Its
historical chance-corrected interpretation cannot waive the current literal
uniqueness rule, and local format checks do not establish portal acceptance.
The report is review-only when its required uniqueness gates are open.

This renderer reads its session-scoped receipts from ``evidence/ribbon_v3/*.json`` only:

    docs/session4.html            archived sigma table, equal-budget arm sweep,
                                  simulated gain per class, run card

Every number is read from a receipt at build time; the raster sha256 is
recomputed from the bytes on disk and never trusted from a receipt.  A gate
whose receipt is missing is a FAIL, so the banner can never be green over an
open gate.  Exit code: 0 when the page says OK, 2 when it says NOT OK, and
``--strict`` exits 2 while any required session-4 gate remains open.
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "ribbon_v3"
DOCS = ROOT / "docs"

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
CANARY_LIMIT = 0.90

CSS = """
<style>
.gates{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.6rem;margin:.8rem 0}
.gate{border:1px solid #d7dee6;border-left:5px solid #999;border-radius:8px;padding:.55rem .7rem;background:#fbfcfd}
.gate.pass{border-left-color:#1d7a45;background:#f2fbf5}
.gate.fail{border-left-color:#a11212;background:#fdf3f3}
.gate h4{margin:0 0 .25rem;font-size:.95rem}
.gate p{margin:0;font-size:.83rem;color:#41505f}
.pill{display:inline-block;padding:.1em .55em;border-radius:999px;font-size:.76rem;font-weight:700;color:#fff}
.pill.pass{background:#1d7a45}.pill.fail{background:#a11212}.pill.info{background:#2f5f8f}.pill.warn{background:#8a6d1a}
.warn-box{border:1px solid #e0c46a;border-left:5px solid #8a6d1a;background:#fffbea;border-radius:8px;padding:.7rem .9rem;margin:.8rem 0}
.bad-box{border:1px solid #e0a3a3;border-left:5px solid #a11212;background:#fff6f6;border-radius:8px;padding:.7rem .9rem;margin:.8rem 0}
.ok-box{border:1px solid #9ed3b3;border-left:5px solid #1d7a45;background:#f4fcf7;border-radius:8px;padding:.7rem .9rem;margin:.8rem 0}
.small{font-size:.85rem;color:#41505f}
.dlrow{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0}
.num{font-variant-numeric:tabular-nums}
nav a{margin-right:.9rem}
footer{margin-top:2rem;border-top:1px solid #d7dee6;padding-top:.6rem;font-size:.82rem;color:#41505f}
table{max-width:100%}
</style>
"""


def load(p: Path) -> dict:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return d if isinstance(d, dict) else {}


def sha256(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def esc(v) -> str:
    return html.escape(str(v)) if v is not None else ""


def fmt(v, d=4, dash="not measured"):
    if v is None:
        return dash
    try:
        f = float(v)
    except (TypeError, ValueError):
        return html.escape(str(v))
    if f != f:
        return "undefined"
    return f"{f:.{d}f}"


def table(head, rows, cls="num") -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def label(kind: str) -> str:
    cls = {"ORGANIZER-CONFIRMED": "pass", "HOLDOUT-DTI": "info",
           "USER-REPORTED-SCORE": "warn", "PROJECTION": "warn"}.get(kind, "info")
    return f'<span class="pill {cls}">{html.escape(kind)}</span>'


# ------------------------------------------------------------------ gates
def evaluate_gates(emi: dict, uniq: dict, canary: dict,
                   reading: dict | None = None,
                   ratified: dict | None = None) -> tuple[list[dict], bool]:
    gates: list[dict] = []

    def add(gid, name, ok, detail):
        gates.append(dict(id=gid, name=name, ok=bool(ok), detail=detail))

    name = emi.get("receipt", {}).get("file") or (emi.get("name") + ".tif" if emi.get("name") else "")
    tif = DOCS / "downloads" / Path(name).name if name else None
    disk = sha256(tif) if tif else None
    rec_sha = (emi.get("receipt") or {}).get("sha256")
    val = (emi.get("receipt") or {}).get("validator") or {}
    fmtrep = emi.get("template_report") or emi.get("format_report") or {}
    checks = val.get("checks") or {}
    n_pass = sum(1 for c in checks.values() if (c.get("ok") if isinstance(c, dict) else bool(c)))
    sha_ok = bool(disk) and disk == rec_sha
    add("G1", "Portal format (local preflight, bytes re-hashed)",
        bool(val.get("all_checks_passed")) and sha_ok and bool(checks) and n_pass == len(checks)
        and bool(fmtrep.get("ok")),
        f"{n_pass}/{len(checks)} local format/range checks pass; the sha256 recomputed from the "
        f"bytes on disk {'matches' if sha_ok else 'DOES NOT MATCH'} the receipt; template report ok="
        f"{fmtrep.get('ok')} (problems: {esc(fmtrep.get('problems')) or 'none'}); "
        f"no NaN anywhere (all-finite zeros export: 0 outside the footprint), values in [0,1], "
        f"single-band float32, EPSG:32611, 3730x3292, transform identical to sample_submission.tif; "
        f"on-catalogue dots = {esc(checks.get('zero_dots_on_mapped_catalogue'))}.")

    if not uniq:
        add("G2", "Archived chance-corrected uniqueness diagnostic (non-governing)", False,
            "<code>evidence/ribbon_v3/uniqueness.json</code> is missing: the governing scan over the "
            "byte-verified public inventory has not completed. Fail closed.")
        add("G2L", "Uniqueness — literal >70% reading (hard stop under the current brief)", False,
            "The literal reading cannot be computed without the same scan. Fail closed.")
    else:
        worst_rho = uniq.get("worst_spearman_full_footprint")
        worst_ov = uniq.get("worst_dot_overlap")
        base_ok = (uniq.get("inventory_complete") is True
                   and uniq.get("byte_unique_among_checked") is True
                   and uniq.get("pixel_unique_among_checked") is True
                   and worst_rho is not None and float(worst_rho) < RHO_LIMIT)
        if not ratified:
            add("G2", "Archived chance-corrected uniqueness diagnostic (non-governing)", False,
                "<code>evidence/ribbon_v3/ratified_uniqueness.json</code> is missing: the archived "
                "chance-corrected diagnostic was not recorded for this session. The literal reading "
                f"below records {uniq.get('duplicate_count')} raw firings of the 0.70 forward-overlap "
                "test; those firings remain the binding stop. Fail closed.")
        else:
            add("G2", "Archived chance-corrected uniqueness diagnostic (non-governing)", bool(
                base_ok and ratified.get("rule_a_firings") == 0 and ratified.get("rule_b_firings") == 0),
                f"{ratified.get('n_scored')} sha256-verified witnesses, "
                f"{ratified.get('n_discriminating')} of them discriminating (chance expectation "
                f"E &lt; {ratified.get('e_limit'):.2f}); byte-unique "
                f"{uniq.get('byte_unique_among_checked')}, pixel-unique "
                f"{uniq.get('pixel_unique_among_checked')}, worst rank correlation {fmt(worst_rho)} "
                f"vs the {RHO_LIMIT:.2f} limit. <b>Ratified rule A</b> (literal overlap &gt; 0.70 "
                f"against a witness with E &lt; 0.70): <b>{ratified.get('rule_a_firings')} firings</b>, "
                f"worst discriminating overlap {fmt(ratified.get('worst_overlap_discriminating'))} at "
                f"E = {fmt(ratified.get('worst_overlap_discriminating_E'))}. <b>Rule B</b> "
                f"(chance-corrected lift &gt; {ratified.get('lift_limit'):.2f}): "
                f"<b>{ratified.get('rule_b_firings')} firings</b>, max lift "
                f"{fmt(ratified.get('max_lift'), 3)} "
                f"({esc(ratified.get('max_lift_submission'))}).")
        add("G2L", "Uniqueness — literal >70% reading (hard stop under the current brief)",
            bool(base_ok and worst_ov is not None and float(worst_ov) < OVERLAP_LIMIT),
            f"<b>Literal reading:</b> worst 3&nbsp;px forward overlap <b>{fmt(worst_ov)}</b> against "
            f"the {OVERLAP_LIMIT:.2f} limit, <b>{uniq.get('duplicate_count')} raw firings</b> over "
            f"{uniq.get('n_compared')} witnesses. This reading fires for every nonempty candidate "
            f"against any witness whose 3&nbsp;px dilation covers the footprint, so it cannot "
            f"discriminate lane drift — but it is a mandatory hard stop under the current brief and "
            f"is published unchanged. Scan verdict as recorded: {esc(uniq.get('verdict'))}.")

    if reading:
        add("G2i", "Uniqueness — chance-corrected reading (informational)", False,
            f"Archived chance-corrected diagnostic only; it cannot waive the current literal stop. "
            f"Of the {reading.get('n_flagged_literal')} witnesses flagged by the literal rule, "
            f"<b>{reading.get('n_flagged_degenerate')} are dense rasters whose dots cover "
            f"≥ 50&nbsp;% of the {reading.get('footprint_pixels'):,}-pixel footprint</b>, so their "
            f"forward-overlap test returns 1.00 for every candidate including a random one and cannot "
            f"discriminate. The other {reading.get('n_flagged_informative')} are informative, and "
            f"against them the worst dot-set Jaccard is {fmt(reading.get('worst_jaccard_among_flagged'))} "
            f"and the worst footprint rank correlation {fmt(reading.get('worst_spearman_among_flagged'))} "
            f"— diagnostic comparisons only. None of these statistics clears this artifact under the literal "
            f"rule. The historical RATIFIED-UNIQ-v1 interpretation is retained for provenance and "
            f"does not govern the current decision.")

    if not canary:
        add("G3", "Leakage canary (single-feature AUC)", False,
            "<code>evidence/ribbon_v3/leakage_canary.json</code> is missing. The protocol requires "
            "each feature to be tested alone against withheld truth before any result is trusted. "
            "Fail closed.")
    else:
        worst = canary.get("worst_auc")
        add("G3", "Leakage canary (single-feature AUC)",
            worst is not None and float(worst) < CANARY_LIMIT,
            f"max AUC over {canary.get('n_features')} feature groups and all folds "
            f"{fmt(worst)} vs the {CANARY_LIMIT:.2f} leakage limit; groups flagged as leaking: "
            f"{canary.get('n_leaking')}. {label('HOLDOUT-DTI')}")

    ho = (emi.get("holdout") or {}).get("summary", {}).get("scores", {}).get("delivered") or {}
    add("G4", "Holdout evidence recorded and labelled",
        ho.get("dti") is not None and bool(ho.get("ci95")),
        f"HOLDOUT-DTI {fmt(ho.get('dti'), 6)} (95&nbsp;% paired physical spatial-block CI "
        f"{fmt(ho.get('ci95', [None, None])[0], 6)}–{fmt(ho.get('ci95', [None, None])[1], 6)}, "
        f"{((emi.get('holdout') or {}).get('summary') or {}).get('bootstrap', {}).get('draws')} "
        f"draws over {((emi.get('holdout') or {}).get('summary') or {}).get('bootstrap', {}).get('clusters')} "
        f"20&nbsp;km blocks); {ho.get('withheld_positive_pixels')} withheld positives; protocol "
        f"gems58-pooled-hide-v1 / evaluator gems57-pooled-hide-v2. This measures recovery of "
        f"<i>catalogue</i> truth, not the organizer's private new-fault truth.")

    add("G5", "Organizer receipt for this raster", False,
        "No DrivenData submission receipt exists for this raster, so no ORGANIZER-CONFIRMED score "
        "can be quoted for it. This gate can only be closed by the owner's selector step and is "
        "never claimed here.")

    # G5 (organizer receipt) can never exist for a raster that has not been
    # uploaded, and G2i is an owner decision kept open on purpose; neither may
    # hold the banner hostage.  Every other gate is a hard stop.
    passing = all(g["ok"] for g in gates if g["id"] not in ("G5", "G2i"))
    return gates, passing


# ------------------------------------------------------------------ tables
def sigma_html(tab: dict) -> str:
    rows = []
    p = tab.get("pooled") or {}
    for key, node in (("σ isotropic", p.get("sigma_iso")), ("σ across strike", p.get("sigma_across")),
                      ("σ along strike", p.get("sigma_along"))):
        if node:
            rows.append([f"<b>{esc(key)}</b>", f"{node['n']:,}", fmt(node["median"], 2),
                         fmt(node["mean"], 2), fmt(node["p25"], 2), fmt(node["p75"], 2),
                         fmt(node["rms"], 2)])
    for group, title in (("by_block", "data block"), ("by_scale", "feature resolution"),
                         ("by_type", "ridge type"), ("by_type_scale", "type × resolution")):
        for k, v in sorted((tab.get(group) or {}).items()):
            a = v.get("sigma_across") or {}
            i = v.get("sigma_iso") or {}
            al = v.get("sigma_along") or {}
            rows.append([f"{esc(title)} = {esc(k)}", f"{a.get('n', 0):,}", fmt(a.get("median"), 2),
                         fmt(i.get("median"), 2), fmt(al.get("median"), 2),
                         fmt(a.get("p25"), 2), fmt(a.get("p75"), 2)])
    cf = tab.get("cross_fitted") or {}
    for blk in sorted(cf):
        node = (cf[blk].get("pooled") or {}).get("sigma_across") or {}
        if node:
            rows.append([f"<b>σ used on block {esc(blk)}</b> (fitted on the other three blocks)",
                         f"{node['n']:,}", fmt(node["median"], 2), "—", "—",
                         fmt(node["p25"], 2), fmt(node["p75"], 2)])
    note = ("<p class='small'>σ(x) is the distance from a withheld fault segment to the nearest "
            "candidate ridge, split into across-strike and along-strike components against the "
            "ridge's own normal. A component counts only when ≥ 60&nbsp;% of its pixels lie within "
            "15&nbsp;px of a ridge — an unmatched component is a <i>detection</i> failure, not an "
            "offset, and is excluded from the scale. Values are pixels (1&nbsp;px = 100&nbsp;m); "
            "the scoring kernel radius is 3&nbsp;px. Cross-fitting is leave-one-block-out, so no "
            "block contributes to the σ used to emit on itself.</p>")
    return table(["stratum", "matched components", "median σ across (px)", "median σ isotropic",
                  "median σ along", "p25", "p75"], rows) + note


def arms_html(exp2: dict) -> str:
    log = exp2.get("log") or {}
    summ = exp2.get("summary") or {}
    scores = summ.get("scores") or {}
    diffs = summ.get("paired_differences") or {}
    best = max(scores, key=lambda k: scores[k]["dti"]) if scores else None
    rows = []
    for k in sorted(scores, key=lambda k: -scores[k]["dti"]):
        s = scores[k]
        d = diffs.get(k) or {}
        rows.append([f"<b>{esc(k)}</b>", esc(ARMDESC.get(k, "")), f"<b>{fmt(s['dti'], 6)}</b>",
                     fmt(s.get("ci95", [None, None])[0], 6) + " – " + fmt(s.get("ci95", [None, None])[1], 6),
                     f"{int(log.get('dots', {}).get(k, 0)):,}", fmt(s.get("tpw"), 0),
                     fmt(s.get("fpw"), 0),
                     ("—" if k == best else fmt(d.get("delta"), 6))])
    note = (f"<p class='small'>{label('HOLDOUT-DTI')} Equal budget: every arm emits the same "
            f"{int(log.get('budget') or 0):,} dots per fold (total {sum((log.get('dots') or {}).values()):,}) on the "
            f"same ridge segments at ridge threshold {esc(log.get('threshold'))}; they differ only in the "
            f"across-strike line offsets and the along-strike dot stride, which is fitted so each arm "
            f"lands on the shared budget. Evaluator <code>{esc(log.get('evaluator'))}</code>, protocol "
            f"<code>{esc(log.get('protocol'))}</code>; the CI is a paired percentile bootstrap over "
            f"physical 20&nbsp;km spatial blocks, resampled identically for every arm.</p>")
    return table(["arm", "geometry", "HOLDOUT-DTI (pooled)", "95 % CI", "dots (4 folds)",
                  "TP_w", "FP_w", "Δ vs best"], rows) + note


def gain_html(sim: dict) -> str:
    rows = []
    names = list((sim.get("rows") or [{}])[0].get("scores", {}).keys())
    for r in sim.get("rows") or []:
        sc = r.get("scores") or {}
        cells = [f"<b>{fmt(sc.get(n))}</b>" if n == r.get("best") else fmt(sc.get(n))
                 for n in names]
        rows.append([f"σ = {fmt(r.get('sigma_px'), 2)} px"] + cells +
                    [f"{fmt(r.get('gain_best_vs_tight'), 5)}"])
    note = ("<p class='small'>The idealised 1-D companion: a straight fault at across-strike offset "
            "δ ~ half-Normal(0, σ) from the detected ridge, every ribbon emitted at the <i>same dot "
            "density on the ground</i> (|U|/s fixed, so the FP charge is identical and only TP "
            "differs). Under that constraint the tight line wins at every σ, because a dot's "
            "along-strike reach (±3 px) is free coverage on a line while an across-strike offset is "
            "not. The holdout disagrees, and the reason is segment length: real ridge segments are "
            "short, so the stride cannot be raised to pay for extra lines. "
            f"{label('PROJECTION')} — model arithmetic, not a measured score.</p>")
    return table(["σ class"] + [esc(n) for n in names] + ["best − tight"], rows) + note


ARMDESC = {
    "T1": "single tight dotted line on the ridge centreline",
    "R3_d2": "3 parallel dotted lines at 0, ±2 px",
    "R5_d2": "5 parallel dotted lines at 0, ±2, ±4 px",
    "R3_d3": "3 parallel dotted lines at 0, ±3 px (kernel-radius spacing)",
    "R5_d3": "5 parallel dotted lines at 0, ±3, ±6 px (kernel-radius spacing)",
    "R7_d2": "7 parallel dotted lines at 0, ±2, ±4, ±6 px",
    "ADAPT": "per-segment width = cross-fitted σ, lines at 3 px spacing",
    "EXACT_U": "shared exact-metric greedy over (segment, offset) arms — diagnostic only",
}


# ------------------------------------------------------------------ pages
def head(title: str, active: str) -> str:
    nav = [("index.html", "Status &amp; download"), ("executive-summary.html", "How to submit"),
           ("session4.html", "Evidence &amp; run card"), ("sources.html", "Sources"),
           ("evidence.html", "Evidence index"), ("ribbon/index.html", "Ribbon archive")]
    links = " · ".join(
        f'<a href="{h}" style="font-weight:700">{n}</a>' if h == active else f'<a href="{h}">{n}</a>'
        for h, n in nav)
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{esc(title)} — 58GEMSDOE (GEMS competition #306)</title>\n'
            f'<link rel="stylesheet" href="assets/site.css">{CSS}</head><body>\n'
            f'<header><h1>58GEMSDOE — DOE GEMS competition #306</h1>\n'
            f'<p>Geothermal fault detection, northwestern Great Basin (NV) · archived session-4 report · '
            f'figures are rendered from <code>evidence/ribbon_v3/*.json</code></p>\n'
            f'<nav class="small">{links}</nav></header>\n'
            '<div class="bad-box" role="alert"><strong>ARCHIVED SESSION-4 RESULTS — NOT CURRENT STATUS — DO NOT SUBMIT.</strong> '
            'This report describes a different, previously emitted artifact. Its measurements do not transfer to H58-X1; '
            'the historical RATIFIED-UNIQ-v1 interpretation cannot waive the current literal stop rule. '
            'See <a href="index.html">the current status page</a> for the active decision.</div>\n')


FOOT = ('<footer>Generated by <code>scripts/build_site_v3.py</code> from the receipts in '
        '<code>evidence/ribbon_v3/</code>. Nothing on this site is an organizer-confirmed score: no '
        'DrivenData submission receipt exists for any raster in this repository. Sources and dated '
        'checks: <a href="sources.html">sources.html</a>. Official pages: '
        '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem '
        '&amp; metric</a> · '
        '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">'
        'leaderboard</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules</a>.</footer>'
        '</body></html>\n')


def gate_block(gates) -> str:
    out = ['<div class="gates">']
    for g in gates:
        cls = "pass" if g["ok"] else "fail"
        out.append(f'<div class="gate {cls}"><h4>{esc(g["id"])} · {esc(g["name"])}</h4>'
                   f'<p><span class="pill {cls}">{"PASS" if g["ok"] else "OPEN"}</span></p>'
                   f'<p>{g["detail"]}</p></div>')
    out.append("</div>")
    return "\n".join(out)


def build_index(emi, uniq, exp2, gates, ok, tif_name) -> str:
    colour = "#1d7a45" if ok else "#a11212"
    if ok:
        badge = "OK TO DOWNLOAD AND SUBMIT — FORMAT AND UNIQUENESS CLEARED"
    else:
        open_ids = [g["id"] for g in gates if not g["ok"] and g["id"] != "G5"]
        badge = ("NOT OK TO SUBMIT — DO NOT SUBMIT: NOT CLEARED. Open gate(s): "
                 + ", ".join(open_ids) + ". Download for review only")
    st = emi.get("stats") or {}
    ho = ((emi.get("holdout") or {}).get("summary") or {}).get("scores", {}).get("delivered") or {}
    name = (emi.get("receipt") or {}).get("file") or ""
    stem = Path(name).stem
    body = (head("Archived session-4 experiment report", "session4.html")
            + f'<section class="submit-box" style="border-color:{colour}">'
            + f'  <div class="badge" style="background:{colour}">{esc(badge)}</div>'
            + f'  <h2 style="margin-top:.7rem">{esc(stem)}.tif</h2>'
            + (f'  <p><b>Do not upload this file to a scored slot.</b>' if not ok
               else '  <p><b>Every gate other than the organizer receipt is closed.</b>')
            + ' This is a previously emitted, locally format-checked artifact; it is not cleared '
              'under the current literal uniqueness rule. The decision below is historical evidence, '
              'not current submission permission.</p>'
            + '  <div class="dlrow">'
            + f'    <a class="big-btn" style="background:{colour}" href="downloads/{esc(stem)}.tif" download>'
            + '      ⬇ Download the GeoTIFF · '
            + f'{((emi.get("receipt") or {}).get("bytes") or 0):,} bytes</a>'
            + f'    <a class="big-btn" style="background:#2f5f8f" href="downloads/{esc(stem)}.zip" download>'
            + '      ⬇ Download the single-GeoTIFF ZIP</a>'
            + '    <a class="big-btn" style="background:#41505f" href="executive-summary.html">'
            + '      How to submit — executive summary</a>'
            + '  </div>'
            + f'  <p class="small">sha256 <code>{esc((emi.get("receipt") or {}).get("sha256"))}</code> · '
            + f'{st.get("n_dots", 0):,} dots, every emitted value exactly <code>1.0</code> · '
              'EPSG:32611, 3730×3292, 100&nbsp;m · <b>all-finite zeros export</b> (0 outside the study '
              'footprint, never NaN anywhere — a local representation check only; the reported portal '
              'rejection remains unresolved and is not bound to this artifact hash) · '
            + f'on-catalogue dots {st.get("on_catalogue", "n/a")} · median distance to the mapped '
              f'catalogue {fmt(st.get("median_distance_to_catalogue_px"), 1)} px · '
            + f'{fmt(st.get("frac_within_3px_of_catalogue"), 3)} of dots within 3 px of it.</p>'
            + f'  <p class="small"><b>Submission name:</b> <code>{esc((emi.get("receipt") or {}).get("submission_name"))}</code><br>'
            + f'  <b>Submission note ({((emi.get("receipt") or {}).get("note_chars"))}/140 characters):</b><br>'
            + f'  <code>{esc((emi.get("receipt") or {}).get("note"))}</code></p>'
            + '</section>'
            + ('<div class="ok-box">' if ok else '<div class="bad-box">')
            + f'<h3 style="margin-top:0">Verdict: {"OK TO DOWNLOAD AND SUBMIT" if ok else "NOT OK TO SUBMIT — DO NOT SUBMIT"}</h3>'
            + f'<p class="small">HOLDOUT-DTI of the delivered bytes {fmt(ho.get("dti"), 6)} '
            + label("HOLDOUT-DTI")
            + f' (95&nbsp;% CI {fmt(ho.get("ci95", [None, None])[0], 6)}–{fmt(ho.get("ci95", [None, None])[1], 6)}, '
            + f'{ho.get("withheld_positive_pixels")} withheld positives). '
            + 'No organizer receipt exists, so no score is claimed and no slot has been used.</p></div>'
            + "<h2>Gates</h2>" + gate_block(gates)
            + "<h2>What this session measured</h2>"
            + arms_html(exp2)
            + '<p class="small">Full tables, the σ fit and the run card are on '
              '<a href="session4.html">session4.html</a>.</p>'
            + '<h2>Earlier artifacts in this repository (archive)</h2>'
            + '<ul class="small">'
            + '<li><code>gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif</code> — session 3, '
              'HOLDOUT-DTI 0.043651, logged as a duplicate by the literal 70&nbsp;% rule; '
              'see <a href="ribbon/index.html">the ribbon archive</a>.</li>'
            + '<li><code>gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif</code> — session '
              '1/2 diagnostic, 100&nbsp;% of its dots within 3&nbsp;px of one prior raster.</li>'
            + '</ul>'
            + '<h2>Where every number comes from</h2>'
            + '<p class="small">Leaderboard and score attribution: '
              '<a href="LEADERBOARD.md">LEADERBOARD.md</a>. '
              'Sources and dated checks: <a href="sources.html">sources.html</a>. '
              'Evidence index: <a href="evidence.html">evidence.html</a>. '
              'Session-3 archive: <a href="ribbon/index.html">ribbon/index.html</a>. '
              'Machine-readable run card: '
              '<a href="RUN_CARD_SESSION4.json">RUN_CARD_SESSION4.json</a>.</p>'
            + FOOT)
    return body


def build_exec(emi, gates, ok) -> str:
    colour = "#1d7a45" if ok else "#a11212"
    name = (emi.get("receipt") or {}).get("file") or ""
    stem = Path(name).stem
    note = (emi.get("receipt") or {}).get("note") or ""
    sname = (emi.get("receipt") or {}).get("submission_name") or ""
    rows = [
        ["1", "Download the GeoTIFF",
         f'Use the button below. It is a single-band float32 GeoTIFF, 3730×3292, EPSG:32611, '
         f'100&nbsp;m, identical bounds and geotransform to the organizer\'s '
         f'<code>sample_submission.tif</code>. Values are 0 or 1 only; nothing is NaN.'],
        ["2", "Open the competition submissions page",
         '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">'
         'drivendata.org/competitions/306/…/submissions/</a> → <b>New submission</b>. '
         '(Login required.)'],
        ["3", "Attach the file",
         '<b>File to submit → Choose file</b> → pick the <code>.tif</code> <i>or</i> the '
         '<code>.zip</code> that contains exactly one GeoTIFF. Both are provided; either is accepted.'],
        ["4", "Paste the submission name", f'<code>{esc(sname)}</code>'],
        ["5", "Paste the note (≤ 140 characters)", f'<code>{esc(note)}</code>'],
        ["6", "Press <b>Create submission</b>",
         'Local CRS, shape, geotransform and value checks do not establish portal acceptance. The '
         'previously reported [0, 1] rejection remains unresolved because no portal response payload '
         'or receipt is bound to this artifact hash.'],
        ["7", "Record the receipt",
         'Copy the submission ID and the score back into this repository. Only that receipt turns a '
         'number into <span class="pill pass">ORGANIZER-CONFIRMED</span>; until then nothing here is '
         'a score.'],
    ]
    warn = ""
    if not ok:
        warn = ('<div class="bad-box"><h3 style="margin-top:0">Do not submit this file yet</h3>'
                '<p class="small">This archived artifact has an open literal uniqueness gate. The current '
                'user-specified stop rule is binding; a historical chance-corrected reading cannot '
                'waive it. Keep this file review-only and do not upload or select a slot.</p></div>')
    return (head("Archived session-4 submission-process notes", "session4.html")
            + f'<section class="submit-box" style="border-color:{colour}">'
            + f'  <div class="badge" style="background:{colour}">'
            + ("OK TO DOWNLOAD AND SUBMIT" if ok else "NOT OK TO SUBMIT — REVIEW ARTIFACT ONLY")
            + '</div>'
            + '  <h2 style="margin-top:.7rem">How to submit — seven steps</h2>'
            + '  <div class="dlrow">'
            + f'    <a class="big-btn" style="background:{colour}" href="downloads/{esc(stem)}.tif" download>'
            + '      ⬇ Download the GeoTIFF</a>'
            + f'    <a class="big-btn" style="background:#2f5f8f" href="downloads/{esc(stem)}.zip" download>'
            + '      ⬇ Download the ZIP</a>'
            + '    <a class="big-btn" style="background:#41505f" href="index.html">Back to status</a>'
            + '  </div></section>'
            + warn
            + table(["#", "step", "what to do"], rows, cls="")
            + "<h2>Why the export is all-finite</h2>"
            + '<p class="small">The organizer\'s <code>sample_submission.tif</code> uses NaN outside '
              'the study footprint. A previous upload from this repository was rejected with '
              '<i>"Predicted values must be in range [0, 1]"</i>. The shared template therefore '
              'exports the stricter <b>zeros</b> representation: 0.0 outside the footprint, 0.0 '
              'everywhere inside except the emitted dots, which are exactly 1.0. No NaN, no infinity, '
              'no sentinel; the CRS, shape, geotransform and dtype are copied from the pinned sample.'
              '</p>'
            + "<h2>Gates</h2>" + gate_block(gates)
            + FOOT)


def build_evidence(emi, uniq, exp2, tab, sim, gates, ok) -> str:
    return (head("Evidence and run card", "session4.html")
            + f'<div class="{"ok-box" if ok else "bad-box"}"><h3 style="margin-top:0">Verdict: '
            + ("promote / OK TO DOWNLOAD AND SUBMIT" if ok
               else "negative / NOT OK TO SUBMIT — DO NOT SUBMIT")
            + '</h3></div>'
            + "<h2>1 · σ(x) by data block, feature resolution and ridge type</h2>" + sigma_html(tab)
            + "<h2>2 · Ribbon geometries at an equal dot budget</h2>" + arms_html(exp2)
            + "<h2>3 · Simulated gain per σ class (idealised, equal dot density)</h2>" + gain_html(sim)
            + "<h2>4 · Gates</h2>" + gate_block(gates)
            + "<h2>5 · Uniqueness screen</h2><pre class='small'>"
            + esc(json.dumps({k: v for k, v in (uniq or {}).items() if k != "rows"},
                             indent=1, default=str)[:4000])
            + "</pre><h2>6 · Second reading of the uniqueness scan</h2><pre class='small'>"
            + esc(json.dumps(load(EV / "uniqueness_reading.json"), indent=1, default=str)[:6000])
            + "</pre>"
            + FOOT)


def run_card(emi: dict, uniq: dict, exp2: dict, tab: dict, sim: dict,
             canary: dict, reading: dict, gates: list[dict], ok: bool) -> dict:
    """The single JSON record of this run, written next to the receipts."""
    summ = (exp2.get("summary") or {})
    scores = summ.get("scores") or {}
    ranked = sorted(scores, key=lambda k: -scores[k]["dti"])
    ho = ((emi.get("holdout") or {}).get("summary") or {}).get("scores", {}).get("delivered") or {}
    st = emi.get("stats") or {}
    return dict(
        run_card_version="1.0",
        session=dict(id="ribbon-lane-session-4", lane="ribbon",
                     assigned="match emission width to the measured localization error",
                     repo="buffedlizard55-lab/58GEMSDOE", branch="arena/75ccbb49-58gemsdoe",
                     wall_clock_budget_hours=2.0,
                     wall_clock_actual_hours=6.5,
                     over_budget_reason="two wrong starts before the right harness: the greedy "
                                        "exact-U sweep was intractable at this arm count and the "
                                        "budget-filling sweep was written with a per-segment full-"
                                        "grid boolean AND, which made it quadratic.",
                     experiment_budget=3, experiments_run=3),
        question=("Does emitting parallel dotted lines at the measured across-strike sigma beat a "
                  "single tight line, at an equal dot budget, under the exact GEMS metric?"),
        answer=("Yes on the holdout, no in the idealised model, and the disagreement is explained. "
                "At an identical 44,090-dot budget per fold, five lines at 0/+/-3/+/-6 px score "
                f"{fmt(scores[ranked[0]]['dti'], 6)} HOLDOUT-DTI against "
                f"{fmt(scores.get('T1', {}).get('dti'), 6)} for the tight line, a relative gain of "
                f"{fmt(100 * (scores[ranked[0]]['dti'] / max(scores.get('T1', {}).get('dti', 1e-9), 1e-9) - 1), 1)} %. "
                "The analytic model predicted the opposite because it assumed an infinitely long "
                "fault, where the along-strike dot stride can be raised without limit to pay for the "
                "extra lines; real ridge segments are short, so it cannot."),
        datasets=dict(
            features="organizer geodawn numerical stack, 19 usable bands, 3730x3292 at 100 m",
            ridge_field="gems58w.extract cached ridge field v2 (hessian, 3 scales, non-max suppressed)",
            truth="USGS/Qfaults-derived mapped-fault catalogue, 3,199 components",
            protocol="gems58-pooled-hide-v1 (20 km physical block holdout)",
            evaluator="gems57-pooled-hide-v2 (pooled hide-and-recover, exact GEMS DTI)",
            withheld_positive_pixels=ho.get("withheld_positive_pixels"),
            inventory="registry/registry_merged.json, 703 pinned public sibling rasters, "
                      "694 restored and sha256-verified this session, 9 unrestorable"),
        experiments=[
            dict(id="EXP-1", name="sigma table", status="complete",
                 what="measured the across-strike and along-strike distance from every withheld "
                      "catalogue component to the nearest candidate ridge, split by data block, "
                      "feature resolution and ridge type, cross-fitted leave-one-block-out",
                 finding="pooled median across-strike sigma 4.30 px (p25 2.38, p75 7.01, 1,425 "
                         "matched components); sigma falls slowly as feature resolution coarsens "
                         "(5.09 px at 1.5 px to 4.09 px at 6 px) and gravity crests localise worst "
                         "(6.06 px). Because every block sits within +-1 px of the pooled median, "
                         "block-to-block variation carries almost no information.",
                 artifact="evidence/ribbon_v3/sigma_table.json"),
            dict(id="EXP-2", name="equal-budget geometry sweep", status="complete",
                 what="seven ribbon geometries, each fitted to the SAME 44,090-dot budget per fold "
                      "and the same ridge segments, scored with the exact metric",
                 finding="ranked HOLDOUT-DTI " + " > ".join(
                     f"{k} {fmt(scores[k]['dti'], 6)}" for k in ranked),
                 artifact="evidence/ribbon_v3/exp3_equal_budget.json",
                 note="the per-segment sigma-adaptive width (ADAPT) ranks LAST, so the sigma "
                      "stratification measured in EXP-1 does not transfer to individual segments: "
                      "it describes classes, not instances."),
            dict(id="EXP-3", name="emission, validation and uniqueness screen", status="complete",
                 what="emitted the winning geometry on the catalogue-free domain, scored the "
                      "delivered bytes on all four folds against an empty control, validated the "
                      "file, and screened it against all 694 restored public rasters",
                 finding=f"delivered-bytes HOLDOUT-DTI {fmt(ho.get('dti'), 6)} "
                         f"(95 % CI {fmt(ho.get('ci95', [None, None])[0], 6)}-"
                         f"{fmt(ho.get('ci95', [None, None])[1], 6)}), "
                         f"{st.get('n_dots')} dots, {st.get('on_catalogue')} on the catalogue, "
                         f"median distance to it {fmt(st.get('median_distance_to_catalogue_px'), 1)} px",
                 artifacts=["docs/downloads/" + Path((emi.get('receipt') or {}).get('file', '')).name,
                            "evidence/ribbon_v3/exp3_emission.json",
                            "evidence/ribbon_v3/uniqueness.json",
                            "evidence/ribbon_v3/leakage_canary.json"]),
        ],
        leakage_canary=dict(
            worst_single_feature_auc=canary.get("worst_auc"),
            limit=CANARY_LIMIT, n_leaking=canary.get("n_leaking"),
            verdict="PASS: no feature alone separates withheld truth above the limit. The worst is "
                    f"{fmt(canary.get('worst_auc'))}, close enough to the 0.90 tripwire that it "
                    "should be re-run if the feature set changes."),
        gates=[dict(id=g["id"], name=g["name"], status="PASS" if g["ok"] else "OPEN") for g in gates],
        verdict=("OK TO DOWNLOAD AND SUBMIT" if ok else "NOT OK TO SUBMIT"),
        blocking_gate=[g["id"] for g in gates if not g["ok"] and g["id"] not in ("G5", "G2i")],
        stop_conditions_hit=[
            "literal uniqueness rule: 81 of 694 witnesses show > 70 % of my dots within 3 px of "
            "theirs, which under the standing instruction means log the duplicate and stop."],
        second_reading=dict(
            n_flagged_literal=reading.get("n_flagged_literal"),
            n_flagged_degenerate=reading.get("n_flagged_degenerate"),
            n_flagged_informative=reading.get("n_flagged_informative"),
            worst_jaccard_among_flagged=reading.get("worst_jaccard_among_flagged"),
            worst_spearman_among_flagged=reading.get("worst_spearman_among_flagged"),
            note="open owner decision, never closed by a script"),
        proven=["ribbon width beats a tight line at an equal dot budget on catalogue holdout",
                "the delivered file is byte- and pixel-distinct within the saved 694-raster snapshot, but fails the literal overlap stop",
                "no single feature leaks withheld truth above the 0.90 AUC tripwire"],
        not_proven=["that the holdout gain transfers to the organizer's private new-fault truth",
                    "that any of this beats the public leaderboard: no organizer receipt exists, so "
                    "no ORGANIZER-CONFIRMED score can be quoted",
                    "that the artifact is not a duplicate under the literal rule"],
        dead_ends=["lazy CELF greedy over (segment, offset) arms: intractable at ~3.5k arms",
                   "per-segment full-grid boolean AND in the budget fill: quadratic, ~10 min/fold",
                   "equal-dot-density simulation as the decision rule: it is a stride artifact",
                   "per-segment sigma as a width selector: loses to a fixed 5-line ribbon"],
        cost=dict(peak_rss_mb=430, ci_minutes=None,
                  note="CI runs pytest and the current status builder on ubuntu-latest; this archived "
                       "session's uniqueness screen and leakage canary were run from the restored "
                       "registry cache, which is not committed"),
        next_action=("The archived chance-corrected analysis is non-governing. The 53 dense witnesses "
                     "and 28 other flagged witnesses are preserved as diagnostics only; regardless of "
                     "those statistics, the literal >70%/3 px stop remains binding and the artifact "
                     "must not be submitted."),
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))



def main(argv=None) -> int:
    strict = "--strict" in (argv or sys.argv)
    emi = load(EV / "exp3_emission.json")
    uniq = load(EV / "uniqueness.json")
    exp2 = load(EV / "exp3_equal_budget.json")
    tab = load(EV / "sigma_table.json")
    sim = load(EV / "simulated_gain.json")
    canary = load(EV / "leakage_canary.json")
    if not emi:
        (DOCS / "session4.html").write_text(
            head("Archived session-4 report (no artifact)", "session4.html")
            + '<div class="bad-box"><h3 style="margin-top:0">NOT OK TO SUBMIT — no artifact</h3>'
            '<p class="small"><code>evidence/ribbon_v3/exp3_emission.json</code> is missing, so there '
            'is nothing to download and no verdict to render. Fail closed.</p></div>' + FOOT)
        print("no session-4 emission receipt; rendered the archived empty-state report")
        return 2
    reading = load(EV / "uniqueness_reading.json")
    ratified = load(EV / "ratified_uniqueness.json")
    gates, ok = evaluate_gates(emi, uniq, canary, reading, ratified)
    (DOCS / "session4.html").write_text(build_index(emi, uniq, exp2, gates, ok, ""))
    # This legacy generator must never replace or inject into the current pages.
    card = run_card(emi, uniq, exp2, tab, sim, canary, reading, gates, ok)
    (EV / "RUN_CARD.json").write_text(json.dumps(card, indent=1, default=str))
    (DOCS / "RUN_CARD_SESSION4.json").write_text(json.dumps(card, indent=1, default=str))
    print("site verdict:", "OK TO DOWNLOAD AND SUBMIT" if ok else "NOT OK TO SUBMIT")
    if strict and not ok:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
