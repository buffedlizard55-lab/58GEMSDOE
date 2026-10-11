#!/usr/bin/env python3
"""Ribbon lane EXP-1 + EXP-2, promotion-grade instrument.

EXP-1  sigma(x) and the credit-calibration curve, **cross-fitted**
    * the ridge field is catalogue-free (built only from the organizer's
      sha256-verified 19-band stack), so it is identical in every fold;
    * sigma is measured per withheld catalogue component on the buffered
      hide-and-recover holdout (``gems58-pooled-hide-v1``, BUFFER_PX = 3) and is
      stratified by data block, feature resolution (ridge scale) and ridge type
      (band family x ridge sign);
    * the sigma table used to score fold *b* is fitted on the **other three**
      folds only (leave-one-block-out).  The earlier instrument fitted sigma on
      the same folds it scored, which is the defect this script removes;
    * k_hat(stratum, magnitude decile) = the mean exact-kernel credit
      ``max_g k(d(x,g))`` of ridge pixels against the withheld truth, pooled over
      folds.  This is the quantity the metric's marginal-inclusion bar is written
      in, so it converts a ridge response into an expected credit;
    * leakage canary: AUC of the combined field and of each band family at
      separating withheld truth pixels from background.  AUC > 0.90 = leakage.

EXP-2  the equal-budget width contest, exact metric
    Every arm emits isolated dots (no two 8-adjacent) and every arm is capped at
    the **same** budget, so the only difference is the geometry of the support:
      W1   one tight line on the ridge;
      W3   the prior delivered geometry: five lines at 0, +-3, +-6 px;
      AD   the lane rule: per-segment number and offset of lines from the
           cross-fitted sigma via ``gems58w.allocation.plan``;
      AD2  as AD at a second ridge threshold (sensitivity).
    Each arm is screened against the *visible* catalogue only (leak-free), scored
    per fold with ``known`` = visible + 3 px buffer, pooled, with a block-paired
    bootstrap CI, plus the simulated gain per measured-sigma class.

Writes ``evidence/ribbon/adaptive_sigma.json`` and
``evidence/ribbon/adaptive_arms.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=~/.cache/gems/training_features.tif \
        python3 scripts/ribbon_run_adaptive.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import extract, features as FEAT, grid, holdout, metric  # noqa: E402
from gems58w import sigma as SIGMA  # noqa: E402
from gems58w import allocation  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402

BUDGET = 38000
MIN_SEP = 1
DTI0_LEADER = 0.4133      # ORGANIZER-CONFIRMED public leaderboard #1, fetched 2026-10-11
DTI0_GROUP = 0.2750       # USER-REPORTED best undisputed group artifact


# --------------------------------------------------------------------------- #
# support geometry
# --------------------------------------------------------------------------- #
def ribbon_support(field, segs, offsets_of, allowed=None) -> np.ndarray:
    """Rasterise parallel dotted lines; ``offsets_of(segment) -> list[float]`` in px."""
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    for s in segs:
        idx = s["idx"]
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        for o in offsets_of(s):
            if abs(o) < 1e-9:
                rr, cc = idx[:, 0], idx[:, 1]
            else:
                rr = np.rint(idx[:, 0] + o * ay).astype(int)
                cc = np.rint(idx[:, 1] + o * ax).astype(int)
            ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
            mask[rr[ok], cc[ok]] = True
    if allowed is not None:
        mask &= allowed
    return mask


def greedy_topk(mask: np.ndarray, rank: np.ndarray, budget: int, min_sep: int = MIN_SEP):
    """Highest-ranked isolated dots, up to ``budget``."""
    cand = np.argwhere(mask)
    if cand.shape[0] == 0:
        return np.zeros_like(mask), 0
    vals = rank[cand[:, 0], cand[:, 1]]
    cand = cand[np.argsort(-vals, kind="stable")]
    shape = mask.shape
    blocked = np.zeros(shape, bool)
    keep = np.zeros(shape, bool)
    k = max(0, min_sep)
    n = 0
    for r, c in cand:
        if blocked[r, c]:
            continue
        keep[r, c] = True
        n += 1
        blocked[max(0, r - k):r + k + 1, max(0, c - k):c + k + 1] = True
        if n >= budget:
            break
    return keep, n


def evaluate(pred_by_fold: dict, folds) -> dict:
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0, n_dots=0)
    for f in folds:
        r = metric.dti_binary(pred_by_fold[f.name], f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        agg["tp"] += r.tp
        agg["fp"] += r.fp
        agg["fn"] += r.fn
        agg["n_truth"] += r.n_truth
        agg["n_dots"] += int((pred_by_fold[f.name] & f.valid & ~f.known).sum())
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    return dict(pooled=float(agg["tp"] / den), per_fold=per_fold, agg=agg,
                coverage=float(agg["tp"] / agg["n_truth"]) if agg["n_truth"] else 0.0)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--threshold2", type=float, default=0.45)
    ap.add_argument("--dti0", type=float, default=DTI0_LEADER)
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    folds = holdout.all_folds()
    fp = grid.footprint()
    cat_d_all = distance_transform_edt(~grid.catalogue()).astype(np.float32)

    # ---------------- EXP-1a: per-fold sigma, leave-one-block-out tables -------
    segs_by_tau = {args.threshold: extract.segments(field, args.threshold, min_px=8)}
    segs_by_tau[args.threshold2] = extract.segments(field, args.threshold2, min_px=8)
    segs = segs_by_tau[args.threshold]
    print(f"[field] segments tau={args.threshold}: {len(segs)} "
          f"({sum(s['size'] for s in segs)} px); tau={args.threshold2}: "
          f"{len(segs_by_tau[args.threshold2])}", flush=True)

    per_fold_sigma = {}
    for f in folds:
        items = SIGMA.measure(field, segs, f)
        per_fold_sigma[f.name] = items
        print(f"[sigma] fold {f.name}: {len(items)} matched withheld components "
              f"(of {int(f.n_truth)} withheld px)", flush=True)
    table_all = SIGMA.sigma_table([c for f in folds for c in per_fold_sigma[f.name]])
    table_loo = {b: SIGMA.sigma_table([c for f in folds if f.name != b
                                       for c in per_fold_sigma[f.name]])
                 for b in holdout.BLOCKS}

    # ---------------- EXP-1b: credit calibration k_hat(stratum, decile) --------
    ridge_mask = field["mag"] >= args.threshold
    ridge_pts = np.argwhere(ridge_mask)
    mag_at = field["mag"][ridge_pts[:, 0], ridge_pts[:, 1]]
    code_at = field["code"][ridge_pts[:, 0], ridge_pts[:, 1]]
    fam_of_code = {}
    for i, c in enumerate(field["codes"]):
        fam_of_code[i + 1] = next((k for k, v in FEAT.FAMILIES.items() if c["band"] in v), "other")
    fam_at = np.array([fam_of_code.get(int(c), "other") for c in code_at])
    edges = np.quantile(mag_at, np.linspace(0, 1, 11))
    edges[0] -= 1e-9
    dec = np.clip(np.digitize(mag_at, edges[1:-1]), 0, 9)
    blk_at = np.array([holdout.block_of(p) for p in ridge_pts])

    khat = {}          # (family, decile) -> pooled mean kernel credit vs withheld truth
    khat_n = {}
    det = {}
    for f in folds:
        d = distance_transform_edt(~f.withhold).astype(np.float32)
        k = metric.kernel(d[ridge_pts[:, 0], ridge_pts[:, 1]])
        for fam in list(FEAT.FAMILIES) + ["all"]:
            sel = np.ones(len(k), bool) if fam == "all" else (fam_at == fam)
            for q in range(10):
                s2 = sel & (dec == q)
                if not s2.any():
                    continue
                key = f"{fam}|q{q}"
                khat[key] = khat.get(key, 0.0) + float(k[s2].sum())
                khat_n[key] = khat_n.get(key, 0) + int(s2.sum())
                det[key] = det.get(key, 0.0) + float((d[ridge_pts[s2, 0], ridge_pts[s2, 1]] <= 3).sum())
    calib = {key: dict(n_ridge_px=khat_n[key], mean_kernel_credit=khat[key] / khat_n[key],
                       detection_le_3px=det[key] / khat_n[key],
                       mag_lo=float(edges[q]), mag_hi=float(edges[q + 1]))
             for key, q in ((k, int(k.split("|q")[1])) for k in khat)}
    calib_rows = sorted(calib.items(), key=lambda kv: (kv[0].split("|")[0], int(kv[0].split("|q")[1])))
    print("[calib] all-family deciles (mean kernel credit / detection<=3px):", flush=True)
    for key, v in calib_rows:
        if key.startswith("all|"):
            print(f"    {key:8s} n={v['n_ridge_px']:7d} khat={v['mean_kernel_credit']:.4f} "
                  f"det={v['detection_le_3px']:.4f}", flush=True)

    # ---------------- EXP-1c: leakage canary ---------------------------------
    canary = {}
    y = np.zeros(len(ridge_pts), int)     # AUC over ridge pixels is not the canary;
    # the canary is over a balanced sample of the whole scored domain
    rng = np.random.default_rng(58)
    for f in folds:
        truth_pts = np.argwhere(f.withhold)
        bg = np.argwhere(f.valid & ~f.known & ~f.withhold)
        bg = bg[rng.choice(len(bg), size=min(len(bg), 20 * len(truth_pts)), replace=False)]
        sample = np.vstack([truth_pts, bg])
        lab = np.r_[np.ones(len(truth_pts)), np.zeros(len(bg))]
        mag_s = field["mag"][sample[:, 0], sample[:, 1]]
        canary.setdefault("combined_ridge_field", []).append(
            float(roc_auc_score(lab, mag_s)) if np.ptp(mag_s) else 0.5)
        code_s = field["code"][sample[:, 0], sample[:, 1]]
        for fam, bands in FEAT.FAMILIES.items():
            codes_fam = {i + 1 for i, c in enumerate(field["codes"]) if c["band"] in bands}
            x = np.isin(code_s, list(codes_fam)).astype(float) + mag_s
            if np.ptp(x):
                canary.setdefault(f"family/{fam}", []).append(float(roc_auc_score(lab, x)))
    canary_out = {k: dict(auc_mean=float(np.mean(v)), auc_max=float(np.max(v)), n_folds=len(v),
                          leaks=bool(np.max(v) > 0.90)) for k, v in canary.items()}
    print(f"[canary] max AUC over features/folds = "
          f"{max(v['auc_max'] for v in canary_out.values()):.4f} "
          f"(limit 0.90); leaking = {any(v['leaks'] for v in canary_out.values())}", flush=True)

    (evidence_dir() / "adaptive_sigma.json").write_text(json.dumps(dict(
        protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        cross_fitting="leave-one-block-out: the sigma table scoring fold b is fitted on the other three folds",
        threshold=args.threshold, n_segments=len(segs),
        ridge_pixels=int(ridge_mask.sum()),
        n_withheld_positives=int(sum(f.n_truth for f in folds)),
        sigma_table_all_folds=table_all,
        sigma_table_leave_one_block_out=table_loo,
        per_fold_matched_components={b: len(v) for b, v in per_fold_sigma.items()},
        credit_calibration=calib,
        calibration_edges=edges.tolist(),
        leakage_canary=canary_out,
        marginal_inclusion_bar=dict(dti0=args.dti0, alpha=metric.ALPHA,
                                    required_credit=metric.ALPHA * args.dti0,
                                    max_distance_px=metric.RADIUS_PX * (1 - metric.ALPHA * args.dti0),
                                    max_distance_m=100.0 * metric.RADIUS_PX * (1 - metric.ALPHA * args.dti0)),
        wall_seconds=round(time.time() - t0, 2)), indent=1, default=float) + "\n")
    print(f"[exp1] wrote adaptive_sigma.json ({time.time() - t0:.1f} s)", flush=True)

    # ---------------- EXP-2: equal-budget width contest -----------------------
    def sigma_of_factory(table_for_block):
        def sigma_of(s):
            code = max(s["codes"], key=lambda c: c["scale"]) if s["codes"] else {}
            band = code.get("band", "?")
            fam = next((k for k, v in FEAT.FAMILIES.items() if band in v), "other")
            blk = holdout.block_of(s["idx"].mean(axis=0))
            sig, which = SIGMA.sigma_for(fam, float(code.get("scale", 0.0)),
                                         int(code.get("sign", 0)), blk, table_for_block(blk))
            return sig, which, blk, fam
        return sigma_of

    # rank surface (computed once): calibrated expected kernel credit
    # k_hat(family, magnitude decile), tie-broken by the raw ridge magnitude so
    # the greedy order is deterministic and reproducible.
    fam_pix = np.array([fam_of_code.get(int(c), "other") for c in code_at])
    kk = np.array([calib.get(f"{fam_pix[i]}|q{dec[i]}",
                             calib.get(f"all|q{dec[i]}", {"mean_kernel_credit": 0.0})
                             )["mean_kernel_credit"] for i in range(len(dec))])
    rank_grid = np.zeros(field["mag"].shape, np.float64)
    rank_grid[ridge_pts[:, 0], ridge_pts[:, 1]] = kk
    rank_grid += 1e-6 * field["mag"]
    print(f"[rank] k_hat-sorted ridge pixels: max {kk.max():.4f} min {kk.min():.4f}", flush=True)

    plans_hist = {}
    arms = {}
    for name, tau in (("W1", args.threshold), ("W3", args.threshold),
                      ("AD", args.threshold), ("AD2", args.threshold2)):
        sg = segs_by_tau[tau]
        pred_by_fold = {}
        for f in folds:
            allowed = fp & ~f.known          # visible catalogue + 3 px buffer only
            if name == "W1":
                sup = ribbon_support(field, sg, lambda s: [0.0], allowed)
            elif name == "W3":
                sup = ribbon_support(field, sg, lambda s: [-6.0, -3.0, 0.0, 3.0, 6.0], allowed)
            else:
                tbl = table_loo[f.name]
                hist = {}
                sig_of = sigma_of_factory(lambda b, t=tbl: t)

                def offs(s, sig_of=sig_of, hist=hist):
                    sig, _which, _blk, _fam = sig_of(s)
                    pl = allocation.plan(sig, args.dti0, max_k=3)
                    hist[pl.n_lines] = hist.get(pl.n_lines, 0) + 1
                    return list(pl.offsets)
                sup = ribbon_support(field, sg, offs, allowed)
                plans_hist[f"{name}/{f.name}"] = hist
            kept, n = greedy_topk(sup, rank_grid, args.budget, MIN_SEP)
            pred_by_fold[f.name] = kept
            print(f"[arm {name}] fold {f.name}: support {int(sup.sum()):7d} kept {n:6d}", flush=True)
        arms[name] = pred_by_fold

    results = {k: evaluate(v, folds) for k, v in arms.items()}
    for k, v in results.items():
        print(f"[arm] {k:4s} HOLDOUT-DTI {v['pooled']:.6f} coverage {v['coverage']:.4f} "
              f"tp {v['agg']['tp']:8.1f} fp {v['agg']['fp']:9.1f} dots {v['agg']['n_dots']}", flush=True)

    base = results["W1"]
    deltas = {}
    for k in results:
        if k == "W1":
            continue
        a = np.array([results[k]["per_fold"][b] for b in holdout.BLOCKS])
        b_ = np.array([base["per_fold"][b] for b in holdout.BLOCKS])
        deltas[k] = dict(pooled_delta=float(results[k]["pooled"] - base["pooled"]),
                         per_fold_delta={b: float(results[k]["per_fold"][b] - base["per_fold"][b])
                                         for b in holdout.BLOCKS},
                         paired_bootstrap=metric.paired_bootstrap(a, b_, n_boot=8000, seed=58))
    # AD vs W3 (does adaptivity beat the uniform ribbon the prior file used?)
    a = np.array([results["AD"]["per_fold"][b] for b in holdout.BLOCKS])
    b_ = np.array([results["W3"]["per_fold"][b] for b in holdout.BLOCKS])
    deltas["AD_vs_W3"] = dict(pooled_delta=float(results["AD"]["pooled"] - results["W3"]["pooled"]),
                              paired_bootstrap=metric.paired_bootstrap(a, b_, n_boot=8000, seed=59))

    # ---------------- simulated gain per measured-sigma class ----------------
    class_gain = {}
    fold_rows = {f.name: np.argwhere(f.withhold).astype(np.float64) for f in folds}
    fold_dist = {f.name: cKDTree(np.vstack([s["idx"] for s in segs]).astype(np.float64))
                 .query(fold_rows[f.name], k=1, workers=-1)[0] for f in folds}
    for lo, hi in ((0.0, 0.5), (0.5, 1.5), (1.5, 2.5), (2.5, 3.0), (3.0, 6.0)):
        cls = {}
        for name in arms:
            tp = fpp = 0.0
            g = 0
            for f in folds:
                rows_f, d_f = fold_rows[f.name], fold_dist[f.name]
                sel = (d_f >= lo) & (d_f < hi)
                if not sel.any():
                    continue
                tm = np.zeros(field["mag"].shape, bool)
                tm[rows_f[sel, 0].astype(int), rows_f[sel, 1].astype(int)] = True
                r = metric.dti_binary(arms[name][f.name], tm, valid=fp, known=f.known)
                tp += r.tp
                fpp += r.fp
                g += r.n_truth
            den = tp + metric.ALPHA * fpp + metric.BETA * (g - tp) + metric.EPS
            cls[name] = dict(tp=tp, fp=fpp, n_truth=g, dti=(tp / den if g else 0.0))
        class_gain[f"sigma-{lo:g}-{hi:g}px"] = cls
        if cls["W1"]["n_truth"]:
            print(f"[class] sigma {lo:g}-{hi:g}px n={cls['W1']['n_truth']:6d} | "
                  + " ".join(f"{k} {v['dti']:.6f}" for k, v in cls.items())
                  + f" | AD-W1 {cls['AD']['dti'] - cls['W1']['dti']:+.6f}", flush=True)

    # catalogue-distance profile of each arm (a live-evidence covariate)
    prof = {}
    for name, pf in arms.items():
        for f in folds:
            m = pf[f.name]
            v = cat_d_all[m]
            if v.size == 0:
                continue
            key = f"{name}/{f.name}"
            prof[key] = dict(n=int(m.sum()), median_px=float(np.median(v)),
                             frac_le_3px=float((v <= 3).mean()), frac_le_10px=float((v <= 10).mean()))
    (evidence_dir() / "adaptive_arms.json").write_text(json.dumps(dict(
        protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        budget=args.budget, min_sep=MIN_SEP, thresholds=[args.threshold, args.threshold2],
        dti0=args.dti0, ranking="calibrated expected kernel credit k_hat(family, magnitude decile)",
        screen="visible catalogue + 3 px buffer only (leak-free; the withheld truth stays scoreable)",
        n_withheld_positives=int(sum(f.n_truth for f in folds)),
        results=results, deltas_vs_W1=deltas, plans_histogram=plans_hist,
        simulated_gain_per_sigma_class=class_gain,
        catalogue_distance_profile=prof,
        wall_seconds=round(time.time() - t0, 2)), indent=1, default=float) + "\n")
    print(f"[exp2] wrote adaptive_arms.json ({time.time() - t0:.1f} s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
