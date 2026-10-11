"""Ribbon lane (58GEMSDOE): match emission width to the measured localization error.

Lane paragraph (verbatim contract)
----------------------------------
"On the hide-and-recover holdout, measure the across-strike distance between
each candidate ridge and the nearest withheld segment, and fit an error scale
sigma(x) by data block, feature resolution and ridge type.  Then choose, per
segment, the number and offset of parallel dotted lines (spacing near the 3-px
kernel radius) that maximize U = (1 - 0.2*DTI0)*TP - 0.2*DTI0*FP, evaluated
with the exact metric.  Use a single tight line where sigma is under about
0.5 px and a ribbon about +/-sigma wide where it is 2-3 px.  Emit included dots
at exactly 1.0."

Design
------
Candidate ridge axes come from two independent, visible-only sources
(ridge *type*):

* ``cat-axis``  -- skeleton of the **visible** catalogue only (per fold), i.e.
  the mapped-trace axis continuation population.  Feature resolution: the
  100 m competition catalogue (INGENIOUS-detail digitising).
* ``sgmc-axis`` -- skeleton of ``sgmc_faults_100m.tif`` minus the visible
  catalogue, i.e. an **independent public mapping** (state geologic map
  compilation, ~1:250k source scale rasterised on the 100 m grid).  Its offset
  from a withheld catalogue segment measures independent-mapping localization
  error.  SGMC bytes are fixed external data, so this cannot leak the draw.

Neither constructor touches the withheld mask; both are pixel-exactly masked
away from visible faults, per parallel-run protocol rule 2.  The leakage canary
(rule 4) scores each type's distance-to-ridge credit surface alone.

Per-segment emission patterns: dots at stride 3 px along the axis (the kernel
radius), with parallel lines offset +/-s px across strike.  A pattern's
marginal effect on the **exact** DTI is computed against the accumulated
credit state (T per truth pixel, M self credit, n dots); the acceptance test is
the exact two-sided recomputation from ``gems57.metric``.  U is reported
alongside for the lane's formula; the final numbers all come from the shared
exact evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.stats import rankdata
from skimage.morphology import skeletonize

from gems57.metric import ALPHA, BETA, EPS, RADIUS_PX, kernel
from gems57.network import segments as decompose_segments

RIDGE_TYPES = ("cat-axis", "sgmc-axis")
MATCH_CAP_PX = 8.0        # a ridge farther than this from truth is "unmatched", not wide-sigma
SIGMA_SHRINK_K = 8.0      # pseudo-count toward the pooled sigma (small-n stabilisation)
STRIDE_PX = 3             # along-line dot spacing: the 3-px kernel radius
MAX_SIGMA_PX = 3.0        # offsets never exceed the kernel radius
KERNEL_R = int(np.ceil(RADIUS_PX))


# --------------------------------------------------------------------------- #
# Ridge axis construction (visible-only sources)
# --------------------------------------------------------------------------- #
def clean_skeleton(mask: np.ndarray) -> np.ndarray:
    """Skeletonise a boolean mask and drop isolated single-pixel artifacts."""
    m = np.asarray(mask, bool)
    if not m.any():
        return m
    sk = skeletonize(m)
    n = ndi.convolve(sk.astype(np.int8), np.ones((3, 3), np.int8), mode="constant") - sk.astype(np.int8)
    return sk & (n >= 1)


def sgmc_mask(root, grid) -> np.ndarray:
    """Pinned SGMC auxiliary raster on the competition grid, minus catalogue."""
    import rasterio
    from pathlib import Path

    path = Path(root) / "data" / "external" / "sgmc_faults_100m.tif"
    with rasterio.open(path) as src:
        if str(src.crs) != "EPSG:32611" or (src.height, src.width) != grid.shape:
            raise ValueError("SGMC raster is not on the pinned competition grid")
        sgmc = src.read(1) > 0
    return sgmc & grid.footprint


def axis_mask_for_type(kind: str, visible: np.ndarray, sgmc: np.ndarray) -> np.ndarray:
    """Ridge-axis pixels for one ridge type from visible-only sources."""
    if kind == "cat-axis":
        return clean_skeleton(visible)
    if kind == "sgmc-axis":
        return clean_skeleton(sgmc & ~visible)
    raise ValueError(f"unknown ridge type {kind!r}")


@dataclass
class AxisSegment:
    """One ridge-axis segment (<=12 px chunk between junctions)."""
    kind: str                # ridge type
    seg_id: int
    order: np.ndarray        # (k,2) crop-coord pixels ordered along the axis
    u: np.ndarray            # (2,) unit along-strike direction (crop coords)
    p: np.ndarray            # (2,) unit across-strike direction
    length_px: float


def axis_segments(kind: str, axes_full: np.ndarray, bbox, ) -> list[AxisSegment]:
    """Decompose an axis mask into ordered per-segment pixel lists (crop coords)."""
    seg, n_seg, _ = decompose_segments(axes_full, max_len_px=12)
    sub = seg[bbox]
    out: list[AxisSegment] = []
    for sid in np.unique(sub[sub > 0]):
        yy, xx = np.nonzero(sub == sid)
        pts = np.stack([yy, xx], 1).astype(np.float64)
        c = pts.mean(0)
        q = pts - c
        try:
            _, _, vt = np.linalg.svd(q, full_matrices=False)
        except np.linalg.LinAlgError:
            continue
        u = vt[0]
        if u[0] < 0 or (u[0] == 0 and u[1] < 0):    # deterministic sign
            u = -u
        t = q @ u
        pix = np.stack([yy, xx], 1)[np.argsort(t, kind="stable")]
        out.append(AxisSegment(kind=kind, seg_id=int(sid), order=pix.astype(np.int64),
                               u=u, p=np.array([-u[1], u[0]]), length_px=float(len(pix))))
    return out


# --------------------------------------------------------------------------- #
# Sigma fitting: across-strike distance between candidate ridge and withheld truth
# --------------------------------------------------------------------------- #
def across_strike_measurements(axsegs: list[AxisSegment], truth_yx, k_dg: np.ndarray) -> list[dict]:
    """Per-segment nearest-withheld measurements (pixels on the 100 m grid)."""
    ty, tx = truth_yx
    if len(ty) == 0 or not axsegs:
        return []
    tree = cKDTree(np.stack([ty, tx], 1).astype(np.float64))
    recs = []
    for s in axsegs:
        d, idx = tree.query(s.order.astype(np.float64), k=1)
        near = np.stack([ty[idx], tx[idx]], 1).astype(np.float64) - s.order.astype(np.float64)
        along = np.abs(near @ s.u)
        across = np.abs(near @ s.p)
        k_self = k_dg[s.order[:, 0], s.order[:, 1]]
        recs.append(dict(
            kind=s.kind, seg_id=s.seg_id, n_px=int(len(s.order)),
            d_med=float(np.median(d)), d_rms=float(np.sqrt(np.mean(d ** 2))),
            across_med=float(np.median(across)), across_rms=float(np.sqrt(np.mean(across ** 2))),
            along_max=float(along.max()) if len(along) else 0.0,
            k_self_max=float(k_self.max()) if len(k_self) else 0.0,
            matched=bool(np.median(d) <= MATCH_CAP_PX),
        ))
    return recs


def fit_sigma(recs: list[dict]) -> dict:
    """Sigma table by ridge type; RMS across-strike error with shrinkage to the pool.

    ``sigma_raw`` is the RMS across-strike offset of matched ridges; ``sigma``
    shrinks toward ``sigma_pool`` with a pseudo-count of ``SIGMA_SHRINK_K``
    segments so a 2-segment cell cannot set the width.
    """
    pool = np.array([r["across_rms"] for r in recs if r["matched"]], float)
    sigma_pool = float(np.sqrt(np.mean(pool ** 2))) if pool.size else 0.0
    per_type = {}
    for kind in RIDGE_TYPES:
        sel = [r for r in recs if r["kind"] == kind]
        m = np.array([r["across_rms"] for r in sel if r["matched"]], float)
        n = int(m.size)
        raw = float(np.sqrt(np.mean(m ** 2))) if n else float("nan")
        shr = (float(np.sqrt((n * raw ** 2 + SIGMA_SHRINK_K * sigma_pool ** 2) / (n + SIGMA_SHRINK_K)))
               if n else float("nan"))
        per_type[kind] = dict(
            n_segments=len(sel), n_matched=n,
            sigma_raw_px=raw, sigma_px=shr,
            median_across_px=(float(np.median([r["across_med"] for r in sel if r["matched"]]))
                              if n else float("nan")),
            matched_fraction=(n / len(sel)) if sel else 0.0,
        )
    return dict(per_type=per_type, sigma_pool_px=sigma_pool, n_matched_total=int(pool.size))


# --------------------------------------------------------------------------- #
# Leakage canary (rule 4): each ridge type's credit surface alone vs withheld truth
# --------------------------------------------------------------------------- #
def canary_auc(score: np.ndarray, truth_yx, active: np.ndarray,
               rng: np.random.Generator, n_neg: int = 150_000) -> float:
    """Tie-corrected AUC of one feature surface, truth vs active non-truth.

    ``score`` must be the feature's OWN surface (here: kernel of distance to
    the ridge axes of one type, cropped to the cell) -- never a truth-derived
    field such as kernel-of-distance-to-withheld.
    """
    ty, tx = truth_yx
    n_truth = len(ty)
    if n_truth == 0 or not active.any():
        return float("nan")
    s_pos = score[ty, tx].astype(np.float64)
    truth_flat = ty.astype(np.int64) * score.shape[1] + tx.astype(np.int64)
    ay, ax = np.nonzero(active)
    flat = ay.astype(np.int64) * score.shape[1] + ax.astype(np.int64)
    pos = np.sort(truth_flat)
    loc = np.searchsorted(pos, flat)
    loc_c = np.clip(loc, 0, len(pos) - 1)
    is_truth = pos[loc_c] == flat
    neg = flat[~is_truth]
    if len(neg) > n_neg:
        neg = rng.choice(neg, size=n_neg, replace=False)
    ny, nx = neg // score.shape[1], neg % score.shape[1]
    s_neg = score[ny, nx].astype(np.float64)
    r = rankdata(np.concatenate([s_pos, s_neg]), method="average")
    n = len(s_pos)
    return float((r[:n].sum() - n * (n + 1) / 2.0) / (n * len(s_neg)))


# --------------------------------------------------------------------------- #
# Per-segment ribbon patterns and exact-metric selection
# --------------------------------------------------------------------------- #
def pattern_offsets(sigma: float) -> dict[str, tuple[int, ...]]:
    """Candidate parallel-line offset sets (px across strike).

    The lane's canonical rule is included explicitly: a single tight line when
    sigma < ~0.5 px; a ribbon about +/-sigma wide when sigma is 2-3 px.
    """
    cands = {
        "tight": (0,),
        "pair1": (-1, 1),
        "pair2": (-2, 2),
        "pair3": (-3, 3),
        "tri2": (0, -2, 2),
        "tri3": (0, -3, 3),
    }
    r = int(np.clip(round(float(sigma)), 0, int(MAX_SIGMA_PX)))
    cands[f"sig_pair{r}"] = (-r, r) if r >= 1 else (0,)
    if r >= 1:
        cands[f"sig_tri{r}"] = (0, -r, r)
    return cands


def build_pattern_dots(seg: AxisSegment, offsets: tuple[int, ...],
                       stride: int = STRIDE_PX) -> np.ndarray:
    """Dots for one pattern: stride-spaced axis pixels shifted across strike."""
    base = seg.order[::stride]
    lines = [base]
    for off in offsets:
        if off == 0:
            continue
        lines.append(np.rint(base + seg.p * off).astype(np.int64))
    return np.unique(np.concatenate(lines, 0), axis=0)


@dataclass
class CellState:
    """Exact-metric bookkeeping for one holdout cell (crop coordinates)."""
    k_dg: np.ndarray                  # kernel(dist to truth), crop
    truth_yx: tuple[np.ndarray, np.ndarray]
    credit: np.ndarray                # per-truth-pixel accumulated kernel credit
    tree: cKDTree
    n_dots: int = 0
    M: float = 0.0
    emitted: set = field(default_factory=set)
    H: int = 0
    W: int = 0

    @property
    def T(self) -> float:
        return float(self.credit.sum())

    def dti(self, K: int) -> float:
        # D = tp + alpha*fp + beta*fn with fn = K - tp  ==  alpha*(T + fp) + beta*K
        fp = self.n_dots - self.M
        return float(self.T / (ALPHA * (self.T + fp) + BETA * K + EPS))


def make_cell_state(cell) -> CellState:
    ty, tx = cell.truth_yx
    return CellState(k_dg=cell.k_dg.astype(np.float64), truth_yx=(ty, tx),
                     credit=np.zeros(len(ty), np.float64),
                     tree=cKDTree(np.stack([ty, tx], 1).astype(np.float64)),
                     H=cell.k_dg.shape[0], W=cell.k_dg.shape[1])


def _clip(dots: np.ndarray, H: int, W: int) -> np.ndarray:
    ok = (dots[:, 0] >= 0) & (dots[:, 0] < H) & (dots[:, 1] >= 0) & (dots[:, 1] < W)
    return dots[ok]


def _affected_truth(state: CellState, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    hits = state.tree.query_ball_point(np.stack([ys, xs], 1).astype(np.float64), RADIUS_PX)
    lens = np.fromiter((len(h) for h in hits), np.int64, len(hits))
    if lens.sum() == 0:
        return np.empty(0, np.int64)
    flat = np.fromiter((g for h in hits for g in h), np.int64, int(lens.sum()))
    return np.unique(flat)


def pattern_gain(state: CellState, dots: np.ndarray) -> tuple[float, float, float]:
    """Exact marginal (dT, dFP, k_self_sum) of adding a pattern's dots."""
    d = _clip(dots, state.H, state.W)
    if len(d) == 0:
        return 0.0, 0.0, 0.0
    ys, xs = d[:, 0], d[:, 1]
    k_self = state.k_dg[ys, xs]
    d_fp = float((1.0 - k_self).sum())
    k_sum = float(k_self.sum())
    g = _affected_truth(state, ys, xs)
    if len(g) == 0:
        return 0.0, d_fp, k_sum
    gy = state.truth_yx[0][g].astype(np.float64)
    gx = state.truth_yx[1][g].astype(np.float64)
    d2 = (gy[:, None] - ys[None, :]) ** 2 + (gx[:, None] - xs[None, :]) ** 2
    w = kernel(np.sqrt(d2))
    d_t = float(np.maximum(w.max(axis=1) - state.credit[g], 0.0).sum())
    return d_t, d_fp, k_sum


