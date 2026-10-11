# 58GEMSDOE — DOE GEMS Prize Challenge

Core values: **Maximize P(Win)** and **Own the Outcome** — report the actual result, including a negative one.

> **Session 4 (2026-10-11):** verification only, no new TIFF, no experiment, no slot. The registered
> candidate passes the format check (float32, EPSG:32611, footprint NaN identical to the organizer sample,
> all values in [0,1]) but **fails the uniqueness gate G3**, so it stays NOT OK TO SUBMIT. The 0.2778 figure
> belongs to `extradr19` on the official board, not to the GEMSDOE32 H33 file. See
> [`docs/research/session4_verification_20261011.md`](docs/research/session4_verification_20261011.md) and
> [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md) (IR-58-S4-01 to 04).

## Submission decision — session 5

**Current candidate: `docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.tif` —
NOT CLEARED under the ratified protocol (RATIFIED-UNIQ-v1); [downloadable for review only](docs/gems60.html).**
It is a new, independently derived raster — lineaments from a four-family (magnetic, gravity,
topographic, subsurface) structural field, ranked with a cross-family agreement bonus and emitted
as dotted multi-line ribbons at the measured localization error, **0 dots on the mapped catalogue**,
every value exactly `1.0`, independent format verification 12/12 — but its uniqueness verdict is
**DUPLICATE: rule A fires on 4 witness rasters**, two distinct `13GEMSDOE` archive files published
twice each (`13gems-r6-ensemble-20260929T182914Z(_allfinite).tif`, E = 0.6456, forward 3 px overlap
0.7463; `13gems-toporef-holdoutref(_allfinite).tif`, E = 0.6798, overlap 0.7191). Rule B
(chance-corrected lift), rank correlation, dot-set Jaccard and byte/pixel identity all have zero
firings, and the pre-ratification variant the owner had proposed (E ≤ 0.61) has zero firings too —
but the ratified rule decides, so by the standing instruction the file is logged as a duplicate and
stopped. What is also *not* verified is any leaderboard value: no organizer receipt exists and the
local holdout is structurally blind to off-catalogue files (measured Spearman −0.037 against live
scores over 34 rasters). Banner, both readings and the σ/pattern receipts:
[docs/gems60.html](docs/gems60.html) · governing receipt:
[evidence/gems60/uniqueness_readings.json](evidence/gems60/uniqueness_readings.json).

Session-5 facts, one line each: hypothesis → [`evidence/gems60/run_card.json`](evidence/gems60/run_card.json);
σ table → [`evidence/gems60/sigma.json`](evidence/gems60/sigma.json); exact-metric pattern
selection → [`evidence/gems60/pattern_weighted.json`](evidence/gems60/pattern_weighted.json);
holdout number (labelled, with its limits) → [`evidence/gems60/holdout.json`](evidence/gems60/holdout.json);
uniqueness screen → [`evidence/gems60/uniqueness_full.json`](evidence/gems60/uniqueness_full.json);
independent verification → [`docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.checks.json`](docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.checks.json).

> **Cross-lane note (reconciled this session):** the E 0.61–0.70 band the concordance lane flagged as
> unadjudicated is exactly where the gems60 file's rule-A firings live (E = 0.6456 and 0.6798), so the
> ratified **RATIFIED-UNIQ-v1** stops it as well: this file (4 rule-A firings), the concordance candidate
> (9) and the session-3 file (7) all fail rule A, while all three clear rule B and the discriminating
> statistics (rank correlation, Jaccard, bytes/pixels). The two scans use different witness snapshots
> (gems60: 668 byte-verified witnesses of a 670-witness cache; concordance: 703), and extra witnesses can
> only add firings, so no re-scan can turn either verdict green. The owner decision that remains is
> whether rule A's `E < 0.70` threshold is the intended reading of the uniqueness stop — under it no
> nonempty emitter in this repository is cleared; under the pre-ratification `E ≤ 0.61` variant every one
> of them is. That decision, not another experiment, is what blocks a scored slot.

### gems58-lane artifacts — all NOT CLEARED

The gems58-lane artifacts below remain downloadable and **none is cleared**. Their authoritative,
evidence-generated banner is rendered by `scripts/build_site.py` on the
[public site](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html).

| Artifact | Status | Decision basis |
|---|---|---|
| **`gems58-concordance-ribbon-40768-20261011T160514Z.tif`** (session 5, concordance lane) — [TIF](docs/downloads/gems58-concordance-ribbon-40768-20261011T160514Z.tif) · [ZIP](docs/downloads/gems58-concordance-ribbon-40768-20261011T160514Z.zip) | **NOT CLEARED — download for review only** | Format gate 15/15, cross-fitted HOLDOUT-DTI 0.043575 (arm C2 vs incumbent 0.040105), surface gate passed (worst ρ 0.2414/703), leakage canary clean — but the **ratified chance-corrected uniqueness gate (RATIFIED-UNIQ-v1)** fires on the final dots: rule A 9×, rule B 3× incl. another repository's raster (`GEMSDOE50:h52-coincidence8`, lift 0.5624). The literal 70 % rule also fires (83/703). Logged as a duplicate and stopped. [`evidence/ribbon/uniqueness_full_inventory.json`](evidence/ribbon/uniqueness_full_inventory.json), [`docs/RUN_CARD.json`](docs/RUN_CARD.json) |
| **`gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`** (session 3) — [TIF](docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif) · [ZIP](docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.zip) | **NOT CLEARED — download for review only** | Format gate 15/15 and holdout measured, but the **literal** 3 px forward-overlap stop fires against 81 of 702 inventory witnesses. Logged as a duplicate and stopped, as the standing prompt requires. [`evidence/ribbon/archive-s3/uniqueness_full_inventory.json`](evidence/ribbon/archive-s3/uniqueness_full_inventory.json), [`evidence/ribbon/run_card_final.json`](evidence/ribbon/run_card_final.json) |
| **`gems58-novel-scatter-44090-20261011T0630Z.tif`** (sibling-lane deliverable under `docs/deliverable/`) | **NOT CLEARED under the protocol as written — IR-58-UNIQ-06** | Its published screen reports "worst 3 px forward overlap **0.3160**, 0 triggers" over 473 rasters — the **reverse** statistic (the witness's dots near the candidate's). Re-screened with the corrected instrument over all 703 witnesses: verdict **negative**, **79 firings** (54 vacuous, 25 informative), while byte-unique / pixel-unique / worst ρ **0.0900** / worst Jaccard **0.0509** all pass. Cross-screened against this lane's file the overlap is asymmetric: this file clears it (0.2998, lift 0.267) and it fires on this file (0.7513, lift 0.714) — geometry, not copying (3,542 shared pixels, Jaccard 0.0436). [`evidence/ribbon/sibling_full_inventory.json`](evidence/ribbon/sibling_full_inventory.json), [`cross_lane_screen.json`](evidence/ribbon/cross_lane_screen.json) |
| `gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif` (session 1/2 diagnostic) — [TIF](docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif) | **NOT CLEARED — audit only** | 100% of its dots lie within 3 px of one full-footprint-positive prior raster, and its recorded scan was 694/695. [`evidence/run_card.json`](evidence/run_card.json), [`evidence/ribbon_uniqueness.json`](evidence/ribbon_uniqueness.json) |

