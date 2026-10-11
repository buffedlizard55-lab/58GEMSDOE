#!/usr/bin/env python3
"""58GEMSDOE session-2 experiments E1 (leakage canary) + E2 (metric-optimal emission).

E1 -- leakage canary (parallel-run protocol rule 4)
    Every single feature is scored alone against the withheld truth on the
    hide-and-recover holdout.  AUC > 0.90 is treated as leakage until proven
    otherwise.  Reported separately for the two holdout modes:
      * ``all``      -- any wholly-interior segment may be withheld; visible
                        traces usually run into a withheld one, so catalogue
                        proximity is structurally leaky here.
      * ``detached`` -- only segments >= 4 px from every other catalogue
                        component are withheld.  This is the live analogue of a
                        genuinely unmapped splay and is the instrument the
                        shipped emission is validated on.

E2 -- metric-optimal emission
    A per-pixel fault ranking built from the sha256-pinned official 19-band
    GeoDAWN stack (leave-one-quadrant-out spatial blocking) is converted to a
    binary dot field by a global probability threshold plus 3-px non-maximum
    suppression (the 300 m kernel radius).  Every arm is scored with the shared
    exact evaluator ``gems57.holdout.score_cell`` (alpha 0.2, beta 0.8, 3 px
    triangular kernel).  ``solid`` (no thinning) is the control.

Feature families
    ``GF``  -- geophysical operators only; nothing sees the fault catalogue.
    ``CTX`` -- GF + distance to the *visible* catalogue (per fold: every segment
               withheld in any cell of that fold is removed before the distance
               transform, so the context feature cannot see withheld truth).

Every number written by this script is HOLDOUT-DTI.  Nothing is a projection.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import HEIGHT, WIDTH, load_grid         # noqa: E402
from gems57.holdout import (FOLD_NAMES, build_holdout,   # noqa: E402
                            score_cell)
from gems57.metric import ALPHA, BETA, EPS               # noqa: E402
from gems59.features import iter_blocks, open_stack      # noqa: E402

CACHE = Path.home() / ".cache" / "gems"
EVID = ROOT / "evidence"
SEEDS = (20, 21)
MODES = ("all", "detached")
NEG_PER_POS = 5
N_TRAIN_CAP = 200_000
THRESHOLDS = (0.50, 0.70, 0.80, 0.90, 0.95, 0.97, 0.98, 0.99, 0.995, 0.998, 0.999)
NMS_RADIUS_PX = 3          # 300 m kernel radius at the 100 m grid
RNG_SEED = 20261011


# --------------------------------------------------------------------------- #
# caches
# --------------------------------------------------------------------------- #
def gf_cube(stack) -> np.ndarray:
    """Full-grid geophysical feature cube as a float32 memmap (rebuilt if absent)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "feat_gf.f32"
    n = len(stack.names)
    want = n * HEIGHT * WIDTH * 4
    fresh = path.exists() and path.stat().st_size == want and (CACHE / "feat_gf.done").exists()
    mm = np.memmap(path, dtype=np.float32, mode="r+" if fresh else "w+", shape=(n, HEIGHT, WIDTH))
    if fresh:
        return mm
    t0 = time.time()
    for r0, r1, feats in iter_blocks(stack):
        mm[:, r0:r1, :] = feats
    mm.flush()
    (CACHE / "feat_gf.done").write_text(json.dumps(list(stack.names)))
    print(f"  built GF cube {mm.shape} in {time.time()-t0:.0f}s", flush=True)
    return mm


def prob_memmap(tag: str) -> np.ndarray:
    path = CACHE / f"prob_{tag}.f32"
    return np.memmap(path, dtype=np.float32, mode="w+", shape=(HEIGHT, WIDTH))


def predict_grid(model, cube, footprint, extra=None, chunk=128) -> np.ndarray:
    """Per-pixel probability over the footprint, block-wise (memory-safe)."""
    out = np.zeros((HEIGHT, WIDTH), np.float32)
    F = cube.shape[0]
    for r0 in range(0, HEIGHT, chunk):
        r1 = min(HEIGHT, r0 + chunk)
        blk = np.asarray(cube[:, r0:r1, :]).reshape(F, -1).T
        if extra is not None:
            blk = np.concatenate([blk, extra[r0:r1].reshape(-1, 1).astype(np.float32)], axis=1)
        ok = np.isfinite(blk).any(axis=1)   # HGB takes NaN natively
        if not ok.any():
            continue
        p = np.zeros(blk.shape[0], np.float32)
        p[ok] = model.predict_proba(blk[ok])[:, 1].astype(np.float32)
        out[r0:r1] = p.reshape(r1 - r0, -1)
    out[~footprint] = 0.0
    return out


