# Exact-candidate qualification receipt contract

This note documents the fail-closed contract enforced by `scripts/build_site.py` and
`scripts/build_ribbon_emission.py`. It does **not** authorize an experiment, emission, slot selection,
or upload. The current candidate is blocked by the 81-trigger literal final-dot scan, the
non-current inventory audit, and missing qualification receipts. `evidence/ribbon_qualification.json`
is currently absent.

## Candidate identity

All qualification records must refer to one exact serialized candidate:

- `candidate_file` — final relative path under `docs/downloads/`;
- `candidate_file_sha256` — SHA-256 of the exact TIFF bytes;
- `candidate_decoded_sha256` — SHA-256 of the raster decoded as contiguous float32 pixels in
  C-order. `gems57.submission_writer` records this value after re-reading the written TIFF;
- every canary, holdout, final-dot scan, and qualification receipt must repeat these hashes;
- the on-disk SHA is recomputed by the site builder. A stale receipt, mismatched file or decoded
  array blocks the gate.

## Inventory freshness and two uniqueness gates

A future `registry_freshness_audit.json` must explicitly mark `fresh_current_inventory: true` and
bind `registry_index_sha256` to the actual `registry/registry_merged.json` bytes. The qualification
`registry` object must repeat that index hash and the SHA-256 of the freshness receipt. Merely having
many indexed rasters or `complete_accessible_scan: true` is not enough; inaccessible, private,
renamed, deleted, stale or organizer-wide omissions remain a blocker.

`preplacement_surface_gate` must contain:

- `passed: true`;
- `candidate_surface_path` and `receipt_path` for files retained in the repository; their on-disk
  SHA-256 values must equal `candidate_surface_sha256` and `receipt_sha256` (both 64-hex hashes);
- the exact `registry_index_sha256` and `freshness_receipt_sha256` used.

`final_dot_gate` must contain `passed: true`, exact candidate TIFF and decoded-pixel hashes, the
SHA-256 of the candidate-matched `uniqueness_full_inventory.json`, and the same index/freshness
hashes. The saved scan itself must be complete, have no missing/invalid sources, `unique: true`,
`stop_required: false`, and no literal firings. The limits remain **rank correlation >0.90** or
**more than 70% of candidate dots within 3 px of any one registry raster**. Do not substitute
chance correction, reverse overlap, or a dense-raster exception.

## Feature-alone leakage canary

`leakage_canary` must bind the exact candidate/pixel hashes and current index/freshness receipt. It
must include a nonempty per-feature collection (one result per tested feature), with each fold's
spatial protocol recorded, each feature's maximum AUC strictly below 0.90, and no feature marked as
leaking. It must retain a `receipt_path` whose bytes match `receipt_sha256`.
`n_features_tested` must equal the collection length and `max_single_feature_auc` must match its
maximum. Missing a feature-level record is not clearance.

## Promotion-grade holdout

`promotion_grade_holdout` must record:

- `passed: true`, `evidence_class: "HOLDOUT-DTI"`;
- `evaluator: "gems57.evaluate_holdout"` and `evaluator_version: "gems57-pooled-hide-v2"`;
- a positive `withheld_positive_pixels` count and pooled DTI in `[0,1]`;
- the full protocol fields: buffered whole fault segments, catalogue features from visible faults
  only, visible faults masked pixel-exactly, pooled scoring, α=0.2, β=0.8, and a 300 m triangular
  kernel;
- a two-sided `[low, high]` `ci95`, `ci95_reportable: true`, a named physical-spatial-cluster
  method, confidence 0.95, and at least two independent spatial clusters;
- a `receipt_path` whose bytes match `receipt_sha256`; and
- candidate TIFF/pixel, inventory-index and freshness-receipt hashes identical to the other gates.

A four-quadrant min–max interval, reused truth-informed selection, or legacy `gems58w` score does not
satisfy this contract. Report the withheld-positive count, evaluator/version, protocol and 95% CI
with every future numeric `HOLDOUT-DTI` value. Use `ORGANIZER-CONFIRMED` only with an organizer
score receipt and artifact-hash crosswalk.

## E1/E2 emission inputs

Before emission, the script separately validates:

- E1 has a complete `HOLDOUT-STRUCTURE` sigma table for each outer block (`NW`, `NE`, `SW`, `SE`)
  and ridge type (`cat-axis`, `sgmc-axis`), with positive finite sigma and matched counts, plus the
  shared evaluator/version, buffered context, and per-feature canary.
- E2 carries the same shared protocol/evaluator, a promotion-grade candidate result with withheld
  positives and defensible 95% CI, and per-class gains each accompanied by a reportable interval.

Only after the pre-emission qualification and E1/E2 receipts pass does the builder write to a private
staging directory. It checks the staged TIFF's exact byte and decoded-pixel hashes against the
qualification before publishing the TIFF/ZIP/receipt and updating the qualification file. Failure
removes the staged artifact. This pipeline is not being run now.

## Current machine-readable status

The latest generated status is [`../../evidence/site_status.json`](../../evidence/site_status.json).
It records `NOT_OK_TO_SUBMIT`, local format preflight separately from portal acceptance, the final-dot
stop, `H58-U1` as not validated, and no experiment/slot/upload action.
