#!/usr/bin/env python3
"""E1+E2: sigma fit, leakage canary, and ribbon-vs-baseline holdout comparison.

Experiments (lane budget: 3 total, E3 is the emission build)
  E1  sigma table + leakage canary on the shared hide-and-recover holdout.
  E2  oracle/diagnostic arms on buffered whole-component cells. The legacy
      per-segment selector consults the same cell's withheld truth, so its DTI
      is not promotion-grade; a future nested outer-block run is required.
      Scoring delegates to gems57.evaluate_holdout (shared exact evaluator).

Run:  python3 scripts/run_ribbon_experiments.py
Writes: evidence/ribbon_e1_sigma.json, evidence/ribbon_e2_arms.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57.grid import load_grid
from gems57.holdout import FOLD_NAMES, build_buffered_holdout_context
from gems57.evaluate_holdout import evaluate as evaluate_holdout, pooled_summary
from gems57.metric import ALPHA, BETA, EPS, RADIUS_PX

import ribbon_lane as rl

SEEDS = (20, 21)
MODE = "all"          # template primary instrument
DTI0_ASSUMED = 0.28   # assumed operating point for U ordering only (best prior receipt 0.2778 rounded); never a score claim
ARMS = ("tight", "ribbon", "ribbon-pool")
BLOCK_PX = 200        # 20 km spatial blocks for the paired bootstrap


CTX = None   # module-global HoldoutContext (Grid is a frozen dataclass)


def cell_visible(cell):
    """Buffered, visible-only catalogue context for a holdout cell."""
    return CTX.visible(cell.key)


def cell_axes(grid, sgmc, cell, cache):
    """Axis segments for one cell from visible-only sources (cached per cell)."""
    if cell.key in cache:
        return cache[cell.key]
    visible = cell_visible(cell)
    out = []
    for kind in rl.RIDGE_TYPES:
        axes = rl.axis_mask_for_type(kind, visible, sgmc)
        out.extend(rl.axis_segments(kind, axes, cell.bbox))
    cache[cell.key] = out
    return out


def run_arm_on_cell(cell, axsegs, sigma_by_type, menu, dti0_ref, stride=rl.STRIDE_PX):
    """One arm on one cell -> (state, choices).  Exact accept test at sweep time."""
    K = cell.n_truth
    state = rl.make_cell_state(cell)
    configs = []
    for s in axsegs:
        sig = sigma_by_type.get(s.kind, float("nan"))
        if not np.isfinite(sig):
            continue
        offs_menu = rl.pattern_offsets(sig)
        names = list(menu) if menu is not None else list(offs_menu)
        names = [n for n in names if n in offs_menu]
        if not names:
            continue
        dots_by_cfg = {}
        for n in names:
            d = rl._clip(rl.build_pattern_dots(s, offs_menu[n], stride), state.H, state.W)
            if len(d):
                d = d[cell.active[d[:, 0], d[:, 1]]]   # scored domain only
            if len(d):
                dots_by_cfg[n] = d
        if not dots_by_cfg:
            continue
        all_dots = np.unique(np.concatenate(list(dots_by_cfg.values()), 0), axis=0)
        k_self = state.k_dg[all_dots[:, 0], all_dots[:, 1]]
        if k_self.max() < 0.5 * ALPHA * max(dti0_ref, 0.02):
            continue
        hits = state.tree.query_ball_point(all_dots.astype(np.float64), RADIUS_PX)
        pair_count = sum(len(h) for h in hits)
        if pair_count:
            di = np.repeat(np.arange(len(all_dots)), np.fromiter((len(h) for h in hits), np.int64, len(hits)))
            gi = np.fromiter((g for h in hits for g in h), np.int64, int(pair_count))
            gy = state.truth_yx[0][gi].astype(np.float64)
            gx = state.truth_yx[1][gi].astype(np.float64)
            w = rl.kernel(np.hypot(gy - all_dots[di, 0], gx - all_dots[di, 1]))
        else:
            di = gi = np.empty(0, np.int64)
            w = np.empty(0, np.float64)
        keys = [all_dots[:, 0] * state.W + all_dots[:, 1]]
        flat_keys = all_dots[:, 0].astype(np.int64) * state.W + all_dots[:, 1].astype(np.int64)
        for n, d in dots_by_cfg.items():
            rows = np.searchsorted(np.sort(flat_keys), d[:, 0].astype(np.int64) * state.W + d[:, 1].astype(np.int64))
            sorted_keys = np.sort(flat_keys)
            rows = np.searchsorted(sorted_keys, d[:, 0].astype(np.int64) * state.W + d[:, 1].astype(np.int64))
            rows = np.clip(rows, 0, len(all_dots) - 1)
            rmap = np.full(len(all_dots), -1, np.int64)
            # rows into all_dots via matching keys
            pos = np.searchsorted(np.argsort(flat_keys), rows)
            del pos
            # simpler: map by key dictionary
            rmap = {int(k): i for i, k in enumerate(flat_keys)}
            ridx = np.array([rmap[int(a) * state.W + int(b)] for a, b in d], np.int64)
            del rmap
            in_cfg = np.zeros(len(all_dots), bool)
            in_cfg[ridx] = True
            sel_mask = in_cfg[di]
            if sel_mask.any():
                gg = gi[sel_mask]
                ww = w[sel_mask]
                order = np.argsort(gg, kind="stable")
                gg_s, ww_s = gg[order], ww[order]
                uniq, start = np.unique(gg_s, return_index=True)
                maxw = np.maximum.reduceat(ww_s, start)
                d_t = float(np.maximum(maxw - state.credit[uniq], 0.0).sum())
            else:
                d_t = 0.0
            d_fp = float((1.0 - k_self[ridx]).sum())
            k_sum = float(k_self[ridx].sum())
            if d_t <= 0:
                continue
            U = (1.0 - ALPHA * dti0_ref) * d_t - ALPHA * dti0_ref * d_fp
            configs.append(dict(kind=s.kind, seg_id=s.seg_id, cfg=n, offsets=offs_menu[n],
                                dots=d, U=U))
    configs.sort(key=lambda c: -c["U"])
    choices = {}
    chosen_segments = set()   # lane contract: exactly ONE ribbon choice per segment
    for c in configs:
        key = (c["kind"], c["seg_id"])
        if key in chosen_segments:
            continue
        base = c["dots"][:, 0].astype(np.int64) * state.W + c["dots"][:, 1].astype(np.int64)
        fresh = ~np.isin(base, np.array(sorted(state.emitted), np.int64)) if state.emitted else np.ones(len(base), bool)
        if not fresh.any():
            continue
        dd = c["dots"][fresh]
        d_t2, d_fp2, k_sum2 = rl.pattern_gain(state, dd)
        if d_t2 <= 0:
            continue
        if rl.exact_accept(state, d_t2, d_fp2, k_sum2, K):
            rl.apply_pattern(state, dd, k_sum2)
            chosen_segments.add(key)
            choices[key] = dict(
                cfg=c["cfg"], offsets=[int(o) for o in c["offsets"]],
                n_dots=int(len(dd)), d_t=float(d_t2), d_fp=float(d_fp2), U=float(c["U"]),
                kind=c["kind"],
                flat=(dd[:, 0].astype(np.int64) * state.W + dd[:, 1].astype(np.int64)).tolist())
    return state, choices


def crop_emission_from_choices(cell, choices) -> np.ndarray:
    H, W = cell.k_dg.shape
    m = np.zeros((H, W), bool)
    for v in choices.values():
        f = np.array(v["flat"], np.int64)
        if len(f):
            m[f // W, f % W] = True
    return m


def evaluate_cell(cell, emission, block_side=BLOCK_PX):
    """Score one crop through the shared template evaluator, not a lane-local metric."""
    p = np.asarray(emission, bool)
    if p.shape == CTX.grid.shape:
        p = p[cell.bbox]
    if p.shape != cell.active.shape:
        raise ValueError('emission crop does not match holdout cell')
    truth = np.zeros(cell.active.shape, dtype=bool)
    truth[cell.truth_yx] = True
    zeros = np.zeros_like(truth)
    fold = dict(truth=truth, region=np.ones_like(truth),
                visible=zeros, masked_known=zeros)
    origin = (int(cell.bbox[0].start), int(cell.bbox[1].start))
    return evaluate_holdout(
        p.astype(np.float32), fold, cell.active, block_side=block_side,
        origin=origin, global_shape=CTX.grid.shape)


def block_terms(cell, choices, block_px=BLOCK_PX):
    """Exact pooled terms from the shared evaluator on globally aligned blocks."""
    _, terms = evaluate_cell(cell, crop_emission_from_choices(cell, choices), block_side=block_px)
    return terms


def main() -> int:
    global grid
    t_start = time.time()
    grid = load_grid(ROOT / "data" / "bridge")
    sgmc = rl.sgmc_mask(ROOT, grid)
    print(f"grid: catalogue px={int(grid.catalogue.sum())} footprint px={int(grid.footprint.sum())}", flush=True)

    global CTX
    CTX = build_buffered_holdout_context(grid, seeds=SEEDS)
    cells = CTX.cells
    rng = np.random.default_rng(2026)

    # ---------------- E1 ----------------
    seg_records, sigma_rows, canary_rows = [], [], []
    for cell in cells:
        visible = cell_visible(cell)
        axsegs = []
        axis_rasters = {}
        for kind in rl.RIDGE_TYPES:
            axes = rl.axis_mask_for_type(kind, visible, sgmc)
            axis_rasters[kind] = axes
            axsegs.extend(rl.axis_segments(kind, axes, cell.bbox))
        recs = rl.across_strike_measurements(axsegs, cell.truth_yx, cell.k_dg)
        for r in recs:
            r["cell"] = cell.key
        seg_records.extend(recs)
        fit = rl.fit_sigma(recs)
        sigma_rows.append(dict(cell=cell.key, fold=cell.fold, seed=cell.seed,
                               n_truth=int(cell.n_truth), **fit))
        for kind in rl.RIDGE_TYPES:
            # feature-alone canary: kernel of distance to THIS type's ridge axes
            sc = kernel(ndi.distance_transform_edt(~axis_rasters[kind][cell.bbox]))
            a = rl.canary_auc(sc, cell.truth_yx, cell.active, rng)
            canary_rows.append(dict(cell=cell.key, kind=kind, auc_distance_to_ridge=a))
        print(f"E1 {cell.key}: sig cat={fit['per_type']['cat-axis']['sigma_px']:.2f} "
              f"sgmc={fit['per_type']['sgmc-axis']['sigma_px']:.2f}", flush=True)

    pooled_sigma = {}
    for kind in rl.RIDGE_TYPES:
        m = np.array([r["across_rms"] for r in seg_records if r["kind"] == kind and r["matched"]], float)
        pooled_sigma[kind] = dict(
            n_segments=int(sum(1 for r in seg_records if r["kind"] == kind)),
            n_matched=int(m.size),
            sigma_raw_px=(float(np.sqrt(np.mean(m ** 2))) if m.size else float("nan")),
            matched_fraction=float(m.size / max(1, sum(1 for r in seg_records if r["kind"] == kind))),
            evidence_class="HOLDOUT-STRUCTURE")
    allm = np.array([r["across_rms"] for r in seg_records if r["matched"]], float)
    sigma_pool = float(np.sqrt(np.mean(allm ** 2))) if allm.size else float("nan")

    max_auc = {k: float(np.nanmax([r["auc_distance_to_ridge"] for r in canary_rows if r["kind"] == k]))
               for k in rl.RIDGE_TYPES}
    e1 = dict(
        experiment="E1-sigma-and-canary",
        evidence_class="HOLDOUT-STRUCTURE",
        promotion_grade=False,
        buffered_whole_component_context_used=True,
        holdout_status="buffered whole-component feature context; E1 diagnostics only, not an untouched outer-block promotion evaluation",
        instrument=dict(kind="hide-and-recover", seeds=list(SEEDS), mode=MODE, folds=list(FOLD_NAMES),
                        constructor="gems57.holdout.build_buffered_holdout_context",
                        feature_buffer_px=3, quadrant_boundary_px=12,
                        evaluator_version="gems57-pooled-hide-v2",
                        evaluator="gems57.evaluate_holdout (shared)", alpha=ALPHA, beta=BETA,
                        triangular_radius_px=RADIUS_PX),
        ridge_types={
            "cat-axis": dict(source="skeleton of the visible catalogue only (per fold)",
                             feature_resolution="100 m competition catalogue (INGENIOUS-detail digitising)"),
            "sgmc-axis": dict(source="skeleton of SGMC minus the visible catalogue",
                              feature_resolution="100 m grid; SGMC compiled at ~1:250k source scale")},
        match_cap_px=rl.MATCH_CAP_PX,
        sigma_shrink_pseudo_k=rl.SIGMA_SHRINK_K,
        sigma_pool_px=sigma_pool,
        sigma_pooled_by_type=pooled_sigma,
        sigma_by_cell=sigma_rows,
        leakage_canary=dict(
            evidence_class="BUFFERED-FEATURE-ALONE-CANARY",
            rule="feature alone on the holdout; AUC > 0.90 means leakage until proven otherwise",
            per_cell=canary_rows, max_auc_by_type=max_auc,
            verdict=("PASS - no ridge type exceeds AUC 0.90"
                     if all(v <= 0.90 for v in max_auc.values()) else
                     "FAIL - do not trust results until explained")),
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "ribbon_e1_sigma.json").write_text(json.dumps(e1, indent=1, default=float) + "\n")
    print(f"E1 done in {time.time()-t_start:.0f}s | canary: {e1['leakage_canary']['verdict']} "
          f"| max AUC {max_auc}", flush=True)

    # ---------------- E2 ----------------
    sigma_by_cell_type = {}
    for row in sigma_rows:
        for kind in rl.RIDGE_TYPES:
            sigma_by_cell_type[(row["cell"], kind)] = row["per_type"][kind]["sigma_px"]

    cache: dict = {}
    store: dict[str, dict[str, dict]] = {a: {} for a in ARMS}
    per_cell_meta: dict[str, dict] = {}

    # Stage 1: tight baseline -> DTI0 (exact pooled)
    for cell in cells:
        axsegs = cell_axes(grid, sgmc, cell, cache)
        sig = {k: sigma_by_cell_type[(cell.key, k)] for k in rl.RIDGE_TYPES}
        state, ch = run_arm_on_cell(cell, axsegs, sig, ("tight",), DTI0_ASSUMED)
        store["tight"][cell.key] = ch
        r = evaluate_cell(cell, crop_emission_from_choices(cell, ch))[0]
        per_cell_meta.setdefault("tight", {})[cell.key] = dict(dti=r["dti"], dots=int(r["n_emitted"]))
        print(f"E2-tight {cell.key}: emitted={r['n_emitted']} | raw DTI suppressed (oracle diagnostic; not reportable)", flush=True)
    tp = sum(v["tp"] for v in [])  # placeholder no-op
    tp = fp = fn = 0.0
    for cell in cells:
        r = evaluate_cell(cell, crop_emission_from_choices(cell, store["tight"][cell.key]))[0]
        tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
    dti0 = float(tp / (tp + ALPHA * fp + BETA * fn + EPS))
    print("E2: pooled raw DTI suppressed; oracle/selection diagnostic is not reportable.", flush=True)

    arms_out = {"tight": dict(pooled_dti=dti0, per_cell=per_cell_meta["tight"])}
    for arm in ("ribbon", "ribbon-pool"):
        per_cell_meta[arm] = {}
        tp = fp = fn = 0.0
        for cell in cells:
            axsegs = cell_axes(grid, sgmc, cell, cache)
            sig = {k: sigma_by_cell_type[(cell.key, k)] for k in rl.RIDGE_TYPES}
            if arm == "ribbon-pool":
                sig = {k: sigma_pool for k in rl.RIDGE_TYPES}
            state, ch = run_arm_on_cell(cell, axsegs, sig, None, dti0)
            store[arm][cell.key] = ch
            r = evaluate_cell(cell, crop_emission_from_choices(cell, ch))[0]
            per_cell_meta[arm][cell.key] = dict(dti=r["dti"], dots=int(r["n_emitted"]))
            tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
            print(f"E2-{arm} {cell.key}: emitted={r['n_emitted']} | raw DTI suppressed (oracle diagnostic; not reportable)", flush=True)
        pooled = float(tp / (tp + ALPHA * fp + BETA * fn + EPS))
        arms_out[arm] = dict(pooled_dti=pooled, per_cell=per_cell_meta[arm])
        print(f"E2-{arm}: pooled raw DTI suppressed (oracle diagnostic; not reportable)", flush=True)

    # paired spatial-block bootstrap: ribbon vs tight, and ribbon vs ribbon-pool
    def block_stack(arm):
        # Sum all seeds/folds into the same physical 20 km cells before resampling;
        # repeated copies of one geographic block are not independent clusters.
        stacks = [block_terms(cell, store[arm][cell.key]) for cell in cells]
        if not stacks:
            raise ValueError('no holdout cells to aggregate')
        return np.sum(np.stack(stacks, axis=0), axis=0)

    T = {a: block_stack(a) for a in ARMS}
    bootstrap = pooled_summary(T, draws=1000, seed=520810, candidate='ribbon')
    paired = dict(
        evidence_class="HOLDOUT-DTI (oracle diagnostic; not promotion-grade)",
        method="shared evaluate_holdout pooled physical 20 km blocks; repeated folds merged before paired resampling",
        blocks=bootstrap["bootstrap"]["clusters"], draws=bootstrap["bootstrap"]["draws"],
        seed=bootstrap["bootstrap"]["seed"],
        ribbon_minus_tight=bootstrap["paired_differences"]["tight"],
        ribbon_minus_ribbonpool=bootstrap["paired_differences"]["ribbon-pool"],
        caveat="Conditional on fitted folds. Segment configurations are accepted using the same cell's withheld truth; CI does not remove selection leakage and is not a leaderboard interval.",
    )

    # per-class gains (class-restricted emissions, exact evaluator)
    class_gains = {}
    for kind in rl.RIDGE_TYPES:
        stats = {}
        for arm in ("ribbon", "tight"):
            tp = fp = fn = 0.0
            for cell in cells:
                sub = {k: v for k, v in store[arm][cell.key].items() if k[0] == kind}
                r = evaluate_cell(cell, crop_emission_from_choices(cell, sub))[0]
                tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
            stats[arm] = float(tp / (tp + ALPHA * fp + BETA * fn + EPS))
        n_dots = int(sum(v["n_dots"] for cell in cells for k, v in store["ribbon"][cell.key].items() if k[0] == kind))
        n_dots_t = int(sum(v["n_dots"] for cell in cells for k, v in store["tight"][cell.key].items() if k[0] == kind))
        class_gains[kind] = dict(ribbon_only_dti=stats["ribbon"], tight_only_dti=stats["tight"],
                                 gain=stats["ribbon"] - stats["tight"],
                                 n_dots_ribbon=n_dots, n_dots_tight=n_dots_t,
                                 evidence_class="HOLDOUT-DTI (class-restricted emission)")
        print(f"E2 class {kind}: per-class raw DTI/gain suppressed (oracle diagnostic; not reportable)", flush=True)

    mix = {}
    for cell in cells:
        for (kind, _sid), v in store["ribbon"][cell.key].items():
            mix[f"{kind}|{v['cfg']}"] = mix.get(f"{kind}|{v['cfg']}", 0) + 1

    n_withheld_positive_pixels = int(sum(c.n_truth for c in cells))
    legacy_score_label = "LEGACY HOLDOUT-DTI DIAGNOSTIC — INVALID/NOT REPORTABLE"
    evaluator_version = "gems57-pooled-hide-v2 (shared arithmetic; E2 selection remains oracle/leaky)"
    score_limitation = (
        "Patterns were accepted using the same cell's withheld truth and sigma was fitted on scored folds. "
        "The legacy interval is not a promotion-grade independent 95% CI."
    )
    for arm_record in arms_out.values():
        arm_record.update(evidence_class=legacy_score_label,
                          evaluator_version=evaluator_version,
                          withheld_positive_pixels=n_withheld_positive_pixels,
                          absolute_ci95=None, ci95_reportable=False,
                          score_claim_allowed=False, reporting_limitation=score_limitation)
        for cell_record in arm_record.get("per_cell", {}).values():
            cell_record.update(evidence_class=legacy_score_label,
                               evaluator_version=evaluator_version,
                               withheld_positive_pixels=n_withheld_positive_pixels,
                               ci95=None, ci95_reportable=False,
                               score_claim_allowed=False, reporting_limitation=score_limitation)
    for class_record in class_gains.values():
        class_record.update(evidence_class=legacy_score_label,
                            evaluator_version=evaluator_version,
                            withheld_positive_pixels=n_withheld_positive_pixels,
                            ci95=None, ci95_reportable=False,
                            score_claim_allowed=False, reporting_limitation=score_limitation)
    paired.update(evidence_class=legacy_score_label,
                  evaluator_version=evaluator_version,
                  withheld_positive_pixels=n_withheld_positive_pixels,
                  ci95_reportable=False, score_claim_allowed=False,
                  reporting_limitation=score_limitation)
    e2 = dict(
        experiment="E2-ribbon-arms",
        evidence_class=legacy_score_label,
        promotion_grade=False,
        validation_limitations=[
            "per-segment exact_accept consults the same cell's withheld truth",
            "sigma is fitted on the scored draw rather than an untouched outer block",
            "an outer spatial-block evaluation with train-only tuning is still required",
        ],
        buffered_whole_component_context_used=True,
        instrument=dict(kind="hide-and-recover", seeds=list(SEEDS), mode=MODE,
                        constructor="gems57.holdout.build_buffered_holdout_context",
                        feature_buffer_px=3, quadrant_boundary_px=12,
                        evaluator_version="gems57-pooled-hide-v2",
                        evaluator="gems57.evaluate_holdout.evaluate (shared exact; buffered split)",
                        alpha=ALPHA, beta=BETA, triangular_radius_px=RADIUS_PX),
        dti0_reference=dict(value=dti0, arm="tight", evidence_class=legacy_score_label,
                            evaluator_version=evaluator_version,
                            withheld_positive_pixels=n_withheld_positive_pixels,
                            ci95=None, ci95_reportable=False, score_claim_allowed=False,
                            reporting_limitation=score_limitation),
        dti0_assumed_for_ordering=DTI0_ASSUMED,
        arms=arms_out,
        absolute_score_intervals_diagnostic_only=dict(
            evidence_class=legacy_score_label,
            evaluator_version=evaluator_version,
            withheld_positive_pixels=n_withheld_positive_pixels,
            values=bootstrap["scores"],
            ci95_reportable=False, score_claim_allowed=False,
            reporting_limitation=score_limitation),
        paired_bootstrap=paired,
        per_class_gains=class_gains,
        config_mix_ribbon=mix,
        pattern_rule=dict(stride_px=rl.STRIDE_PX,
                          note="along-line stride = 3 px (kernel radius); parallel lines spaced 2*|offset| px"),
        withheld_positive_pixels=n_withheld_positive_pixels,
        reporting_contract=dict(
            score_claim_allowed=False,
            evidence_class=legacy_score_label,
            evaluator_version=evaluator_version,
            withheld_positive_pixels=n_withheld_positive_pixels,
            absolute_arm_ci95_reportable=False,
            paired_ci95_reportable=False,
            reason=score_limitation),
        elapsed_s=time.time() - t_start,
    )
    (ROOT / "evidence" / "ribbon_e2_arms.json").write_text(json.dumps(e2, indent=1, default=float) + "\n")
    print(f"E2 done -> evidence/ribbon_e2_arms.json ({time.time()-t_start:.0f}s total)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
