# Mission and current decision

## Mission

Win the DOE GEMS competition by improving the localization of **geological faults indicative of
geothermal resources** in the GeoDAWN test region. This is not geothermal-vent detection. Keep the
placement surface fixed and work only in the localization-error / ribbon-width lane described in
[`../PROMPT.md`](../PROMPT.md); a width change cannot recover a fault absent from the fixed ridge
surface.

## Current decision — 2026-10-11 UTC

**NOT OK TO SUBMIT — DO NOT UPLOAD OR SELECT A SLOT.** The available candidate is an audit artifact.
Its 15/15 local format checks do not establish portal acceptance. The reported `[0,1]` rejection is
unresolved because no portal response or receipt is tied to the candidate's SHA-256.

The candidate-matched 702-raster scan recorded 81 literal 3-px forward-overlap triggers
(27 informative, 54 saturated/vacuous), `unique: false`, and `stop_required: true`. It applies only
to the indexed public-inventory snapshot; it does not certify an organizer-wide inventory. The
separate freshness audit is not current clearance. There is no qualifying pre-placement surface
receipt, no promotion-grade leakage canary, and no reportable shared-evaluator holdout for this
candidate. **The top-ranked proposal is not validated.** No trigger, experiment cap, or scope
restriction is waived.

## Evidence levels

- `PUBLIC-LEADERBOARD-SNAPSHOT` is a dated participant row, not an artifact score.
- `HOLDOUT-DTI` requires `gems57.evaluate_holdout`, evaluator/version, withheld-positive count, the
  prescribed spatial holdout, and a defensible 95% confidence interval.
- `ORGANIZER-CONFIRMED` requires an organizer receipt/hash crosswalk.
- A local format check or matching the official sample's NaN-outside representation is neither
  portal acceptance nor score attribution.

See [`IRREGULARITIES.md`](IRREGULARITIES.md), [`SUBMISSION_GUIDE.md`](SUBMISSION_GUIDE.md),
[`LEADERBOARD.md`](LEADERBOARD.md), and the generated [status page](index.html) before using any
artifact. The repository's complete research contract remains in [`../PROMPT.md`](../PROMPT.md).