def exact_accept(state: CellState, d_t: float, d_fp_unused: float, k_sum: float, K: int) -> bool:
    """Exact test: does the atomic pattern raise DTI? (both sides recomputed)"""
    T0, M0, n0 = state.T, state.M, state.n_dots
    D0 = ALPHA * (T0 + n0 - M0) + BETA * K + EPS
    D1 = ALPHA * (T0 + d_t + n0 + 1 - (M0 + k_sum)) + BETA * K + EPS
    return (T0 + d_t) / D1 > T0 / D0


def apply_pattern(state: CellState, dots: np.ndarray, k_sum: float) -> None:
    d = _clip(dots, state.H, state.W)
    ys, xs = d[:, 0], d[:, 1]
    state.n_dots += len(ys)
    state.M += k_sum
    state.emitted.update((ys.astype(np.int64) * state.W + xs.astype(np.int64)).tolist())
    g = _affected_truth(state, ys.astype(np.float64), xs.astype(np.float64))
    if len(g) == 0:
        return
    gy = state.truth_yx[0][g].astype(np.float64)
    gx = state.truth_yx[1][g].astype(np.float64)
    d2 = (gy[:, None] - ys[None, :]) ** 2 + (gx[:, None] - xs[None, :]) ** 2
    state.credit[g] = np.maximum(state.credit[g], kernel(np.sqrt(d2)).max(axis=1))