def train_fold(cube, grid, quad, fold, ctx_map=None, seed=RNG_SEED) -> HistGradientBoostingClassifier:
    """One leave-one-quadrant-out classifier (fold ``fold`` is held out)."""
    cat, fp = grid.catalogue, grid.footprint
    rng = np.random.default_rng(seed + fold)
    train_q = np.isin(quad, [f for f in range(4) if f != fold])
    py, px = np.nonzero(cat & fp & train_q)
    ny, nx = np.nonzero(fp & ~cat & train_q)
    n_neg = min(ny.size, NEG_PER_POS * py.size)
    sel = rng.choice(ny.size, size=n_neg, replace=False)
    ny, nx = ny[sel], nx[sel]
    if py.size + ny.size > N_TRAIN_CAP:
        keep = N_TRAIN_CAP / (py.size + ny.size)
        py, px = py[: int(py.size * keep)], px[: int(px.size * keep)]
        ny, nx = ny[: int(ny.size * keep)], nx[: int(nx.size * keep)]
    ys = np.concatenate([py, ny]); xs = np.concatenate([px, nx])
    X = np.asarray(cube[:, ys, xs]).T.copy()
    y = np.concatenate([np.ones(py.size, np.int8), np.zeros(ny.size, np.int8)])
    if ctx_map is not None:
        X = np.concatenate([X, ctx_map[ys, xs].reshape(-1, 1).astype(np.float32)], axis=1)
    # HistGradientBoosting handles NaN natively; drop only fully-empty rows.
    good = np.isfinite(X).any(axis=1)
    X, y = X[good], y[good]
    m = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=60,
        l2_regularization=1.0, early_stopping=False, random_state=seed)
    t0 = time.time()
    m.fit(X, y)
    label = FOLD_NAMES[fold] if 0 <= fold < 4 else "ALL"
    print(f"  fold {label}{' CTX' if ctx_map is not None else ''}: "
          f"{int(y.sum())} pos / {int((y == 0).sum())} neg -> {len(m._predictors)} iters "
          f"in {time.time()-t0:.0f}s", flush=True)
    return m


# --------------------------------------------------------------------------- #
def auc_symmetric(values: np.ndarray, label: np.ndarray) -> float | None:
    """AUC made direction-free (max(a, 1-a)): the canary asks 'is it informative?'."""
    lab = np.asarray(label, bool)
    if lab.sum() == 0 or lab.sum() == lab.size:
        return None
    v = np.asarray(values, np.float64)
    ok = np.isfinite(v)
    if ok.sum() < 100 or lab[ok].sum() in (0, ok.sum()):
        return None
    a = float(roc_auc_score(lab[ok], v[ok]))
    return max(a, 1.0 - a)


CANARY_MAX_NEG = 50_000       # background pixels kept PER CELL; every withheld truth pixel is kept


def canary(cube, cells, names, ctx_maps, seed=13):
    """Single-feature AUC against the withheld truth, pooled per mode.

    Every withheld truth pixel is kept; background pixels are subsampled to
    ``CANARY_MAX_NEG`` per cell (AUC standard error at 400k pooled negatives and
    ~3k positives is < 0.01, far below the 0.90 decision line).
    """
    out = {}
    rng = np.random.default_rng(seed)
    for mode in MODES:
        idx = []
        for c in [x for x in cells if x.mode == mode]:
            ay, ax = np.nonzero(c.active)
            tmask = np.zeros(c.active.shape, bool)
            tmask[c.truth_yx] = True
            lab = tmask[ay, ax]
            neg = np.flatnonzero(~lab)
            if neg.size > CANARY_MAX_NEG:
                neg = rng.choice(neg, size=CANARY_MAX_NEG, replace=False)
            keep = np.concatenate([np.flatnonzero(lab), neg])
            keep.sort()
            idx.append((c, ay[keep], ax[keep], lab[keep].astype(np.int8)))
        aucs = {}
        for f, nm in enumerate(names):
            vals = [np.asarray(cube[f][c.bbox][ay, ax]).ravel() for c, ay, ax, _ in idx]
            labs = [lab for _, _, _, lab in idx]
            a = auc_symmetric(np.concatenate(vals), np.concatenate(labs))
            if a is not None:
                aucs[nm] = a
        vals = [-ctx_maps[c.fold][c.bbox][ay, ax].ravel() for c, ay, ax, _ in idx]
        labs = [lab for _, _, _, lab in idx]
        a = auc_symmetric(np.concatenate(vals), np.concatenate(labs))
        if a is not None:
            aucs["CTX/distance_to_visible_catalogue"] = a
        out[mode] = dict(
            n_pixels=int(sum(i[1].size for i in idx)),
            n_truth=int(sum(i[3].sum() for i in idx)),
            auc_by_feature=dict(sorted(aucs.items(), key=lambda kv: -kv[1])),
            max_auc=max(aucs.values()), max_auc_feature=max(aucs, key=aucs.get),
            leakage_flag=bool(max(aucs.values()) > 0.90),
            rule="single feature alone vs withheld truth; AUC > 0.90 = leakage until proven otherwise")
    return out


