"""Sigma-calibrated ribbon emission: the session-6 lane implementation.

The lane question, implemented literally
----------------------------------------
1. **sigma(x) by data block, feature resolution and ridge type.**  For every
   (family, scale, sign) ridge class the Euclidean distance from every withheld
   catalogue pixel to the nearest ridge pixel of that class is measured on the
   shared buffered hide-and-recover instrument (``gems58w.holdout``, protocol
   ``gems58-pooled-hide-v1``: whole 8-connected catalogue components withheld by
   spatial block, 3 px buffer around visible faults, visible faults masked
   pixel-exactly).  A component is *matched* by a class when at least
   ``MIN_FRAC`` of its pixels lie within ``L_MAX`` px; its localisation error is
   the RMS of ``min(d, L_MAX)`` over its pixels.  ``sigma`` is the mean over the
   matched components of a block, and the value used for a block is always the
   **leave-one-block-out** mean of the other three blocks.
2. **Parallel dotted line choice per class.**  A pattern is a tuple of
   across-strike offsets in pixels -- ``(0,)`` for one tight line, ``(-3, 0, 3)``
   for three parallel dotted lines at the 3 px (300 m) kernel radius.  Every
   pattern is scored with the **exact** metric arithmetic (TP = sum over withheld
   truth pixels of the best kernel credit within 3 px of the pattern's dots;
   FP = sum over dots of ``1 - kernel(distance to nearest withheld pixel)`` --
   the same formulas as ``gems58w.metric.dti_binary``, checked against it by
   :func:`crosscheck_fast_vs_shared`).  Its marginal utility against the
   single-line base is

       U = (1 - 0.2 * DTI0) * dTP - 0.2 * DTI0 * dFP

   with ``DTI0`` the pooled single-line base DTI of this lane on the same
   instrument.  The largest-U pattern per class is emitted; ties go to fewer
   lines.
3. **Emission.**  Winning patterns are applied to the full-region ridge field,
   dots are ranked by ridge magnitude, thinned to the lane budget, catalogue
   pixels are dropped (the scorer masks them and the shared writer refuses
   them), and a uniqueness repair removes the weakest dots inside the support of
   any informative inventory witness until the overlap clears.  Every emitted dot
   carries the value exactly ``1.0``.

No catalogue-derived feature is used anywhere: the ridge field is read from the
geophysical layers only, which is what makes the measurement leakage-free.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.spatial import cKDTree

from gems58w import holdout as HO
from gems58w import metric as M58
from gems58w.grid import catalogue, footprint
from gems57.metric import RADIUS_PX as KERNEL_PX
from gems57.metric import kernel as tri_kernel

from . import detect

MIN_COMP_PX = 8
MIN_FRAC = 0.6
MIN_PAIRS = 10
L_MAX = 15.0
SIGMA_FLOOR = 0.5
SIGMA_CAP = 6.0
OVERLAP_LIMIT = 0.70

#: Pattern ladder: across-strike offsets in pixels.  The ribbon spacing is the
#: 3 px kernel radius (300 m) or half of it, as the lane requires.
PATTERNS: dict[str, tuple[float, ...]] = {
    "single": (0.0,),
    "pair-1": (-1.0, 1.0),
    "pair-2": (-2.0, 2.0),
    "pair-3": (-3.0, 3.0),
    "trio-2": (-2.0, 0.0, 2.0),
    "trio-3": (-3.0, 0.0, 3.0),
    "quint-3": (-3.0, -1.5, 0.0, 1.5, 3.0),
}


def disc(radius: float = 3.0) -> np.ndarray:
    """Circular structuring element of the protocol's 3 px kernel radius."""
    r = int(np.ceil(radius))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return (yy * yy + xx * xx) <= radius * radius


# ------------------------------------------------------------------ fold glue
def fold_active(fold: HO.Fold) -> np.ndarray:
    """Scored domain of a fold: footprint minus the masked visible catalogue+buffer."""
    return footprint() & ~fold.known


def fold_truth(fold: HO.Fold) -> np.ndarray:
    return fold.withhold & fold_active(fold)


def fold_truth_distance(fold: HO.Fold) -> np.ndarray:
    """Distance (px) from every pixel to the fold's withheld truth (float32)."""
    g = fold_truth(fold)
    return distance_transform_edt(~g).astype(np.float32)


