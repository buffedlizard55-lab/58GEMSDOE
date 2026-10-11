# Submission guide — current artifact is stopped

> **NOT OK TO SUBMIT — DO NOT UPLOAD OR SELECT A SLOT.** The TIFF linked here is downloadable for audit only. It is not a qualified competition submission. A local format pass is not organizer/portal acceptance.

## Current artifact and verdict

- GeoTIFF: [`58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif`](downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif)
- ZIP containing one TIFF: [`58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip`](downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip)
- Per-file metadata: [`58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json`](downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json)
- Artifact SHA-256: `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448` (49,139,380 bytes).
- Proposed internal name only: `58GEMSDOE-ribbon-sparse-diagnostic-20261011T182511Z`. This is **not authorized** for the portal.
- Proposed note (62/140 characters): `Diagnostic only; uniqueness and holdout gates are not cleared.` This is **not a submission instruction**.

The previous filename contained `unique`, but there was no supporting uniqueness measurement when it was named. It has been renamed review-only; the raster pixel bytes did not change. Keep the artifact only for audit/reproducibility. Its download link does not indicate eligibility.

A separate ML-named [TIFF](downloads/gems58-ml-binary-ridge-20261012T000000Z.tif) and [ZIP](downloads/gems58-ml-binary-ridge-20261012T000000Z.zip) were added to the base branch after the session-7 review. They were not generated, evaluated, or qualified in this review, and they do not satisfy this checkout's fixed-surface ribbon-width scope. The complete download index labels each separately; **do not submit or run their generation scripts under the current prompt.**

## Gate-by-gate status

| Gate | Result | Evidence and limit |
|---|---|---|
| On-disk format/range | **19/19 LOCAL-FILE-AUDIT checks pass** | One-band float32; EPSG:32611; 3730×3292; sample CRS/shape/transform match; values finite in [0,1]; positives exactly 1.0; outside-footprint positives zero; no positive on the bridged mapped catalogue; ZIP round trip succeeds. This establishes only the recorded local checks. |
| Nodata metadata | **Difference flagged** | Candidate has `nodata=null`; sample has `nodata=NaN`. Candidate values are finite everywhere. Portal acceptance of this representation is unconfirmed. |
| Pre-placement registry surface | **NOT MEASURED** | No candidate-specific scalar surface, generating script, or pre-placement receipt exists for this diagnostic. |
| Final-dot literal uniqueness rule | **FAIL — STOP** | **REGISTRY-MEASUREMENT:** 1.0000 of final dots lie within 3 px of a hash-pinned registry witness; the user's stop threshold is >0.70. This is a duplicate/drift protocol stop, not a byte- or pixel-copying claim. |
| Registry freshness | **BLOCKED_NOT_EXHAUSTIVE** | The prior 703-raster scan is complete only for its frozen scope; current exhaustive accessible-registry clearance is not established. One directly observed literal trigger already stops this file. |
| HOLDOUT-DTI | **NOT MEASURED** | No shared `gems57.evaluate_holdout` run for this TIFF; no evaluator result, withheld-positive count, or 95% CI. |
| σ table / gain by class | **NOT MEASURED** | No current artifact-specific calibration result. |
| Feature-alone leakage canary | **NOT RUN** | AUC >0.90 remains a leakage stop until explained. |
| Organizer score/acceptance | **NONE / NOT CONFIRMED** | No hash-bound organizer receipt or portal response exists. Do not infer a score or acceptance. |
| Experiments / slots / uploads | **0 / 0 / 0** | No experiment, slot selection, or upload occurred during this review. |

## The direct overlap stop

The hash-pinned witness is `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`, SHA-256 `03d619fa75689b48bd3eb4f74c3fa529a9b04c19bd716e15640d910baf3d5a90`. The public blob matches the owner-maintained registry pin; it is not independent organizer provenance. The witness has 5,167,373 positive cells across all 5,167,373 cells in the bridged allowed footprint; 3-px dilation leaves zero uncovered cells. The current file's final-dot overlap was measured directly at 1.0000. This satisfies the active literal >70% stop. Rank correlation with the all-positive constant witness is undefined; the overlap trigger is decisive. See [`evidence/58gemsdoe_unique_ribbon/audit.json`](../evidence/58gemsdoe_unique_ribbon/audit.json) and [`evidence/58gemsdoe_unique_ribbon/run_card.json`](../evidence/58gemsdoe_unique_ribbon/run_card.json).

Do not replace this literal test with the chance-corrected interpretation retained in old session-5 docs. Do not generate a replacement candidate under the same active stop, and do not use a competition slot.

## The reported portal `[0,1]` error

The reported error's cause is **unknown**. The repository has no hash-bound portal response, submission ID, or validation receipt establishing whether NaN, an out-of-range value, or another issue caused it. A local all-finite `[0,1]` check is a precaution, not a causal diagnosis or an acceptance guarantee. Candidate nodata metadata also differs from the sample (`null` versus `NaN`), and the effect of that difference has not been tested at the portal. See [`docs/IRREGULARITIES.md`](IRREGULARITIES.md#session-7-verified-blockers-and-corrections) and [`docs/SOURCES.md`](SOURCES.md#portal-01-report--unresolved).

## Score attribution: 0.2778

The dated public leaderboard observation ties 0.2778 to participant `extradr19`, not to a local raster hash. The GEMSDOE32 owner-maintained H33 page calls its file unscored and describes 0.2747 as a projection; no organizer receipt/hash crosswalk links H33 to `extradr19`. The actual cause of the public 0.2778 score is unknown from the public row. It is not an ORGANIZER-CONFIRMED score for this repository. See [`docs/research/why-02778.md`](research/why-02778.md) and [`docs/LEADERBOARD.md`](LEADERBOARD.md).

## Future qualification — only if the active stop no longer applies

Any future authorized research would have to be preregistered and stay in the ribbon-width/localization-error lane: hold the ridge-placement surface fixed; vary only width/offset calibration; fit on training-only blocks; test each feature alone; use buffered whole-segment holdouts; derive catalogue features only from visible faults; mask visible faults pixel-exactly; use pooled DTI with α=0.2, β=0.8, 300 m triangular kernel; and reuse shared `gems57.evaluate_holdout` and `gems57.submission_writer`. Report HOLDOUT-DTI with evaluator/version, withheld-positive count, protocol, and defensible 95% CI. Stop on a literal uniqueness trigger, stale/incomplete inventory, AUC >0.90, invalid holdout, or unsupported/nonpositive result. Budget is at most three experiments or two hours. **No slot selection or upload during research.**

Before any eventual competition action, require a complete current inventory, pre-placement surface measurement, final-dot measurement, all local format checks (including an explicitly accepted nodata representation), leakage/holdout evidence, the exact artifact hash, and a human/organizer authorization step. A public leaderboard row is not a file score; an organizer receipt/hash crosswalk is required for ORGANIZER-CONFIRMED.

## Primary-source links for manual review

- [Official problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login may be required.
- [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — dynamic; the repository contains a dated snapshot, not a fresh fetch from this session.
- Complete source ledger: [`docs/SOURCES.md`](SOURCES.md).
