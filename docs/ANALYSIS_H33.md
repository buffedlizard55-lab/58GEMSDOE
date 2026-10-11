# Why did the top-scoring prior submission score 0.2778? (analysis, unverified)

**Question (brief):** Why did `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32, 0.2778, user-supplied) score highest, and can we beat 0.2778?

## What we can and cannot establish

| Item | Status |
|---|---|
| The submission's raster | **Cannot read.** GEMSDOE32 (S20) is unreachable. |
| Its method and code | **Cannot read.** No source is accessible. |
| Its score | **User-supplied only.** No DrivenData receipt was available (ORGANIZER-CONFIRMED label not possible). |
| Its footprint (NaN vs zero outside the valid area) | **Unknown.** The name suffix `-zeros` hints that the file wrote zeros, not NaN, outside the footprint. This is a guess from the name. |
| What a score of 0.2778 implies | The score comes from the organizer's metric (S3, unreachable). Our metric is an approximation (`gems/metric.py`). |

So a full causal answer is not possible from this sandbox. Below is a reasoned hypothesis, labelled as such.

## Hypotheses for why it scored well (ranked by how much they would matter)

1. **Tolerance-aware dots, not one-pixel lines.** The metric gives partial credit within 300 m (S8, section 17). A dotted or buffered line places mass where a one-pixel trace would miss. The name "h33-2-b2" and the cluster of "dotted" submissions near 0.25–0.28 on the user-supplied list are consistent with this, but do not prove it.
2. **Calibration of the false-positive mass.** With α=0.2 and β=0.8, a false-positive costs 0.2 and a false-negative costs 0.8. Scores near 0.28 suggest that the high-scoring submissions keep recall high while keeping diffuse false-positive mass small. This is a property of the metric, which we could not verify.
3. **Footprint handling.** If the file wrote zeros outside the valid area (the `-zeros` suffix), the zeros add no false positives, so this does not hurt the score. NaN handling matters for validity, not for the score. A NaN in the output is one plausible cause of the user-reported "must be in range [0,1]" error, so zero encoding may avoid that error (unverified). Check whether the organizer's example_submission.tif uses NaN (S8 says it does; unverified).
4. **Name-suffix variants.** The leaderboard has many entries with `-nan` and `-zeros` suffixes that score similarly. Those suffixes probably record a NaN-vs-zero output choice, not a different model. Entries that differ only by suffix are a useful controlled comparison, but we cannot see them.

## Can we beat 0.2778?

Not established. Honest answer:
- The best-supported lever is the one the metric rewards: tolerance-weighted, calibrated, graded dots or ribbons around candidate traces, whose width is set by the measured localization error. This is the "ribbon lane" in the brief.
- We cannot test it on the holdout yet, so there is no evidence that it beats 0.2778. Projecting a score would violate the "never write a projection as a score" rule.

## What would settle this (needed access)

1. The competition rasters (S5, S14): needed to build the holdout and run the metric.
2. The official metric and worked example (S3): needed to validate `gems/metric.py`.
3. The GEMSDOE32 raster or its method notes (S20): needed to confirm the footprint and dot hypotheses.
