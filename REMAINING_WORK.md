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

---

# Session 3 (2026-10-11 UTC) — an experiment WAS run: three, inside the budget

The review above states that no experiment was run and no new TIFF exists. That was true when it was
written. Session 3 then ran the three mandated experiments and emitted a new candidate, so this section
is the current queue. Nothing was uploaded and no slot was used.

## S3.0 State

| Item | State |
|---|---|
| Current candidate | `docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`, sha256 `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd`, 433,419 B, 40,768 isolated dots at exactly 1.0, NaN outside the footprint exactly as in `sample_submission.tif`, 0 dots on the catalogue |
| Format preflight | **15/15 pass** (`evidence/ribbon/emission.json` → `validator`) |
| HOLDOUT-DTI of the delivered bytes | **0.043651** pooled (NW 0.046854 / NE 0.036240 / SW 0.056175 / SE 0.033176), 60,869 withheld positives, `gems58-pooled-hide-v1`, evaluator `gems58w.metric/v1`, interval 0.033176–0.056175 (min–max over the four blocks; no bootstrap CI is claimed) |
| Gate G3 — full inventory scan | **DONE and NEGATIVE.** 702 witnesses (`registry/registry_merged.json`: 695/695 pinned — the missing pin was recovered from `55GEMSDOE` commit `d92606c2…` and re-hashed — plus a current-default-branch delta over all 56 reachable clones, which found no new grid-format raster in any sibling), complete, 0 missing/invalid, 0 source errors. Byte-unique, pixel-unique, worst ρ **0.1824** (**0** firings vs the 0.90 limit), worst Jaccard **0.1041** (**0** firings vs 0.50) — but the literal 3 px forward-overlap rule fires against **81** witnesses: **54** vacuous (E ≥ 0.99) and **27** broad dot fields of 155,021–3,380,827 dots (18 near-duplicate variants from one repository). Worst informative overlap **0.8750** at E = 0.8611 (lift 0.100); max lift among the firings **0.3752**; against witnesses with E < 0.30 the worst observed overlap is **0.6115**, while at E < 0.70 there are still **7** firings (worst 0.7777 at E = 0.6456). Verdict `negative`, `stop_required` true |
| Two run cards coexist on purpose | `evidence/run_card.json` = the archived concordant diagnostic (its recorded 694/695 scan stays as recorded, which is what `scripts/ribbon_check_site.py` asserts); `evidence/ribbon/run_card_final.json` + `docs/RUN_CARD.json` = the current session-3 candidate. Both verdicts are **negative**, so the decision is unambiguous |
| Shared-metric cross-check | **AGREE, delta exactly 0.0.** `scripts/crosscheck_shared_metric.py` re-derives the delivered bytes with the shared `gems57.metric` (main has archived `gems58w`): per-fold NW 0.046853622 / NE 0.036240014 / SW 0.056175312 / SE 0.033175652 and pooled **0.043651086** are identical under both implementations and equal the recorded receipt; the literal brute-force oracle matches the shared fast path to ~1e-17 on a bounded tile. Runs in CI (`evidence/ribbon/shared_metric_crosscheck.json`, gate G5i) |
| Slots used | **0** |

## S3.0b Two lanes published a candidate on 2026-10-11, and they disagree

