#!/usr/bin/env python3
"""Session-6 ribbon lane: sigma measurement, exact-metric geometry choice, emission.

Protocol (fixed before the first measurement, see docs/s6/PROTOCOL.md):

* holdout = buffered hide-and-recover over the four spatial blocks of the mapped
  catalogue (``gems58w.holdout``, protocol ``gems58-pooled-hide-v1``);
* every number is pooled exact DTI (alpha 0.2, beta 0.8, 300 m triangular
  kernel) computed with the shared ``gems57.metric``;
* the candidate ridge field is read only from the organizer's 19-band stack, so
  withholding catalogue segments cannot change it;
* patterns are compared at an EQUAL DOT BUDGET, and the per-class width choice is
  made with the lane's exact utility rule
  ``U = (1 - alpha*DTI0)*dTP - alpha*DTI0*dFP`` with ``DTI0`` the pooled
  holdout DTI of the incumbent pattern.

Subcommands:  sigma | canary | geom | emit | all
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("GEMS_FEATURE_STACK", str(Path.home() / ".cache/gems/training_features.tif"))

from gems57 import metric as M                      # noqa: E402  (shared evaluator)
from gems58w import extract, grid, holdout, ridges, sigma as sigmod  # noqa: E402

EV = ROOT / "evidence" / "s6"
PROTOCOL = "gems58-pooled-hide-v1"
EVALUATOR = "gems57.metric/shared"
ALPHA, BETA, RADIUS = M.ALPHA, M.BETA, M.RADIUS_PX


# --------------------------------------------------------------------------
# geometry: place dot ribbons along ridge segments
# --------------------------------------------------------------------------

@dataclass
class Pattern:
    """Across-strike parallel-line pattern.

    ``n_lines`` is odd: offsets are 0, +-s, +-2s, ... The along-strike dot
    pitch is ``pitch`` pixels; a pitch of 2 or more keeps every dot isolated
    (no two dots 8-adjacent), which is what every high-scoring registry raster
    in this family has.
    """
    n_lines: int
    spacing: float
    pitch: int

    def key(self) -> str:
        return f"K{self.n_lines}_s{self.spacing:g}_p{self.pitch}"

    def offsets(self) -> list[float]:
        half = self.n_lines // 2
        return sorted({round(i * self.spacing, 6) for i in range(-half, half + 1)})


def _axis(idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Principal (along-strike u, across-strike n) unit vectors of a pixel set."""
    p = idx.astype(np.float64)
    c = p.mean(axis=0)
    q = p - c
    if len(p) < 2:
        return np.array([1.0, 0.0]), np.array([0.0, 1.0])
    cov = q.T @ q / max(len(p) - 1, 1)
    w, v = np.linalg.eigh(cov)
    return v[:, -1], v[:, 0]


def segment_dots(idx: np.ndarray, field: dict, pat: Pattern,
                 allowed: np.ndarray | None = None) -> np.ndarray:
    """Dot coordinates (n,2) for one ridge segment under pattern ``pat``."""
    h, w = field["mag"].shape
    u, nvec = _axis(idx)
    t = idx.astype(np.float64) @ u
    order = np.argsort(t, kind="stable")
    idx = idx[order]
    t = t[order]
    # along-strike thinning: walk the ordered pixels, keep one every `pitch` px
    keep = [0]
    for i in range(1, len(idx)):
        if t[i] - t[keep[-1]] >= pat.pitch - 0.25:
            keep.append(i)
    idx = idx[keep]
    ax = field["ax"][idx[:, 0], idx[:, 1]]
    ay = field["ay"][idx[:, 0], idx[:, 1]]
    # fall back to the segment normal where the field vector is degenerate
    bad = ~(np.isfinite(ax) & np.isfinite(ay)) | ((np.abs(ax) + np.abs(ay)) < 1e-6)
    ax = np.where(bad, nvec[1], ax)
    ay = np.where(bad, nvec[0], ay)
    out = []
    for o in pat.offsets():
        rr = np.rint(idx[:, 0] + o * ay).astype(int)
        cc = np.rint(idx[:, 1] + o * ax).astype(int)
        ok = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        out.append(np.stack([rr[ok], cc[ok]], axis=1))
    dots = np.concatenate(out, axis=0) if out else np.zeros((0, 2), int)
    if allowed is not None:
        dots = dots[allowed[dots[:, 0], dots[:, 1]]]
    return np.unique(dots, axis=0)


