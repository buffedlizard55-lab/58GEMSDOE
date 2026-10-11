# Official DTI metric and exact marginal-utility rule

The competition metric below is transcribed from the official [DrivenData problem description, “Performance metric”](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The shared implementation and its brute-force tests are under `src/gems57/` and `tests/`.

```text
R      = 300 m = 3 pixels at 100 m resolution
k(d)   = max(1 - d / R, 0)                           (triangular kernel)

TP_w   = sum over truth cells g of max over predictions x of p(x) k(d(x,g))
FP_w   = sum over predictions x of p(x) [1 - max over truth cells g of k(d(x,g))]
FN_w   = |G| - TP_w

alpha  = 0.2      beta = 0.8
DTI    = TP_w / (TP_w + alpha FP_w + beta FN_w + epsilon)
```

Let `T = TP_w`, `F = FP_w`, and `G = |truth|`. Because `FN_w = G − T` and `1 − beta = alpha`,

```text
D = T + alpha F + beta(G - T)
  = alpha(T + F) + beta G
DTI = T / D
```

This denominator identity is exact. It does **not** imply that one additional prediction pixel always adds exactly `alpha` to the denominator: max-credit interactions may make its marginal truth credit smaller than its self-credit.

## Exact utility for a pattern change

For a proposed change to the prediction pattern, compute exact metric differences under the same truth, visible-fault mask, and scored domain:

```text
DeltaTP = TP_after - TP_before
DeltaFP = FP_after - FP_before
s       = DTI_before
U       = (1 - alpha*s) * DeltaTP - alpha*s * DeltaFP
```

Since `D_after = D_before + alpha(DeltaTP + DeltaFP)`, the change increases DTI exactly when `U > 0` (ties when `U = 0`). `DeltaTP` and `DeltaFP` must be measured after applying the metric's maxima; overlapping predictions do not receive additive truth credit.

### The limited isolated-dot shortcut

For one newly added binary dot with self-credit `k` that captures fresh truth credit, `DeltaTP = k` and its own false-positive mass is `DeltaFP = 1 − k`. Only in this special case does the exact condition reduce to

```text
U = k - alpha*s > 0    iff    k > alpha*s.
```

For a redundant dot, `DeltaTP` can be less than `k`; the shortcut is not sufficient. For an interacting group of ribbon dots, compute the setwise `DeltaTP` and `DeltaFP` with the shared exact metric rather than summing independent dot utilities. The regression test `test_redundant_dot_does_not_use_isolated_threshold` covers the counterexample.

The conditional threshold at any reference index `s` is `k > 0.2s`, or `d < 300(1−0.2s)` metres for the triangular kernel. For context only, the official public board observed on 2026-10-11 listed DARD at 0.3195 (rank 8); this is not the current leader and not a local artifact score. See [`docs/LEADERBOARD.md`](../LEADERBOARD.md). No projected score or local holdout value is implied by this algebra.

## Scope of this repository's holdout

The shared local evaluator scores pooled DTI on buffered whole-component hide-and-recover folds built from the public catalogue. That is a development proxy, not the organizer's private expert-labelled test set. Do not call a proxy DTI a leaderboard prediction or use it to attribute a score to another team's TIFF.
