#!/usr/bin/env python3
"""Session-6 emission: ribbon width matched to the measured localisation error.

What this script does, in order:

1. reads the cached multi-family / multi-scale ridge field (geophysics only, never
   the catalogue);
2. assigns every ridge segment a ``(block, family/sign, scale)`` stratum and a
   localisation scale ``sigma`` from the holdout sigma table, through the module's
   explicit, recorded fallback chain;
3. compares, **with the shared exact metric** and at an equal dot budget on the
   pooled four-fold buffered hide-and-recover holdout:
     * ``uniform``  -- one (K, spacing, pitch) for every segment, K taken from the
       geometry sweep in ``evidence/s6/geom.json``;
     * ``adaptive`` -- K = 2*round(sigma/spacing) + 1 per segment, i.e. a ribbon
       about +-sigma wide (the lane's prescription), capped at 7 lines;
   and reports the marginal utility ``U = (1 - alpha*DTI0)*dTP - alpha*DTI0*dFP``
   per sigma class for the chosen arm;
4. emits the delivered raster (full-catalogue collar) and the holdout-domain
   raster (visible-fault collar only), runs the local format gate on the former.

Two different rasters are produced on purpose. The delivered file excludes a
collar around the *whole* mapped catalogue, because the organizer masks catalogue
pixels and the live evidence says the scoring population lies away from them. The
holdout file can only be scored against withheld *catalogue* segments, so it must
exclude only the *visible* catalogue plus the protocol buffer. Their geometry and
support ranking are identical; only the exclusion mask differs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("GEMS_FEATURE_STACK", str(Path.home() / ".cache/gems/training_features.tif"))

from gems57 import metric as M                                   # noqa: E402
from gems58w import extract, grid, holdout, sigma as sigmod, submission  # noqa: E402
import s6_ribbon as S                                            # noqa: E402

EV = ROOT / "evidence" / "s6"
ALPHA = M.ALPHA


def strata_of(seg: dict) -> tuple[str, str, str]:
    """(block, family/sign, scale) of the segment's dominant ridge code."""
    codes = seg.get("codes") or []
    fam, scale, sign = "other", 0.0, 0
    if codes:
        c = max(codes, key=lambda c: float(c.get("scale", 0.0)))
        fam = sigmod._family_of(c.get("band", "?"))
        scale = float(c.get("scale", 0.0))
        sign = int(c.get("sign", 0))
    block = holdout.block_of(seg["idx"].mean(axis=0))
    return block, f"{fam}/{'crest' if sign < 0 else 'trough'}", f"{scale:g}px"


