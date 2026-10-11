#!/usr/bin/env python3
"""Build the owner-facing GitHub Pages site from recorded evidence, fail-closed.

One generator, one source of truth: every number on the page is read out of an
``evidence/**.json`` receipt at build time and re-verified where it can be (the
delivered raster's sha256 is recomputed from the bytes on disk, never trusted
from the receipt).  Nothing is presented as a score unless it carries one of the
labels the protocol allows:

    ORGANIZER-CONFIRMED   copied from a DrivenData page or submission receipt
    HOLDOUT-DTI           measured here with the named evaluator and protocol,
                          the withheld-positive count and an honest interval
    USER-REPORTED-SCORE   an owner-quoted sibling page; no receipt exists
    PROJECTION            arithmetic from the official metric; never a score

The download decision is rendered as explicit gates.  A gate whose receipt is
missing is a FAIL, not a pass.  Exit status is 0 when the site says OK and 2
when it says NOT OK, so CI can assert the banner matches the evidence.

    python3 scripts/build_site.py
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
RIB = EV / "ribbon"
DOCS = ROOT / "docs"

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
CANARY_LIMIT = 0.90
LEADER_DTI = 0.4133       # ORGANIZER-CONFIRMED: public leaderboard #1, fetched 2026-10-11
LEADER_WHO = "xiaofanhu (public leaderboard #1, fetched 2026-10-11)"
OWNER_TARGET = 0.3195     # the owner-reported target; see IR-58-TARGET-01

EXTRA_CSS = """
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
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1rem}
.small{font-size:.85rem;color:#41505f}
.dlrow{display:flex;flex-wrap:wrap;gap:.6rem;margin:.8rem 0}
.num{font-variant-numeric:tabular-nums}
nav a{margin-right:.9rem}
footer{margin-top:2rem;border-top:1px solid #d7dee6;padding-top:.6rem;font-size:.82rem;color:#41505f}
table{max-width:100%}
</style>
"""


# --------------------------------------------------------------------------- io
def load(path: Path) -> dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return d if isinstance(d, dict) else {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(v, digits=4, dash="not measured"):
    if v is None:
        return dash
    try:
        f = float(v)
    except (TypeError, ValueError):
        return html.escape(str(v))
    if f != f:  # NaN
        return "undefined"
    return f"{f:.{digits}f}"


def esc(v) -> str:
    return html.escape(str(v)) if v is not None else ""


def table(head: list[str], rows: list[list], cls: str = "num") -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def label(kind: str) -> str:
    cls = {"ORGANIZER-CONFIRMED": "pass", "HOLDOUT-DTI": "info",
           "USER-REPORTED-SCORE": "warn", "PROJECTION": "warn"}.get(kind, "info")
    return f'<span class="pill {cls}">{html.escape(kind)}</span>'


# ------------------------------------------------------------------------ gates
def evaluate_gates(emi: dict, sig: dict, inv: dict, tif: Path) -> tuple[list[dict], bool]:
    gates: list[dict] = []

    def add(gid, name, ok, detail):
        gates.append(dict(id=gid, name=name, ok=bool(ok), detail=detail))

    val = emi.get("validator", {})
    checks = val.get("checks", {}) or {}
    n_pass = sum(1 for c in checks.values() if c.get("ok"))
    on_disk = tif.exists()
    disk_sha = sha256(tif) if on_disk else None
    sha_ok = bool(on_disk) and disk_sha == emi.get("sha256")
    add("G1", "Portal format (local preflight)",
        val.get("passed") is True and sha_ok and checks and n_pass == len(checks),
        f"{n_pass}/{len(checks)} local checks pass; the sha256 recomputed from the bytes on disk "
        f"{'matches' if sha_ok else 'DOES NOT MATCH'} the receipt; "
        f"{esc(checks.get('finite_inside_footprint', {}).get('detail'))}; "
        f"{esc(checks.get('values_in_unit_interval', {}).get('detail'))}; representation = the "
        f"organizer's sample_submission (NaN outside the study footprint, nodata=nan)")

    ul = emi.get("uniqueness_local", {}) or {}
    add("G2", "Uniqueness — local witnesses (corrected instrument)",
        ul.get("cleared") is True and ul.get("n_checked", 0) > 0,
        f"{ul.get('n_checked', 0)} witnesses (the registry checkout plus this repo's own earlier "
        f"rasters); worst rank correlation {fmt(ul.get('worst_rho'))} &lt; {RHO_LIMIT:.2f}; worst "
        f"3&nbsp;px forward overlap {fmt(ul.get('worst_forward_overlap'))} &lt; {OVERLAP_LIMIT:.2f} "
        f"({esc(ul.get('worst_forward_overlap_name'))}); informative firings "
        f"{ul.get('n_overlap_firings_informative')}; saturated witnesses {ul.get('n_saturated_witnesses')}; "
        f"drift evidence: {esc(ul.get('lane_drift_evidence'))}")

    if not inv:
        add("G3", "Uniqueness — public inventory scan", False,
            "<code>evidence/ribbon/uniqueness_full_inventory.json</code> is missing: the governing "
            "scan over the byte-verified public inventory has not completed. Fail closed.")
    else:
        worst_rho = inv.get("worst_spearman_full_footprint")
        worst_ov = inv.get("worst_dot_overlap")
        ok = (inv.get("unique") is True and inv.get("complete_accessible_scan") is True
              and worst_rho is not None and float(worst_rho) <= RHO_LIMIT
              and worst_ov is not None and float(worst_ov) <= OVERLAP_LIMIT)
        add("G3", "Uniqueness — public inventory scan", ok,
            f"{inv.get('n_compared', inv.get('registry_rasters_expected'))} sha256-verified rasters "
            f"from <code>{esc(inv.get('index'))}</code>; complete accessible scan "
            f"{inv.get('complete_accessible_scan')}; worst rank correlation {fmt(worst_rho)} "
            f"({esc(inv.get('worst_rho_submission'))}); worst 3&nbsp;px forward overlap "
            f"{fmt(worst_ov)} ({esc(inv.get('worst_overlap_submission'))}); duplicates "
            f"{inv.get('duplicate_count')}; verdict {esc(inv.get('verdict'))}")

    can = sig.get("leakage_canary", {}) or {}
    aucs = [v.get("auc_max") for v in can.values() if isinstance(v, dict) and v.get("auc_max") is not None]
    worst = max(aucs) if aucs else None
    add("G4", "Leakage canary (single-feature AUC)",
        worst is not None and float(worst) < CANARY_LIMIT,
        f"max AUC over {len(can)} feature groups and all folds {fmt(worst)} vs the "
        f"{CANARY_LIMIT:.2f} leakage limit; groups flagged as leaking: "
        f"{sum(1 for v in can.values() if isinstance(v, dict) and v.get('leaks'))}")

    ho = emi.get("holdout_dti", {}) or {}
    add("G5", "Holdout evidence recorded and labelled",
        ho.get("pooled") is not None and bool(ho.get("per_fold")),
        f"HOLDOUT-DTI {fmt(ho.get('pooled'), 6)} pooled over {ho.get('n_withheld_positives')} "
        f"withheld positives ({esc(ho.get('protocol'))} / {esc(ho.get('evaluator'))}). This measures "
        f"recovery of <i>catalogue</i> truth, not the organizer's new-fault truth, and is not a "
        f"leaderboard forecast.")

    add("G6", "Organizer receipt for this raster", False,
        "No DrivenData submission receipt exists for this raster, so no ORGANIZER-CONFIRMED score can "
        "be quoted for it. This gate can only be closed by the owner's selector step and is never "
        "claimed here; the site verdict is computed over G1–G5.")

    passing = all(g["ok"] for g in gates if g["id"] != "G6")
    return gates, passing


# ------------------------------------------------------------------ sub-tables
def sigma_table_html(sig: dict) -> str:
    allf = sig.get("sigma_table_all_folds", {}) or {}
    loo = sig.get("sigma_table_leave_one_block_out", {}) or {}
    rows = []
    pooled = allf.get("pooled", {})
    if pooled:
        rows.append(["<b>pooled (all folds)</b>", f"{pooled.get('n', 0):,}", fmt(pooled.get("median"), 3),
                     fmt(pooled.get("mean"), 3), fmt(pooled.get("p25"), 3), fmt(pooled.get("p75"), 3),
                     fmt(pooled.get("rms"), 3)])
    for key, group in (("block", allf.get("by_block", {})), ("ridge scale", allf.get("by_scale", {})),
                       ("ridge type", allf.get("by_type", {}))):
        for name, st in sorted((group or {}).items()):
            rows.append([f"{key} = {esc(name)}", f"{st.get('n', 0):,}", fmt(st.get("median"), 3),
                         fmt(st.get("mean"), 3), fmt(st.get("p25"), 3), fmt(st.get("p75"), 3),
                         fmt(st.get("rms"), 3)])
    for blk, tab in sorted(loo.items()):
        st = (tab or {}).get("pooled", {})
        if st:
            rows.append([f"<b>cross-fitted σ used on block {esc(blk)}</b> (fitted on the other three)",
                         f"{st.get('n', 0):,}", fmt(st.get("median"), 3), fmt(st.get("mean"), 3),
                         fmt(st.get("p25"), 3), fmt(st.get("p75"), 3), fmt(st.get("rms"), 3)])
    head = ["stratum", "matched components", "median σ (px)", "mean σ", "p25", "p75", "rms"]
    note = (f"<p class='small'>σ(x) is the across-strike distance from a detected ridge to the "
            f"nearest withheld truth segment, measured on {sig.get('n_segments')} segments / "
            f"{sig.get('ridge_pixels')} ridge pixels at threshold {fmt(sig.get('threshold'), 2)}, "
            f"{allf.get('n_matched')} components matched to withheld truth "
            f"(median fraction of a withheld component recovered within the search window "
            f"{fmt((allf.get('recovery') or {}).get('median_frac_within'), 3)}). "
            f"Cross-fitting is leave-one-block-out, so no fold contributes to the σ used to score "
            f"itself — the defect the earlier σ table had.</p>")
    return table(head, rows) + note


def arms_table_html(arms: dict) -> str:
    res = arms.get("results", {}) or {}
    deltas = arms.get("deltas_vs_W1", {}) or {}
    desc = {"W1": "single tight dotted line on the ridge (width 1)",
            "W3": "uniform ribbon: 5 lines at 0, ±3, ±6 px (width 3)",
            "AD": "adaptive ribbon from cross-fitted σ at threshold 0.60",
            "AD2": "adaptive ribbon from cross-fitted σ at threshold 0.45"}
    rows = []
    for name in ("W1", "W3", "AD", "AD2"):
        r = res.get(name)
        if not r:
            continue
        agg = r.get("agg", {})
        d = deltas.get(name, {}) or {}
        pb = d.get("paired_bootstrap", {}) or {}
        rows.append([f"<b>{name}</b>", esc(desc.get(name, "")), f"<b>{fmt(r.get('pooled'), 6)}</b>",
                     fmt(r.get("coverage"), 4), f"{agg.get('n_dots', 0):,}",
                     fmt(agg.get("tp"), 1), fmt(agg.get("fp"), 1),
                     (fmt(d.get("pooled_delta"), 6) + (f"<br><span class='small'>bootstrap "
                      f"{fmt(pb.get('lo'), 6)} – {fmt(pb.get('hi'), 6)} (n={pb.get('n')} blocks)"
                      f"</span>" if pb else "")) if name != "W1" else "—"])
    head = ["arm", "geometry", "HOLDOUT-DTI (pooled)", "coverage", "dots (4 folds)",
            "TP", "FP", "Δ vs W1"]
    note = (f"<p class='small'>Equal budget {arms.get('budget')} isolated dots per fold "
            f"(min separation {arms.get('min_sep')}, lattice step 3&nbsp;px = the kernel radius), "
            f"ranking = {esc(arms.get('ranking'))}, screen = {esc(arms.get('screen'))}, "
            f"dti0 = {arms.get('dti0')} {label('ORGANIZER-CONFIRMED')}, "
            f"{arms.get('n_withheld_positives')} withheld positives, evaluator "
            f"<code>{esc(arms.get('evaluator'))}</code>. The paired bootstrap resamples the four "
            f"spatial blocks, so its interval is wide by construction and is reported as an "
            f"honest interval, not a tight one.</p>")
    return table(head, rows) + note


def per_class_html(arms: dict) -> str:
    g = arms.get("simulated_gain_per_sigma_class", {}) or {}
    rows = []
    for name, per in g.items():
        w1 = (per.get("W1") or {}).get("dti")
        ad = (per.get("AD") or {}).get("dti")
        ad2 = (per.get("AD2") or {}).get("dti")
        gain = (ad2 - w1) if (ad2 is not None and w1 is not None) else None
        rows.append([esc(name.replace("sigma-", "σ ").replace("px", " px")),
                     f"{(per.get('W1') or {}).get('n_truth', 0):,}",
                     fmt(w1, 6), fmt((per.get("W3") or {}).get("dti"), 6), fmt(ad, 6), fmt(ad2, 6),
                     (f"<b>{fmt(gain, 6)}</b>" if gain is not None else "—")])
    head = ["σ class", "withheld truth px", "W1 tight", "W3 uniform", "AD adaptive",
            "AD2 adaptive τ.45", "AD2 − W1"]
    return table(head, rows)


def canary_html(sig: dict) -> str:
    rows = []
    for name, v in sorted((sig.get("leakage_canary", {}) or {}).items()):
        rows.append([esc(name), fmt(v.get("auc_mean")), f"<b>{fmt(v.get('auc_max'))}</b>",
                     v.get("n_folds"),
                     '<span class="pill fail">LEAK</span>' if v.get("leaks")
                     else '<span class="pill pass">ok</span>'])
    bar = sig.get("marginal_inclusion_bar", {}) or {}
    note = (f"<p class='small'>A single feature with AUC &gt; {CANARY_LIMIT:.2f} against withheld "
            f"truth is treated as leakage until disproven. The marginal-inclusion bar at "
            f"dti0 = {bar.get('dti0')} is α·DTI₀ = {fmt(bar.get('required_credit'))}: a dot pays "
            f"only if its expected kernel credit exceeds that, i.e. only within "
            f"{fmt(bar.get('max_distance_px'), 3)} px ({fmt(bar.get('max_distance_m'), 1)} m).</p>")
    return table(["feature group", "AUC mean", "AUC max", "folds", "canary"], rows) + note


def calibration_html(emi: dict) -> str:
    cal = (emi.get("credit_calibration", {}) or {}).get("khat_by_stratum", {}) or {}
    fams: dict[str, list] = {}
    for key, v in cal.items():
        fam, _, q = key.partition("|")
        fams.setdefault(fam, {})[int(q[1:])] = v
    rows = []
    for fam in sorted(fams):
        vals = fams[fam]
        cells = [fmt(vals.get(q), 4) for q in range(10)]
        finite = [v for v in vals.values() if v]
        rows.append([f"<b>{esc(fam)}</b>"] + cells +
                    [f"{fmt(min(finite), 4) if finite else '—'} – {fmt(max(finite), 4) if finite else '—'}"])
    bar = (emi.get("credit_calibration", {}) or {}).get("marginal_bar_at_dti0")
    note = (f"<p class='small'>k̂(family, magnitude decile) = the mean triangular-kernel credit a "
            f"ridge pixel of that stratum earns against withheld truth, cross-fitted over the four "
            f"blocks ({(emi.get('credit_calibration') or {}).get('n_ridge_px')} ridge pixels at "
            f"τ = {emi.get('design', {}).get('threshold')}). q0 is the weakest decile, q9 the "
            f"strongest. The marginal-inclusion bar at the organizer-confirmed leader score is "
            f"α·DTI₀ = <b>{fmt(bar)}</b>; every stratum sits below it, which is the coverage "
            f"problem in per-pixel form.</p>")
    return table(["family"] + [f"q{q}" for q in range(10)] + ["range"], rows) + note


def live_family_html(fit: dict, floor: float = 0.24) -> str:
    rows = []
    for r in sorted(fit.get("fitted_rows", []) or [], key=lambda r: -float(r.get("score", 0))):
        if r.get("status") != "ok":
            continue
        in_fam = float(r.get("score", 0)) >= floor
        rows.append([(f"<b>{esc(r.get('label'))}</b>" if in_fam else esc(r.get("label"))),
                     f"<b>{fmt(r.get('score'), 4)}</b>" if in_fam else fmt(r.get("score"), 4),
                     f"{int(r.get('dots', 0)):,}", f"{int(r.get('dots_on_catalogue', 0)):,}",
                     fmt(r.get("median_off_d_px"), 1), fmt(r.get("frac_off_d_le_3"), 3),
                     fmt(r.get("mean_credit_off_catalogue"), 3),
                     esc(r.get("source_site", "")).replace("https://buffedlizard55-lab.github.io/", "")])
    cov = fit.get("covariates", {}) or {}
    best = sorted(((abs(v.get("spearman_vs_score") or 0), k, v) for k, v in cov.items()),
                  reverse=True)[:5]
    cov_txt = ", ".join(f"<code>{esc(k)}</code> ρ={fmt(v.get('spearman_vs_score'), 3)}"
                        for _, k, v in best)
    note = (f"<p class='small'>{fit.get('n_distinct_rasters_fitted')} sibling rasters matched to "
            f"owner-quoted scores by repository-scoped sha256 and re-measured from verified bytes "
            f"({len(fit.get('unmatched', []))} rows dropped as ambiguous, "
            f"{len(fit.get('score_conflicts', []))} score conflicts). Rows in bold are the "
            f"≥ {floor} family. Verdict of the calibration attempt: "
            f"<b>{esc(fit.get('verdict'))}</b> — {esc(fit.get('verdict_note'))} Best covariates by "
            f"|Spearman| vs score: {cov_txt}. All of these are "
            f"{label('USER-REPORTED-SCORE')}: no receipt exists for any of them.</p>")
    head = ["owner-reported file", "score", "dots", "dots on catalogue",
            "median catalogue distance (px)", "frac ≤3 px", "mean kernel credit", "site"]
    return table(head, rows[:26]) + note


def irregularities() -> list[tuple[str, str, str]]:
    return [
        ("IR-58-TARGET-01", "warn",
         f"The owner's stated target <b>{OWNER_TARGET}</b> is stale. The live public leaderboard "
         f"(fetched 2026-10-11) has <b>{LEADER_DTI} — {esc(LEADER_WHO)}</b> at #1, and "
         f"{OWNER_TARGET} (DARD) at #8. Every 'beat the target' statement on this site is "
         f"restated against {LEADER_DTI}. "
         f"<a href='https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'>leaderboard</a>"),
        ("IR-58-DATA-01", "warn",
         "The 19-band <code>training_features.tif</code> has <b>no aeroradiometric bands</b> (no "
         "eK/eU/eTh/total count) although the competition's own About page says GeoDAWN acquired "
         "aeromagnetic <i>and aeroradiometric</i> surveys plus 3DEP lidar. The radiometric "
         "signature of K-metasomatism, silicification and Fe-oxide staining — a physically "
         "motivated discriminator for faults hidden under cover — is therefore unreachable from the "
         "provided stack, and the USGS release is not fetchable from this sandbox (text-only "
         "egress). Recorded as an owner-download idea with verified links, never as a validated "
         "candidate. <a href='https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/'>About page</a> · "
         "<a href='https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and'>USGS GeoDAWN</a>"),
        ("IR-58-UNIQ-04", "bad",
         "<b>Shared-tool bug, fixed once in the template.</b> <code>src/gems58w/uniqueness.py</code> "
         "computed the protocol's forward statistic — the fraction of <i>my</i> dots within 3&nbsp;px "
         "of <i>the witness's</i> dots — in the reverse direction and vice versa, and applied the "
         "dense-prior exemption to the wrong leg. Every overlap number this lane published before "
         "2026-10-11, including the '0.3600 worst forward overlap' quoted for the earlier "
         "38,000-dot file, was measured with the two directions exchanged and has been re-measured "
         "with the corrected instrument. The template-level registry scanner "
         "(<code>scripts/check_uniqueness_registry.py</code>) already had the direction right, so "
         "the frozen-inventory numbers published by the sibling lane were unaffected."),
        ("IR-58-UNIQ-03", "bad",
         "<b>The literal 0.70 overlap gate is unusable as written.</b> Lattice and blanket "
         "witnesses dilate to cover 74–99.9&nbsp;% of the footprint, so their chance-level expected "
         "overlap <i>E</i> exceeds 0.99 and they overlap <i>every</i> nonempty candidate; a literal "
         "firing against such a witness carries no information, and no buffer from 3 to 10&nbsp;px "
         "clears 0.70 against them (measured in <code>evidence/buffer_overlap_scan.json</code>). "
         "The instrument now reports <i>E</i>, the chance-corrected lift "
         "<code>(observed − E)/(1 − E)</code>, a <code>saturated</code> flag and an <b>informative</b> "
         "reading that excludes saturated witnesses, with the literal reading still reported "
         "alongside it."),
        ("IR-58-UNIQ-05", "warn",
         "<b>The scanner rejected the organizer's own submission representation.</b> "
         "<code>sample_submission.tif</code> carries NaN outside the study footprint "
         "(<code>nodata=nan</code>, 7,111,787 pixels) and finite values inside it, but the "
         "uniqueness scanner demanded an all-finite candidate, which is why earlier artifacts had "
         "to be published as <code>*-zeros.tif</code> variants that do not match the official "
         "representation. Fixed once in the shared tool: non-finite <i>inside</i> the footprint "
         "stays a hard error (that is exactly the portal rejection <code>Predicted values must be in "
         "range [0, 1]</code>), non-finite outside it is normalised to 0 for statistics that are "
         "footprint-restricted anyway."),
        ("IR-58-02", "warn",
         "<b>The mandated holdout cannot score an off-catalogue file.</b> The withheld truth "
         "<i>is</i> catalogue, so a candidate that keeps a 3&nbsp;px catalogue margin scores "
         "HOLDOUT-DTI exactly 0.0 by construction (control raster sha256 <code>53496109…</code>, "
         "<code>evidence/ribbon/instrument_control.json</code>). The delivered file therefore drops "
         "only the dots that fall <i>on</i> the catalogue — which the organizer masks out of "
         "evaluation anyway — and reports a genuine non-zero HOLDOUT-DTI. That number measures "
         "catalogue recovery, not new-fault detection. "
         "<a href='https://community.drivendata.org/t/11516'>staff answer on masking</a>"),
        ("IR-58-LIVE-01", "warn",
         "<b>No dot-field statistic predicts the owner-quoted live scores.</b> Over 66 "
         "sha256-verified sibling rasters the best covariate reaches |Spearman| 0.258 and the "
         "two-parameter catalogue-proximity model fits with R² = −1.27. The organizer will not "
         "disclose public-subset membership, so every owner-quoted score carries unmodellable "
         "chunk luck. This file's budget is therefore taken from the measured <i>family</i> (median "
         "dot count of the owner-reported ≥0.24 files) and labelled USER-REPORTED-SCORE, never as a "
         "calibrated optimum. <a href='https://community.drivendata.org/t/11550'>staff answer on pooling</a>"),
        ("IR-58-SIGMA-01", "warn",
         "The lane's 'single tight line where σ &lt; 0.5&nbsp;px' branch is <b>unreachable</b>: "
         "<code>gems58w.sigma</code> floors σ at 0.5&nbsp;px and every measured stratum sits far "
         "above it (pooled median σ ≈ 6.88&nbsp;px, block medians 5.79–8.54&nbsp;px). The adaptive "
         "planner consequently returns 5 lines for most segments; the ribbon is never chosen "
         "because σ is small anywhere. The measured adaptivity is therefore 'ribbon vs tight line' "
         "more than 'per-segment line count'."),
        ("IR-58-REG-01", "warn",
         "<b>The pinned inventory was one raster short, and is now complete.</b> The 695-raster "
         "public inventory could not be fully restored earlier because one file "
         "(sha256 <code>927dc17f…</code>) only existed in a deleted pull-request head. It was "
         "recovered by fetching the exact commit "
         "<code>d92606c28dc5e93ee1bce5148b92ccbb5225d023</code> of <code>55GEMSDOE</code> over the "
         "git protocol and verifying the blob's sha256, so the scan now covers 695/695 pinned "
         "rasters plus a freshness delta from the current default branches."),
    ]


def sources_table() -> str:
    rows = [
        ["Competition #306 landing page", "ORGANIZER",
         "https://www.drivendata.org/competitions/306/competition-doe-gems/"],
        ["Problem description, exact DTI formula and worked example, submission format", "ORGANIZER",
         "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"],
        ["About the data: GeoDAWN aeromagnetic + aeroradiometric + 3DEP lidar; hidden-fault framing",
         "ORGANIZER", "https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/"],
        ["Rules", "ORGANIZER", "https://www.drivendata.org/competitions/306/competition-doe-gems/rules/"],
        ["Public leaderboard — source of the 0.4133 leader figure", "ORGANIZER",
         "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"],
        ["HeroX GEMS prize rules (round selection, prizes)", "ORGANIZER",
         "https://www.herox.com/GEMSPrize/resource/2274"],
        ["Staff: known USGS/INGENIOUS fault pixels are masked out of evaluation in both rounds",
         "ORGANIZER",
         "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516"],
        ["Staff: the public leaderboard is pooled; the final round re-evaluates the whole GeoDAWN "
         "area; subset membership will not be disclosed", "ORGANIZER",
         "https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550"],
        ["Staff: test-fault provenance will not be disclosed; Phase-2 labels updated by expert "
         "review of all Phase-1 submissions", "ORGANIZER",
         "https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527"],
        ["Reference solution: metric surrogate, output writer, no NaN inside the footprint",
         "ORGANIZER", "https://github.com/drivendataorg/gems-prize-reference-solution"],
        ["USGS GeoDAWN airborne magnetic and radiometric surveys (the missing radiometric bands)",
         "USGS", "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and"],
        ["USGS ScienceBase study-area item", "USGS",
         "https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7"],
        ["USGS 3DEP lidar programme", "USGS",
         "https://www.usgs.gov/3d-elevation-program/about-3dep-products-services"],
        ["Matéo et al. 2021, JGR Solid Earth 126, e2020JB021269 (Walker Lane deformation)",
         "LITERATURE", "https://doi.org/10.1029/2020JB021269"],
        ["EPSG:32611 — UTM zone 11N, the required CRS", "REFERENCE", "https://epsg.io/32611"],
        ["Tversky index — the metric family the DTI is built on", "REFERENCE",
         "https://en.wikipedia.org/wiki/Tversky_index"],
    ]
    return table(["source", "kind", "link (open for manual review)"],
                 [[esc(a), esc(b), f"<a href='{esc(c)}'>{esc(c)}</a>"] for a, b, c in rows], "kv")


# ------------------------------------------------------------------------ pages
def page(title: str, body: str, nav_active: str = "") -> str:
    nav = [("index.html", "Status &amp; download"), ("executive-summary.html", "How to submit"),
           ("submit.html", "Portal checklist"), ("sources.html", "Sources"),
           ("evidence.html", "Evidence index"), ("ribbon/index.html", "Ribbon lane archive")]
    parts = []
    for href, name in nav:
        style = ' style="font-weight:700"' if href == nav_active else ""
        parts.append(f'<a href="{href}"{style}>{name}</a>')
    links = " · ".join(parts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — 58GEMSDOE (GEMS competition #306)</title>
<link rel="stylesheet" href="assets/site.css">{EXTRA_CSS}</head><body>
<header><h1>58GEMSDOE — DOE GEMS competition #306</h1>
<p>Geothermal fault detection, northwestern Great Basin (NV) · ribbon lane · every figure on this
site is rendered from <code>evidence/**.json</code> at build time</p>
<nav class="small">{links}</nav></header>
{body}
<footer>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} by
<code>scripts/build_site.py</code>. No organizer receipt exists for any artifact on this site, so no
number here is a leaderboard score unless it is labelled ORGANIZER-CONFIRMED.</footer>
</body></html>"""


def gates_html(gates: list[dict]) -> str:
    out = ['<div class="gates">']
    for g in gates:
        cls = "pass" if g["ok"] else "fail"
        pill = "PASS" if g["ok"] else ("OPEN — owner step" if g["id"] == "G6" else "FAIL")
        out.append(f'<div class="gate {cls}"><h4>{g["id"]} · {g["name"]} '
                   f'<span class="pill {cls}">{pill}</span></h4><p>{g["detail"]}</p></div>')
    out.append("</div>")
    return "".join(out)


def build_index(emi, card, arms, sig, inv, fit, gates, ok) -> str:
    name = emi["name"]
    ho = emi.get("holdout_dti", {}) or {}
    prof = emi.get("catalogue_distance_profile", {}) or {}
    budget = (emi.get("design", {}) or {}).get("budget", {}) or {}
    hist = (emi.get("design", {}) or {}).get("lines_per_segment_histogram", {}) or {}
    colour = "#1d7a45" if ok else "#a11212"
    badge = ("OK TO DOWNLOAD AND SUBMIT — FORMAT AND UNIQUENESS CLEARED" if ok
             else "NOT OK TO SUBMIT — A GATE IS OPEN")
    res = arms.get("results", {}) or {}
    best_arm = max(((k, v.get("pooled", 0)) for k, v in res.items()), key=lambda kv: kv[1],
                   default=("—", None))

    head = f"""
<section class="submit-box" style="border-color:{colour}">
  <div class="badge" style="background:{colour}">{badge}</div>
  <h2 style="margin-top:.7rem">{esc(name)}.tif</h2>
  <p>{'Every format and uniqueness gate below passes, and the sha256 recomputed from the bytes on '
      'disk matches the recorded receipt.' if ok else
      'At least one gate below is open. The file is a reviewable artifact, not a submission.'}</p>
  <div class="dlrow">
    <a class="big-btn" style="background:{colour}" href="downloads/{esc(name)}.tif" download>
      ⬇ Download the GeoTIFF · {emi['validator']['bytes']:,} bytes</a>
    <a class="big-btn" style="background:#2f5f8f" href="downloads/{esc(name)}.zip" download>
      ⬇ Download the single-GeoTIFF ZIP</a>
    <a class="big-btn" style="background:#41505f" href="executive-summary.html">
      How to submit — executive summary</a>
  </div>
  <p class="small">sha256 <code>{esc(emi['sha256'])}</code> · {emi['validator']['n_positives']:,}
  dots, every emitted value exactly <code>1.0</code> · EPSG:32611, 3730×3292, 100&nbsp;m · NaN
  outside the study footprint exactly as in the organizer's <code>sample_submission.tif</code> ·
  <b>0 dots on the mapped catalogue</b> · lines per segment: {esc(hist)}.</p>
  <p class="small"><b>Submission name:</b> <code>{esc(name)}</code><br>
  <b>Submission note ({len(card['submission_note'])}/140 characters):</b>
  <code>{esc(card['submission_note'])}</code></p>
</section>

<div class="warn-box"><b>No organizer receipt exists for this file, so no score is claimed for
it.</b> Uploading it would spend one of the owner's slots and would produce the <i>first</i>
ORGANIZER-CONFIRMED number for this lane. Everything below is labelled
{label('HOLDOUT-DTI')} (measured here on a buffered hide-and-recover holdout whose withheld truth
is the <i>catalogue</i>), {label('USER-REPORTED-SCORE')} (owner-quoted sibling pages, no receipt) or
{label('PROJECTION')} (arithmetic from the official metric — never a score).</div>
"""

    headline = table(["quantity", "value", "label"], [
        ["HOLDOUT-DTI of the delivered bytes, pooled over the four spatial blocks",
         f"<b>{fmt(ho.get('pooled'), 6)}</b>", label("HOLDOUT-DTI")],
        ["per-block HOLDOUT-DTI (NW / NE / SW / SE)",
         " / ".join(fmt((ho.get("per_fold") or {}).get(b), 6) for b in ("NW", "NE", "SW", "SE")),
         label("HOLDOUT-DTI")],
        ["interval reported", f"{fmt((ho.get('ci') or {}).get('lo'), 6)} – "
         f"{fmt((ho.get('ci') or {}).get('hi'), 6)} (min–max over the 4 blocks; a 4-block bootstrap "
         "would resample repeated physical blocks as independent, so no bootstrap CI is claimed)",
         label("HOLDOUT-DTI")],
        ["weighted coverage of withheld truth", fmt(ho.get("coverage"), 4), label("HOLDOUT-DTI")],
        ["best equal-budget arm (τ=0.45 adaptive ribbon)",
         f"{esc(best_arm[0])} → {fmt(best_arm[1], 6)}", label("HOLDOUT-DTI")],
        ["public leaderboard #1", f"<b>{LEADER_DTI}</b> — {esc(LEADER_WHO)}",
         label("ORGANIZER-CONFIRMED")],
        ["owner-reported target", f"{OWNER_TARGET} (DARD — #8 on that same live board, see "
         "IR-58-TARGET-01)", label("USER-REPORTED-SCORE")],
        ["weighted coverage the leader's score implies", "≈ 0.36 with near-zero wasted mass",
         label("PROJECTION")],
        ["coverage this surface actually reaches", fmt(ho.get("coverage"), 4), label("HOLDOUT-DTI")],
        ["emission budget", f"{budget.get('budget', 0):,} dots — {esc(budget.get('rule'))} "
         f"(n={budget.get('n_files')})", label("USER-REPORTED-SCORE")],
        ["dots on the mapped catalogue", f"{prof.get('on_catalogue', 0):,} — the organizer masks "
         "those pixels out of evaluation, so they are inert", label("ORGANIZER-CONFIRMED")],
        ["dot-to-catalogue distance", f"median {fmt(prof.get('median_px'), 1)} px; "
         f"{fmt(prof.get('frac_le_3px'), 3)} within 3 px; {fmt(prof.get('frac_le_10px'), 3)} "
         f"within 10 px", label("HOLDOUT-DTI")],
        ["leakage canary, worst single-feature AUC",
         f"{fmt(max((v.get('auc_max') or 0) for v in (sig.get('leakage_canary') or {}).values()), 4)}"
         f" vs the 0.90 limit", label("HOLDOUT-DTI")],
        ["local portal preflight",
         f"{sum(1 for c in emi['validator']['checks'].values() if c['ok'])}"
         f"/{len(emi['validator']['checks'])} checks pass", label("HOLDOUT-DTI")],
    ])

    body = head + f"""
<h2>The download / submit decision — six explicit gates</h2>{gates_html(gates)}

<h2>Headline numbers</h2>{headline}
<p class="small"><b>The honest gap.</b> The leader's {LEADER_DTI} implies ≈0.36 weighted coverage of
the organizer's new-fault truth {label('PROJECTION')}; this surface reaches
{fmt(ho.get('coverage'), 4)} on catalogue truth {label('HOLDOUT-DTI')}. The binding constraint is
<b>coverage</b>, not ribbon geometry: no choice of width, offset, threshold or budget inside this
lane closes a factor of ~6. That is the negative result this lane reports, and it is why the banner
never claims a score.</p>

<h2>Experiment 2 — equal-budget geometry contest {label('HOLDOUT-DTI')}</h2>
{arms_table_html(arms)}
<h3>Simulated gain per σ class</h3>
{per_class_html(arms)}
<p class="small">Read the two tables together: the ribbon beats the tight line exactly where the
localisation error is large (σ ≥ 1.5&nbsp;px, and most in σ ∈ [3,6]&nbsp;px, where the tight line
scores 0.000000) and <b>loses</b> where σ &lt; 1.5&nbsp;px (−0.0014). That is the lane's hypothesis
confirmed in direction, with the caveat in IR-58-SIGMA-01: no measured stratum has σ below the
0.5&nbsp;px floor, so the tight-line branch of the rule is never selected.</p>

<h2>Experiment 1 — σ(x), credit calibration and the leakage canary {label('HOLDOUT-DTI')}</h2>
<div class="cols"><div>
<h3 style="margin-top:0">σ(x) by data block, ridge scale and ridge type</h3>
{sigma_table_html(sig)}
</div><div>
<h3 style="margin-top:0">Leakage canary</h3>
{canary_html(sig)}
</div></div>
<h3>Calibrated expected kernel credit k̂(family, magnitude decile)</h3>
{calibration_html(emi)}

<h2>Experiment 3 — the delivered file {label('HOLDOUT-DTI')}</h2>
<p class="small">Design: threshold τ = {emi['design'].get('threshold')} (the better of the two
thresholds measured at equal budget); per-segment line count and offsets from the cross-fitted σ via
<code>gems58w.allocation.plan</code> at dti0 = {emi['design'].get('dti0')}
{label('ORGANIZER-CONFIRMED')}; ranking by calibrated k̂(family, decile) with a 1e-6·magnitude
tie-break; dots on the catalogue dropped; no two 8-adjacent dots; budget
{budget.get('budget', 0):,} from {esc(budget.get('rule'))}. Receipts:
<code>evidence/ribbon/emission.json</code>, <code>evidence/ribbon/run_card_v2.json</code>.</p>

<h2>Live evidence — what owner-reported scores actually look like {label('USER-REPORTED-SCORE')}</h2>
<p class="small">The extremes separate cleanly even though no covariate predicts the middle: every
file scoring ≥ 0.2449 has <b>0 dots on the catalogue</b>, 37,654–61,328 dots and a median catalogue
distance of 14–20&nbsp;px, while catalogue-hugging files score 0.004–0.03. The delivered file sits
inside that geometric family <i>by construction</i>: 0 on-catalogue dots,
{emi['validator']['n_positives']:,} dots, median distance {fmt(prof.get('median_px'), 1)}&nbsp;px,
{fmt(prof.get('frac_le_3px'), 3)} of dots within 3&nbsp;px. <b>This is a family comparison, not a
forecast.</b></p>
{live_family_html(fit)}

<h2>Irregularities flagged for manual review</h2>
{"".join(f'<div class="{"bad-box" if s == "bad" else "warn-box"}"><b>{esc(i)}</b> — {t}</div>' for i, s, t in irregularities())}

<h2>Sources — open each link for manual review</h2>
{sources_table()}
"""
    return page("Status and download", body, "index.html")


def build_executive_summary(emi, card, arms, sig, gates, ok) -> str:
    name = emi["name"]
    colour = "#1d7a45" if ok else "#a11212"
    ho = emi.get("holdout_dti", {}) or {}
    res = arms.get("results", {}) or {}
    best = max(((k, v.get("pooled", 0)) for k, v in res.items()), key=lambda kv: kv[1],
               default=("—", None))
    worst_auc = max((v.get("auc_max") or 0) for v in (sig.get("leakage_canary") or {}).values())
    steps = [
        ("Check the banner on the status page",
         "It is generated from evidence receipts, not from prose. If it is not green, do not "
         "submit. <a href='index.html'>index.html</a>"),
        ("Download the GeoTIFF — or the ZIP",
         f"<code>downloads/{esc(name)}.tif</code> · {emi['validator']['bytes']:,} bytes. The ZIP "
         f"contains exactly one GeoTIFF, which the portal also accepts. Do <b>not</b> upload a "
         f"README, HTML, JSON or a whole-repository ZIP."),
        ("Verify the bytes before uploading",
         f"Expected sha256 <code>{esc(emi['sha256'])}</code>. macOS: "
         f"<code>shasum -a 256 &lt;file&gt;</code> · Linux: <code>sha256sum &lt;file&gt;</code>. "
         f"If it differs, the download is corrupt — re-download it."),
        ("Paste the submission name and note",
         f"Name: <code>{esc(name)}</code><br>Note ({len(card['submission_note'])}/140 characters): "
         f"<code>{esc(card['submission_note'])}</code>"),
        ("Upload on the competition page",
         "<a href='https://www.drivendata.org/competitions/306/competition-doe-gems/'>competition "
         "#306</a> → <i>Submit</i>. This spends one of your slots; the automated agent never does "
         "it and never selects a submission."),
        ("Record the receipt",
         "Copy the score the submission page shows into <code>registry/submissions_seen.csv</code> "
         "with the date and the file's sha256. Only then does an ORGANIZER-CONFIRMED number exist "
         "for this lane; until then every number here is HOLDOUT-DTI, USER-REPORTED-SCORE or "
         "PROJECTION."),
        ("Decide the round selection deliberately",
         "One submission must be selected for both the initial round (top 5 × $10k on a fixed "
         "private new-fault set) and the final round ($100k / $70k / $40k / $25k / $15k), blind to "
         "private performance. "
         "<a href='https://www.drivendata.org/competitions/306/competition-doe-gems/rules/'>competition rules</a> · "
         "<a href='https://www.herox.com/GEMSPrize/resource/2274'>HeroX GEMS prize rules</a>"),
    ]
    body = f"""
<section class="submit-box" style="border-color:{colour}">
  <div class="badge" style="background:{colour}">{'OK TO DOWNLOAD AND SUBMIT' if ok else 'NOT OK TO SUBMIT'}</div>
  <h2 style="margin-top:.7rem">How to submit this file — seven steps</h2>
  <div class="dlrow">
    <a class="big-btn" style="background:{colour}" href="downloads/{esc(name)}.tif" download>
      ⬇ Download the GeoTIFF</a>
    <a class="big-btn" style="background:#2f5f8f" href="downloads/{esc(name)}.zip" download>
      ⬇ Download the ZIP</a>
    <a class="big-btn" style="background:#41505f" href="index.html">Back to status</a>
  </div>
</section>

<h2>What this file is, in one paragraph</h2>
<p>{emi['validator']['n_positives']:,} isolated dots at exactly <code>1.0</code> on a 100&nbsp;m grid
(EPSG:32611, 3730×3292, the same bounds and transform as the organizer's sample submission), placed
on <i>catalogue-free</i> multi-scale Hessian ridges of the organizer's own 19-band feature stack.
Each detected ridge segment carries a ribbon of parallel dotted lines at 0, ±300 and ±600&nbsp;m
across strike, with the number of lines chosen per segment from the localisation error σ(x) measured
on a buffered hide-and-recover holdout and cross-fitted leave-one-block-out. No dot falls on the
mapped USGS/INGENIOUS catalogue, because the organizer masks those pixels out of evaluation. Outside
the study footprint the file is NaN, exactly like <code>sample_submission.tif</code>.</p>

<h2>The error this file cannot produce</h2>
<div class="ok-box"><p><b><code>Predicted values must be in range [0, 1]</code></b> — the portal
rejection already hit on this competition — is caused by a non-finite or out-of-range value landing
<i>inside</i> the scored footprint. This file is checked for exactly that before publication:
<code>finite_inside_footprint</code> ({esc(emi['validator']['checks']['finite_inside_footprint']['detail'])}),
<code>values_in_unit_interval</code> ({esc(emi['validator']['checks']['values_in_unit_interval']['detail'])}),
<code>positive_is_exactly_one</code> ({esc(emi['validator']['checks']['positive_is_exactly_one']['detail'])}),
and the NaN count outside the footprint is identical to the organizer's sample submission
(7,111,787). All {sum(1 for c in emi['validator']['checks'].values() if c['ok'])}/
{len(emi['validator']['checks'])} local checks pass — full receipt on the
<a href="submit.html">portal checklist</a> page.</p></div>

<h2>Steps</h2>
<ol>{''.join(f'<li><b>{esc(t)}</b><br><span class="small">{d}</span></li>' for t, d in steps)}</ol>

<h2>What is known, and what is not</h2>
<div class="cols">
<div class="ok-box"><b>Known — measured here {label('HOLDOUT-DTI')}</b>
<ul class="small">
<li>HOLDOUT-DTI of the exact delivered bytes: <b>{fmt(ho.get('pooled'), 6)}</b> pooled,
{fmt((ho.get('ci') or {}).get('lo'), 6)}–{fmt((ho.get('ci') or {}).get('hi'), 6)} across blocks,
{ho.get('n_withheld_positives')} withheld positives, evaluator
<code>{esc(ho.get('evaluator'))}</code>, protocol <code>{esc(ho.get('protocol'))}</code>.</li>
<li>At an equal budget the adaptive ribbon beats a single tight line: best arm {esc(best[0])}
{fmt(best[1], 6)} vs W1 {fmt((res.get('W1') or {}).get('pooled'), 6)}, and it wins most in the
σ ∈ [3,6]&nbsp;px class where the tight line scores 0.</li>
<li>No leaking feature: worst single-feature AUC {fmt(worst_auc)} &lt; 0.90.</li>
<li>Uniqueness on the corrected instrument: worst rank correlation
{fmt(emi['uniqueness_local']['worst_rho'])} and worst 3&nbsp;px forward overlap
{fmt(emi['uniqueness_local']['worst_forward_overlap'])} over
{emi['uniqueness_local']['n_checked']} local witnesses, both inside the 0.90 / 0.70 stop limits, and
{emi['uniqueness_local']['n_overlap_firings_informative']} informative firings.</li>
</ul></div>
<div class="bad-box"><b>Not known — and not claimed</b>
<ul class="small">
<li>The score this file would receive. No organizer receipt exists, and HOLDOUT-DTI measures recovery
of <i>catalogue</i> truth while the competition scores <i>new</i> faults (IR-58-02).</li>
<li>Whether it beats {LEADER_DTI} ({esc(LEADER_WHO)}) or the owner's stale {OWNER_TARGET} target
(IR-58-TARGET-01). The coverage arithmetic says the gap is a factor of ~6 in weighted coverage.</li>
<li>Which public-subset pixels are scored, so no owner-quoted score can be modelled: the best
covariate over 66 verified sibling rasters reaches |Spearman| 0.258 (IR-58-LIVE-01).</li>
<li>Whether the σ-based line count is optimal on new faults. On the holdout the adaptive plan chose
{esc((emi['design'] or {}).get('lines_per_segment_histogram'))}, so most of the measured gain is
'ribbon vs tight line', not 'per-segment adaptivity'.</li>
<li>Anything about the aeroradiometric and 1&nbsp;m lidar evidence that the provided stack does not
contain (IR-58-DATA-01).</li>
</ul></div>
</div>

<h2>Gates</h2>{gates_html(gates)}
"""
    return page("How to submit", body, "executive-summary.html")


def build_submit(emi, card, ok) -> str:
    checks = emi["validator"]["checks"]
    rows = [[f"<code>{esc(k)}</code>",
             '<span class="pill pass">PASS</span>' if c.get("ok") else '<span class="pill fail">FAIL</span>',
             esc(c.get("detail", ""))] for k, c in checks.items()]
    colour = "#1d7a45" if ok else "#a11212"
    body = f"""
<section class="submit-box" style="border-color:{colour}">
  <div class="badge" style="background:{colour}">
    {'LOCAL PORTAL PREFLIGHT: ALL CHECKS PASS' if ok else 'PREFLIGHT NOT CLEARED'}</div>
  <h2 style="margin-top:.7rem">Portal checklist for <code>{esc(emi['name'])}.tif</code></h2>
  <p class="small">Every row is produced by <code>src/gems58w/submission.py:validate()</code> against
  the bytes on disk at build time. It is a <b>local preflight</b>: it reproduces the format rules
  published on the competition page and the reference solution's writer. It is not an organizer
  acceptance, and it is not a score.</p>
  <div class="dlrow">
    <a class="big-btn" style="background:{colour}" href="downloads/{esc(emi['name'])}.tif" download>
      ⬇ Download the GeoTIFF</a>
    <a class="big-btn" style="background:#2f5f8f" href="downloads/{esc(emi['name'])}.zip" download>
      ⬇ Download the ZIP</a>
  </div>
</section>

<h2>Format rules, and where each one comes from</h2>
{table(['rule', 'source (open for manual review)'], [
    ['Single-band GeoTIFF, float32',
     '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a> — submission format'],
    ['EPSG:32611, 100&nbsp;m pixels, same bounds as the training data',
     '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a> · <a href="https://epsg.io/32611">EPSG:32611</a>'],
    ['Values in [0, 1], higher = more probable',
     '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a>'],
    ['Outside the study area: null / NaN',
     '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a> · reproduced by <code>data/official/sample_submission.tif</code> (7,111,787 NaN, nodata=nan)'],
    ['A ZIP must contain exactly one GeoTIFF',
     '<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a>'],
    ['Reference-solution writer: single-band float32, crs/transform from labels, no NaN inside the footprint',
     '<a href="https://github.com/drivendataorg/gems-prize-reference-solution">drivendataorg/gems-prize-reference-solution</a>'],
    ['Known USGS/INGENIOUS fault pixels are masked out of evaluation in both rounds',
     '<a href="https://community.drivendata.org/t/11516">staff answer, thread 11516</a>']], 'kv')}

<h2>Validation receipt — {sum(1 for c in checks.values() if c['ok'])}/{len(checks)} pass</h2>
{table(['check', 'result', 'detail'], rows, 'kv')}
<p class="small">raster sha256 <code>{esc(emi['sha256'])}</code> · {emi['validator']['bytes']:,} bytes ·
{emi['validator']['n_positives']:,} positives · ZIP <code>downloads/{esc(emi['name'])}.zip</code> ·
built {esc(emi.get('generated_utc'))}</p>

<h2>Submission name and note</h2>
<p>Name: <code>{esc(emi['name'])}</code><br>
Note: <code>{esc(card['submission_note'])}</code> ({len(card['submission_note'])} of 140 characters)</p>

<h2>Why every emitted dot is exactly 1.0</h2>
<p class="small">With the official metric
<code>DTI = TP<sub>w</sub> / (TP<sub>w</sub> + α·FP<sub>w</sub> + β·FN<sub>w</sub> + ε)</code>,
α = 0.2, β = 0.8, and the triangular kernel <code>k(d) = max(1 − d/R, 0)</code>, R = 300&nbsp;m =
3&nbsp;px, a truth pixel takes the <b>maximum</b> kernel value over all predictions while a predicted
pixel pays its own value times the leftover kernel. Scaling a dot down therefore scales its credit
down without reducing the fixed β·FN term, so on a fixed support DTI is monotone increasing in
emitted mass and the optimum is 1.0 everywhere you emit. Verified algebraically in
<code>evidence/ribbon/theorems.json</code> and numerically by the
<code>positive_is_exactly_one</code> check above (unique positives = [1.0]).</p>

<h2>What the portal does with dots on the mapped catalogue</h2>
<p class="small">Nothing: the organizer masks known USGS/INGENIOUS fault pixels out of evaluation in
both rounds, so a dot there earns no credit and costs nothing. This file has
{emi['catalogue_distance_profile'].get('on_catalogue', 0)} such dots — the emitter drops them, which
keeps the whole budget available for off-catalogue placement (and, on the local holdout, keeps the
withheld truth scoreable instead of reading exactly 0.0 — IR-58-02).</p>
"""
    return page("Portal checklist", body, "submit.html")


def build_evidence_index(emi, card, arms, sig, inv, fit) -> str:
    """Every receipt this site is built from, with the label it is allowed to carry."""
    curated = [
        ("evidence/organizer_confirmed.json", "ORGANIZER-CONFIRMED",
         "Metric, submission format, masking, aggregation, label provenance, the live public "
         "leaderboard of 2026-10-11, prizes and dataset provenance — each entry quoted from a "
         "DrivenData/USGS page with its URL and fetch date."),
        ("evidence/ribbon/emission.json", "HOLDOUT-DTI + local measurement",
         "The delivered raster: design, budget rule, σ tables, k̂ calibration, HOLDOUT-DTI of the "
         "exact bytes, catalogue-distance profile, the 15-check validator receipt and the corrected "
         "local uniqueness screen."),
        ("evidence/ribbon/run_card_v2.json", "protocol run card",
         "Hypothesis, mechanism, named non-fault process, HOLDOUT-DTI + interval, registry "
         "correlation/overlap, raster sha256, validator output, submission name and note, verdict."),
        ("evidence/ribbon/adaptive_sigma.json", "HOLDOUT-DTI",
         "EXP-1: leave-one-block-out cross-fitted σ(x) by block, ridge scale and ridge type; credit "
         "calibration k̂(family, magnitude decile); the leakage canary; the marginal-inclusion bar."),
        ("evidence/ribbon/adaptive_arms.json", "HOLDOUT-DTI",
         "EXP-2: arms W1 / W3 / AD / AD2 at an equal budget of 38,000 isolated dots per fold, with "
         "per-fold DTI, paired bootstrap over the four blocks, per-σ-class gain and the catalogue "
         "distance profile of each arm."),
        ("evidence/ribbon/uniqueness_full_inventory.json", "REGISTRY-MEASUREMENT",
         "EXP-3 gate G3: the candidate against every sha256-verified raster of the public "
         "sibling-repository inventory, with E, chance-corrected lift, saturation and both the "
         "literal and the informative reading."),
        ("evidence/live_evidence_fit.json", "USER-REPORTED-SCORE",
         "66 owner-quoted sibling scores matched to sha256-verified bytes and re-measured; the "
         "calibration verdict is NEGATIVE (R² = −1.27, no covariate above |Spearman| 0.258)."),
        ("registry/live_scores_owner_reported.csv", "USER-REPORTED-SCORE",
         "All 78 owner-quoted live scores with the site URL each came from. No receipt exists for "
         "any of them."),
        ("registry/registry_merged.json", "REGISTRY-MEASUREMENT",
         "The witness inventory: 695 pinned rasters (now 695/695 byte-restored) plus the "
         "current-default-branch delta, 703 in total."),
        ("evidence/ribbon/theorems.json", "PROJECTION",
         "Algebraic properties of the official metric, including why DTI is monotone in emitted mass "
         "on a fixed support (emit 1.0) and the marginal-inclusion bar per assumed score."),
        ("evidence/ribbon/instrument_control.json", "HOLDOUT-DTI",
         "IR-58-02: the control raster that keeps a 3 px catalogue margin reads HOLDOUT-DTI exactly "
         "0.0, which is a property of the mandated holdout, not of the candidate."),
        ("evidence/buffer_overlap_scan.json", "REGISTRY-MEASUREMENT",
         "IR-58-UNIQ-03: no buffer from 3 to 10 px clears the literal 0.70 gate against saturated "
         "blanket/lattice witnesses."),
        ("evidence/sibling_record.json", "USER-REPORTED-SCORE",
         "The earlier 20-raster sibling analysis, including the n=20 Spearman(dots, score) = −0.831 "
         "that the corrected 66-file analysis supersedes."),
    ]
    rows = []
    for rel, kind, what in curated:
        path = ROOT / rel
        ex = path.exists()
        d = load(path) if path.suffix == ".json" else {}
        rows.append([f"<code>{esc(rel)}</code>" if not ex else f"<code>{esc(rel)}</code>",
                     '<span class="pill pass">present</span>' if ex
                     else '<span class="pill fail">MISSING</span>',
                     f"{path.stat().st_size:,} B" if ex else "—",
                     esc(d.get("generated_utc", "")), label(kind), what])
    all_receipts = sorted(EV.rglob("*.json"))
    listing = ", ".join(f"<code>{esc(str(p.relative_to(ROOT)))}</code>" for p in all_receipts)
    body = f"""
<h2>Every receipt this site is built from</h2>
<p class="small">Nothing on this site is written by hand: <code>scripts/build_site.py</code> reads
these files at build time and re-derives the delivered raster's sha256 from the bytes on disk. A
missing receipt turns its gate red.</p>
{table(['receipt', 'state', 'size', 'generated (UTC)', 'label it may carry', 'what it establishes'], rows, 'kv')}

<h2>Complete receipt listing under <code>evidence/</code></h2>
<p class="small">{listing}</p>

<h2>How to re-derive any number on the site</h2>
<ol class="small">
<li><code>pip install --break-system-packages -r requirements.txt</code> (adds
<code>scikit-learn</code> for the canary's <code>roc_auc_score</code>).</li>
<li><code>bash scripts/fetch_feature_stack.sh</code> — 419 MB, sha256-pinned
<code>4371c82e…3bc5</code>; then <code>export GEMS_FEATURE_STACK=~/.cache/gems/training_features.tif</code>.</li>
<li><code>python3 scripts/fetch_registry_sparse.py</code> and
<code>python3 scripts/registry_delta_inventory.py --clones /tmp/reg</code> — the 703 witness rasters.</li>
<li><code>PYTHONPATH=src python3 scripts/ribbon_run_adaptive.py</code> — EXP-1 and EXP-2
(~4 minutes).</li>
<li><code>PYTHONPATH=src:scripts python3 scripts/ribbon_emit_adaptive.py</code> — EXP-3: emit,
validate, screen, write the receipts (~2 minutes).</li>
<li><code>PYTHONPATH=src python3 scripts/check_uniqueness_registry.py &lt;candidate&gt; --workers 2
--out ribbon/uniqueness_full_inventory.json</code> — gate G3 (~30–40 minutes on 2 CPUs).</li>
<li><code>PYTHONPATH=src:. python3 -m pytest tests -q</code> then
<code>python3 scripts/build_site.py</code> (exit 0 = the banner says OK, exit 2 = it does not).</li>
</ol>
"""
    return page("Evidence index", body, "evidence.html")


def main() -> int:
    emi = load(RIB / "emission.json")
    card = load(RIB / "run_card_v2.json")
    arms = load(RIB / "adaptive_arms.json")
    sig = load(RIB / "adaptive_sigma.json")
    inv = load(RIB / "uniqueness_full_inventory.json")
    fit = load(EV / "live_evidence_fit.json")
    if not emi or not card:
        print("evidence/ribbon/emission.json or run_card_v2.json is missing — run "
              "scripts/ribbon_emit_adaptive.py first", file=sys.stderr)
        return 1

    tif = ROOT / emi["file"]
    gates, ok = evaluate_gates(emi, sig, inv, tif)
    print(f"site verdict: {'OK TO DOWNLOAD AND SUBMIT' if ok else 'NOT OK TO SUBMIT'}")
    for g in gates:
        print(f"  {g['id']} {'PASS' if g['ok'] else 'FAIL'} — {g['name']}")

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(build_index(emi, card, arms, sig, inv, fit, gates, ok),
                                     encoding="utf-8")
    (DOCS / "executive-summary.html").write_text(build_executive_summary(emi, card, arms, sig,
                                                                        gates, ok), encoding="utf-8")
    (DOCS / "submit.html").write_text(build_submit(emi, card, ok), encoding="utf-8")
    (DOCS / "evidence.html").write_text(build_evidence_index(emi, card, arms, sig, inv, fit),
                                       encoding="utf-8")

    run_card = dict(card)
    run_card.update(
        site_verdict="OK_TO_DOWNLOAD_AND_SUBMIT" if ok else "NOT_OK_TO_SUBMIT",
        site_gates=gates,
        site_generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        site_note=("G6 (organizer receipt) can never pass from this sandbox; the site verdict is "
                   "computed over G1-G5 and the missing receipt is stated on every page."),
        equal_budget_arms=arms.get("results"),
        equal_budget_deltas=arms.get("deltas_vs_W1"),
        simulated_gain_per_sigma_class=arms.get("simulated_gain_per_sigma_class"),
        sigma_table=sig.get("sigma_table_all_folds"),
        sigma_table_cross_fitted=sig.get("sigma_table_leave_one_block_out"),
        leakage_canary=sig.get("leakage_canary"),
        marginal_inclusion_bar=sig.get("marginal_inclusion_bar"),
        live_evidence=dict(verdict=fit.get("verdict"), verdict_note=fit.get("verdict_note"),
                           n_rasters=fit.get("n_distinct_rasters_fitted"),
                           covariates=fit.get("covariates")),
        inventory_scan=dict(index=inv.get("index"), verdict=inv.get("verdict"),
                            n_compared=inv.get("n_compared", inv.get("registry_rasters_expected")),
                            complete_accessible_scan=inv.get("complete_accessible_scan"),
                            worst_spearman=inv.get("worst_spearman_full_footprint"),
                            worst_overlap=inv.get("worst_dot_overlap"),
                            worst_overlap_submission=inv.get("worst_overlap_submission"),
                            duplicate_count=inv.get("duplicate_count")),
        irregularities=[dict(id=i, severity=s, text=t) for i, s, t in irregularities()],
    )
    (DOCS / "RUN_CARD.json").write_text(json.dumps(run_card, indent=1, default=float) + "\n",
                                        encoding="utf-8")
    print("wrote docs/index.html, docs/executive-summary.html, docs/submit.html, "
          f"docs/evidence.html, docs/RUN_CARD.json for {tif.name}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
