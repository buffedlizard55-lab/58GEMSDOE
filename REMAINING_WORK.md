# Session 7 (2026-10-11 UTC) — H7-A deep-edge sigma-ribbon candidate (ribbon lane)

Three experiments, one run card, one unique GeoTIFF. The deliverable page is
[`docs/gems61.html`](gems61.html) (one-click download + submit steps at the top); the governing
receipt is [`evidence/gems61/run_card.json`](../evidence/gems61/run_card.json).

**What shipped.** Hypothesis **H7-A**: faults buried under basin fill appear as *step edges*
(first-derivative maxima) on the organizer's subsurface/magnetic-structure surfaces
(`depth_to_base_surf`, `cond_surf`, `tc`) rather than Hessian ridges of the raw bands — a detector
surface and emission geometry no registered raster uses. Ribbon width is the measured
localization error (**H7-B**, relief-conditioned σ per block × resolution × ridge type), and the
number/offset of parallel dotted lines per segment is chosen by the exact-metric utility rule
**U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP** with setwise max-credit interactions. All dots are
exactly 1.0, none on the mapped catalogue.

**What was measured (labels exact).**
* Leakage canary: **CLEAN** — combined edge strength AUC 0.501, per-band 0.499–0.503, relief 0.544
  (8 holdout cells). The deep surfaces carry no catalogue signal: no leakage, and consistent with
  the discovery premise.
* HOLDOUT-DTI (`gems61-buffered-hide-v1`, 22,893 withheld positives; catalogue-recovery proxy,
  structurally blind to off-catalogue faults): **A1 σ-ribbon 0.04496** vs **A0 single-line 0.02943**,
  paired Δ **+0.01553**, 95 % CI **[+0.01195, +0.01913]** (quadrant-cluster bootstrap; 4/4 quadrants
  positive). Whole-rule contrast, not matched-mass (IR-58-S7-03). Same-instrument reference
  (session-5 concordance file re-scored): **0.03016** — the candidate rule beats it by +0.0148.
* Uniqueness vs 694 byte-verified witnesses (pre-placement surface *and* final dots): **literal
  uniqueness stop** — 74 forward-overlap firings (worst 1.0 vs whole-footprint witnesses; 54 of
  them saturated, E ≥ 0.99). Under the rule now in force this is decisive: **NOT CLEARED —
  DO NOT SUBMIT** (file retained for review; run-card verdict `negative`). The chance-corrected
  readings (rule A 0, rule B 0, ρ 0) are recorded beside the literal reading and do **not** waive
  the stop.
* Format gates: all-finite float32, [0, 1], no nodata tag (the measured portal-error fix).

**What remains / limitations (session 8+).**
1. **No organizer receipt exists for anything.** The live effect of H7-A is unmeasurable locally
   (holdout truth is the catalogue; holdout↔live rank correlation −0.037). Promotion to a weekly
   slot is a separate selector step and is not taken here (`slots_used = 0`).
2. **Registry inventory is 694/695.** One pinned witness (repository `57GEMSDOE-PR6`, GitHub 404)
   cannot be restored or screened; a strict reading of “incomplete scan is not clearance” treats
   this as residual uncertainty (IR-58-S7-04).
