# Submission guide

## Current decision (session 3, 2026-10-11): **NOT OK TO SUBMIT — download for review only**

> **DO NOT UPLOAD OR SELECT A WEEKLY SLOT.** The current candidate is format-valid and measured, but
> the protocol's literal uniqueness rule fires against it, so by the standing instruction it is logged
> as a duplicate and stopped. The authoritative, evidence-generated banner is on the
> [site status page](index.html); the how-to-submit steps are on the
> [executive summary](executive-summary.html); the full local preflight receipt is on the
> [portal checklist](submit.html).

### Current candidate

- File: [`gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`](downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif)
  (+ a [ZIP](downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.zip) containing exactly one GeoTIFF)
- Name: `gems58-ribbon-sigma-adaptive-40768-20261011T052942Z`
- Note (135/140 chars): `Ribbon lane: adaptive dotted ribbons 0/+-300/+-600 m on catalogue-free Hessian ridges (sigma cross-fitted); 40768 isolated dots at 1.0.`
- SHA256: `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd` (433,419 B)
- Raster: one float32 band; EPSG:32611; 3730 × 3292; 100 m; transform `(100, 0, 243350, 0, -100, 4508550)`;
  40,768 dots, every emitted value **exactly 1.0**; **NaN outside the study footprint exactly as in the
  organizer's `sample_submission.tif`** (7,111,787 NaN, `nodata=nan`) and finite everywhere inside it —
  which is what makes the portal rejection `Predicted values must be in range [0, 1]` impossible for
  this file. **15/15** local checks pass (`evidence/ribbon/emission.json` → `validator`).
- HOLDOUT-DTI of the exact delivered bytes: **0.043651** pooled (NW 0.046854 / NE 0.036240 /
  SW 0.056175 / SE 0.033176), 60,869 withheld positives, protocol `gems58-pooled-hide-v1`, evaluator
  `gems58w.metric/v1`, interval 0.033176–0.056175 (min–max over the four blocks). This measures
  recovery of *catalogue* truth, not the organizer's new-fault truth, and is **not** a leaderboard
  forecast.
- 0 dots on the mapped catalogue (the organizer masks those pixels out of evaluation in both rounds).

### Why the status is still negative

1. **The literal 3 px forward-overlap rule fires.** The governing scan over **702** sha256-verified
   public witness rasters (`evidence/ribbon/uniqueness_full_inventory.json`, complete, 0 missing or
   invalid, 0 source errors) reports **81** witnesses with more than 70 % of this file's dots within
   3 px of theirs. Verdict `negative`, `stop_required` true.
2. **Those firings are all against broad or plane-filling witnesses.** 54 have a chance-level expected
   overlap E ≥ 0.99, so they overlap *every* nonempty candidate and carry no information; the other 27
   are dot fields of 155,021–3,380,827 dots (18 of them near-duplicate variants published by one
   repository). The worst is 0.8750 against a witness with E = 0.8611 (chance-corrected lift 0.100);
   the largest lift among all 81 firings is 0.3752.
3. **Every discriminating statistic passes by a wide margin.** Byte-unique and pixel-unique among all
   702; worst rank correlation **0.1824** against a 0.90 limit (**0** firings, and the worst case is
   this repository's own control raster); worst dot-set Jaccard **0.1041** against a 0.50 limit
   (**0** firings). Against witnesses whose own expected overlap is below 0.30 — the ones that can tell
   two emissions apart — the worst observed overlap is **0.6115**.
4. **No organizer receipt exists.** Nothing was uploaded and no slot was used, so no
   ORGANIZER-CONFIRMED score exists for this or any other file here.

### The decision that would change it (owner only)

Ratify a chance-corrected uniqueness rule. In its **lift** form — a witness fires only if
`(observed − E)/(1 − E) > 0.50` — this file produces **2 firings, both against this repository's own
earlier ribbon files** (family resemblance, not reuse of another lane), and the highest lift against
any other repository is **0.4898**. In its **E-limit** form ("fire only if E < limit and observed >
0.70") the limit must be ≤ **0.61** to give zero firings. Keeping the literal rule instead means no
ridge-based or coverage-based emitter in this repository family can ever be submitted, because the
registry already contains near-plane-filling witnesses (IR-58-UNIQ-02/03). `scripts/build_site.py`
computes both readings from the scan rows at build time and does not choose between them.

---

# Archive — the session-1 guide and its diagnostic file

Everything below describes the **previous** candidate
(`gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif`) and the state of the repository
before session 3. It is retained for audit. Two of its statements are corrected by session 3 and are
annotated inline: the registry restore is now **695/695** complete plus a current-default-branch delta
(703 byte-verified witnesses, IR-58-REG-01), and the uniqueness instrument's two overlap directions
were exchanged until 2026-10-11 (IR-58-UNIQ-04), so overlap numbers quoted below were measured with
the directions swapped.

## Score-attribution note

The official public leaderboard observed on 2026-10-11 UTC showed xiaofanhu at 0.4133 (rank 1), DARD at 0.3195 (rank 8), and extradr19 at 0.2778 (rank 23). These dynamic public rows are not tied to this TIFF. The GEMSDOE32 owner-maintained H33 page says its named artifact has no organizer score and describes 0.2747 as a projection; no receipt/hash crosswalk links 0.2778 to that file. See [`LEADERBOARD.md`](LEADERBOARD.md) and [`research/why-02778.md`](research/why-02778.md).

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
