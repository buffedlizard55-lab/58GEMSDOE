# Submission guide — current decision: **NOT OK TO SUBMIT**

> **DO NOT UPLOAD OR SELECT A WEEKLY SLOT FOR THE CURRENT FILE.**
> The file below is retained as a research/diagnostic artifact so its findings are auditable. It is not a cleared competition submission.

## Diagnostic GeoTIFF (not cleared)

- File: [`gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif`](downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif)
- Name: `gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros`
- SHA256: `8b196e6eea06fef0d6cf2c9109091d1e2677a77d6e48d8b04f334a879551687f`
- Local raster properties: one float32 band; EPSG:32611; 3730 × 3292; 100 m; transform `(100, 0, 243350, 0, -100, 4508550)`; values in [0,1]; all finite under the project's conservative local policy. The recorded local format validator passed, but that is **not** uniqueness clearance, official portal acceptance, or an organizer receipt.
- Current site/receipt note is a diagnostic warning, not a recommendation: `H58b ribbon diagnostic; dots at 1.0; format preflight only; uniqueness and promotion-grade holdout not cleared; DO NOT SUBMIT.`

## Why the status is negative

1. **Literal final-dot gate fails in the frozen scan.** `evidence/ribbon_uniqueness.json` reports that 100% of candidate dots are within 3 px of one prior raster (`GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`; that prior has 5,167,373 positive pixels, equal to the recorded footprint). The protocol stop threshold is >70%. Rank correlation is below its 0.90 threshold, but that does not override the independent overlap failure.
2. **The scan is not current or complete.** The frozen 695-raster result covers 57 pinned repository snapshots generated at `2026-10-10T19:58:45.875405Z`. Public tree checks on 2026-10-11 found TIFFs in unrepresented repositories 58, 59, 60 and 61, plus 88 TIFF paths added to the already-scanned GEMSDOE52 tree since its pinned commit. A later restore checked only 694/695 pinned rasters; one raster row is missing, so this is not a complete scan either. After that initial tree audit, `origin/main` advanced to commit `d8c17dd` with 10 TIF/TIFF paths in this repository, including two inherited MECE candidates that were not compared against a complete registry. `evidence/registry_freshness_audit.json`, `evidence/registry_fetch_report.json`, and `evidence/ribbon_uniqueness.json` record the scopes and exact missing/error result.
3. **Pre-placement surface status is not cleared for this candidate.** The available historical `registry/uniqueness_surface_pre-placement_summary.json` concerns a different 38,163-dot build, compared a different inventory and excluded dense rasters from overlap. It is not a valid clearance under the current literal gate. The current candidate needs its own pre-placement surface test against a current registry.
4. **No promotion-grade holdout result exists for the revised instrument.** A new buffered whole-component constructor and tests now exist, but E1/E2 were not rerun. The recorded older experiment used same-cell withheld truth to accept per-segment patterns, fitted σ on scored folds, and its old bootstrap treated repeated copies of physical blocks as separate clusters. Its DTI/CI are legacy diagnostics, not valid promotion evidence. See `evidence/ribbon_e1_sigma.json`, `evidence/ribbon_e2_arms.json`, and `scripts/run_ribbon_experiments.py` for the record and code review.
5. **No organizer receipt exists.** No submission was uploaded, no weekly slot was spent, and there is no `ORGANIZER-CONFIRMED` score.
6. **Inherited MECE artifacts are out of scope and not cleared.** A separate main-branch change added MECE/multi-evidence TIFFs and a run card that compared only against the ribbon candidate. Its full-catalogue holdout is leakage-flagged, its comparison is not a full-registry scan, and the method is outside this ribbon-only task. Those files remain diagnostic; the script's command-line entry point exits with a NO-GO message; do not run or submit them.

These blockers are independent. Passing the local TIFF format validator cannot cure either the literal overlap stop or holdout leakage.

## Requirements before the status can change

1. Refresh and hash the complete accessible public raster inventory at current default-branch commits. Include every candidate/prior TIFF/TIFF, verify CRS, shape **and transform**, and record inaccessible repositories/artifacts. A current public-repository scan still cannot prove coverage of private, unlinked or organizer-held files.
2. Test the proposed feature surface **before placement** and the final dots with the shared `gems57.uniqueness` gate. Stop if rank ρ >0.90 or >70% of candidate dots lie within 3 px of any one prior raster. The current all-footprint-positive witness means any nonempty candidate on that same grid would fail; do not try to route around it.
3. Use `gems57.holdout.build_buffered_holdout_context` for whole-component buffered hide-and-recover. Compute catalogue-derived context from visible faults only, mask every still-known fault pixel exactly, and use `gems57.evaluate_holdout` (version `gems57-pooled-hide-v2`) for exact pooled DTI. The evaluator reports scores with withheld-positive counts and block-bootstrap 95% CIs; only use those CIs when the physical-block terms are pooled before resampling and all tuning is confined to training blocks.
4. Run feature-alone leakage canaries before trusting a feature. AUC >0.90 is a leakage suspect until disproven.
5. Keep the current three-experiment / two-hour limit. Do not select a weekly slot during model development.
6. Generate a current run card with the hypothesis, mechanism, named non-fault mimic, evaluator/version, withheld-positive count and valid CI (or explicit “not measured”), pre-placement and final registry results, TIFF SHA256, local validator output, ≤140-character name/note, and explicit promote/negative decision.
7. Only after every local gate passes should a registered competitor independently decide whether to use one of the platform's allowed feedback submissions. The official rules allow up to three automated-scoring submissions per week, but require selecting **one** final submission for both prize rounds.
8. Read the complete [official rules (September 2026)](https://docs.nlr.gov/docs/fy26osti/96647.pdf). They require disclosure in the narrative of generative-AI use when applicable and impose eligibility, licensing, verification, and final-solution requirements. The user/competitor is responsible for those representations.

## Portal steps — only after this page says OK TO SUBMIT

1. Sign in and register for the challenge on the [official DrivenData competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Confirm the live deadline and requirements. There is a discrepancy: the homepage lists **Dec. 3, 2026, 11:59 p.m. UTC**, while Appendix A of the September 2026 rules says **5:00 p.m. ET** on the deadline date. Until clarified, use the earlier 5:00 p.m. ET cutoff (22:00 UTC on Dec. 3 if ET is UTC−5).
3. Open the [submissions page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/) and upload the single-band GeoTIFF (not the ZIP unless the live portal specifically requires it). Add the approved ≤140-character note.
4. Save the submission page/receipt. Only a value transcribed from that receipt may be called **ORGANIZER-CONFIRMED**. A holdout DTI, model projection, or local validator result is not an organizer score.
5. Make the final one-submission selection as a separate, deliberate step; do not let experiments or a high public-board score choose it automatically.

## Official format facts and a local-policy caveat

The official problem page specifies EPSG:32611, 100 m, the same bounds as the training data, one float32 layer, prediction values in [0,1], and null/NaN outside the bounds. The local bridge sample has NaNs outside its finite study-area footprint. This repo's recorded all-finite/zero-outside local policy is conservative and has not been confirmed by an organizer as equivalent for portal nodata handling. The current file's local validator result must not be paraphrased as “officially valid.”

See [the current site status](index.html), [official source register](SOURCES.md), [irregularities](IRREGULARITIES.md), and [ranked research hypotheses](research/hypotheses_new.md).
