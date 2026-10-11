#!/usr/bin/env python3
"""ARCHIVED legacy theorem script — do not use for current qualification.

This script imports the private ``gems58w`` metric and its old marginal-rule
wording generalized ``k > alpha*s`` beyond the non-redundant one-dot case.
Its command-line entry point is disabled. The corrected exact pattern rule and
shared-metric regression test are in ``docs/research/metric.md`` and
``tests/test_metric_exact.py``; current holdout work must use ``gems57``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import metric  # noqa: E402
from gems58w.paths import evidence_dir  # noqa: E402


def theorem_denominator(seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    truth = rng.random((60, 64)) < 0.04
    dots = rng.random((60, 64)) < 0.02
    r = metric.dti_binary(dots, truth)
    lhs = r.tp + metric.ALPHA * r.fp + metric.BETA * r.fn
    rhs = metric.ALPHA * (r.tp + r.fp) + metric.BETA * r.n_truth
    return dict(abs_diff=abs(lhs - rhs), passed=abs(lhs - rhs) < 1e-9)


def theorem_binary_dominates(seed: int = 2) -> dict:
    rng = np.random.default_rng(seed)
    truth = rng.random((60, 64)) < 0.05
    b = rng.random((60, 64)) < 0.02
    lams = np.linspace(0.05, 1.0, 20)
    vals = [metric.dti_exact(b.astype(float) * lam, truth).dti for lam in lams]
    d = [(t / (metric.ALPHA * b.sum() + metric.BETA * truth.sum() + metric.EPS))
         for t in [float(metric.kernel(0.0)) * b.sum() * lam for lam in lams]]  # noqa: F841
    r = metric.dti_binary(b, truth)
    analytic = [lam * r.tp / (metric.ALPHA * lam * (r.tp + r.fp) + metric.BETA * r.n_truth
                              + metric.EPS) for lam in lams]
    max_err = float(np.max(np.abs(np.array(vals) - np.array(analytic))))
    monotone = all(y > x for x, y in zip(vals, vals[1:]))
    return dict(monotone=monotone, max_abs_error=float(max_err),
                passed=bool(monotone and max_err < 1e-9))


def theorem_marginal_rule() -> dict:
    """Sign of the exact DTI change when one dot is added to a *fresh* truth pixel.

    Layout: two truth pixels, 40 px apart.  A base dot sits 1 px from the first
    (credit 1/3), and **nothing** covers the second, so the added test dot
    charges the second truth pixel from scratch and its own credit is exactly
    ``k = max(1 - d/3, 0)`` with ``d`` an available integer-grid distance.

    The rule predicts an improvement iff ``k >= alpha * s``; the test walks the
    available credits and checks every sign, bracketing the measured break-even.
    """
    n = 61
    truth = np.zeros((n, n), bool)
    a = (10, 10)
    b = (50, 50)
    truth[a] = True
    truth[b] = True
    base = np.zeros((n, n), bool)
    base[a[0], a[1] + 1] = True           # credit 2/3 on truth a
    s = metric.dti_binary(base, truth).dti
    target = metric.marginal_inclusion_threshold(s)

    offsets = [(0, 1), (1, 1), (0, 2), (1, 2), (2, 2), (0, 3)]
    rows = []
    for dy, dx in offsets:
        d = float(np.hypot(dy, dx))
        k = max(0.0, 1.0 - d / metric.RADIUS_PX)
        test = base.copy()
        test[b[0] + dy, b[1] + dx] = True
        delta = metric.dti_binary(test, truth).dti - s
        rows.append(dict(dy=dy, dx=dx, distance_px=d, credit=k, delta_dti=delta,
                         rule_says_improve=bool(k >= target),
                         measured_improve=bool(delta > 0),
                         agree=bool((k >= target) == (delta > 0))))

    improving = [r["credit"] for r in rows if r["measured_improve"]]
    hurting = [r["credit"] for r in rows if not r["measured_improve"]]
    lo = max(hurting) if hurting else 0.0
    hi = min(improving) if improving else None
    bracketed = hi is not None and lo < target <= hi
    return dict(dti_before=s, threshold_alpha_s=target, samples=rows,
                measured_break_even_bracket=[lo, hi], bracketed=bracketed,
                all_signs_agree=bool(all(r["agree"] for r in rows)),
                passed=bool(bracketed and all(r["agree"] for r in rows)))


def main() -> int:
    t1 = theorem_denominator()
    t2 = theorem_binary_dominates()
    t3 = theorem_marginal_rule()
    table = []
    for s in (0.10, 0.20, 0.2778, 0.3195, 0.40):
        k = metric.marginal_inclusion_threshold(s)
        table.append(dict(dti=s, required_credit=k, max_distance_m=metric.max_distance_for_credit(k)))
    out = dict(theorem_1_fna_identity=t1, theorem_2_binary_dominates_soft=t2,
               theorem_3_marginal_inclusion=t3,
               threshold_table=table, all_passed=all(x["passed"] for x in (t1, t2, t3)))
    (evidence_dir() / "theorems.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))
    return 0 if out["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(
        "DEPRECATED/NO-GO: this legacy theorem script uses private gems58w logic. "
        "See docs/research/metric.md and the shared gems57 regression tests instead."
    )
