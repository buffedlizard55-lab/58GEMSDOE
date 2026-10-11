#!/usr/bin/env python3
"""EXP-1: leakage canary, localization-error (sigma) table and equal-budget check.

Protocol items implemented here:

* **Leakage canary** -- every feature family is scored *alone* against the
  withheld truth of the shared buffered hide-and-recover holdout
  (``gems57.holdout.build_buffered_holdout_context``).  AUC > 0.90 would mean
  leakage; the field never reads the catalogue, so the canary is meaningful.
* **sigma table** -- the across-strike distance from each candidate lineament to
  the nearest withheld segment, stratified by *spatial block* (the four
  quadrants), *feature resolution* (winning structure-tensor scale) and *ridge
  type* (winning physical family).  This is the measured localization error the
  ribbon width must be calibrated to.
* **Equal-budget precision** -- of the top-N ranked candidates, the fraction
  within 1 / 3 px of withheld truth and the mean exact kernel credit, for the
  convergence ranking and for each single family alone.

Nothing here selects or scores an emission; this is instrument calibration.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import load_grid                                   # noqa: E402
from gems57.holdout import build_buffered_holdout_context           # noqa: E402
from gems57.metric import kernel                                    # noqa: E402
from gems60 import convergence as C                                 # noqa: E402

CACHE = Path.home() / ".cache" / "gems" / "gems60_convergence.npz"
EVID = ROOT / "evidence" / "gems60"
TOPN = 40000
CAPTURE_PX = 6.0          # candidates farther than this from withheld truth are
                          # "unassociated": they are counted, but do not define sigma


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank AUC with ties averaged (Mann-Whitney U / (n1*n2))."""
    s = np.asarray(scores, np.float64)
    y = np.asarray(labels, bool)
    n1 = int(y.sum())
    n0 = int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="stable")
    r = np.empty(s.size, np.float64)
    r[order] = np.arange(1, s.size + 1, dtype=np.float64)
    # average ties
    sv = s[order]
    i = 0
    while i < sv.size:
        j = i + 1
        while j < sv.size and sv[j] == sv[i]:
            j += 1
        if j - i > 1:
            r[order[i:j]] = r[order[i:j]].mean()
        i = j
    return float((r[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20)
    ap.add_argument("--sample", type=int, default=300000)
    ap.add_argument("--topn", type=int, default=TOPN)
    ap.add_argument("--out", default=str(EVID / "sigma.json"))
    args = ap.parse_args()

    t0 = time.time()
    grid = load_grid(ROOT / "data" / "bridge")
    conv = C.load(CACHE)
    ctx = build_buffered_holdout_context(grid, seeds=(args.seed,))
    print(f"holdout : {len(ctx.cells)} cells, seed {args.seed} ({time.time() - t0:.1f}s)")

    rng = np.random.default_rng(1234)
    canary, sigma_rows, budget_rows = {}, [], []
    for cell in ctx.cells:
        sl = cell.bbox
        active = cell.active
        truth = np.zeros(active.shape, bool)
        truth[cell.truth_yx] = True
        hidden_full = ctx.hidden_by_cell[cell.key]
        hidden = hidden_full[sl]
        dist_hidden = ndi.distance_transform_edt(~hidden)

        # ---- canary: each family's own strength surface, alone -------------
        sub = dict(score=conv.score[sl], strength=conv.strength[sl],
                   fam_ix=conv.fam_ix[sl], scale_ix=conv.scale_ix[sl])
        n_act = int(active.sum())
        take = min(args.sample, n_act)
        ys, xs = np.nonzero(active)
        pick = rng.choice(ys.size, take, replace=False)
        py, px = ys[pick], xs[pick]
        lab = truth[py, px]
        base = auc(sub["strength"][py, px], lab)
        canary.setdefault("overall_binomial_auc", []).append(base)
        for fi, fam in enumerate(conv.families):
            m = sub["fam_ix"][py, px] == fi
            if m.sum() > 1000:
                canary.setdefault(f"family_{fam}", []).append(
                    auc(sub["strength"][py, px][m], lab[m]))
        canary.setdefault("families_agreeing", []).append(
            auc(sub["score"][py, px].astype(np.float64), lab))

        # ---- sigma table: candidates that are actually associated ----------
        cand = active & (sub["score"] >= 2) & (sub["strength"] > 0)
        cy, cx = np.nonzero(cand)
        if cy.size:
            d = dist_hidden[cy, cx]
            assoc = d <= CAPTURE_PX
            for fi, fam in enumerate(conv.families):
                for si, sc in enumerate(conv.scales):
                    m = assoc & (sub["fam_ix"][cy, cx] == fi) & (sub["scale_ix"][cy, cx] == si)
                    if m.sum() >= 50:
                        sigma_rows.append(dict(
                            fold=cell.key, family=fam, scale_px=sc, n=int(m.sum()),
                            sigma_median_px=float(np.median(d[m])),
                            sigma_p25_px=float(np.percentile(d[m], 25)),
                            sigma_p75_px=float(np.percentile(d[m], 75)),
                            frac_within_1px=float((d[m] <= 1).mean()),
                            frac_within_3px=float((d[m] <= 3).mean())))
            for fi, fam in enumerate(conv.families):
                m = assoc & (sub["fam_ix"][cy, cx] == fi)
                if m.sum() >= 50:
                    sigma_rows.append(dict(
                        fold=cell.key, family=fam, scale_px=None, n=int(m.sum()),
                        sigma_median_px=float(np.median(d[m])),
                        sigma_p25_px=float(np.percentile(d[m], 25)),
                        sigma_p75_px=float(np.percentile(d[m], 75)),
                        frac_within_1px=float((d[m] <= 1).mean()),
                        frac_within_3px=float((d[m] <= 3).mean())))
            sigma_rows.append(dict(
                fold=cell.key, family="all", scale_px=None, n=int(cy.size),
                capture_rate_within_6px=float(assoc.mean()),
                frac_within_1px=float((d <= 1).mean()), frac_within_3px=float((d <= 3).mean()),
                sigma_median_px=float(np.median(d[assoc])) if assoc.any() else None,
                sigma_p25_px=float(np.percentile(d[assoc], 25)) if assoc.any() else None,
                sigma_p75_px=float(np.percentile(d[assoc], 75)) if assoc.any() else None))

        # ---- equal-budget precision: convergence vs each single family -----
        order_all = np.argsort(-sub["strength"][py, px], kind="stable")
        k = min(args.topn, order_all.size)
        rows = [("all_families_strength", order_all[:k])]
        for fi, fam in enumerate(conv.families):
            m = sub["fam_ix"][py, px] == fi
            if m.sum() >= 200:
                idx = np.flatnonzero(m)
                rows.append((f"family_{fam}", idx[np.argsort(-sub["strength"][py, px][idx])[:k]]))
        for name, idx in rows:
            pyy, pxx = py[idx], px[idx]
            dd = dist_hidden[pyy, pxx]
            budget_rows.append(dict(
                fold=cell.key, ranking=name, n=int(idx.size),
                frac_within_1px=float((dd <= 1).mean()), frac_within_2px=float((dd <= 2).mean()),
                frac_within_3px=float((dd <= 3).mean()),
                mean_kernel_credit=float(kernel(dd).mean()),
                score_ge2_frac=float((sub["score"][pyy, pxx] >= 2).mean())))

    summary = dict(
        evidence_class="HOLDOUT-CALIBRATION",
        protocol="gems60-convergence-sigma-v1",
        evaluator_version="gems57.metric (kernel-only AUC/precision; no DTI claimed here)",
        holdout="gems57.holdout.build_buffered_holdout_context",
        seed=args.seed,
        withheld_positive_pixels=int(sum(c.n_truth for c in ctx.cells)),
        cache=str(CACHE),
        families=list(conv.families), scales=list(conv.scales),
        canary=canary, sigma=sigma_rows, equal_budget=budget_rows,
        capture_radius_px=CAPTURE_PX,
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(summary, indent=1, default=str) + "\n")
        print("wrote:", args.out)

    # ---- human-readable receipts -------------------------------------------
    print("\nLEAKAGE CANARY (AUC of one feature alone vs withheld truth; >0.90 = leakage)")
    for k2, v in canary.items():
        a = np.array([x for x in v if np.isfinite(x)])
        if a.size:
            print(f"  {k2:24s} mean AUC {a.mean():.4f}  (n={a.size})")

    print("\nSIGMA TABLE (across-strike distance to nearest withheld segment, associated candidates)")
    print(f"  {'fold':28s} {'family':12s} {'scale':>5s} {'n':>7s} {'p25':>5s} {'med':>5s} {'p75':>5s} {'<=1px':>6s} {'<=3px':>6s}")
    for r in sigma_rows:
        sc = "-" if r.get("scale_px") is None else f"{r['scale_px']:.1f}"
        med = "-" if r.get("sigma_median_px") is None else f"{r['sigma_median_px']:.2f}"
        p25 = "-" if r.get("sigma_p25_px") is None else f"{r['sigma_p25_px']:.2f}"
        p75 = "-" if r.get("sigma_p75_px") is None else f"{r['sigma_p75_px']:.2f}"
        print(f"  {r['fold']:28s} {r['family']:12s} {sc:>5s} {r['n']:>7d} {p25:>5s} {med:>5s} {p75:>5s} "
              f"{r.get('frac_within_1px', float('nan')):6.3f} {r.get('frac_within_3px', float('nan')):6.3f}")

    print("\nEQUAL-BUDGET PRECISION (top candidates by each ranking, vs withheld truth)")
    print(f"  {'ranking':24s} {'n':>7s} {'<=1px':>6s} {'<=2px':>6s} {'<=3px':>6s} {'mean credit':>11s}")
    agg: dict[str, list] = {}
    for r in budget_rows:
        agg.setdefault(r["ranking"], []).append(r)
    for name, rs in agg.items():
        n = sum(r["n"] for r in rs)
        w = lambda key: sum(r[key] * r["n"] for r in rs) / max(1, n)   # noqa: E731
        print(f"  {name:24s} {n:>7d} {w('frac_within_1px'):6.3f} {w('frac_within_2px'):6.3f} "
              f"{w('frac_within_3px'):6.3f} {w('mean_kernel_credit'):11.4f}")
    print(f"\ndone in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
