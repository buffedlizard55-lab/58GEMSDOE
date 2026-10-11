# Downloads — review-only diagnostic

> **NOT OK TO SUBMIT — DO NOT SUBMIT.** This directory contains historical research artifacts and one latest sparse TIFF available only for audit. No GeoTIFF here is approved for a competition upload.

## Latest artifact

- [GeoTIFF](58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif)
- [ZIP containing one TIFF](58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip)
- [Per-file metadata](58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json)
- SHA-256: `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`
- 49,139,380 bytes; one-band float32, EPSG:32611, 3730 × 3292; 15,000 positive pixels, all exactly 1.0.

The previous filename contained `unique`, but uniqueness had not been measured. The raster was renamed to `review-only`; pixel bytes were not changed. Its exact current negative verdict is in [`../../evidence/58gemsdoe_unique_ribbon/run_card.json`](../../evidence/58gemsdoe_unique_ribbon/run_card.json) and the read-only audit is [`../../evidence/58gemsdoe_unique_ribbon/audit.json`](../../evidence/58gemsdoe_unique_ribbon/audit.json).

## Why this TIFF is stopped

A direct hash-pinned registry comparison measured **1.0000** of its positive dots within **3 px** of one prior raster, above the current literal **0.70** stop threshold. The witness's 3-px dilation covers all cells in the bridged allowed footprint. This is a duplicate/drift protocol stop, not a claim of byte or pixel copying. The current registry freshness remains `BLOCKED_NOT_EXHAUSTIVE`, and no pre-placement surface receipt exists.

The local 19/19 format/range checks are not uniqueness clearance, holdout evidence, or organizer acceptance. Nodata metadata differs from the sample (`null` versus `NaN`) and portal handling is unknown. HOLDOUT-DTI, σ, simulated gain by class, and a feature-alone leakage canary are not measured for this artifact. No experiment, slot, or upload occurred in session 7.

The old `RATIFIED-UNIQ-v1` chance-corrected protocol in session-5 records is not used to waive the current literal rule. Do not generate a replacement candidate, select a slot, or upload under the current stop.

## Other records

- [Generated per-file download status](index.html)
- [Current status page](../index.html)
- [Executive review](../executive-summary.html)
- [Submission guide](../SUBMISSION_GUIDE.md)
- [Ranked within-lane hypotheses](../research/hypotheses_new.md)
- [Why the 0.2778 attribution is unverified](../research/why-02778.md)
- [Primary-source and evidence register](../SOURCES.md)