# --------------------------------------------------------------- exact scoring
def score_dots(dots_rc: np.ndarray, fold: HO.Fold, truth_dist: np.ndarray) -> dict:
    """Exact-metric components of a dot set on one fold.

    Identical arithmetic to ``gems58w.metric.dti_binary`` (a KD-tree replaces the
    second distance transform); :func:`crosscheck_fast_vs_shared` checks equality
    against the shared implementation.
    """
    active = fold_active(fold)
    g = fold_truth(fold)
    if not g.any():
        raise ValueError(f"fold {fold.name} has no withheld truth inside the active domain")
    if dots_rc.size:
        keep = (dots_rc[:, 0] >= 0) & (dots_rc[:, 0] < g.shape[0]) & \
               (dots_rc[:, 1] >= 0) & (dots_rc[:, 1] < g.shape[1])
        dots_rc = dots_rc[keep]
        on = active[dots_rc[:, 0], dots_rc[:, 1]]
        dots_rc = dots_rc[on]
    n = int(g.sum())
    if dots_rc.shape[0] == 0:
        return dict(dti=0.0, tp=0.0, fp=0.0, fn=float(n), n_truth=n, n_dots=0)
    ty, tx = np.nonzero(g)
    tree = cKDTree(dots_rc.astype(np.float64))
    d_g_to_p, _ = tree.query(np.stack([ty, tx], axis=1).astype(np.float64), k=1, workers=1)
    tp = float(tri_kernel(d_g_to_p, RADIUS).sum())
    d_p_to_g = truth_dist[dots_rc[:, 0], dots_rc[:, 1]].astype(np.float64)
    fp = float((1.0 - tri_kernel(d_p_to_g, RADIUS)).sum())
    fn = float(n) - tp
    den = tp + M58.ALPHA * fp + M58.BETA * fn + 1e-12
    return dict(dti=float(tp / den), tp=tp, fp=fp, fn=fn, n_truth=n,
                n_dots=int(dots_rc.shape[0]))


RADIUS = float(KERNEL_PX)


def crosscheck_fast_vs_shared(dots_rc: np.ndarray, fold: HO.Fold) -> dict:
    """Compare the KD-tree scoring with the shared ``gems58w.metric`` binary path."""
    fast = score_dots(dots_rc, fold, fold_truth_distance(fold))
    active = fold_active(fold)
    pred = np.zeros(active.shape, bool)
    if dots_rc.size:
        pred[dots_rc[:, 0], dots_rc[:, 1]] = True
    pred &= active
    ref = M58.dti_binary(pred, fold_truth(fold), valid=active)
    return dict(fold=fold.name,
                fast=dict(dti=fast["dti"], tp=fast["tp"], fp=fast["fp"], fn=fast["fn"]),
                shared=dict(dti=float(ref.dti), tp=float(ref.tp), fp=float(ref.fp), fn=float(ref.fn)),
                abs_delta=dict(dti=abs(fast["dti"] - float(ref.dti)),
                               tp=abs(fast["tp"] - float(ref.tp)),
                               fp=abs(fast["fp"] - float(ref.fp))),
                agree=bool(abs(fast["tp"] - float(ref.tp)) < 1e-6
                           and abs(fast["fp"] - float(ref.fp)) < 1e-6))