def emission_mask_from_state(state: CellState) -> np.ndarray:
    m = np.zeros((state.H, state.W), bool)
    e = np.array(sorted(state.emitted), np.int64)
    m[e // state.W, e % state.W] = True
    return m


def select_configs_for_cell(cell, axsegs: list[AxisSegment], sigma_by_type: dict[str, float],
                            dti0_ref: float, stride: int = STRIDE_PX, passes: int = 3):
    """Greedy per-segment pattern selection; accept test is the exact DTI recomputation.

    U (the lane's formula at reference DTI0) sets the visiting order inside a
    pass; every acceptance is re-evaluated exactly against the current state.
    Returns (state, choices, stats).
    """
    K = cell.n_truth
    state = make_cell_state(cell)
    configs = []
    for s in axsegs:
        sig = sigma_by_type.get(s.kind, float("nan"))
        if not np.isfinite(sig):
            continue
        for name, offs in pattern_offsets(sig).items():
            dots = _clip(build_pattern_dots(s, offs, stride), state.H, state.W)
            if len(dots) == 0:
                continue
            kmax = state.k_dg[dots[:, 0], dots[:, 1]].max()
            if kmax < 0.5 * ALPHA * max(dti0_ref, 0.02):   # cannot ever clear the bar
                continue
            configs.append((s.kind, s.seg_id, name, offs, dots))
    choices: dict = {}
    n_eval = 0
    n_accept = 0
    for _pass in range(passes):
        progressed = False
        scored = []
        for (kind, sid, name, offs, dots) in configs:
            key = (kind, sid)
            base = np.array([int(y) * state.W + int(x) for y, x in dots])
            fresh = ~np.isin(base, np.array(sorted(state.emitted), np.int64)) if state.emitted else np.ones(len(dots), bool)
            if not fresh.any():
                continue
            d = dots[fresh]
            d_t, d_fp, k_sum = pattern_gain(state, d)
            n_eval += 1
            if d_t <= 0:
                continue
            U = (1.0 - ALPHA * dti0_ref) * d_t - ALPHA * dti0_ref * d_fp
            scored.append((U, kind, sid, name, offs, d, d_t, d_fp, k_sum))
        scored.sort(key=lambda t: -t[0])
        for (U, kind, sid, name, offs, d, _dt, _dfp, _ks) in scored:
            base = d[:, 0].astype(np.int64) * state.W + d[:, 1].astype(np.int64)
            fresh = ~np.isin(base, np.array(sorted(state.emitted), np.int64)) if state.emitted else np.ones(len(d), bool)
            if not fresh.any():
                continue
            dd = d[fresh]
            d_t2, d_fp2, k_sum2 = pattern_gain(state, dd)
            n_eval += 1
            if d_t2 <= 0:
                continue
            if exact_accept(state, d_t2, d_fp2, k_sum2, K):
                apply_pattern(state, dd, k_sum2)
                choices[(kind, sid)] = dict(
                    config=name, offsets=list(int(o) for o in offs), n_dots=int(len(dd)),
                    d_t=float(d_t2), d_fp=float(d_fp2),
                    U=float((1.0 - ALPHA * dti0_ref) * d_t2 - ALPHA * dti0_ref * d_fp2),
                    kind=kind)
                n_accept += 1
                progressed = True
        if not progressed:
            break
    stats = dict(n_configs=len(configs), n_evals=n_eval, n_accepted=n_accept, passes=passes,
                 final_dti=state.dti(K), final_dots=state.n_dots)
    return state, choices, stats
