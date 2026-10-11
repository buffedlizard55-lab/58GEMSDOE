"""Sigma(x) measurement for the ribbon lane — session 7.

Lane brief: "On the hide-and-recover holdout, measure the across-strike distance
between each candidate ridge and the nearest withheld segment, and fit an error
scale sigma(x) by data block, feature resolution and ridge type."

Implemented exactly in that direction: for every candidate step-edge segment
(inside the scored domain of a holdout cell) the distance from its pixels to the
nearest withheld catalogue pixel is measured with a Euclidean distance transform,
censored at ``L_MAX`` (same constants as the shared ``gems58w.sigma``).  The
per-segment localization scale is the RMS of those censored distances — the
across-strike error of the detected ridge relative to the true trace.  A segment
is *associated* when at least ``MIN_FRAC`` of its pixels lie within ``L_MAX`` of
withheld truth.

Strata (published in the sigma table):
* **data block**            — the quadrant of the segment centroid (NW/NE/SW/SE);
* **feature resolution**    — the winning edge scale (1.5 px / 3.0 px);
* **ridge type**            — (band family, band name) of the winning band;
* **relief class** (H7-B)   — tercile of the 21-px det_elev relief field.

The truth-anchored RMS (withheld pixels to nearest edge pixel) is reported
alongside it: that is the width needed to *cover* the truth, while the
ridge-anchored RMS is the width the lane brief asks for.  Constants are imported
from the shared ``gems58w.sigma`` so the two instruments cannot drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from gems58w.sigma import L_MAX, MIN_COMP_PX, MIN_FRAC, MIN_PAIRS, SIGMA_CAP, SIGMA_FLOOR

BLOCKS = ("NW", "NE", "SW", "SE")


@dataclass
class SegSigma:
    block: str
    seg_px: int
    frac_within: float
    sigma: float                 # ridge->truth censored RMS (px, censor L_MAX)
    truth_rms: float             # truth->ridge RMS of the coverable truth px (px)
    family: str
    band: str
    scale: float
    relief_class: int
    strength: float
    frac_strict: float = 0.0     # fraction of seg px within strict_lmax (6 px) of truth
    strict_sigma: float = float("nan")   # ridge->truth RMS at the strict radius


def block_of(centroid: tuple[float, float], shape: tuple[int, int]) -> str:
    r, c = centroid
    rows, cols = shape
    return ("N" if r < rows / 2 else "S") + ("W" if c < cols / 2 else "E")


def measure(segs, fold_truth: np.ndarray, fold_active: np.ndarray,
            shape: tuple[int, int], l_max: float = L_MAX,
            min_frac: float = MIN_FRAC, strict_lmax: float = 6.0) -> list[SegSigma]:
    """Per-segment ridge->truth localization scale on one holdout cell.

    Only segment pixels inside ``fold_active`` are measured (pixels outside the
    scored domain of the fold would be artificially far from that fold's truth).
    ``sigma`` censors at ``l_max``; ``strict_sigma`` additionally records the RMS
    over pixels within ``strict_lmax`` (the sibling instrument's capture radius)
    and ``frac_strict`` is the associated fraction at that radius.
    """
    if not segs or not fold_truth.any():
        return []
    dist = distance_transform_edt(~fold_truth)   # px to nearest withheld pixel
    out: list[SegSigma] = []
    truth_pts = np.argwhere(fold_truth).astype(np.float64)
    truth_tree = cKDTree(truth_pts) if truth_pts.size else None
    for s in segs:
        ys, xs = s.idx[:, 0], s.idx[:, 1]
        inside = fold_active[ys, xs]
        if not inside.any():
            continue
        ys, xs = ys[inside], xs[inside]
        d = dist[ys, xs].astype(np.float64)
        frac = float((d <= l_max).mean())
        if frac < min_frac:
            continue
        dc = np.minimum(d, l_max)
        sigma = float(np.sqrt(np.mean(dc ** 2)))
        strict = d <= strict_lmax
        frac_strict = float(strict.mean())
        strict_sigma = float(np.sqrt(np.mean(d[strict] ** 2))) if strict.any() else float("nan")
        # truth-anchored: the withheld pixels this segment could cover (within
        # strict_lmax of its pixels) and the width needed to reach them
        truth_rms = float("nan")
        if truth_tree is not None:
            near_truth_ids: set[int] = set()
            pts = np.stack([ys, xs], axis=1).astype(np.float64)
            for idxs in truth_tree.query_ball_point(pts, r=strict_lmax):
                near_truth_ids.update(idxs)
            if near_truth_ids:
                tp = truth_pts[sorted(near_truth_ids)]
                dt, _ = cKDTree(pts).query(tp, k=1, workers=-1)
                truth_rms = float(np.sqrt(np.mean(np.minimum(dt, l_max) ** 2)))
        out.append(SegSigma(block=block_of(s.centroid, shape), seg_px=int(ys.size),
                            frac_within=frac, sigma=sigma, truth_rms=truth_rms,
                            family=s.family, band=s.band, scale=s.scale,
                            relief_class=s.relief_class, strength=s.strength,
                            frac_strict=frac_strict, strict_sigma=strict_sigma))
    return out


def _agg(vals: list[float]) -> dict:
    v = np.asarray([x for x in vals if np.isfinite(x)], float)
    if v.size == 0:
        return dict(n=0)
    return dict(n=int(v.size), median=float(np.median(v)), mean=float(v.mean()),
                p25=float(np.quantile(v, 0.25)), p75=float(np.quantile(v, 0.75)),
                rms=float(np.sqrt(np.mean(v ** 2))))


def _group(rows: list[SegSigma], key) -> dict:
    out: dict[str, dict] = {}
    for r in rows:
        k = key(r)
        out.setdefault(k, []).append(r)
    return {k: dict(n_segments=len(v), **{f"sigma_{a}": b for a, b in
            _agg([x.sigma for x in v]).items() if a != "n"},
            **{f"strict_sigma_{a}": b for a, b in
            _agg([x.strict_sigma for x in v]).items() if a != "n"},
            frac_strict_mean=float(np.mean([x.frac_strict for x in v])),
            **{f"truth_rms_{a}": b for a, b in
            _agg([x.truth_rms for x in v]).items() if a != "n"})
            for k, v in sorted(out.items())}


def sigma_table(rows: list[SegSigma]) -> dict:
    """Stratified sigma table; strata with < MIN_PAIRS segments are marked thin."""
    pooled = _agg([r.sigma for r in rows])
    table = dict(
        constants=dict(L_MAX=L_MAX, MIN_FRAC=MIN_FRAC, MIN_PAIRS=MIN_PAIRS,
                       SIGMA_FLOOR=SIGMA_FLOOR, SIGMA_CAP=SIGMA_CAP,
                       MIN_COMP_PX=MIN_COMP_PX, STRICT_LMAX=6.0),
        n_segments_measured=len(rows),
        pooled_sigma=pooled,
        pooled_strict_sigma=_agg([r.strict_sigma for r in rows]),
        pooled_truth_rms=_agg([r.truth_rms for r in rows]),
        by_block=_group(rows, lambda r: r.block),
        by_resolution=_group(rows, lambda r: f"{r.scale:g}px"),
        by_ridge_type=_group(rows, lambda r: f"{r.family}:{r.band}"),
        by_relief_class=_group(rows, lambda r: f"relief{r.relief_class}"),
        by_type_scale=_group(rows, lambda r: f"{r.family}:{r.band}@{r.scale:g}px"),
    )
    return table


def sigma_for(family: str, band: str, scale: float, relief_class: int,
              block: str, table_rows: list[SegSigma]) -> tuple[float, dict]:
    """Fallback chain: (band, scale, relief, block) -> coarser strata -> pooled."""

    def med(pred) -> float | None:
        v = [r.sigma for r in table_rows if pred(r) and np.isfinite(r.sigma)]
        return float(np.median(v)) if len(v) >= MIN_PAIRS else None

    chain = [
        ("band_scale_relief_block", lambda r: r.band == band and r.scale == scale
         and r.relief_class == relief_class and r.block == block),
        ("band_scale_relief", lambda r: r.band == band and r.scale == scale
         and r.relief_class == relief_class),
        ("band_scale", lambda r: r.band == band and r.scale == scale),
        ("family_scale", lambda r: r.family == family and r.scale == scale),
        ("family", lambda r: r.family == family),
        ("pooled", lambda r: True),
    ]
    for name, pred in chain:
        m = med(pred)
        if m is not None:
            return float(np.clip(m, SIGMA_FLOOR, SIGMA_CAP)), dict(source=name, sigma_raw=m)
    return float(SIGMA_FLOOR), dict(source="floor", sigma_raw=None)


def rows_as_json(rows: list[SegSigma]) -> list[dict]:
    return [asdict(r) for r in rows]
