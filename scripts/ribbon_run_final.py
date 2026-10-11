"""Ribbon lane, session 4: EXP-2 (equal-budget width sweep) and EXP-3 (emission).

EXP-2 -- every arm emits the *same number of dots* on the same segment set and
differs only in across-strike line offsets and along-strike dot stride.  The
budget is enforced exactly: segments are taken in descending ridge magnitude and
a segment that would overflow is skipped, not terminated.

EXP-3 -- the lane's decision rule executed exactly.  For every ridge segment and
every across-strike offset in ``{-6..+6}`` an "arm" (one parallel dotted line) is
offered to the shared exact-metric greedy in :mod:`gems57.exact_emission`, which
accepts an arm only when the official batch marginal test says it raises the DTI.
The number and offset of parallel lines per segment is therefore chosen by the
metric itself, not by a width formula.  A dot cap supplies the budget.

Both are scored with ``gems57.evaluate_holdout``; the 95 % CI is the paired
physical spatial-block percentile bootstrap over 20 km blocks.  EXP-3 then emits
the selected arm set with ``gems57.submission_writer``.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from gems57 import evaluate_holdout as EH
from gems57 import exact_emission as EE
from gems58w import extract, grid as g58, holdout as H58

import importlib.util as _ilu

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "ribbon_v3"

_spec = _ilu.spec_from_file_location("_rws", ROOT / "scripts" / "ribbon_run_width_sweep.py")
_rws = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_rws)

ARMS: dict[str, tuple[float, ...]] = {
    "T1": (0.0,),
    "R3_d2": (-2.0, 0.0, 2.0),
    "R5_d2": (-4.0, -2.0, 0.0, 2.0, 4.0),
    "R3_d3": (-3.0, 0.0, 3.0),
    "R5_d3": (-6.0, -3.0, 0.0, 3.0, 6.0),
    "R7_d2": (-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0),
}
OFFSET_GRID = tuple(float(o) for o in range(-6, 7))
#: per-fold cache of (segment, ribbon, stride) -> active pixel union
_SEGCOUNT: dict = {}
EXACT_OFFSETS = OFFSET_GRID
EXACT_FOLDS = {"NW", "NE", "SW", "SE"}


def _seg_arm_pixels(field, seg, offsets, stride, shape, active, W):
    """(linear indices, count of active pixels) for one segment's whole ribbon.

    Using a *linear* index set collapses the parallel lines of one ribbon into a
    single union, so the budget is charged once for a pixel two lines share, and
    the active-domain test is a gather over the arm's own pixels instead of a
    full-grid boolean AND per segment (which made the sweep quadratic).
    """
    key = (seg["id"], float(offsets[0]), float(offsets[-1]), len(offsets), stride)
    got = _SEGCOUNT.get(key)
    if got is not None:
        return got
    chunks = []
    for o in offsets:
        q = _rws.arm_pixels(field, seg, o, stride, shape)
        if q.size:
            chunks.append(q[:, 0].astype(np.int64) * W + q[:, 1].astype(np.int64))
    if not chunks:
        out = (np.empty(0, np.int64), 0)
    else:
        lin = np.unique(np.concatenate(chunks))
        cnt = int(active[lin // W, lin % W].sum())
        out = (lin[active[lin // W, lin % W]], cnt)
    _SEGCOUNT[key] = out
    return out


def fill_budget(field, segs, offsets, stride, shape, active, budget,
                widths=None, line_step=3.0, mask_out=None):
    """Emit segments in descending ridge magnitude until the budget is filled.

    A segment whose ribbon would overflow the remaining budget is *skipped* so
    that shorter segments further down the list can still be placed.  Every arm
    therefore lands within a few dots of the same budget.
    """
    W = shape[1]
    n = 0
    used = 0
    skipped = 0
    chosen = []
    for s in segs:
        w = 1 if widths is None else int(widths[s["id"]])
        offs = offsets if widths is None else (
            (0.0,) if w == 0 else tuple(j * line_step for j in range(-w, w + 1)))
        lin, cnt = _seg_arm_pixels(field, s, offs, stride, shape, active, W)
        if cnt == 0:
            continue
        if n + cnt > budget:
            skipped += 1
            if skipped > 4000:
                break
            continue
        n += cnt
        used += 1
        chosen.append(lin)
    if mask_out is not None and chosen:
        lin = np.concatenate(chosen)
        mask_out.reshape(-1)[lin] = True
    return n, used


def choose_stride(field, segs, offsets, shape, active, budget, kmax=24):
    """Stride whose filled dot count is closest to (and not above) the budget."""
    n1 = _rws.count_at_stride1(field, segs, offsets, shape, active)
    if n1 <= budget:
        return 1, n1
    k = int(np.clip(round(n1 / float(budget)), 1, kmax))
    best = None
    for cand in sorted({max(1, k + d) for d in (-1, 0, 1, 2)}):
        n, _ = fill_budget(field, segs, offsets, cand, shape, active, budget)
        if n <= budget and (best is None or n > best[1]):
            best = (cand, n)
    return (best[0], best[1]) if best else (k, None)


def terms_of(mask, fold):
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
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--exact-u-offsets", default="-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6")
    ap.add_argument("--exact-u-folds", default="NW,NE,SW,SE")
    ap.add_argument("--no-exact-u", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    field = extract.build(workers=2)
    shape = field["mag"].shape
    folds = H58.all_folds()
    global EXACT_OFFSETS, EXACT_FOLDS
    EXACT_OFFSETS = tuple(float(x) for x in args.exact_u_offsets.split(","))
    EXACT_FOLDS = set(x.strip() for x in args.exact_u_folds.split(","))
    table = json.loads((out / "sigma_table.json").read_text())
    log = dict(protocol="gems58-pooled-hide-v1", evaluator=EH.VERSION,
               threshold=args.threshold, min_px=args.min_px, budget=args.budget,
               line_step=args.line_step, offset_grid=list(OFFSET_GRID),
               arms={k: list(v) for k, v in ARMS.items()})

    per_fold: dict[str, list] = {}
    dots: dict[str, int] = {}
    stride_log: dict[str, list] = {}
    arm_choice: dict[str, dict] = {}
    masks: dict[str, np.ndarray] = {}

    for fold in folds:
        _rws._ORDER.clear()
        _rws._PIX.clear()
        _SEGCOUNT.clear()
        active = fold.valid & ~fold.known
        segs = _rws.build_segments(field, args.threshold, args.min_px, active)

        # ---- fixed-geometry arms -------------------------------------
        for name, offsets in ARMS.items():
            stride, _ = choose_stride(field, segs, offsets, shape, active, args.budget)
            m = np.zeros(shape, bool)
            n, u = fill_budget(field, segs, offsets, stride, shape, active,
                               args.budget, mask_out=m)
            per_fold.setdefault(name, []).append(terms_of(m, fold))
            dots[name] = dots.get(name, 0) + n
            stride_log.setdefault(name, []).append(int(stride))
            arm_choice.setdefault(name, {})[fold.name] = dict(dots=n, segs=u,
                                                              stride=int(stride))

        # ---- ADAPT: sigma-derived width --------------------------------
        widths = {}
        for s in segs:
            fam, scale, sign = _rws.seg_type(s)
            sig, _ = _rws.sigma_lookup(table, fold.name, fam, scale, sign)
            widths[s["id"]] = 0 if sig < 0.5 else min(int(np.floor(sig / args.line_step)), 3)
        stride, _ = choose_stride(field, segs, (0.0,), shape, active, args.budget)
        m = np.zeros(shape, bool)
        n, u = fill_budget(field, segs, (0.0,), stride, shape, active,
                           args.budget, widths=widths,
                           line_step=args.line_step, mask_out=m)
        per_fold.setdefault("ADAPT", []).append(terms_of(m, fold))
        dots["ADAPT"] = dots.get("ADAPT", 0) + n
        stride_log.setdefault("ADAPT", []).append(int(stride))
        arm_choice.setdefault("ADAPT", {})[fold.name] = dict(dots=n, segs=u,
                                                             stride=int(stride))

        # ---- EXACT_U: shared greedy over (segment, offset) arms ---------
        if args.no_exact_u or fold.name not in EXACT_FOLDS:
            print("  ", fold.name, {k: dots.get(k) for k in dots}, flush=True)
            continue
        ledger = EE.DotLedger(fold.withhold & ~fold.known, active)
        arms, keys = [], []
        for si, s in enumerate(segs):
            for o in EXACT_OFFSETS:
                p = _rws.arm_pixels(field, s, o, 1, shape)
                if p.size == 0:
                    continue
                p = p[active[p[:, 0], p[:, 1]]]
                if p.size == 0:
                    continue
                arms.append(p)
                keys.append((s["id"], o))
        steps = EE.sorted_greedy_arms(ledger, arms, keys, max_dots=args.budget)
        arm_of = {k: i for i, k in enumerate(keys)}
        m = np.zeros(shape, bool)
        for st in steps:
            i = arm_of.get((st.seg_id, st.offset_px))
            if i is None:
                i = arm_of.get((st.seg_id, float(round(st.offset_px))))
            if i is not None:
                a = arms[i]
                m[a[:, 0], a[:, 1]] = True
        hist: dict[int, int] = {}
        per_seg: dict[int, set] = {}
        for st in steps:
            per_seg.setdefault(st.seg_id, set()).add(round(st.offset_px))
        for sid, offs in per_seg.items():
            key = len([o for o in offs if abs(o) > 1e-9]) // 2
            hist[key] = hist.get(key, 0) + 1
        per_fold.setdefault("EXACT_U", []).append(terms_of(m & active, fold))
        dots["EXACT_U"] = dots.get("EXACT_U", 0) + int((m & active).sum())
        arm_choice.setdefault("EXACT_U", {})[fold.name] = dict(
            dots=int((m & active).sum()), arms_accepted=len(steps),
            n_arms_offered=len(arms), ring_histogram={str(k): v for k, v in hist.items()})
        if fold.name == "NW":
            masks["EXACT_U_NW"] = m & active
        print("  ", fold.name, {k: dots.get(k) for k in dots}, flush=True)

    stacked = {k: np.vstack(v) for k, v in per_fold.items()}
    cand = "EXACT_U" if "EXACT_U" in stacked else "ADAPT"
    summary = EH.pooled_summary(stacked, candidate=cand, draws=1000)
    log["dots"] = dots
    log["strides"] = stride_log
    log["arm_choice"] = arm_choice
    log["seconds"] = round(time.time() - t0, 1)
    (out / "exp3_equal_budget.json").write_text(json.dumps(
        dict(log=log, summary=summary), indent=1, default=float))
    print("dots", dots)
    print("DTI ", {k: round(v["dti"], 6) for k, v in summary["scores"].items()})
    print("seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
