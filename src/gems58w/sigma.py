"""Localisation-error scale sigma(x) for the ridge field, measured on the holdout.

What the ribbon width has to match
----------------------------------
The scoring kernel is **isotropic**: a prediction pixel at Euclidean distance
``d`` from a truth pixel carries credit ``max(1 - d/300 m, 0)``.  A ribbon
stretched across strike only pays if it spans the distance between the detected
ridge and the true trace, so the quantity to calibrate is the **isotropic
localisation error of a matched ridge**, measured in the same units the metric
uses.  We therefore define, on the buffered hide-and-recover holdout, for each
withheld catalogue component ``w`` (a whole fault segment):

    d_w(p)          = Euclidean distance from a withheld pixel p to the nearest
                      candidate-ridge pixel (all ridge segments pooled);
    match(w)        = at least ``MIN_FRAC`` of the pixels of w have d_w <= L_MAX;
    sigma(w)        = sqrt( mean over p in w of min(d_w(p), L_MAX)^2 )   [pixels]

``L_MAX`` censors the few far pixels, so ``sigma`` is a conservative (never
optimistic) RMS localisation error.  1 px = 100 m and the kernel radius is
3 px, so a stratum with ``sigma > 3`` is **unreachable** by construction and is
reported as such rather than emitted.

Strata, as required by the lane protocol:

* **data block**  -- the quadrant of the withheld component's centroid
  (``NW``, ``NE``, ``SW``, ``SE``);
* **feature resolution** -- the ridge scale of the dominant matched segment
  (1.5 px = 150 m, 3.0 px = 300 m, 6.0 px = 600 m);
* **ridge type** -- (organizer band family, ridge sign) of the dominant segment.

A stratum is published only when it holds at least ``MIN_PAIRS`` matched
components; otherwise the documented fallback chain in :func:`sigma_for` is
used and the substitution is recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from scipy.ndimage import label
from scipy.spatial import cKDTree

MIN_COMP_PX = 8
MIN_FRAC = 0.6
MIN_PAIRS = 10
L_MAX = 15.0
SIGMA_FLOOR = 0.5
SIGMA_CAP = 6.0


@dataclass
class CompSigma:
    block: str
    comp_px: int
    frac_within: float
    sigma: float
    band: str
    family: str
    scale: float
    sign: int
    ridge_px: int

    def as_dict(self) -> dict:
        return asdict(self)


def _family_of(band: str) -> str:
    from . import features as F

    return next((f for f, bs in F.FAMILIES.items() if band in bs), "other")


def measure(field: dict, segs, fold, min_frac: float = MIN_FRAC,
            l_max: float = L_MAX) -> list[CompSigma]:
    """Per withheld component: recovery fraction, sigma, and the dominant ridge type."""
    wmask = fold.withhold
    lab, n = label(wmask, structure=np.ones((3, 3), int))
    if n == 0 or not segs:
        return []

    pts = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    owner = np.concatenate([np.full(s["size"], i) for i, s in enumerate(segs)])
    tree = cKDTree(pts)

    comp_pixels = np.argwhere(wmask)
    d, j = tree.query(comp_pixels.astype(np.float64), k=1, workers=-1)
    comp_label = lab[comp_pixels[:, 0], comp_pixels[:, 1]]

    out: list[CompSigma] = []
    order = np.argsort(comp_label, kind="stable")
    comp_label, d, j = comp_label[order], d[order], j[order]
    comp_pixels = comp_pixels[order]
    bounds = np.flatnonzero(np.diff(comp_label)) + 1
    for a, b in zip(np.r_[0, bounds], np.r_[bounds, comp_label.size]):
        if b - a < MIN_COMP_PX:
            continue
        dd = d[a:b]
        frac = float((dd <= l_max).mean())
        if frac < min_frac:
            continue
        sigma = float(np.sqrt(np.mean(np.minimum(dd, l_max) ** 2)))
        seg_ids = owner[j[a:b][dd <= l_max]]
        if seg_ids.size == 0:
            continue
        # dominant segment = the one holding the mode of the matched pixels
        vals, counts = np.unique(seg_ids, return_counts=True)
        dom = segs[int(vals[counts.argmax()])]
        code = max(dom["codes"], key=lambda c: c["scale"]) if dom["codes"] else {}
        band = code.get("band", "?")
        out.append(CompSigma(block=fold.name, comp_px=int(b - a), frac_within=frac,
                             sigma=sigma, band=band, family=_family_of(band),
                             scale=float(code.get("scale", 0.0)),
                             sign=int(code.get("sign", 0)),
                             ridge_px=int(dom["size"])))
    return out


def _agg(vals: list[float]) -> dict:
    v = np.asarray(vals, float)
    return dict(n=int(v.size), median=float(np.median(v)), mean=float(v.mean()),
                p25=float(np.quantile(v, 0.25)), p75=float(np.quantile(v, 0.75)),
                rms=float(np.sqrt(np.mean(v ** 2))))


def sigma_table(items: list[CompSigma]) -> dict:
    """Stratified sigma summary; only strata with >= MIN_PAIRS components are published."""
    if not items:
        return dict(n_matched=0, pooled=None, by_block={}, by_scale={}, by_type={},
                    by_type_scale={}, by_block_scale={}, unreachable={})

    def grp(key):
        keys = sorted({key(i) for i in items})
        out = {}
        for k in keys:
            sub = [i for i in items if key(i) == k]
            if len(sub) >= MIN_PAIRS:
                out[str(k)] = _agg([s.sigma for s in sub])
        return out

    type_name = lambda i: f"{i.family}/{'crest' if i.sign < 0 else 'trough'}"  # noqa: E731
    return dict(
        n_matched=len(items),
        pooled=_agg([i.sigma for i in items]),
        recovery=dict(n_components_withheld=int(len(items)),
                      median_frac_within=float(np.median([i.frac_within for i in items]))),
        by_block=grp(lambda i: i.block),
        by_scale=grp(lambda i: f"{i.scale:g}px"),
        by_type=grp(type_name),
        by_type_scale=grp(lambda i: f"{type_name(i)}/{i.scale:g}px"),
        by_block_scale=grp(lambda i: f"{i.block}/{i.scale:g}px"),
        unreachable={k: v for k, v in grp(type_name).items() if v["median"] > 3.0},
    )


def sigma_for(family: str, scale: float, sign: int, block: str, table: dict,
              floor: float = SIGMA_FLOOR, cap: float = SIGMA_CAP) -> tuple[float, str]:
    """Sigma lookup with an explicit, recorded fallback chain.

    Returns ``(sigma_px, which_stratum_was_used)``.
    """
    sign_name = "crest" if sign < 0 else "trough"
    chain = (
        ("type_scale", f"{family}/{sign_name}/{scale:g}px", table.get("by_type_scale", {})),
        ("type", f"{family}/{sign_name}", table.get("by_type", {})),
        ("scale", f"{scale:g}px", table.get("by_scale", {})),
        ("block", block, table.get("by_block", {})),
    )
    for name, key, bucket in chain:
        if key in bucket:
            return float(min(max(bucket[key]["median"], floor), cap)), f"{name}:{key}"
    pooled = table.get("pooled") or {}
    return float(min(max(float(pooled.get("median", 1.0)), floor), cap)), "pooled"