def k_from_sigma(sigma: float, spacing: float, kmax: int = 7) -> int:
    """Ribbon about +-sigma wide: K = 2*round(sigma/spacing) + 1 parallel lines."""
    if sigma < 0.5:
        return 1                      # tighter than half a pixel: one tight line
    return int(min(kmax, 2 * max(1, int(round(sigma / spacing))) + 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--budget", type=int, default=38000)
    ap.add_argument("--spacing", type=float, default=3.0)
    ap.add_argument("--pitch", type=int, default=3)
    ap.add_argument("--collar", type=int, default=2)
    ap.add_argument("--uniform-k", type=int, default=5)
    ap.add_argument("--overemit", type=float, default=1.35,
                    help="emit this multiple of the budget, then thin to isolated dots")
    ap.add_argument("--name", default=None)
    ap.add_argument("--outdir", default="docs/downloads")
    a = ap.parse_args()

    t0 = time.time()
    field = extract.build(workers=2)
    segs = extract.segments(field, a.threshold, min_px=6)
    for i, s in enumerate(segs):
        s["tag"] = i
    folds = holdout.all_folds()
    table = json.loads((EV / "sigma.json").read_text())["table"]
    geom = json.loads((EV / "geom.json").read_text())
    dti0 = float(geom["dti0_for_U_rule"])
    bar = ALPHA * dti0

    for s in segs:
        block, kind, scale_s = strata_of(s)
        s["block"], s["kind"], s["scale_s"] = block, kind, scale_s
        fam, signame = kind.split("/")
        s["sigma"], s["stratum_used"] = sigmod.sigma_for(
            fam, float(scale_s.rstrip("px")), -1 if signame == "crest" else 1, block, table)
        s["stratum"] = f"{block}/{kind}/{scale_s}"
        s["K_adaptive"] = k_from_sigma(s["sigma"], a.spacing)

    emit_budget = int(round(a.budget * a.overemit))

    def thin(mask):
        m = S.isolate(mask)
        n = int(m.sum())
        if n > a.budget:                       # keep the strongest ridge pixels
            yy, xx = np.nonzero(m)
            v = field["mag"][yy, xx]
            keep = np.argsort(-v, kind="stable")[: a.budget]
            m = np.zeros(m.shape, bool)
            m[yy[keep], xx[keep]] = True
        return m

    arms = {
        f"uniform_K{a.uniform_k}_s{a.spacing:g}_p{a.pitch}":
            (lambda s: S.Pattern(a.uniform_k, a.spacing, a.pitch)),
        "adaptive_K(sigma)": (lambda s: S.Pattern(s["K_adaptive"], a.spacing, a.pitch)),
    }
    rank = lambda s: s["mag"] * s["size"]                      # noqa: E731
    results = {}
    for label, pat_of in arms.items():
        terms = []
        for f in folds:
            allowed = f.valid & ~f.known
            m, _ = S.emit(field, segs, pat_of, allowed, emit_budget, order_key=rank)
            terms.append(S.score_fold(thin(m), f))
        r = S.pool(terms)
        r.update(per_fold=[dict(block=fo.name, **t) for fo, t in zip(folds, terms)],
                 withheld_positive_pixels=sum(int(t["n_truth"]) for t in terms))
        results[label] = r
        print(f"{label:34s} HOLDOUT-DTI {r['dti']:.6f}  n={r['n_emitted']}  "
              f"cov {r['coverage']:.4f}  credit/dot {r['credit_per_dot']:.4f}", flush=True)

    best_label = max(results, key=lambda k: results[k]["dti"])
    best = results[best_label]
    print("chosen arm:", best_label, round(best["dti"], 6), flush=True)

    # ---- per-class marginal utility of the chosen arm vs a tight line ----
    per_class: dict[str, dict] = {}
    groups: dict[str, list] = {}
    for s in segs:
        groups.setdefault(s["stratum"], []).append(s)
    for name in sorted(groups, key=lambda k: -len(groups[k])):
        sub = groups[name]
        if len(sub) < 20:
            continue
        arms_cls = {"K1_tight": (lambda s: S.Pattern(1, a.spacing, a.pitch)),
                    "chosen": (arms[best_label])}
        out = {}
        for lbl, pat_of in arms_cls.items():
            terms = [S.score_fold(
                thin(S.emit(field, sub, pat_of, f.valid & ~f.known,
                            max(200, int(round(emit_budget * len(sub) / len(segs)))),
                            order_key=rank)[0]), f) for f in folds]
            out[lbl] = S.pool(terms)
        dTP = out["chosen"]["tp"] - out["K1_tight"]["tp"]
        dFP = out["chosen"]["fp"] - out["K1_tight"]["fp"]
        U = (1.0 - ALPHA * dti0) * dTP - ALPHA * dti0 * dFP
        per_class[name] = dict(
            n_segments=len(sub), sigma_px=round(float(np.median([s["sigma"] for s in sub])), 3),
            stratum_used=sub[0]["stratum_used"],
            k_adaptive=int(np.median([s["K_adaptive"] for s in sub])),
            dti_K1=round(out["K1_tight"]["dti"], 6), dti_chosen=round(out["chosen"]["dti"], 6),
            dTP=round(dTP, 3), dFP=round(dFP, 3), U=round(U, 4), positive=bool(U > 0),
            n_emitted_K1=out["K1_tight"]["n_emitted"], n_emitted_chosen=out["chosen"]["n_emitted"])
        print(f"  {name:38s} n={len(sub):5d} sigma={per_class[name]['sigma_px']:5.2f} "
              f"K={per_class[name]['k_adaptive']}  {out['K1_tight']['dti']:.5f} -> "
              f"{out['chosen']['dti']:.5f}  U={U:+.2f}", flush=True)

    # ---------------- emission ----------------
    pat_of = arms[best_label]
    cat = grid.catalogue()
    fp = grid.footprint()
    real_allowed = fp & ~cat
    if a.collar > 0:
        real_allowed &= ~binary_dilation(cat, np.ones((2 * a.collar + 1,) * 2, bool))
    mask_real, plans = S.emit(field, segs, pat_of, real_allowed, emit_budget, order_key=rank)
    mask_real = thin(mask_real)
    n_dots = int(mask_real.sum())

    hold_masks = [thin(S.emit(field, segs, pat_of, f.valid & ~f.known, emit_budget,
                              order_key=rank)[0]) for f in folds]
    hold_terms = [S.score_fold(m, f) for m, f in zip(hold_masks, folds)]
    hold = S.pool(hold_terms)
    hold.update(per_fold=[dict(block=fo.name, **t) for fo, t in zip(folds, hold_terms)],
                withheld_positive_pixels=sum(int(t["n_truth"]) for t in hold_terms))

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = a.name or f"gems58-s6-ribbon-sigma{n_dots}-{stamp}"
    outdir = ROOT / a.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    tif = outdir / f"{name}.tif"
    for suf in (".tif", ".zip", ".json"):
        q = (tif.with_suffix(suf))
        if q.exists():
            q.unlink()
    submission.write(tif, mask_real)
    val = submission.validate(tif, min_dots=1000, max_dots=200000)

    dcat = distance_transform_edt(~cat)
    dist = dcat[mask_real]
    kdist = {}
    for K in sorted({p["pattern"] for p in plans}):
        kdist[K] = int(sum(p["dots"] for p in plans if p["pattern"] == K))

    res = dict(
        evidence_class="HOLDOUT-DTI+FORMAT", protocol=S.PROTOCOL, evaluator=S.EVALUATOR,
        threshold=a.threshold, budget=a.budget, spacing=a.spacing, pitch=a.pitch,
        collar=a.collar, dti0_for_U=dti0, marginal_bar=bar,
        isolated_dots=True, overemit=a.overemit,
        arms=results, chosen_arm=best_label,
        per_class=per_class,
        n_segments=len(segs), n_dots=n_dots, dots_by_pattern_before_thinning=kdist,
        holdout=hold,
        delivered_file_excludes=dict(catalogue_pixels=int(cat.sum()),
                                     collar_px=a.collar),
        distance_to_catalogue_px=dict(median=float(np.median(dist)),
                                      p10=float(np.quantile(dist, .1)),
                                      p90=float(np.quantile(dist, .9)),
                                      frac_within_3px=float((dist <= 3).mean())),
        validator=val, file=tif.name, sha256=val["sha256"], bytes=val["bytes"],
        wall_seconds=round(time.time() - t0, 1))
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "emit.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: res[k] for k in ("chosen_arm", "n_dots", "holdout",
                                          "distance_to_catalogue_px", "sha256")},
                     indent=1, default=float))
    print("validator passed:", val["passed"], "wrote", tif)
    return 0 if val["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
