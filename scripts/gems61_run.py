#!/usr/bin/env python3
"""Session-7 ribbon-lane experiments (H7-A deep-structure step edges).

EXP-1  surfaces + leakage canary + sigma table (block x resolution x ridge type x relief)
EXP-2  nested exact-U pattern selection, cross-fitted HOLDOUT-DTI vs two references
EXP-3  production emission, writer (all-finite [0,1]), validators, uniqueness screen

Shared instruments (never forked):
  * feature stack  : gems58w.paths.feature_stack (pinned sha256, 19 bands)
  * holdout        : gems57.holdout.build_buffered_holdout_context
  * scoring        : gems57.holdout.score_cell / gems57.metric (exact DTI)
  * writer         : gems57.submission_writer.write_submission
  * uniqueness     : gems57.uniqueness definitions via gems58w.uniqueness
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import holdout as H                      # noqa: E402
from gems57.grid import load_grid                    # noqa: E402
from gems61 import patterns as P                     # noqa: E402
from gems61 import sigma_fit as S                    # noqa: E402
from gems61 import surfaces as SU                    # noqa: E402

EVID = ROOT / "evidence" / "gems61"
SEEDS = (20, 21)
HIDE_FRAC = 0.20
N_BUDGET = 40_000
STRENGTH_TERMS = ("high", "mid", "low")
REF_TIF = ROOT / "docs" / "downloads" / "gems58-concordance-ribbon-40768-20261011T160514Z.tif"
INSTRUMENT = ("gems61-buffered-hide-v1: gems57.holdout.build_buffered_holdout_context "
              f"seeds={SEEDS} hide_frac={HIDE_FRAC} mode=all; exact triangular DTI "
              "alpha=0.2 beta=0.8 R=3px (gems57.metric)")


def _auc(scores: np.ndarray, labels: np.ndarray) -> float:
    s = np.asarray(scores, np.float64)
    y = np.asarray(labels, bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="stable")
    r = np.empty(s.size, np.float64)
    r[order] = np.arange(1, s.size + 1, dtype=np.float64)
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_state(force: bool = False):
    t0 = time.time()
    surf = SU.build(force=force)
    grid = load_grid(ROOT / "data" / "bridge")
    ctx = H.build_buffered_holdout_context(grid, hide_frac=HIDE_FRAC, seeds=SEEDS)
    segs = SU.segments(surf, keep=grid.footprint)
    print(f"state: surfaces+grid+ctx+segments in {time.time() - t0:.1f}s; "
          f"{len(segs)} edge segments", flush=True)
    return surf, grid, ctx, segs


# ----------------------------------------------------------------- EXP-1


def exp1(force: bool = False) -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    surf, grid, ctx, segs = _load_state(force)
    rng = np.random.default_rng(58_007)

    # per-band edge responses (canary: feature alone)
    per_band = {}
    for bi, (name, index, fam) in enumerate(SU.EDGE_BANDS):
        z, v = SU._read_band(index)
        r = np.zeros_like(z)
        for s in SU.SCALES:
            r = np.maximum(r, SU._edge_response(z, v, s))
        per_band[bi] = r
        print(f"canary surface ready: {fam}:{name}", flush=True)

    canary: dict[str, list[float]] = {}
    sigma_rows: list[S.SegSigma] = []
    for cell in ctx.cells:
        truth = np.zeros(cell.active.shape, bool)
        truth[cell.truth_yx] = True
        active = cell.active
        ys, xs = np.nonzero(active)
        take = min(200_000, ys.size)
        pick = rng.choice(ys.size, take, replace=False)
        py, px = ys[pick], xs[pick]
        lab = truth[py, px]
        canary.setdefault("combined_edge_strength", []).append(
            _auc(surf.strength[cell.bbox][py, px], lab))
        for bi, (name, _index, fam) in enumerate(SU.EDGE_BANDS):
            canary.setdefault(f"band_{fam}:{name}", []).append(
                _auc(per_band[bi][cell.bbox][py, px], lab))
        canary.setdefault("relief_field_H7B", []).append(
            _auc(surf.relief[cell.bbox][py, px], lab))

        # sigma: ridge->truth across-strike distance on this cell
        truth_full = np.zeros(grid.footprint.shape, bool)
        truth_full[cell.bbox] = truth
        active_full = np.zeros(grid.footprint.shape, bool)
        active_full[cell.bbox] = active
        rows = S.measure(segs, truth_full, active_full, grid.footprint.shape)
        sigma_rows.extend(rows)
        print(f"cell {cell.key}: canary n={take}, sigma rows +{len(rows)}", flush=True)

    canary_summary = {k: float(np.nanmean(v)) for k, v in canary.items()}
    canary_summary["n_cells"] = len(ctx.cells)
    canary_summary["per_cell"] = {k: [float(x) for x in v] for k, v in canary.items()}
    bad = {k: v for k, v in canary_summary.items()
           if isinstance(v, float) and v > 0.90}
    table = S.sigma_table(sigma_rows)

    out = dict(
        evidence_class="LOCAL-MEASUREMENT",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        instrument=INSTRUMENT,
        hypothesis="H7-A deep-structure step edges; H7-B relief-conditioned sigma",
        canary=canary_summary,
        canary_verdict="LEAKAGE-SUSPECT" if bad else "CLEAN",
        canary_firings_a_gt_090={k: v for k, v in bad.items()},
        sigma_table=table,
        sigma_rows=[r.__dict__ for r in sigma_rows],
        n_segments=len(segs),
    )
    (EVID / "exp1_sigma_canary.json").write_text(json.dumps(out, indent=1) + "\n")
    (EVID / "sigma.json").write_text(json.dumps(
        dict(evidence_class="LOCAL-MEASUREMENT", sigma_table=table,
             generated_utc=out["generated_utc"]), indent=1) + "\n")
    print(json.dumps(canary_summary, indent=1)[:800])
    print("sigma pooled:", json.dumps(table["pooled_sigma"]))
    print(f"canary verdict: {out['canary_verdict']}")
    return 0


# ----------------------------------------------------------------- EXP-2


def _seg_stratum(seg) -> tuple:
    return (seg.band, seg.scale, seg.relief_class)


def _seg_dots(seg, pat: P.Pattern, sigma: float, shape) -> np.ndarray:
    return P.segment_dots(seg, pat.offsets(sigma), shape)


def _mask_terms(mask: np.ndarray, cells) -> tuple[float, float, float, int]:
    tp = fp = fn = nt = 0.0
    for c in cells:
        r = H.score_cell(c, mask)
        tp += r["tp"]; fp += r["fp"]; fn += r["fn"]; nt += r["n_truth"]
    return tp, fp, fn, int(nt)


def _pooled_dti(tp: float, fp: float, fn: float) -> float:
    return float(tp / (tp + H.ALPHA * fp + H.BETA * fn + 1e-12))


def exp2() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    surf, grid, ctx, segs = _load_state()
    shape = grid.footprint.shape
    cell_block = {c.key: c.key.split("_fold")[1].split("_")[0] for c in ctx.cells}
    blocks = sorted(set(cell_block.values()))
    folds = {q: [c for c in ctx.cells if cell_block[c.key] == q] for q in blocks}

    # sigma rows from EXP-1 (fitted per segment stratum, nested per outer fold)
    exp1 = json.loads((EVID / "exp1_sigma_canary.json").read_text())
    sigma_rows = [S.SegSigma(**{k: v for k, v in r.items()}) for r in exp1["sigma_rows"]]

    # strength terciles per stratum for the include decision
    strat: dict[tuple, list] = {}
    for s in segs:
        strat.setdefault(_seg_stratum(s), []).append(s)
    bin_of: dict[int, int] = {}
    for _key, group in strat.items():
        strengths = np.array([s.strength for s in group])
        q1, q2 = np.quantile(strengths, [1 / 3, 2 / 3])
        for s in group:
            bin_of[id(s)] = 0 if s.strength >= q2 else (1 if s.strength >= q1 else 2)

    class_rows = []          # simulated gain per class
    outer_params = {}        # outer block -> {stratum: {bin: (pattern_name or DROP)}}
    arms = {"A0_single_line": {}, "A1_sigma_ribbon": {}}
    selection = {}

    for q in blocks:
        inner_cells = [c for b in blocks if b != q for c in folds[b]]
        outer_cells = folds[q]
        inner_rows = [r for r in sigma_rows if r.block != q]

        # baseline s0: single-line arm on inner cells
        base_mask = np.zeros(shape, bool)
        for s in segs:
            sig, _src = S.sigma_for(s.family, s.band, s.scale, s.relief_class, q, inner_rows)
            d = _seg_dots(s, P.PATTERNS[0], sig, shape)
            base_mask[d[:, 0], d[:, 1]] = True
        tp0, fp0, fn0, nt0 = _mask_terms(base_mask, inner_cells)
        s0 = _pooled_dti(tp0, fp0, fn0)
        print(f"[outer {q}] inner baseline s0={s0:.5f} ({int(base_mask.sum())} dots)", flush=True)

        chosen: dict[tuple, dict[int, str]] = {}
        for key, group in sorted(strat.items()):
            band, scale, rcls = key
            fam = SU.EDGE_BANDS[[b for b, _i, _f in SU.EDGE_BANDS].index(band)][2]
            entry = {}
            for b in (0, 1, 2):
                members = [s for s in group if bin_of[id(s)] == b]
                if len(members) < 3:
                    continue
                best_pat, best_u = "DROP", 0.0
                per_pat = {}
                for pat in P.PATTERNS:
                    m = np.zeros(shape, bool)
                    for s in members:
                        sig, _src = S.sigma_for(fam, s.band, s.scale, s.relief_class, q, inner_rows)
                        d = _seg_dots(s, pat, sig, shape)
                        m[d[:, 0], d[:, 1]] = True
                    tp, fp, fn, nt = _mask_terms(m, inner_cells)
                    u = P.utility(tp, fp, s0)
                    n_dots = int(m.sum())
                    per_pat[pat.name] = dict(U=u, TP=tp, FP=fp, n_dots=n_dots,
                                             U_per_dot=(u / n_dots if n_dots else 0.0))
                    if u > best_u + P.U_TOL:
                        best_pat, best_u = pat.name, u
                entry[b] = best_pat
                class_rows.append(dict(
                    outer=q, stratum=f"{fam}:{band}@{scale:g}px relief{rcls}",
                    strength_bin=STRENGTH_TERMS[b], n_segments=len(members),
                    chosen=best_pat, U_best=best_u, per_pattern=per_pat,
                    sigma_source_examples=[
                        S.sigma_for(fam, s.band, s.scale, s.relief_class, q, inner_rows)
                        for s in members[:3]]))
            chosen[key] = entry
        outer_params[q] = chosen

        # A1: cross-fitted sigma-ribbon (patterns + include set chosen on inner cells)
        m1 = np.zeros(shape, bool)
        for key, group in sorted(strat.items()):
            band, scale, rcls = key
            fam = SU.EDGE_BANDS[[b for b, _i, _f in SU.EDGE_BANDS].index(band)][2]
            for s in group:
                b = bin_of[id(s)]
                pn = chosen.get(key, {}).get(b, "DROP")
                if pn == "DROP":
                    continue
                pat = next(p for p in P.PATTERNS if p.name == pn)
                sig, _src = S.sigma_for(fam, s.band, s.scale, s.relief_class, q, inner_rows)
                d = _seg_dots(s, pat, sig, shape)
                m1[d[:, 0], d[:, 1]] = True
        tp, fp, fn, nt = _mask_terms(m1, outer_cells)
        arms["A1_sigma_ribbon"][q] = dict(tp=tp, fp=fp, fn=fn, n_truth=nt,
                                         n_dots=int(m1.sum()), dti=_pooled_dti(tp, fp, fn))

        # A0: incumbent-style single tight line, SAME dot budget (strength-ranked,
        # no truth input) — isolates the value of the sigma-ribbon geometry
        target = int(m1.sum())
        m0 = np.zeros(shape, bool)
        n0 = 0
        for s in sorted(segs, key=lambda x: -x.strength):
            if n0 >= target:
                break
            sig, _src = S.sigma_for(s.family, s.band, s.scale, s.relief_class, q, inner_rows)
            d = _seg_dots(s, P.PATTERNS[0], sig, shape)
            m0[d[:, 0], d[:, 1]] = True
            n0 = int(m0.sum())
        tp, fp, fn, nt = _mask_terms(m0, outer_cells)
        arms["A0_single_line"][q] = dict(tp=tp, fp=fp, fn=fn, n_truth=nt,
                                        n_dots=int(m0.sum()), dti=_pooled_dti(tp, fp, fn))
        print(f"[outer {q}] A0 {arms['A0_single_line'][q]['dti']:.5f} "
              f"A1 {arms['A1_sigma_ribbon'][q]['dti']:.5f}", flush=True)

    # pooled + quadrant-cluster paired bootstrap
    def pool(arm):
        tp = sum(v["tp"] for v in arm.values())
        fp = sum(v["fp"] for v in arm.values())
        fn = sum(v["fn"] for v in arm.values())
        nt = sum(v["n_truth"] for v in arm.values())
        return dict(dti=_pooled_dti(tp, fp, fn), tp=tp, fp=fp, fn=fn, n_truth=int(nt),
                    n_dots=sum(v["n_dots"] for v in arm.values()))

    pooled = {k: pool(v) for k, v in arms.items()}

    # reference arm: the published concordance file, same instrument
    ref = None
    if REF_TIF.exists():
        import rasterio
        with rasterio.open(REF_TIF) as src:
            arr = src.read(1)
        emitted = np.isfinite(arr) & (arr > 0)
        tp = fp = fn = nt = 0.0
        per = {}
        for c in ctx.cells:
            r = H.score_cell(c, emitted)
            per[c.key] = r
            tp += r["tp"]; fp += r["fp"]; fn += r["fn"]; nt += r["n_truth"]
        ref = dict(dti=_pooled_dti(tp, fp, fn), tp=tp, fp=fp, fn=fn, n_truth=int(nt),
                   n_dots=int(emitted.sum()), file=REF_TIF.name,
                   label="published session-5 concordance candidate re-scored on this instrument")
        print(f"[ref] {ref['dti']:.5f}", flush=True)

    rng = np.random.default_rng(77)
    qs = blocks
    boot = {k: [] for k in arms}
    n_draws = 2000
    for _ in range(n_draws):
        picks = rng.integers(0, len(qs), len(qs))
        for name, arm in arms.items():
            tp = sum(arm[qs[i]]["tp"] for i in picks)
            fp = sum(arm[qs[i]]["fp"] for i in picks)
            fn = sum(arm[qs[i]]["fn"] for i in picks)
            boot[name].append(_pooled_dti(tp, fp, fn))
    delta = (np.array(boot["A1_sigma_ribbon"]) - np.array(boot["A0_single_line"]))
    ci = [float(x) for x in np.quantile(delta, [0.025, 0.975])]

    out = dict(
        evidence_class="HOLDOUT-DTI",
        evaluator_version=INSTRUMENT,
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        label=("HOLDOUT-DTI on catalogue-recovery proxy truth (withheld whole components); "
               "not a leaderboard forecast; protocol item 3"),
        n_withheld_positive_pixels=pooled["A1_sigma_ribbon"]["n_truth"],
        arms=pooled,
        per_quadrant={k: v for k, v in arms.items()},
        reference=ref,
        paired_A1_minus_A0=dict(
            delta=pooled["A1_sigma_ribbon"]["dti"] - pooled["A0_single_line"]["dti"],
            ci95_quadrant_cluster_bootstrap=ci, draws=n_draws, clusters=len(qs),
            note="paired percentile bootstrap over the 4 spatial quadrants (both seeds pooled per quadrant); coarse, 4 clusters"),
        simulated_gain_per_class=class_rows,
        cross_fitted_selection={q: {f"{k[0]}@{k[1]:g}r{k[2]}": v for k, v in d.items()}
                                for q, d in outer_params.items()},
    )
    (EVID / "exp2_holdout_arms.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(dict(arms=pooled, ref=(ref or {}).get("dti"), paired=out["paired_A1_minus_A0"]),
                     indent=1))
    return 0


# ----------------------------------------------------------------- EXP-3


def exp3(emit_stamp: str) -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    surf, grid, ctx, segs = _load_state()
    shape = grid.footprint.shape
    exp1 = json.loads((EVID / "exp1_sigma_canary.json").read_text())
    exp2 = json.loads((EVID / "exp2_holdout_arms.json").read_text())
    sigma_rows = [S.SegSigma(**r) for r in exp1["sigma_rows"]]
    selection = exp2["cross_fitted_selection"]

    # production parameters: majority vote of the outer selections
    keys_by_stratum = {}
    for q, d in selection.items():
        for k, v in d.items():
            keys_by_stratum.setdefault(k, []).append(v)
    majority: dict[str, dict[int, str]] = {}
    for k, votes in keys_by_stratum.items():
        per_bin: dict[int, str] = {}
        for b in (0, 1, 2):
            names = [v.get(str(b), v.get(b, "DROP")) for v in votes]
            names = [n for n in names if n]
            drop = sum(1 for n in names if n == "DROP")
            keep = [n for n in names if n != "DROP"]
            if keep and drop <= len(names) - drop:
                # most-chosen pattern among keep votes; ties -> simpler
                counts = {n: keep.count(n) for n in set(keep)}
                best = max(counts.items(), key=lambda kv: (kv[1], -P.PATTERNS.index(
                    next(p for p in P.PATTERNS if p.name == kv[0]))))
                per_bin[b] = best[0]
            else:
                per_bin[b] = "DROP"
        majority[k] = per_bin

    # strength bins (same rule as EXP-2, recomputed on the production segments)
    strat: dict[tuple, list] = {}
    for s in segs:
        strat.setdefault(_seg_stratum(s), []).append(s)
    bin_of: dict[int, int] = {}
    for _key, group in strat.items():
        strengths = np.array([s.strength for s in group])
        q1, q2 = np.quantile(strengths, [1 / 3, 2 / 3])
        for s in group:
            bin_of[id(s)] = 0 if s.strength >= q2 else (1 if s.strength >= q1 else 2)

    # production emission: all-fold sigma (no outer restriction) + majority patterns
    kept: list[tuple] = []       # (strength, dots, seg)
    for key, group in sorted(strat.items()):
        band, scale, rcls = key
        fam = SU.EDGE_BANDS[[b for b, _i, _f in SU.EDGE_BANDS].index(band)][2]
        for s in group:
            b = bin_of[id(s)]
            pn = majority.get(f"{band}@{scale:g}r{rcls}", {}).get(b, "DROP")
            if pn == "DROP":
                continue
            pat = next(p for p in P.PATTERNS if p.name == pn)
            sig, src = S.sigma_for(fam, s.band, s.scale, s.relief_class,
                                   S.block_of(s.centroid, shape), sigma_rows)
            d = _seg_dots(s, pat, sig, shape)
            if len(d):
                kept.append((s.strength, d, s, pn, sig, src["source"]))
    kept.sort(key=lambda t: -t[0])

    # catalogue prune B=2 (H33 mechanism) and footprint clip, then budget cap
    from scipy.ndimage import binary_dilation
    prune = binary_dilation(grid.catalogue, structure=np.ones((5, 5), bool))
    dots_rows = []
    total = 0
    for strength, d, s, pn, sig, src in kept:
        ok = ~prune[d[:, 0], d[:, 1]] & grid.footprint[d[:, 0], d[:, 1]]
        d = d[ok]
        if not len(d):
            continue
        if total + len(d) > N_BUDGET:
            d = d[: max(0, N_BUDGET - total)]
            if not len(d):
                break
        total += len(d)
        dots_rows.append((d, s, pn, strength, sig, src))
    dots = np.concatenate([r[0] for r in dots_rows]) if dots_rows else np.zeros((0, 2), int)
    mask = np.zeros(shape, bool)
    mask[dots[:, 0], dots[:, 1]] = True
    assert mask.sum() == len(np.unique(dots, axis=0)), "duplicate dots after merge"

    pred = mask.astype(np.float32)
    pred[~grid.footprint] = 0.0
    pred[grid.catalogue] = 0.0
    assert np.isfinite(pred).all() and pred.min() >= 0.0 and pred.max() <= 1.0

    # ---- uniqueness: pre-placement surface screen + final dot screen
    sys.path.insert(0, str(ROOT / "scripts"))
    from gems61_screen import screen_fast
    from scipy.ndimage import distance_transform_edt as _edt
    witness_dir = ROOT / ".cache" / "registry"
    meta_cache = ROOT / ".cache" / "registry_meta"
    paths = sorted(witness_dir.glob("*.tif"))
    reg = json.loads((ROOT / "registry" / "registry_refreshed.json").read_text())
    src_by_sha = {r["sha256"]: ";".join(r.get("sources", [])[:2]) for r in reg["rasters"]}

    def name_of(p):
        return f"{p.stem[:12]} {src_by_sha.get(p.stem, '')}"[:160]

    surface_support = (surf.strength > 0) & grid.footprint
    print(f"uniqueness pre-placement screen vs {len(paths)} witnesses ...", flush=True)
    pre = screen_fast(surface_support, paths, grid.footprint, name_of, cache_dir=meta_cache)
    if "error" in pre:
        raise RuntimeError(pre)
    print(f"uniqueness final-dot screen (pre gap-pass) vs {len(paths)} witnesses ...", flush=True)
    post0 = screen_fast(mask, paths, grid.footprint, name_of, cache_dir=meta_cache)
    if "error" in post0:
        raise RuntimeError(post0)

    # H7-C preregistered registry-gap pass (hypotheses_session7.md, rank 3): trim ONLY
    # against INFORMATIVE firings of the governing RATIFIED-UNIQ-v1 rule (rule A: O>0.70
    # with E<0.70; rule B: lift>0.50 with E<0.99).  Saturated/vacuous witnesses (E>=0.99,
    # whole-footprint surfaces) fire on every nonempty candidate and are NOT evidence of
    # lane drift — trimming against them would delete any emission and manufacture a
    # vacuous clearance on a degenerate raster (IR-58-S7-05).  Removal-only within the
    # informative set, weakest-strength dots first, until forward overlap <= GAP_CAP.
    GAP_CAP = 0.68
    dot_strength = np.concatenate([np.full(len(r[0]), r[3], np.float64) for r in dots_rows])
    dot_yx = dots
    keep = np.ones(len(dot_yx), bool)
    gap_log = []

    def _informative(s):
        e = s["chance_expected_overlap"]
        lift = s["chance_corrected_lift"]
        rule_a = s["forward_overlap"] > 0.70 and np.isfinite(e) and e < 0.70
        rule_b = np.isfinite(lift) and lift > 0.50 and np.isfinite(e) and e < 0.99
        return rule_a or rule_b

    firings = [s for s in post0["screens"] if _informative(s) and s["forward_overlap"] > GAP_CAP]
    sha_by_name = {}
    for p in paths:
        sha_by_name[name_of(p)] = p
    for s in firings:
        p = sha_by_name.get(s["name"])
        if p is None:
            continue
        import rasterio as _rio
        with _rio.open(p) as src:
            a = src.read(1)
        other = np.isfinite(a) & (a > 0) & grid.footprint
        if not other.any():
            continue
        other_dil = _edt(~other) <= 3.0
        inside = other_dil[dot_yx[:, 0], dot_yx[:, 1]]
        n = int(keep.sum())
        m = int((inside & keep).sum())
        need = 0
        if n > 0 and m / n > GAP_CAP:
            need = int(np.ceil((m - GAP_CAP * n) / (1.0 - GAP_CAP)))
        if need > 0:
            idx_inside = np.flatnonzero(inside & keep)
            order = idx_inside[np.argsort(dot_strength[idx_inside], kind="stable")]
            keep[order[:need]] = False
        gap_log.append(dict(witness=s["name"], forward_before=s["forward_overlap"],
                            removed=need, witness_sha=p.stem))
    if gap_log:
        dots = dots[keep]
        dot_yx = dots
        mask = np.zeros(shape, bool)
        mask[dots[:, 0], dots[:, 1]] = True
        pred = mask.astype(np.float32)
        pred[~grid.footprint] = 0.0
        pred[grid.catalogue] = 0.0
        print(f"H7-C gap pass: {len(gap_log)} witnesses trimmed, {int((~keep).sum())} dots removed",
              flush=True)
        print("uniqueness final-dot screen (post gap-pass) ...", flush=True)
        post = screen_fast(mask, paths, grid.footprint, name_of, cache_dir=meta_cache)
        if "error" in post:
            raise RuntimeError(post)
    else:
        post = post0

    verdict = "UNIQUE"
    worst = dict(rho=post["summary"]["worst_rho"],
                 forward=post["summary"]["worst_forward_overlap"])

    def readings(screens):
        lit = [s["name"] for s in screens if s["forward_overlap"] > 0.70]
        rule_a = [s["name"] for s in screens if s["forward_overlap"] > 0.70
                  and np.isfinite(s["chance_expected_overlap"])
                  and s["chance_expected_overlap"] < 0.70]
        rule_b = [s["name"] for s in screens if np.isfinite(s["chance_corrected_lift"])
                  and s["chance_corrected_lift"] > 0.50
                  and np.isfinite(s["chance_expected_overlap"])
                  and s["chance_expected_overlap"] < 0.99]
        rho_f = [s["name"] for s in screens if s["rho"] > 0.90]
        return dict(literal_overlap_firings=len(lit), literal_names=lit[:12],
                    rule_a_informative=len(rule_a), rule_a_names=rule_a[:12],
                    rule_b_lift=len(rule_b), rule_b_names=rule_b[:12],
                    rho_firings=len(rho_f), rho_names=rho_f[:12],
                    saturated_overlap_firings=len([s for s in screens
                                                   if s["forward_overlap"] > 0.70
                                                   and s["saturated"]]))

    read_final = readings(post["screens"])
    ratified_fires = (read_final["rule_a_informative"] > 0 or read_final["rule_b_lift"] > 0
                      or read_final["rho_firings"] > 0)
    literal_fires = read_final["literal_overlap_firings"] > 0 or read_final["rho_firings"] > 0
    if ratified_fires:
        verdict = "DUPLICATE_OR_DRIFT"
    elif literal_fires:
        verdict = "UNIQUE_UNDER_RATIFIED_LITERAL_FIRES"
    else:
        verdict = "UNIQUE"

    stamp = emit_stamp
    stem = f"gems61-deepedge-sigribbon-{len(dots)}-{stamp}"
    out_dir = ROOT / "docs" / "downloads"
    tif = out_dir / f"{stem}.tif"
    name = f"h61a-deepedge-sigribbon-{stamp}"
    holdout_dti = exp2["arms"]["A1_sigma_ribbon"]["dti"]
    note = (f"H7-A deep-edge sigma-ribbon, {len(dots)} dots @1.0, 0 on catalogue; "
            f"HOLDOUT-DTI {holdout_dti:.4f}; uniq {verdict[:9]}")[:140]

    from gems57.submission_writer import write_submission
    receipt = write_submission(tif, pred, ROOT / "data" / "bridge" / "sample_submission.tif",
                              grid.footprint, note=note, name=name,
                              catalogue=grid.catalogue,
                              metadata=dict(hypothesis="H7-A/H7-B/H7-C", instrument=INSTRUMENT))

    run_card = dict(
        hypothesis="H7-A: deep-structure step edges (depth_to_base_surf, cond_surf, tc) with "
                   "sigma-adaptive parallel dotted ribbons (H7-B relief-conditioned width, "
                   "H7-C registry-gap uniqueness selection)",
        mechanism=("step-edge (first-derivative) detector on subsurface/magnetic-structure "
                   "surfaces finds cover-buried faults absent from the surface-trace catalogue; "
                   "ribbon width matches the measured ridge->truth localization error; "
                   "per-stratum pattern chosen by exact-metric U; dots exactly 1.0"),
        non_fault_mimic=("lithologic contacts and basin-fill pinch-outs, dike swarms, alteration "
                         "fronts, survey-footprint edges"),
        holdout=dict(label="HOLDOUT-DTI (catalogue-recovery proxy; NOT a leaderboard score)",
                     evaluator=INSTRUMENT,
                     withheld_positive_pixels=exp2["n_withheld_positive_pixels"],
                     A1_sigma_ribbon=exp2["arms"]["A1_sigma_ribbon"],
                     A0_single_line=exp2["arms"]["A0_single_line"],
                     reference=exp2.get("reference"),
                     paired_A1_minus_A0=exp2["paired_A1_minus_A0"]),
        canary=exp1["canary_verdict"],
        sigma_table=exp1["sigma_table"],
        simulated_gain_per_class_file=str(EVID / "exp2_holdout_arms.json"),
        uniqueness=dict(verdict=verdict,
                        n_witnesses=len(paths),
                        worst_rho_final=worst["rho"],
                        worst_forward_overlap_final=worst["forward"],
                        readings_final=read_final,
                        readings_pre_gap=readings(post0["screens"]),
                        gap_pass=gap_log,
                        pre_placement=pre["summary"],
                        final=post["summary"],
                        instrument="scripts/gems61_screen.py (definitions = "
                                   "gems57.uniqueness via gems58w.uniqueness; forward = "
                                   "fraction of MY dots within 3 px of their dots; "
                                   "governing rule RATIFIED-UNIQ-v1, literal reading published "
                                   "beside it)"),
        raster=dict(path=str(tif.relative_to(ROOT)), sha256=receipt["sha256"],
                    decoded_prediction_sha256=receipt["decoded_prediction_sha256"],
                    dots=int(len(dots)),
                    validator=receipt["validator"]),
        submission=dict(name=name, note=note, note_chars=len(note),
                        download=f"docs/downloads/{stem}.tif"),
        verdict="promote" if (
            verdict in ("UNIQUE", "UNIQUE_UNDER_RATIFIED_LITERAL_FIRES")
            and exp2["paired_A1_minus_A0"]["delta"] > 0
            and exp2["paired_A1_minus_A0"]["ci95_quadrant_cluster_bootstrap"][0] > 0
            and exp1["canary_verdict"] == "CLEAN"
            and exp2.get("reference") is not None
            and exp2["arms"]["A1_sigma_ribbon"]["dti"] > exp2["reference"]["dti"]
            and len(dots) >= 1000
        ) else "negative",
        verdict_rule=("promote requires ALL of: uniqueness clear under RATIFIED-UNIQ-v1; "
                      "paired A1-A0 HOLDOUT-DTI delta > 0 with the 95% CI lower bound > 0; "
                      "leakage canary CLEAN; cross-fitted pooled HOLDOUT-DTI above the "
                      "same-instrument reference arm (the published session-5 concordance file "
                      "re-scored on this instrument); and a non-degenerate emission "
                      "(>= 1000 dots — a vacuous clearance on a 0-dot raster is not a "
                      "candidate). AMENDED PREREGISTRATION (before EXP-3): "
                      "the initial bar 'A1 > 0.043575' was withdrawn after measuring that "
                      "0.043575 comes from a different withhold instrument "
                      "(gems58-pooled-hide-v1, 60,988 withheld positives) and is not "
                      "like-for-like with gems61-buffered-hide-v1; the same-instrument "
                      "reference replaces it. See IRREGULARITIES IR-58-S7-02."),
        slots_used=0,
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    (EVID / "run_card.json").write_text(json.dumps(run_card, indent=1) + "\n")
    (EVID / "uniqueness_post.json").write_text(json.dumps(post, indent=1) + "\n")
    (EVID / "uniqueness_pre.json").write_text(json.dumps(pre, indent=1) + "\n")
    (EVID / "emission.json").write_text(json.dumps(dict(
        evidence_class="LOCAL-MEASUREMENT", dots=len(dots), stem=stem,
        per_segment=[dict(n=int(len(d)), pattern=pn, strength=st, sigma=sig,
                          sigma_source=src, band=s.band, scale=s.scale,
                          relief_class=s.relief_class, family=s.family)
                     for d, s, pn, st, sig, src in dots_rows],
        majority_vote=majority,
    ), indent=1, default=str) + "\n")
    print(f"emitted {len(dots)} dots -> {tif}")
    print(f"uniqueness: {verdict} (worst rho {worst['rho']:.4f}, "
          f"worst forward {worst['forward']:.4f}, {len(paths)} witnesses)")
    print(f"verdict: {run_card['verdict']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp", choices=["exp1", "exp2", "exp3"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    args = ap.parse_args()
    if args.exp == "exp1":
        return exp1(force=args.force)
    if args.exp == "exp2":
        return exp2()
    return exp3(args.stamp)


if __name__ == "__main__":
    raise SystemExit(main())
