#!/usr/bin/env python3
"""Session-5 EXP-3: emit, validate and screen the H58-X1 concordance-ribbon candidate.

Recipe = the EXP-2 winner (evidence/ribbon/concordance_arms.json, arm C2):

surface      combined catalogue-free Hessian ridge field, gated so that a ridge
             pixel survives only where >= 2 independent organizer data families
             (magnetic / gravity / topographic / subsurface / geodetic / seismic)
             have their own NMS ridge response >= 0.30 within 1 px
             (H58-X1, docs/research/hypotheses_session5.md).  Leakage canary max
             AUC 0.5666 < 0.90 (evidence/ribbon/concordance_sigma.json).
threshold    tau = 0.35 (EXP-2 winner C2 at equal budget, cross-fitted ranking:
             C2 0.043575 vs C1 0.040911 vs incumbent R0 0.040105 pooled).
geometry     per-segment number and offset of parallel dotted lines (spacing
             R = 3 px) from the leave-one-block-out cross-fitted sigma(x) via
             allocation.plan at dti0 = 0.4133.
ranking      k_hat(family, magnitude decile) fitted on the full catalogue
             (production fit; the promotion-grade number is EXP-2's cross-fitted
             arm, not this file's diagnostic read-out).
screen       dots exactly on the mapped catalogue are dropped (organizer-masked,
             inert); no catalogue margin (IR-58-02).
budget       median dot count of the owner-reported >= 0.24 live family
             (same measured rule as the session-3 emitter).
isolation    no two 8-adjacent dots.
emission     every included dot at exactly 1.0 (scaling down only scales the
             net gain down -- see docs/research/ribbon-algebra.md).

Phases (so the pre-placement gate can run between them):
  --surface   write the placement surface (ranked support, [0,1]) to
              evidence/ribbon/concordance_surface.tif for the registry gate.
  --emit      write docs/downloads/<name>.tif/.zip/.checks.json + receipt.

    PYTHONPATH=src GEMS_FEATURE_STACK=~/.cache/gems/training_features.tif \
        python3 scripts/ribbon_emit_concordance.py --surface
    python3 scripts/check_uniqueness_registry.py evidence/ribbon/concordance_surface.tif ...
    python3 scripts/ribbon_emit_concordance.py --emit
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems58w import allocation, extract, features as FEAT, grid, holdout, metric  # noqa: E402
from gems58w import sigma as SIGMA  # noqa: E402
from gems58w import submission as SUB  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402
from gems58w import uniqueness as UNIQ  # noqa: E402
from ribbon_build_family_cache import build as build_families  # noqa: E402
from ribbon_run_adaptive import greedy_topk, ribbon_support  # noqa: E402
from ribbon_run_concordance import TAU_FAMILY, MIN_FAMILIES, gated_field, offsets_factory, sigma_machinery  # noqa: E402

TAU = 0.35             # EXP-2 winner C2
DTI0 = 0.4133          # public leaderboard #1 recorded 2026-10-11 (evidence/official_leaderboard_observation_20261011.json)
MIN_SEP = 1
LIVE_FLOOR = 0.24
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTDIR = ROOT / "docs" / "downloads"
SURFACE_TIF = evidence_dir() / "concordance_surface.tif"
STATE_NPZ = evidence_dir() / "concordance_emit_state.npz"
STATE_JSON = evidence_dir() / "concordance_emit_state.json"


def live_budget() -> dict:
    d = json.loads((ROOT / "evidence" / "live_evidence_fit.json").read_text())
    rows = [r for r in d["fitted_rows"] if r["score"] >= LIVE_FLOOR]
    dots = sorted(int(r["dots"]) for r in rows)
    if not dots:
        raise SystemExit("no live-evidence rows at or above the floor")
    return dict(budget=int(np.median(dots)), n_files=len(dots), score_floor=LIVE_FLOOR,
                dot_counts=dots, source="evidence/live_evidence_fit.json",
                score_label="USER-REPORTED-SCORE (owner-quoted sibling pages; no organizer receipt)",
                rule=f"median dot count of the owner-reported >= {LIVE_FLOOR} family")


def build_surface() -> dict:
    t0 = time.time()
    fp = grid.footprint()
    folds = holdout.all_folds()
    field = extract.build()
    fams = build_families()
    gfield, gate_stats, _ = gated_field(field, fams)
    segs = extract.segments(gfield, TAU, min_px=8)
    print(f"[surface] gated tau={TAU}: {len(segs)} segments, "
          f"{sum(s['size'] for s in segs)} ridge px", flush=True)

    per_fold, table_loo, table_all = sigma_machinery(gfield, segs, folds)

    # production k_hat: (family, decile) mean kernel credit against the FULL catalogue
    ridge_mask = gfield["mag"] >= TAU
    pts = np.argwhere(ridge_mask)
    mag_at = gfield["mag"][pts[:, 0], pts[:, 1]]
    code_at = gfield["code"][pts[:, 0], pts[:, 1]]
    fam_of_code = {i + 1: next((k for k, v in FEAT.FAMILIES.items() if c["band"] in v), "other")
                   for i, c in enumerate(gfield["codes"])}
    fam_at = np.array([fam_of_code.get(int(c), "other") for c in code_at])
    edges = np.quantile(mag_at, np.linspace(0, 1, 11))
    dec = np.clip(np.digitize(mag_at, edges[1:-1]), 0, 9)
    d_cat = distance_transform_edt(~grid.catalogue()).astype(np.float32)
    k = metric.kernel(d_cat[pts[:, 0], pts[:, 1]])
    calib = {}
    for fam in list(FEAT.FAMILIES) + ["all"]:
        sel = np.ones(len(k), bool) if fam == "all" else (fam_at == fam)
        for q in range(10):
            s2 = sel & (dec == q)
            if s2.any():
                calib[f"{fam}|q{q}"] = float(k[s2].mean())
    kk = np.array([calib.get(f"{fam_at[i]}|q{dec[i]}", calib.get(f"all|q{dec[i]}", 0.0))
                   for i in range(len(dec))])
    rank_grid = np.zeros(gfield["mag"].shape, np.float64)
    rank_grid[pts[:, 0], pts[:, 1]] = kk
    rank_grid += 1e-6 * gfield["mag"]

    hist, plan_rows = {}, []
    support = ribbon_support(gfield, segs, offsets_factory(table_loo, hist, plan_rows), fp)
    print(f"[geometry] support {int(support.sum())} px; "
          f"lines histogram {dict(sorted(hist.items()))}", flush=True)

    # the pre-placement surface: ranked support, normalised to [0,1]
    surf = np.where(support, rank_grid, 0.0)
    m = float(surf.max())
    surf01 = (surf / m if m > 0 else surf).astype(np.float32)
    SUB.write(SURFACE_TIF, np.zeros_like(fp, bool), fp)  # grid-conform shell
    import rasterio
    with rasterio.open(SURFACE_TIF, "r+") as dst:
        out = np.full(fp.shape, np.nan, np.float32)
        out[fp] = surf01[fp]
        dst.write(out, 1)

    np.savez_compressed(STATE_NPZ, support=support, rank_grid=rank_grid)
    state = dict(generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 tau=TAU, tau_family=TAU_FAMILY, min_families=MIN_FAMILIES,
                 gate=gate_stats, n_segments=len(segs),
                 support_px=int(support.sum()),
                 lines_histogram={str(kk_): v for kk_, v in sorted(hist.items())},
                 sigma_table_all_folds=table_all,
                 sigma_table_leave_one_block_out=table_loo,
                 plan_rows_sample=plan_rows[:40],
                 khat_production=calib,
                 surface_tif=str(SURFACE_TIF.relative_to(ROOT)),
                 wall_seconds=round(time.time() - t0, 1))
    STATE_JSON.write_text(json.dumps(state, indent=1))
    print(f"[surface] wrote {SURFACE_TIF} + state ({time.time()-t0:.1f}s)", flush=True)
    return state


def emit() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.all_folds()
    z = np.load(STATE_NPZ)
    support, rank_grid = z["support"].astype(bool), z["rank_grid"]
    state = json.loads(STATE_JSON.read_text())

    n_on_cat = int((support & cat).sum())
    support &= ~cat
    budget = live_budget()
    dots, n = greedy_topk(support, rank_grid, budget["budget"], MIN_SEP)
    print(f"[emit] dropped {n_on_cat} on-catalogue px; budget {budget['budget']}; kept {n}",
          flush=True)

    # HOLDOUT-DTI of the delivered bytes -- DIAGNOSTIC (ranking consulted the
    # full catalogue; the promotion-grade number is EXP-2 arm C2, cross-fitted)
    per_fold_dti, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0)
    for f in folds:
        r = metric.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        per_fold_dti[f.name] = r.dti
        for kk in ("tp", "fp", "fn", "n_truth"):
            agg[kk] += getattr(r, kk)
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    pooled = float(agg["tp"] / den)
    print(f"[holdout] delivered-bytes diagnostic pooled {pooled:.6f} "
          f"per-fold { {k: round(v, 6) for k, v in per_fold_dti.items()} }", flush=True)

    d_cat = distance_transform_edt(~cat).astype(np.float32)
    v = d_cat[dots]
    profile = dict(n=int(dots.sum()), on_catalogue=int((dots & cat).sum()),
                   median_px=float(np.median(v)), mean_px=float(v.mean()),
                   frac_le_1px=float((v <= 1).mean()), frac_le_3px=float((v <= 3).mean()),
                   frac_le_10px=float((v <= 10).mean()),
                   min_px=float(v.min()), max_px=float(v.max()))

    name = f"gems58-concordance-ribbon-{n}-{STAMP}"
    tif = OUTDIR / f"{name}.tif"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    SUB.write(tif, dots, fp)
    checks = SUB.validate(tif, min_dots=1000, max_dots=120000)
    note = SUB.note(f"Ribbon lane H58-X1: 2-family-concordant Hessian ridges, "
                    f"sigma-adaptive dotted ribbons 0/±300/±600 m; {n} isolated dots at 1.0.")
    print(f"[validate] passed={checks['passed']} sha256={checks['sha256']}", flush=True)
    for kk, c in checks["checks"].items():
        if not c["ok"]:
            print(f"    FAIL {kk}: {c['detail']}", flush=True)
    zip_path = OUTDIR / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zz:
        zz.write(tif, arcname=tif.name)

    # local uniqueness screen: registry checkout + every earlier raster in this repo
    own = sorted((ROOT / "docs" / "downloads").glob("*.tif")) + \
        sorted((ROOT / "docs" / "downloads" / "archive").glob("*.tif")) + \
        sorted((ROOT / "docs" / "deliverable" / "downloads").glob("*.tif")) + \
        sorted((ROOT / "docs" / "ribbon" / "downloads").glob("*.tif")) + \
        sorted((ROOT / "evidence").rglob("*.tif"))
    own = [p for p in own if p.resolve() != tif.resolve()
           and p.resolve() != SURFACE_TIF.resolve()]
    witnesses = sorted((ROOT / "data" / "registry" / "rasters").glob("*.tif"))
    names = [p.name for p in witnesses]
    witnesses += own
    names += [f"OWN:{p.relative_to(ROOT)}" for p in own]
    rows_local, uniq_local = UNIQ.screen_paths(dots, witnesses, names=names)
    print(f"[uniqueness:local] {uniq_local['n_checked']} witnesses | worst rho "
          f"{uniq_local['worst_rho']:.4f} | worst fwd overlap "
          f"{uniq_local['worst_forward_overlap']:.4f} | cleared {uniq_local['cleared']}",
          flush=True)

    receipt = dict(
        evidence_class="HOLDOUT-DTI(diagnostic) + LOCAL-FORMAT-PREFLIGHT",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        name=name, file=str(tif.relative_to(ROOT)), zip=str(zip_path.relative_to(ROOT)),
        sha256=checks["sha256"], bytes=checks["bytes"], n_positives=checks["n_positives"],
        validator=checks, submission_note=note, submission_note_chars=len(note),
        design=dict(hypothesis="H58-X1 cross-family concordance gate",
                    tau=TAU, tau_family=TAU_FAMILY, min_families=MIN_FAMILIES,
                    dti0=DTI0, min_sep=MIN_SEP,
                    ranking="k_hat(family, magnitude decile) fitted on the full catalogue "
                            "(production); promotion-grade evidence is EXP-2 arm C2",
                    screen="on-catalogue dots dropped (organizer-masked, inert); no margin",
                    budget=budget,
                    lines_per_segment_histogram=state["lines_histogram"],
                    sigma_cross_fitting="leave-one-block-out"),
        sigma_table_all_folds=state["sigma_table_all_folds"],
        sigma_table_leave_one_block_out=state["sigma_table_leave_one_block_out"],
        plan_rows_sample=state["plan_rows_sample"],
        uniqueness_local=uniq_local,
        uniqueness_local_rows=[r.as_dict() if hasattr(r, "as_dict") else r for r in rows_local],
        holdout_dti=dict(
            pooled=pooled, pooled_is_diagnostic=True, per_fold=per_fold_dti, components=agg,
            coverage=float(agg["tp"] / agg["n_truth"]) if agg["n_truth"] else 0.0,
            protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
            n_withheld_positives=int(agg["n_truth"]),
            ci=dict(lo=float(min(per_fold_dti.values())), hi=float(max(per_fold_dti.values())),
                    note="min-max over the four spatial blocks; no bootstrap over 4 blocks"),
            label=("DIAGNOSTIC: the production ranking consulted the full catalogue, so this "
                   "number is not promotion-grade. Promotion-grade HOLDOUT-DTI is EXP-2 arm C2 "
                   "(cross-fitted): pooled 0.043575, evidence/ribbon/concordance_arms.json. "
                   "Withheld truth is catalogue-based proxy truth, not the organizer's "
                   "private expert faults; neither number is a leaderboard forecast.")),
        catalogue_distance_profile=profile,
        wall_seconds=round(time.time() - t0, 1))
    (evidence_dir() / "concordance_emission.json").write_text(json.dumps(receipt, indent=1))
    (OUTDIR / f"{name}.checks.json").write_text(json.dumps(checks, indent=1))
    print(f"[done] {tif} ({time.time()-t0:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", action="store_true")
    ap.add_argument("--emit", action="store_true")
    a = ap.parse_args()
    if a.surface:
        build_surface()
    if a.emit:
        raise SystemExit(emit())
    if not (a.surface or a.emit):
        raise SystemExit("pass --surface and/or --emit")
