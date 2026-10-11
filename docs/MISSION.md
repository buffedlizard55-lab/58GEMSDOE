# Mission brief — GEMS competition 306

This is the concise project charter. The full standing protocol is in [`../PROMPT.md`](../PROMPT.md) and is embedded in [`../README.md`](../README.md).

## Objective and lane

Maximize the probability of winning the DOE GEMS Prize while owning the result. The organizer's stated task is to predict geological faults indicative of geothermal resources, not geothermal vents. This checkout is limited to the **ribbon-width lane**: calibrate emitted ribbon width and offsets to measured ridge-localization error. Do not change to another detection lane or select a competition slot.

## Current decision

**NOT OK TO SUBMIT — DO NOT SUBMIT.** The existing downloadable raster is a diagnostic only. A 695-raster frozen scan checked 694 rasters and found 100% of the candidate dots within 3 px of one full-footprint-positive prior raster, above the literal 70% stop threshold. The registry is stale/incomplete; the candidate-specific pre-placement gate and current buffered holdout are not cleared. Local format checks do not establish uniqueness, portal acceptance, or an organizer score. No new TIFF or model experiment was run in this review.

## Required operating rules

1. Before implementation, review `REMAINING_WORK.md` and prior experiment receipts; rank 3–5 untried within-lane hypotheses by expected relative benefit, uncertainty, and cost; define experiments and stopping criteria.
2. Compare the placement surface before emission and the final dots against the registry. Stop on Spearman rank correlation >0.90 or >70% forward dot overlap within 3 px of any one raster. A stale or incomplete scan is not a pass.
3. Reuse the cached feature stack plus shared `gems57.evaluate_holdout` and `gems57.submission_writer`. Do not maintain private metric/evaluator/writer forks. Hold out buffered whole fault segments, build catalogue-derived context from visible faults only, mask visible faults pixel-exactly, and use pooled DTI (α=0.2, β=0.8, 300 m triangular kernel).
4. Test each feature alone; AUC >0.90 is leakage until explained. For any pattern change, compute exact marginal ΔTP and ΔFP with max-credit interactions; the isolated-dot `k > αs` shortcut is not a general ribbon rule.
5. Label performance claims HOLDOUT-DTI with shared evaluator version, withheld-positive count, protocol, and a defensible 95% CI—or ORGANIZER-CONFIRMED from a receipt/hash crosswalk. Record public-board observations separately; never attribute a public row to a file without a receipt/crosswalk.
6. Stop after three experiments or two hours. Never pick or use a competition slot.
7. End with the required JSON run card, exact raster hash, validator evidence, registry status, ≤140-character note/name, and unambiguous promote/negative decision.

## Current public score context

The official public leaderboard snapshot observed on 2026-10-11 UTC showed xiaofanhu at rank 1 (0.4133), DARD at rank 8 (0.3195), and extradr19 at rank 23 (0.2778). These are dynamic public-board rows, not results for a local TIFF. The GEMSDOE32 owner-maintained H33 page says **NO ORGANISER SCORE EXISTS** for the named H33 raster and calls 0.2747 a model projection. No receipt/hash crosswalk attributes 0.2778 to that artifact. See [`LEADERBOARD.md`](LEADERBOARD.md) and [`research/why-02778.md`](research/why-02778.md).

## Sources

- [Official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- Dated source/availability verification: [`SOURCES.md`](SOURCES.md)
