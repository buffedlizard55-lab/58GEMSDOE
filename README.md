# 58GEMSDOE — DOE GEMS Prize Challenge

**Mission:** Maximize P(Win) and own the outcome, subject to evidence and no-go gates. **Current review (session 7, 2026-10-11 UTC): negative. Do not submit the downloadable raster.** This checkout's lane is ribbon width around existing ridge centerlines, calibrated from localization error. The task is geological fault detection, not geothermal-vent detection. Required gates take precedence over producing a TIFF.

## Current decision at a glance

- **Review-only artifact:** [`58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif) · [ZIP](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip) · [metadata](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.json). Its previous filename said `unique`; that claim was unsupported. It was renamed review-only without changing the raster bytes.
- **Literal uniqueness stop:** the direct final-dot measurement found **1.0000** of the candidate dots within 3 px of one hash-pinned registry raster, above the active **70%** stop. The witness's 3 px dilation covers the full bridged footprint. This is a protocol stop, not proof of byte- or pixel-copying. Do not waive it using the old chance-corrected reading.
- **Local format/range audit:** 19/19 checks pass; this is not uniqueness clearance, holdout evidence, or organizer/portal acceptance. The candidate TIFF has `nodata=null`, while the sample has `nodata=NaN`; portal handling is unconfirmed.
- **Unmeasured:** pre-placement surface, current exhaustive inventory clearance, HOLDOUT-DTI, σ table, simulated gain by class, and leakage canary. No score is projected.
- **This review:** zero experiments; zero slots used; no upload. The feature-stack cache was restored and hash-checked against an owner-maintained GitHub bridge pin, not independently authenticated by the competition.

Full review: [`docs/research/session7_review_20261011.md`](docs/research/session7_review_20261011.md). Current issue/status log: [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md). Artifact-specific JSON run card: [`evidence/58gemsdoe_unique_ribbon/run_card.json`](evidence/58gemsdoe_unique_ribbon/run_card.json); audit receipt: [`evidence/58gemsdoe_unique_ribbon/audit.json`](evidence/58gemsdoe_unique_ribbon/audit.json).

**Post-review base-branch notice:** a separate file, [`gems58-ml-binary-ridge-20261012T000000Z.tif`](docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif), its [ZIP](docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.zip), and [sidecar record](docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.evidence.json) were added to the base branch after this session-7 review. This review did not generate, evaluate, or qualify that artifact. It is outside this checkout's current ribbon-width task and is **not approved for submission**; the per-file download index labels it review-only. Do not run its generation scripts or use sidecar fields as current HOLDOUT-DTI or organizer evidence.

## Requested deliverables and evidence

| Deliverable | Current record | What it says |
|---|---|---|
| Downloadable GeoTIFF | [`review-only TIFF`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif), [`ZIP`](docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip) | Available for audit only; **NOT OK TO SUBMIT — DO NOT SUBMIT**. No file is labeled unique or ready. |
| Executive submission guide | [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md), [`docs/submit.html`](docs/submit.html), [`docs/executive-summary.html`](docs/executive-summary.html) | Updated status and organizer-receipt requirements; local preflight is not portal acceptance. |
| Ranked within-lane hypotheses | [`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md) | Three proposal-only ribbon-width tests; H58-U1 relief-conditioned width ranks first. None is implemented or validated. |
| 0.2778 score discrepancy | [`docs/research/why-02778.md`](docs/research/why-02778.md), [`session-7 review §3`](docs/research/session7_review_20261011.md#3-highest-score-attribution-what-can-and-cannot-be-answered), [`docs/LEADERBOARD.md`](docs/LEADERBOARD.md) | The dated public board associates 0.2778 with `extradr19`. No hash/receipt ties it to the GEMSDOE32 H33 file; the H33 owner page calls 0.2747 a projection. Why `extradr19` scored 0.2778 is unknown from the available records. |
| Auditable sources | [`docs/SOURCES.md`](docs/SOURCES.md), [`evidence/feature_stack_restore_20261011.json`](evidence/feature_stack_restore_20261011.json) | Official sources are linked and evidence classes separated. The official DrivenData/USGS/PDF pages were not freshly fetched in this session; the stack pin is an owner-mirror integrity check only. |
| JSON run card | [`evidence/58gemsdoe_unique_ribbon/run_card.json`](evidence/58gemsdoe_unique_ribbon/run_card.json) | Records the negative verdict, stop, unmeasured holdout and surface gates, hashes, validator, zero experiments, and zero slots. |

## Current artifact facts

The downloadable raster is one float32 band on the 100 m sample grid (EPSG:32611, 3730 × 3292; transform `[100,0,243350,0,-100,4508550]`). It has 15,000 positive pixels, each exactly `1.0`; all values are finite and within `[0,1]`, outside-footprint positives are zero, and there are no positive pixels on the bridged mapped catalogue. Raster SHA-256: `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`. Decoded-pixel SHA-256: `21178ff6da8eef1bc286826deb963224a7909c0ee4f318dc4feac7a9e1ff5b15`.

The review witness is `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`, SHA-256 `03d619fa75689b48bd3eb4f74c3fa529a9b04c19bd716e15640d910baf3d5a90`. The public blob bytes match this owner-maintained registry pin. Its positive support covers 5,167,373/5,167,373 bridged footprint cells and leaves zero uncovered after 3 px dilation; the candidate's measured overlap is 1.0. The repository's older 703-raster scan is complete only for its frozen scope; the current inventory freshness record remains `BLOCKED_NOT_EXHAUSTIVE`. One literal stop is sufficient to block this raster, but neither a fresh exhaustive scan nor a complete uniqueness clearance is claimed.

## Evidence labels and score attribution

A model result must be labeled **HOLDOUT-DTI** and include shared evaluator/version, withheld-positive count, protocol, and a defensible 95% CI. If not measured, say so. A competition score may be **ORGANIZER-CONFIRMED** only with a receipt/hash crosswalk for the exact artifact. Public-board observations are dated **PUBLIC-LEADERBOARD-SNAPSHOT** records, never scores for a local TIFF without that crosswalk. A projection, raster property, format check, or local proxy is not a competition score.

For the 0.2778 question: the local dated 2026-10-11 public-board snapshot places `extradr19` at 0.2778 (rank 23 in one saved observation). The GEMSDOE32 owner-maintained H33 page says “no organizer score” and describes 0.2747 as a projection. No submission receipt or hash crosswalk identifies the H33 TIFF with `extradr19`. Therefore the claim that H33 scored 0.2778 is unsubstantiated, and the cause of `extradr19`'s public score cannot be inferred from the row alone. The saved board also records 0.4133 for xiaofanhu and 0.3195 for DARD; these are dated snapshots, not today's live board. No score forecast is made for this repository's raster.

## Safe review commands

These audit or documentation commands do not run experiments or emit candidate rasters:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_sparse_candidate.py \
  --witness .cache/registry/universal-blocker.tif
.venv/bin/python scripts/build_downloads_index.py
.venv/bin/python scripts/build_session7_pages.py
PYTHONPATH=src .venv/bin/python -m pytest -q
```

Do not run experiment/emission/slot/upload commands after the literal stop. The former `scripts/build_site.py` and `scripts/gems60_build_page.py` render historical sessions; the session-7 builder owns current pages. The standing prompt caps work at three experiments or two hours, stops on the literal rule, and requires shared `gems57.evaluate_holdout` and `gems57.submission_writer` if a future experiment is authorized. See `PROMPT.md` and `REMAINING_WORK.md` before further work.

## Session-start reading order

At the start of each session, read `PROMPT.md`, `README.md`, and `REMAINING_WORK.md` in full, then the current status and linked evidence. The **complete current operating prompt** is reproduced verbatim below and is also kept as [`PROMPT.md`](PROMPT.md).

<!-- BEGIN FULL PROMPT: PROMPT.md -->

# Standing project prompt — 58GEMSDOE

Read this file, `README.md`, and `REMAINING_WORK.md` at the start of each session, then read the current status/evidence documents they point to. This is the operating contract. If a request to produce or submit a TIFF conflicts with a hard validation or uniqueness stop, preserve the gate, report the negative result, and do not manufacture a clearance.

## Mission and lane

Work on the DOE GEMS Prize Challenge (DrivenData competition 306). The target is geological faults indicative of geothermal resources, not geothermal vents. The strategic goal is to maximize the probability of winning and own the outcome. Work autonomously; do not request manual input. Use official or trusted sources and state uncertainty where access or provenance is incomplete rather than filling gaps with assumptions. This checkout's lane is **ribbon width calibrated to measured localization error**. Keep an existing ridge-placement surface fixed; vary only width/offset/ribbon support around already-detected ridges. Do not switch to a detector, another feature/detection lane, alternate competition lane, or submission-slot work. Never claim a ribbon can detect a fault for which the fixed ridge surface has no nearby ridge.

The requested deliverables remain: a clearly labeled downloadable GeoTIFF, executive submission guide, ranked within-lane hypotheses, source-bounded explanation of the disputed 0.2778 score, auditable sources, and a JSON run card. A negative verdict is acceptable; never label a file unique or ready without the required evidence. A link or local artifact label does not authorize a competition submission.

A qualifying, unique, downloadable GeoTIFF is the goal, but uniqueness and validation are **gates, not labels**. A failed or unmeasured gate means **NOT OK TO SUBMIT — DO NOT SUBMIT**. Never copy a prior submission except for learning. Never select or use a competition slot during research and never upload while researching.

## Uniqueness stop — use the literal rule for this task

Compare the candidate-specific pre-placement surface **before placement/emission** and the final dots against the accessible registry. Stop and record a duplicate/drift failure if **either**:

1. surface rank correlation with any one registry raster is **greater than 0.90**; or
2. **more than 70%** of the candidate's final positive dots fall within **3 pixels** of any one registry raster's positive dots.

Do not waive, reinterpret, chance-correct, or exempt a firing because the witness is dense, saturated, a lattice, a blanket, a carrier, or believed to be non-discriminating. The chance-corrected `RATIFIED-UNIQ-v1` text retained in older records is superseded for this current-session task where it conflicts with this literal rule. An incomplete or stale registry is not clearance. A directly observed literal trigger is decisive; do not generate a replacement candidate, use a slot, or keep searching for a non-triggering witness merely to manufacture a pass. If the pre-placement surface or required registry evidence is unavailable, record that gate as NOT MEASURED / BLOCKED, not passed.

A literal overlap trigger is a protocol stop; by itself it is **not** proof of byte copying, pixel copying, or intentional reuse. State only what the measurements show.

## Evidence labels and score attribution

- A model result is reportable only as **HOLDOUT-DTI**, with the shared evaluator and version, withheld-positive count, protocol, and a defensible 95% confidence interval. If it was not run, write `NOT MEASURED`; do not substitute zero, a projection, or an older artifact's result.
- Use **ORGANIZER-CONFIRMED** for a competition score only if an organizer receipt or equivalent submission record ties the exact raster hash to that score. A public participant-board entry is a separately labeled, dated **PUBLIC-LEADERBOARD-SNAPSHOT**, never a score attributed to a local TIFF without a hash/receipt crosswalk.
- A projection, local proxy, raster property, format preflight, and public leaderboard row are not a score for this repository's TIFF.
- The saved 2026-10-11 board observation recorded xiaofanhu at 0.4133, DARD at 0.3195, and extradr19 at 0.2778. These are dated public rows, not fresh live-board results and not local file scores. The GEMSDOE32 owner-maintained H33 page says its artifact has no organizer score and calls 0.2747 a projection. There is no receipt/hash crosswalk connecting H33 to extradr19's 0.2778. The cause of the actual extradr19 result is not established by its public score alone. See `docs/LEADERBOARD.md`, `docs/research/why-02778.md`, and `docs/SOURCES.md`.

## PARALLEL-RUN PROTOCOL — mandatory

## Holdout and shared tooling

Reuse the cached feature stack, shared `gems57.evaluate_holdout`, and `gems57.submission_writer`. Do not create or use a private metric, scoring, evaluator, holdout, or writer fork. If a shared tool is wrong, fix the shared implementation and regression tests once.

Any authorized experiment must:

- withhold buffered **whole fault segments**;
- derive catalogue-based features only from visible faults;
- mask visible faults pixel-exactly;
- use pooled DTI with α=0.2, β=0.8, and a 300 m triangular kernel;
- test each feature alone as a leakage canary; AUC >0.90 is leakage until explained; and
- report evaluator/version, withheld-positive count, protocol, and a defensible 95% CI.

Do not reuse legacy holdout values as current evidence. A result on known-catalogue faults estimates performance on that proxy truth; it does not establish performance on the organizer's hidden faults.

## Ribbon-width calibration and hypotheses

Before implementation, review the prior-session status and rank **3–5 genuinely untried within-lane hypotheses** by expected relative benefit, uncertainty, and cost. Name the feature layers and physical signature, a plausible named non-fault mimic, how the proposal differs from existing code, and the official source for any proposed external data. Explain why a width/offset change might capture a nearby uncatalogued fault only where the existing ridge is already present. Keep the top hypotheses and falsifiers in `docs/research/hypotheses_new.md`.

Measure localization error on training-only spatial blocks by block, feature resolution, ridge type, and any preregistered conditioning variable. Do not tune on the outer holdout. Choose ribbon widths/offsets only using exact max-credit marginal metric changes, including interactions and redundant predictions. For a pattern change use:

`U = (1 − αs)·ΔTP − αs·ΔFP`

where `s` is current DTI and `ΔTP`,`ΔFP` are exact marginal changes. The shortcut `k > αs` is valid only for one added, non-redundant dot with fresh truth credit `ΔTP=k` and FP increment `ΔFP=1−k`.

## Budget, stopping, and artifacts

- Run at most **three experiments or two hours**, whichever comes first.
- Stop immediately on a literal uniqueness trigger, stale/incomplete required inventory, leakage-canary failure, an invalid holdout, or a nonpositive/uncertain primary result under the preregistered rule. Do not add experiments because a result is weak.
- Do not run an experiment, emit or regenerate a prediction candidate, use a slot, or upload after a literal uniqueness stop.
- Keep a downloadable GeoTIFF only with an unmistakable per-file warning when qualification is incomplete. A failed artifact may be available for audit; its name/button is not permission to submit. Never label it unique or ready without the required evidence.
- Reconcile project docs and generated pages with the evidence. Do not leave a stale green badge, incorrect score claim, or unverified causal diagnosis in the README, front page, download index, or submission guide.

## Required end-of-review JSON run card

Maintain an artifact-specific machine-readable card containing:

- hypothesis, mechanism, and named non-fault mimic (or explicit proposal-only / not run);
- HOLDOUT-DTI value and evaluator/version, withheld-positive count, protocol and defensible 95% CI, or explicit `NOT MEASURED`;
- pre-placement surface and final-dot registry results separately, including inventory scope/freshness and an explicit unmeasured state where needed;
- raster SHA-256 and decoded-pixel SHA-256 if measured;
- local validator output clearly separated from organizer acceptance;
- submission/artifact name and a note of at most 140 characters;
- experiment/slot counts; and
- an unmistakable `promote` or `negative` verdict, with stop status.

Negative results are valid deliverables. Do not turn missing evidence into a pass.

## Current status — session 7, 2026-10-11 UTC

- Existing raster: `docs/downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif` (15,000 positive dots, SHA-256 `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`). Its former filename contained `unique`; it was renamed review-only without changing raster bytes. **Do not submit.**
- The local format/range audit passes 19/19 checks, not organizer acceptance. Candidate nodata metadata is null while the sample's is NaN; portal acceptance is unconfirmed.
- Direct final-dot comparison with a hash-pinned registry raster measured overlap 1.0000 within 3 px. This exceeds the literal 70% stop. The witness's 3-px support covers the entire bridged footprint. This is a duplicate/drift protocol stop, not proof of byte or pixel copying.
- Pre-placement surface is NOT MEASURED. The current registry freshness audit is BLOCKED_NOT_EXHAUSTIVE. No holdout-DTI, σ table, simulated gain by class, or leakage canary was measured for this TIFF. No score is projected.
- Experiments this review: 0. Slots used: 0. Nothing was uploaded. Verdict: `negative`.
- Full session record: `docs/research/session7_review_20261011.md`; run card: `evidence/58gemsdoe_unique_ribbon/run_card.json`; audit: `evidence/58gemsdoe_unique_ribbon/audit.json`; status log: `docs/IRREGULARITIES.md`.

## Official source links

- [Competition problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition About page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Official data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login may be required.
- [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — dynamic; refresh directly before relying on rank.
- Source/evidence register: `docs/SOURCES.md`.

<!-- END FULL PROMPT: PROMPT.md -->
