# Remaining work (reviewed 2026-10-11 UTC)

## Decision

**NOT OK TO SUBMIT — DO NOT UPLOAD OR SELECT A SLOT.** The existing 40,768-positive TIFF is an
audit/review artifact, not an eligible submission. Its local format receipt does not imply portal
acceptance. No new TIFF, experiment, holdout, weekly slot decision, or upload was made in this review.

## Evidence already checked

- **H33 attribution:** the public board's 0.2778 row belongs to participant `extradr19` (#23 in the
  2026-10-11 observation). GEMSDOE32's owner page marks H33-2-B2 UNSCORED; 0.2747 is a projection.
  There is no organizer receipt/hash crosswalk tying either value to H33. See
  [`docs/research/why-02778.md`](docs/research/why-02778.md).
- **Candidate artifact:** 40,768 positives, SHA-256
  `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd`, 15/15 checks in its local
  emission receipt and 11/11 checks in the independent TIFF/ZIP audit. These verify local bytes/grid,
  not portal acceptance or submission eligibility.
- **Final-dot uniqueness:** the recorded 702-raster accessible public-inventory scan is negative:
  81 literal triggers, including 27 informative firings; `unique: false`, `stop_required: true`.
  The scan is scoped to its indexed snapshot, not a complete organizer-wide inventory. The freshness
  audit is not current clearance. The literal hard-stop rule remains in force.
- **Pre-placement uniqueness:** no qualifying candidate-specific surface receipt is present.
- **Portal rejection:** the reported `[0,1]` error is unresolved. The repository has no portal error
  payload or acceptance receipt tied to this TIFF hash. NaNs outside the official sample footprint do
  not prove that this TIFF passes portal checks.
- **Holdout and hypotheses:** the existing `gems58w` score and signed-offset result use a legacy
  evaluator/protocol. They are not promotion-grade `HOLDOUT-DTI`. The three listed proposals were
  audited against code/evidence; signed bias, adaptive scalar widths, and along-strike spacing are
  excluded because prior implementations or measurements exist. The new top proposal is **not
  validated**.

## Safe next steps — in order

1. Keep every downloadable TIFF/ZIP explicitly marked **NOT OK TO SUBMIT — REVIEW ONLY**. Refresh
   the site status only from hash-bound local receipts; do not imply portal eligibility from a local
   preflight.
2. Obtain and record an organizer-wide/current registry snapshot and validate the feature inventory
   freshness. Do not try to clear the recorded 81 literal firings using chance correction, a dense
   raster exemption, a reverse overlap, or a changed threshold.
3. Re-run the pre-placement surface uniqueness comparison for the exact frozen surface against that
   current inventory. Do not emit a candidate unless the literal gate clears.
4. Only after steps 2–3 clear, run the promotion-grade feature-alone leakage canary and a preregistered
   buffered whole-fault-segment holdout using visible-catalogue-only features, pixel-exact visible-fault
   masking, pooled α=0.2/β=0.8 DTI, a 300 m triangular kernel, `gems57.evaluate_holdout`, and
   `gems57.submission_writer`. Test features individually; report withheld positives and a defensible
   95% interval. The currently ranked top hypothesis remains untested and cannot be run while the
   uniqueness stop is active.
5. If a future exact candidate passes every gate, record its file and decoded-pixel hashes, validator
   receipt, final-dot receipt and qualification receipt before anyone considers a slot. Do not select
   a weekly slot or upload under the current decision.
6. If a portal error recurs in a separately authorized submission, preserve the exact portal
   response/receipt, submission ID, timestamp and TIFF SHA-256. Until then, the `[0,1]` rejection is
   unresolved; do not speculate about whether NaNs, bounds or another validation stage caused it.

## Review maintenance

- Keep [`README.md`](README.md), [`docs/index.html`](docs/index.html),
  [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md),
  [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md), and the archive notice in
  [`docs/ribbon/`](docs/ribbon/) consistent with this decision.
- Keep leaderboard rows labeled `PUBLIC-LEADERBOARD-SNAPSHOT`; only a receipt/hash crosswalk can
  support an artifact attribution or `ORGANIZER-CONFIRMED` score.
- Preserve negative results and the governing [`PROMPT.md`](PROMPT.md). Any future PR must be made
  from this session's fixed branch; the requested create-and-merge action is tracked separately from
  research eligibility.