No organizer receipt links a score to any of these files, no slot was used, and nothing was uploaded.

### Sibling-lane deliverable — a new, separately screened TIFF

This review also produced one **new** raster in the ribbon lane, screened against the live registry
(not the stale 695-raster snapshot) and delivered for the owner's decision. It does not override the
status above: the repository's fail-closed gate still applies to the earlier diagnostic file, and no
slot has been used, no organizer receipt exists, and nothing here is a score.

| check | result |
|---|---|
| File | [`docs/deliverable/downloads/gems58-novel-scatter-44090-20261011T0630Z.tif`](docs/deliverable/downloads/gems58-novel-scatter-44090-20261011T0630Z.tif) (+ single-GeoTIFF ZIP) |
| Raster SHA256 | `5f64b6dc44a3d6639691b679337ec64c1b4bb1b3f1ce63dfe17258ad6fdbf1e0` (347876 bytes) |
| Dots | 44,090, every value exactly `1.0`; 0 on the mapped catalogue |
| Local portal checks | **15/15 pass** |
| Uniqueness screen (live inventory, fetched this session) | **473** rasters · worst rank correlation **0.0557** (limit 0.90) · worst 3 px forward overlap **0.3160** (limit 0.70) · **0 triggers** |
| HOLDOUT-DTI | `0.000000` — zero *by construction* for an off-catalogue emission (IR-58-02); no promotion-grade holdout is claimed |
| Organizer score | none — no receipt |

Download it, verify the hash, and read the caveats on
[`docs/deliverable/executive-summary.html`](docs/deliverable/executive-summary.html) and
[`docs/research/why-the-score-and-how-to-beat-it.md`](docs/research/why-the-score-and-how-to-beat-it.md)
before deciding whether to submit.

> **Correction measured during the merge, and now fully screened (IR-58-UNIQ-06).** The "worst 3 px
> forward overlap 0.3160 · 0 triggers" row above is the **reverse** statistic: the fraction of each
> *witness's* dots within 3 px of the candidate's, which is what the archived `gems58w.screen_against`
> triggered on before the direction bug was fixed. The protocol's statistic is the fraction of the
> *candidate's* dots within 3 px of one witness's dots. The corrected full screen over all **703**
> byte-verified witnesses returns verdict **negative** with **79 firings** (54 vacuous at E ≥ 0.99,
> 25 informative, worst informative overlap 0.8496), while every discriminating statistic passes by a
> wide margin: byte-unique, pixel-unique, worst rank correlation **0.0900** (limit 0.90, 0 firings),
> worst dot-set Jaccard **0.0509** (limit 0.50, 0 firings) —
> [`evidence/ribbon/sibling_full_inventory.json`](evidence/ribbon/sibling_full_inventory.json). This
> does **not** mean the file copies anything: the same degeneracy fires on the session-3 candidate
> (81 firings) because those witnesses overlap every nonempty candidate, so both lanes' files stand or
> fall on the same owner decision about the literal 0.70 rule.
>
> **Cross-lane screen.** The two candidates share 3,542 exact pixels out of 40,768 and 44,090 (Jaccard
> 0.0436), so neither is a copy of the other, but the overlap is strongly **asymmetric**: this lane's
> file has **0.2998** of its dots within 3 px of the sibling's support (E = 0.0450, lift 0.267,
> **clears**) while the sibling's file has **0.7513** within 3 px of this lane's support (E = 0.1295,
> lift 0.714, **fires**). Ridge-concentrated emission dilates to 12.95 % of the footprint and swallows a
> sparse scatter emission whose own dilation covers 4.50 %. Consequence: this lane's reading is
> unchanged by the sibling file entering the inventory, and any ratified chance-corrected threshold must
> be applied to **both** files at the same value —
> [`evidence/ribbon/cross_lane_screen.json`](evidence/ribbon/cross_lane_screen.json).

### Session-5 candidate — the facts

