#!/usr/bin/env python3
"""Build, screen, validate and publish the GEMS58 ribbon-lane submission.

Pipeline (one run, no manual steps):

1. read the cached multi-family ridge field (``extract.build``);
2. keep every ridge segment and expand it into a **per-segment parallel dotted
   ribbon**: sigma(x) is looked up for the segment's (band family, ridge sign,
   ridge scale, data block) from the holdout-measured table
   (``gems58w.sigma``), and the number of lines and their offsets are chosen by
   ``gems58w.allocation.plan`` on the kernel-radius lattice so that the marginal
   credit of the last pair still exceeds ``alpha * DTI0`` --- a single tight
   line where sigma < 0.5 px, a 3-line ribbon at 0, +-3 px where sigma is the
   measured 1.2-1.8 px, and wider ribbons beyond that;
3. require every dot to be at least ``CAT_MARGIN`` px from the official
   catalogue: dots on a mapped fault are inert (the organizer masks them) and
   dots beside one are wasted mass;
4. greedy-keep the strongest **isolated** dots (no two 8-adjacent) up to the
   38,000-dot budget that the three best measured live files used;
5. write the GeoTIFF, run the 15 local portal checks, the uniqueness screen
   against every registry raster, and the exact-metric holdout read-out;
6. publish the downloadable TIFF + single-file ZIP and a machine-readable run
   card into ``docs/downloads/`` and ``evidence/``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... python3 scripts/ribbon_build_submission.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import allocation, extract, grid, holdout, metric, submission, uniqueness  # noqa: E402
from gems58w import features as FEAT  # noqa: E402
from gems58w import sigma as SIGMA  # noqa: E402
from gems58w.paths import EVIDENCE, REGISTRY, downloads_dir, evidence_dir  # noqa: E402

NAME = "gems58-adaptive-ribbon-38000-20261011T000000Z"
BUDGET = 38000
CAT_MARGIN = 3.0
WIDTH = 3
LINE_STEP = 3.0
MIN_SEP = 1
THRESHOLD = 0.6


def ribbon_support(field, segs, width=WIDTH, step=LINE_STEP) -> np.ndarray:
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    for s in segs:
        idx = s["idx"]
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        for j in range(width):
            o = j * step
            for sgn in ((1,) if o == 0 else (1, -1)):
                rr = np.rint(idx[:, 0] + sgn * o * ay).astype(int)
                cc = np.rint(idx[:, 1] + sgn * o * ax).astype(int)
                ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
                mask[rr[ok], cc[ok]] = True
    return mask


def ribbon_support_adaptive(field, segs, table: dict, dti0: float, max_k: int = 3,
                            shift_of=None, along_spacing: int = 1):
    """Per-segment ribbon: sigma -> (n_lines, offsets) via allocation.plan.

    ``shift_of(segment) -> mu`` optionally translates the *whole* ribbon across
    strike by the stratum's measured signed bias ``mu`` (px), so the emitted
    lines sit at ``mu + k*R`` instead of ``k*R``.  ``shift_of=None`` reproduces
    the original symmetric emission exactly.

    Returns ``(mask, histogram_of_line_counts, rows)`` where ``rows`` records the
    (block, family, sign, scale, sigma, stratum-used, n_lines, offsets) decision
    for every segment, so the run card can publish the plan that was executed.
    """
    shape = field["mag"].shape
    mask = np.zeros(shape, bool)
    hist: dict[int, int] = {}
    rows = []
    for s in segs:
        idx = s["idx"]
        if along_spacing > 1:
            axis = int(np.argmax(np.var(idx.astype(float), axis=0)))
            idx = idx[np.argsort(idx[:, axis])][::along_spacing]
        code = max(s["codes"], key=lambda c: c["scale"]) if s["codes"] else {}
        band = code.get("band", "?")
        family = next((f for f, bs in FEAT.FAMILIES.items() if band in bs), "other")
        scale = float(code.get("scale", 0.0))
        sign = int(code.get("sign", 0))
        blk = holdout.block_of(s["idx"].mean(axis=0))
        sig, which = SIGMA.sigma_for(family, scale, sign, blk, table)
        mu = float(shift_of(s)) if shift_of is not None else 0.0
        plan = allocation.plan(sig, dti0, max_k=max_k)
        hist[plan.n_lines] = hist.get(plan.n_lines, 0) + 1
        rows.append(dict(block=blk, family=family, sign=sign, scale=scale,
                         sigma_px=sig, shift_px=mu, stratum=which, n_lines=plan.n_lines,
                         offsets_px=[o + mu for o in plan.offsets], segment_px=int(s["size"])))
        ax = field["ax"][idx[:, 0], idx[:, 1]]
        ay = field["ay"][idx[:, 0], idx[:, 1]]
        for o in plan.offsets:
            o = o + mu
            if abs(o) < 1e-9:
                rr, cc = idx[:, 0], idx[:, 1]
            else:
                rr = np.rint(idx[:, 0] + o * ay).astype(int)
                cc = np.rint(idx[:, 1] + o * ax).astype(int)
            ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
            mask[rr[ok], cc[ok]] = True
    return mask, hist, rows


def shift_lookup(table: dict, cap_px: float = 3.0):
    """``shift_of(segment)`` from the signed-sigma table, with the same fallback chain.

    ``table`` is the ``by_family_sign`` mapping of ``evidence/ribbon_v2/signed_sigma.json``
    entries (each with a ``mu_mean``).  The shift is capped at ``cap_px`` so a
    noisy stratum cannot fling the ribbon outside the kernel.
    """
    def mu_for(family: str, sign: int) -> float:
        for key in (f"{family}/{sign}", f"{family}/1", f"{family}/-1"):
            rec = table.get(key)
            if rec and abs(float(rec["mu_mean"])) >= 0.0:
                return float(np.clip(rec["mu_mean"], -cap_px, cap_px))
        return 0.0

    def shift_of(s) -> float:
        code = max(s["codes"], key=lambda c: c["scale"]) if s["codes"] else {}
        band = code.get("band", "?")
        family = next((f for f, bs in FEAT.FAMILIES.items() if band in bs), "other")
        return mu_for(family, int(code.get("sign", 0)))

    return shift_of


def greedy_isolated(mask: np.ndarray, rank: np.ndarray, budget: int, min_sep: int = 1):
    from scipy.ndimage import maximum_filter

    m = mask.copy()
    keep = np.zeros_like(m)
    while int(keep.sum()) < budget and m.any():
        cand = m & (rank >= maximum_filter(np.where(m, rank, -np.inf), 3))
        if not cand.any():
            break
        new = cand & ~maximum_filter(keep, 2 * min_sep + 1)
        if not new.any():
            break
        take = np.argwhere(new)
        room = budget - int(keep.sum())
        if take.shape[0] > room:
            vals = rank[take[:, 0], take[:, 1]]
            take = take[np.argsort(-vals, kind="stable")][:room]
        keep[take[:, 0], take[:, 1]] = True
        m &= ~maximum_filter(keep, 2 * min_sep + 1)
    return keep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--width", type=int, default=0,
                    help="0 = adaptive per-segment ribbon (default); >0 = fixed n-line ribbon")
    ap.add_argument("--dti0", type=float, default=0.3195,
                    help="reference index for the marginal-inclusion rule")
    ap.add_argument("--cat-margin", type=float, default=CAT_MARGIN)
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    ap.add_argument("--name", default=NAME)
    ap.add_argument("--shift-json", default=None,
                    help="evidence/ribbon_v2/signed_sigma.json: translate each ribbon by "
                         "the stratum's measured signed bias mu")
    ap.add_argument("--registry-dir", default=None,
                    help="directory of prior rasters for the uniqueness screen "
                         "(default: the 19 in-repo cop_ies in data/registry/rasters)")
    ap.add_argument("--along-spacing", type=int, default=1,
                    help="keep every Nth pixel along strike (dotted emission)")
    ap.add_argument("--rho-subsample", type=int, default=None,
                    help="stride for the registry rank correlation (large inventories; "
                         "None = exact full-field Spearman)")
    args = ap.parse_args()

    t0 = time.time()
    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=8)
    cat_d = distance_transform_edt(~grid.catalogue()).astype(np.float32)

    # ---- sigma(x) table, measured on the hide-and-recover holdout ----
    items = []
    for f in holdout.all_folds():
        items.extend(SIGMA.measure(field, segs, f))
    table = SIGMA.sigma_table(items)
    print(f"[sigma] matched {table['n_matched']} withheld components; pooled median "
          f"{(table['pooled'] or {}).get('median', float('nan')):.2f} px "
          f"(rms {(table['pooled'] or {}).get('rms', float('nan')):.2f}); strata "
          f"{sorted(table['by_type_scale'])[:6]}...", flush=True)

    if args.width > 0:
        raw = ribbon_support(field, segs, args.width)
        hist, rows = {args.width: len(segs)}, []
        print(f"[plan] fixed {args.width}-line ribbon over {len(segs)} segments", flush=True)
    else:
        shift_of = None
        if args.shift_json:
            sj = json.loads(Path(args.shift_json).read_text())
            shift_of = shift_lookup(sj["by_family_sign"])
            print(f"[plan] signed shift table loaded: "
                  f"{ {k: round(v['mu_mean'], 3) for k, v in sj['by_family_sign'].items()} }",
                  flush=True)
        raw, hist, rows = ribbon_support_adaptive(field, segs, table, args.dti0,
                                                  shift_of=shift_of,
                                                  along_spacing=args.along_spacing)
        print(f"[plan] adaptive per-segment ribbon: line-count histogram {hist} "
              f"over {len(segs)} segments", flush=True)
        used = {}
        for r in rows:
            used[r["stratum"]] = used.get(r["stratum"], 0) + 1
        print(f"[plan] sigma strata used: {used}", flush=True)
    n_raw = int(raw.sum())
    screened = raw & (cat_d >= args.cat_margin) & grid.footprint()
    n_screened = int(screened.sum())
    dots = greedy_isolated(screened, field["mag"], args.budget, MIN_SEP)
    n_dots = int(dots.sum())
    print(f"[build] raw ribbon {n_raw} | after >= {args.cat_margin:g}px catalogue screen "
          f"{n_screened} | kept {n_dots}", flush=True)

    tif = downloads_dir() / f"{args.name}.tif"
    submission.write(tif, dots)
    val = submission.validate(tif)
    print(f"[validate] passed={val['passed']} n_positives={val['n_positives']} "
          f"sha256={val['sha256'][:16]}...", flush=True)
    for k, v in val["checks"].items():
        if not v["ok"]:
            print("   FAIL", k, v["detail"])

    reg_dir = Path(args.registry_dir) if args.registry_dir else REGISTRY
    screens, usum = uniqueness.screen_against(dots, reg_dir,
                                              rho_subsample=args.rho_subsample)
    print(f"[unique] checked {usum['n_checked']} rasters | worst rho {usum['worst_rho']:.4f} "
          f"({usum['worst_rho_name']}) | worst forward overlap "
          f"{usum['worst_forward_overlap']:.4f} ({usum['worst_forward_overlap_name']}) | "
          f"triggers {usum['n_triggers']} | dense priors {usum['n_dense_priors']}",
          flush=True)

    # holdout read-out (evidence, never a projection): exact metric, 4 folds
    folds = holdout.all_folds()
    per_fold, agg = {}, dict(tp=0.0, fp=0.0, fn=0.0, n_truth=0, n_dots=0)
    for f in folds:
        r = metric.dti_binary(dots, f.withhold, valid=f.valid, known=f.known)
        per_fold[f.name] = r.dti
        for k in ("tp", "fp", "fn", "n_truth"):
            agg[k] += getattr(r, k)
        agg["n_dots"] += int((dots & f.valid & ~f.known).sum())
    den = agg["tp"] + metric.ALPHA * agg["fp"] + metric.BETA * agg["fn"] + metric.EPS
    pooled = float(agg["tp"] / den)
    print(f"[holdout] HOLDOUT-DTI {pooled:.6f} on {agg['n_truth']} withheld positives; "
          f"folds {per_fold}", flush=True)

    # catalogue-distance profile of the delivered dots (live-evidence covariate)
    v = cat_d[dots]
    prof = dict(median_px=float(np.median(v)), mean_px=float(v.mean()),
                frac_le3px=float((v <= 3).mean()), frac_le10px=float((v <= 10).mean()),
                on_catalogue=int((v <= 0.001).sum()))

    widths = sorted(k for k in hist if isinstance(k, int))
    off_px = sorted({abs(o) for r in rows for o in r.get("offsets_px", [])} if rows else set())
    max_off = int(max(off_px)) if off_px else 0
    spokes = ", ".join(f"+-{o * 100:g} m" for o in off_px if o > 0)
    note = submission.note(
        "Ribbon lane: per-segment dotted ribbons ("
        + ("/".join(str(w) for w in widths) if widths else "?")
        + f" lines at 0{', ' + spokes if spokes else ''}) on off-catalogue ridge detections; "
        + "38k isolated dots.")
    card = dict(
        name=args.name,
        hypothesis="H58-R ribbon lane: emission width matched to the measured localisation error",
        mechanism=("the scoring kernel is isotropic, so a detected ridge that is off by "
                   "sigma covers truth only within 3 px of the ridge; three parallel "
                   "dotted lines at the kernel radius +-3 px convert a 1.68 px RMS "
                   "localisation error into kernel credit"),
        named_non_fault_process=("flight-line levelling and draped-sensor artefacts in the "
                                 "aeromagnetic grid produce lineaments parallel to survey "
                                 "flight lines that no fault occupies; dense volcanic and "
                                 "alluvial contacts in the detrended DEM produce scarp-shaped "
                                 "curvature that is not tectonic"),
        holdout_dti=pooled, holdout_dti_evaluator=metric.EVALUATOR_VERSION,
        holdout_dti_protocol=holdout.PROTOCOL,
        holdout_dti_withheld_positives=int(agg["n_truth"]),
        holdout_dti_per_fold=per_fold,
        holdout_dti_ci=[None, None],
        holdout_dti_ci_note=("not reported: the four spatial blocks give only 4 paired "
                             "observations, so a bootstrap interval over blocks is not "
                             "informative; the equal-budget width test reports the "
                             "block-paired bootstrap instead"),
        registry=usum,
        registry_rows=[s.as_dict() for s in screens],
        raster_sha256=val["sha256"], raster_bytes=val["bytes"],
        validator=dict(passed=val["passed"], n_positives=val["n_positives"],
                       checks=val["checks"]),
        catalogue_distance_profile=prof,
        sigma_table={k: v for k, v in table.items() if k != "by_type_scale"},
        plan_histogram={str(k): v for k, v in hist.items()},
        plan_rows=rows[:400],
        geometry=dict(width=("adaptive" if args.width == 0 else args.width),
                      line_step_px=LINE_STEP, dti0=args.dti0,
                      min_separation_px=MIN_SEP + 1, budget=args.budget,
                      catalogue_margin_px=args.cat_margin, threshold=args.threshold,
                      n_ridge_segments=len(segs), n_raw_ribbon=n_raw,
                      n_after_catalogue_screen=n_screened),
        submission_note=note, submission_note_chars=len(note),
        verdict="candidate — download OK, submit decision belongs to the slot selector",
        wall_seconds=round(time.time() - t0, 2),
    )

    zp = downloads_dir() / f"{args.name}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zp) as z:
        assert z.namelist() == [tif.name], z.namelist()
        card["zip_sha256"] = submission.sha256(zp)
        card["zip_contains"] = z.namelist()

    (evidence_dir() / "run_card.json").write_text(json.dumps(card, indent=1, default=float))
    (EVIDENCE / "uniqueness.json").write_text(json.dumps(
        dict(summary=usum, rows=[s.as_dict() for s in screens]), indent=1, default=float))
    (downloads_dir() / f"{args.name}.checks.json").write_text(json.dumps(
        dict(validator=val, uniqueness_summary=usum, holdout=dict(pooled=pooled, per_fold=per_fold),
             catalogue_distance_profile=prof, geometry=card["geometry"]), indent=1, default=float))
    print("wrote", tif, "\nwrote", zp, "\nwrote evidence/run_card.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
