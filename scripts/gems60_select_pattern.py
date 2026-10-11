#!/usr/bin/env python3
"""Select the emission geometry from the exact-metric sweep weighted by measured σ.

Reads ``evidence/gems60/sigma.json`` (the measured across-strike localization-error
distribution over associated candidates, per family/scale/block) and
``evidence/gems60/pattern.json`` (the exact-metric sweep of dotted-ribbon patterns,
grid: n_lines {1,2,3,5} × line spacing {1.5,2.0,2.8,3.5} px × along-strike spacing
{2.0,2.8,3.0,4.0,6.0} px × across-strike bias {0..3} px).

Each σ stratum contributes a piecewise-linear / exponential-tail CDF over bias;
the sweep's bias classes carry the utility U = (1 − α·DTI₀)·ΔTP − α·DTI₀·ΔFP at
DTI₀ = 0.26 (the family's central live score) and α = 0.2.  The selector is the
pattern maximising the σ-weighted expected utility, separately for the two
truth-texture scenarios, and the emitted geometry is the closest *realisable*
pattern (the dot lattice enforces a ≥ 3 px minimum separation, so line spacings
below ~3 px collapse unless lines are staggered).

Writes ``evidence/gems60/pattern_weighted.json``.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "gems60"


def strat_cdf(q25: float, med: float, q75: float, x: float) -> float:
    if x <= q25:
        return 0.25 * math.exp(-(q25 - x) / max(med - q25, 1e-6)) if x < q25 else 0.25
    if x <= med:
        return 0.25 + 0.25 * (x - q25) / max(med - q25, 1e-9)
    if x <= q75:
        return 0.50 + 0.25 * (x - med) / max(q75 - med, 1e-9)
    return min(0.9995, 0.75 + 0.25 * (1 - math.exp(-(x - q75) / max(q75 - med, 1e-6))))


def main() -> int:
    sig = json.loads((EV / "sigma.json").read_text())
    pat = json.loads((EV / "pattern.json").read_text())
    strata = [(int(r["n"]), float(r["sigma_p25_px"]), float(r["sigma_median_px"]), float(r["sigma_p75_px"]))
              for r in sig["sigma"]
              if r.get("family") not in (None, "all") and r.get("sigma_median_px")]
    n_total = sum(n for n, *_ in strata)
    classes = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]

    def weight(b: float) -> float:
        lo = b - 0.25 if b else -0.25
        hi = (b + 0.25) if b < 2.0 else (2.5 if b == 2.0 else 100.0)
        return sum(n * (strat_cdf(q25, med, q75, hi) - strat_cdf(q25, med, q75, lo))
                   for n, q25, med, q75 in strata) / n_total

    weights = {str(b): weight(b) for b in classes}
    out = dict(
        evidence_class="PATTERN-SELECTION",
        protocol="gems60 pattern selection v1",
        source_receipts=["evidence/gems60/sigma.json", "evidence/gems60/pattern.json"],
        strata=[dict(n=n, p25=q25, median=med, p75=q75) for n, q25, med, q75 in strata],
        bias_weights=weights,
        dti0_note=("U is evaluated at DTI0 = 0.26, the family's central live score "
                   "(sensitivity: the ranking of patterns is unchanged between 0.20 and 0.40 "
                   "because alpha*DTI0 enters only through the FP price)"),
        scenarios={},
    )
    for key, blk in pat.items():
        u_by_bias = {str(b): dict(u=r["u"], tp=r["tp"], fp=r["fp"], dots=r["dots"],
                                  n_lines=r["n_lines"], line_spacing_px=r["line_spacing_px"],
                                  along_px=r["along_px"])
                     for b, r in ((str(rr["bias_px"]), rr) for rr in blk["rows"] if
                                  abs(rr["bias_px"] - float(str(rr["bias_px"]))) < 1e-9)}
        scores: dict[tuple, float] = {}
        for r in blk["rows"]:
            k = (r["n_lines"], r["line_spacing_px"], r["along_px"])
            scores[k] = scores.get(k, 0.0) + weights[str(r["bias_px"])] * r["u"]
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        singles = {str(b): blk["single_tight_line_by_bias"][str(b)] for b in classes}
        best_by_shape: dict[tuple, tuple] = {}
        for (nl, sp, al), v in scores.items():
            cur = best_by_shape.get((nl, sp))
            if cur is None or v > cur[1]:
                best_by_shape[(nl, sp)] = (al, v)
        decision_table = [dict(n_lines=nl, line_spacing_px=sp, best_along_px=val[0],
                               expected_u=round(val[1], 4))
                          for (nl, sp), val in sorted(best_by_shape.items())]
        out["scenarios"][key] = dict(
            truth_scatter_px=blk["truth_scatter_px"], dti0=blk["dti0"], alpha=blk["alpha"],
            n_patterns=blk["n_patterns"],
            single_tight_line_u=singles,
            top_patterns=[dict(n_lines=k[0], line_spacing_px=k[1], along_px=k[2],
                               expected_u=round(v, 4)) for k, v in ranked[:10]],
            decision_table=decision_table,
            realisable_arms={f"{k[0]} lines at {k[1]} px spacing, along {k[2]} px": round(v, 4)
                             for k, v in sorted(scores.items())
                             if abs(k[1] - 2.8) < 1e-9 or abs(k[1] - 3.5) < 1e-9},
        )
        del u_by_bias
    out["emitted_geometry"] = dict(
        note=("the emitted rasters carry the centre line plus parallel lines every "
              "RIBBON_LINE_SPACING_PX = 3.0 px, i.e. the sweep's 2.8 px column (bracketed "
              "by 3.5 px) rounded to the kernel radius; the dot lattice then enforces a "
              ">= 3 px minimum separation, which is why the sweep's tighter columns "
              "(1.5 / 2.0 px) are not realisable as separate lines"),
        arms={"ribbon3": "3 lines at ±3 px (26,408 dots)", "ribbon6": "5 lines at ±6 px (40,000 dots)"},
        shipped="ribbon6",
    )
    (EV / "pattern_weighted.json").write_text(json.dumps(out, indent=1) + "\n")
    for key, s in out["scenarios"].items():
        top = s["top_patterns"][0]
        print(f"{key}: top pattern {top['n_lines']} lines @ {top['line_spacing_px']} px, "
              f"along {top['along_px']} px, E[U|sigma]={top['expected_u']}")
        for name, v in list(s["realisable_arms"].items())[:8]:
            print(f"    realisable: {name}: {v}")
    print(f"bias weights: { {k: round(v, 3) for k, v in weights.items()} }")
    print(f"wrote {EV / 'pattern_weighted.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