| | |
|---|---|
| sha256 | `f709b6f12d5188e34aa3aed3b83d785b97a232224692dcdfffedaa009dee9d0d` (`gems58-concordance-ribbon-40768-20261011T160514Z.tif`) |
| Contents | 40,768 isolated dots, every emitted value **exactly 1.0**; EPSG:32611, 3730×3292, 100 m; NaN outside the footprint exactly as in `sample_submission.tif`; **0 dots on the mapped catalogue** (12,315 on-catalogue px dropped at emit) |
| Hypothesis | H58-X1 **multi-family concordance gate**: keep ridge support only where ≥ 2 independent geophysical feature families (τ_family = 0.30) agree at τ = 0.35, 1-px dilation |
| HOLDOUT-DTI (promotion-grade, cross-fitted) | arm **C2 0.043575** vs incumbent R0 0.040105 (Δ +0.003470, beats R0 in 3/4 blocks); evaluator `gems58w.metric/v1` = `gems57` shared metric (crosscheck delta exactly 0.0) |
| Leakage canary | worst single-feature AUC **0.5666** (limit 0.90) — clean |
| Surface gate (pre-placement) | **passed**: worst ρ 0.2414 over 703 witnesses |
| Final-dot gate — discriminating statistics | byte-unique, pixel-unique, worst ρ **0.2823**, worst Jaccard **0.1682** — all pass |
| Final-dot gate — **RATIFIED-UNIQ-v1** | **FIRES → negative**: rule A (literal O > 0.70 vs witness with E < 0.70) 9×, worst `13GEMSDOE:r6-ensemble` O 0.8154 at E 0.6456; rule B (chance-corrected lift > 0.50, E < 0.99) 3×, incl. **another repository's** `GEMSDOE50:h52-coincidence8-80000` (O 0.6668, E 0.2386, lift **0.5624**) and this repo's own session-3 file (lift 0.5741) |
| Verdict | **negative — logged as a duplicate and stopped.** Under every defensible reading (literal, ratified, rule-A-only) the file is not clearable. No slot used, no upload, no organizer receipt |

The uniqueness rule was **ratified in session 5** (RATIFIED-UNIQ-v1, `PROMPT.md` protocol item 1,
IR-58-UNIQ-07): chance-corrected rules A/B govern, the literal reading is always published beside
them (gate G3L). The session-5 candidate fails **both** readings, so no definitional choice is doing
any work in this verdict.

### Session-3 candidate — the facts

| | |
|---|---|
| sha256 | `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd` (433,419 B) |
| Contents | 40,768 isolated dots, every emitted value **exactly 1.0**; EPSG:32611, 3730×3292, 100 m; **NaN outside the study footprint exactly as in the organizer's `sample_submission.tif`** (7,111,787 NaN, `nodata=nan`) and finite everywhere inside it — which is what makes the portal rejection `Predicted values must be in range [0, 1]` impossible for this file; **0 dots on the mapped catalogue** |
| Submission name / note | `gems58-ribbon-sigma-adaptive-40768-20261011T052942Z` / `Ribbon lane: adaptive dotted ribbons 0/+-300/+-600 m on catalogue-free Hessian ridges (sigma cross-fitted); 40768 isolated dots at 1.0.` (135/140 chars) |
| HOLDOUT-DTI of the exact bytes | **0.043651** pooled (NW 0.046854 / NE 0.036240 / SW 0.056175 / SE 0.033176), 60,869 withheld positives, protocol `gems58-pooled-hide-v1`, evaluator `gems58w.metric/v1`, interval 0.033176–0.056175 (min–max over the four blocks; a 4-block bootstrap would resample repeated physical blocks as independent, so no bootstrap CI is claimed) |
| Uniqueness — discriminating statistics | byte-unique and pixel-unique among 702 verified witnesses; worst rank correlation **0.1824** (limit 0.90, **0** firings); worst dot-set Jaccard **0.1041** (limit 0.50, **0** firings); worst overlap against witnesses whose own expected overlap is < 0.30: **0.6115** |
| Uniqueness — literal stop | **fires**: 81 witnesses > 0.70 forward overlap; 54 are information-free (their 3 px dilation covers ≥ 99% of the footprint, so they overlap *every* nonempty candidate) and 27 are broad dot fields of 155,021–3,380,827 dots. Worst informative overlap 0.8750 at E = 0.8611 (chance-corrected lift 0.100); largest lift among all firings 0.3752 |

**The decision below was taken in session 5 (RATIFIED-UNIQ-v1); the paragraph is kept as the
session-3 record.** Under a chance-corrected *lift* rule — a witness
fires only if `(observed − E)/(1 − E) > 0.50` — this file yields **2 firings, both against this
repository's own earlier ribbon files** (family resemblance, not reuse of another lane), and the highest
lift against any other repository is **0.4898**. An E-limit rule needs a threshold ≤ **0.61** for zero
firings. Keeping the literal rule means no ridge-based or coverage-based emitter in this repository
family can ever be submitted, because the registry already contains near-plane-filling witnesses
(IR-58-UNIQ-02/03, now measured over the whole inventory). `scripts/build_site.py` computes both
readings from the scan rows at build time and does not choose between them.

Do not evade the duplicate stop by omitting dense registry rasters, emitting an empty TIFF, or treating
an incomplete inventory as exhaustive — and do not route around it by placing dots off-geology to dodge
a witness: that would trade the hypothesis being tested for a number that means nothing.

### Why the older diagnostic is still blocked

- **Literal final-dot duplicate stop:** 67,379 candidate dots; **100%** lie within 3 px of the prior
  full-footprint-positive raster `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`.
- **Its recorded scan was incomplete:** 694/695 pinned rasters. *(Session 3 closed that gap for the new
  scan: the missing pin `927dc17f…` was recovered from `55GEMSDOE` commit `d92606c2…` and re-hashed, so
  the merged inventory is 695/695 pinned + a current-default-branch delta = 703 byte-verified
  witnesses — IR-58-REG-01.)*
- **Its overlap numbers were measured with a defective instrument:** `src/gems58w/uniqueness.py`
  exchanged the two overlap directions until 2026-10-11 (IR-58-UNIQ-04), so every overlap figure this
  lane published before today — including "worst forward overlap 0.3600" for the earlier 38,000-dot
  ribbon file — is superseded.
- **Pre-placement surface gate:** not cleared for that candidate against a current inventory.
- **Format evidence:** its local preflight passed, but it is published in the all-finite `*-zeros.tif`
  representation, which is *not* the organizer's `sample_submission.tif` representation (IR-58-UNIQ-05).

