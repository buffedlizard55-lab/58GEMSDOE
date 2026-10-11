#!/usr/bin/env python3
"""Uniqueness gate for the ribbon lane: pick the best pre-specified line configuration that passes.

Why this exists: scripts/run_ribbon_lane.py chose triple3 (+-3 px lines) by U on calibration blocks.
Its surface check against the 682 unique registry rasters FAILED (13GEMSDOE r13-lattice-s5: 99.7 % of
dots within 3 px of that raster's dots). Protocol: log as duplicate. This script re-evaluates ALL
five configurations (same lane, same candidate ridges) under two gates, then keeps the best one that
passes both:
  Gate A (holdout): pooled DTI on the four hide-and-recover blocks (exact metric, same as the pipeline).
  Gate B (uniqueness): Spearman < 0.90 AND dots within 3 px of any single registry raster <= 70 %.
    Overlap is only defined for rasters whose positive set is a dot set (<= 50 % of the footprint);
    continuous rasters (positive almost everywhere) are excluded from the overlap test, not passed.
Multiple-selection note: 5 configs x 682 rasters were checked; the report states this.

Writes: reports/ribbon_lane_report.json (adds config_selection + registry sections) and, only if a
config passes, docs/submissions/<name>.tif + .json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "src"))
from run_ribbon_lane import CONFIGS, CLASSES, REG, DATA, REPORTS, SUBS, BUF, log, sha256  # noqa: E402
from gems58 import ribbon as R  # noqa: E402
from gems58.dti import dti_components  # noqa: E402
from gems58.uniqueness import dot_overlap_within, rank_corr  # noqa: E402
from gems58.validate import validate  # noqa: E402


def main() -> int:
    t0 = time.time()
    with rasterio.open(DATA / "labels.tif") as s:
        L = s.read(1)
        tf, crs = s.transform, s.crs
    foot = L != -1
    G0 = L == 1
    H, W = L.shape
    from scipy import ndimage as ndi
    seg_all, nseg = ndi.label(G0, structure=np.ones((3, 3)))
    ys, xs = np.nonzero(foot)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    cents = np.array(ndi.center_of_mass(G0, seg_all, range(1, nseg + 1)))
    qseg = np.where(cents[:, 0] < cy, np.where(cents[:, 1] < cx, 0, 1), np.where(cents[:, 1] < cx, 2, 3))
    qmap = np.full(nseg + 1, -1)
    qmap[1:] = qseg
    seg_q = qmap[seg_all]
    names = ["NW", "NE", "SW", "SE"]
    folds = []
    for k in range(4):
        Wk = G0 & (seg_q == k)
        buf = ndi.binary_dilation(Wk, iterations=BUF) & ~Wk
        valid = foot & ~buf
        known = G0 & ~Wk & valid
        folds.append(dict(k=k, name=names[k], W=Wk, valid=valid, known=known))

    # union dots per configuration (same candidate ridges for all configurations)
    union = {cfg: np.zeros((H, W), bool) for cfg in CONFIGS}
    for rtype, res in CLASSES:
        band = {"topo": 12, "edge": 3}[rtype]
        with rasterio.open(DATA / "training_features.tif") as s:
            b = s.read(band).astype(np.float64)
        b[b < -1e38] = np.nan
        sc = R.ridge_score(b, foot, rtype, res)
        sk = R.candidate_ridges(sc, foot, top_frac=0.03)
        nx, ny = R.across_strike_normals(sc, foot)
        for cfg, offs in CONFIGS.items():
            union[cfg] |= R.emit_parallel(sk, nx, ny, offs, foot)
        del b, sc, nx, ny
        log("class", rtype, res, "added")
    log("dot counts", {c: int(v.sum()) for c, v in union.items()})

    # Gate A: holdout pooled DTI per configuration
    holdout = {}
    for cfg, dots in union.items():
        tp = fp = n = 0.0
        blocks = []
        for f in folds:
            _, _, _, s = dti_components(dots, f["W"], valid=f["valid"], known=f["known"])
            tp += s["tp"]
            fp += s["fp"]
            n += s["n_truth"]
            blocks.append(dict(block=f["name"], dti=round(s["dti"], 5)))
        pooled = tp / (0.2 * (tp + fp) + 0.8 * n)
        holdout[cfg] = dict(pooled_dti=round(float(pooled), 5), tp=round(tp, 3), fp=round(fp, 3),
                            withheld_positives=int(n), per_block=blocks, dots=int(dots.sum()))
        log("holdout", cfg, holdout[cfg]["pooled_dti"], "dots", holdout[cfg]["dots"])

    # Gate B: registry check, every unique raster loaded once, all configurations at once
    idx = json.loads((REG / "index.json").read_text())
    seen = set()
    rows = {cfg: [] for cfg in CONFIGS}
    n_foot = int(foot.sum())
    # Fixed Spearman sample over the footprint (same seed/size as rank_corr; reg is finite on the footprint)
    from scipy.stats import spearmanr
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(0)
    foot_idx = np.flatnonzero(foot.ravel())
    samp = rng.choice(foot_idx, 300_000, replace=False) if foot_idx.size > 300_000 else foot_idx
    cand_s = {cfg: np.where(union[cfg], 1.0, 0.0).ravel()[samp] for cfg in CONFIGS}
    cand_trees = {}
    for r in idx:
        if r["sha"] in seen:
            continue
        seen.add(r["sha"])
        p = REG / "blobs" / f"{r['sha']}.tif"
        with rasterio.open(p) as s:
            if (s.height, s.width) != (H, W):
                continue
            a = s.read(1).astype(np.float64)
        a = np.nan_to_num(a, nan=0.0)
        pos = (a > 0) & foot
        dot_set = pos.sum() <= 0.5 * n_foot
        reg_s = a.ravel()[samp]
        reg_tree = cKDTree(np.column_stack(np.nonzero(pos))) if dot_set and pos.any() else None
        for cfg in CONFIGS:
            rho = float(spearmanr(cand_s[cfg], reg_s).statistic)
            ovl = None
            if dot_set:
                if reg_tree is None or not union[cfg].any():
                    ovl = 0.0
                else:
                    cy, cx = np.nonzero(union[cfg])
                    d, _ = reg_tree.query(np.column_stack([cy, cx]), distance_upper_bound=3.0 + 1e-9)
                    ovl = float(np.mean(np.isfinite(d) & (d <= 3.0)))
            rows[cfg].append(dict(repo=r["repo"], path=r["path"], sha=r["sha"][:12],
                                  spearman=None if np.isnan(rho) else round(rho, 4),
                                  dot_overlap_3px=None if ovl is None else round(ovl, 4),
                                  positives=int(pos.sum())))
        if len(seen) % 100 == 0:
            log("registry rasters checked", len(seen))

    selection = {}
    for cfg in CONFIGS:
        rr = rows[cfg]
        rhos = [x["spearman"] for x in rr if x["spearman"] is not None]
        ovs = [x for x in rr if x["dot_overlap_3px"] is not None]
        max_rho = max(rhos) if rhos else None
        worst_ov = max(ovs, key=lambda x: x["dot_overlap_3px"]) if ovs else None
        n_ov70 = sum(1 for x in ovs if x["dot_overlap_3px"] > 0.70)
        passed = (max_rho is not None and max_rho < 0.90) and (worst_ov is None or worst_ov["dot_overlap_3px"] <= 0.70)
        selection[cfg] = dict(offsets_px=CONFIGS[cfg], holdout=holdout[cfg],
                              registry_rasters_compared=len(rr), dot_set_rasters=len(ovs),
                              max_spearman=max_rho, max_dot_overlap_3px=None if worst_ov is None else worst_ov["dot_overlap_3px"],
                              worst_match=worst_ov, rasters_over_70pct=n_ov70, passed_gate_B=bool(passed))
        log("gate B", cfg, "max_rho", max_rho, "max_overlap", selection[cfg]["max_dot_overlap_3px"],
            "over70", n_ov70, "PASS" if passed else "FAIL")
    eligible = [c for c in CONFIGS if selection[c]["passed_gate_B"]]
    chosen = max(eligible, key=lambda c: holdout[c]["pooled_dti"]) if eligible else None

    report_path = REPORTS / "ribbon_lane_report.json"
    report = json.loads(report_path.read_text())
    report["config_selection"] = dict(
        rule="best pooled holdout DTI among configurations that pass gate B (uniqueness)",
        multiple_selection_note=f"{len(CONFIGS)} configurations x {len(seen)} unique registry rasters were tested",
        configurations=selection, chosen=chosen,
        duplicate_log=[] if chosen else ["ALL configurations failed gate B: logged as lane drift / duplicate; no file written"],
    )
    if chosen is None:
        report["submission"] = None
        report_path.write_text(json.dumps(report, indent=1))
        log("NO CONFIGURATION PASSED. Nothing written.")
        return 0

    dots = union[chosen]
    arr = np.where(foot, np.where(dots, 1.0, 0.0), np.nan).astype(np.float32)
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = __import__("hashlib").sha256(arr.tobytes()).hexdigest()[:8]
    name = f"gems58-ribbon-{chosen}-{stamp}-{digest}"
    out = SUBS / f"{name}.tif"
    SUBS.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32",
                       crs=crs, transform=tf, nodata=None, compress="deflate") as d:
        d.write(arr, 1)
    v = validate(out, DATA / "sample_submission.tif")
    ho = holdout[chosen]
    audit = dict(name=name, file=out.name, sha256=sha256(out), bytes=out.stat().st_size, validator=v,
                 positive_dots=int(dots.sum()), config=chosen, offsets_px=CONFIGS[chosen],
                 holdout_dti=ho["pooled_dti"],
                 holdout_ci95_tile_bootstrap=report["holdout"]["pooled_dti_ci95_tile_bootstrap"]
                 if chosen == "triple3" else None,
                 evidence_class="HOLDOUT-DTI (local hide-and-recover; NOT the DrivenData score)",
                 note=f"Ribbon lane {chosen} dots; holdout DTI {ho['pooled_dti']:.4f} (local); not submitted")
    (SUBS / f"{name}.json").write_text(json.dumps(audit, indent=1))
    report["submission"] = audit
    report_path.write_text(json.dumps(report, indent=1))
    log("WROTE", out.name, "valid", v["checks"]["all_checks_passed"], "dots", int(dots.sum()))
    log("time", round(time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