_THIN: dict[tuple, tuple] = {}


def thinned(idx: np.ndarray, field: dict, pitch: int, tag: int):
    """Cacheable along-strike thinning + across-strike unit vectors for a segment."""
    key = (tag, pitch)
    hit = _THIN.get(key)
    if hit is not None:
        return hit
    u, nvec = _axis(idx)
    t = idx.astype(np.float64) @ u
    order = np.argsort(t, kind="stable")
    idx = idx[order]
    t = t[order]
    keep = [0]
    for i in range(1, len(idx)):
        if t[i] - t[keep[-1]] >= pitch - 0.25:
            keep.append(i)
    idx = idx[keep]
    ax = field["ax"][idx[:, 0], idx[:, 1]]
    ay = field["ay"][idx[:, 0], idx[:, 1]]
    bad = ~(np.isfinite(ax) & np.isfinite(ay)) | ((np.abs(ax) + np.abs(ay)) < 1e-6)
    ax = np.where(bad, nvec[1], ax).astype(np.float32)
    ay = np.where(bad, nvec[0], ay).astype(np.float32)
    _THIN[key] = (idx, ax, ay)
    return _THIN[key]


def isolate(mask: np.ndarray) -> np.ndarray:
    """Keep one pixel per 8-connected cluster, so every dot is isolated.

    Every registry raster scoring above 0.23 in this family has its largest
    8-connected component equal to 1 pixel (measured, docs/s6/LIVE_CALIBRATION.md).
    Two touching dots can earn at most the same truth credit as one, for 0.2 more
    false-positive mass each, so the survivor is kept and its neighbours dropped.
    """
    lab, n = label(mask, structure=np.ones((3, 3), int))
    if n == 0:
        return mask
    sel = np.argwhere(lab > 0)
    comp = lab[sel[:, 0], sel[:, 1]]
    order = np.lexsort((sel[:, 1], sel[:, 0], comp))
    sel, comp = sel[order], comp[order]
    first = np.r_[True, comp[1:] != comp[:-1]]
    out = np.zeros(mask.shape, bool)
    out[sel[first, 0], sel[first, 1]] = True
    return out


def emit(field: dict, segs: list, pat_of, allowed: np.ndarray,
         budget: int, order_key=None) -> tuple[np.ndarray, list]:
    """Emit dots over ranked segments until ``budget`` distinct dots are placed."""
    mask = np.zeros(field["mag"].shape, bool)
    if order_key is None:
        order_key = lambda s: s["mag"] * s["size"]          # noqa: E731
    plans = []
    h, w = mask.shape
    placed = 0
    for s in sorted(segs, key=order_key, reverse=True):
        if placed >= budget:
            break
        pat = pat_of(s)
        idx, ax, ay = thinned(s["idx"], field, pat.pitch, s["tag"])
        chunks = []
        for o in pat.offsets():
            rr = np.rint(idx[:, 0] + o * ay).astype(int)
            cc = np.rint(idx[:, 1] + o * ax).astype(int)
            ok = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
            chunks.append(np.stack([rr[ok], cc[ok]], axis=1))
        if not chunks:
            continue
        d = np.concatenate(chunks, axis=0)
        d = np.unique(d, axis=0)
        d = d[~mask[d[:, 0], d[:, 1]]]
        d = d[allowed[d[:, 0], d[:, 1]]]
        if d.size == 0:
            continue
        room = budget - placed
        if d.shape[0] > room:
            d = d[:room]
        mask[d[:, 0], d[:, 1]] = True
        placed += int(d.shape[0])
        plans.append(dict(size=s["size"], mag=float(s["mag"]), pattern=pat.key(),
                          dots=int(d.shape[0]),
                          stratum=s.get("stratum", "?"), sigma=s.get("sigma", None)))
    return mask, plans