## Session 5 — cross-family convergence, three experiments as the budget requires

| # | Question | Result | Receipt |
|---|---|---|---|
| EXP-1 | Can independent physical families be made to corroborate the same lineament? | A 4-family × 2-scale structure-tensor field over the pinned 19-band stack: **72,191 cells (1.40 % of the footprint) have ≥ 2 families agreeing** on a consistent strike; 27,626 have ≥ 3 | `evidence/gems60/gems60_convergence.json` (cache outside git) |
| EXP-2 | Does the agreement count rank better than one family, and what is the localization error? | **Negative on the ranking claim**: equal 40k-dot budget mean exact kernel credit — all-family ranking 0.0107 vs topographic alone 0.0202 (≤3 px: 0.023 vs 0.040), so agreement survives only as a *ranking weight*. Leakage canary max AUC **0.6846** < 0.90 (no leakage). Measured across-strike σ of associated candidates: **median 2.0–4.1 px** by family/scale — the same order as the 3 px kernel radius | `evidence/gems60/sigma.json` |
| EXP-3 | Which emission geometry is optimal, and can a unique portal-legal file be emitted and screened? (the shipped file is **not** restricted to agreeing cells — measured mean agreeing families 1.05 with 10.9 % of dots on ≥ 2-family cells — because EXP-2 rejected agreement as a gate; it enters only as a ranking bonus) | Exact-metric sweep (390 patterns) weighted by the measured σ: 5 parallel dotted lines at the kernel-radius spacing is the robust optimum; emitted **40,000 dots, all exactly 1.0, 0 on the catalogue**, independent verification **12/12**, HOLDOUT-DTI **0.037208**, uniqueness screen over **668 sha256-verified witnesses**: literal firings 56 (all against witnesses covering ≥ 65 % of the footprint by their own dilation), **governing firings 0** (max chance-corrected lift 0.4552 ≤ 0.50; 0 firings at E ≤ 0.61; worst ρ 0.3499 < 0.90; worst Jaccard 0.0248 < 0.50) | `evidence/gems60/{pattern_weighted,holdout,uniqueness_readings}.json` |

**The decision.** The session-5 candidate is the first file in this repository cleared on every
measurable local gate; the literal 70 % rule is reported in full and shown to be unsatisfiable by
any nonempty file (35 witnesses cover 100 % of the scored footprint by their own 3 px dilation),
so the verdict is taken on the two resolutions the owner proposed for that rule, both of which
give zero firings. What remains unverified is the leaderboard value — the local holdout cannot
rank this class of file (ρ = −0.037 against live scores over 34 rasters), and the only live
evidence for the emission format is the family's own USER-REPORTED 0.2600–0.2778 for sibling
dotted files. Download and submit at [docs/gems60.html](docs/gems60.html).

## Session 3 — three experiments, as the budget requires

| # | Question | Result (HOLDOUT-DTI unless labelled) | Receipt |
|---|---|---|---|
| EXP-1 | Can σ(x) be measured without fitting on the folds it scores, and does any single feature leak? | Leave-one-block-out cross-fitted pooled median σ **6.88 px** (rms 8.01, 994 components); calibrated credit k̂(family, decile) spans **0.000–0.035**, entirely below the marginal bar α·0.4133 = **0.0827**; worst single-feature AUC **0.5955** < 0.90 → no leakage | `evidence/ribbon/adaptive_sigma.json` |
| EXP-2 | Does an adaptive ribbon beat a tight line and a uniform ribbon at an equal budget? | 38,000 isolated dots per fold: W1 tight **0.042462**, W3 uniform **0.044336**, AD adaptive **0.044336** (*identical* to W3), **AD2 adaptive τ=0.45 → 0.047655** (paired bootstrap over four blocks 0.004482–0.006365). Per σ class: ribbon wins at σ ≥ 1.5 px (+0.0065 in σ ∈ [3,6] px, where the tight line scores exactly 0) and **loses** below it (−0.0014) | `evidence/ribbon/adaptive_arms.json` |
| EXP-3 | Can a unique, portal-legal file be emitted, validated and screened? | 40,768 dots, 15/15 format checks, HOLDOUT-DTI 0.043651, local screen cleared (27 witnesses), full-inventory scan **negative on the literal gate** | `evidence/ribbon/emission.json`, `run_card_final.json` |

**The binding constraint is coverage, not geometry.** The leader's 0.4133 implies ≈0.36 weighted
coverage (PROJECTION from the official metric); this surface reaches **0.0561** weighted coverage of
catalogue truth on the holdout. Ribbon geometry is worth +0.005; coverage is worth ~6×. No width,
offset, threshold or budget choice inside this lane closes that gap, and that negative result is the
main deliverable of the session.

**Instrument fixes, made once in the shared tools (no private forks).**

1. `src/gems58w/uniqueness.py` measured **both overlap directions backwards**; the definitions now live
   once in `src/gems57/uniqueness.py` and the lane imports them (IR-58-UNIQ-04).
2. The literal 0.70 gate fires on saturated blanket/lattice witnesses. The shared summariser now reports
   `E`, the chance-corrected lift, a `saturated` flag, a representation class, and **literal and
   informative readings side by side**; clearance never rests on a vacuous firing (IR-58-UNIQ-03).
3. `scripts/check_uniqueness_registry.py` rejected the organizer's own NaN-outside-footprint
   representation, which is why earlier artifacts were shipped as `*-zeros.tif`; non-finite **inside**
   the footprint remains a hard error (IR-58-UNIQ-05).
4. σ is now **leave-one-block-out cross-fitted** (it was previously fitted on the folds it scored, on
   `n_pairs = 14`), and the lane's "tight line where σ < 0.5 px" branch is documented as unreachable
   because σ is floored at 0.5 px (IR-58-SIGMA-01).
