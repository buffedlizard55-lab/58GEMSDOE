# Final deliverable summary — session 7 review (2026-10-11 UTC)

## Decision

**Negative. NOT OK TO SUBMIT — DO NOT SUBMIT.** The available TIFF is retained as a downloadable audit artifact only. The repo does **not** claim it is unique, ready, or accepted by DrivenData. No experiment, replacement raster, slot selection, or upload occurred in this review.

The earlier copy of this summary claimed “mission accomplished,” uniqueness, and readiness. Those claims were unsupported and are superseded by the measured literal registry-overlap stop below.

## Files

| File | Type | Size | SHA-256 | Status |
|---|---|---:|---|---|
| [`docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif) | GeoTIFF | 49,139,380 bytes | `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448` | Audit only — **DO NOT SUBMIT** |
| [`docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip) | ZIP, one TIFF | 102,070 bytes | `3f00cef2c4c6f8443b6e64ec0576fde470ccf17850fc165a0501f472b3240689` | Audit only — **DO NOT SUBMIT** |
| [`docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json) | Metadata | — | — | Local metadata, not an organizer receipt |

The TIFF was renamed from a path containing `unique`; the raster bytes were not changed. Direct downloads and the per-file review warning are linked from [`docs/index.html`](docs/index.html), [`docs/downloads/index.html`](docs/downloads/index.html), and [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md).

A separate ML-named TIFF/ZIP was added to the base branch after this session-7 review. It was not produced, evaluated, or qualified by this review; it is outside the stated ribbon-width scope and must remain review-only. The generated per-file index includes it separately. Do not run its generator or submit it under the current stop.

## Exact results and evidence classes

### LOCAL-FILE-AUDIT

**19/19 local format/range checks pass**, including one float32 band, sample CRS/shape/transform, finite `[0,1]` values, positives exactly `1.0`, zero outside-footprint positives, zero positives on the bridged mapped catalogue, and a one-TIFF ZIP round trip. These are local checks only—not a uniqueness clearance, holdout result, or portal acceptance. Candidate `nodata=null` differs from sample `nodata=NaN`; portal handling is unconfirmed.

### REGISTRY-MEASUREMENT — literal stop

The current file's final dots were compared directly against one hash-pinned registry witness: `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`, SHA-256 `03d619fa75689b48bd3eb4f74c3fa529a9b04c19bd716e15640d910baf3d5a90`. The witness covers all 5,167,373 cells in the bridged allowed footprint after 3-px dilation. **Measured candidate-dot overlap: 1.0000**; active user limit: **0.70**. The literal stop fails. This is logged as a duplicate/drift protocol stop; it is not evidence of byte copying, pixel copying, or intent.

No complete-current-registry clearance is claimed: freshness is `BLOCKED_NOT_EXHAUSTIVE`. The prior 703-raster scan is complete only within its frozen scope. Pre-placement surface is **NOT MEASURED** because no candidate-specific surface or generating lineage was found.

### NOT MEASURED / NOT RUN

- **HOLDOUT-DTI:** not measured for this TIFF; no evaluator value, withheld-positive count, or 95% CI.
- Localization-error σ table and simulated gain by class: not measured.
- Feature-alone leakage canary: not run.
- ORGANIZER-CONFIRMED score or portal acceptance: none; no receipt/hash crosswalk or candidate-specific portal response.
- Experiments this review: 0. Slots used: 0. Uploads: 0.

## Other requested items

- **0.2778 attribution:** The saved public leaderboard snapshot associates 0.2778 with `extradr19`. The GEMSDOE32 H33 owner page says that file is unscored and calls 0.2747 a projection. No hash/receipt crosswalk ties H33 to the `extradr19` row. The cause of the actual participant's result is not established. See [`docs/research/why-02778.md`](docs/research/why-02778.md).
- **Ranked within-lane hypotheses:** three proposal-only ribbon-width tests appear in [`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md). H58-U1 (relief-conditioned width around existing topographic ridges) is ranked first. None has been implemented or validated; the stop blocks experiments.
- **Executive submission guide:** [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md) is the authoritative manual checklist. The file is not authorized for submission.
- **Auditable sources:** official/primary links and evidence classes are listed in [`docs/SOURCES.md`](docs/SOURCES.md). Official competition and USGS pages were not freshly fetched in this session; the feature-stack hash is an owner-maintained bridge pin, not independent organizer provenance.
- **JSON run card / audit:** [`evidence/58gemsdoe_unique_ribbon/run_card.json`](evidence/58gemsdoe_unique_ribbon/run_card.json) and [`evidence/58gemsdoe_unique_ribbon/audit.json`](evidence/58gemsdoe_unique_ribbon/audit.json).

## Reproducibility and scope limits

The experiment/cache feature stack was restored outside Git and its part/whole SHA-256 values match the owner-maintained bridge pins; this establishes integrity relative to that mirror only. No feature was evaluated. The current prompt's literal rule is authoritative for this review; the later `RATIFIED-UNIQ-v1` chance-corrected interpretation in historical session-5 files does not waive a >70% trigger.

Read [`PROMPT.md`](PROMPT.md), [`README.md`](README.md), and [`REMAINING_WORK.md`](REMAINING_WORK.md) before continuing. Do not run an experiment, generate a replacement candidate, choose a slot, or upload under the current stop.
