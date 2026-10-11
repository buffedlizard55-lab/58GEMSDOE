# 58GEMSDOE — DOE GEMS Prize Challenge

Core values: **Maximize P(Win)** and **Own the Outcome** — report the actual result, including a negative one.

> **Session 4 (2026-10-11):** verification only, no new TIFF, no experiment, no slot. The registered
> candidate passes the format check (float32, EPSG:32611, footprint NaN identical to the organizer sample,
> all values in [0,1]) but **fails the uniqueness gate G3**, so it stays NOT OK TO SUBMIT. The 0.2778 figure
> belongs to `extradr19` on the official board, not to the GEMSDOE32 H33 file. See
> [`docs/research/session4_verification_20261011.md`](docs/research/session4_verification_20261011.md) and
> [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md) (IR-58-S4-01 to 04).

## Submission decision — session 5

**Current candidate: `docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.tif`** —
[CLEARED ON EVERY MEASURABLE LOCAL GATE (download & submit)](docs/gems60.html). It is a new,
unique raster: lineaments from a four-family (magnetic, gravity, topographic, subsurface)
structural field, ranked with a cross-family agreement bonus and emitted as dotted multi-line
ribbons at the measured localization error, **0 dots on the mapped catalogue**, every value
exactly `1.0`, independent format verification 12/12, and **0 discriminating uniqueness
firings** over the byte-verifiable registry inventory. What is *not* verified is its
leaderboard value: no organizer receipt exists and the local holdout is structurally blind to
off-catalogue files (measured Spearman −0.037 against live scores over 34 rasters). The
authoritative, evidence-generated banner for the *previous* lane's artifacts is rendered by
`scripts/build_site.py` on the
[public site](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html); the session-5
deliverable has its own receipt-driven page, [docs/gems60.html](docs/gems60.html).

Session-5 facts, one line each: hypothesis → [`evidence/gems60/run_card.json`](evidence/gems60/run_card.json);
σ table → [`evidence/gems60/sigma.json`](evidence/gems60/sigma.json); exact-metric pattern
selection → [`evidence/gems60/pattern_weighted.json`](evidence/gems60/pattern_weighted.json);
holdout number (labelled, with its limits) → [`evidence/gems60/holdout.json`](evidence/gems60/holdout.json);
uniqueness screen → [`evidence/gems60/uniqueness_full.json`](evidence/gems60/uniqueness_full.json);
independent verification → [`docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.checks.json`](docs/downloads/gems60-convergence-ribbon6-20261011T155420Z.checks.json).

### Earlier artifacts — still NOT CLEARED

Two artifacts remain downloadable and **neither is cleared**.

| Artifact | Status | Decision basis |
|---|---|---|
| **`gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`** (session 3, current candidate) — [TIF](docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif) · [ZIP](docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.zip) | **NOT CLEARED — download for review only** | Format gate 15/15 and holdout measured, but the **literal** 3 px forward-overlap stop fires against 81 of 702 inventory witnesses. Logged as a duplicate and stopped, as the standing prompt requires. [`evidence/ribbon/uniqueness_full_inventory.json`](evidence/ribbon/uniqueness_full_inventory.json), [`evidence/ribbon/run_card_final.json`](evidence/ribbon/run_card_final.json) |
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

### Session-3 candidate — the facts

| | |
|---|---|
| sha256 | `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd` (433,419 B) |
| Contents | 40,768 isolated dots, every emitted value **exactly 1.0**; EPSG:32611, 3730×3292, 100 m; **NaN outside the study footprint exactly as in the organizer's `sample_submission.tif`** (7,111,787 NaN, `nodata=nan`) and finite everywhere inside it — which is what makes the portal rejection `Predicted values must be in range [0, 1]` impossible for this file; **0 dots on the mapped catalogue** |
| Submission name / note | `gems58-ribbon-sigma-adaptive-40768-20261011T052942Z` / `Ribbon lane: adaptive dotted ribbons 0/+-300/+-600 m on catalogue-free Hessian ridges (sigma cross-fitted); 40768 isolated dots at 1.0.` (135/140 chars) |
| HOLDOUT-DTI of the exact bytes | **0.043651** pooled (NW 0.046854 / NE 0.036240 / SW 0.056175 / SE 0.033176), 60,869 withheld positives, protocol `gems58-pooled-hide-v1`, evaluator `gems58w.metric/v1`, interval 0.033176–0.056175 (min–max over the four blocks; a 4-block bootstrap would resample repeated physical blocks as independent, so no bootstrap CI is claimed) |
| Uniqueness — discriminating statistics | byte-unique and pixel-unique among 702 verified witnesses; worst rank correlation **0.1824** (limit 0.90, **0** firings); worst dot-set Jaccard **0.1041** (limit 0.50, **0** firings); worst overlap against witnesses whose own expected overlap is < 0.30: **0.6115** |
| Uniqueness — literal stop | **fires**: 81 witnesses > 0.70 forward overlap; 54 are information-free (their 3 px dilation covers ≥ 99% of the footprint, so they overlap *every* nonempty candidate) and 27 are broad dot fields of 155,021–3,380,827 dots. Worst informative overlap 0.8750 at E = 0.8611 (chance-corrected lift 0.100); largest lift among all firings 0.3752 |

**The one decision that would change it (owner only).** Under a chance-corrected *lift* rule — a witness
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
PYTHONPATH=src python -m pytest -q          # 123 tests, all pass (session 4 count)
python scripts/build_site.py                # renders docs/ from the receipts (exit 0)
python scripts/build_site.py --strict       # exits 2 while any gate G1-G5 is open
PYTHONPATH=src python scripts/crosscheck_shared_metric.py  # re-derive the DTI with gems57 (21 s)
python scripts/ribbon_check_site.py         # QA: archived ribbon pages + current negative gates
```

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
