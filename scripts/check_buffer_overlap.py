#!/usr/bin/env python3
"""Pick an off-catalogue buffer whose dot set clears the protocol's drift gate.

Protocol rule 1: "more than [70%] of your dots fall within 3 px of one registry
raster's dots" means lane drift. The first E3 emission (buffer = 3 px, 36,394 dots)
passed the rank-correlation gate by a wide margin (worst Spearman rho 0.140) and the
Jaccard gate (worst 0.061), but seven *sparse* registry rasters (80k-192k dots, all
near-catalogue bands) sit above 0.70 forward overlap, the worst at 0.876 against
``13GEMSDOE:.../13gems_20261001_r14-union-tips10-lat6_zerofill.tif``.

This script measures the forward overlap of the SAME ranking at a range of
off-catalogue buffers against the shortlist that actually binds (the sparse
registry rasters, plus the proven dotted-ridge lineage as a reference), so the
emission can be moved to a buffer that is both holdout-competitive and clearly
inside its own lane.

Cost is kept low on purpose: only the shortlist is scanned, one dilation per
raster, reused across every buffer.
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
sys.path.insert(0, str(ROOT / "scripts"))

from gems57.grid import HEIGHT, WIDTH, load_grid          # noqa: E402
from gems57.uniqueness import _near                       # noqa: E402
from gems59.features import open_stack                    # noqa: E402
from run_model_experiments import NMS_RADIUS_PX, nms_dots  # noqa: E402

BUFFERS = (3, 4, 5, 6, 7, 8, 10)
BUDGET = 40_000
SHORTLIST_MAX_DOTS = 300_000      # dense carpets (>=1M dots) are excluded: they overlap 1.00 with anything
LINEAGE_KEYS = ("h27-4-solo-d28", "d28-poisson300m-offcat", "dotted-h19-5", "h19-5-powerlaw",
                "h36-1-rung30", "anderson-geothermal", "h32-1-prethin", "h38-1-hf-euler")
STRUCT = np.ones((3, 3), bool)


def main() -> int:
    grid = load_grid(ROOT / "data" / "bridge")
    fp = grid.footprint
    reg = json.loads((ROOT / "registry" / "registry_refreshed.json").read_text())
    prev = json.loads((ROOT / "evidence" / "model_uniqueness.json").read_text())

    # shortlist = every registry entry that flagged the first emission, plus the proven lineage
    short: dict[str, str] = {}
    for r in prev["rows"]:
        if r.get("error") or r.get("their_dots", 0) > SHORTLIST_MAX_DOTS:
            continue
        if r.get("duplicate_by_overlap"):
            short[r["sha256"]] = r["submission"]
    for x in reg["rasters"]:
        if any(k in x["sources"][0] for k in LINEAGE_KEYS):
            short.setdefault(x["sha256"], x["sources"][0])
    print(f"shortlist: {len(short)} registry rasters", flush=True)

    # the live ranking the emission uses: NMS over the footprint minus the catalogue,
    # ordered by distance to the catalogue (the PROX family chosen by E3 on the holdout)
    dcat = ndi.distance_transform_edt(~grid.catalogue).astype(np.float32)
    base = fp & ~grid.catalogue & (dcat > 0)
    dots_all = {b: nms_dots(np.where(base & (dcat > b), -dcat, -np.inf), base & (dcat > b))
                for b in BUFFERS}
    sets = {}
    for b in BUFFERS:
        dy, dx = np.nonzero(dots_all[b])
        vals = dcat[dy, dx]
        n = min(BUDGET, dy.size)
        keep = np.argpartition(vals, n - 1)[:n] if dy.size > n else np.arange(dy.size)
        m = np.zeros((HEIGHT, WIDTH), bool)
        m[dy[keep], dx[keep]] = True
        sets[b] = m
        print(f"  buffer {b:2d} px: {int(m.sum()):,} dots", flush=True)

    rows = []
    for sha, name in sorted(short.items(), key=lambda kv: kv[1]):
        p = ROOT / ".cache" / "registry" / f"{sha}.tif"
        if not p.is_file():
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != sha:
            rows.append(dict(sha256=sha, submission=name, error="sha256 pin mismatch"))
            continue
        with rasterio.open(p) as src:
            t = src.read(1)
        t = np.where(np.isfinite(t), t, 0.0)
        t[~fp] = 0.0
        sup = t > 0
        near = _near(sup)      # exact same 3-px disk the registry scan uses
        rec = dict(sha256=sha, submission=name, their_dots=int(sup.sum()),
                   three_px_dilation_coverage_of_footprint=float(near[fp].mean()),
                   overlap_by_buffer={str(b): float(near[sets[b]].mean()) if sets[b].any() else 0.0
                                      for b in BUFFERS})
        rec["max_overlap"] = max(rec["overlap_by_buffer"].values())
        rows.append(rec)
        print(f"  {name[:58]:58s} cov={rec['three_px_dilation_coverage_of_footprint']:.3f} " +
              " ".join(f"{rec['overlap_by_buffer'][str(b)]:.3f}" for b in BUFFERS), flush=True)

    worst = {str(b): max(r.get("max_overlap", 0.0) for r in rows) for b in BUFFERS}
    ok = [b for b in BUFFERS if worst[str(b)] <= 0.70]
    out = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        question="which off-catalogue buffer keeps the emission inside its own lane (<=70% forward "
                 "3-px dot overlap against any registry raster)?",
        shortlist_rasters=len(rows), budget_dots=BUDGET, nms_radius_px=NMS_RADIUS_PX,
        buffers=list(BUFFERS),
        worst_overlap_by_buffer=worst,
        buffers_clearing_the_gate=ok,
        chosen_buffer=int(ok[0]) if ok else None,
        rows=rows,
        discriminative_rasters=[r["submission"] for r in rows
                                if r.get("three_px_dilation_coverage_of_footprint", 1.0) <= 0.70],
        rule="parallel-run protocol rule 1; dense soft carpets (>300k positive cells) are not on the "
             "shortlist because they overlap 1.00 with ANY near-catalogue emission (IR-58-UNIQ-01). "
             "three_px_dilation_coverage_of_footprint is the objective carrier test: a raster whose own "
             "3-px dilation covers most of the study area flags every emission at ~1.00 and carries no "
             "information about lane drift (IR-58-UNIQ-02).",
    )
    (ROOT / "evidence" / "buffer_overlap_scan.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("worst overlap by buffer:", {k: round(v, 3) for k, v in worst.items()})
    print("buffers clearing the 0.70 gate:", ok, "-> chosen:", out["chosen_buffer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