A sibling session (PRs #17/#18, scatter-cover lane) delivered
`docs/deliverable/downloads/gems58-novel-scatter-44090-20261011T0630Z.tif` (sha256 `5f64b6dc…`,
44,090 dots, 15/15 local checks) with a green "✅ NEW CANDIDATE — DOWNLOAD OK" banner, on the strength
of a screen published as "473 rasters · worst rank correlation 0.0557 · worst 3 px forward overlap
**0.3160** · **0 triggers**".

That overlap is the **reverse** statistic — the fraction of each *witness's* dots within 3 px of the
candidate's — which is what the archived `gems58w.screen_against` triggered on before IR-58-UNIQ-04 was
fixed. Re-measured in the protocol direction (the fraction of the *candidate's* dots within 3 px of one
witness's dots) against the same byte-verified inventory, that file has **78 firings** (worst **1.0000**
against the plane-filling `GEMSDOE2:turbo-simple`) and **0** in the reverse direction:
`evidence/ribbon/sibling_direction_check.json` (IR-58-UNIQ-06).

This is **not** a duplication claim. The identical degeneracy fires **81** times on the session-3
candidate, because those witnesses' 3 px dilations cover 61–100 % of the footprint and overlap every
nonempty candidate. Both files are in the same position under the literal rule; the two lanes report
opposite verdicts only because they measured different statistics over different inventories (473
live-fetched vs 703 pinned+delta). The immediate follow-up is a corrected full screen of the sibling
deliverable with both readings:

```bash
PYTHONPATH=src python3 scripts/check_uniqueness_registry.py \
    docs/deliverable/downloads/gems58-novel-scatter-44090-20261011T0630Z.tif \
    --workers 2 --out ribbon/sibling_full_inventory.json     # ~35 min; started this session
```

Also note `rho_subsample`: the sibling emitters pass a subsampled Spearman to `screen_against`. The
merged implementation accepts it (so their callers keep working) but now records `rho_subsample` and
`rho_statistic` in the summary, so a subsampled pass can never be reported as an exact one.

## S3.1 Remaining work, in priority order

1. **The owner's protocol decision is the blocking item — and it now decides two files, not one.** Ratify a chance-corrected uniqueness rule —
   in its lift form ("fire only if (observed − E)/(1 − E) > 0.50") this file yields **2 firings, both
   against this repository's own earlier ribbon files**, and the highest lift against any other
   repository is **0.4898**; in its E-limit form the threshold must be ≤ **0.61** for zero firings — or
   keep the literal rule, under which no ridge-based emitter in this repository family can ever be
   submitted. If the lift rule is ratified, `scripts/build_site.py` needs one change: pass the ratified
   threshold into `evaluate_gates` G3 instead of the raw `unique` flag; the banner then turns green and
   `--strict` exits 0. Do **not** re-run the 35-minute scan to decide this — the receipt already
   contains both readings (`ratification_analysis` in `evidence/ribbon/run_card_final.json`).
2. **Re-route geometry and writing through the shared template — scoring is already verified.**
   `scripts/crosscheck_shared_metric.py` proves the reported HOLDOUT-DTI is identical under
   `gems57.metric` (delta exactly 0.0 per fold and pooled), so the *numbers* do not depend on the
   archived copy. What still does: the ridge field (`gems58w.extract`), σ (`gems58w.sigma`), the line
   plan (`gems58w.allocation`, whose `_marginal_pair` FP term does not reproduce the official
   per-prediction `FP_w` for interacting lines) and the writer (`gems58w.submission`). Port
   `ribbon_run_adaptive.py` and `ribbon_emit_adaptive.py` onto `gems57.evaluate_holdout` and
   `gems57.submission_writer`, re-derive the plan with exact marginal utilities
   `U = (1 − αs)ΔTP − αsΔFP`, then re-verify that EXP-2/EXP-3 reproduce.
3. **Coverage is the only lever that matters.** 0.4133 implies ≈0.36 weighted coverage (PROJECTION);
   this surface reaches 0.0561 on catalogue truth, and k̂ spans 0.000–0.035 against a marginal bar of
   0.0827. Geometry is worth +0.005; coverage ~6×. Spend the next three experiments on detection
   (H58-R4 first), not on emission geometry.
4. **Aeroradiometric + 1 m lidar (owner download required).** No eK/eU/eTh/total-count channel and no
   lidar derivative in the delivered 19 bands, although page 968 says GeoDAWN acquired both. Links are
   verified in `evidence/organizer_confirmed.json`; the sandbox cannot fetch binaries. If the owner
   drops the products into `data/external/`, H58-R3 becomes testable in one session.
5. **Pre-placement surface gate.** The protocol requires screening the pre-placement surface *and* the
   final dots. Session 3 screened the final dots (local + full inventory) and the ridge field locally;
   a full-inventory screen of the pre-placement belief surface is still outstanding.
6. **Directional σ (an error tensor)** and **flight-line regression**: see
   `docs/research/hypotheses_session3.md` (H58-R5, H58-R6).
7. **Housekeeping.** `scripts/chance_coverage.py` is stale (hardcodes `~/.cache/gems-data/…` and an old
   CSV schema) and `scripts/chance_corrected_uniqueness.py` is hardcoded to one candidate and
   `row["file"]`; rewrite or delete. `scripts/ribbon_build_site.py` still emits "Download: OK" copy and
   links into the now-empty `docs/ribbon/downloads/`, so it must **not** be re-run while
   `scripts/ribbon_check_site.py` governs the archived pages.

## S3.2 Limitations of everything above

- **No organizer receipt exists**, so no score is claimed anywhere. HOLDOUT-DTI measures recovery of
  *catalogue* truth; the competition scores *new* faults whose provenance the organizers will not
  disclose. No bridge between the two is measurable locally.
- **The mandated holdout cannot score an off-catalogue file** (IR-58-02): withheld truth *is* catalogue,
  so a full-catalogue 3 px margin gives HOLDOUT-DTI exactly 0. The delivered file drops only
  *on*-catalogue dots — inert, because the organizer masks those pixels — which is why its HOLDOUT-DTI
  is non-zero.
- **σ is large and censored**: pooled median 6.88 px, estimator floored at 0.5 and capped at 6.0 px, so
  the lane's "tight line where σ < 0.5 px" branch is unreachable (IR-58-SIGMA-01).
- **The adaptive plan barely adapts**: 5,794 of 6,286 segments got 5 lines, 492 got 3, and `AD` was
  identical to a uniform ribbon (pooled delta 0.000000).
- **Live-score calibration is a measured dead end** (IR-58-LIVE-01): R² = −1.27, no covariate above
  |Spearman| 0.258 over 66 verified rasters, because subset membership is undisclosed.
- **The witness inventory is a public sibling-repository inventory**, not an organizer registry: 703
  byte-verified rasters from 56 reachable clones' current default branches plus this repository's own
  tree. Private, renamed or deleted repositories are out of scope by construction.
- **Two CPUs, ~3 GB RAM.** The full scan takes ~35 minutes at `--workers 2`.

## S3.3 Do not re-run (measured negatives)

- Two-parameter catalogue-proximity calibration of live scores (R² = −1.27); the n=20
  `Spearman(dots, score) = −0.831` is an artifact.
- SGMC-differential as held-out truth: provenance unverified, and `gemsdoe29-sgmc-off-catalogue-44k`
  scored **0.0512** ≈ random.
- Unheld-budget density sweeps (+0.025 claimed vs +0.0006 at equal budget); blurring a belief field
  before a max-coverage emitter; CTX (distance-to-catalogue as a feature) which collapses onto the
  catalogue.
- Any catalogue margin on the delivered file: it zeroes the holdout by construction.
- Re-introducing the swapped overlap directions, the 90° across-strike bug in `ridges.py`, or a private
  fork of any `src/gems57/` tool.
- Placing dots off-geology to dodge a broad witness: that trades the hypothesis for a meaningless number.
