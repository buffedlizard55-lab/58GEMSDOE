# The official metric, transcribed

Source: **DrivenData competition 306, problem description, "Performance metric"**
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>

```text
R      = 300 m = 3 pixels at 100 m resolution
k(d)   = max(1 - d / R, 0)                                    (triangular kernel)

TP_w   = sum_{g in G}  max_{x : d(x,g) <= R}  p(x) * k(d(x,g))
FP_w   = sum_{x : p(x) > 0}  p(x) * [1 - max_{g in G} k(d(x,g))]
FN_w   = sum_{g in G}  [1 - max_{x : d(x,g) <= R} p(x) * k(d(x,g))]

alpha  = 0.2      beta = 0.8

DTI    = TP_w / (TP_w + alpha * FP_w + beta * FN_w + eps)
```

Two organizer rules change what these sums mean in practice:

1. **Known-fault masking.** Pixels on the mapped USGS/INGENIOUS catalogue are removed from the
   prediction *and* from the truth before the kernel is applied, so a prediction on a mapped fault
   is inert and cannot radiate credit into the scored domain. Organizer clarification, community
   thread 11516 (recorded second-hand; see `registry/sources.json` S3).
2. **The scored truth is faults the catalogue does not contain.** The example submission shipped by
   the organizers (`data/official/sample_submission.tif`, sha256 `2176d08e…`) is literally the
   catalogue: 1.0 on the 60,988 mapped pixels, 0 elsewhere inside the footprint, `NaN` outside.

## Collapse to a one-line index

Because `FN_w = |G| - TP_w` exactly,

```text
DTI = TP / (TP + alpha*FP + beta*(|G| - TP))
    = TP / (alpha*(TP + FP) + beta*|G|)                          (A)
```

(A) is the form every script in this repository uses; `scripts/verify_theorems.py` theorem 1 checks
it to `0.0` absolute difference on a random grid.

## Why the index is a *distance* filter

For one emitted pixel of unit mass the pair `(p, 1-p)` sums to one: the pixel contributes
`k(d)` to `TP` (via the per-truth maximum) and `1 - k(d)` to `FP`. Adding it therefore moves
`TP + FP` by exactly **1** and the denominator by exactly **0.2**, wherever it lands. Writing `s`
for the index before the addition,

```text
(T + k) / (D + 0.2)  >=  T / D      <=>      k >= alpha * s         (B)
```

At the owner-stated leader `s = 0.3195` this is `k >= 0.0639`, i.e. **within 280.8 m** of a scored
truth pixel. Nothing about being *on* the trace is worth anything beyond credit 1; being 290 m away
is worth 0.033 and does not pay. This is why the group's empirical `dot_thin` family located the
optimum at ≈ 2.4–2.8 px spacing (GEMSDOE32 `docs/research/why-d28-scored-026.md`) and why every
competitive artifact is binary, sparse and off-catalogue.

## Why binary beats graded

For the support-scaled family `p_lambda = lambda * b` with `b` binary and `lambda in (0, 1]`,

```text
DTI(lambda) = lambda * T / (alpha * lambda * (T + F) + beta * G)
dDTI/dlambda = alpha * T * G / (alpha*lambda*(T+F) + beta*G)^2  >  0
```

so the graded raster is strictly dominated by its own thresholded support. **Emit exactly 1.0.**
Machine check: theorem 2, max abs error `5.55e-17`.