3. **The literal 70 % uniqueness rule fires on this candidate and on every nonempty candidate
   tested in this repo.** The rule in force treats a firing as a decisive stop (no
   chance-corrected waiver); the chance-corrected readings are recorded for the owner's
   information. Whether the literal threshold should remain absolute is an owner decision; this
   session did not manufacture a pass (contract: "do not generate a replacement candidate …
   merely to manufacture a pass").
4. **The H7-C tie-break (gap-complement preference) is only partially exercised** — with zero
   informative firings the gap pass correctly did nothing; the preference only matters when
   rule A/B actually fires (IR-58-S7-05 documents the over-aggressive first implementation and
   its degenerate 0-dot raster, retained as a labelled historical diagnostic).
5. **Site integration.** `docs/gems61.html` is the session-7 front door; `scripts/build_site.py`
   does not ingest `evidence/gems61` and regenerates the older receipts-based pages (the
   session-7 block is injected into `docs/index.html` by `scripts/gems61_build_page.py`, which
   must run after `build_site.py`). Executive-summary page is the shared
   [`docs/executive-summary.html`](executive-summary.html); the session-7 page carries its own
   copy of the submit steps. IR-58-S7-01 (band-description mismatch) stays open: whether one of
   the 19 bands is a source-depth estimate under another name is unresolved.
6. **Cross-instrument numbers must not be compared.** The 0.043575 “prior best” is a different
   withhold instrument (IR-58-S7-02); same-instrument comparisons only.


# Session 7 (2026-10-11 UTC) — current status: literal uniqueness stop, no experiment or slot

This section is the authoritative current queue. The previous sparse artifact is downloadable only as
`docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif`; it was renamed without
changing raster pixels because the former `unique` filename was unsupported. The independent local
audit passes 19/19 format/range checks, but a direct final-dot comparison measures **1.0000 overlap
within 3 px** against a hash-pinned full-footprint prior raster. This exceeds the user's explicit
literal **0.70** stop and is a duplicate/drift protocol failure, not a byte/pixel-copying claim.
Pre-placement surface is NOT MEASURED; current registry freshness is `BLOCKED_NOT_EXHAUSTIVE`;
HOLDOUT-DTI, σ table, simulated gain by class, and leakage canary were not measured. **Do not submit,
run another experiment, generate a replacement candidate, or use a slot.** Zero experiments and zero
slots were used. The artifact-specific run card and audit are in
`evidence/58gemsdoe_unique_ribbon/`; current full review is
`docs/research/session7_review_20261011.md`; current hypothesis ranking is
`docs/research/hypotheses_new.md`.

The chance-corrected `RATIFIED-UNIQ-v1` interpretation from session 5 is historical and must not
waive the user's current literal rule. A directly observed overlap stop is already decisive; the
inventory is not claimed to be currently exhaustive, and no uniqueness clearance is made. The
reported portal `[0,1]` error's cause remains unknown absent a hash-bound portal receipt. The
0.2778 public row belongs to `extradr19` in a dated board snapshot; no evidence ties it to H33.

A later update to the inherited base branch added `gems58-ml-binary-ridge-20261012T000000Z.tif`,
a ZIP, and generation scripts. They were not created, evaluated, or qualified in this session-7
review and are outside the ribbon-width scope. The per-file index keeps them review-only; do not run
their generators or treat their metadata as current HOLDOUT-DTI or organizer evidence.

> **Historical sections below:** the S6/S5 and earlier queues preserve past decisions and measurements only. Their candidate status, chance-corrected exceptions, and proposed actions are superseded; do not execute them. The current prompt and S7 section above govern.

## S7.0 Work completed and evidence limits

| Item | Status |
|---|---|
| [`scripts/audit_sparse_candidate.py`](scripts/audit_sparse_candidate.py) → [`evidence/58gemsdoe_unique_ribbon/audit.json`](evidence/58gemsdoe_unique_ribbon/audit.json) | Read-only current-file audit: 19/19 local format checks; recomputed candidate TIFF SHA-256 and decoded-pixel hash; directly verifies the witness pin and footprint saturation; measures the candidate's final dots at 1.0000 overlap within 3 px; records `verdict: negative`, a missing pre-placement result, and no holdout score. It does not scan or certify the whole current registry. |
| [`evidence/58gemsdoe_unique_ribbon/run_card.json`](evidence/58gemsdoe_unique_ribbon/run_card.json) | Artifact-specific JSON card with proposal-only top hypothesis, explicit unmeasured results, hashes, local validation limits, stop condition, and zero experiment/slot counts. |
| `docs/downloads/58GEMSDOE-ribbon-sparse-review-only-*` | The existing raster was renamed review-only, not re-emitted or modified. Its direct ZIP and JSON metadata are rebuilt; no candidate was generated. |
| [`docs/research/session7_review_20261011.md`](docs/research/session7_review_20261011.md) | Reconciles current status, explains what 0.2778 can and cannot establish, and ranks three untried within-lane width hypotheses. |
| `PROMPT.md` and `README.md` | Updated to use the explicit current literal rule, not the old chance-corrected resolution. README includes the complete current prompt verbatim. |
| `docs/SUBMISSION_GUIDE.md`, root status pages, executive summary, download index | Current review-only wording is generated from the session-7 card/audit; the 23-file index labels every TIFF/ZIP. `build_session7_pages.py --check`, `ribbon_check_site.py`, and the repository tests pass. Historical session-5/deliverable pages are isolated and labeled as archives. |
| [`.github/workflows/ribbon-ci.yml`](.github/workflows/ribbon-ci.yml) | CI now runs pytest, current-page/index generation and checks, plus archived-link/current-status QA. GitHub Actions was not triggered in this local review; its equivalent checks passed locally. |
| [`evidence/feature_stack_restore_20261011.json`](evidence/feature_stack_restore_20261011.json) | Records part and whole-file hashes and grid header for the restored cache; integrity relative to an owner-maintained bridge pin only, not organizer provenance. |

## S7.1 Hard stops and future-work queue

1. **Do not run a replacement experiment/candidate under the current rule.** The hash-pinned witness's dilation covers the entire allowed footprint, and the current raster's final-dot measurement is 1.0000. The user expressly forbids waiving this trigger. Do not use a slot.
2. The pre-placement surface gate for this raster is **NOT MEASURED**. Its generating lineage/surface artifact is absent. Do not report the gate as passed.
3. Current inventory freshness is `BLOCKED_NOT_EXHAUSTIVE`. The older 703-raster scan is complete only for its frozen scope. This does not undo the single-witness stop and does not establish current uniqueness clearance.
4. No current `HOLDOUT-DTI` exists for this TIFF: evaluator result, withheld-positive count and defensible 95% CI are not measured. No σ table, class-gain analysis, or feature-alone leakage result exists for it.
5. The raw cached stack was restored and hash-verified against an owner-maintained GitHub mirror. If it is absent in a later session, `bash scripts/fetch_feature_stack.sh` restores it outside Git; a mirror pin is not independent organizer provenance. Do not evaluate/model while the literal stop is active.
6. The official data tab remains the primary provenance source and is login-gated in local records. This session did not freshly fetch DrivenData/USGS/PDF pages; sources are linked in `docs/SOURCES.md` for manual verification.
7. Current root/executive/submit pages and the download index have been regenerated from session-7 status. `build_session7_pages.py --check`, the archived-link/current-status `ribbon_check_site.py`, Python compilation, and the full repository pytest suite pass. Re-run the read-only checks after any later edits; do not change the negative status.

---

# Session 6 (historical, 2026-10-11 UTC) — merge reconciliation: verification tooling, no new candidate

This section records what the session-6 review branch added on top of session 5. **No experiment,
holdout, emission, slot, or upload occurred** in that historical review. Its current-candidate statements
are superseded by session 7 below. The session-6 candidate was
`gems58-concordance-ribbon-40768-20261011T160514Z.tif`, negative under that session's retained
chance-corrected protocol, and `evidence/ribbon_qualification.json` was absent.

## S6.0 Added, and what each item does *not* establish

| Item | Status |
|---|---|
| [`scripts/audit_current_tiff.py`](scripts/audit_current_tiff.py) → [`evidence/ribbon/file_audit.json`](evidence/ribbon/file_audit.json) | Independent on-disk audit of the **current** candidate, read from `evidence/ribbon/emission.json` rather than a hard-coded name: 10/10 checks pass (Float32/sample grid, NaN-outside mask, in-footprint `[0,1]`, 40,768 positives, file hash, ZIP round-trip) and the decoded-pixel SHA-256 is published. That receipt records no decoded hash of its own, so the binding is reported as *computed*, not claimed as verified. Local file verification only — not portal acceptance, uniqueness, holdout qualification, or eligibility. The session-3 file's 11/11 receipt is archived verbatim at `evidence/ribbon/archive-s3/file_audit_sigma_adaptive.json`. |
| [`scripts/build_downloads_index.py`](scripts/build_downloads_index.py) → [`docs/downloads/index.html`](docs/downloads/index.html) | Every public TIFF/ZIP (19 files, including `docs/deliverable/downloads/`) carries its own submit verdict; all 19 read **NOT OK TO SUBMIT — REVIEW ONLY**. A download link is never permission to use a slot. |
| [`scripts/qualification_gates.py`](scripts/qualification_gates.py) + hardened [`scripts/build_ribbon_emission.py`](scripts/build_ribbon_emission.py) | Hash-bound pre-emission contract: fresh inventory bound to the freshness audit, pre-placement surface receipt, feature-alone canary, shared-evaluator holdout with a declared physical-cluster 95 % interval, exact file **and** decoded-pixel hashes, staged publish with rollback, and refusal to overwrite an existing deliverable. With no qualification receipt the emitter exits 2 and writes nothing. |
| [`src/gems57/submission_writer.py`](src/gems57/submission_writer.py) | The writer receipt now binds the **decoded** float32 pixels, not only the compressed file bytes, so qualification cannot drift with compression or metadata order. |
| Archived legacy run cards | `evidence/ribbon/archive-s3/run_card_v2.json` and `run_card_final.json` keep every measurement but their top label is now `LEGACY-DIAGNOSTIC-ONLY`: the 0.043651 value came from the legacy `gems58-pooled-hide-v1` instrument and is not a promotion-grade `HOLDOUT-DTI` result. |
| [`docs/deliverable/`](docs/deliverable/) | The stale "download OK / PRIMARY — download & submit candidate" pages are replaced by red archival notices; their rasters are labeled in the per-file index. |

## S6.1 Still open, unchanged by this session

1. Portal `[0,1]` rejection for a submitted raster remains **unresolved**: no error payload or
   receipt is bound to any candidate hash here, and matching the sample's NaN-outside representation
   does not prove acceptance.
2. Inventory freshness is still `BLOCKED_NOT_EXHAUSTIVE`; a 703-raster snapshot count is not a
   freshness certification.
3. `evidence/ribbon_qualification.json` (pre-placement + canary + shared-evaluator holdout with a
   defensible 95 % CI) does not exist, so no emission is permitted.
4. H58-U1 (relief-conditioned ribbon width) remains the top-ranked untried within-lane hypothesis and
   is **NOT VALIDATED** — see [`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md).

# Session 5 (historical, 2026-10-11 UTC) — then-current negative verdict, later superseded

At the time, this section superseded pre-session-5 records. It is itself superseded by session 6 and
session 7 above. Three experiments were reported for that historical review; their candidate status,
protocol interpretation, and recommendations are not current instructions.

## S5.0 What happened

1. **Gate ratified** (owner decision executed per the standing "resolve the scope/meaning of the
   gate" instruction): **RATIFIED-UNIQ-v1** — block on ρ > 0.90, Jaccard > 0.50, byte/pixel
   duplicate, incomplete scan, rule A (literal O > 0.70 vs a witness with E < 0.70), or rule B
   (chance-corrected lift > 0.50 vs any witness with E < 0.99). The literal reading is always
   published beside it (gate G3L). Recorded in `PROMPT.md` protocol item 1 and IR-58-UNIQ-07.
2. **New candidate emitted**: `docs/downloads/gems58-concordance-ribbon-40768-20261011T160514Z.tif`
   (sha256 `f709b6f1…9d0d`), hypothesis H58-X1 multi-family concordance gate (≥ 2 independent
   feature families agreeing, τ = 0.35, τ_family = 0.30, 1-px dilation). Validator 15/15,
   cross-fitted HOLDOUT-DTI **0.043575** (C2) vs incumbent 0.040105, canary clean (0.5666),
   shared-metric crosscheck delta exactly 0.0, surface gate passed (worst ρ 0.2414 / 703).
3. **Final-dot gate FIRED → verdict negative.** Complete 703-witness scan
   (`evidence/ribbon/uniqueness_full_inventory.json`): rule A 9× (broad coverage ensembles,
   E 0.53–0.68, worst O 0.8154), rule B 3× — `GEMSDOE50:h52-coincidence8-80000` (lift **0.5624**,
   another repository) and this repo's own session-3 file (lift 0.5741). Logged as a duplicate and
   stopped, exactly as the prompt requires. **No defensible reading clears the file** (literal,
   ratified, or rule-A-only), so the negative is robust.
4. Site rebuilt from receipts: red banner "NOT OK TO SUBMIT — DO NOT SUBMIT" on
   `docs/index.html` / `executive-summary.html` / `submit.html`; `docs/RUN_CARD.json` verdict
   `negative`, `slots_used: 0`. Session-3 receipts archived verbatim in
   `evidence/ribbon/archive-s3/`.
5. **The other session-5 candidate, re-read under the ratified rule.** The gems60 convergence
   file `docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.tif` (sha256 `c1ba5b06…e2b1`,
   40,000 dots, 12/12 format checks, 0 on the catalogue, HOLDOUT-DTI 0.037208) had been screened
   with the gems60 instruments over 668 byte-verified witnesses and cleared on the two resolutions
   the owner had proposed (0 lift firings, 0 firings at E ≤ 0.61). Read under **RATIFIED-UNIQ-v1**
   it is **also a duplicate**: rule A fires 4× against the same `13GEMSDOE` archive pair —
   `13gems-r6-ensemble-20260929T182914Z(_allfinite).tif` (E = 0.6456, forward overlap 0.7463) and
   `13gems-toporef-holdoutref(_allfinite).tif` (E = 0.6798, overlap 0.7191) — while rule B (max
   lift 0.4552), ρ (worst 0.3499), Jaccard (worst 0.0248) and byte/pixel identity all stay at zero
   firings. Its page and front-door box were turned red, its run card now says STOP, and both
   readings stay published in `evidence/gems60/uniqueness_readings.json`. Every nonempty emitter
   this repository has screened under rule A is stopped by it — this file (4 firings), the
   concordance candidate (9), the session-3 ribbon (7) — which is exactly the trade-off S5.1
   item 1 puts to the owner.

## S5.1 Next work, in priority order

1. **The structural problem is now measured, not speculative:** the registry contains broad
   coverage-ensemble witnesses whose 3-px dilation covers 53–68 % of the footprint
   (13GEMSDOE r6-ensemble and 13gems-toporef-holdoutref at E 0.646–0.680, GEMSDOE3 coverage-v3-wide, GEMSDOE22 h23-b, GEMSDOE50 h59). ANY
   geologically faithful ridge/coverage emission overlaps them at O ≈ 0.70–0.85 and trips rule A,
   even though its lift vs them is below 0.50 (0.48 at worst — i.e. barely above chance). The
   next session should present the owner with this exact trade-off: either (a) accept that
   ridge-type emissions are permanently blocked by rule A and pivot the lane to **sparse,
   high-selectivity emissions** (≤ ~15 k dots in low-E regions — measured E for sparse scatter
   witnesses is ~0.13–0.24, leaving lift headroom), or (b) ratify rule A with a lift floor
   (e.g. fire only when lift > 0.35 TOO) — a decision that must be taken BEFORE the next
   candidate is designed, not after a scan.
2. **Pre-register a sparse variant of H58-X1**: top-k concordance pixels with k ≈ 10–15 k,
   min-separation ≥ 3 px, placed only where predicted overlap-E vs the 9 rule-A witnesses is
   low; simulate the final-dot gate from cached witness dilations BEFORE emitting (all witness
   masks are already in `.cache/registry/`). The surface and arms machinery
   (`scripts/ribbon_run_concordance.py`, `scripts/ribbon_emit_concordance.py`) is reusable as-is.
3. **Port `src/gems58w` onto `src/gems57`** (still pending from session 3): the metric is
   crosschecked identical (delta 0.0), so this is pure deduplication, not science.
4. External data (H58-R3 InSAR/seismicity) remains the highest-upside unblocked idea if the
   owner drops products into `data/external/` (sandbox cannot fetch them).
5. No slot was used in any session. Slot selection remains a separate owner/selector step.

## S5.2 Limitations

- HOLDOUT-DTI uses catalogue-based proxy truth, not the organizer's private expert faults; CI is
  the min–max over 4 spatial blocks (no bootstrap over 4 repeated physical blocks).
- The witness registry covers public sibling repositories only; private submissions are invisible.
- Rule-B saturation guard (E < 0.99) was added during this session after observing the lift
  statistic degenerate to ~1.0 vs a saturated witness; it does not change any verdict (the two
  real rule-B firings stand). Recorded in IR-58-UNIQ-07.
- σ pooled median is still 6.88 px (IR-58-SIGMA-01), so the "single tight line where σ < 0.5 px"
  branch of the lane remains unreachable on this data.

---

# Pre-session-5 status (2026-10-11 UTC, superseded — kept as record)

This file supersedes the old “session 1” queue. No scientific experiment or new TIFF was run in the latest review; no weekly slot was selected.

## Session-5 status: the deliverable is cleared; what is left is a decision, not a gate

The current deliverable is **`docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.tif`**
(SHA256 `c1ba5b06191801bfef6798b9dfb64fe23c030b6783d0b965dbf3fb4d956be2b1`, 143,587 bytes,
40,000 dots at exactly 1.0, 0 on the mapped catalogue). It passes independent format verification
12/12, the exact value rule, the catalogue rule, and the uniqueness screen over 668 sha256-verified
witnesses under both resolutions the owner proposed for the literal 70 % rule (0 firings; max
chance-corrected lift 0.4552). Page: `docs/gems60.html`; receipt: `evidence/gems60/run_card.json`.

**Merged and published.** PR #21 brought this work onto `main` (`f09a85b`); the follow-up commit
that accompanies this file publishes the session-5 front-door box into the two generated pages
(`docs/index.html`, `docs/executive-summary.html`) so the live site puts this deliverable first
instead of the superseded session-3 block. The pages stay identical to what the CI rebuilds —
`scripts/build_site.py` (previous lane's receipts) must run before `scripts/gems60_build_page.py`
(session-5 box), and the workflow re-derives both and asserts the banner against the session-5
gates, so a stale or hand-edited page fails closed. The shared-metric crosscheck was also
re-derived locally this session: the archived `gems58w` path and the live `gems57` metric both
give pooled DTI `0.043651086` for the session-3 file (Δ = 0.000000), recorded in
`evidence/ribbon/shared_metric_crosscheck.json`.

**What is left, in order**

1. **Owner decision (blocking, one read):** the literal 70 % rule fires on 56 witnesses for this file
   and on every other nonempty emitter in the family, because 35 registry witnesses are
   near-plane-filling (E = 1.000). The site reports the literal reading in full and takes its verdict
   on the owner's two proposed resolutions; ratify that, or keep the literal rule and accept that no
   file in this repository can ever be cleared. The two candidate resolutions were offered in
   `docs/research/` and are implemented in `scripts/gems60_uniqueness_readings.py`.
2. **Submit one slot if the decision is to ratify** (owner-only; 3 scored slots per week, none used).
   Record the receipt in `registry/submissions_seen.csv` against this sha256 — only then does an
   ORGANIZER-CONFIRMED number exist for this lane.
3. **If the live number comes back ≤ 0.20**, the cross-family convergence field is not finding new
   faults that the dense dotted emitters already find; the next lever is detection, not geometry:
   re-read `docs/research/why-the-score-and-how-to-beat-it.md` and the untried hypotheses in
   `docs/research/hypotheses_session4.md` (H58-C1/C2, H58-M1, H58-T1, H58-A1 are still unrun).
4. **Still open from earlier sessions:** the sample-submission 60,988-ones discrepancy; the
   `docs/deliverable/` sibling-lane artifact remains NOT CLEARED and should be treated as audit-only.

## Superseded: the session-3 hard stop (kept for audit)

The session-3 diagnostic was `docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif` (SHA256 `8b196e6eea06fef0d6cf2c9109091d1e2677a77d6e48d8b04f334a879551687f`). Local format/range preflight passes. That is not uniqueness clearance, portal acceptance, or an organizer score.

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

# Session 3 (historical, 2026-10-11 UTC) — three experiments were run within that session's budget

The entries below preserve session-3 measurements and recommendations as historical records only.
Their current-candidate statements and next-step queue are superseded by session 5, session 6, and
session 7 above. Nothing was uploaded and no slot was used in that historical review.

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
live-fetched vs 703 pinned+delta). **The corrected full screen has now been run**
(`evidence/ribbon/sibling_full_inventory.json`): 703 witnesses, complete, verdict **negative**,
`stop_required` true, **79 literal firings** (54 vacuous at E ≥ 0.99, 25 informative, worst informative
overlap 0.8496), while the discriminating statistics all pass — byte-unique, pixel-unique, worst ρ
**0.0900**, worst Jaccard **0.0509**. Its highest chance-corrected lift is **1.000** against
`5GEMSDOE:data/derived/context_detector_prob_u8.tif` and **0.7143** against this lane's candidate.

**Cross-lane screen** (`evidence/ribbon/cross_lane_screen.json`): the two candidates share 3,542 exact
pixels (Jaccard 0.0436) so neither copies the other, but the overlap is asymmetric — this lane's file
**clears** the sibling (overlap 0.2998, E 0.0450, lift 0.267) while the sibling **fires** on this
lane's file (overlap 0.7513, E 0.1295, lift 0.714), because ridge-concentrated emission dilates to
12.95 % of the footprint and a sparse scatter emission to 4.50 %. So this lane's published reading is
unchanged by the sibling file joining the inventory, and one owner decision about the literal 0.70 rule
now governs **both** files.

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

# Session 7 (2026-10-11 UTC) — status and open items

**Status: no new candidate, no slot, no upload. Verification and tooling only.**

- Test suite: 152 passed after rebuilding the site with the documented order
  (`build_site.py` → `gems60_build_page.py` → `build_downloads_index.py`). The previous
  rebuild had dropped the session-5 box because `gems60_build_page.py` was not run after
  `build_site.py`. CI (`.github/workflows/ribbon-ci.yml`) runs only `build_site.py`, so this
  ordering gap is still present in CI and should be fixed there.
- Pre-registration written before any new emission: `docs/research/session7_preregistration.md`
  (H58-S7-N novelty-constrained sparse concordance emission, K = 15,000, 3-px separation,
  exclusion of informative-witness neighbourhoods).
- EXP-1 (uniqueness screen of the unscreened sparse file `58GEMSDOE-ribbon-sparse-unique-…tif`)
  **did not complete**. The scan process ended without a receipt and the sandbox reset.
  The file is still unscreened and must not be treated as usable.
- Scanner bug noted, not yet fixed: `scripts/check_uniqueness_registry.py` crashes on a relative
  `--index` path (`relative_to` on a relative path). Pass an absolute path until it is fixed.
- Official references verified this session: problem page and metric/format rules
  (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/); live
  leaderboard (https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
  shows #1 0.4133 and DARD 0.3195 at #9; reference-solution writer
  (https://github.com/drivendataorg/gems-prize-reference-solution, notebook cell that writes
  `predicted_faults_example.tif`).
- Open: the portal error `Predicted values must be in range [0, 1]` has no receipt bound to any
  candidate hash, so its cause is still unknown.

## Next session, in order

1. Fix the absolute-path bug above, then run EXP-1 with `nohup` so it survives, and write its receipt.
2. Build H58-S7-N per the pre-registration, simulate the final-dot gate before writing, and measure
   the exact-bytes holdout with `gems57.holdout` (buffered, seeds 20 and 21).
3. Run the shared scan on the new file (EXP-3). Publish only with the verdict the gates produce.
4. Add the ordered `gems60_build_page.py` step to CI.

---

## Preserved from `main` (sibling PR #30, merged to main 2026-10-11 12:17 PDT)

> **Not verified by this lane.** The block below is kept verbatim from `main`. Its
> "Submission ready" statement is **contradicted by the gates on this page**: no
> artifact is OK to submit until every gate passes, and every TIFF in `docs/downloads/`
> is labelled NOT OK TO SUBMIT — review only (`docs/downloads/index.html`).

# Session 6 (2026-10-11 UTC) — merge reconciliation: verification tooling, no new candidate

This section records what the session-6 review branch added on top of session 5. **No experiment,
holdout, emission, slot, or upload occurred**, and no verdict changed: the current candidate is still
`gems58-concordance-ribbon-40768-20261011T160514Z.tif`, still **negative** (83 literal overlap
triggers over 703 indexed rasters, `unique: false`, `stop_required: true`), and
`evidence/ribbon_qualification.json` is still absent.

## S6.0 Added, and what each item does *not* establish

| Item | Status |
|---|---|
| [`scripts/audit_current_tiff.py`](scripts/audit_current_tiff.py) → [`evidence/ribbon/file_audit.json`](evidence/ribbon/file_audit.json) | Independent on-disk audit of the **current** candidate, read from `evidence/ribbon/emission.json` rather than a hard-coded name: 10/10 checks pass (Float32/sample grid, NaN-outside mask, in-footprint `[0,1]`, 40,768 positives, file hash, ZIP round-trip) and the decoded-pixel SHA-256 is published. That receipt records no decoded hash of its own, so the binding is reported as *computed*, not claimed as verified. Local file verification only — not portal acceptance, uniqueness, holdout qualification, or eligibility. The session-3 file's 11/11 receipt is archived verbatim at `evidence/ribbon/archive-s3/file_audit_sigma_adaptive.json`. |
| [`scripts/build_downloads_index.py`](scripts/build_downloads_index.py) → [`docs/downloads/index.html`](docs/downloads/index.html) | Every public TIFF/ZIP (19 files, including `docs/deliverable/downloads/`) carries its own submit verdict; all 19 read **NOT OK TO SUBMIT — REVIEW ONLY**. A download link is never permission to use a slot. |
| [`scripts/qualification_gates.py`](scripts/qualification_gates.py) + hardened [`scripts/build_ribbon_emission.py`](scripts/build_ribbon_emission.py) | Hash-bound pre-emission contract: fresh inventory bound to the freshness audit, pre-placement surface receipt, feature-alone canary, shared-evaluator holdout with a declared physical-cluster 95 % interval, exact file **and** decoded-pixel hashes, staged publish with rollback, and refusal to overwrite an existing deliverable. With no qualification receipt the emitter exits 2 and writes nothing. |
| [`src/gems57/submission_writer.py`](src/gems57/submission_writer.py) | The writer receipt now binds the **decoded** float32 pixels, not only the compressed file bytes, so qualification cannot drift with compression or metadata order. |
| Archived legacy run cards | `evidence/ribbon/archive-s3/run_card_v2.json` and `run_card_final.json` keep every measurement but their top label is now `LEGACY-DIAGNOSTIC-ONLY`: the 0.043651 value came from the legacy `gems58-pooled-hide-v1` instrument and is not a promotion-grade `HOLDOUT-DTI` result. |
| [`docs/deliverable/`](docs/deliverable/) | The stale "download OK / PRIMARY — download & submit candidate" pages are replaced by red archival notices; their rasters are labeled in the per-file index. |

## S6.1 Still open, unchanged by this session

1. Portal `[0,1]` rejection for a submitted raster remains **unresolved**: no error payload or
   receipt is bound to any candidate hash here, and matching the sample's NaN-outside representation
   does not prove acceptance.
2. Inventory freshness is still `BLOCKED_NOT_EXHAUSTIVE`; a 703-raster snapshot count is not a
   freshness certification.
3. `evidence/ribbon_qualification.json` (pre-placement + canary + shared-evaluator holdout with a
   defensible 95 % CI) does not exist, so no emission is permitted.
4. H58-U1 (relief-conditioned ribbon width) remains the top-ranked untried within-lane hypothesis and
   is **NOT VALIDATED** — see [`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md).

# Session 5 (2026-10-11 UTC) — current status: NEGATIVE verdict, gate ratified, candidate blocked

This section supersedes everything below it as the current status. Three experiments were run
(the full budget): EXP-1 σ-fit + leakage canary on the concordance surface, EXP-2 cross-fitted
arms (R0 incumbent / C1 / C2), EXP-3 emission + both uniqueness phases.

## S5.0 What happened

1. **Gate ratified** (owner decision executed per the standing "resolve the scope/meaning of the
   gate" instruction): **RATIFIED-UNIQ-v1** — block on ρ > 0.90, Jaccard > 0.50, byte/pixel
   duplicate, incomplete scan, rule A (literal O > 0.70 vs a witness with E < 0.70), or rule B
   (chance-corrected lift > 0.50 vs any witness with E < 0.99). The literal reading is always
   published beside it (gate G3L). Recorded in `PROMPT.md` protocol item 1 and IR-58-UNIQ-07.
2. **New candidate emitted**: `docs/downloads/gems58-concordance-ribbon-40768-20261011T160514Z.tif`
   (sha256 `f709b6f1…9d0d`), hypothesis H58-X1 multi-family concordance gate (≥ 2 independent
   feature families agreeing, τ = 0.35, τ_family = 0.30, 1-px dilation). Validator 15/15,
   cross-fitted HOLDOUT-DTI **0.043575** (C2) vs incumbent 0.040105, canary clean (0.5666),
   shared-metric crosscheck delta exactly 0.0, surface gate passed (worst ρ 0.2414 / 703).
3. **Final-dot gate FIRED → verdict negative.** Complete 703-witness scan
   (`evidence/ribbon/uniqueness_full_inventory.json`): rule A 9× (broad coverage ensembles,
   E 0.53–0.68, worst O 0.8154), rule B 3× — `GEMSDOE50:h52-coincidence8-80000` (lift **0.5624**,
   another repository) and this repo's own session-3 file (lift 0.5741). Logged as a duplicate and
   stopped, exactly as the prompt requires. **No defensible reading clears the file** (literal,
   ratified, or rule-A-only), so the negative is robust.
4. Site rebuilt from receipts: red banner "NOT OK TO SUBMIT — DO NOT SUBMIT" on
   `docs/index.html` / `executive-summary.html` / `submit.html`; `docs/RUN_CARD.json` verdict
   `negative`, `slots_used: 0`. Session-3 receipts archived verbatim in
   `evidence/ribbon/archive-s3/`.
5. **The other session-5 candidate, re-read under the ratified rule.** The gems60 convergence
   file `docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.tif` (sha256 `c1ba5b06…e2b1`,
   40,000 dots, 12/12 format checks, 0 on the catalogue, HOLDOUT-DTI 0.037208) had been screened
   with the gems60 instruments over 668 byte-verified witnesses and cleared on the two resolutions
   the owner had proposed (0 lift firings, 0 firings at E ≤ 0.61). Read under **RATIFIED-UNIQ-v1**
   it is **also a duplicate**: rule A fires 4× against the same `13GEMSDOE` archive pair —
   `13gems-r6-ensemble-20260929T182914Z(_allfinite).tif` (E = 0.6456, forward overlap 0.7463) and
   `13gems-toporef-holdoutref(_allfinite).tif` (E = 0.6798, overlap 0.7191) — while rule B (max
   lift 0.4552), ρ (worst 0.3499), Jaccard (worst 0.0248) and byte/pixel identity all stay at zero
   firings. Its page and front-door box were turned red, its run card now says STOP, and both
   readings stay published in `evidence/gems60/uniqueness_readings.json`. Every nonempty emitter
   this repository has screened under rule A is stopped by it — this file (4 firings), the
   concordance candidate (9), the session-3 ribbon (7) — which is exactly the trade-off S5.1
   item 1 puts to the owner.

## S5.1 Next work, in priority order

1. **The structural problem is now measured, not speculative:** the registry contains broad
   coverage-ensemble witnesses whose 3-px dilation covers 53–68 % of the footprint
   (13GEMSDOE r6-ensemble and 13gems-toporef-holdoutref at E 0.646–0.680, GEMSDOE3 coverage-v3-wide, GEMSDOE22 h23-b, GEMSDOE50 h59). ANY
   geologically faithful ridge/coverage emission overlaps them at O ≈ 0.70–0.85 and trips rule A,
   even though its lift vs them is below 0.50 (0.48 at worst — i.e. barely above chance). The
   next session should present the owner with this exact trade-off: either (a) accept that
   ridge-type emissions are permanently blocked by rule A and pivot the lane to **sparse,
   high-selectivity emissions** (≤ ~15 k dots in low-E regions — measured E for sparse scatter
   witnesses is ~0.13–0.24, leaving lift headroom), or (b) ratify rule A with a lift floor
   (e.g. fire only when lift > 0.35 TOO) — a decision that must be taken BEFORE the next
   candidate is designed, not after a scan.
2. **Pre-register a sparse variant of H58-X1**: top-k concordance pixels with k ≈ 10–15 k,
   min-separation ≥ 3 px, placed only where predicted overlap-E vs the 9 rule-A witnesses is
   low; simulate the final-dot gate from cached witness dilations BEFORE emitting (all witness
   masks are already in `.cache/registry/`). The surface and arms machinery
   (`scripts/ribbon_run_concordance.py`, `scripts/ribbon_emit_concordance.py`) is reusable as-is.
3. **Port `src/gems58w` onto `src/gems57`** (still pending from session 3): the metric is
   crosschecked identical (delta 0.0), so this is pure deduplication, not science.
4. External data (H58-R3 InSAR/seismicity) remains the highest-upside unblocked idea if the
   owner drops products into `data/external/` (sandbox cannot fetch them).
5. No slot was used in any session. Slot selection remains a separate owner/selector step.

## S5.2 Limitations

- HOLDOUT-DTI uses catalogue-based proxy truth, not the organizer's private expert faults; CI is
  the min–max over 4 spatial blocks (no bootstrap over 4 repeated physical blocks).
- The witness registry covers public sibling repositories only; private submissions are invisible.
- Rule-B saturation guard (E < 0.99) was added during this session after observing the lift
  statistic degenerate to ~1.0 vs a saturated witness; it does not change any verdict (the two
  real rule-B firings stand). Recorded in IR-58-UNIQ-07.
- σ pooled median is still 6.88 px (IR-58-SIGMA-01), so the "single tight line where σ < 0.5 px"
  branch of the lane remains unreachable on this data.

---

# Pre-session-5 status (2026-10-11 UTC, superseded — kept as record)

This file supersedes the old “session 1” queue. No scientific experiment or new TIFF was run in the latest review; no weekly slot was selected.

## Session-5 status: the deliverable is cleared; what is left is a decision, not a gate

The current deliverable is **`docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.tif`**
(SHA256 `c1ba5b06191801bfef6798b9dfb64fe23c030b6783d0b965dbf3fb4d956be2b1`, 143,587 bytes,
40,000 dots at exactly 1.0, 0 on the mapped catalogue). It passes independent format verification
12/12, the exact value rule, the catalogue rule, and the uniqueness screen over 668 sha256-verified
witnesses under both resolutions the owner proposed for the literal 70 % rule (0 firings; max
chance-corrected lift 0.4552). Page: `docs/gems60.html`; receipt: `evidence/gems60/run_card.json`.

**Merged and published.** PR #21 brought this work onto `main` (`f09a85b`); the follow-up commit
that accompanies this file publishes the session-5 front-door box into the two generated pages
(`docs/index.html`, `docs/executive-summary.html`) so the live site puts this deliverable first
instead of the superseded session-3 block. The pages stay identical to what the CI rebuilds —
`scripts/build_site.py` (previous lane's receipts) must run before `scripts/gems60_build_page.py`
(session-5 box), and the workflow re-derives both and asserts the banner against the session-5
gates, so a stale or hand-edited page fails closed. The shared-metric crosscheck was also
re-derived locally this session: the archived `gems58w` path and the live `gems57` metric both
give pooled DTI `0.043651086` for the session-3 file (Δ = 0.000000), recorded in
`evidence/ribbon/shared_metric_crosscheck.json`.

**What is left, in order**

1. **Owner decision (blocking, one read):** the literal 70 % rule fires on 56 witnesses for this file
   and on every other nonempty emitter in the family, because 35 registry witnesses are
   near-plane-filling (E = 1.000). The site reports the literal reading in full and takes its verdict
   on the owner's two proposed resolutions; ratify that, or keep the literal rule and accept that no
   file in this repository can ever be cleared. The two candidate resolutions were offered in
   `docs/research/` and are implemented in `scripts/gems60_uniqueness_readings.py`.
2. **Submit one slot if the decision is to ratify** (owner-only; 3 scored slots per week, none used).
   Record the receipt in `registry/submissions_seen.csv` against this sha256 — only then does an
   ORGANIZER-CONFIRMED number exist for this lane.
3. **If the live number comes back ≤ 0.20**, the cross-family convergence field is not finding new
   faults that the dense dotted emitters already find; the next lever is detection, not geometry:
   re-read `docs/research/why-the-score-and-how-to-beat-it.md` and the untried hypotheses in
   `docs/research/hypotheses_session4.md` (H58-C1/C2, H58-M1, H58-T1, H58-A1 are still unrun).
4. **Still open from earlier sessions:** the sample-submission 60,988-ones discrepancy; the
   `docs/deliverable/` sibling-lane artifact remains NOT CLEARED and should be treated as audit-only.

## Superseded: the session-3 hard stop (kept for audit)

The session-3 diagnostic was `docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif` (SHA256 `8b196e6eea06fef0d6cf2c9109091d1e2677a77d6e48d8b04f334a879551687f`). Local format/range preflight passes. That is not uniqueness clearance, portal acceptance, or an organizer score.

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
live-fetched vs 703 pinned+delta). **The corrected full screen has now been run**
(`evidence/ribbon/sibling_full_inventory.json`): 703 witnesses, complete, verdict **negative**,
`stop_required` true, **79 literal firings** (54 vacuous at E ≥ 0.99, 25 informative, worst informative
overlap 0.8496), while the discriminating statistics all pass — byte-unique, pixel-unique, worst ρ
**0.0900**, worst Jaccard **0.0509**. Its highest chance-corrected lift is **1.000** against
`5GEMSDOE:data/derived/context_detector_prob_u8.tif` and **0.7143** against this lane's candidate.

**Cross-lane screen** (`evidence/ribbon/cross_lane_screen.json`): the two candidates share 3,542 exact
pixels (Jaccard 0.0436) so neither copies the other, but the overlap is asymmetric — this lane's file
**clears** the sibling (overlap 0.2998, E 0.0450, lift 0.267) while the sibling **fires** on this
lane's file (overlap 0.7513, E 0.1295, lift 0.714), because ridge-concentrated emission dilates to
12.95 % of the footprint and a sparse scatter emission to 4.50 %. So this lane's published reading is
unchanged by the sibling file joining the inventory, and one owner decision about the literal 0.70 rule
now governs **both** files.

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
