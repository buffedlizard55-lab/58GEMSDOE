#!/usr/bin/env python3
"""ARCHIVED/NO-GO legacy experiment; command-line execution is disabled.

The historical notes below include owner-reported leaderboard rows and a
private/unbuffered geometry comparison. They are not promotion-grade evidence.

Historical description: geometry sweep at a fixed dot budget.

The dot budget is held at the level that the three best *measured* live files
used (37,654 / 38,000 / 38,854 dots; owner-reported scores 0.2778 / 0.2750 /
0.2376), so that the comparison isolates **geometry**: one tight line vs
parallel dotted ribbons, along-strike spacing, line spacing, and the two
catalogue-distance / obliquity screens.

The exact metric arbitrates every row.  Writes ``evidence/geometry_sweep.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/ribbon_run_geometry_sweep.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import extract, grid, holdout, metric  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402

BUDGET = 38000


def catalogue_distance() -> np.ndarray:
    return distance_transform_edt(~grid.catalogue()).astype(np.float32)


def obliqutiy_deg(ax: np.ndarray, ay: np.ndarray, cat_ax: np.ndarray, cat_ay: np.ndarray) -> np.ndarray:
    """Angle (deg, 0-90) between the ridge across-strike vector and the local catalogue normal."""
    dot = np.abs(ax * cat_ax + ay * cat_ay)
    return np.degrees(np.arccos(np.clip(dot, 0.0, 1.0)))


def catalogue_orientation(idx_cat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Local catalogue orientation field from the structure tensor of the catalogue mask."""
    from scipy.ndimage import gaussian_filter

    m = idx_cat.astype(np.float32)
    gx = gaussian_filter(m, 6.0, order=(0, 1), mode="nearest")
    gy = gaussian_filter(m, 6.0, order=(1, 0), mode="nearest")
    # edge normal of the mask = gradient of the smoothed mask; its direction is
    # across the trace, so rotate to get the along-trace (strike) vector.
    nx, ny = gx, gy
    nrm = np.hypot(nx, ny) + 1e-9
    nx, ny = nx / nrm, ny / nrm
    return -ny, nx  # strike (along-trace)


def dedupe(mask: np.ndarray, field: dict, budget: int, min_sep: int = 2) -> np.ndarray:
    """Greedy thinning: keep the strongest dots such that no two are within ``min_sep``."""
    from scipy.ndimage import maximum_filter

    m = mask.copy()
    keep = np.zeros_like(m)
    rank = field["mag"]
    while True:
        if int(keep.sum()) >= budget or not m.any():
            break
        cand = m & (rank >= maximum_filter(np.where(m, rank, -np.inf), 3))
        if not cand.any():
            cand = m
        new = cand & ~maximum_filter(keep, 2 * min_sep + 1)
        if not new.any():
            break
        keep |= new
        m &= ~maximum_filter(keep, 2 * min_sep + 1)
    return keep