def score_fold(dots: np.ndarray, fold) -> dict:
    """Exact DTI terms of a dot mask on one holdout fold."""
    active = fold.valid & ~fold.known
    p = dots & active
    g = fold.withhold & active
    r = M.dti_binary(p, g, valid=active)
    return dict(tp=float(r["tp"]), fp=float(r["fp"]), fn=float(r["fn"]),
                n_truth=int(r["n_truth"]), n_emitted=int(r["n_emitted"]),
                dti=float(r["dti"]), coverage=float(r["coverage"]))


def pool(terms: list[dict]) -> dict:
    tp = sum(t["tp"] for t in terms)
    fp = sum(t["fp"] for t in terms)
    fn = sum(t["fn"] for t in terms)
    g = sum(t["n_truth"] for t in terms)
    n = sum(t["n_emitted"] for t in terms)
    dti = M.dti_from_components(tp, fp, fn)
    return dict(evidence_class="HOLDOUT-DTI", evaluator=EVALUATOR, protocol=PROTOCOL,
                tp=tp, fp=fp, fn=fn, n_truth=g, n_emitted=n,
                dti=dti, coverage=tp / max(g, 1),
                credit_per_dot=tp / max(n, 1))


# --------------------------------------------------------------------------
# stage: sigma
# --------------------------------------------------------------------------

def stage_sigma(threshold: float = 0.5, min_px: int = 6, out: str = "sigma.json") -> dict:
    t0 = time.time()
    field = extract.build(workers=2)
    segs = extract.segments(field, threshold, min_px=min_px)
    folds = holdout.all_folds()
    items, per_fold = [], {}
    for f in folds:
        it = sigmod.measure(field, segs, f)
        items.extend(it)
        tbl = sigmod.sigma_table(it)
        per_fold[f.name] = dict(n_withheld_px=int(f.n_truth),
                                n_withheld_components_matched=tbl["n_matched"],
                                pooled=tbl["pooled"], by_scale=tbl["by_scale"])
        print(f"[{f.name}] withheld {f.n_truth} px | matched components "
              f"{tbl['n_matched']} | sigma median "
              f"{tbl['pooled']['median'] if tbl['pooled'] else float('nan'):.3f}", flush=True)
    table = sigmod.sigma_table(items)
    res = dict(evidence_class="HOLDOUT-STRUCTURE", protocol=PROTOCOL, evaluator=EVALUATOR,
               threshold=threshold, min_px=min_px,
               n_segments=len(segs), ridge_px=int(sum(s["size"] for s in segs)),
               n_matched_components=len(items),
               per_fold=per_fold, table=table,
               per_component=[i.as_dict() for i in items],
               wall_seconds=round(time.time() - t0, 1))
    EV.mkdir(parents=True, exist_ok=True)
    (EV / out).write_text(json.dumps(res, indent=1, default=float))
    print("wrote", EV / out)
    return res


# --------------------------------------------------------------------------
# stage: leakage canary (single-feature AUC on the holdout)
# --------------------------------------------------------------------------

def stage_canary(out: str = "canary.json") -> dict:
    from gems58w import features as F
    from sklearn.metrics import roc_auc_score

    t0 = time.time()
    fp = grid.footprint()
    folds = holdout.all_folds()
    rng = np.random.default_rng(20261011)
    aucs = {}
    for name in F.BANDS:
        v = F.band(name).astype(np.float32)
        v[~np.isfinite(v)] = np.nan
        per_fold = []
        for f in folds:
            active = f.valid & ~f.known
            pos = np.flatnonzero((f.withhold & active).ravel())
            neg_all = np.flatnonzero((~f.withhold & active & np.isfinite(v)).ravel())
            if pos.size < 20 or neg_all.size < 100:
                continue
            neg = rng.choice(neg_all, size=min(20 * pos.size, neg_all.size), replace=False)
            y = np.r_[np.ones(pos.size), np.zeros(neg.size)]
            x = v.ravel()[np.r_[pos, neg]]
            ok = np.isfinite(x)
            per_fold.append(roc_auc_score(y[ok], x[ok]))
        if per_fold:
            aucs[name] = float(np.mean(per_fold))
        print(f"  {name:22s} AUC {aucs.get(name, float('nan')):.4f}", flush=True)
    worst = max(aucs.values())
    res = dict(evidence_class="HOLDOUT-LEAKAGE-CANARY", protocol=PROTOCOL,
               auc_by_band=aucs, max_auc=worst, limit=0.90,
               verdict="clean" if worst < 0.90 else "LEAKAGE SUSPECTED",
               wall_seconds=round(time.time() - t0, 1))
    EV.mkdir(parents=True, exist_ok=True)
    (EV / out).write_text(json.dumps(res, indent=1, default=float))
    print("worst single-feature AUC", round(worst, 4), res["verdict"])
    print("wrote", EV / out)
    return res


