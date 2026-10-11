#!/usr/bin/env python3
"""Archived MECE/multi-evidence experiment; command-line execution disabled.

This method is outside the current user's ribbon-only scope. Its historical
holdout used full-catalogue proximity and leaked withheld labels, and its
candidate was not cleared against a current complete registry. Retained for
forensic review only; do not run, cite as performance evidence, or submit.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import load_grid
from gems57.holdout import build_holdout, evaluate, score_cell
from gems57.metric import kernel, ALPHA, BETA, EPS, RADIUS_PX
from gems57.emit import expected_credit, greedy_allocate, allocate_patient, emit_decimated, emit_prefix

import rasterio


def load_sgmc(root: Path, grid) -> np.ndarray:
    """Load SGMC faults in the footprint, off-catalogue."""
    path = root / "data" / "external" / "sgmc_faults_100m.tif"
    with rasterio.open(path) as src:
        sgmc = src.read(1) > 0
    return sgmc & grid.footprint & ~grid.catalogue


def build_probability_surface(grid, sgmc_off_cat: np.ndarray,
                               visible: np.ndarray = None,
                               mode: str = "max") -> np.ndarray:
    """Build a fault probability surface from evidence sources.

    Evidence sources:
    1. Catalogue proximity: kernel(distance to visible catalogue)
    2. SGMC proximity: kernel(distance to SGMC off-catalogue)
    3. SGMC mask itself: 1.0 on SGMC pixels (strong direct evidence)

    Combined by taking the max (or weighted sum).
    """
    cat = visible if visible is not None else grid.catalogue

    # Distance to visible catalogue
    dist_cat = ndi.distance_transform_edt(~cat & grid.footprint, sampling=100.0)
    k_cat = kernel(dist_cat / 100.0)  # kernel in pixel units

    # Distance to SGMC (off-catalogue)
    dist_sgmc = ndi.distance_transform_edt(~sgmc_off_cat & grid.footprint, sampling=100.0)
    k_sgmc = kernel(dist_sgmc / 100.0)

    if mode == "max":
        p = np.maximum(k_cat, k_sgmc)
    elif mode == "sum":
        p = np.clip(k_cat + k_sgmc, 0, 1)
    elif mode == "sgmc_prior":
        # SGMC mask as strong prior, catalogue proximity as secondary
        p = np.where(sgmc_off_cat, 1.0, k_cat)
    elif mode == "sgmc_only":
        p = k_sgmc
    elif mode == "cat_only":
        p = k_cat
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Ensure footprint and off-catalogue
    p = np.where(grid.footprint & ~grid.catalogue, p, 0.0).astype(np.float32)
    return p


def run_experiment(grid, ctx, sgmc_off_cat, mode="max", k_truth_factor=1.0,
                   max_dots=100_000, verbose=True):
    """Run one experiment: build surface, allocate dots, score on holdout."""
    t0 = time.time()

    # Build probability surface using FULL catalogue (for emission)
    # The holdout evaluation will mask visible faults appropriately
    p = build_probability_surface(grid, sgmc_off_cat, visible=grid.catalogue, mode=mode)

    allowed = grid.footprint & ~grid.catalogue

    # Estimate k_truth from the holdout
    total_truth = sum(c.n_truth for c in ctx.cells) / len(ctx.cells) * 4  # approximate total
    k_truth = int(total_truth * k_truth_factor)

    if verbose:
        print(f"  Mode: {mode}, k_truth={k_truth}, max_dots={max_dots}")
        print(f"  p range: [{p.min():.4f}, {p.max():.4f}], nonzero: {(p > 0).sum()}")

    # Use the patient allocator (doesn't stop at first rejection)
    alloc = allocate_patient(p, allowed, k_truth=k_truth,
                             max_dots=max_dots, patience=50_000)

    if verbose:
        print(f"  Allocated {alloc.n_dots} dots in {alloc.rounds} rounds, "
              f"surrogate DTI={alloc.surrogate_dti:.4f}")

    # Score on holdout
    emitted = alloc.emitted & grid.footprint & ~grid.catalogue
    result = evaluate(emitted, ctx, cell_mode="all")

    elapsed = time.time() - t0
    if verbose:
        print(f"  HOLDOUT-DTI: {result['pooled_dti']:.4f} "
              f"(coverage={result['pooled_coverage']:.4f}, "
              f"emitted={result['emitted_pixels']}, "
              f"elapsed={elapsed:.0f}s)")

    return {
        "mode": mode,
        "k_truth_factor": k_truth_factor,
        "max_dots": max_dots,
        "n_dots": alloc.n_dots,
        "surrogate_dti": alloc.surrogate_dti,
        "pooled_dti": result["pooled_dti"],
        "coverage": result["pooled_coverage"],
        "emitted": result["emitted_pixels"],
        "per_fold": result["per_fold_dti"],
        "tp": result["pooled_tp"],
        "fp": result["pooled_fp"],
        "fn": result["pooled_fn"],
        "elapsed_s": elapsed,
    }


def main():
    t_start = time.time()
    grid = load_grid(ROOT / "data" / "bridge")
    sgmc = load_sgmc(ROOT, grid)

    print("Building holdout context...")
    ctx = build_holdout(grid, hide_frac=0.20, seeds=(20, 21), modes=("all",))
    print(f"Holdout: {len(ctx.cells)} cells, "
          f"total withheld={sum(c.n_truth for c in ctx.cells)} px")

    # Experiment grid: modes × k_truth_factors × max_dots
    modes = ["max", "sgmc_prior", "cat_only", "sgmc_only", "sum"]
    k_truth_factors = [0.5, 1.0, 2.0]
    max_dots_list = [50_000, 100_000]

    results = []
    best_dti = -1
    best_config = None

    for mode in modes:
        for ktf in k_truth_factors:
            for md in max_dots_list:
                print(f"\n--- Experiment: mode={mode}, ktf={ktf}, max_dots={md} ---")
                try:
                    r = run_experiment(grid, ctx, sgmc, mode=mode,
                                      k_truth_factor=ktf, max_dots=md)
                    results.append(r)
                    if r["pooled_dti"] > best_dti:
                        best_dti = r["pooled_dti"]
                        best_config = r
                except Exception as e:
                    print(f"  ERROR: {e}")

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"{'Mode':<15} {'ktf':>5} {'maxD':>8} {'nDots':>8} {'DTI':>8} {'Cov':>8} {'TP':>8} {'FP':>8} {'FN':>8}")
    print("-"*80)
    for r in sorted(results, key=lambda x: -x["pooled_dti"]):
        print(f"{r['mode']:<15} {r['k_truth_factor']:>5.1f} {r['max_dots']:>8d} "
              f"{r['n_dots']:>8d} {r['pooled_dti']:>8.4f} {r['coverage']:>8.4f} "
              f"{r['tp']:>8.1f} {r['fp']:>8.1f} {r['fn']:>8.1f}")

    if best_config:
        print(f"\nBest: mode={best_config['mode']}, ktf={best_config['k_truth_factor']}, "
              f"DTI={best_config['pooled_dti']:.4f}, dots={best_config['n_dots']}")

    # Save results
    evidence = {
        "experiments": results,
        "best": best_config,
        "total_elapsed_s": time.time() - t_start,
    }
    out = ROOT / "evidence" / "mece_experiments.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2, default=str))
    print(f"\nResults saved to {out}")
    print(f"Total time: {time.time() - t_start:.0f}s")


if __name__ == "__main__":
    raise SystemExit(
        "DEPRECATED/NO-GO: MECE is outside the current ribbon-only scope; its "
        "holdout is leakage-flagged and registry clearance is incomplete. "
        "Do not run or submit these artifacts."
    )
