#!/usr/bin/env python3
"""Novelty-constrained variant of the scatter-cover emission (same lane, new mass).

Why this file exists
--------------------
The scatter-cover emission (`ribbon_build_scatter_lane.py`) is the best-measured
emission rule in the family record, but its dots fall on the *same structures* as
the lane's earlier 5-line ribbon file, so 77 % of them land within 3 px of that
earlier raster's dots — a literal breach of the lane's own "one registry raster
within 3 px" stop rule, even though the two files are the same lane's output.

This script builds the same emission with a **novelty constraint**: a candidate
pixel is only eligible when it is more than ``--novel-margin`` px away from every
dot of the named prior rasters.  The result is the max-coverage of the scatter
density over the part of the field the lane has *never emitted*, which is also
the part of the surface that the two-round objective pays for (the final round is
scored against faults the panel verifies from the submissions themselves).

Everything else is identical: scatter sigma, catalogue margin, greedy sweep by
descending density, the 15 local portal checks, the exact-metric holdout read-out
and the registry screen.

    PYTHONPATH=src python3 scripts/ribbon_build_novel_lane.py --exclude <tif> ...
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems58w import extract, grid, holdout, metric, submission, uniqueness  # noqa: E402
from gems58w import sigma as SIGMA  # noqa: E402
from gems58w.metric import ALPHA  # noqa: E402
from gems58w.paths import EVIDENCE, downloads_dir, evidence_dir  # noqa: E402

import ribbon_build_scatter_lane as SL  # noqa: E402


def load_dots(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        a = s.read(1)
    return np.nan_to_num(a) > 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", action="append", default=[], required=True,
                    help="prior raster whose 3-px neighbourhood is off-limits (repeatable)")
    ap.add_argument("--novel-margin", type=float, default=3.0)
    ap.add_argument("--scatter-px", type=float, default=SL.SCATTER_PX)
    ap.add_argument("--g-hat", type=float, default=SL.G_HAT)
    ap.add_argument("--dti0", type=float, default=0.3195)
    ap.add_argument("--cat-margin", type=float, default=3.0)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--max-dots", type=int, default=44090)
    ap.add_argument("--cand-quantile", type=float, default=0.95)
    ap.add_argument("--name", default="gems58-novel-scatter-44090-20261011T0630Z")
    ap.add_argument("--registry-dir", default=str(ROOT / "data" / "registry" / "rasters"))
    ap.add_argument("--rho-subsample", type=int, default=200000)
    args = ap.parse_args()
    t0 = time.time()

    fp = grid.footprint()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=8)
    cat_d = distance_transform_edt(~grid.catalogue()).astype(np.float32)

    items = []
    for f in holdout.all_folds():
        items.extend(SIGMA.measure(field, segs, f))
    sigma_table = SIGMA.sigma_table(items)

    m = SL.scatter_density(field["mag"], fp, args.scatter_px, args.g_hat)
    bar = ALPHA * args.dti0
    thr = float(np.quantile(m[fp], args.cand_quantile))
    cmask = (m >= thr) & fp & (cat_d >= args.cat_margin)

    excl = np.zeros_like(cmask)
    excl_info = []
    for p in args.exclude:
        p = Path(p)
        if not p.exists():
            print(f"[novel] EXCLUDE MISSING: {p}", flush=True)
            continue
        d = load_dots(p)
        near = distance_transform_edt(~d) <= args.novel_margin
        excl |= near
        excl_info.append(dict(path=str(p), name=p.name, dots=int(d.sum()),
                              excluded_px=int(near.sum())))
        print(f"[novel] excluding {int(near.sum())} px within {args.novel_margin:g} px of "
              f"{p.name} ({int(d.sum())} dots)", flush=True)

    cand_mask = cmask & ~excl
    cand = np.argwhere(cand_mask)
    vals = m[cand_mask]
    print(f"[novel] candidates {cand.shape[0]} of {int(cmask.sum())} "
          f"({100.0*cand.shape[0]/max(1,int(cmask.sum())):.1f} % of the scatter support "
          f"survives the novelty constraint)", flush=True)

    dots, log = SL.greedy_marginal(m, cand, vals, 0.0, args.max_dots)
    n_dots = int(dots.sum())
    print(f"[build] placed {n_dots} novel dots in {time.time()-t0:.0f}s "
          f"(last marginal credit {log[-1]['gain']:.4f} px vs bar {bar:.4f})", flush=True)

    tif = downloads_dir() / f"{args.name}.tif"
    submission.write(tif, dots)
    val = submission.validate(tif)
    print(f"[validate] passed={val['passed']} n_positives={val['n_positives']} "
          f"sha256={val['sha256'][:16]}...", flush=True)

    screens, usum = uniqueness.screen_against(dots, Path(args.registry_dir),
                                              rho_subsample=args.rho_subsample)
    print(f"[unique] checked {usum['n_checked']} | worst rho {usum['worst_rho']:.4f} "
          f"({usum['worst_rho_name']}) | worst forward overlap "
          f"{usum['worst_forward_overlap']:.4f} ({usum['worst_forward_overlap_name']}) | "
          f"triggers {usum['n_triggers']}", flush=True)

    folds = holdout.all_folds()
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0)
    for f in folds:
        r = metric.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        for key in ("tp", "fp", "fn", "n_truth"):
            agg[key] += getattr(r, key)
    den = agg["tp"] + ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    pooled = float(agg["tp"] / den)
    print(f"[holdout] HOLDOUT-DTI {pooled:.6f} on {agg['n_truth']:.0f} withheld positives; "
          f"folds { {k: round(v, 4) for k, v in per_fold.items()} }", flush=True)

    v = cat_d[dots]
    prof = dict(median_px=float(np.median(v)), mean_px=float(v.mean()),
                frac_le3px=float((v <= 3).mean()), frac_le10px=float((v <= 10).mean()),
                on_catalogue=int((v <= 0.001).sum()))

    note = submission.note(
        f"Novel-mass scatter cover: {n_dots} dots on the {args.scatter_px}px scatter density, "
        f">= {args.novel_margin:g}px from every earlier registry raster.")
    card = dict(
        name=args.name,
        hypothesis=("H58-S3n novel-mass scatter cover: the same scatter-cover rule restricted to "
                    "the part of the field the lane has never emitted"),
        mechanism=("candidates must lie outside the 3-px neighbourhood of every named prior "
                   "raster, so every dot adds coverage the registry does not already contain; "
                   "the remaining candidates are then swept by descending scatter density "
                   "under the metric's marginal-inclusion rule"),
        named_non_fault_process=("same as the scatter-cover emission: magnetic flight-line "
                                 "artefacts and non-tectonic DEM scarp curvature; the novelty "
                                 "constraint additionally concentrates the emission on the "
                                 "weaker part of the field, where those mimics are relatively "
                                 "more common, which is the main risk of this variant"),
        holdout_dti=pooled, holdout_dti_evaluator=metric.EVALUATOR_VERSION,
        holdout_dti_protocol=holdout.PROTOCOL,
        holdout_dti_withheld_positives=int(agg["n_truth"]),
        holdout_dti_per_fold=per_fold, holdout_dti_ci=[None, None],
        holdout_dti_ci_note=("four spatial blocks give four paired observations; no absolute "
                             "interval is quoted"),
        novelty=dict(exclude=excl_info, margin_px=args.novel_margin,
                     candidates=int(cand.shape[0]),
                     scatter_support=int(cmask.sum())),
        registry=usum, registry_rows=[s.as_dict() for s in screens],
        raster_sha256=val["sha256"], raster_bytes=val["bytes"],
        validator=dict(passed=val["passed"], n_positives=val["n_positives"],
                       checks=val["checks"]),
        catalogue_distance_profile=prof,
        sigma_table={k: x for k, x in sigma_table.items() if k != "by_type_scale"},
        submission_note=note, submission_note_chars=len(note),
        verdict=("candidate — novelty-constrained emission; download OK, submit decision "
                 "belongs to the slot selector"),
        wall_seconds=round(time.time() - t0, 2),
    )

    zp = downloads_dir() / f"{args.name}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zp) as z:
        card["zip_sha256"] = submission.sha256(zp)
        card["zip_contains"] = z.namelist()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "run_card_novel.json").write_text(json.dumps(card, indent=1, default=float))
    (downloads_dir() / f"{args.name}.checks.json").write_text(json.dumps(
        dict(validator=val, uniqueness_summary=usum,
             holdout=dict(pooled=pooled, per_fold=per_fold),
             novelty=card["novelty"], catalogue_distance_profile=prof),
        indent=1, default=float))
    print("wrote", tif, "\nwrote", zp, "\nwrote evidence/run_card_novel.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
