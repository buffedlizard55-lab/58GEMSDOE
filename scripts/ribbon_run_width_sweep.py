"""Ribbon lane, session 4: EXP-1 (sigma table) and EXP-2 (width/offset sweep).

Lane: *match emission width to the measured localisation error.*

EXP-1 measures, on the buffered hide-and-recover holdout (protocol
``gems58-pooled-hide-v1``), how far each withheld fault segment lies from the
nearest candidate ridge, splits that error into across-strike and along-strike
components against the ridge's own normal, and fits an error scale per stratum
(spatial block x feature resolution x ridge type).  Strata are **cross-fitted**:
the sigma used for block *b* is estimated on the other three blocks only.

EXP-2 compares ribbon geometries **at an equal dot budget**.  Every arm emits
exactly the same number of dots; they differ only in how those dots are spread
across strike (number and offset of parallel lines) and along strike (dot
stride).  Scoring uses the shared evaluator ``gems57.evaluate_holdout``; the
95 % CI is the paired physical spatial-block percentile bootstrap implemented in
``gems57.evaluate_holdout.pooled_summary``.  A per-segment width chosen by the
exact marginal test in ``gems57.exact_emission`` is run as a separate arm.

Outputs go to ``evidence/ribbon_v3/``.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from gems57 import evaluate_holdout as EH
from gems58w import extract, holdout as H58, features as F58

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "ribbon_v3"
PROTOCOL = "gems58-pooled-hide-v1"
L_MAX = 15.0
MATCH_FRAC = 0.6
MIN_COMP_PX = 8
MIN_STRATUM = 10
BLOCKS = ("NW", "NE", "SW", "SE")

#: arm name -> (across-strike line offsets in px, along-strike dot stride)
ARMS: dict[str, tuple[tuple[float, ...], int]] = {
    # (across-strike offsets in px, along-strike stride); stride 0 = fit the budget
    "T1_fit": ((0.0,), 0),
    "R3_d2_fit": ((-2.0, 0.0, 2.0), 0),
    "R5_d2_fit": ((-4.0, -2.0, 0.0, 2.0, 4.0), 0),
    "R7_d2_fit": ((-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0), 0),
    "R3_d3_fit": ((-3.0, 0.0, 3.0), 0),
    "R5_d3_fit": ((-6.0, -3.0, 0.0, 3.0, 6.0), 0),
}


# ----------------------------------------------------------------------
# segments / arms
# ----------------------------------------------------------------------

_ORDER: dict[int, np.ndarray] = {}
_PIX: dict[tuple, np.ndarray] = {}


def strike_order(idx: np.ndarray, key: int) -> np.ndarray:
    o = _ORDER.get(key)
    if o is not None:
        return o
    p = idx.astype(np.float64)
    p = p - p.mean(axis=0)
    if len(p) < 2:
        o = np.arange(len(p))
    else:
        cov = p.T @ p / (len(p) - 1)
        _, v = np.linalg.eigh(cov)
        o = np.argsort(p @ v[:, -1], kind="stable")
    _ORDER[key] = o
    return o


def build_segments(field: dict, threshold: float, min_px: int, active: np.ndarray):
    out = []
    for i, s in enumerate(extract.segments(field, threshold, min_px=min_px)):
        idx = s["idx"]
        idx = idx[active[idx[:, 0], idx[:, 1]]]
        if idx.shape[0] < min_px:
            continue
        out.append(dict(id=i, idx=idx, size=int(idx.shape[0]),
                        mag=float(s["mag"]), codes=s["codes"]))
    out.sort(key=lambda s: -s["mag"])
    return out


def arm_pixels(field: dict, seg: dict, offset: float, stride: int,
               shape: tuple[int, int]) -> np.ndarray:
    key = (seg["id"], float(offset), int(stride))
    p = _PIX.get(key)
    if p is not None:
        return p
    idx = seg["idx"][strike_order(seg["idx"], seg["id"])[::stride]]
    ax = field["ax"][idx[:, 0], idx[:, 1]]
    ay = field["ay"][idx[:, 0], idx[:, 1]]
    rr = np.rint(idx[:, 0] + offset * ay).astype(np.int64)
    cc = np.rint(idx[:, 1] + offset * ax).astype(np.int64)
    ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
    p = np.stack([rr[ok], cc[ok]], axis=1)
    _PIX[key] = p
    return p


def count_at_stride1(field: dict, segs, offsets, shape, active) -> int:
    n = 0
    for s in segs:
        for o in offsets:
            p = arm_pixels(field, s, o, 1, shape)
            if p.size:
                n += int(active[p[:, 0], p[:, 1]].sum())
    return n


def emit(field: dict, segs, offsets, stride, shape, active,
         widths=None, line_step: float = 3.0) -> tuple[np.ndarray, int, int]:
    """Emit one arm: every selected segment, uniformly thinned by ``stride``."""
    mask = np.zeros(shape, bool)
    n = used = 0
    for s in segs:
        w = 1 if widths is None else int(widths[s["id"]])
        offs = offsets if widths is None else (
            [0.0] if w == 0 else [j * line_step for j in range(-w, w + 1)])
        for o in offs:
            p = arm_pixels(field, s, o, stride, shape)
            if p.size:
                mask[p[:, 0], p[:, 1]] = True
        used += 1
    mask &= active
    return mask, int(mask.sum()), used


def pick_stride(field: dict, segs, offsets, shape, active, budget: int,
                kmax: int = 40) -> tuple[int, int]:
    """Uniform along-strike stride whose dot count lands closest to ``budget``.

    Every arm is thinned over *all* segments, so no arm is favoured by being
    allowed to concentrate on the highest-magnitude ridges.
    """
    n1 = count_at_stride1(field, segs, offsets, shape, active)
    if n1 <= budget:
        return 1, n1
    k = int(np.clip(round(n1 / float(budget)), 1, kmax))
    best = None
    for cand in range(max(1, k - 2), min(kmax, k + 2) + 1):
        m, n, _ = emit(field, segs, offsets, cand, shape, active)
        score = (abs(n - budget), cand)
        if best is None or score < best[0]:
            best = (score, cand, n)
    return int(best[1]), int(best[2])


# ----------------------------------------------------------------------
# EXP-1 : sigma table
# ----------------------------------------------------------------------

def comp_sigma_rows(field: dict, segs, fold) -> tuple[list[dict], int]:
    """Per withheld component: across/along-strike error to the nearest ridge.

    Returns ``(matched_rows, n_components_considered)``.  A component is
    *matched* when at least :data:`MATCH_FRAC` of its pixels lie within
    ``L_MAX`` of some candidate ridge pixel; unmatched components are detection
    failures, not localisation errors, and are counted separately.
    """
    from scipy.ndimage import label
    from scipy.spatial import cKDTree

    wmask = fold.withhold & ~fold.known
    lab, n = label(wmask, structure=np.ones((3, 3), int))
    considered = 0
    if n == 0 or not segs:
        return [], 0
    pts = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    owner = np.concatenate([np.full(s["size"], i) for i, s in enumerate(segs)])
    tree = cKDTree(pts)
    px = np.argwhere(wmask)
    d, j = tree.query(px.astype(np.float64), k=1, workers=-1)
    near = pts[j]
    ax = field["ax"][near[:, 0].astype(np.int64), near[:, 1].astype(np.int64)]
    ay = field["ay"][near[:, 0].astype(np.int64), near[:, 1].astype(np.int64)]
    dr = px[:, 0] - near[:, 0]
    dc = px[:, 1] - near[:, 1]
    across = np.abs(dr * ay + dc * ax)
    along = np.abs(dr * ax - dc * ay)
    cl = lab[px[:, 0], px[:, 1]]
    order = np.argsort(cl, kind="stable")
    cl, d, j, px, across, along = (cl[order], d[order], j[order], px[order],
                                   across[order], along[order])
    bnd = np.flatnonzero(np.diff(cl)) + 1
    rows = []
    for a, b in zip(np.r_[0, bnd], np.r_[bnd, cl.size]):
        if b - a < MIN_COMP_PX:
            continue
        considered += 1
        dd = d[a:b]
        frac = float((dd <= L_MAX).mean())
        if frac < MATCH_FRAC:
            continue
        aa, ll = across[a:b], along[a:b]
        seg_ids = owner[j[a:b]]
        vals, cnt = np.unique(seg_ids, return_counts=True)
        dom = segs[int(vals[cnt.argmax()])]
        code = max(dom["codes"], key=lambda c: c["scale"]) if dom["codes"] else {}
        band = code.get("band", "?")
        fam = next((f for f, bs in F58.FAMILIES.items() if band in bs), "other")
        rows.append(dict(block=fold.name, comp_px=int(b - a), frac_within=frac,
                         sigma_iso=float(np.sqrt(np.mean(np.minimum(dd, L_MAX) ** 2))),
                         sigma_across=float(np.sqrt(np.mean(np.minimum(aa, L_MAX) ** 2))),
                         sigma_along=float(np.sqrt(np.mean(np.minimum(ll, L_MAX) ** 2))),
                         med_iso=float(np.median(dd)),
                         med_across=float(np.median(aa)),
                         band=band, family=fam,
                         scale=float(code.get("scale", 0.0)),
                         sign=int(code.get("sign", 0))))
    return rows, considered


def _agg(v):
    v = np.asarray(v, float)
    if v.size == 0:
        return None
    return dict(n=int(v.size), median=float(np.median(v)), mean=float(v.mean()),
                p25=float(np.quantile(v, 0.25)), p75=float(np.quantile(v, 0.75)),
                rms=float(np.sqrt(np.mean(v ** 2))),
                min=float(v.min()), max=float(v.max()))


def _grp(rows, key, min_n=MIN_STRATUM):
    out = {}
    for k in sorted({key(r) for r in rows}):
        sub = [r for r in rows if key(r) == k]
        if len(sub) >= min_n:
            out[str(k)] = dict(
                sigma_iso=_agg([r["sigma_iso"] for r in sub]),
                sigma_across=_agg([r["sigma_across"] for r in sub]),
                sigma_along=_agg([r["sigma_along"] for r in sub]),
                med_across=_agg([r["med_across"] for r in sub]),
                frac_within=_agg([r["frac_within"] for r in sub]),
                comp_px=_agg([r["comp_px"] for r in sub]))
    return out


def _fam(r):
    return f"{r['family']}/{'crest' if r['sign'] < 0 else 'trough'}"


def sigma_table(rows: list[dict], considered: dict[str, int]) -> dict:
    tab = dict(n_matched_components=len(rows),
               n_components_considered=considered,
               match_fraction={b: round(considered.get(b, 0) and
                                        len([r for r in rows if r['block'] == b]) /
                                        considered[b], 4) for b in BLOCKS},
               pooled=dict(sigma_iso=_agg([r["sigma_iso"] for r in rows]),
                           sigma_across=_agg([r["sigma_across"] for r in rows]),
                           sigma_along=_agg([r["sigma_along"] for r in rows]),
                           med_across=_agg([r["med_across"] for r in rows]),
                           frac_within=_agg([r["frac_within"] for r in rows])),
               by_block=_grp(rows, lambda r: r["block"]),
               by_scale=_grp(rows, lambda r: f"{r['scale']:g}px"),
               by_type=_grp(rows, _fam),
               by_type_scale=_grp(rows, lambda r: f"{_fam(r)}/{r['scale']:g}px"),
               by_block_scale=_grp(rows, lambda r: f"{r['block']}/{r['scale']:g}px"),
               by_block_type=_grp(rows, lambda r: f"{r['block']}/{_fam(r)}"))
    cf = {}
    for b in BLOCKS:
        others = [r for r in rows if r["block"] != b]
        cf[b] = dict(by_type_scale=_grp(others, lambda r: f"{_fam(r)}/{r['scale']:g}px"),
                     by_type=_grp(others, _fam),
                     by_scale=_grp(others, lambda r: f"{r['scale']:g}px"),
                     by_block=_grp(others, lambda r: r["block"]),
                     pooled=dict(sigma_across=_agg([r["sigma_across"] for r in others]),
                                 sigma_iso=_agg([r["sigma_iso"] for r in others])))
    tab["cross_fitted"] = cf
    return tab


def sigma_lookup(table: dict, block: str, family: str, scale: float, sign: int,
                 cap: float = 8.0) -> tuple[float, str]:
    """Cross-fitted across-strike sigma with a recorded fallback chain."""
    cf = table["cross_fitted"][block]
    name = f"{family}/{'crest' if sign < 0 else 'trough'}"
    for level, key, bucket in (
            ("type_scale", f"{name}/{scale:g}px", cf["by_type_scale"]),
            ("type", name, cf["by_type"]),
            ("scale", f"{scale:g}px", cf["by_scale"]),
            ("block", block, cf["by_block"]),
            ("pooled_other_blocks", "pooled", cf)):
        node = bucket.get(key)
        if node:
            v = float(node["sigma_across"]["median"])
            return min(v, cap), f"{level}:{key}"
    return min(float(table["pooled"]["sigma_across"]["median"]), cap), "pooled_all"


def seg_type(seg: dict) -> tuple[str, float, int]:
    code = max(seg["codes"], key=lambda c: c["scale"]) if seg["codes"] else {}
    band = code.get("band", "?")
    fam = next((f for f, bs in F58.FAMILIES.items() if band in bs), "other")
    return fam, float(code.get("scale", 0.0)), int(code.get("sign", 0))


# ----------------------------------------------------------------------
# scoring
# ----------------------------------------------------------------------

def fold_terms(mask: np.ndarray, fold) -> np.ndarray:
    pred = np.where(mask, 1.0, 0.0).astype(np.float32)
    fdict = dict(region=np.ones(mask.shape, bool), visible=fold.visible,
                 masked_known=fold.known, truth=fold.withhold)
    _, terms = EH.evaluate(pred, fdict, fold.valid, block_side=200)
    return terms


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--min-px", type=int, default=8)
    ap.add_argument("--budget", type=int, default=44090)
    ap.add_argument("--line-step", type=float, default=3.0)
    ap.add_argument("--arms", default="")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    field = extract.build(workers=2)
    shape = field["mag"].shape
    folds = H58.all_folds()
    log = dict(protocol=PROTOCOL, evaluator=EH.VERSION, threshold=args.threshold,
               min_px=args.min_px, budget=args.budget, line_step=args.line_step,
               l_max=L_MAX, match_frac=MATCH_FRAC, block_side_px=200,
               arms={k: [list(v[0]), v[1]] for k, v in ARMS.items()})

    # ------------------------- EXP-1 -----------------------------------
    rows: list[dict] = []
    considered: dict[str, int] = {}
    segs_by_fold: dict[str, list] = {}
    for fold in folds:
        active = fold.valid & ~fold.known
        segs = build_segments(field, args.threshold, args.min_px, active)
        segs_by_fold[fold.name] = segs
        r, c = comp_sigma_rows(field, segs, fold)
        rows.extend(r)
        considered[fold.name] = c
    table = sigma_table(rows, considered)
    (out / "sigma_table.json").write_text(json.dumps(table, indent=1))
    (out / "sigma_rows.json").write_text(json.dumps(rows, indent=1))
    log["exp1"] = dict(pooled=table["pooled"], n_matched=len(rows),
                       considered=considered, seconds=round(time.time() - t0, 1))
    print("EXP-1", len(rows), "matched components; pooled", table["pooled"]["sigma_across"])

    # ------------------------- EXP-2 -----------------------------------
    arm_names = [a for a in ARMS if (not args.arms or a in args.arms.split(","))]
    terms: dict[str, list[np.ndarray]] = {}
    dots: dict[str, int] = {}
    segs_used: dict[str, list] = {}
    strides: dict[str, list] = {}
    for fold in folds:
        _ORDER.clear()
        _PIX.clear()
        active = fold.valid & ~fold.known
        segs = segs_by_fold[fold.name]
        widths = {}
        for s in segs:
            fam, scale, sign = seg_type(s)
            sig, _ = sigma_lookup(table, fold.name, fam, scale, sign)
            # lane rule: tight line below ~0.5 px, ribbon about +-sigma wide above
            widths[s["id"]] = 0 if sig < 0.5 else min(int(np.floor(sig / args.line_step)), 3)
        for name in arm_names + (["ADAPT"] if not args.arms or "ADAPT" in args.arms else []):
            if name == "ADAPT":
                stride, n = pick_stride(field, segs, (0.0,), shape, active, args.budget)
                m, n, u = emit(field, segs, (0.0,), stride, shape, active,
                               widths=widths, line_step=args.line_step)
                # adapt the stride so ADAPT lands on the same budget as the others
                for _ in range(6):
                    if n <= args.budget:
                        break
                    stride += 1
                    m, n, u = emit(field, segs, (0.0,), stride, shape, active,
                                   widths=widths, line_step=args.line_step)
            else:
                offsets, fixed = ARMS[name]
                stride = fixed if fixed > 0 else 1
                if fixed == 0:
                    stride, _ = pick_stride(field, segs, offsets, shape, active,
                                            args.budget)
                m, n, u = emit(field, segs, offsets, stride, shape, active)
            terms.setdefault(name, []).append(fold_terms(m, fold))
            dots[name] = dots.get(name, 0) + n
            segs_used.setdefault(name, []).append(u)
            strides.setdefault(name, []).append(int(stride))
        print("  scored", fold.name, {k: dots.get(k) for k in dots}, flush=True)

    stacked = {k: np.vstack(v) for k, v in terms.items()}
    summary = EH.pooled_summary(stacked, candidate="ADAPT" if "ADAPT" in stacked
                                else arm_names[0], draws=1000)
    (out / "exp2_equal_budget.json").write_text(json.dumps(
        dict(log=log, summary=summary, dots=dots, segments_used=segs_used,
             strides=strides),
        indent=1, default=float))
    log["exp2_seconds"] = round(time.time() - t0, 1)
    print("dots:", dots)
    print("DTI :", {k: round(v["dti"], 6) for k, v in summary["scores"].items()})
    (out / "run_log.json").write_text(json.dumps(log, indent=1, default=float))
    print("seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
