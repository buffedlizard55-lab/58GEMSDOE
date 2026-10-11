#!/usr/bin/env python3
"""Ribbon lane: sigma table, cross-fitted per-class line configuration, holdout DTI, submission.

Inputs : data/training_features.tif, data/labels.tif, data/sample_submission.tif (scripts/fetch_inputs.py)
Outputs: reports/ribbon_lane_report.json (sigma table, canary AUCs, holdout DTI + CI, baselines)
         docs/submissions/<name>.tif + .json (only if the surface uniqueness check passes)

Protocol implemented (see README "Ribbon lane"):
  * Holdout = hide-and-recover over four spatial blocks (quadrants by segment centroid).
    Withheld block W_k is scored; visible faults (other blocks) are masked pixel-exactly from
    scoring; a 5 px buffer around W_k is removed from the scored domain.
  * Candidate ridges come from geophysical bands only (never from the catalogue).
  * sigma(block, resolution, ridge type) = 68th percentile of |across-strike offset| between
    candidate-ridge pixels (<=10 px away) and their nearest withheld segment.
  * Line configurations per ridge class: single tight line, or 2/3 parallel lines with spacing
    1-3 px. Chosen per class by U = (1-0.2*DTI0)*TP - 0.2*DTI0*FP on the THREE calibration blocks,
    then scored on the held-out block (cross-fitting, so the score is never fit on its own truth).
  * Emitted dots are exactly 1.0; everything else in the footprint is 0; outside footprint NaN.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems58 import ribbon as R  # noqa: E402
from gems58.dti import dti_components, utility_U  # noqa: E402
from gems58.uniqueness import dot_overlap_within, rank_corr  # noqa: E402
from gems58.validate import validate  # noqa: E402

DATA = ROOT / "data"
REPORTS = ROOT / "reports"
SUBS = ROOT / "docs" / "submissions"
REG = Path("/tmp/registry")
BUF = 5          # px buffer removed around each withheld block
TILE = 8         # tile size (px) for bootstrap CIs
CONFIGS = {      # parallel-line offsets in px (spacing near the 3-px kernel radius)
    "single": [0],
    "pair2": [-2, 2],
    "pair3": [-3, 3],
    "triple1": [-1, 0, 1],
    "triple2": [-2, 0, 2],
    "triple3": [-3, 0, 3],
}
CLASSES = [("topo", "native"), ("topo", "coarse"), ("edge", "native"), ("edge", "coarse")]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 24), b""):
            h.update(c)
    return h.hexdigest()


def load_band(b: int) -> np.ndarray:
    with rasterio.open(DATA / "training_features.tif") as s:
        a = s.read(b).astype(np.float64)
    a[a < -1e38] = np.nan
    return a


def registry_check(final: np.ndarray, foot: np.ndarray, shape) -> list[dict]:
    """Compare the final dots against every registry raster on the same grid (see uniqueness.py)."""
    import json as _json
    idx = _json.loads((REG / "index.json").read_text())
    seen, rows = set(), []
    for r in idx:
        if r["sha"] in seen:
            continue
        seen.add(r["sha"])
        p = REG / "blobs" / f"{r['sha']}.tif"
        if not p.exists():
            continue
        with rasterio.open(p) as s:
            if (s.height, s.width) != shape:
                continue
            a = s.read(1).astype(np.float64)
        a[~np.isfinite(a)] = np.nan
        pos = np.nan_to_num(a, nan=0.0) > 0
        rho = rank_corr(np.where(foot, np.nan_to_num(a, nan=0.0), np.nan), np.where(foot, np.where(final, 1.0, 0.0), np.nan))
        rows.append(dict(repo=r["repo"], path=r["path"], sha=r["sha"][:12],
                         spearman=None if np.isnan(rho) else round(rho, 4),
                         dots_within_3px=round(dot_overlap_within(final, pos & foot), 4)))
    return rows


def write_submission(final, foot, tf, crs, report):
    """Write the GeoTIFF (float32, EPSG:32611, template grid, NaN outside footprint) + audit JSON."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    arr = np.where(foot, np.where(final, 1.0, 0.0), np.nan).astype(np.float32)
    digest = hashlib.sha256(arr.tobytes()).hexdigest()[:8]
    name = f"gems58-ribbon-sigmaband-{stamp}-{digest}"
    out = SUBS / f"{name}.tif"
    with rasterio.open(out, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype="float32", crs=crs, transform=tf, nodata=None, compress="deflate") as d:
        d.write(arr, 1)
    v = validate(out, DATA / "sample_submission.tif")
    audit = dict(name=name, file=out.name, sha256=sha256(out), bytes=out.stat().st_size,
                 validator=v, positive_dots=int(final.sum()),
                 note=f"Ribbon lane sigma-band dots; HOLDOUT-DTI {report['holdout']['pooled_dti']:.4f} "
                      f"(local, not DrivenData). Not submitted.",
                 holdout_dti=report["holdout"]["pooled_dti"], holdout_ci95=report["holdout"]["pooled_dti_ci95_tile_bootstrap"])
    (SUBS / f"{name}.json").write_text(json.dumps(audit, indent=1))
    log("WROTE", out.name, "valid:", v["checks"]["all_checks_passed"])
    report["submission"] = audit
    (REPORTS / "ribbon_lane_report.json").write_text(json.dumps(report, indent=1))