# --------------------------------------------------------------------------- #
def nms_dots(pi: np.ndarray, active: np.ndarray, radius: int = NMS_RADIUS_PX) -> np.ndarray:
    """Keep the strict local maxima of ``pi`` within a (2r+1) window; 1 dot/plateau."""
    filled = np.where(active, pi, np.float32(-np.inf))
    mx = ndi.maximum_filter(filled, size=2 * radius + 1, mode="constant", cval=-np.inf)
    keep = active & np.isfinite(pi) & (pi >= mx)
    lab, n = ndi.label(keep, structure=np.ones((3, 3), bool))
    if n == 0:
        return keep
    order = np.flatnonzero(keep.ravel())
    lv = lab.ravel()[order]
    _, first_idx = np.unique(lv, return_index=True)
    out = np.zeros(keep.shape, bool)
    out.ravel()[order[first_idx]] = True
    return out


def pooled(scores: list[dict]) -> dict:
    tp = sum(s["tp"] for s in scores); fp = sum(s["fp"] for s in scores)
    fn = sum(s["fn"] for s in scores); nt = sum(s["n_truth"] for s in scores)
    ne = sum(s["n_emitted"] for s in scores)
    return dict(pooled_dti=float(tp / (tp + ALPHA * fp + BETA * fn + EPS)),
                pooled_coverage=float(tp / nt) if nt else 0.0,
                pooled_tp=tp, pooled_fp=fp, pooled_fn=fn, dots=ne, n_truth=int(nt))


def eval_arm(cells, mode, emit_fn, thresholds) -> dict:
    res = {}
    for tau in thresholds:
        scores, per_cell = [], {}
        for c in [x for x in cells if x.mode == mode]:
            r = score_cell(c, emit_fn(c, tau))
            scores.append(r)
            per_cell[c.key] = dict(dti=r["dti"], dots=r["n_emitted"], cov=r["coverage"])
        res[str(tau)] = {**pooled(scores), "per_cell": per_cell}
    return res


def paired_bootstrap(cells, mode, fn_a, tau_a, fn_b, tau_b, draws=1000, seed=520810) -> dict:
    """Paired percentile bootstrap of the pooled-DTI difference over fold cells."""
    mc = [c for c in cells if c.mode == mode]
    A = np.array([[score_cell(c, fn_a(c, tau_a))[k] for k in ("tp", "fp", "fn")] for c in mc])
    B = np.array([[score_cell(c, fn_b(c, tau_b))[k] for k in ("tp", "fp", "fn")] for c in mc])

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
                caveat="Conditional on the fitted folds and fixed thresholds; not a leaderboard interval.")


