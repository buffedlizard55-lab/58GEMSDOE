#!/usr/bin/env python3
"""EXP-3: emit the gems60 candidate, validate it locally, screen it, write receipts.

Pipeline (all shared tools; nothing re-implemented):

1. cached convergence field (``gems60.convergence``, built by ``gems60_build_field.py``)
2. skeletonise by across-strike non-maximum suppression (``gems60.dots.skeleton``)
3. replicate the skeleton at the *measured* localization error
   (``gems60.dots.ribbon``, offsets = +-3 px = the 300 m kernel radius)
4. belief surface + the shared exact-metric allocator
   (``gems57.emit.allocate_by_marginal_bar``)
5. shared fail-closed writer (``gems57.submission_writer.write_submission``)
6. uniqueness screen against every witness raster available in-repo
   (``gems57.uniqueness`` helpers)

Usage:
    PYTHONPATH=src python3 scripts/gems60_emit.py --name <name> --note "<note>"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.emit import allocate_patient                         # noqa: E402
from gems57.grid import load_grid                                   # noqa: E402
from gems57.metric import kernel                                    # noqa: E402
from gems57.submission_writer import write_submission               # noqa: E402
from gems57.uniqueness import _dots, _near, dot_overlap, surface_rho  # noqa: E402
from gems60 import convergence as C                                 # noqa: E402
from gems60 import dots as D                                        # noqa: E402

CACHE = Path.home() / ".cache" / "gems" / "gems60_convergence.npz"
EVID = ROOT / "evidence" / "gems60"
WITNESS_DIR = ROOT / "data" / "registry" / "rasters"
#: owner-reported hidden-truth size (sibling H28 truth model, registry brief).
#: It only sets the allocator's bar, and the sensitivity is reported.
K_TRUTH_DEFAULT = 12691


def screen(candidate_dots: np.ndarray, surface: np.ndarray, footprint: np.ndarray,
           witnesses: list[Path]) -> dict:
    rows = []
    for w in sorted(witnesses):
        with rasterio.open(w) as src:
            a = src.read(1).astype(np.float32)
        if a.shape != candidate_dots.shape:
            rows.append(dict(witness=w.name, error="grid mismatch"))
            continue
        theirs = _dots(a)
        n_t = int(theirs.sum())
        if n_t == 0:
            rows.append(dict(witness=w.name, their_dots=0, forward_overlap=None,
                             reverse_overlap=None, jaccard=None, rho=None))
            continue
        fwd = dot_overlap(candidate_dots, theirs)          # my dots near theirs
        rev = dot_overlap(theirs, candidate_dots)          # their dots near mine
        u = int((candidate_dots | theirs).sum())
        jac = float((candidate_dots & theirs).sum() / u) if u else 0.0
        rho = surface_rho(surface, a, footprint)
        rows.append(dict(witness=w.name, their_dots=n_t,
                         forward_overlap=float(fwd), reverse_overlap=float(rev),
                         jaccard=jac,
                         rho=float(rho["spearman_full_footprint"]),
                         rho_dot_union=float(rho["spearman_on_dot_union"]),
                         dilated_frac=float(_near(theirs).mean())))
        del a
    fwd_ok = [r for r in rows if r.get("forward_overlap") is not None]
    worst_fwd = max(fwd_ok, key=lambda r: r["forward_overlap"]) if fwd_ok else None
    worst_rho = max([r for r in rows if r.get("rho") is not None],
                    key=lambda r: r["rho"], default=None)
    worst_rev = max(fwd_ok, key=lambda r: r["reverse_overlap"]) if fwd_ok else None
    return dict(n_witnesses=len(rows), rows=rows,
                worst_forward_overlap=worst_fwd, worst_reverse_overlap=worst_rev,
                worst_rho=worst_rho,
                rho_limit=0.90, overlap_limit=0.70,
                forward_firings=[r["witness"] for r in fwd_ok if r["forward_overlap"] > 0.70],
                rho_firings=[r["witness"] for r in fwd_ok if r.get("rho", 0) > 0.90])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    ap.add_argument("--k-truth", type=float, default=K_TRUTH_DEFAULT)
    ap.add_argument("--max-dots", type=int, default=40000)
    ap.add_argument("--min-families", type=int, default=2)
    ap.add_argument("--sigma-px", type=float, default=3.0)
    ap.add_argument("--sharpen", type=float, default=4.0)
    ap.add_argument("--agree-bonus", type=float, default=0.5,
                    help="ranking bonus per extra agreeing family (rank only, not a gate)")
    ap.add_argument("--min-sep-px", type=float, default=3.0,
                    help="minimum dot separation (the 300 m kernel radius)")
    args = ap.parse_args()
    if len(args.note) > 140:
        raise SystemExit(f"note is {len(args.note)} chars; the writer caps it at 140")

    t0 = time.time()
    grid = load_grid(ROOT / "data" / "bridge")
    fp, cat = grid.footprint, grid.catalogue
    conv = C.load(CACHE)
    print(f"grid    : {grid.shape} footprint {int(fp.sum())} catalogue {int(cat.sum())}")

    valid = fp & (conv.score >= args.min_families)
    skel = D.skeleton(conv.strength, conv.ax, conv.ay, valid)
    print(f"skeleton: min_families>={args.min_families} -> {int(skel.sum())} cells "
          f"({100.0 * skel.sum() / max(1, int(valid.sum())):.1f}% of the eligible surface)")

    # across-strike direction on the skeleton (for the ribbon translation)
    ax = np.where(skel, conv.ax, 0.0).astype(np.float32)
    ay = np.where(skel, conv.ay, 0.0).astype(np.float32)
    rib, offsets = D.ribbon(skel, ax, ay, args.sigma_px)
    print(f"ribbon  : sigma={args.sigma_px} px -> offsets {offsets} -> {int(rib.sum())} cells")

    p = D.belief(rib, conv.strength, sharpen=args.sharpen)
    # corroboration preference: raise the *rank* of cells where more independent
    # families agree, without turning agreement into a hard gate (the EXP-1
    # instrument did not show the gate by itself beating a single family).
    bonus = 1.0 + args.agree_bonus * np.clip(conv.score - 1.0, 0.0, 3.0)
    p = np.clip(p * bonus, 0.0, 1.0).astype(np.float32)
    # the lane's dotted lattice: min separation = the kernel radius
    lattice = D.thin(p > 0, p, min_sep_px=args.min_sep_px)
    print(f"lattice : min separation {args.min_sep_px} px -> {int(lattice.sum())} candidates")
    # mass must stay inside the study footprint and off the mapped catalogue
    allowed = lattice & fp & ~cat
    print(f"allowed : {int(allowed.sum())} cells "
          f"(catalogue pixels removed: {int((fp & cat).sum())})")

    # allocate_patient is the shared greedy that only stops after `patience`
    # consecutive rejections -- allocate_by_marginal_bar breaks at the first
    # rejection, which on this surface stopped at 460 dots (the documented
    # failure mode in its own docstring, measured again here).
    alloc = allocate_patient(p, allowed, args.k_truth, max_dots=args.max_dots,
                             candidate_cap=600_000, patience=100_000)
    emitted = alloc.emitted
    n = int(emitted.sum())
    print(f"alloc   : {n} dots (asked <= {args.max_dots}); surrogate T={alloc.expected_covered_credit:.1f} "
          f"M={alloc.expected_self_credit:.1f} surrogate_dti={alloc.surrogate_dti:.4f}")

    # ---- geometry receipts, comparable with the family's measured optimum ----
    ys, xs = np.nonzero(emitted)
    from scipy.spatial import cKDTree
    pts = np.c_[ys, xs]
    idx = np.arange(ys.size) if ys.size <= 60000 else np.random.default_rng(0).choice(ys.size, 60000, replace=False)
    t = cKDTree(pts)
    dd, _ = t.query(pts[idx], k=2)
    nn = dd[:, 1]
    dc = ndi.distance_transform_edt(~cat)
    dcat = dc[ys[idx], xs[idx]]
    geom = dict(n_dots=n, nn_median_px=float(np.median(nn)), nn_p10_px=float(np.percentile(nn, 10)),
                nn_p90_px=float(np.percentile(nn, 90)),
                dist_catalogue_median_px=float(np.median(dcat)),
                dist_catalogue_p10_px=float(np.percentile(dcat, 10)),
                on_catalogue_px=int((cat[ys, xs]).sum()),
                on_2families_frac=float((conv.score[ys, xs] >= 2).mean()),
                on_3families_frac=float((conv.score[ys, xs] >= 3).mean()),
                mean_families=float(conv.score[ys, xs].mean()))
    print(f"geometry: nn median {geom['nn_median_px']:.3f} px, "
          f"dist-to-catalogue median {geom['dist_catalogue_median_px']:.2f} px, "
          f"on-catalogue {geom['on_catalogue_px']}, "
          f"mean families {geom['mean_families']:.2f}")

    # ---- write the deliverable through the shared fail-closed writer ----
    out_tif = Path(args.out) / f"{args.name}.tif"
    pred = emitted.astype(np.float32)      # exactly 1.0 where emitted, else 0.0
    if not np.array_equal(np.unique(pred), np.array([0.0, 1.0], np.float32)):
        raise AssertionError("emission must be binary 0/1")
    receipt = write_submission(out_tif, pred, ROOT / "data" / "official" / "sample_submission.tif",
                               fp, note=args.note, name=args.name, catalogue=cat,
                               metadata=dict(lane="gems60 cross-family convergence",
                                             sigma_px=args.sigma_px, offsets=offsets,
                                             k_truth=args.k_truth, max_dots=args.max_dots,
                                             min_families=args.min_families,
                                             agree_bonus=args.agree_bonus,
                                             min_sep_px=args.min_sep_px))
    print(f"wrote   : {out_tif} sha256 {receipt['sha256']} ({receipt['bytes']} B)")

    # ---- uniqueness screen over every witness available in-repo ----
    witnesses = sorted(WITNESS_DIR.glob("*.tif"))
    scr = screen(emitted, conv.strength, fp, witnesses)
    print(f"screen  : {scr['n_witnesses']} witnesses")
    if scr["worst_forward_overlap"]:
        w = scr["worst_forward_overlap"]
        print(f"  worst forward 3-px overlap {w['forward_overlap']:.4f} vs {w['witness']} (limit 0.70)")
    if scr["worst_rho"]:
        w = scr["worst_rho"]
        print(f"  worst rank correlation      {w['rho']:.4f} vs {w['witness']} (limit 0.90)")
    if scr["worst_reverse_overlap"]:
        w = scr["worst_reverse_overlap"]
        print(f"  worst reverse 3-px overlap {w['reverse_overlap']:.4f} vs {w['witness']}")
    print(f"  firings: overlap {len(scr['forward_firings'])}  rho {len(scr['rho_firings'])}")

    evidence = dict(
        evidence_class="LOCAL-FORMAT-AND-UNIQUENESS",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        name=args.name, note=args.note, note_chars=len(args.note),
        file=str(out_tif.relative_to(ROOT)), sha256=receipt["sha256"], bytes=receipt["bytes"],
        zip=receipt["zip_file"], zip_sha256=receipt["zip_sha256"],
        geometry=geom, offsets=list(offsets), k_truth=args.k_truth,
        allocation=dict(allocator="gems57.emit.allocate_patient", n_dots=n,
                        surrogate_dti=alloc.surrogate_dti,
                        surrogate_T=alloc.expected_covered_credit,
                        surrogate_M=alloc.expected_self_credit, rounds=alloc.rounds),
        validator=receipt["validator"], template_report=receipt["template_report"],
        screen=scr,
        inventory=dict(in_repo_witnesses=len(witnesses),
                       recorded_full_inventory=int(json.loads(
                           (ROOT / "registry" / "registry_merged.json").read_text())["counts"].get("rasters", 0))
                       if (ROOT / "registry" / "registry_merged.json").exists() else None,
                       note=("witness blobs are not committed; only the in-repo witness set is "
                             "byte-available in this sandbox")),
    )
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / f"{args.name}.screen.json").write_text(json.dumps(evidence, indent=1, default=str) + "\n")
    print(f"evidence: {EVID / (args.name + '.screen.json')}")
    print(f"elapsed : {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
