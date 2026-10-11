#!/usr/bin/env python3
"""EXP-3 emission: build, validate and screen the session-4 ribbon-lane raster.

Reuses the shared template end to end -- no private scoring, metric or writer:

* ridge field        ``gems58w.extract`` (cached, catalogue-free)
* sigma table        ``evidence/ribbon_v3/sigma_table.json`` (cross-fitted)
* emission geometry  ``scripts/ribbon_run_width_sweep`` helpers
* writer / gates     ``gems57.submission_writer``, ``gems57.gates``, ``gems57.validate``
* uniqueness screen  ``gems57.uniqueness.compare_array_to_registry``
* holdout scoring    ``gems57.evaluate_holdout``

The exported raster is the **all-finite zeros** representation (0 outside the
footprint, never NaN anywhere), which is the shared template's submission policy
and the direct answer to the portal rejection "Predicted values must be in range
[0, 1]".
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util as _ilu
import json
import time
from pathlib import Path

import numpy as np

from gems57 import evaluate_holdout as EH
from gems57 import gates as G57
from gems57 import submission_writer as SW
from gems57 import uniqueness as U57
from gems57 import validate as V57
from gems58w import extract, grid as g58, holdout as H58

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "ribbon_v3"
DOCS = ROOT / "docs"
SAMPLE = ROOT / "data" / "official" / "sample_submission.tif"

_spec = _ilu.spec_from_file_location("_rws", ROOT / "scripts" / "ribbon_run_width_sweep.py")
_rws = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_rws)
_spec2 = _ilu.spec_from_file_location("_rf", ROOT / "scripts" / "ribbon_run_final.py")
_rf = _ilu.module_from_spec(_spec2)
_spec2.loader.exec_module(_rf)


def dot_stats(m: np.ndarray, fp: np.ndarray, cat: np.ndarray) -> dict:
    from scipy.ndimage import distance_transform_edt
    d = distance_transform_edt(~cat)
    dm = d[m]
    return dict(n_dots=int(m.sum()),
                footprint_fraction=float(m.sum() / fp.sum()),
                on_catalogue=int((m & cat).sum()),
                median_distance_to_catalogue_px=float(np.median(dm)) if dm.size else None,
                frac_within_3px_of_catalogue=float((dm <= 3).mean()) if dm.size else None,
                frac_beyond_10px=float((dm > 10).mean()) if dm.size else None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--min-px", type=int, default=8)
    ap.add_argument("--budget", type=int, default=44090)
    ap.add_argument("--line-step", type=float, default=3.0)
    ap.add_argument("--name", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--out-dir", default=str(DOCS / "downloads"))
    ap.add_argument("--skip-uniqueness", action="store_true")
    ap.add_argument("--stride", type=int, default=0,
                    help="fix the along-strike dot stride; 0 = fit the budget over all segments")
    args = ap.parse_args()
    t0 = time.time()

    exp3 = json.loads((OUT / "exp3_equal_budget.json").read_text())
    table = json.loads((OUT / "sigma_table.json").read_text())
    scores = exp3["summary"]["scores"]
    # EXACT_U is a per-fold diagnostic (its arm ranking needs the withheld truth
    # of the fold it is emitted in), so it is not deployable; pick the best
    # deployable arm unless one is named explicitly.
    deployable = [k for k in scores if k != "EXACT_U"]
    arm = args.arm or max(deployable, key=lambda k: scores[k]["dti"])
    log = dict(chosen_arm=arm, arm_scores={k: v["dti"] for k, v in scores.items()},
               deployable_arms=deployable, budget=args.budget,
               threshold=args.threshold, min_px=args.min_px,
               line_step=args.line_step,
               note_exact_u="EXACT_U ranks (segment, offset) arms by the fold's own "
                            "withheld truth, so it is a diagnostic upper reference, "
                            "not a deployable rule; it is reported, not emitted.")

    field = extract.build(workers=2)
    shape = field["mag"].shape
    fp = g58.footprint()
    cat = g58.catalogue()
    active = fp & ~cat                      # catalogue pixels are masked by the organiser

    _rws._ORDER.clear()
    _rws._PIX.clear()
    _rf._SEGCOUNT.clear()
    segs = _rws.build_segments(field, args.threshold, args.min_px, active)

    widths = None
    if arm == "ADAPT":
        widths = {}
        for s in segs:
            # block of the segment centroid, so the sigma lookup is cross-fitted
            blk = H58.block_of(s["idx"].mean(axis=0))
            fam, scale, sign = _rws.seg_type(s)
            sig, _ = _rws.sigma_lookup(table, blk, fam, scale, sign)
            widths[s["id"]] = 0 if sig < 0.5 else min(int(np.floor(sig / args.line_step)), 3)
        offsets = (0.0,)
        stride = args.stride or _rf.choose_stride(field, segs, offsets, shape,
                                                  active, args.budget)[0]
        mask = np.zeros(shape, bool)
        n, used = _rf.fill_budget(field, segs, offsets, stride, shape, active,
                                  args.budget, widths=widths,
                                  line_step=args.line_step, mask_out=mask)
    else:
        offsets = _rf.ARMS[arm]
        stride = args.stride or _rf.choose_stride(field, segs, offsets, shape,
                                                  active, args.budget)[0]
        mask = np.zeros(shape, bool)
        n, used = _rf.fill_budget(field, segs, offsets, stride, shape, active,
                                  args.budget, mask_out=mask)
    log.update(dots=n, segments_used=used, stride=int(stride),
               stride_rule=("fixed at --stride" if args.stride
                            else "fit to the budget over all segments"),
               offsets=list(offsets), arms_offered=len(segs))
    print("emitted", n, "dots from", used, "segments at stride", stride, flush=True)

    # ---- holdout score of the exact delivered bytes --------------------
    per_fold = {}
    terms = []
    for fold in H58.all_folds():
        res, t = EH.evaluate(np.where(mask, 1.0, 0.0).astype(np.float32),
                             dict(region=np.ones(shape, bool), visible=fold.visible,
                                  masked_known=fold.known, truth=fold.withhold),
                             fold.valid, block_side=200)
        per_fold[fold.name] = res
        terms.append(t)
    stacked = {"delivered": np.vstack(terms)}
    # a paired bootstrap needs two arms; bootstrap against the empty emission
    empty = np.zeros(shape, bool)
    eterms = []
    for fold in H58.all_folds():
        _, t = EH.evaluate(np.where(empty, 1.0, 0.0).astype(np.float32),
                           dict(region=np.ones(shape, bool), visible=fold.visible,
                                masked_known=fold.known, truth=fold.withhold),
                           fold.valid, block_side=200)
        eterms.append(t)
    stacked["empty_control"] = np.vstack(eterms)
    summ = EH.pooled_summary(stacked, candidate="delivered", draws=1000)
    log["holdout"] = dict(summary=summ, per_fold={k: {kk: vv for kk, vv in v.items()
                                                      if kk in ("dti", "tp", "fp", "fn",
                                                                "n_truth", "n_emitted")}
                                                 for k, v in per_fold.items()})
    print("HOLDOUT-DTI", summ["scores"]["delivered"]["dti"],
          summ["scores"]["delivered"]["ci95"], flush=True)

    # ---- write with the shared writer ----------------------------------
    name = args.name or f"gems58-s4-ribbon-{arm.lower().replace('_','-')}-{n}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    note = args.note or (
        f"Ribbon lane: {arm} parallel dotted lines on catalogue-free Hessian ridges, "
        f"width from cross-fitted sigma; {n} dots at 1.0, all-finite zeros export.")
    note = " ".join(note.split())[:140]
    pred = np.where(mask, 1.0, 0.0).astype(np.float32)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tif = out_dir / f"{name}.tif"
    receipt = SW.write_submission(tif, pred, SAMPLE, fp, note=note, name=name,
                                  catalogue=cat,
                                  metadata=dict(lane="ribbon-width-vs-localisation-error",
                                                session=4, arm=arm, protocol="gems58-pooled-hide-v1",
                                                holdout_dti=summ["scores"]["delivered"]["dti"]))
    log["receipt"] = receipt
    log["stats"] = dot_stats(mask, fp, cat)
    print("wrote", tif, receipt["sha256"], receipt["bytes"], flush=True)

    # ---- independent re-validation of the bytes on disk ----------------
    log["validate"] = V57.validate(tif, fp, cat)
    log["format_report"] = G57.format_report(tif, SAMPLE, footprint=fp)

    # ---- uniqueness screen against the restored inventory --------------
    if not args.skip_uniqueness:
        with __import__("rasterio").open(tif) as src:
            arr = src.read(1)
        idx = json.loads((ROOT / "registry" / "registry_v3_index.json").read_text())
        rep = U57.compare_array_to_registry(arr, idx, fp,
                                            file_sha256=receipt["sha256"],
                                            progress=(lambda i, n_, r: None))
        keep = {k: v for k, v in rep.items() if k != "rows"}
        keep["rows"] = rep.get("rows", [])
        (OUT / "uniqueness.json").write_text(json.dumps(keep, indent=1, default=str))
        log["uniqueness"] = keep
        print("uniqueness", {k: keep.get(k) for k in
                             ("inventory_complete", "duplicate_count", "firings",
                              "worst_rho", "worst_overlap") if k in keep}, flush=True)

    log["seconds"] = round(time.time() - t0, 1)
    (OUT / "exp3_emission.json").write_text(json.dumps(log, indent=1, default=str))
    print("done", log["seconds"])


if __name__ == "__main__":
    main()
