#!/usr/bin/env python3
"""E3: equal-budget ranking contest + the shipped, locally validated submission raster.

E2 (``scripts/run_model_experiments.py``) swept an absolute probability threshold. That is the wrong
instrument for two reasons, both measured: the CTX family's off-catalogue probabilities never reach 0.5,
so an absolute threshold emits nothing at all; and threshold sweeps compare arms at wildly different dot
counts, which ``evidence/sibling_record.json`` shows is the dominant variable. E3 therefore compares
rankings **at equal budget**: take the top-N pixels of each ranking, thin them with 3-px non-maximum
suppression (the 300 m kernel radius), and score with the shared exact evaluator.

Rankings compared (all live-computable, none sees withheld truth):
  ``GF``    -- geophysical operators only (19 GeoDAWN bands + 16 NaN-aware local operators).
  ``CTX``   -- GF plus distance to the visible catalogue.
  ``PROX``  -- the trivial strong baseline: rank by proximity to the visible catalogue alone. This is the
               mechanism behind the whole 0.24-0.28 cluster of the owner's own record, so a supervised
               ranking that cannot beat it at equal budget is a negative result and is reported as one.

Budget is expressed as nu = dots / withheld-truth pixels, because that ratio (not the absolute count) is
what transfers between the holdout and the real test. The shipped absolute count comes from the
owner-raster record, and the two together give an ESTIMATE of the real truth-set size.

Everything is packaged through ``gems57.submission_writer`` (fail-closed: refuses NaN, out-of-range
values, positive mass outside the footprint or on the mapped catalogue, and re-validates the bytes it
actually wrote before publishing).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import HEIGHT, WIDTH, load_grid        # noqa: E402
from gems57.holdout import (FOLD_NAMES, build_holdout,   # noqa: E402
                            quadrant_ids, score_cell)
from gems57.metric import ALPHA, BETA, EPS               # noqa: E402
from gems57.submission_writer import write_submission    # noqa: E402
from gems59.features import open_stack                   # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from run_model_experiments import (CACHE, MODES, NMS_RADIUS_PX, SEEDS,  # noqa: E402
                                   gf_cube, nms_dots, predict_grid,
                                   train_fold)

MAX_NAME = 140
NU_GRID = (0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.5, 7.0, 10.0)
# Off-catalogue buffer, in pixels. The scored domain excludes mapped fault pixels, so a dot inside the
# 300 m kernel of a mapped trace but far from any new fault is pure false-positive mass. Within the
# <=50k-dot budget of the owner-raster record the best-scoring rasters carry the least near-catalogue
# mass (evidence/sibling_record.json), so the buffer is swept rather than assumed.
BUFFER_GRID = (0, 2, 3, 4, 6)
SIBLING_BUDGET_DOTS = 40_000      # evidence/sibling_record.json: <=44,090 px out-scores every raster >50,000
FAMILIES = ("GF", "CTX", "PROX")

_PROB = {}


def prob_field(fam: str, fold: int) -> np.ndarray:
    key = (fam, fold)
    if key not in _PROB:
        _PROB[key] = np.memmap(CACHE / f"prob_{fam}_f{fold}.f32", dtype=np.float32,
                               mode="r", shape=(HEIGHT, WIDTH))
    return _PROB[key]


def rank_field(fam: str, cell, dvis_crop: np.ndarray) -> np.ndarray:
    """Higher-is-better ranking field, cropped to ``cell.bbox``."""
    if fam == "PROX":
        return -dvis_crop
    return np.asarray(prob_field(fam, cell.fold)[cell.bbox])


def pooled(scores):
    tp = sum(s["tp"] for s in scores); fp = sum(s["fp"] for s in scores)
    fn = sum(s["fn"] for s in scores); nt = sum(s["n_truth"] for s in scores)
    ne = sum(s["n_emitted"] for s in scores)
    return dict(dti=float(tp / (tp + ALPHA * fp + BETA * fn + EPS)),
                coverage=float(tp / nt) if nt else 0.0,
                tp=tp, fp=fp, fn=fn, dots=ne, n_truth=int(nt))


def emit_cell(pi, active, dvis, buf, n_target, dots=None):
    """Top-``n_target`` pixels of ``pi`` inside ``active``, thinned to 3-px separation.

    ``dots`` may be a precomputed candidate dot mask (the thinning depends only on
    the ranking and the buffer, not on the budget, so it is memoised by the caller).
    """
    if dots is None:
        cand = active & np.isfinite(pi) & (dvis > buf)
        dots = nms_dots(pi, cand)
    if n_target <= 0 or not dots.any():
        return np.zeros(dots.shape, bool)
    dy, dx = np.nonzero(dots)
    vals = pi[dy, dx]
    if vals.size > n_target:
        keep = np.argpartition(-vals, n_target)[:n_target]
        sel = np.zeros(dy.size, bool); sel[keep] = True
        out = np.zeros(dots.shape, bool); out[dy[sel], dx[sel]] = True
        return out
    return dots


def budget_sweep(cells, ctx, mode, nu_grid, families=FAMILIES, buffers=BUFFER_GRID):
    mode_cells = [c for c in cells if c.mode == mode]
    prep = {}
    for c in mode_cells:
        vis = ctx.visible(c.key)
        dvis = ndi.distance_transform_edt(~vis)[c.bbox].astype(np.float32)
        prep[c.key] = (c, dvis, {f: rank_field(f, c, dvis) for f in families})
    out = {}
    for fam in families:
        for buf in buffers:
            # thinning depends only on (ranking, buffer); memoise it across the budget sweep
            cache = {}
            for c in mode_cells:
                cc, dvis, rk = prep[c.key]
                cache[cc.key] = nms_dots(rk[fam], cc.active & np.isfinite(rk[fam]) & (dvis > buf))
            for nu in nu_grid:
                scores, per_cell = [], {}
                for c in mode_cells:
                    cc, dvis, rk = prep[c.key]
                    em = emit_cell(rk[fam], cc.active, dvis, buf, int(round(nu * cc.n_truth)),
                                   dots=cache[cc.key])
                    r = score_cell(cc, em)
                    scores.append(r)
                    per_cell[cc.key] = dict(dti=r["dti"], dots=r["n_emitted"], cov=r["coverage"])
                out[f"{fam}|buf{buf}|nu{nu}"] = {
                    **pooled(scores), "per_cell": per_cell, "family": fam,
                    "nu": nu, "buffer_px": buf,
                    "n_truth_total": int(sum(c.n_truth for c in mode_cells))}
    return out


def paired_ci(cells, mode, dvis_map, spec_a, spec_b, draws=1000, seed=520810):
    """Paired percentile bootstrap of the pooled-DTI difference over fold cells."""
    mc = [c for c in cells if c.mode == mode]

    def stats(spec):
        fam, buf, nu = spec
        rows = []
        for c in mc:
            dvis = dvis_map[c.key]
            em = emit_cell(rank_field(fam, c, dvis), c.active, dvis, buf,
                           int(round(nu * c.n_truth)))
            r = score_cell(c, em)
            rows.append((r["tp"], r["fp"], r["fn"]))
        return np.array(rows, np.float64)

    A, B = stats(spec_a), stats(spec_b)

    def dti(s):
        return s[0] / (s[0] + ALPHA * s[1] + BETA * s[2] + EPS)

    rng = np.random.default_rng(seed)
    n = len(mc)
    d = np.empty(draws)
    for i in range(draws):
        pick = rng.integers(0, n, n)
        d[i] = dti(A[pick].sum(axis=0)) - dti(B[pick].sum(axis=0))
    return dict(delta=float(dti(A.sum(axis=0)) - dti(B.sum(axis=0))),
                ci95=[float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
                draws=draws, seed=seed, cells=n,
                caveat="Conditional on the fitted folds and fixed budgets; not a leaderboard interval.")


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit-only", action="store_true",
                    help="skip the (slow) holdout sweep, reuse evidence/model_e3.json for the arm "
                         "choice, and rebuild only the deterministic emission and its receipt")
    args = ap.parse_args(argv)
    t0 = time.time()
    e12 = json.loads((ROOT / "evidence" / "model_e1e2.json").read_text())
    sib = json.loads((ROOT / "evidence" / "sibling_record.json").read_text())

    grid = load_grid(ROOT / "data" / "bridge")
    ctx = build_holdout(grid, seeds=SEEDS, modes=MODES)
    cells = ctx.cells

    if args.emit_only:
        prev = json.loads((ROOT / "evidence" / "model_e3.json").read_text())
        fam_star = prev["family"]; nu_star = float(prev["nu_star_detached"])
        buf_star = int(prev["buffer_star_px"]); best_key = prev["best_detached_arm"]
        sweep = prev["holdout_sweep"]
        best_det = sweep["detached"][best_key]
        best_prox = max((v for v in sweep["detached"].values() if v["family"] == "PROX"),
                        key=lambda v: v["dti"])
        pair = prev["paired_vs_prox"]
        print(f"emit-only: reusing {best_key} (nu*={nu_star}, buffer*={buf_star}px)", flush=True)
        return _emit(grid, e12, fam_star, nu_star, buf_star, best_key, best_det, best_prox,
                     pair, sweep, sib, t0)

    sweep = {}
    for mode in MODES:
        t1 = time.time()
        sweep[mode] = budget_sweep(cells, ctx, mode, NU_GRID)
        best = max(sweep[mode].items(), key=lambda kv: kv[1]["dti"])
        print(f"  {mode}: best {best[0]} DTI={best[1]['dti']:.4f} dots={best[1]['dots']} "
              f"cov={best[1]['coverage']:.3f} ({time.time()-t1:.0f}s)", flush=True)
        for fam in FAMILIES:
            sub = {k: v for k, v in sweep[mode].items() if v["family"] == fam}
            b = max(sub.items(), key=lambda kv: kv[1]["dti"])
            print(f"    {fam:5s}: best {b[0]} DTI={b[1]['dti']:.4f} dots={b[1]['dots']} "
                  f"cov={b[1]['coverage']:.3f}", flush=True)

    best_key, best_det = max(sweep["detached"].items(), key=lambda kv: kv[1]["dti"])
    fam_star = best_det["family"]; nu_star = float(best_det["nu"]); buf_star = int(best_det["buffer_px"])
    best_prox = max((v for v in sweep["detached"].values() if v["family"] == "PROX"),
                    key=lambda v: v["dti"])
    print(f"  winner on detached: {best_key} (DTI {best_det['dti']:.4f}); "
          f"best PROX baseline DTI {best_prox['dti']:.4f}", flush=True)

    # paired bootstrap of the winner against the proximity baseline at the baseline's own best budget
    dvis_map = {c.key: ndi.distance_transform_edt(~ctx.visible(c.key))[c.bbox].astype(np.float32)
                for c in cells if c.mode == "detached"}
    pair = paired_ci(cells, "detached", dvis_map,
                     (fam_star, buf_star, nu_star),
                     (best_prox["family"], best_prox["buffer_px"], best_prox["nu"]))
    pair["arms"] = [best_key, f"PROX|buf{best_prox['buffer_px']}|nu{best_prox['nu']}"]
    print(f"  paired winner-minus-PROX: {pair['delta']:+.4f} CI95 {pair['ci95']}", flush=True)

    K_est = SIBLING_BUDGET_DOTS / nu_star if nu_star > 0 else None
    print(f"  nu* = {nu_star}, buffer* = {buf_star}px -> implied real |truth| estimate "
          f"K_est = {SIBLING_BUDGET_DOTS}/{nu_star} = {K_est:,.0f} px (ESTIMATE, not a score)", flush=True)
    return _emit(grid, e12, fam_star, nu_star, buf_star, best_key, best_det, best_prox,
                 pair, sweep, sib, t0)


def _emit(grid, e12, fam_star, nu_star, buf_star, best_key, best_det, best_prox,
          pair, sweep, sib, t0) -> int:
    K_est = SIBLING_BUDGET_DOTS / nu_star if nu_star > 0 else None
    # ---------------- final live model: trained on the whole catalogue ----------
    dcat_live = ndi.distance_transform_edt(~grid.catalogue).astype(np.float32)
    if fam_star == "PROX":
        pi = -dcat_live
    else:
        stack = open_stack()
        cube = gf_cube(stack)
        quad = quadrant_ids(grid.footprint)
        model = train_fold(cube, grid, quad, -1,
                           ctx_map=dcat_live if fam_star == "CTX" else None)
        pi = predict_grid(model, cube, grid.footprint,
                          extra=dcat_live if fam_star == "CTX" else None)
        del cube

    allowed = (grid.footprint & ~grid.catalogue & np.isfinite(pi) & (dcat_live > buf_star))
    dots = nms_dots(pi, allowed)
    dy, dx = np.nonzero(dots)
    vals = pi[dy, dx]
    order = np.argsort(-vals, kind="stable")
    n_emit = min(SIBLING_BUDGET_DOTS, dy.size)
    sel = order[:n_emit]
    pred = np.zeros((HEIGHT, WIDTH), np.float32)
    pred[dy[sel], dx[sel]] = 1.0
    print(f"  live ranking {fam_star}: {dy.size} candidate dots after 3-px NMS; "
          f"emitting top {n_emit}", flush=True)

    sid = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"gems58-{fam_star.lower()}-dot{n_emit // 1000}k-{stamp}-{sid}-zeros"
    assert len(name) <= MAX_NAME, len(name)
    if fam_star == "PROX":
        how = "= dot ranking by distance to the mapped USGS/INGENIOUS catalogue"
    else:
        how = f"= LOQO {fam_star} ranking (19 GeoDAWN bands + local operators)"
    note = (f"58GEMSDOE {how}; 3px-thinned dots at 1.0; budget {n_emit} per the owner-raster "
            f"record; >{buf_star}px off-catalogue; holdout-validated")
    if len(note) > MAX_NAME:
        note = (f"58GEMSDOE: dots by distance to the mapped catalogue; 3px-thinned, value 1.0; "
                f"budget {n_emit}; >{buf_star}px off-catalogue; holdout-validated")
    assert len(note) <= MAX_NAME, (len(note), note)

    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = write_submission(
        out_dir / f"{name}.tif", pred, ROOT / "data" / "official" / "sample_submission.tif",
        grid.footprint, note=note, name=name, catalogue=grid.catalogue,
        metadata=dict(
            lane="supervised geophysical ranking + metric-derived dot budget (equal-budget contest)",
            family=fam_star, nms_radius_px=NMS_RADIUS_PX, dot_value=1.0,
            off_catalogue_buffer_px=buf_star,
            dots_emitted=int(n_emit), candidate_dots_after_nms=int(dy.size),
            budget_source="evidence/sibling_record.json (20 sha256-verified owner rasters; "
                          "<=44,090 dots out-score every raster >50,000; Spearman -0.83)",
            holdout=dict(evidence_class="HOLDOUT-DTI",
                         evaluator="gems57.holdout.score_cell (shared, exact)",
                         nu_grid=NU_GRID, buffer_grid=BUFFER_GRID, families=list(FAMILIES),
                         best_arm=best_key, best_detached=best_det,
                         best_prox_baseline=best_prox, paired_vs_prox=pair, sweep=sweep),
            implied_truth_pixels=dict(value=K_est, label="ESTIMATE",
                                      derivation="sibling-record budget / holdout nu*"),
            e2_threshold_sweep_best=e12.get("best_on_detached"),
            canary={m: dict(max_auc=e12["canary"][m]["max_auc"],
                            max_auc_feature=e12["canary"][m]["max_auc_feature"],
                            leakage_flag=e12["canary"][m]["leakage_flag"]) for m in MODES},
        ))
    print(f"wrote {name}.tif sha256 {receipt['sha256']} "
          f"all_checks_passed={receipt['validator']['all_checks_passed']}", flush=True)

    ev = dict(evidence_class="HOLDOUT-DTI + ESTIMATE",
              experiment="E3-equal-budget-ranking-contest-and-emission",
              family=fam_star, nu_star_detached=nu_star, buffer_star_px=buf_star,
              best_detached_arm=best_key,
              sibling_budget_dots=SIBLING_BUDGET_DOTS,
              implied_truth_pixels_estimate=K_est,
              paired_vs_prox=pair, holdout_sweep=sweep,
              submission=dict(name=name, sha256=receipt["sha256"], note=note, dots=int(n_emit),
                              validator_all_checks_passed=receipt["validator"]["all_checks_passed"]))
    (ROOT / "evidence" / "model_e3.json").write_text(json.dumps(ev, indent=1, default=float) + "\n")
    print(f"wrote evidence/model_e3.json | total {time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
