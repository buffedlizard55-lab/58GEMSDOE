# Remaining work — current status (2026-10-11 UTC)

This file supersedes the old “session 1” queue. No scientific experiment or new TIFF was run in the latest review; no weekly slot was selected.

## Hard stop: do not submit or launch an experiment

The current diagnostic is `docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif` (SHA256 `8b196e6eea06fef0d6cf2c9109091d1e2677a77d6e48d8b04f334a879551687f`). Local format/range preflight passes. That is not uniqueness clearance, portal acceptance, or an organizer score.

`evidence/ribbon_uniqueness.json` compares the candidate with 694 of 695 pinned rasters and records 100% of its dots within 3 px of `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`. This exceeds the literal >70% stop threshold. The one full-footprint-positive witness makes the literal final-dot test fail for this nonempty candidate. The registry is also stale/incomplete, and a candidate-specific current pre-placement surface result is absent. Do not exempt, omit, or silently down-weight this raster; resolve the scope/meaning of the gate before any new placement/emission experiment.

No current promotion-grade HOLDOUT-DTI exists. The historical E1/E2 artifacts under `evidence/ribbon/` are legacy diagnostics; E2 consulted the same-cell withheld truth for selection, fit σ on scored folds, and used an invalid repeated-block bootstrap. Do not cite those values as promotion-grade results.

## Completed in this review

1. Checked the current official DrivenData leaderboard and recorded a dated snapshot in `evidence/official_leaderboard_observation_20261011.json`: xiaofanhu rank 1 at 0.4133, DARD rank 8 at 0.3195, extradr19 rank 23 at 0.2778. This is a public-board observation, not a receipt/hash crosswalk to a local file.
2. Checked the current GEMSDOE32 owner-maintained page through its public GitHub source. It says the named H33 artifact has no organizer score and calls 0.2747 a model projection. No evidence ties 0.2778 to the H33 file. See `docs/LEADERBOARD.md` and `docs/research/why-02778.md`.
3. Rechecked the existing candidate's local format/range preflight against `data/bridge`; the TIFF bytes/hash are unchanged. This does not waive the registry stop.
4. Reconciled the exact marginal-utility explanation and the legacy ribbon site's messaging. See `docs/research/metric.md`, `docs/research/ribbon-algebra.md`, `src/gems58w/`, and `docs/ribbon/`.
5. Ranked four previously unrun, strictly within-lane calibration hypotheses in `docs/research/hypotheses_new.md`. They are proposals, not measured improvements.

## Next work, in order — only if the literal gate can be resolved

1. **Resolve the inventory/gate blocker:** refresh the complete accessible public-raster inventory at current default-branch commits; record inaccessible sources and exact CRS/shape/transform; retain the full-footprint witness unless an authorized, documented policy says otherwise. No run proceeds while the required accessible inventory is stale or a literal stop still fires.
2. **Run the surface gate before placement:** compare the proposed ridge-placement surface with every current accessible registry raster. Stop on rank correlation >0.90 or >70% 3-px overlap; do not produce a candidate TIFF in a stopped run.
3. **Preregister only the top hypothesis** from `docs/research/hypotheses_new.md`. Reuse the cached feature stack, buffered whole-component context, shared feature-alone leakage canary, `gems57.evaluate_holdout` and `gems57.submission_writer`. Do not select or use a slot.
4. **Promotion-grade result:** use training-only/nested selection and untouched buffered outer spatial blocks; report pooled HOLDOUT-DTI with evaluator version, withheld-positive count, CI method and valid 95% CI. The positive labels remain catalogue-based proxy truth, not the organizer's private expert faults; state that limitation.
5. **If and only if holdout and both uniqueness phases pass:** write a new raster with the shared writer, validate exact bounds/transform/CRS/range/nodata requirements, run final-dot inventory comparison, record a hash-bound run card, and clearly distinguish local preflight from organizer acceptance. Only a separate human/selector process may choose a weekly slot.

## Experiment budget and stopping criteria

The session limit is at most three experiments and two hours. Stop early for any uniqueness trigger, stale/incomplete inventory, AUC >0.90 without a leakage explanation, an invalid holdout protocol, a nonpositive paired primary result, or a 95% CI that does not support the predeclared promotion rule. Do not start additional variants because an outcome is weak.

## Score attribution facts

- Official page 967 gives the task and metric; local score claims require either a conforming HOLDOUT-DTI record or an organizer receipt tied to the artifact.
- A 2026-10-11 public-board row shows extradr19 at 0.2778 and DARD at 0.3195; current rank 1 is xiaofanhu at 0.4133. These dynamic public rows are not tied to the GEMSDOE32 H33 TIFF.
- The GEMSDOE32 page says that H33 artifact is unscored and that 0.2747 is a projection. Do not call it a score.
- No competition slot was selected and no organizer receipt was obtained for this repository's TIFF.

Official links and dated checks are in `docs/SOURCES.md`; the full protocol is in `PROMPT.md` and `README.md`.