# --------------------------------------------------------------------------
# stage: geometry sweep
# --------------------------------------------------------------------------

PATTERN_GRID = [Pattern(1, 1.0, p) for p in (2, 3, 4)] + \
               [Pattern(3, s, p) for s in (1.0, 2.0, 3.0) for p in (2, 3)] + \
               [Pattern(5, s, p) for s in (2.0, 3.0) for p in (2, 3)] + \
               [Pattern(7, 2.0, 2)]


def _allowed(fold, collar: int) -> np.ndarray:
    """Scoreable, catalogue-free emission domain for a fold."""
    active = fold.valid & ~fold.known
    if collar > 0:
        st = np.ones((2 * collar + 1,) * 2, bool)
        active &= ~binary_dilation(fold.visible, st)
    return active


def stage_geom(threshold: float = 0.5, budget: int = 38000, collar: int = 0,
               out: str = "geom.json") -> dict:
    t0 = time.time()
    field = extract.build(workers=2)
    segs = extract.segments(field, threshold, min_px=6)
    for i, sg in enumerate(segs):
        sg["tag"] = i
    folds = holdout.all_folds()

    # ---- random control at the same budget
    rng = np.random.default_rng(61011)
    terms = []
    for f in folds:
        a = _allowed(f, collar)
        cand = np.flatnonzero(a.ravel())
        pick = rng.choice(cand, size=min(budget * len(folds) // len(folds), cand.size),
                          replace=False)
        d = np.zeros(a.shape, bool)
        d.ravel()[pick] = True
        terms.append(score_fold(d, f))
    rand = pool(terms)
    print(f"RANDOM control: DTI {rand['dti']:.6f}  n={rand['n_emitted']}", flush=True)

    # ---- pattern sweep
    rows = []
    for pat in PATTERN_GRID:
        terms = []
        for f in folds:
            a = _allowed(f, collar)
            m, _ = emit(field, segs, lambda s, p=pat: p, a, budget)
            terms.append(score_fold(m, f))
        r = pool(terms)
        r.update(pattern=pat.key(), n_lines=pat.n_lines, spacing=pat.spacing,
                 pitch=pat.pitch, offsets=pat.offsets())
        rows.append(r)
        print(f"  {pat.key():16s} DTI {r['dti']:.6f}  n={r['n_emitted']:6d} "
              f"cov {r['coverage']:.4f}  credit/dot {r['credit_per_dot']:.4f}", flush=True)

    rows_sorted = sorted(rows, key=lambda r: -r["dti"])
    best = rows_sorted[0]
    dti0 = float(best["dti"])
    res = dict(evidence_class="HOLDOUT-DTI", protocol=PROTOCOL, evaluator=EVALUATOR,
               budget=budget, threshold=threshold, collar=collar,
               random_control=rand, sweep=rows, best=best["pattern"],
               dti0_for_U_rule=dti0,
               wall_seconds=round(time.time() - t0, 1))
    EV.mkdir(parents=True, exist_ok=True)
    (EV / out).write_text(json.dumps(res, indent=1, default=float))
    print("BEST", best["pattern"], round(best["dti"], 6), "wrote", EV / out)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["sigma", "canary", "geom", "all"])
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--budget", type=int, default=38000)
    ap.add_argument("--collar", type=int, default=0)
    a = ap.parse_args()
    if a.stage in ("sigma", "all"):
        stage_sigma(a.threshold)
    if a.stage in ("canary", "all"):
        stage_canary()
    if a.stage in ("geom", "all"):
        stage_geom(a.threshold, a.budget, a.collar)
