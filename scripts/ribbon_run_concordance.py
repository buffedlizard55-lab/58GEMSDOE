#!/usr/bin/env python3
"""Session-5 ribbon-lane experiments for H58-X1 (cross-family concordance gate).

EXP-1  sigma(x), leakage canary and allocator simulation for the gated field
    * gate: an NMS ridge pixel of the combined field survives iff at least
      MIN_FAMILIES organizer data families have their own NMS ridge response
      >= TAU_FAMILY within 1 px (family grids from
      scripts/ribbon_build_family_cache.py; catalogue-free by construction);
    * sigma is measured per withheld catalogue component on the buffered
      hide-and-recover holdout (gems58-pooled-hide-v1) for the gated segments,
      stratified by data block, ridge scale and ridge type, and the table used
      to plan fold b is fitted on the other three folds (leave-one-block-out);
    * leakage canary: feature-alone AUC of each family grid (and the gated
      combined field) at separating withheld truth from background. AUC > 0.90
      means leakage until proven otherwise;
    * allocator simulation: U(plan) - U(single line) per measured sigma class
      (the lane's "simulated gain per class").

EXP-2  equal-budget arms contest, exact metric, leak-free
    R0   incumbent recipe (tau = 0.45, ungated)  -- the control to beat;
    C1   concordance gate at tau = 0.45, TAU_FAMILY = 0.30;
    C2   concordance gate at tau = 0.35 (relaxed supply), TAU_FAMILY = 0.30.
    Every arm: same budget, same min-separation, same LOO k_hat ranking rule,
    dots selected only outside the fold's visible-catalogue + 3 px collar
    (leak-free), scored per fold with gems58w.metric.dti_binary and pooled.
    Unlike the session-3 instrument, k_hat here is ALSO cross-fitted
    (leave-one-block-out), for the control arm too, so no arm's ranking ever
    saw the truth it is scored on.

Promotion rule (preregistered in docs/research/hypotheses_session5.md): a gated
arm is promoted only if its pooled HOLDOUT-DTI >= R0's pooled HOLDOUT-DTI.

Writes evidence/ribbon/concordance_sigma.json and
       evidence/ribbon/concordance_arms.json

    PYTHONPATH=src GEMS_FEATURE_STACK=~/.cache/gems/training_features.tif \
        python3 scripts/ribbon_run_concordance.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems58w import allocation, extract, features as FEAT, grid, holdout, metric  # noqa: E402
from gems58w import sigma as SIGMA  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402
from ribbon_build_family_cache import build as build_families  # noqa: E402
from ribbon_run_adaptive import evaluate, greedy_topk, ribbon_support  # noqa: E402

BUDGET = 38000          # identical to the session-3 arms instrument
MIN_SEP = 1
DTI0 = 0.4133           # public leaderboard #1 recorded 2026-10-11 (see evidence/)
TAU_FAMILY = 0.30       # preregistered family-support threshold
MIN_FAMILIES = 2        # concordance = at least two independent physical families
DILATE_PX = 1           # "within 1 px" agreement tolerance

ARMS = {
    "R0": dict(tau=0.45, gated=False),
    "C1": dict(tau=0.45, gated=True),
    "C2": dict(tau=0.35, gated=True),
}


def gated_field(field: dict, fams: dict) -> tuple[dict, dict]:
    """Combined field with non-concordant ridge pixels zeroed, + gate stats."""
    st = np.ones((2 * DILATE_PX + 1,) * 2, bool)
    n_support = np.zeros(field["mag"].shape, np.int16)
    per_family_px = {}
    for name in sorted(fams):
        sup = binary_dilation(fams[name] >= TAU_FAMILY, structure=st)
        n_support += sup
        per_family_px[name] = int((fams[name] >= TAU_FAMILY).sum())
    gate = n_support >= MIN_FAMILIES
    g = dict(field)
    g["mag"] = np.where(gate, field["mag"], 0.0).astype(np.float32)
    stats = dict(tau_family=TAU_FAMILY, min_families=MIN_FAMILIES,
                 dilate_px=DILATE_PX, per_family_support_px=per_family_px,
                 gate_px=int(gate.sum()))
    return g, stats, gate


def loo_khat(field: dict, tau: float, folds):
    """Leave-one-block-out k_hat(family, magnitude decile) rank grids."""
    ridge_mask = field["mag"] >= tau
    pts = np.argwhere(ridge_mask)
    mag_at = field["mag"][pts[:, 0], pts[:, 1]]
    code_at = field["code"][pts[:, 0], pts[:, 1]]
    fam_of_code = {i + 1: next((k for k, v in FEAT.FAMILIES.items() if c["band"] in v), "other")
                   for i, c in enumerate(field["codes"])}
    fam_at = np.array([fam_of_code.get(int(c), "other") for c in code_at])
    edges = np.quantile(mag_at, np.linspace(0, 1, 11))
    dec = np.clip(np.digitize(mag_at, edges[1:-1]), 0, 9)
    # per-fold sums
    sums, cnts = {}, {}
    for f in folds:
        d = distance_transform_edt(~f.withhold).astype(np.float32)
        k = metric.kernel(d[pts[:, 0], pts[:, 1]])
        for fam in list(FEAT.FAMILIES) + ["all"]:
            sel = np.ones(len(k), bool) if fam == "all" else (fam_at == fam)
            for q in range(10):
                s2 = sel & (dec == q)
                if not s2.any():
                    continue
                key = (fam, q)
                sums.setdefault(key, {})[f.name] = float(k[s2].sum())
                cnts.setdefault(key, {})[f.name] = int(s2.sum())
    grids = {}
    for f in folds:
        others = [g.name for g in folds if g.name != f.name]
        val = np.zeros(len(pts), np.float64)
        for i in range(len(pts)):
            fam, q = fam_at[i], int(dec[i])
            for key in ((fam, q), ("all", q)):
                s = sum(sums.get(key, {}).get(o, 0.0) for o in others)
                n = sum(cnts.get(key, {}).get(o, 0) for o in others)
                if n:
                    val[i] = s / n
                    break
        rg = np.zeros(field["mag"].shape, np.float64)
        rg[pts[:, 0], pts[:, 1]] = val
        rg += 1e-6 * field["mag"]
        grids[f.name] = rg
    return grids


def loo_khat_fast(field: dict, tau: float, folds):
    """Vectorised version of loo_khat (same arithmetic)."""
    ridge_mask = field["mag"] >= tau
    pts = np.argwhere(ridge_mask)
    mag_at = field["mag"][pts[:, 0], pts[:, 1]]
    code_at = field["code"][pts[:, 0], pts[:, 1]]
    fam_names = list(FEAT.FAMILIES) + ["other"]
    fam_idx_of_code = np.zeros(len(field["codes"]) + 1, np.int32)
    for i, c in enumerate(field["codes"]):
        fam = next((k for k, v in FEAT.FAMILIES.items() if c["band"] in v), "other")
        fam_idx_of_code[i + 1] = fam_names.index(fam)
    fam_at = fam_idx_of_code[code_at]
    edges = np.quantile(mag_at, np.linspace(0, 1, 11))
    dec = np.clip(np.digitize(mag_at, edges[1:-1]), 0, 9)
    nf, nq = len(fam_names), 10
    stratum = fam_at * nq + dec
    sums = {}
    cnts = np.bincount(stratum, minlength=nf * nq).astype(np.float64)
    cred = {}
    for f in folds:
        d = distance_transform_edt(~f.withhold).astype(np.float32)
        k = metric.kernel(d[pts[:, 0], pts[:, 1]])
        cred[f.name] = np.bincount(stratum, weights=k, minlength=nf * nq)
    # "all" pooled over families, per decile
    dec_cnt = np.bincount(dec, minlength=nq).astype(np.float64)
    dec_cred = {f.name: np.bincount(dec, weights=metric.kernel(
        distance_transform_edt(~f.withhold).astype(np.float32)[pts[:, 0], pts[:, 1]]),
        minlength=nq) for f in folds}
    grids = {}
    for f in folds:
        others = [g.name for g in folds if g.name != f.name]
        num = sum(cred[o] for o in others)
        den = cnts * len(others)
        khat = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
        num_d = sum(dec_cred[o] for o in others)
        den_d = dec_cnt * len(others)
        khat_d = np.divide(num_d, den_d, out=np.zeros_like(num_d), where=den_d > 0)
        val = khat[stratum]
        empty = den[stratum] <= 0
        val[empty] = khat_d[dec[empty]]
        rg = np.zeros(field["mag"].shape, np.float64)
        rg[pts[:, 0], pts[:, 1]] = val
        rg += 1e-6 * field["mag"]
        grids[f.name] = rg
    return grids


def sigma_machinery(field: dict, segs, folds):
    per_fold = {f.name: SIGMA.measure(field, segs, f) for f in folds}
    table_loo = {b: SIGMA.sigma_table([c for f in folds if f.name != b
                                       for c in per_fold[f.name]])
                 for b in holdout.BLOCKS}
    table_all = SIGMA.sigma_table([c for f in folds for c in per_fold[f.name]])
    return per_fold, table_loo, table_all


def offsets_factory(table_loo, hist, plan_rows):
    def offsets_of(s):
        code = max(s["codes"], key=lambda c: c["scale"]) if s["codes"] else {}
        band = code.get("band", "?")
        fam = next((k for k, v in FEAT.FAMILIES.items() if band in v), "other")
        blk = holdout.block_of(s["idx"].mean(axis=0))
        sig, which = SIGMA.sigma_for(fam, float(code.get("scale", 0.0)),
                                     int(code.get("sign", 0)), blk, table_loo[blk])
        pl = allocation.plan(sig, DTI0, max_k=3)
        hist[pl.n_lines] = hist.get(pl.n_lines, 0) + 1
        plan_rows.append(dict(block=blk, family=fam, sigma_px=sig, stratum=which,
                              n_lines=pl.n_lines, offsets_px=list(pl.offsets),
                              U=pl.U, segment_px=int(s["size"])))
        return list(pl.offsets)
    return offsets_of


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    folds = holdout.all_folds()
    field = extract.build()
    fams = build_families()
    gfield, gate_stats, gate = gated_field(field, fams)
    print(f"[gate] {gate_stats['gate_px']} px pass >= {MIN_FAMILIES}-family "
          f"concordance at tau_f={TAU_FAMILY}", flush=True)

    # ------------------------- EXP-1: sigma + canary -------------------------
    segs_c1 = extract.segments(gfield, ARMS["C1"]["tau"], min_px=8)
    per_fold_sig, table_loo_c1, table_all_c1 = sigma_machinery(gfield, segs_c1, folds)
    print(f"[sigma] C1 gated tau=0.45: {len(segs_c1)} segments, "
          f"{sum(s['size'] for s in segs_c1)} px, pooled sigma "
          f"{(table_all_c1.get('pooled') or {}).get('median')}", flush=True)

    # feature-alone canary: each family grid, the gated and ungated combined field
    rng = np.random.default_rng(58)
    bg = np.argwhere(fp)
    bg = bg[rng.choice(len(bg), size=min(300000, len(bg)), replace=False)]
    canary = {}
    truth_all = np.zeros_like(fp)
    for f in folds:
        truth_all |= f.withhold
    tr = np.argwhere(truth_all & fp)
    st3 = np.ones((7, 7), bool)  # value within kernel radius 3 px
    for name in sorted(fams) + ["combined_ungated", "combined_gated"]:
        g = {"combined_ungated": field["mag"], "combined_gated": gfield["mag"]}.get(name, fams.get(name))
        from scipy.ndimage import maximum_filter
        gmax = maximum_filter(g, footprint=st3)
        y = np.r_[np.ones(len(tr)), np.zeros(len(bg))]
        x = np.r_[gmax[tr[:, 0], tr[:, 1]], gmax[bg[:, 0], bg[:, 1]]]
        canary[name] = float(roc_auc_score(y, x))
    worst = max(canary.values())
    print(f"[canary] feature-alone AUC: { {k: round(v, 4) for k, v in canary.items()} } "
          f"worst={worst:.4f} (limit 0.90)", flush=True)

    # allocator simulation: U(plan) - U(single line) per sigma class
    sim = {}
    for lo, hi, label in ((0.0, 0.5, "sigma<0.5px"), (0.5, 1.0, "0.5-1px"),
                          (1.0, 2.0, "1-2px"), (2.0, 3.0, "2-3px"), (3.0, 99.0, ">3px")):
        mid = min(max((lo + hi) / 2.0, 0.25), 6.0)
        pl = allocation.plan(mid, DTI0, max_k=3)
        u1 = (1 - metric.ALPHA * DTI0) * allocation.normal_credit(0.0, mid) - metric.ALPHA * DTI0 * 0.0
        sim[label] = dict(sigma_px=mid, n_lines=pl.n_lines, offsets=list(pl.offsets),
                          U_plan=pl.U, U_single_line_credit=float(allocation.normal_credit(0.0, mid)),
                          note="U per dot of the chosen plan vs credit of a single tight line; "
                               "legacy Normal-model simulation, not a holdout claim")
    e1 = dict(
        evidence_class="HOLDOUT-DTI instrument calibration (catalogue proxy truth)",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
        hypothesis="H58-X1 cross-family concordance gate (docs/research/hypotheses_session5.md)",
        gate=gate_stats,
        n_segments_c1=len(segs_c1),
        sigma_table_all_folds=table_all_c1,
        sigma_table_leave_one_block_out=table_loo_c1,
        leakage_canary=dict(auc=canary, limit=0.90, worst=worst,
                            verdict="no leakage signal" if worst <= 0.90 else "LEAKAGE SUSPECT"),
        simulated_gain_per_sigma_class=sim,
        wall_seconds=round(time.time() - t0, 1))
    (evidence_dir() / "concordance_sigma.json").write_text(json.dumps(e1, indent=1))

    # ------------------------- EXP-2: arms contest ---------------------------
    results, deltas, arm_meta = {}, {}, {}
    for arm, cfg in ARMS.items():
        fld = gfield if cfg["gated"] else field
        segs = segs_c1 if (cfg["gated"] and cfg["tau"] == ARMS["C1"]["tau"]) else \
            extract.segments(fld, cfg["tau"], min_px=8)
        _, table_loo, _ = (per_fold_sig, table_loo_c1, table_all_c1) if segs is segs_c1 else \
            sigma_machinery(fld, segs, folds)
        rank_by_fold = loo_khat_fast(fld, cfg["tau"], folds)
        hist, plan_rows = {}, []
        support = ribbon_support(fld, segs, offsets_factory(table_loo, hist, plan_rows), fp)
        pred_by_fold = {}
        n_dots = {}
        for f in folds:
            allowed = support & fp & ~f.known
            dots, n = greedy_topk(allowed, rank_by_fold[f.name], BUDGET, MIN_SEP)
            pred_by_fold[f.name] = dots
            n_dots[f.name] = n
        r = evaluate(pred_by_fold, folds)
        results[arm] = dict(cfg=cfg, n_segments=len(segs),
                            support_px=int(support.sum()), dots_per_fold=n_dots,
                            lines_histogram={str(k): v for k, v in sorted(hist.items())},
                            pooled=r["pooled"], per_fold=r["per_fold"],
                            coverage=r["coverage"], agg=r["agg"])
        print(f"[arm {arm}] tau={cfg['tau']} gated={cfg['gated']}: segments={len(segs)} "
              f"support={int(support.sum())} pooled={r['pooled']:.6f} "
              f"per-fold={ {k: round(v, 6) for k, v in r['per_fold'].items()} }", flush=True)
    for arm in ("C1", "C2"):
        deltas[arm] = dict(
            pooled=float(results[arm]["pooled"] - results["R0"]["pooled"]),
            per_fold={b: float(results[arm]["per_fold"][b] - results["R0"]["per_fold"][b])
                      for b in holdout.BLOCKS})
    winner = max(results, key=lambda a: results[a]["pooled"])
    promote = results[winner]["pooled"] >= results["R0"]["pooled"] and winner != "R0"
    e2 = dict(
        evidence_class="HOLDOUT-DTI (catalogue proxy truth; not a leaderboard forecast)",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
        n_withheld_positives=int(sum(f.n_truth for f in folds)),
        budget=BUDGET, min_sep=MIN_SEP, dti0=DTI0,
        ranking="k_hat(family, magnitude decile), leave-one-block-out cross-fitted "
                "for every arm including the control (fixes the pooled-k_hat defect "
                "of the session-3 instrument)",
        screen="dots selected outside the fold's visible catalogue + 3 px collar (leak-free)",
        arms=results, deltas_vs_R0=deltas, winner=winner,
        promotion_rule="gated arm promoted iff pooled >= R0 pooled (preregistered)",
        promoted=("C-arm " + winner) if promote else "none (R0 stands)",
        wall_seconds=round(time.time() - t0, 1))
    (evidence_dir() / "concordance_arms.json").write_text(json.dumps(e2, indent=1))
    print(f"[done] winner={winner} promoted={promote} wall={time.time()-t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
