#!/usr/bin/env python3
"""Session-6 lane runner: extended-evidence ridge field -> sigma -> patterns -> TIF.

Usage (from the repository root, with ``PYTHONPATH=src``)::

    python3 scripts/gems61_run.py field     # build/cache the extended ridge field
    python3 scripts/gems61_run.py sigma     # measure sigma(x) on the shared holdout
    python3 scripts/gems61_run.py pattern   # exact-metric pattern ladder + choices
    python3 scripts/gems61_run.py canary    # single-feature leakage canary
    python3 scripts/gems61_run.py emit      # emit + package the candidate GeoTIFF
    python3 scripts/gems61_run.py all

Every number written here is labelled in ``evidence/gems61/run_card.json``:
HOLDOUT-DTI (evaluator version, withheld positives, CI) or explicitly NOT MEASURED.
No projection is ever written as a score.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems61 import detect, lane, layers                                    # noqa: E402
from gems58w import holdout as HO                                          # noqa: E402
from gems58w.grid import catalogue, footprint                              # noqa: E402
from gems58w.paths import cache_dir                                        # noqa: E402

EV = ROOT / "evidence" / "gems61"
EV.mkdir(parents=True, exist_ok=True)

THRESHOLD = float(__import__("os").environ.get("GEMS61_THRESHOLD", "0.25"))
BUDGET = int(__import__("os").environ.get("GEMS61_BUDGET", "44000"))


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump(name: str, obj: dict) -> None:
    (EV / name).write_text(json.dumps(obj, indent=1, sort_keys=False), encoding="utf-8")
    print(f"wrote evidence/gems61/{name}")


def load(name: str) -> dict:
    p = EV / name
    return json.loads(p.read_text()) if p.exists() else {}


# ---------------------------------------------------------------------- field
def cmd_field(args) -> int:
    t0 = time.time()
    field = detect.build(force=args.force, workers=args.workers)
    fp = footprint()
    rows = layers.inventory()
    family_ridge: dict[str, int] = {}
    for key, mask in lane.class_masks(field, threshold=0.0).items():
        family_ridge[key[0]] = family_ridge.get(key[0], 0) + int(mask.sum())
    for r in rows:
        r["ridge_px_at_zero_threshold"] = family_ridge.get(r["family"], 0)
    cls = detect.classes(field)
    out = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        generated_utc=utc(),
        band_families={k: list(v) for k, v in layers.EXT_FAMILIES.items()},
        n_bands=len(layers.EXT_BANDS),
        n_classes=len(cls),
        classes=cls,
        cache=field["cache"],
        cached=field["cached"],
        ridge_px_total=int((field["code"] > 0).sum()),
        ridge_px_in_footprint=int(((field["code"] > 0) & fp).sum()),
        footprint_px=int(fp.sum()),
        layer_inventory=rows,
        ordinals_note=("the owner-published mirrors are 8-bit encodings whose physical scaling is not "
                       "published in this checkout; they are rank-transformed inside the footprint "
                       "and used ordinally only"),
        wall_seconds=round(time.time() - t0, 1),
    )
    dump("field.json", out)
    print(f"ridges {out['ridge_px_total']} px; {out['n_classes']} classes")
    return 0


# ---------------------------------------------------------------------- sigma
def cmd_sigma(args) -> int:
    t0 = time.time()
    field = detect.build(workers=1)
    folds = HO.folds()
    print(f"folds: {[f.name for f in folds]}")
    table = lane.sigma_table(field, folds)
    table.update(evidence_class="HOLDOUT-DTI-PROTOCOL-MEASUREMENT", generated_utc=utc(),
                 protocol="gems58-pooled-hide-v1",
                 note=("sigma is the RMS of min(d, 15 px) over withheld whole components matched by "
                       "the class (>= 60 % of pixels within 15 px); the value attached to a block is "
                       "the leave-one-block-out mean over the other three blocks"),
                 wall_seconds=round(time.time() - t0, 1))
    dump("sigma.json", table)
    ok = [r for r in table["rows"] if r["sigma_lobo_px"] is not None]
    print(f"{len(ok)}/{len(table['rows'])} (block,class) rows carry a LOBO sigma")
    return 0


# -------------------------------------------------------------------- pattern
def cmd_pattern(args) -> int:
    t0 = time.time()
    field = detect.build(workers=1)
    folds = HO.folds()
    table = lane.pattern_table(field, folds, threshold=THRESHOLD, dti0=args.dti0)
    choices = lane.choose_patterns(table)
    # agreement check between the fast scorer and the shared metric on one fold
    f0 = folds[0]
    m = detect.class_mask(field, family="magnetic", scale=1.5, sign=-1, threshold=THRESHOLD)
    dots = lane.pattern_dots(m & lane.fold_active(f0), field["ax"], field["ay"],
                             lane.PATTERNS["trio-3"])
    xcheck = lane.crosscheck_fast_vs_shared(dots, f0)
    sim = {}
    for c in choices["choices"]:
        rows = [r for r in table["rows"] if (r["family"], r["scale"], r["sign"])
                == (c["family"], c["scale"], c["sign"])]
        sim[f"{c['family']}|{c['scale']:g}|{c['sign']}"] = [
            dict(pattern=r["pattern"], U=r["U"], d_tp=r["d_tp"], d_fp=r["d_fp"], n_dots=r["n_dots"])
            for r in sorted(rows, key=lambda r: -r["U"])]
    out = dict(evidence_class="HOLDOUT-DTI", generated_utc=utc(),
               protocol=table["protocol"], evaluator=table["evaluator"],
               alpha=table["alpha"], beta=table["beta"], radius_px=table["radius_px"],
               threshold=THRESHOLD, dti0=table["dti0"], dti0_source=table["dti0_source"],
               base_dti=table["base_dti"], base_pool=table["base_pool"],
               base_dots_per_fold=table["base_dots_per_fold"],
               utility="U = (1 - 0.2*DTI0)*dTP - 0.2*DTI0*dFP (exact metric components)",
               choices=choices, simulated_gain_per_class=sim,
               crosscheck_fast_vs_shared=xcheck, wall_seconds=round(time.time() - t0, 1),
               note=("dTP/dFP are pooled over the four buffered hide-and-recover folds against "
                     "withheld whole catalogue components; this instrument measures recovery of "
                     "catalogue truth, not the organizer's new-fault truth (IR-58-02)"))
    dump("pattern.json", out)
    print(json.dumps({k: v["pattern"] for k, v in
                      {f"{c['family']}|{c['scale']:g}|{c['sign']}": c for c in choices["choices"]}.items()},
                     indent=0)[:1200])
    return 0


# --------------------------------------------------------------------- canary
def cmd_canary(args) -> int:
    """Single-feature AUC against the withheld catalogue (leakage canary, limit 0.90)."""
    t0 = time.time()
    rng = np.random.default_rng(61)
    folds = HO.folds()
    truth = np.zeros(footprint().shape, bool)
    active = np.zeros(footprint().shape, bool)
    for f in folds:
        truth |= lane.fold_truth(f)
        active |= lane.fold_active(f)
    rows = []
    for band in layers.EXT_BANDS:
        a = layers.band(band)
        v = a[truth & np.isfinite(a)]
        bg = np.flatnonzero(active & np.isfinite(a))
        if v.size < 50 or bg.size < 1000:
            continue
        take = rng.choice(bg, size=min(200000, bg.size), replace=False)
        b = a.ravel()[take]
        # rank-based AUC with ties handled by midrank
        allv = np.concatenate([v, b])
        r = np.argsort(np.argsort(allv, kind="stable"), kind="stable").astype(np.float64)
        n1, n0 = v.size, b.size
        auc = (r[:n1].sum() - n1 * (n1 - 1) / 2.0) / (n1 * n0)
        auc = max(auc, 1.0 - auc)  # two-sided: either polarity can carry information
        rows.append(dict(feature=band, family=layers.family_of(band), auc=float(auc),
                         n_truth=int(n1), n_background=int(n0),
                         leaks=bool(auc > 0.90)))
    worst = max((r["auc"] for r in rows), default=None)
    out = dict(evidence_class="HOLDOUT-DTI", generated_utc=utc(),
               protocol="gems58-pooled-hide-v1", limit=0.90, worst_auc=worst,
               n_features=len(rows), n_leaking=sum(1 for r in rows if r["leaks"]),
               rows=sorted(rows, key=lambda r: -r["auc"]),
               note=("two-sided AUC of a single extended band against the pooled withheld catalogue "
                     "truth, background subsampled to 200k pixels; a feature above 0.90 is leakage "
                     "until explained"),
               wall_seconds=round(time.time() - t0, 1))
    dump("canary.json", out)
    print(f"worst feature AUC {worst}")
    return 0


# ----------------------------------------------------------------------- emit
def cmd_emit(args) -> int:
    t0 = time.time()
    from gems57.submission_writer import write_submission
    from gems57 import validate as V
    from gems57.grid import load_grid

    field = detect.build(workers=1)
    choices = load("pattern.json")["choices"]
    dots, mag, info = lane.emit_dots(field, choices, threshold=THRESHOLD, budget=BUDGET)
    print(f"emitted {dots.shape[0]} dots before uniqueness repair")

    # --- uniqueness repair against witnesses fetched for this session (if present)
    wdir = Path(os.environ.get("GEMS61_WITNESSES", Path.home() / ".cache" / "gems" / "registry_witnesses"))
    index = json.loads((ROOT / "evidence" / "registry_scan_index.json").read_text())
    witnesses = []
    if wdir.exists() and args.repair:
        import rasterio
        by_sha = {e["sha256"]: e for e in index}
        cand = []
        for p in sorted(wdir.glob("*.tif")):
            sha = p.stem
            e = by_sha.get(sha)
            if e is None:
                continue
            try:
                with rasterio.open(p) as src:
                    a = src.read(1)
            except Exception:
                continue
            if a.shape != footprint().shape:
                continue
            sup = np.isfinite(a) & (a > 0) if np.isnan(a).any() else (a > 0)
            fp = footprint()
            n = int(fp.sum())
            if not sup.any():
                continue
            from gems57.uniqueness import chance_expected_overlap
            E = float(chance_expected_overlap(sup, fp))
            cand.append(dict(name=f"{e['repo_first']}:{e.get('submission') or sha[:12]}",
                             support=sup, chance_expected_overlap=E, sha256=sha))
        # only informative witnesses can steer the field (E < 0.99)
        witnesses = sorted([w for w in cand if w["chance_expected_overlap"] < 0.99],
                           key=lambda w: -w["chance_expected_overlap"])[: args.max_witnesses]
        print(f"repairing against {len(witnesses)} informative witnesses "
              f"(of {len(cand)} cached rasters)")
    rep = lane.uniqueness_repair(dots, mag, witnesses, overlap_limit=args.overlap_limit,
                                 margin=args.margin)
    keep = rep["keep"]
    dots, mag = dots[keep], mag[keep]
    print(f"after repair: {dots.shape[0]} dots (dropped {rep['n_dropped']})")

    grid = load_grid(ROOT / "data" / "bridge")
    pred = np.zeros(grid.footprint.shape, np.float32)
    pred[dots[:, 0], dots[:, 1]] = 1.0
    pred = np.where(grid.footprint, pred, np.float32("nan"))

    name = args.name or f"gems61-sigma-ribbon-{dots.shape[0]}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    note = (args.note or
            "58GEMSDOE gems61 lane: sigma-matched dotted ribbons on organiser stack + "
            "GeoDAWN radiometric/lidar/DEM mirrors; 0 dots on catalogue")[:140]
    out_tif = ROOT / "docs" / "downloads" / f"{name}.tif"
    receipt = write_submission(out_tif, pred, ROOT / "data" / "bridge" / "sample_submission.tif",
                               grid.footprint, note=note, name=name,
                               catalogue=grid.catalogue)
    val = V.validate(out_tif, footprint=grid.footprint, catalogue=grid.catalogue)

    # --- shared-evaluator holdout numbers for the emitted dots
    folds = HO.folds()
    dist = {f.name: lane.fold_truth_distance(f) for f in folds}
    per_fold, tp, fp_, fn, ntruth = {}, 0.0, 0.0, 0.0, 0
    for f in folds:
        r = lane.score_dots(dots, f, dist[f.name])
        per_fold[f.name] = r
        tp += r["tp"]; fp_ += r["fp"]; fn += r["fn"]; ntruth += r["n_truth"]
    dti = tp / (tp + 0.2 * fp_ + 0.8 * fn + 1e-12)
    xcheck = {}
    for f in folds[:1]:
        xcheck = lane.crosscheck_fast_vs_shared(dots, f)

    emission = dict(evidence_class="HOLDOUT-DTI", generated_utc=utc(),
                    file=str(out_tif.relative_to(ROOT)), name=name, note=note,
                    sha256=receipt.get("sha256") if isinstance(receipt, dict) else None,
                    n_dots=int(dots.shape[0]), threshold=THRESHOLD, budget=BUDGET,
                    emission_info=info, uniqueness_repair=dict(
                        n_dropped=rep["n_dropped"],
                        rows=rep["rows"],
                        n_witnesses=len(witnesses),
                        overlap_limit=args.overlap_limit, margin=args.margin),
                    validator=dict(passed=bool(all(v.get("ok") for v in val["checks"].values())),
                                   checks={k: dict(ok=bool(v.get("ok")), detail=v.get("detail"))
                                           for k, v in val["checks"].items()},
                                   n_positives=int(val.get("n_positives", dots.shape[0]))),
                    holdout_dti=dict(pooled=float(dti), per_fold=per_fold,
                                     n_withheld_positives=int(ntruth),
                                     protocol="gems58-pooled-hide-v1",
                                     evaluator="gems58w.metric/v1 (shared gems57 arithmetic)",
                                     fast_vs_shared=xcheck),
                    audit=lane.audit_dots(dots, mag),
                    wall_seconds=round(time.time() - t0, 1))
    dump("emission.json", emission)
    np.save(cache_dir() / "gems61_dots.npy", dots)
    print(f"wrote {out_tif.name}: sha256 {emission['sha256']}; validator "
          f"{sum(1 for v in val['checks'].values() if v.get('ok'))}/{len(val['checks'])}; "
          f"holdout DTI {dti:.6f} on {ntruth} withheld positives")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("field"); p.add_argument("--force", action="store_true")
    p.add_argument("--workers", type=int, default=1); p.set_defaults(func=cmd_field)
    p = sub.add_parser("sigma"); p.set_defaults(func=cmd_sigma)
    p = sub.add_parser("pattern"); p.add_argument("--dti0", type=float, default=None)
    p.set_defaults(func=cmd_pattern)
    p = sub.add_parser("canary"); p.set_defaults(func=cmd_canary)
    p = sub.add_parser("emit")
    p.add_argument("--repair", action="store_true")
    p.add_argument("--max-witnesses", type=int, default=40)
    p.add_argument("--overlap-limit", type=float, default=0.70)
    p.add_argument("--margin", type=float, default=0.05)
    p.add_argument("--name", default=None)
    p.add_argument("--note", default=None)
    p.set_defaults(func=cmd_emit)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
