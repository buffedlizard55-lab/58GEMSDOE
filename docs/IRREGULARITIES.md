# Current irregularities and stop decision

**Reviewed:** 2026-10-11 UTC. **Decision: NOT OK TO SUBMIT — DO NOT SUBMIT.** No experiment, holdout,
new TIFF emission, slot selection, upload, or portal check was performed in this review. This page is
the concise current record; detailed legacy run records remain in `evidence/` and are not promotion
evidence.

## Active blockers and corrections

1. **Final-dot literal uniqueness stop.** The candidate-matched scan in
   [`evidence/ribbon/uniqueness_full_inventory.json`](../evidence/ribbon/uniqueness_full_inventory.json)
   checked 702 indexed rasters in its recorded accessible public-inventory snapshot. It reports
   **81 literal forward-overlap firings** (27 informative, 54 saturated/vacuous),
   `unique: false`, `stop_required: true`. The worst literal forward overlap is 1.0 against
   `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`; 27 informative
   firings remain even when saturated witnesses are distinguished. The worst rank correlation is
   below 0.90, but that does not override the independent overlap gate. No chance-corrected reading,
   dense-raster rule, or reversed overlap direction is authorized to waive a literal trigger.
2. **Inventory freshness and scope are not cleared.** The count of 702 means the saved scan covered
   its indexed snapshot; it is not evidence of a current, organizer-wide or private-repository
   inventory. [`evidence/registry_freshness_audit.json`](../evidence/registry_freshness_audit.json)
   records `fresh_current_inventory: false` and `BLOCKED_NOT_EXHAUSTIVE`. A complete scan of that
   saved set is not current inventory clearance. No new scan was run in this review.
3. **Pre-placement surface gate missing.** No qualifying pre-placement surface receipt for the exact
   frozen candidate surface is present. The final-dot scan cannot substitute for this independent
   pre-placement check.
4. **No promotion-grade feature-alone leakage canary.** Historical canaries use old/legacy
   diagnostics. A current qualification receipt with feature-by-feature leakage checks is absent.
5. **No reportable current HOLDOUT-DTI.** The candidate's local `gems58w-pooled-hide-v1` diagnostic
   used a legacy evaluator/protocol. Its saved score/interval is not the required result from
   `gems57.evaluate_holdout`; it does not satisfy the current buffered whole-segment, visible-only,
   pixel-exact-mask protocol and defensible 95% CI. Do not cite it as current performance.
6. **Portal `[0,1]` rejection unresolved.** The candidate's custom local emission receipt reports
   15/15 local format checks, but no portal response or receipt ties the reported rejection to this
   TIFF's SHA-256. The organizer sample's NaN-outside representation does not prove this candidate
   passes; nor does it establish that NaNs caused the reported rejection. Cause and exact candidate
   identity remain unknown. See [`SUBMISSION_GUIDE.md`](SUBMISSION_GUIDE.md).
7. **Public-board score attribution corrected.** The 2026-10-11 public snapshot shows
   `extradr19` at rank 23 / 0.2778 and DARD at rank 9 / 0.3195; an earlier same-day snapshot had DARD
   at rank 8. Those are participant rows, not artifact receipts. GEMSDOE32's owner page marks
   H33-2-B2 `UNSCORED`, calls 0.2747 a projection, and provides no organizer hash crosswalk. The
   H33 “0.2778” attribution is unsupported. See [`LEADERBOARD.md`](LEADERBOARD.md) and
   [`research/why-02778.md`](research/why-02778.md).
8. **Untried hypothesis list corrected.** Magnetic/geodetic signed-offset work, adaptive scalar
   widths, and along-strike spacing already have legacy implementations or measurements. They are
   excluded from the revised ranked list. Three specific alternatives are documented in
   [`research/hypotheses_new.md`](research/hypotheses_new.md); the top candidate is **not validated**
   and no holdout may run before the uniqueness gate clears.
9. **Historical site/status records were stale.** Older pages described a 694/695 scan, promoted
   NaN matching as proof of portal acceptance, or showed a signed-offset idea as untried. The current
   root status, per-file download index, and archived ribbon pages now reflect this review. Older
   records remain historical, not current qualification.
10. **Official deadline sources disagree.** The competition homepage and September 2026 rules PDF
    show different cutoff times. Follow the earlier cutoff unless the organizer clarifies; this is a
    planning precaution, not a verified resolution. Sources are listed in [`SOURCES.md`](SOURCES.md).

## Artifact facts

The current downloadable TIFF is `gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`, SHA-256
`ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd`, with 40,768 positive pixels.
Its emission record is [`evidence/ribbon/emission.json`](../evidence/ribbon/emission.json). The
independent on-disk [`file_audit.json`](../evidence/ribbon/file_audit.json) passes 11/11 local checks
for the grid, float32 pixels, footprint/mask, values, hashes and ZIP round-trip; this does not resolve
the portal report or clear submission eligibility. The file and ZIP must be labeled
**NOT OK TO SUBMIT — REVIEW ONLY** wherever linked.

## Scope and safe next action

Remain in the localization-error/ribbon-width lane, keep the ridge surface fixed, and preserve the
three ranked proposals in [`research/hypotheses_new.md`](research/hypotheses_new.md). Do not switch to
fault detection or another lane. **Do not run a holdout, emit/promote another TIFF, choose a slot, or
upload while the literal stop or stale/incomplete inventory condition remains.**

The next safe action is to refresh and independently audit the registry inventory, then evaluate the
exact pre-placement surface gate and final-dot gate using the literal protocol. Stop on any trigger;
do not invent a waiver. Only after these gates and a promotion-grade leakage canary clear can a
preregistered holdout be considered, within the three-experiment/two-hour cap and using the shared
`gems57.evaluate_holdout` / `gems57.submission_writer` path.

For every future numeric result, preserve evaluator/version, withheld-positive count, protocol,
artifact/pixel hashes, and a defensible 95% CI under `HOLDOUT-DTI`. Use `ORGANIZER-CONFIRMED` only
with an organizer receipt/hash crosswalk. No slot is selected; negative evidence is a valid outcome.