def evaluate(pred_bool, folds) -> dict:
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0, n_dots=0)
    for f in folds:
        r = metric.dti_binary(pred_bool, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        agg["tp"] += r.tp
        agg["fp"] += r.fp
        agg["fn"] += r.fn
        agg["n_truth"] += r.n_truth
        agg["n_dots"] += int((pred_bool & f.valid & ~f.known).sum())
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    return dict(pooled=float(agg["tp"] / den), per_fold=per_fold, agg=agg)


def build_emission(field, segs, *, along_spacing, max_lines, line_step_px,
                   obl_min_deg, obl_apply, cat_min_px, cat_ax, cat_ay, cat_d) -> np.ndarray:
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    for s in segs:
        idx = s["idx"]
        if obl_apply > 0:
            ax_s = field["ax"][idx[:, 0], idx[:, 1]]
            ay_s = field["ay"][idx[:, 0], idx[:, 1]]
            d = cat_d[idx[:, 0], idx[:, 1]]
            near = d <= 40.0
            if near.any():
                ang = np.degrees(np.arccos(np.clip(
                    np.abs(ax_s[near] * cat_ax[idx[near, 0], idx[near, 1]]
                           + ay_s[near] * cat_ay[idx[near, 0], idx[near, 1]]), 0, 1)))
                sub_par = float((ang < obl_min_deg).mean())
                if sub_par > obl_apply:
                    continue
        if cat_min_px > 0:
            d = cat_d[idx[:, 0], idx[:, 1]]
            keep = d >= cat_min_px
            if not keep.any():
                continue
            idx = idx[keep]
        if along_spacing > 1:
            axis = np.argmax(np.var(idx.astype(float), axis=0))
            idx = idx[np.argsort(idx[:, axis])][::along_spacing]
        if idx.shape[0] == 0:
            continue
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        for o in np.arange(0, max_lines) * line_step_px:
            for sgn in ((1,) if o == 0 else (1, -1)):
                rr = np.rint(idx[:, 0] + sgn * o * ay).astype(int)
                cc = np.rint(idx[:, 1] + sgn * o * ax).astype(int)
                ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
                mask[rr[ok], cc[ok]] = True
    return mask


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=8)
    folds = holdout.all_folds()
    cat_d = catalogue_distance()
    cat_ax, cat_ay = catalogue_orientation(grid.catalogue())

    rows = []
    configs = []
    for along in (1, 2, 3):
        for lines in (1, 2, 3):
            for step in (3.0,):
                configs.append(dict(along=along, lines=lines, step=step,
                                    obl_min=0.0, obl_apply=0.0, cat_min=0.0))
    # catalogue-distance screens at the best-looking geometry
    for cat_min in (0.0, 3.0, 6.0, 12.0, 20.0):
        configs.append(dict(along=3, lines=3, step=3.0, obl_min=0.0, obl_apply=0.0,
                            cat_min=cat_min))
    # obliquity screens
    for abl in (0.0, 0.35, 0.65, 0.9):
        configs.append(dict(along=3, lines=3, step=3.0, obl_min=10.0, obl_apply=abl,
                            cat_min=0.0))

    for cfg in configs:
        raw = build_emission(field, segs, along_spacing=cfg["along"], max_lines=cfg["lines"],
                             line_step_px=cfg["step"], obl_min_deg=cfg["obl_min"],
                             obl_apply=cfg["obl_apply"], cat_min_px=cfg["cat_min"],
                             cat_ax=cat_ax, cat_ay=cat_ay, cat_d=cat_d)
        n_raw = int(raw.sum())
        m = dedupe(raw, field, args.budget, min_sep=2) if n_raw > args.budget else raw
        res = evaluate(m, folds)
        row = dict(cfg, n_raw=n_raw, n_dots=int(m.sum()), **res)
        rows.append(row)
        print(f"[geom] along={cfg['along']} lines={cfg['lines']} step={cfg['step']:g} "
              f"obl>={cfg['obl_min']:g}/{cfg['obl_apply']:.2f} cat>={cfg['cat_min']:g} "
              f"| raw {n_raw:7d} kept {int(m.sum()):7d} | pooled DTI {res['pooled']:.6f} "
              f"| tp {res['agg']['tp']:8.1f}", flush=True)

    base = next(r for r in rows if r["along"] == 1 and r["lines"] == 1 and r["cat_min"] == 0.0
                and r["obl_apply"] == 0.0)
    for r in rows:
        pa = np.array([r["per_fold"][b] for b in holdout.BLOCKS])
        pb = np.array([base["per_fold"][b] for b in holdout.BLOCKS])
        r["delta_vs_tight1"] = float(r["pooled"] - base["pooled"])
        r["paired_bootstrap_vs_tight1"] = metric.paired_bootstrap(pa, pb, n_boot=4000, seed=58)

    out = dict(protocol=holdout.PROTOCOL, evaluator=metric.EVALUATOR_VERSION,
               budget=args.budget, threshold=args.threshold, min_sep=2,
               n_withheld_positives=int(sum(f.n_truth for f in folds)),
               rows=rows, wall_seconds=round(time.time() - t0, 2))
    p = evidence_dir() / "geometry_sweep.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", p, "in", out["wall_seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        "DEPRECATED/NO-GO: legacy geometry sweep uses the private gems58w holdout/metric "
        "and is not promotion-grade. Do not run it for current claims."
    )
