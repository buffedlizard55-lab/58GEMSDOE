# Session-7 answer: why the H33-family file scores highest on the GEMSDOE sites, and can we beat 0.2778?

**Evidence discipline.** 0.2778 is a *public leaderboard row* (`extradr19`, official board snapshot
2026-10-11 — `docs/LEADERBOARD.md`). It is **not** hash-bound to the GEMSDOE32 H33-2-B2 TIFF; that
page itself reports no organizer score for the file and calls 0.2747 a *model projection*
(`docs/research/why-02778.md`, IR-58-S4-01…04). What follows therefore explains the **method
family** that the best GEMSDOE-site artifacts belong to, not a claimed receipt.

## Why the dotted H19-5/H33 family is the best of the public attempts

The mechanism follows from the official metric (verified 2026-10-11 at
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ , "Performance metric" —
scoring example TP_w=3.00, FP_w=1.89, FN_w=2.00 → 0.60 reproduced in `tests/`):

```
TP_w = Σ_{g∈G} max_x p(x)·k(d(x,g))          k(d) = max(1 − d/300m, 0)
FP_w = Σ_x p(x)·(1 − max_g k(d(x,g)))
FN_w = |G| − TP_w
DTI  = TP_w / (0.2·(TP_w + FP_w) + 0.8·|G|)   (exact denominator identity)
```

1. **The max on the TP side makes mass a budget.** Each truth pixel buys at most one unit of
   cover, no matter how much prediction mass sits near it. A thick surface or a solid ribbon
   spends mass that the max has already covered — that mass contributes nothing to TP_w and
   degrades the denominator through FP_w at α = 0.2.
2. **Dotted thinning at spacing ≈ the 3-px kernel radius keeps the cover and drops the waste.**
   A dot 3 px along-strike from the next still reaches the same truth pixels the dropped interior
   pixels would have covered (k is 0 only at ≥ 3 px), so the cover per emitted pixel is maximal
   at dot spacing near 3 px. The GEMSDOE-family results table shows exactly this family on top:
   `dotted-h19-5-d2-8` (0.2600 owner-reported), `h27-4-solo-d28` (0.2708), `d28-poisson300m-offcat`
   (0.2600), and H33-2-B2 (0.2747 projection) — all 37k–44k dots at value exactly 1.0.
3. **Initial-round truth is the *new* faults only** ("faults that are not contained within the
   current public USGS database" — problem description). Dots on the mapped catalogue are
   therefore FP mass with near-zero expected cover of G. Every family leader emits **0 dots on the
   catalogue**; H33-2-B2 additionally deletes every dot within 2 px of it (44,090 → 37,654),
   which its own live-mirror estimates at +0.0049 — consistent with the metric arithmetic.
4. **Placement within about one pixel is what pays.** k falls 0.33 per 100-m pixel; a dot one
   pixel closer to a hidden fault wins the max against any other dot near the same truth pixel.
   The hidden set is scattered around real structure at σ ≈ 1.85 px (the GEMSDOE25 H28 inference
   the GEMSDOE32 page cites) — which is precisely the ribbon-lane brief.

So: the family wins because it is the best-known *mass allocator* on one detector surface
(pooled Hessian ridges of the 19-band stack). Its ceiling — about 0.27–0.28 on every public
attempt — is the recall of that detector surface: no allocator can cover a hidden fault the
ridge surface never approached.

## Can we score higher than 0.2778?

The metric says the gap is a **credit-density** problem: DTI = T/(0.2·(T+F)+0.8·|G|); at constant
mass, moving 0.2778 → 0.32 needs ≈ +20 % mean cover per emitted pixel. Three levers exist:

1. **New detector surface (recall).** Cover hidden faults the ridge family never approached.
   Session 7 tests this with H7-A: step edges (first-derivative) of the subsurface/magnetic
   structure surfaces — geometry and physics that no registered raster uses. *Locally
   unverifiable*: the hide-and-recover holdout's truth is the catalogue, and the measured
   correlation between that proxy and live scores is −0.037 (Spearman, 34 rasters). The canary
   AUC of these surfaces against the catalogue is ≈ 0.50 — no leakage, and also no catalogue
   signal, as expected for a discovery surface.
2. **Placement (σ-adaptive ribbons).** Measured this session on the blocked holdout: the
   U-selected σ-ribbon rule scores **HOLDOUT-DTI 0.04496** vs **0.02943** for the single-line
   control (whole-rule contrast, +0.0155, 95 % CI [0.0120, 0.0191], 4/4 quadrants) and beats the
   session-5 concordance file re-scored on the same instrument (0.03016). This lever is
   *measured*, not projected.
3. **Mass discipline.** Keep the credit bar U > 0 per class and 0 dots on the catalogue
   (B = 2 prune, the H33 mechanism).

**Bottom line.** Beating 0.2778 is possible in principle and the two real levers are (1)+(2);
(2) is validated on the holdout and is in the delivered file; (1) is the physically-motivated
discovery bet that the local instruments cannot score. Whether the delivered raster exceeds
0.2778 **cannot be known before an organizer receipt exists** — nothing on this site calls any
number a score. What we can say: no public artifact uses this detector surface or this emission
rule, the file is format-validated and uniqueness-screened against every reachable earlier
raster, and the mechanisms are chosen by the exact metric rather than by copying the saturated
family.

## What the delivered session-7 file does differently

| | best public family (d2-8 / H33-2-B2) | session-7 candidate |
|---|---|---|
| detector surface | Hessian ridges, pooled families | step edges (gradient maxima) on `depth_to_base_surf`, `cond_surf`, `tc` |
| emission geometry | dotted thinning at 2–3 px | per-segment parallel dotted lines, offsets ±σ̂ from the measured ridge→truth error (σ table), spacing 3 px |
| width rule | fixed | σ(x) by block × resolution × ridge type × relief class (H7-B), pattern chosen by exact U (H7-C gap-aware) |
| values | 1.0, 0 on catalogue | same |
| format | NaN-outside in some artifacts (portal `[0,1]` rejections) | all-finite, `[0,1]`, no nodata tag (the measured fix) |
| uniqueness | not screened against the full registry | pre-placement surface + final dots vs 694 byte-verified witnesses |
