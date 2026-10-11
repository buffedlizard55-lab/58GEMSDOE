# Mission brief (condensed copy of the project prompt)

This file is a condensed, faithful copy of the project prompt. The leaderboard dump is not repeated here. It lives in `LEADERBOARD.md` and is user-supplied and unverified. Read this file at the start of every session.

## Goal
Place at the top of the DrivenData **GEMS Prize Challenge** (U.S. DOE Office of Geothermal; NLR administers): produce a full-region, one-band, 100 m, float32 GeoTIFF of fault probabilities, in EPSG:32611, with values in [0,1] and NaN outside the valid footprint. Competition page: https://www.drivendata.org/competitions/306/competition-doe-gems/ (unreachable from this sandbox; see `SOURCES.md`).

## Non-negotiable requirements
1. **A submission TIF must be generated** and be easy to download. It must be obvious on the site whether it is OK to download and submit it. It must be validated before it is offered.
2. **Uniqueness.** Do not copy a previous submission, except for learning. Check the raster against every earlier GEMSDOE raster (correlation below 0.90 and under 70% of dots within 3 px of any registry raster).
3. **Name and note.** Each submission gets a unique name and a short note (140 characters or fewer).
4. **Executive summary.** The site opens with an executive summary and a step-by-step submission guide.
5. **Validation.** No NaN inside the footprint; values in [0,1]; CRS, shape, and transform match the sample submission.
6. **Verification.** Every number is labelled HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.
7. **Leakage canary.** Each feature is tested alone on the holdout. AUC above 0.90 means leakage until proven otherwise.
8. **Holdout protocol.** Hide-and-recover: withhold whole fault segments with a buffer; derive every catalogue-based feature only from visible faults; score pooled DTI (α=0.2, β=0.8, 300 m triangular kernel).
9. **Budget.** Stop after 3 experiments or 2 hours. Promotion to a submission slot is a separate step within the weekly cap.
10. **Run card.** End each run with one JSON card (`RUN_CARD.json`). Negative results are deliverables.
11. **Work from official, verified sources.** Give links for manual review. Flag irregularities. No hallucinations; verify line by line. No manual input.

## Ribbon-lane method (this session's lane)
- Match emission width to the measured localization error. Placement within about one pixel is what pays. Parallel dotted lines pay when location is uncertain.
- On the holdout, measure the across-strike distance from each candidate ridge to the nearest withheld segment. Fit an error scale σ(x) by data block, feature resolution, and ridge type.
- Per segment, choose the number and offset of parallel dotted lines (spacing near the 3-px kernel radius) that maximize U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact metric.
- Use a single tight line where σ < ~0.5 px; a ribbon about ±σ wide where σ is 2–3 px.
- Report the σ table and the simulated gain per class.

## Candidate hypotheses
Before implementing, name 3–5 hypotheses (layer, physical signature, why it catches a fault missing from the catalogue, how it differs from what exists). Rank by expected DTI gain and cost. Validate the top one on the holdout before using a submission slot. See `HYPOTHESES.md`.

## Core values
- **Maximize P(Win):** in every decision, weigh trade-offs and choose the path that most raises the chance of a top result.
- **Own the Outcome:** own results end to end. When something breaks and we can act, act. Treat failure and success as signals.

## Where things stand
Infrastructure is in place (`gems/`, `scripts/`, `tests/`). No competition raster is available in this sandbox, so no holdout result and no competition TIF exist yet. See `IRREGULARITIES.md`.