# --------------------------------------------------------------------------- #
def main() -> int:
    t_start = time.time()
    grid = load_grid(ROOT / "data" / "bridge")
    stack = open_stack()
    cube = gf_cube(stack)
    names = list(stack.names)
    print(f"stack: {stack.path} ({len(names)} features)", flush=True)

    print("building holdout ...", flush=True)
    t0 = time.time()
    ctx = build_holdout(grid, seeds=SEEDS, modes=MODES)
    cells = ctx.cells
    print(f"  {len(cells)} cells in {time.time()-t0:.0f}s | withheld px "
          f"all={sum(c.n_truth for c in cells if c.mode == 'all')} "
          f"detached={sum(c.n_truth for c in cells if c.mode == 'detached')}", flush=True)

    quad = ctx.quad
    ctx_maps = {}
    for fold in range(4):
        hidden = np.zeros(grid.shape, bool)
        for c in cells:
            if c.fold == fold:
                hidden |= ctx.hidden_by_cell[c.key]
        ctx_maps[fold] = ndi.distance_transform_edt(~(grid.catalogue & ~hidden)).astype(np.float32)

    print("E1: leakage canary ...", flush=True)
    t0 = time.time()
    can = canary(cube, cells, names, ctx_maps)
    for mode in MODES:
        c = can[mode]
        print(f"  {mode}: n_truth={c['n_truth']} max AUC={c['max_auc']:.3f} "
              f"({c['max_auc_feature']}) leakage={c['leakage_flag']}", flush=True)
        print(f"    top5: {[(k, round(v, 3)) for k, v in list(c['auc_by_feature'].items())[:5]]}", flush=True)
    print(f"  canary in {time.time()-t0:.0f}s", flush=True)
    del cube

    # ---- LOQO predictions, one family at a time (keeps RAM bounded) ----
    prob_paths: dict[tuple[str, int], Path] = {}
    for fam in ("GF", "CTX"):
        cube = gf_cube(stack)
        for fold in range(4):
            m = train_fold(cube, grid, quad, fold,
                           ctx_map=ctx_maps[fold] if fam == "CTX" else None)
            t0 = time.time()
            p = predict_grid(m, cube, grid.footprint,
                             extra=ctx_maps[fold] if fam == "CTX" else None)
            mm = prob_memmap(f"{fam}_f{fold}")
            mm[:, :] = p
            mm.flush(); del mm
            prob_paths[(fam, fold)] = CACHE / f"prob_{fam}_f{fold}.f32"
            print(f"  predicted {fam} {FOLD_NAMES[fold]} in {time.time()-t0:.0f}s", flush=True)
            del p, m
        del cube

    prob: dict[tuple[str, int], np.ndarray] = {
        k: np.memmap(v, dtype=np.float32, mode="r", shape=(HEIGHT, WIDTH))
        for k, v in prob_paths.items()}

    def mk_dotted(fam):
        def emit(c, tau):
            pi = np.asarray(prob[(fam, c.fold)][c.bbox])
            return nms_dots(pi, c.active & (pi >= tau))
        return emit

    def mk_solid(fam):
        def emit(c, tau):
            pi = np.asarray(prob[(fam, c.fold)][c.bbox])
            return c.active & (pi >= tau)
        return emit

    fns = {f"{fam}|dotted3px": mk_dotted(fam) for fam in ("GF", "CTX")}
    fns.update({f"{fam}|solid": mk_solid(fam) for fam in ("GF", "CTX")})

    results = {"experiment": "E1-leakage-canary + E2-metric-optimal-emission",
               "evidence_class": "HOLDOUT-DTI",
               "instrument": dict(kind="hide-and-recover", seeds=list(SEEDS), modes=list(MODES),
                                  evaluator="gems57.holdout.score_cell (shared, exact)",
                                  alpha=ALPHA, beta=BETA, triangular_radius_px=3.0),
               "stack_path": str(stack.path),
               "stack_sha256": hashlib.sha256(Path(stack.path).read_bytes()).hexdigest(),
               "features": names, "canary": can, "arms": {}}

    for key, fn in fns.items():
        for mode in MODES:
            t0 = time.time()
            res = eval_arm(cells, mode, fn, THRESHOLDS)
            results["arms"][f"{key}|{mode}"] = res
            best = max(res.items(), key=lambda kv: kv[1]["pooled_dti"])
            print(f"  {key}|{mode}: best tau={best[0]} DTI={best[1]['pooled_dti']:.4f} "
                  f"dots={best[1]['dots']} cov={best[1]['pooled_coverage']:.3f} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    for mode in MODES:
        det = {k: max(v.items(), key=lambda kv: kv[1]["pooled_dti"])
               for k, v in results["arms"].items() if k.endswith(f"|{mode}")}
        best_key, (best_tau, best_val) = max(det.items(), key=lambda kv: kv[1][1]["pooled_dti"])
        results[f"best_on_{mode}"] = dict(arm=best_key, threshold=float(best_tau),
                                          **{k: v for k, v in best_val.items() if k != "per_cell"})
        print(f"BEST on {mode}: {best_key} tau={best_tau} DTI={best_val['pooled_dti']:.4f}", flush=True)

    # paired CI: best dotted arm vs its own solid control, per mode
    results["paired"] = {}
    for mode in MODES:
        fam = results[f"best_on_{mode}"]["arm"].split("|")[0]
        tau = results[f"best_on_{mode}"]["threshold"]
        solid = max(results["arms"][f"{fam}|solid|{mode}"].items(),
                    key=lambda kv: kv[1]["pooled_dti"])
        results["paired"][f"dotted3px_minus_solid|{mode}"] = paired_bootstrap(
            cells, mode, fns[f"{fam}|dotted3px"], tau, fns[f"{fam}|solid"], float(solid[0]))
        results["paired"][f"dotted3px_minus_solid|{mode}"]["solid_control_tau"] = float(solid[0])
        print(f"  paired dotted-solid ({mode}): "
              f"{results['paired'][f'dotted3px_minus_solid|{mode}']['delta']:+.4f} "
              f"CI95 {results['paired'][f'dotted3px_minus_solid|{mode}']['ci95']}", flush=True)

    EVID.mkdir(exist_ok=True)
    (EVID / "model_e1e2.json").write_text(json.dumps(results, indent=1, default=float) + "\n")
    print(f"wrote evidence/model_e1e2.json | total {time.time()-t_start:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
