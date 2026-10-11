# Review summary — session 7 (2026-10-11 UTC)

## Decision

**Negative. NOT OK TO SUBMIT — DO NOT SUBMIT.** The available GeoTIFF is downloadable for audit only. It is not labeled unique, ready, or accepted. Its former filename contained `unique`; it was renamed `review-only` without changing the raster pixels.

No experiment, replacement candidate, slot selection, or upload occurred in this review.

## Measured result

- Current artifact: [`docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif).
- Raster SHA-256: `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`.
- `LOCAL-FILE-AUDIT`: 19/19 local format/range checks pass. Nodata metadata differs from the sample (`null` vs `NaN`); organizer/portal acceptance is not established.
- `REGISTRY-MEASUREMENT`: final-dot overlap is **1.0000 within 3 px** against one hash-pinned prior registry raster, above the active literal **>70%** stop. Its 3-px dilation covers the full bridged allowed footprint. This is a duplicate/drift protocol stop, not proof of byte or pixel copying.
- Current registry freshness: `BLOCKED_NOT_EXHAUSTIVE`; the older 703-raster scan is complete only for its frozen scope.
- Pre-placement surface: **NOT MEASURED**. HOLDOUT-DTI, evaluator/count/95% CI, σ table, simulated class gain, and leakage canary: **NOT MEASURED / NOT RUN**. No score is projected.

## Requested deliverables

- **Audit-only GeoTIFF and one-TIFF ZIP:** [`docs/downloads/`](docs/downloads/README.md), each clearly marked DO NOT SUBMIT.
- **Executive submission guide:** [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md).
- **Ranked within-lane proposals:** [`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md); three hypotheses, H58-U1 first, none implemented or validated.
- **0.2778 attribution:** the dated public board ties the row to participant `extradr19`. No receipt/hash crosswalk ties it to H33; the H33 owner page labels it unscored and 0.2747 a projection. Why `extradr19` got 0.2778 is unknown from available evidence. See [`docs/research/why-02778.md`](docs/research/why-02778.md).
- **Source register:** [`docs/SOURCES.md`](docs/SOURCES.md). Official competition/USGS pages were not freshly fetched this session; the restored stack's hash pin is owner-maintained, not independent organizer provenance.
- **JSON run card and audit:** [`evidence/58gemsdoe_unique_ribbon/run_card.json`](evidence/58gemsdoe_unique_ribbon/run_card.json) and [`evidence/58gemsdoe_unique_ribbon/audit.json`](evidence/58gemsdoe_unique_ribbon/audit.json).

## Current status and safe next steps

The literal uniqueness stop blocks this artifact and, under the current prompt, no replacement candidate or experiment is authorized. No slot may be used. Read [`PROMPT.md`](PROMPT.md), [`README.md`](README.md), and [`REMAINING_WORK.md`](REMAINING_WORK.md) before further work. The current status page is [`docs/index.html`](docs/index.html).
