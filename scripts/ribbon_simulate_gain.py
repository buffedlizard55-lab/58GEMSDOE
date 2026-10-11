"""Analytic companion to EXP-2: expected DTI per sigma class at equal dot density.

The model is deliberately 1-D and transparent, so the qualitative ordering can
be read off without any holdout noise:

* the truth is a straight fault trace at across-strike offset ``delta`` from the
  detected ridge centreline, ``delta ~ half-Normal(0, sigma)`` (the measured
  across-strike error scale);
* the along-strike component of the localisation error is absorbed by the line
  itself, because a dotted line extends along strike -- which is exactly why the
  measured ``sigma_along`` (2.8 px) is smaller than ``sigma_across`` (4.3 px);
* a ribbon emits ``|U|`` parallel lines at across-strike offsets ``U``, dotted at
  along-strike spacing ``s``;
* every configuration is compared at the **same dot density** on the ground,
  i.e. ``|U| / s`` is held fixed, so the false-positive charge is identical and
  only the true-positive term differs.

Credit uses the official triangular kernel ``k(d) = max(1 - d/3, 0)`` and the
official per-truth maximum over predictions, so the numbers below are the exact
metric for this idealised geometry.

    DTI(sigma, U, s) = E_delta[ c(delta) ] / (0.8 + 0.2 * |U| / s)

where ``c(delta)`` is the covered truth credit per unit of fault length and the
denominator is the exact ``TP + alpha*FP + beta*FN`` per unit of fault length
(one truth pixel per unit length).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ALPHA = 0.2
BETA = 0.8
R = 3.0

#: across-strike line offsets, in pixels, of each candidate ribbon
RIBBONS: dict[str, tuple[float, ...]] = {
    "T1": (0.0,),
    "R3_d2": (-2.0, 0.0, 2.0),
    "R5_d2": (-4.0, -2.0, 0.0, 2.0, 4.0),
    "R7_d2": (-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0),
    "R3_d3": (-3.0, 0.0, 3.0),
    "R5_d3": (-6.0, -3.0, 0.0, 3.0, 6.0),
    "R3_d1": (-1.0, 0.0, 1.0),
    "R5_d1": (-2.0, -1.0, 0.0, 1.0, 2.0),
}

#: reference dot density: dots per pixel of fault length (|U| / s)
DENSITY = 1.0 / 6.0


def kernel(d):
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / R, 0.0)


def covered_credit(delta: float, offsets: tuple[float, ...], stride: int,
                   half: int = 8) -> float:
    """Covered kernel credit per unit fault length for one across-strike offset."""
    best = 0.0
    t = np.arange(-half, stride + half, dtype=np.float64)
    m = 0
    while m * stride - half <= stride + half:
        for u in offsets:
            d = np.hypot(delta - u, t - m * stride)
            best = max(best, float(kernel(d).sum()))
        m += 1
        if m > 40:
            break
    # the sum above double counts overlapping kernels when stride < 6; take the
    # per-truth maximum instead, which is what the metric does.
    tt = np.arange(-half, stride + half, dtype=np.float64)
    tot = 0.0
    for u in offsets:
        d = np.minimum.reduce([np.hypot(delta - u, tt - m * stride)
                               for m in range(-3, 4)])
        tot = max(tot, float(kernel(d).sum()))
    return tot / float(stride)


def dti_for_class(sigma: float, offsets: tuple[float, ...], density: float = DENSITY,
                  n_delta: int = 241, tail: float = 4.0) -> float:
    """Expected DTI for one sigma class at a fixed dot density."""
    stride = max(1.0, len(offsets) / density)
    stride_i = int(round(stride))
    stride_i = max(1, stride_i)
    actual_density = len(offsets) / float(stride_i)
    grid = np.linspace(0.0, tail * max(sigma, 1e-6), n_delta)
    w = np.exp(-0.5 * (grid / max(sigma, 1e-6)) ** 2)
    w /= w.sum()
    c = np.array([covered_credit(float(g), offsets, stride_i) for g in grid])
    tp = float((w * np.minimum(c, 1.0)).sum())
    den = tp + ALPHA * actual_density + BETA * (1.0 - tp)
    return float(tp / den)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", default="0.25,0.5,1.0,1.5,2.0,2.5,3.0,4.0,5.0,6.0,8.0")
    ap.add_argument("--density", type=float, default=DENSITY)
    ap.add_argument("--out", default="evidence/ribbon_v3/simulated_gain.json")
    args = ap.parse_args()

    classes = [float(x) for x in args.classes.split(",")]
    rows = []
    for sg in classes:
        scores = {name: dti_for_class(sg, offs, args.density)
                  for name, offs in RIBBONS.items()}
        best = max(scores, key=scores.get)
        rows.append(dict(sigma_px=sg, scores=scores, best=best,
                         best_dti=scores[best],
                         tight_dti=scores["T1"],
                         gain_best_vs_tight=scores[best] - scores["T1"]))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        dict(alpha=ALPHA, beta=BETA, radius_px=R,
             dot_density_per_fault_px=args.density,
             note="equal dot density on the ground: |U|/s is held fixed, so the "
                  "false-positive charge is identical across ribbons",
             rows=rows), indent=1))
    hdr = "sigma  " + "  ".join(f"{n:>7s}" for n in RIBBONS) + "   best"
    print(hdr)
    for r in rows:
        print(f"{r['sigma_px']:5.2f}  " +
              "  ".join(f"{r['scores'][n]:7.4f}" for n in RIBBONS) +
              f"   {r['best']} (+{r['gain_best_vs_tight']:.4f})")


if __name__ == "__main__":
    main()
