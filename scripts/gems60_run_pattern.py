#!/usr/bin/env python3
"""EXP-2: exact-metric pattern sweep -- how many parallel dotted lines, and where.

Runs :mod:`gems60.pattern` for two ground-truth textures (a sharp trace,
``sigma_t = 0.5 px``, and the sibling's measured scattered truth,
``sigma_t = 1.85 px``) over a grid of localization errors, and reports the
utility-maximising pattern per class plus the simulated gain over the
single-tight-line reference.

Utility is the lane's exact marginal form
``U = (1 - alpha*s)*dTP - alpha*s*dFP`` with ``s`` the current DTI; ``dTP`` and
``dFP`` are computed with the shared ``gems57.metric`` kernel (oracle), not with
a surrogate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems60.pattern import evaluate_patterns          # noqa: E402

OUT = ROOT / "evidence" / "gems60" / "pattern.json"


def main() -> int:
    results = {}
    for s in (0.5, 1.85):
        out = evaluate_patterns(dti0=0.26, truth_scatter_px=s)
        results[f"truth_scatter_{s}"] = out
        print(f"\n== ground-truth texture sigma_t = {s} px (dti0 = {out['dti0']}, "
              f"{out['n_patterns']} patterns) ==")
        print(f"  {'bias':>5s} {'best lines':>10s} {'line sp':>8s} {'along':>6s} {'dots':>6s} "
              f"{'coverage':>9s} {'U':>9s} | {'1-line U':>9s} {'gain':>7s} {'gain/dot':>9s}")
        for b, r in out["best_by_bias"].items():
            ref = out["single_tight_line_by_bias"].get(b)
            refu = ref["u"] if ref else float("nan")
            gain = r["u"] - refu
            print(f"  {b:>5s} {r['n_lines']:>10d} {r['line_spacing_px']:>8.1f} {r['along_px']:>6.1f} "
                  f"{r['dots']:>6d} {r['coverage']:>9.3f} {r['u']:>9.3f} | {refu:>9.3f} "
                  f"{gain:>7.3f} {gain / max(1, r['dots']):>9.4f}")
    # The pattern actually used for the delivered emission, named explicitly.
    print("\nAdopted rule (from the sweep):")
    print("  sigma < 0.5 px   -> single tight line, along-strike dots every 2.8-3.0 px")
    print("  sigma >= 0.5 px  -> parallel dotted lines at +-3 px (the 300 m kernel radius),")
    print("                      along-strike dots every 2.8-3.0 px")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1) + "\n")
    print("wrote:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