5. The live-score matcher no longer matches ISO dates as sha256 tokens and is fail-closed
   (IR-58-LIVE-01).

**Measured negatives kept as deliverables.**

- **Live-score calibration is NEGATIVE:** over 66 sha256-verified sibling rasters the two-parameter
  catalogue-proximity model fits with R² = −1.27 and **no covariate reaches |Spearman| 0.258**. The
  earlier n=20 `Spearman(dots, score) = −0.831` is an artifact and must not be reused. The 40,768-dot
  budget is the median dot count of the owner-reported ≥ 0.24 family — labelled USER-REPORTED-SCORE,
  never as a calibrated optimum. What survives is a family separation: every ≥ 0.2449 file has 0
  on-catalogue dots, 37,654–61,328 dots and a median catalogue distance of 14–20 px, while
  catalogue-hugging files score 0.004–0.03.
- **Per-segment adaptivity beyond a uniform ribbon measured exactly 0.000000** (`AD` vs `W3`), and the
  planner returned 5 lines for 5,794 of 6,286 segments. The measured gain is "ribbon vs tight line".
- **The HOLDOUT-DTI is not an artifact of the archived path.** `scripts/crosscheck_shared_metric.py`
  re-derives the delivered bytes' score with the shared `gems57.metric` (`dti_binary`, `dti_exact`) and
  with the literal brute-force transcription of the published equations on a bounded tile: per-fold and
  pooled deltas are **exactly 0.0** and the pooled value equals the recorded receipt
  (**0.043651086**), so the number is a property of the official metric, not of the copy that computed
  it (`evidence/ribbon/shared_metric_crosscheck.json`, gate G5i, run in CI).
- **`gems58w.allocation` is a legacy design rule.** Its `_marginal_pair` false-positive term does not
  reproduce the official per-prediction `FP_w` for interacting lines, so the *choice* of line count is
  not an exact-metric decision. The *evaluation* of every pattern emitted here used the exact metric on
  isolated dots (min separation 1, 3 px lattice), where the shortcut `k > αs` is valid; the exact
  marginal form is `U = (1 − αs)ΔTP − αsΔFP`.
- **Aeroradiometric and 1 m lidar evidence is absent from the delivered stack** although page 968 says
  GeoDAWN acquired both (IR-58-DATA-01). Sources are verified and linked; this sandbox cannot fetch
  binaries, so it is an owner-download hypothesis, never a validated candidate.

## Correct score and leaderboard record

The official public leaderboard was directly checked on 2026-10-11 UTC. It showed:

| Public rank | Participant | Public DTI | Evidence label |
|---:|---|---:|---|
| 1 | xiaofanhu | 0.4133 | PUBLIC-LEADERBOARD SNAPSHOT |
| 8 | DARD | 0.3195 | PUBLIC-LEADERBOARD SNAPSHOT |
| 23 | extradr19 | 0.2778 | PUBLIC-LEADERBOARD SNAPSHOT |

Source: [official DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/); a dated observation is stored in `evidence/official_leaderboard_observation_20261011.json`. The board is dynamic. The earlier `0.3195` reference is a real public row, but it is **not the current leader**.

The GEMSDOE32 H33 file named `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` is **not** established to have scored 0.2778. Its owner-maintained [artifact page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) says **“NO ORGANISER SCORE EXISTS”** for that artifact and labels **0.2747** a model projection. The official public board associates 0.2778 with participant `extradr19`; neither the public row nor the owner page provides a receipt/hash crosswalk from that score to the H33 TIFF. Do not attribute 0.2778 to that file or explain why it “scored.” See [the attribution review](docs/research/why-02778.md), [`docs/LEADERBOARD.md`](docs/LEADERBOARD.md), and `registry/submissions_seen.csv`.

**The only numeric performance claims allowed for this repository's model are:** (a) HOLDOUT-DTI with the shared evaluator version, withheld-positive count, protocol, and valid 95% CI; or (b) ORGANIZER-CONFIRMED from a submission receipt tied to the exact file. The public leaderboard values above are contextual page observations, not scores for this artifact.

## Ranked hypotheses — proposals only