def main() -> int:
    t0 = time.time()
    REPORTS.mkdir(exist_ok=True)
    SUBS.mkdir(parents=True, exist_ok=True)
    with rasterio.open(DATA / "labels.tif") as s:
        L = s.read(1)
        tf, crs = s.transform, s.crs
    foot = L != -1
    G0 = L == 1
    H, W = L.shape

    # ---- folds: quadrants by segment centroid -------------------------------------------
    seg_all, nseg = ndi.label(G0, structure=np.ones((3, 3)))
    ys, xs = np.nonzero(foot)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    cents = np.array(ndi.center_of_mass(G0, seg_all, range(1, nseg + 1)))
    qseg = np.where(cents[:, 0] < cy, np.where(cents[:, 1] < cx, 0, 1), np.where(cents[:, 1] < cx, 2, 3))
    qmap = np.full(nseg + 1, -1)
    qmap[1:] = qseg
    seg_q = qmap[seg_all]  # per-pixel block id (-1 = not a fault)
    fold_name = ["NW", "NE", "SW", "SE"]  # rows<cy = north; cols<cx = west
    folds = []
    for k in range(4):
        Wk = G0 & (seg_q == k)
        seg_k, _ = ndi.label(Wk, structure=np.ones((3, 3)))
        buf = ndi.binary_dilation(Wk, iterations=BUF) & ~Wk
        valid = foot & ~buf
        known = G0 & ~Wk & valid  # visible faults, masked pixel-exactly
        folds.append(dict(k=k, name=fold_name[k], W=Wk, seg=seg_k, valid=valid, known=known,
                          n_truth=int(Wk.sum()), n_segments=int(seg_k.max())))
        log(f"fold {k} {fold_name[k]}: withheld px={Wk.sum()} segments={seg_k.max()} "
            f"valid px={valid.sum()} visible-known px={known.sum()}")

    # ---- per-class candidate ridges + sigma table ----------------------------------------
    rng = np.random.default_rng(0)
    classes = {}
    sigma_table = []
    for rtype, res in CLASSES:
        band = {"topo": 12, "edge": 3}[rtype]
        b = load_band(band)
        score = R.ridge_score(b, foot, rtype, res)
        skel = R.candidate_ridges(score, foot, top_frac=0.03)
        nx, ny = R.across_strike_normals(score, foot)
        nx = nx.astype(np.float32)
        ny = ny.astype(np.float32)
        classes[(rtype, res)] = dict(skel=skel, nx=nx, ny=ny, band=band)
        # random null with the same number of candidate pixels, placed inside footprint
        fy, fx = np.nonzero(foot)
        pick = rng.choice(fy.size, int(skel.sum()), replace=False)
        null = np.zeros((H, W), bool)
        null[fy[pick], fx[pick]] = True
        for f in folds:
            off, dd = R.across_strike_offsets(f["W"], f["seg"], skel, foot)
            offn, _ = R.across_strike_offsets(f["W"], f["seg"], null, foot)
            row = dict(ridge_type=rtype, resolution=res, block=f["name"], n_pairs=int(off.size),
                       sigma68=float(np.quantile(np.abs(off), 0.68)) if off.size else None,
                       median_abs=float(np.median(np.abs(off))) if off.size else None,
                       null_sigma68=float(np.quantile(np.abs(offn), 0.68)) if offn.size else None)
            sigma_table.append(row)
            log("sigma", row)
        log(f"class {rtype}/{res}: skeleton px={int(skel.sum())}")
        del b, score

    # ---- feature canary: each feature alone, truth vs background, pooled over blocks -----
    canary = []
    truth_any = G0 & foot
    tidx = np.flatnonzero(truth_any.ravel())
    bidx = np.flatnonzero((foot & ~G0).ravel())
    rng2 = np.random.default_rng(1)
    bidx = rng2.choice(bidx, min(300_000, bidx.size), replace=False)
    sel = np.concatenate([tidx, bidx])
    lab = np.concatenate([np.ones(tidx.size), np.zeros(bidx.size)])
    with rasterio.open(DATA / "training_features.tif") as s:
        names = [s.tags(i).get("description", f"band{i}") for i in range(1, s.count + 1)]
    for bnd in range(1, 20):
        a = load_band(bnd).ravel()[sel]
        a = np.where(np.isfinite(a), a, np.nanmedian(a))
        r = rankdata(a)
        n1, n0 = tidx.size, bidx.size
        auc = (r[lab == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
        canary.append(dict(feature=f"band{bnd}", description=names[bnd - 1][:70], auc=round(float(auc), 4)))
    for (rtype, res), c in classes.items():
        sc = R.ridge_score(load_band(c["band"]), foot, rtype, res).ravel()[sel]
        r = rankdata(sc)
        n1, n0 = tidx.size, bidx.size
        auc = (r[lab == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
        canary.append(dict(feature=f"ridge:{rtype}/{res}", description="candidate ridge score (geophysics only)",
                           auc=round(float(auc), 4)))
    log("canary max AUC", max(c["auc"] for c in canary))

    # ---- candidate configurations per class; per-fold exact components ---------------------
    cfg_names = list(CONFIGS)
    emis = {}
    for key, c in classes.items():
        for cfg in cfg_names:
            emis[(key, cfg)] = R.emit_parallel(c["skel"], c["nx"], c["ny"], CONFIGS[cfg], foot)
    log("emissions built", len(emis), "time", round(time.time() - t0))

    comp = {}  # (class,cfg,fold) -> dict(tp, fp, n)
    for key in classes:
        for cfg in cfg_names:
            for f in folds:
                _, _, _, s = dti_components(emis[(key, cfg)], f["W"], valid=f["valid"], known=f["known"])
                comp[(key, cfg, f["k"])] = s
        log("class", key, "components done", round(time.time() - t0))

    # ---- cross-fitted selection: choose config per class on 3 calibration blocks ----------
    def agg(keys, blocks):
        tp = sum(comp[(k[0], k[1], b)]["tp"] for k in keys for b in blocks)
        fp = sum(comp[(k[0], k[1], b)]["fp"] for k in keys for b in blocks)
        return tp, fp

    chosen_cv = {}   # held-out block -> {class: cfg}
    cv_rows = []
    for f in folds:
        cal = [g["k"] for g in folds if g["k"] != f["k"]]
        choice = {}
        for key in classes:
            tp_s, fp_s = agg([(key, "single")], cal)
            n_cal = sum(comp[(key, "single", b)]["n_truth"] for b in cal)
            d0 = tp_s / (0.2 * (tp_s + fp_s) + 0.8 * n_cal) if n_cal else 0.0
            scores = {}
            for cfg in cfg_names:
                tp, fp = agg([(key, cfg)], cal)
                scores[cfg] = utility_U(tp, fp, d0)
            best = max(scores, key=scores.get)
            choice[key] = best
            cv_rows.append(dict(held_out=f["name"], ridge_type=key[0], resolution=key[1], chosen=best,
                                U_by_config={k: round(v, 3) for k, v in scores.items()}, dti0_calibration=round(d0, 5)))
        chosen_cv[f["k"]] = choice
        log("held-out", f["name"], "chosen", {f"{k[0]}/{k[1]}": v for k, v in choice.items()})

    # ---- union emission per held-out block and exact test scoring --------------------------
    def union_for(choice):
        u = np.zeros((H, W), bool)
        for key, cfg in choice.items():
            u |= emis[(key, cfg)]
        return u

    tile_id = (np.arange(H)[:, None] // TILE) * ((W + TILE - 1) // TILE) + (np.arange(W)[None, :] // TILE)
    n_tiles = int(tile_id.max()) + 1
    cv_tp = cv_fp = cv_n = 0.0
    tile_stats = np.zeros((n_tiles, 3))  # tp, fp, n per tile (pooled across held-out blocks)
    per_block = []
    baselines = {"all_ones_in_domain": [], "null_union_same_size": []}
    for f in folds:
        u = union_for(chosen_cv[f["k"]])
        tpm, fpm, gm, s = dti_components(u, f["W"], valid=f["valid"], known=f["known"])
        cv_tp += s["tp"]
        cv_fp += s["fp"]
        cv_n += s["n_truth"]
        tid = tile_id.ravel()
        tile_stats[:, 0] += np.bincount(tid, weights=tpm.ravel(), minlength=n_tiles)
        tile_stats[:, 1] += np.bincount(tid, weights=fpm.ravel(), minlength=n_tiles)
        tile_stats[:, 2] += np.bincount(tid, weights=gm.ravel().astype(float), minlength=n_tiles)
        del tpm, fpm, gm
        ones = f["valid"].copy()
        bl = dti_components(ones, f["W"], valid=f["valid"], known=f["known"])[3]
        baselines["all_ones_in_domain"].append(dict(block=f["name"], dti=round(bl["dti"], 5), tp=bl["tp"], fp=bl["fp"]))
        # null: same number of dots placed uniformly in the footprint
        nd = int(u.sum())
        fy, fx = np.nonzero(f["valid"])
        pick = np.random.default_rng(7 + f["k"]).choice(fy.size, nd, replace=False)
        nul = np.zeros((H, W), bool)
        nul[fy[pick], fx[pick]] = True
        ns = dti_components(nul, f["W"], valid=f["valid"], known=f["known"])[3]
        baselines["null_union_same_size"].append(dict(block=f["name"], dti=round(ns["dti"], 5), tp=ns["tp"], fp=ns["fp"]))
        per_block.append(dict(block=f["name"], dti=round(s["dti"], 5), tp=round(s["tp"], 3), fp=round(s["fp"], 3),
                              n_truth=s["n_truth"], dots=nd,
                              config={f"{k[0]}/{k[1]}": v for k, v in chosen_cv[f["k"]].items()}))
        log("test", per_block[-1])
    pooled = cv_tp / (0.2 * (cv_tp + cv_fp) + 0.8 * cv_n)
    # tile bootstrap (over pooled tiles) for a 95% CI
    rng3 = np.random.default_rng(11)
    tps, fps, ns_ = tile_stats[:, 0], tile_stats[:, 1], tile_stats[:, 2]
    boots = []
    for _ in range(2000):
        idx = rng3.integers(0, n_tiles, n_tiles)
        tp, fp, n = tps[idx].sum(), fps[idx].sum(), ns_[idx].sum()
        boots.append(tp / (0.2 * (tp + fp) + 0.8 * n) if n else 0.0)
    ci = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]

    # ---- final submission emission: selection on ALL four blocks ---------------------------
    final_choice = {}
    for key in classes:
        scores = {}
        tp_all = {cfg: sum(comp[(key, cfg, b)]["tp"] for b in range(4)) for cfg in cfg_names}
        fp_all = {cfg: sum(comp[(key, cfg, b)]["fp"] for b in range(4)) for cfg in cfg_names}
        n_all = sum(comp[(key, "single", b)]["n_truth"] for b in range(4))
        d0 = tp_all["single"] / (0.2 * (tp_all["single"] + fp_all["single"]) + 0.8 * n_all)
        for cfg in cfg_names:
            scores[cfg] = utility_U(tp_all[cfg], fp_all[cfg], d0)
        final_choice[key] = max(scores, key=scores.get)
    final = union_for(final_choice)

    report = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        lane="ribbon (parallel dotted lines, sigma-scaled emission width)",
        metric=dict(alpha=0.2, beta=0.8, radius_px=3, evaluator="gems58.dti (exact, cross-checked vs brute force in tests/test_dti.py)",
                    evidence_class="HOLDOUT-DTI (local hide-and-recover; not the DrivenData score)"),
        holdout=dict(scheme="4 spatial blocks by segment centroid; withheld block scored; visible faults masked; 5 px buffer",
                     withheld_positives_total=int(cv_n), pooled_dti=round(pooled, 5),
                     pooled_dti_ci95_tile_bootstrap=[round(ci[0], 5), round(ci[1], 5)],
                     bootstrap="2000 resamples of 8x8 px tiles", per_block=per_block,
                     baselines=baselines),
        sigma_table=sigma_table,
        selection_cv=cv_rows,
        final_config_on_all_blocks={f"{k[0]}/{k[1]}": v for k, v in final_choice.items()},
        canary=canary,
        canary_max_auc=max(c["auc"] for c in canary),
        registry_check={},
        runtime_s=round(time.time() - t0),
    )
    (REPORTS / "ribbon_lane_report.json").write_text(json.dumps(report, indent=1))
    # ---- surface uniqueness check on the FINAL dots, before anything is written -----------
    reg_rows = registry_check(final, foot, L.shape)
    max_rho = max((r["spearman"] for r in reg_rows if r["spearman"] is not None), default=None)
    max_ovl = max((r["dots_within_3px"] for r in reg_rows), default=0.0)
    worst = max(reg_rows, key=lambda r: r["dots_within_3px"]) if reg_rows else None
    passed = (max_rho is not None and max_rho < 0.90) and (max_ovl <= 0.70)
    report["registry_check"] = dict(n_registry_rasters_compared=len(reg_rows),
                                    max_spearman=max_rho, max_dot_overlap_within_3px=max_ovl,
                                    worst_match=worst, pass_thresholds=dict(spearman_lt=0.90, overlap_le=0.70),
                                    passed=bool(passed))
    log("registry check", {k: report["registry_check"][k] for k in ("n_registry_rasters_compared", "max_spearman", "max_dot_overlap_within_3px", "passed")})
    log("holdout pooled DTI", round(pooled, 5), "CI", ci, "withheld positives", int(cv_n))
    log("final config", report["final_config_on_all_blocks"])
    if passed:
        write_submission(final, foot, tf, crs, report)
    else:
        log("NOT WRITTEN: uniqueness check failed -> logged as lane drift / duplicate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
