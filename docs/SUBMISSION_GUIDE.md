# Submission guide — current file is review-only

> **NOT OK TO SUBMIT — DO NOT UPLOAD OR SELECT A SLOT.** The TIFF linked below is an audit artifact,
> not a cleared competition submission. A local preflight pass is not portal acceptance.

## Current downloadable candidate

Named by [`evidence/ribbon/emission.json`](../evidence/ribbon/emission.json); the rendered status is
[`docs/RUN_CARD.json`](RUN_CARD.json) (`site_verdict: NOT_OK_TO_SUBMIT`).

- TIFF: [`gems58-concordance-ribbon-40768-20261011T160514Z.tif`](downloads/gems58-concordance-ribbon-40768-20261011T160514Z.tif)
- ZIP: [`gems58-concordance-ribbon-40768-20261011T160514Z.zip`](downloads/gems58-concordance-ribbon-40768-20261011T160514Z.zip)
- SHA-256: `f709b6f12d5188e34aa3aed3b83d785b97a232224692dcdfffedaa009dee9d0d` (427,919 bytes)
- Recorded positive pixels: 40,768.
- The session-3 diagnostic `gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`
  (`ecf833f8…2711dd`) is retained beside it as an archived artifact, with its own audit receipt in
  [`evidence/ribbon/archive-s3/`](../evidence/ribbon/archive-s3/).

Both files are available **for review and reproducibility only**. The directory index at
[`downloads/`](downloads/index.html) labels each TIFF/ZIP separately. Do not upload this candidate,
select a weekly slot, or infer eligibility from the existence of a download button.

## What local validation establishes — and what it does not

The candidate's emission receipt records 15/15 checks in a local format/range preflight. A separate
[on-disk TIFF/ZIP audit](../evidence/ribbon/file_audit.json) records 10/10 checks for the decoded
float32 grid, official-sample alignment, in-footprint `[0,1]` values, NaN outside mask, pixel count,
file hash and ZIP round-trip, and publishes the decoded-pixel SHA-256 it computed. That emission
receipt records no decoded-pixel hash of its own, so the audit reports the binding as computed rather
than claiming a verified match; it is not a silent pass. This is local artifact verification only—not
portal validation, uniqueness clearance, organizer scoring, or submit authorization. Neither receipt
is an organizer response. The final-dot registry scan independently records 83 literal overlap
triggers (29 informative, 54 against witnesses whose 3 px dilation covers ≥ 99 % of the footprint)
over 703 indexed rasters, and a hard stop. The candidate-specific pre-placement surface gate, current inventory
freshness clearance, promotion-grade leakage canary and shared-evaluator holdout qualification are
not cleared. See the [current irregularities log](IRREGULARITIES.md) and [status page](index.html).

The repository's stricter shared validator and the custom emission preflight have different rules
about outside-footprint values. The candidate and official sample use NaNs outside the evaluation
footprint; the shared writer's standard output is finite with zero outside. Neither a local pass nor
matching the sample's NaN-outside representation proves that this exact candidate will pass the
portal. In particular, the organizer-reported `[0,1]` rejection remains **unresolved**: this checkout
has no portal error payload, submission receipt, or acceptance record bound to the TIFF SHA above.
Do not claim that NaNs caused the rejection or that matching the sample makes rejection impossible.

## Evidence gates before any future submission decision

The software and status page use the following gates:

1. Exact candidate file/pixel hashes and local format report.
2. Candidate-specific **pre-placement surface** comparison against a fresh, complete inventory.
3. Exact **final-dot** comparison against that same inventory. Stop if rank correlation exceeds 0.90
   or more than 70% of candidate dots lie within 3 px of any one registry raster. A stale or
   incomplete inventory is not clearance; literal triggers cannot be waived by a chance-adjusted
   calculation, dense-raster exception, or changed overlap direction.
4. Promotion-grade feature-alone leakage tests.
5. Buffered whole-fault-segment spatial holdout: catalogue features from visible faults only,
   pixel-exact masking of visible faults, pooled DTI with α=0.2/β=0.8 and a 300 m triangular kernel,
   scored by `gems57.evaluate_holdout`. Numeric reporting requires evaluator/version,
   withheld-positive count and a defensible 95% CI. Emission uses `gems57.submission_writer`.
6. A submission receipt is post-upload evidence only; no such receipt exists for the current TIFF.

The current final-dot gate is already negative. The next safe action is an inventory refresh and
independent gate audit—not another emission, hypothesis test, slot selection or upload. Experiments
are capped at three or two hours, whichever comes first, with earlier stops on uniqueness, stale or
incomplete inventory, leakage, or unsupported/nonpositive results. A negative result is valid.

## Portal error record needed to resolve the reported rejection

If the organizer's `[0,1]` error recurs in an authorized future submission, preserve the exact
response body/screenshot, timestamp, submission ID, candidate SHA-256 and portal validation stage.
Until a receipt binds those details, the cause cannot be distinguished from another validation
issue and portal acceptance remains unknown.
