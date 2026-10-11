#!/usr/bin/env python3
"""Build and cache the gems60 cross-family convergence field (EXP-0, no scoring).

Reads the sha256-pinned official 19-band stack through ``gems59.features``
(shared reader; the stack pin is re-verified there), computes the convergence
surface block-wise, and caches it OUTSIDE git under ``~/.cache/gems``.

Usage:  PYTHONPATH=src python3 scripts/gems60_build_field.py [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import load_grid                      # noqa: E402
from gems59.features import open_stack                 # noqa: E402
from gems60 import convergence as C                    # noqa: E402

CACHE = Path.home() / ".cache" / "gems" / "gems60_convergence.npz"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--out", default=str(CACHE))
    args = ap.parse_args()
    out = Path(args.out)

    grid = load_grid(ROOT / "data" / "bridge")
    stack = open_stack()
    print(f"stack   : {stack.path} ({Path(stack.path).stat().st_size} B)")
    print(f"bands   : {len(stack.bands)}  grid={grid.shape}")

    if out.exists() and not args.force:
        conv = C.load(out)
        print(f"cached  : {out} ({out.stat().st_size} B) - use --force to rebuild")
    else:
        t0 = time.time()

        def log(r0, r1):
            print(f"  rows {r0:5d}-{r1:5d}  {time.time() - t0:6.1f}s", flush=True)

        conv = C.compute(stack, grid.footprint, writers=log)
        receipt = C.save(conv, out)
        print(f"wrote   : {receipt['path']} ({out.stat().st_size} B) in {time.time() - t0:.1f}s")

    fp = grid.footprint
    score = conv.score[fp]
    hist = {int(k): int(v) for k, v in zip(*np.unique(score.astype(np.int16), return_counts=True))}
    print("families:", conv.families)
    print("scales  :", conv.scales)
    print("score histogram inside the footprint (families agreeing -> cells):")
    for k in sorted(hist):
        print(f"   {k}: {hist[k]:9d}  ({100.0 * hist[k] / score.size:6.2f}%)")
    rows = int((conv.score[fp] >= 2).sum())
    print(f"cells with >=2 families agreeing: {rows} ({100.0 * rows / score.size:.2f}% of footprint)")
    # winning family / scale shares among >=2 agreements
    for th in (2, 3, 4):
        m = fp & (conv.score >= th)
        if m.any():
            fi = conv.fam_ix[m]
            si = conv.scale_ix[m]
            names = [conv.families[i] for i in np.unique(fi) if i >= 0]
            scales = [conv.scales[int(i)] for i in np.unique(si) if i >= 0]
            print(f"  >= {th}: {int(m.sum()):8d} cells, winner families {names}, scales {scales}")
    summary = dict(cache=str(out), bytes=out.stat().st_size, families=list(conv.families),
                   scales=list(conv.scales), score_hist=hist,
                   ge2=int((conv.score[fp] >= 2).sum()), footprint=int(fp.sum()),
                   bands=list(conv.bands))
    (out.with_suffix(".json")).write_text(json.dumps(summary, indent=1) + "\n")
    print("summary :", out.with_suffix(".json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
