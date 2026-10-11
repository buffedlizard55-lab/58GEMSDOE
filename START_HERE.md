# Start here — session-7 negative review

> **NOT OK TO SUBMIT — DO NOT SUBMIT.** The current GeoTIFF is available for audit only. It has a measured literal uniqueness stop. Do not upload it, choose a slot, run another experiment, or generate a replacement candidate under the current prompt.

## Current artifact

- [GeoTIFF — review only](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif)
- [ZIP — review only](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip)
- [Per-file metadata](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json)
- SHA-256: `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`

The raster was renamed from a filename containing `unique`; its pixel bytes are unchanged. It has 15,000 positive pixels at exactly 1.0 and passes 19/19 local format/range checks. Local checks are not uniqueness clearance, a holdout result, portal acceptance, or an organizer score. TIFF nodata metadata is null while the sample uses NaN; portal handling is unconfirmed.

## Why it is stopped

A direct hash-pinned registry comparison measured **1.0000** of this artifact's positive dots within 3 px of one prior raster, exceeding the literal **>70%** stop. The witness's 3-px dilation covers the full bridged allowed footprint. This is a duplicate/drift protocol stop, not proof of byte or pixel copying. The current registry freshness is `BLOCKED_NOT_EXHAUSTIVE`; the prior 703-raster scan is complete only for its frozen scope.

Pre-placement surface: **NOT MEASURED**. HOLDOUT-DTI, evaluator/count/95% CI, σ table, simulated gain by class, leakage canary: **NOT MEASURED / NOT RUN**. No score is projected. Experiments: **0**. Slots: **0**. Uploads: **0**.

## Read the current project files

At each session start, read [`PROMPT.md`](PROMPT.md), [`README.md`](README.md), and [`REMAINING_WORK.md`](REMAINING_WORK.md) in full. Then review:

1. [Current site/status](docs/index.html)
2. [Executive submission guide](docs/SUBMISSION_GUIDE.md)
3. [Full session-7 review](docs/research/session7_review_20261011.md)
4. [Ranked within-lane hypotheses](docs/research/hypotheses_new.md) — proposal only; no hypothesis is validated.
5. [0.2778 attribution analysis](docs/research/why-02778.md) — public row belongs to `extradr19`; no hash/receipt ties it to H33. The actual score's cause is unknown from available records.
6. [Sources/evidence classes](docs/SOURCES.md)
7. [Artifact run card](evidence/58gemsdoe_unique_ribbon/run_card.json) and [local audit](evidence/58gemsdoe_unique_ribbon/audit.json)

## Safe, non-experimental commands

These commands audit the existing bytes, render documentation, and run tests. They do not generate a prediction raster or run a holdout experiment:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_sparse_candidate.py \
  --witness .cache/registry/universal-blocker.tif
.venv/bin/python scripts/build_session7_pages.py
.venv/bin/python scripts/build_downloads_index.py
PYTHONPATH=src .venv/bin/python -m pytest -q
```

The registry witness may be absent in a clean cache; do not report a new direct measurement unless its hash is verified. The legacy `scripts/build_site.py` and `scripts/gems60_build_page.py` render historical sessions; the session-7 builder owns current pages.

## Current-prompt constraints in brief

- Stay in the ribbon-width/localization-error lane. Keep an existing ridge surface fixed; do not switch to detection.
- Use the literal stop: surface rank-correlation >0.90 or >70% of final dots within 3 px of a single registry raster stops the candidate. Stale/incomplete inventory is not clearance. Do not replace this with the historical chance-corrected reading.
- Reuse cached features and shared `gems57.evaluate_holdout` / `gems57.submission_writer`; no private scoring/writer fork. If an experiment is ever authorized, use buffered whole segments, visible-catalogue-only feature derivation, exact visible-fault masking, pooled DTI α=0.2/β=0.8 and 300 m triangular kernel; each feature alone must pass AUC ≤0.90.
- At most three experiments or two hours, stop sooner on any hard gate. Never select/use a slot during research.
- Report model results only as HOLDOUT-DTI with evaluator/version, withheld-positive count and defensible 95% CI. ORGANIZER-CONFIRMED requires a hash-bound organizer receipt. Negative results are valid.