# -------------------------------------------------------------- sigma table
def class_distance(mask: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Distance (px, float32) from every pixel to the nearest class ridge pixel."""
    r = mask & valid
    if not r.any():
        return np.full(valid.shape, np.inf, np.float32)
    return distance_transform_edt(~r).astype(np.float32)


def sigma_table(field: dict, folds: list[HO.Fold]) -> dict:
    """Per (block, class) localisation error plus leave-one-block-out means."""
    fp = footprint()
    cls = detect.classes(field)
    comps = HO.catalogue_components(MIN_COMP_PX)[1]
    rows: list[dict] = []
    for c in cls:
        mask = detect.class_mask(field, family=c["family"], scale=c["scale"], sign=c["sign"])
        d = class_distance(mask, fp)
        for f in folds:
            n = 0
            sigs: list[float] = []
            det_px = 0
            tot_px = 0
            for idx in comps:
                if not f.withhold[idx[:, 0], idx[:, 1]].all():
                    continue
                dd = d[idx[:, 0], idx[:, 1]]
                tot_px += int(idx.shape[0])
                det_px += int((dd <= 3.0).sum())
                if float((dd <= 3.0).mean()) >= MIN_FRAC:
                    n += 1
                    sigs.append(float(np.sqrt(np.mean(np.minimum(dd, L_MAX) ** 2))))
            rows.append(dict(
                block=f.name, family=c["family"], scale=float(c["scale"]), sign=int(c["sign"]),
                n_matched_components=n, n_withheld_components=len(comps),
                detection_rate_px=float(det_px / tot_px) if tot_px else None,
                sigma_px=float(np.mean(sigs)) if sigs else None,
                sigma_std_px=float(np.std(sigs)) if len(sigs) > 1 else None,
                matched=bool(n >= MIN_PAIRS),
            ))
    for r in rows:
        others = [q["sigma_px"] for q in rows
                  if q["family"] == r["family"] and q["scale"] == r["scale"] and q["sign"] == r["sign"]
                  and q["block"] != r["block"] and q["sigma_px"] is not None and q["matched"]]
        r["sigma_lobo_px"] = float(np.mean(others)) if others else None
    return dict(unit="pixel (100 m)", l_max_px=L_MAX, min_frac=MIN_FRAC, min_pairs=MIN_PAIRS,
                radius_px=RADIUS, n_classes=len(cls), n_folds=len(folds),
                blocks=[f.name for f in folds], rows=rows)


def class_sigma(table: dict, family: str, scale: float, sign: int) -> float | None:
    """LOBO sigma for one class, floored/capped to the emittable range."""
    vals = [r["sigma_lobo_px"] for r in table["rows"]
            if r["family"] == family and abs(r["scale"] - scale) < 1e-9 and r["sign"] == sign]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return float(min(max(float(np.mean(vals)), SIGMA_FLOOR), SIGMA_CAP))


# ------------------------------------------------------------- pattern ladder
def pattern_dots(mask: np.ndarray, ax: np.ndarray, ay: np.ndarray,
                 offsets: tuple[float, ...]) -> np.ndarray:
    """Dot coordinates (row, col) of one pattern along a ridge mask."""
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return np.zeros((0, 2), np.int64)
    ux, uy = ax[ys, xs], ay[ys, xs]
    parts = []
    for o in offsets:
        rr = np.rint(ys + o * uy).astype(np.int64)
        cc = np.rint(xs + o * ux).astype(np.int64)
        parts.append(np.stack([rr, cc], axis=1))
    allp = np.concatenate(parts, axis=0)
    h, w = mask.shape
    ok = (allp[:, 0] >= 0) & (allp[:, 0] < h) & (allp[:, 1] >= 0) & (allp[:, 1] < w)
    allp = allp[ok]
    key = allp[:, 0].astype(np.int64) * w + allp[:, 1]
    uniq = np.unique(key)
    return np.stack([uniq // w, uniq % w], axis=1)


def selected_masks(field: dict, q: float, footprint_mask: np.ndarray | None = None) -> dict:
    """Ridge mask per class using per-family top-``q`` quantile thresholds.

    ``q`` is the fraction of the footprint each family may keep, so the ridge set
    is balanced across families instead of being dominated by whichever family
    has the largest absolute response.
    """
    fp = footprint() if footprint_mask is None else footprint_mask
    thr = detect.family_thresholds(field, q, fp)
    out = {}
    for c in detect.classes(field):
        t = thr.get(c["family"], (float("inf"), 0))[0]
        m = detect.class_mask(field, family=c["family"], scale=c["scale"], sign=c["sign"],
                              threshold=t)
        if m.any():
            out[(c["family"], float(c["scale"]), int(c["sign"]))] = m
    return out


def class_masks(field: dict, threshold: float) -> dict:
    """Ridge mask per class at one absolute normalised-magnitude threshold."""
    out = {}
    for c in detect.classes(field):
        m = detect.class_mask(field, family=c["family"], scale=c["scale"], sign=c["sign"],
                              threshold=threshold)
        if m.any():
            out[(c["family"], float(c["scale"]), int(c["sign"]))] = m
    return out


def pattern_table(field: dict, folds: list[HO.Fold], *, threshold: float,
                  dti0: float | None = None, alpha: float = 0.2) -> dict:
    """Exact-metric utility of every pattern for every ridge class, block by block."""
    shape = footprint().shape
    masks = class_masks(field, threshold)
    dist = {f.name: fold_truth_distance(f) for f in folds}
    active = {f.name: fold_active(f) for f in folds}

    base: dict[tuple, dict] = {}
    base_pool = dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0)
    for key, m in masks.items():
        per = {}
        tp = fp_ = fn = nt = 0.0
        for f in folds:
            am = m & active[f.name]
            dots = pattern_dots(am, field["ax"], field["ay"], PATTERNS["single"])
            r = score_dots(dots, f, dist[f.name])
            per[f.name] = r
            tp += r["tp"]; fp_ += r["fp"]; fn += r["fn"]; nt += r["n_truth"]
        base[key] = dict(per=per, tp=tp, fp=fp_, fn=fn)
        base_pool["tp"] += tp; base_pool["fp"] += fp_; base_pool["fn"] += fn
        base_pool["n_truth"] += int(nt)
    den = base_pool["tp"] + alpha * base_pool["fp"] + 0.8 * base_pool["fn"]
    base_dti = float(base_pool["tp"] / den) if den > 0 else 0.0
    s = float(dti0 if dti0 is not None else base_dti)

    rows = []
    for key, m in masks.items():
        for pat_name, offs in PATTERNS.items():
            d_tp = d_fp = 0.0
            n_dots = 0
            per_block = {}
            for f in folds:
                am = m & active[f.name]
                dots = pattern_dots(am, field["ax"], field["ay"], offs)
                r = score_dots(dots, f, dist[f.name])
                b = base[key]["per"][f.name]
                d_tp += r["tp"] - b["tp"]
                d_fp += r["fp"] - b["fp"]
                n_dots += r["n_dots"]
                per_block[f.name] = dict(dti=r["dti"], d_tp=r["tp"] - b["tp"],
                                         d_fp=r["fp"] - b["fp"], n_dots=r["n_dots"])
            u = (1.0 - alpha * s) * d_tp - alpha * s * d_fp
            rows.append(dict(family=key[0], scale=key[1], sign=key[2], pattern=pat_name,
                             offsets=list(offs), n_dots=int(n_dots),
                             d_tp=float(d_tp), d_fp=float(d_fp), U=float(u),
                             per_block=per_block))
    return dict(protocol="gems58-pooled-hide-v1", evaluator="gems58w.metric/v1",
                alpha=alpha, beta=0.8, threshold=float(threshold), radius_px=RADIUS,
                dti0=float(s),
                dti0_source=("explicit" if dti0 is not None else "pooled single-line base measured here"),
                base_dti=base_dti, base_pool=base_pool,
                base_dots_per_fold={f.name: int(sum(base[k]["per"][f.name]["n_dots"] for k in masks))
                                    for f in folds},
                n_classes=len(masks), rows=rows)


def choose_patterns(table: dict) -> dict:
    """Best pattern per class by exact-metric U; ties go to fewer lines."""
    best: dict[tuple, dict] = {}
    for r in table["rows"]:
        key = (r["family"], r["scale"], r["sign"])
        cur = best.get(key)
        if cur is None or (r["U"], -len(r["offsets"])) > (cur["U"], -len(cur["offsets"])):
            best[key] = r
    out = []
    for key, r in sorted(best.items()):
        if r["pattern"] == "single" or r["U"] <= 0.0:
            out.append(dict(family=key[0], scale=key[1], sign=key[2], pattern="single",
                            offsets=[0.0], U=r["U"], d_tp=r["d_tp"], d_fp=r["d_fp"],
                            reason="single tight line is the exact-metric optimum"))
        else:
            out.append(dict(family=key[0], scale=key[1], sign=key[2], pattern=r["pattern"],
                            offsets=r["offsets"], U=r["U"], d_tp=r["d_tp"], d_fp=r["d_fp"],
                            reason="largest exact-metric U"))
    return dict(n_classes=len(out), choices=out,
                n_ribbon_classes=sum(1 for c in out if len(c["offsets"]) > 1),
                n_tight_classes=sum(1 for c in out if len(c["offsets"]) == 1))


# ------------------------------------------------------------------- emission
def emit_dots(field: dict, choices: dict, *, threshold: float,
              budget: int = 40000) -> tuple[np.ndarray, np.ndarray, dict]:
    """Full-region dot field: winning pattern per class, ranked and thinned."""
    shape = footprint().shape
    picked, strength = [], []
    for c in choices["choices"]:
        key = (c["family"], float(c["scale"]), int(c["sign"]))
        m = detect.class_mask(field, family=key[0], scale=key[1], sign=key[2], threshold=threshold)
        if not m.any():
            continue
        dots = pattern_dots(m, field["ax"], field["ay"], tuple(c["offsets"]))
        if dots.shape[0] == 0:
            continue
        picked.append(dots)
        strength.append(field["mag"][dots[:, 0], dots[:, 1]])
    if not picked:
        return np.zeros((0, 2), np.int64), np.zeros(0, np.float32), dict(n_dots=0, budget=budget)
    dots = np.concatenate(picked, axis=0)
    mag = np.concatenate(strength, axis=0)
    key = dots[:, 0].astype(np.int64) * shape[1] + dots[:, 1]
    order = np.lexsort((-mag, key))
    dots, mag, key = dots[order], mag[order], key[order]
    first = np.r_[True, np.diff(key) != 0]
    dots, mag = dots[first], mag[first]
    n_unique = int(dots.shape[0])
    n_capped = 0
    if n_unique > budget:
        cut = np.partition(mag, n_unique - budget)[n_unique - budget]
        sel = mag >= cut
        n_capped = int((~sel).sum())
        dots, mag = dots[sel], mag[sel]
    cat = catalogue()
    on_cat = cat[dots[:, 0], dots[:, 1]]
    n_on_cat = int(on_cat.sum())
    dots, mag = dots[~on_cat], mag[~on_cat]
    return dots, mag, dict(n_dots=int(dots.shape[0]), n_unique_before_budget=n_unique,
                           n_dropped_budget=n_capped, n_dropped_on_catalogue=n_on_cat,
                           budget=int(budget), threshold=float(threshold))


def uniqueness_repair(dots: np.ndarray, mag: np.ndarray, witnesses: list[dict], *,
                      overlap_limit: float = OVERLAP_LIMIT, margin: float = 0.05) -> dict:
    """Drop the weakest dots inside informative witnesses until every overlap clears.

    ``witnesses``: dicts with ``name``, ``support`` (bool grid), ``chance_expected_overlap``
    (E) and optional ``limit``.  Saturated witnesses (E >= 0.99) overlap every nonempty
    candidate and are reported, never used to steer the field.
    """
    keep = np.ones(dots.shape[0], bool)
    rows: list[dict] = []
    if dots.shape[0] == 0:
        return dict(n_dropped=0, rows=rows, keep=keep)
    for w in witnesses:
        sup = np.asarray(w["support"], bool)
        e = float(w["chance_expected_overlap"])
        near = binary_dilation(sup, structure=disc(3.0))
        inside = near[dots[:, 0], dots[:, 1]]
        if e >= 0.99:
            rows.append(dict(name=w["name"], chance_expected_overlap=e, saturated=True,
                             overlap_towards_us=float(inside.mean()),
                             note="3 px dilation covers the footprint: overlaps every nonempty "
                                  "candidate, carries no information, not used to steer"))
            continue
        limit = float(w.get("limit", overlap_limit))
        target = limit - margin
        order = np.flatnonzero(inside & keep)[np.argsort(mag[inside & keep], kind="stable")]
        j = 0
        k = int(keep.sum())
        before = float(inside[keep].mean()) if k else 0.0
        while k > 0 and float(inside[keep].mean()) > target and j < order.size:
            keep[order[j]] = False
            k -= 1
            j += 1
        rows.append(dict(name=w["name"], chance_expected_overlap=e, saturated=False,
                         limit=limit, target=target, dropped=int(j),
                         overlap_before=before,
                         overlap_after=float(inside[keep].mean()) if k else 0.0))
    return dict(n_dropped=int((~keep).sum()), rows=rows, keep=keep)


def expected_credit(sigma: float, radius: float = RADIUS, half_width: float = 0.5,
                    n: int = 4001) -> float:
    """E[max(1 - |delta|/R, 0)] for a uniform across-strike offset of +-half_width.

    Projection only -- reported beside the exact numbers, never as a score.
    """
    x = np.linspace(-half_width, half_width, n)
    return float(tri_kernel(np.abs(x), radius).mean())


def audit_dots(dots: np.ndarray, mag: np.ndarray) -> dict:
    return dict(n_dots=int(dots.shape[0]),
                magnitude_min=float(mag.min()) if mag.size else None,
                magnitude_median=float(np.median(mag)) if mag.size else None,
                magnitude_max=float(mag.max()) if mag.size else None)
