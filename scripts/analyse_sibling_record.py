#!/usr/bin/env python3
"""Measure the owner's own submission record: raster statistics vs reported score.

Why this exists
---------------
No organizer receipt is reachable from this sandbox (the DrivenData submission
page needs a login), so the only external information about the *real* scoring
behaviour is the owner's public record: raster bytes published in the sibling
repositories, paired with the scores quoted on those repositories' pages.  This
script turns that record into measurements rather than anecdotes.

Labels used
-----------
* ``USER-REPORTED-SCORE``  -- the number as quoted in the project prompt / on the
  sibling page.  It is NOT an organizer receipt.  One such attribution is already
  known to be wrong (see ``registry/submissions_seen.csv``: the 0.2778 on the
  public leaderboard belongs to a different team, not to the GEMSDOE32 file), so
  every row here carries that caveat.
* ``REGISTRY-MEASUREMENT`` -- anything computed from the raster bytes themselves,
  each file sha256-verified against ``registry/registry_refreshed.json``.

What it measures
----------------
For each paired raster: positive-pixel count, value range, mean kernel credit
against the *public* catalogue (how near-catalogue the emission is), and the
algebraic consequences of the exact metric for that dot count.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import load_grid                       # noqa: E402
from gems57.metric import ALPHA, BETA, kernel           # noqa: E402

# (registry file name, score as quoted by the owner, where it was quoted)
PAIRS = [
    ("8GEMSDOE_Hedge-v2_submission.tif", 0.1563, "8GEMSDOE page"),
    ("gems7-lidarscarp-ridge-top2pct-36c3a3f341c8.tif", 0.1461, "7GEMSDOE page"),
    ("12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif", 0.1294, "12GEMSDOE page"),
    ("gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
     0.1894, "19GEMSDOE page"),
    ("gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
     0.1922, "19GEMSDOE page"),
    ("gems49-gate_ortho_w0.25-40k-20261006T213721Z-nan.tif", 0.2376, "GEMSDOE49 page"),
    ("GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif",
     0.2632, "GEMSDOE33 page"),
    ("gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-nan.tif",
     0.2750, "GEMSDOE36 page"),
    ("gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708, "GEMSDOE31 page"),
    ("gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710, "GEMSDOE28 page"),
    ("gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif", 0.2649, "GEMSDOE28 page"),
    ("gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif", 0.2707, "GEMSDOE28 page"),
    ("GEMSDOE30__d28-poisson300m-offcat-44090.tif", 0.2600, "GEMSDOE30 page"),
    ("gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600, "GEMSDOE25 page"),
    ("gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, "GEMSDOE24 page"),
    ("gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, "GEMSDOE27 page"),
    ("gems29-wormrank-d28-20261003-59dcaf6dd11d-nan.tif", 0.2560, "GEMSDOE29 page"),
    ("gems29-refd28-repro-20261003-1cc7dc534d51-nan.tif", 0.2600, "GEMSDOE29 page"),
    ("gems29-wormrank-d28-20261003-73a8c4d12139-nan.tif", 0.2560, "GEMSDOE29 page"),
    ("gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif", 0.2778,
     "user prompt; the GEMSDOE32 page itself says NO ORGANISER SCORE EXISTS -- see registry/submissions_seen.csv"),
]


def main() -> int:
    grid = load_grid(ROOT / "data" / "bridge")
    fp = grid.footprint
    N = int(fp.sum())
    k_cat = kernel(ndi.distance_transform_edt(~grid.catalogue))     # kernel credit vs catalogue
    reg = json.loads((ROOT / "registry" / "registry_refreshed.json").read_text())
    by_name = {x["sources"][0].split("/")[-1]: x for x in reg["rasters"]}

    # exact kernel cone sum over the lattice (used in the carpet algebra below)
    r = 3
    S = float(sum(kernel(np.hypot(j, i)) for j in range(-r, r + 1) for i in range(-r, r + 1)))

    rows = []
    for name, score, where in PAIRS:
        rec = by_name.get(name)
        if rec is None:
            rows.append(dict(file=name, status="not_in_registry"))
            continue
        p = ROOT / ".cache" / "registry" / f"{rec['sha256']}.tif"
        if not p.is_file():
            rows.append(dict(file=name, status="not_restored"))
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest != rec["sha256"]:
            rows.append(dict(file=name, status="sha256_pin_mismatch"))
            continue
        with rasterio.open(p) as src:
            a = src.read(1)
        a = np.where(np.isfinite(a), a, 0.0).astype(np.float64)
        a[~fp] = 0.0
        sup = a > 0
        n = int(sup.sum())
        if n == 0:
            rows.append(dict(file=name, status="empty"))
            continue
        # solve the metric algebra for the implied truth credit T, given K unknown:
        #   score = T / (alpha*(T + n - M) + beta*K)
        # with the near-bijection assumption T == M this gives
        #   T = score * (alpha*n + beta*K)
        rows.append(dict(
            file=name, sha256=digest, status="ok",
            score_as_quoted=score, score_label="USER-REPORTED-SCORE", score_source=where,
            dots=n, dots_per_footprint_pct=round(100.0 * n / N, 4),
            value_min=float(a[sup].min()), value_max=float(a[sup].max()),
            value_mean=float(a[sup].mean()), n_unique_values=int(len(np.unique(a[sup]))),
            mean_kernel_credit_vs_public_catalogue=float(k_cat[sup].mean()),
            frac_dots_within_3px_of_catalogue=float((k_cat[sup] > 0).mean()),
            implied_T_if_T_equals_M_per_K={
                str(K): round(score * (ALPHA * n + BETA * K), 1) for K in (60988, 100000, 142000)},
        ))
    ok = [r for r in rows if r.get("status") == "ok"]
    ok.sort(key=lambda r: r["dots"])

    small = [r for r in ok if r["dots"] <= 50_000]
    large = [r for r in ok if r["dots"] > 50_000]
    out = dict(
        evidence_class="REGISTRY-MEASUREMENT + USER-REPORTED-SCORE",
        caveat=("Scores are as quoted by the owner on the sibling pages, not organizer receipts. "
                "At least one attribution in the owner's own record is known to be wrong "
                "(registry/submissions_seen.csv, GEMSDOE32). Every raster statistic below was "
                "recomputed from sha256-verified bytes."),
        footprint_pixels=N, kernel_cone_sum_S=S,
        n_paired=len(rows), n_measured=len(ok),
        rows=rows,
        summary=dict(
            small_budget=dict(n_rasters=len(small),
                              dots_range=[min(r["dots"] for r in small), max(r["dots"] for r in small)],
                              score_range=[min(r["score_as_quoted"] for r in small),
                                           max(r["score_as_quoted"] for r in small)],
                              median_score=float(np.median([r["score_as_quoted"] for r in small]))),
            large_budget=dict(n_rasters=len(large),
                              dots_range=[min(r["dots"] for r in large), max(r["dots"] for r in large)],
                              score_range=[min(r["score_as_quoted"] for r in large),
                                           max(r["score_as_quoted"] for r in large)],
                              median_score=float(np.median([r["score_as_quoted"] for r in large])))
            if large else None,
            spearman_dots_vs_score=float(_spearman([r["dots"] for r in ok],
                                                   [r["score_as_quoted"] for r in ok])),
            note=("All rasters at or below ~44k positive pixels out-score every raster above 50k; "
                  "the metric's alpha*n term makes the dot budget, not the dot values, the first-order lever."),
        ),
    )
    (ROOT / "evidence" / "sibling_record.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    s = out["summary"]
    print(f"measured {len(ok)}/{len(rows)} paired rasters")
    print(f"  <=50k dots: n={s['small_budget']['n_rasters']} "
          f"dots {s['small_budget']['dots_range']} score {s['small_budget']['score_range']} "
          f"median {s['small_budget']['median_score']:.4f}")
    if s["large_budget"]:
        print(f"  >50k dots : n={s['large_budget']['n_rasters']} "
              f"dots {s['large_budget']['dots_range']} score {s['large_budget']['score_range']} "
              f"median {s['large_budget']['median_score']:.4f}")
    print(f"  Spearman(dots, score) = {s['spearman_dots_vs_score']:+.3f}")
    print("wrote evidence/sibling_record.json")
    return 0


def _spearman(x, y):
    from scipy.stats import rankdata
    a = rankdata(x); b = rankdata(y)
    a = a - a.mean(); b = b - b.mean()
    d = float(np.linalg.norm(a)) * float(np.linalg.norm(b))
    return float(np.dot(a, b) / d) if d else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