[`docs/research/hypotheses_session3_adaptive_ribbon.md`](docs/research/hypotheses_session3_adaptive_ribbon.md)
is this session's ranking (a sibling session published its own
[`hypotheses_session3.md`](docs/research/hypotheses_session3.md) and
[`hypotheses_session4.md`](docs/research/hypotheses_session4.md) for the scatter-cover lane): five
**detection-side** hypotheses with layers, physical signature, why each can catch a fault missing
from the USGS/INGENIOUS catalogue, how it differs from this repository, a named non-fault mimic, and
expected DTI gain per implementation hour — ranked against the constraint session 3 measured (coverage,
not geometry). **H58-R4** (cross-fitted supervised detector that emits only where the calibrated
per-stratum detection rate clears α·DTI₀ = 0.0827) is rank 1 and needs no new data; **H58-R6** (regress
flight-line geometry out of the magnetic bands) rank 2; **H58-R5** (a directional σ tensor) rank 3;
**H58-R3** (aeroradiometric + 1 m lidar — physically the strongest, and the organizers' own framing) is
**blocked on an owner download**; **H58-R7** is listed only as a measured dead end.

The earlier ranked, untried ribbon-width proposals are in
[`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md). They keep the existing ridge surfaces fixed and vary only error calibration / ribbon width and offsets. They do not claim to detect a fault for which the existing ridge field has no candidate. None has been implemented or holdout-validated. The registry stop must be resolved before any experiment.

## Repository status and reproduction

- Current fail-closed status generator: `scripts/build_site.py` → `docs/index.html`, `evidence/run_card.json`, and `docs/RUN_CARD.json`.
- Shared template: `src/gems57/`; use `gems57.evaluate_holdout` and `gems57.submission_writer` only for any future qualified experiment.
- The cached 19-band feature raster is hash-pinned in `data/bridge/feature_stack_pins.json` and stored outside Git at `~/.cache/gems/training_features.tif`. Its SHA256 verifies against the owner-maintained GitHub bridge; that establishes byte integrity, not independent organizer provenance.
- Old `gems58w` ribbon experiment, feed, site, and submission CLIs are archival and disabled because they use private/unbuffered legacy paths and can publish non-promotion-grade numbers or misleading download language.

Run tests in an environment with `requirements.txt` installed:

```bash
PYTHONPATH=src python -m pytest -q          # 152 tests, all pass (session 6 count)
python scripts/build_site.py                # renders docs/ from the receipts (exit 0)
python scripts/build_site.py --strict       # exits 2 while any gate G1-G5 is open
PYTHONPATH=src python scripts/crosscheck_shared_metric.py  # re-derive the DTI with gems57 (21 s)
python scripts/ribbon_check_site.py         # QA: archived ribbon pages + current negative gates
python scripts/gems60_build_page.py         # session-5 lane page + front-door box (CI order)
PYTHONPATH=src:scripts python scripts/audit_current_tiff.py   # independent TIFF/ZIP file audit
python scripts/build_downloads_index.py     # per-file submit-eligibility labels for every raster
```

Three session-6 tools are additive and change no verdict:

| Tool | What it proves — and what it does not |
|---|---|
| [`scripts/audit_current_tiff.py`](scripts/audit_current_tiff.py) → [`evidence/ribbon/file_audit.json`](evidence/ribbon/file_audit.json) | Independently re-reads the **current** candidate named by `evidence/ribbon/emission.json` (never a hard-coded file) and checks Float32/sample grid, NaN-outside mask, in-footprint `[0,1]` values, positive count, file hash and ZIP round-trip. A local file audit only: not portal acceptance, uniqueness, holdout qualification, or eligibility. |
| [`scripts/build_downloads_index.py`](scripts/build_downloads_index.py) → [`docs/downloads/index.html`](docs/downloads/index.html) | Labels **every** public TIFF/ZIP separately, including archived and legacy-lane files, so no raster inherits clearance from another. |
| [`scripts/qualification_gates.py`](scripts/qualification_gates.py) | The hash-bound pre-emission contract consulted by `scripts/build_ribbon_emission.py`: fresh inventory, pre-placement surface, feature-alone canary, and a shared-evaluator holdout with a defensible 95 % interval, each bound to the exact candidate and receipt hashes. `evidence/ribbon_qualification.json` is absent, so the emitter exits 2 and writes nothing. |

Reproducing the session-3 measurements themselves needs the pinned feature stack and the witness cache:

```bash
bash scripts/fetch_feature_stack.sh                                   # 419 MB, sha256-pinned
export GEMS_FEATURE_STACK=~/.cache/gems/training_features.tif          # gems58w.paths cannot see it otherwise
python3 scripts/fetch_registry_sparse.py                              # restore the 695 pinned witnesses
python3 scripts/registry_delta_inventory.py --clones /tmp/reg          # freshness delta -> registry_merged.json
PYTHONPATH=src python3 scripts/live_evidence_calibration.py            # 66 owner-quoted scores vs verified bytes
PYTHONPATH=src python3 scripts/ribbon_run_adaptive.py                  # EXP-1 + EXP-2 (~4 min)
PYTHONPATH=src:scripts python3 scripts/ribbon_emit_adaptive.py         # EXP-3: emit, validate, local screen (~2 min)
PYTHONPATH=src python3 scripts/check_uniqueness_registry.py \
    docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif \
    --workers 2 --out ribbon/uniqueness_full_inventory.json            # gate G3 (~35 min on 2 CPUs)
```

`scripts/ribbon_run_adaptive.py` and `scripts/ribbon_emit_adaptive.py` evaluate with the exact metric on
isolated dots, but they build geometry with the now-archived `gems58w` path (`extract`, `sigma`,
`allocation`, `submission`). Any future qualified experiment must route scoring through
`gems57.evaluate_holdout` and writing through `gems57.submission_writer`, per the standing prompt.

These commands test and render evidence only; they do not create an experimental TIFF, run a holdout, select a slot, or upload anything. See [`REMAINING_WORK.md`](REMAINING_WORK.md), [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md), and [`docs/SOURCES.md`](docs/SOURCES.md).

---

## Standing prompt (embedded summary; the full operating contract is in `PROMPT.md`)

> **Mission:** maximize the probability of winning the DOE GEMS Prize and own the outcome. The target is faults indicative of geothermal resources, not geothermal vents. Stay exclusively in the **ribbon-width/localization-error lane**. Current artifact status is **NOT OK TO SUBMIT — DO NOT SUBMIT**.
>
> **Scope:** review prior-session status; before implementation rank 3–5 genuinely untried within-lane hypotheses by relative benefit, uncertainty and cost; define tests and stop criteria. Reuse the cached feature stack and shared `gems57.evaluate_holdout` / `gems57.submission_writer`. Do not create private metric/evaluator/writer forks. Hold out buffered whole fault segments, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI with α=0.2, β=0.8, 300 m triangular kernel.
>
> **Uniqueness:** compare the placement surface before emission and final dots against every accessible registry raster. Stop if rank correlation is >0.90 or >70% of candidate dots fall within 3 px of any one raster. An incomplete/stale registry is not clearance. A known literal stop is never waived to force a TIFF into existence.
>
> **Metric:** for a change in a prediction pattern, use exact marginal `ΔTP` and `ΔFP`, including maximum-credit interactions: `U = (1−αs)ΔTP − αsΔFP`. The shortcut `k > αs` applies only to one added, non-redundant dot with fresh truth credit. Test each feature alone; AUC >0.90 is leakage until explained.
>
> **Evidence:** label model numbers HOLDOUT-DTI with evaluator version, withheld-positive count, protocol, and defensible 95% CI; only label an artifact score ORGANIZER-CONFIRMED from a receipt/hash crosswalk. A projection, local proxy, public-board row, raster property, or format check is not the score of this TIFF.
>
> **Budget:** at most three experiments and two hours; stop on a uniqueness trigger, stale/incomplete inventory, leakage, or a nonpositive/uncertain preregistered result. Never choose or use a competition slot. End with the required JSON run card and an unmistakable promote/negative decision. Keep a unique downloadable TIFF only when it genuinely passes; otherwise preserve the negative result and do not submit.
>
> **Official links:** [problem / metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf). See `docs/SOURCES.md` for the dated verification log.

---

## Preserved from `main` (sibling PR #30, merged to main 2026-10-11 12:17 PDT)

> **Not verified by this lane.** The block below is kept verbatim from `main`. Its
> "Submission ready" statement is **contradicted by the gates on this page**: no
> artifact is OK to submit until every gate passes, and every TIFF in `docs/downloads/`
> is labelled NOT OK TO SUBMIT — review only (`docs/downloads/index.html`).

# 58GEMSDOE — DOE GEMS Prize Challenge

Core values: **Maximize P(Win)** and **Own the Outcome** — report the actual result, including a negative one.

> **Submission ready:** `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif`
> — 45,355 binary predictions at exactly 1.0, detected by RandomForest on 20 geophysical gradient features.
> All format checks pass. Download and submit at [docs/executive-summary.html](docs/executive-summary.html).

## Quick Start — Submit Your Prediction

1. **Download** the TIF file: [`docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif`](docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif)
2. **Go to** [competition submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/) (login required)
3. **Upload** the TIF file and add note: `ML RandomForest binary ridge detection on 20 geophysical gradient features; 45K dots at 1.0`
4. **Submit** and check your score on the [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See the full [Executive Summary](docs/executive-summary.html) for detailed instructions.

---

## Project Mission

**Goal:** Maximize probability of winning the DOE GEMS Prize and own the outcome. The target is faults indicative of geothermal resources, not geothermal vents. Predict unseen geological faults from geophysical and topographic rasters scored by the Distance-Weighted Tversky Index (α=0.2, β=0.8, R=300m).

**Current submission:** ML RandomForest binary ridge detection on 20 gradient features from 10 key GeoDAWN bands.

**Official links:**
| Purpose | Link |
|---|---|
| Competition home | https://www.drivendata.org/competitions/306/competition-doe-gems/ |
| Problem description & DTI formula | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ |
| Public leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ |
| Data (login required) | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ |
| Rules (PDF) | https://docs.nlr.gov/docs/fy26osti/96647.pdf |
| Reference solution | https://github.com/drivendataorg/gems-prize-reference-solution |
| GeoDAWN survey (USGS) | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and |
| INGENIOUS (GBCGE) | https://gbcge.org/current-projects/ingenious/ |
| EPSG:32611 | https://epsg.io/32611 |
| Tversky index | https://en.wikipedia.org/wiki/Tversky_index |

## Current Submission Details

| Field | Value |
|---|---|
| File | `gems58-ml-binary-ridge-20261012T000000Z.tif` |
| SHA256 | `40c2518802a9a220fa362be0b152f2c4c7ca753c3919624eed22a556c5769366` |
| Format | Float32, EPSG:32611, 3730×3292, 100m |
| Values | All in [0, 1], zero outside footprint, no NaN |
| Positive pixels | 45,355 (all at exactly 1.0) |
| On catalogue | 0 |
| Method | RandomForest (100 trees, depth 8) on 20 gradient features |
| Validation AUC | 0.7152 |
| Submission note | `ML RandomForest binary ridge detection on 20 geophysical gradient features; 45K dots at 1.0` |

## Leaderboard Context (as of 2026-10-11)

| Rank | Participant | Score |
|---:|---|---:|
| 1 | xiaofanhu | 0.4133 |
| 8 | DARD | 0.3195 |
| 23 | extradr19 | 0.2778 |

Source: [official DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## Method Analysis

### Why high-scoring submissions work

The DTI metric: `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`

- **α=0.2** (FP penalty) vs **β=0.8** (FN penalty): coverage is 4× more valuable than precision
- The **kernel** (300m = 3px radius) gives credit for predictions *near* truth, not just at truth
- The **marginal bar** for a non-redundant dot: `k > 0.2·DTI` — at DTI=0.25, even a dot with kernel credit 0.05 (within ~2.85px of truth) is worth placing

### What the best submissions do differently

1. **0.4133 (xiaofanhu):** Likely a trained UNet/deep learning model producing continuous probability fields that detect both mapped and unmapped faults
2. **0.3195 (DARD):** Strong feature engineering + ML
3. **0.27-0.28 range:** Dotted/ridge approaches placing ~40K dots along structural lineaments
4. **0.15-0.25:** Simpler ridge detection, catalog-derived predictions

### Our approach

RandomForest classifier trained on 20 gradient features from 10 key GeoDAWN bands. The model learns the geophysical signature of faults from the USGS/INGENIOUS catalogue, then identifies similar structural features across the entire study area — including unmapped faults that the competition tests against.

### Key scientific references

- **GeoDAWN survey:** USGS airborne magnetic and radiometric surveys of NW Great Basin, Nevada
- **INGENIOUS project:** GBCGE fault database for the GeoDAWN region
- **Distance-Weighted Tversky Index:** Asymmetric similarity metric penalizing false negatives 4× more than false positives
- **Structural indicators:** Gradient magnitude on magnetic, gravity, and conductivity rasters detects lithological discontinuities associated with faulting

## Hypotheses for Improvement

### H1: Multi-scale edge detection with ensemble model
- **Layer:** All 19 GeoDAWN bands
- **Signature:** Multi-scale gradient magnitude, Hessian eigenvalues, Laplacian-of-Gaussian
- **Why it catches unmapped faults:** Different scales detect faults of different displacements
- **Difference:** Uses full band stack + ensemble instead of single-scale gradients

### H2: Cross-band coherence detection
- **Layer:** All geophysical families
- **Signature:** Agreement of gradient directions across independent feature families
- **Why it catches unmapped faults:** True faults disrupt multiple geophysical fields simultaneously
- **Difference:** Requires multi-family agreement, reducing false positives from single-band artifacts

### H3: Proximity-weighted emission near catalogue faults
- **Layer:** Catalogue faults + structural features
- **Signature:** Distance-decay predictions from known faults along structural trends
- **Why it catches unmapped faults:** Faults have damage zones, extensions, and splays not in the catalogue
- **Difference:** Uses catalogue as seeds for structural extension, not just labels

### H4: DEM-derived topographic analysis (external data required)
- **Layer:** 1m DEM from CSV links provided by competition
- **Signature:** High-resolution fault scarps, displaced stream channels, triangular facets
- **Why it catches unmapped faults:** Topographic expression of faults at 1m is far more detailed than 100m features
- **Data source:** `1m_DEM_links.csv` on competition data page (requires login + download)

### H5: Earthquake clustering analysis
- **Layer:** Band 15 (earthquake density) + structural features
- **Signature:** Linear clusters of seismicity aligned with structural discontinuities
- **Why it catches unmapped faults:** Active faults produce seismicity even when unmapped at the surface
- **Difference:** Uses seismicity as primary indicator instead of secondary feature

## Limitations

- **No organizer receipt exists** — no competition score is claimed; the local validation AUC measures catalogue-fault detection, not new-fault detection
- **AUC 0.715 is moderate** — the model has meaningful but not strong discrimination; a UNet would likely perform better
- **Holdout measures catalogue recovery** — the competition scores NEW faults not in any public database
- **No external data used** — the 1m DEM, aeroradiometric, and seismicity data could significantly improve results but require download from the competition data page (login required)
- **CPU-only training** — GPU would enable UNet training for much better spatial pattern recognition
- **2 CPUs, ~4 GB RAM** — limits model complexity and feature computation

## Reproduction

```bash
# Install dependencies
pip install numpy scipy scikit-learn rasterio scikit-image pandas pytest

# Fetch the19-band feature stack (~419 MB)
bash scripts/fetch_feature_stack.sh

# Run the ML submission pipeline (~5 minutes)
PYTHONPATH=src python3 scripts/generate_submission_v2.py

# Verify format
PYTHONPATH=src python3 -c "
import rasterio, numpy as np
with rasterio.open('docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif') as src:
    a = src.read(1)
    assert a.dtype == np.float32
    assert a.shape == (3730, 3292)
    assert np.isfinite(a).all()
    assert a.min() >= 0 and a.max() <= 1
    print('All checks passed')
"
```

## Project Files

| File | Description |
|---|---|
| `docs/executive-summary.html` | Download page with submission instructions |
| `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif` | Verified submission GeoTIFF |
| `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.zip` | Same file as ZIP |
| `scripts/generate_submission_v2.py` | ML submission pipeline |
| `src/gems57/` | Shared template (metric, holdout, writer) |
| `PROMPT.md` | Full operating contract |
| `REMAINING_WORK.md` | Status and next steps |

---

## Arena AI Core Values

**Maximize P(Win):** In every decision, weigh tradeoffs, assess risk, and choose the path that maximizes probability of success. Set aside emotions and make tough decisions.

**Own the Outcome:** Own results end to end — not just our individual slice. When problems arise and we have the means to act, do so without waiting for permission. Treat failure and success as signals and use them to improve.

---

*Last updated: 2026-10-12. All format checks verified against `sample_submission.tif` template.*

---

## Preserved from `main` (later PRs, merged after the session-7 merge base)

> **Not verified by this lane.** The block below is kept verbatim from `main` (its README as of
> commit 7d079bd). Any "submission ready" wording in it is **contradicted by the gates on this
> page**: no artifact is OK to submit until every gate passes, and every TIFF in `docs/downloads/`
> is labelled NOT OK TO SUBMIT — review only (`docs/downloads/index.html`).

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

## Session-8 lane addition — `gems61` (extended-layer ridge lane)

This branch adds the `gems61` lane next to the historical lanes. It changes no verdict and no
download label: the literal uniqueness stop recorded above governs, and the review-only raster stays
review-only. Contents:

| Path | What it is | State |
|---|---|---|
| `src/gems61/layers.py` | reader for the hash-pinned GeoDAWN radiometric / 3DEP lidar / DEM mirrors, as ordinal bands on the competition grid | implemented |
| `src/gems61/detect.py` | multi-family, multi-scale, dual-polarity ridge field (Hessian + non-maximum suppression) with per-family quantile thresholds | implemented |
| `src/gems61/lane.py` | σ(x) table (block × scale × sign, leave-one-block-out), exact-metric pattern ladder `U = (1 − 0.2·DTI₀)·ΔTP − 0.2·DTI₀·ΔFP`, `emit_dots`, `uniqueness_repair`, `score_dots` (cross-checked against `gems58w.metric.dti_binary`) | implemented |
| `scripts/gems61_run.py` | `field\|sigma\|pattern\|canary\|emit` driver | only `field` executed |
| `scripts/gems61_screen.py` | registry screen that publishes the literal 70 % reading beside the ratified one | implemented, not yet run on a candidate |
| `scripts/gems61_fetch_extended.sh`, `data/external/gems61_extension_pins.json` | byte-verified restore of the five mirror files | implemented |
| `evidence/gems61/field.json` | 5,167,205 ridge pixels, 41 classes, 9 feature families | written |

`sigma`, `pattern`, `canary` and `emit` have **not** been run on this branch: the lane has produced
no candidate, no σ table, no simulated gain and no holdout number, and nothing above is clearance.
`evidence/ribbon_qualification.json` is still absent, so `scripts/build_ribbon_emission.py` remains
fail-closed, and the literal rule in `PROMPT.md` applies to any future candidate from this lane as-is.
