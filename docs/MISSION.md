# Mission and current decision

## Mission

Maximize the probability of winning the DOE GEMS competition and own the outcome while following the evidence and no-go gates. The target is **geological faults indicative of geothermal resources**, not geothermal vents. This checkout is limited to the localization-error / ribbon-width lane: keep an existing ridge placement surface fixed and change only ribbon width/offset calibration around already-detected ridges. A width change cannot recover a fault absent from that fixed surface.

## Current decision — session 7, 2026-10-11 UTC

**NOT OK TO SUBMIT — DO NOT UPLOAD OR SELECT A SLOT.** The session-7 audited TIFF is an audit artifact renamed `review-only` without changing its pixel bytes. Its local format/range audit passes 19/19 checks, but this is not uniqueness clearance, holdout evidence, or portal acceptance. The candidate TIFF has `nodata=null`; the sample has `nodata=NaN`, so portal interpretation is unconfirmed. A separate ML-named TIFF was added to the base branch after this review; it was not reviewed or qualified here, is outside this ribbon-width task, and is labeled review-only in the per-file download index.

The direct final-dot measurement against one hash-pinned prior registry raster is **1.0000 within 3 px**, greater than the user's literal **0.70** stop. This is a duplicate/drift protocol stop, not proof of byte/pixel copying. The witness's 3-px dilation covers every cell in the bridged allowed footprint. The old chance-corrected `RATIFIED-UNIQ-v1` record is historical and does not waive this current literal stop.

The current inventory freshness audit is `BLOCKED_NOT_EXHAUSTIVE`; the earlier 703-raster scan is complete only for its frozen scope. No candidate-specific pre-placement surface exists or was measured. No current HOLDOUT-DTI, evaluator result, withheld-positive count, defensible 95% CI, σ table, simulated class gain, or feature-alone leakage canary was measured. No score or projection is reported. This review used zero experiments, zero slots, and made zero uploads.

The current artifact-specific run card and audit are [`../evidence/58gemsdoe_unique_ribbon/run_card.json`](../evidence/58gemsdoe_unique_ribbon/run_card.json) and [`../evidence/58gemsdoe_unique_ribbon/audit.json`](../evidence/58gemsdoe_unique_ribbon/audit.json). The detailed review is [`research/session7_review_20261011.md`](research/session7_review_20261011.md); the ranked proposal-only width hypotheses are in [`research/hypotheses_new.md`](research/hypotheses_new.md).

## Evidence labels

- `PUBLIC-LEADERBOARD-SNAPSHOT` is a dated participant row, not an artifact score.
- `HOLDOUT-DTI` requires `gems57.evaluate_holdout`, evaluator/version, withheld-positive count, the prescribed buffered whole-segment holdout, protocol, and a defensible 95% confidence interval.
- `ORGANIZER-CONFIRMED` requires an organizer receipt/hash crosswalk to the exact TIFF.
- A local format check, an owner-maintained data mirror hash, or matching the sample's outside-footprint representation is neither portal acceptance nor score attribution.
- The dated board row at 0.2778 belongs to participant `extradr19`; no verified receipt/hash crosswalk links it to the GEMSDOE32 H33 raster. The H33 owner page calls 0.2747 a projection and the file unscored. The cause of the participant's result is unknown from the public row alone.

Read [`../PROMPT.md`](../PROMPT.md), [`../README.md`](../README.md), and [`../REMAINING_WORK.md`](../REMAINING_WORK.md) in full at session start. For current next work see [`IRREGULARITIES.md`](IRREGULARITIES.md), [`SUBMISSION_GUIDE.md`](SUBMISSION_GUIDE.md), [`LEADERBOARD.md`](LEADERBOARD.md), and [`SOURCES.md`](SOURCES.md). Never select or use a slot during research.
