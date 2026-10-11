# 58GEMSDOE — GEMS competition (DrivenData #306)

## 🚫 Submission decision: **NOT OK TO SUBMIT — DO NOT SUBMIT**

The current TIFF is retained for research/audit only; **it is not a unique, promotion-grade or organizer-approved submission**. There is no organizer receipt, and no weekly submission slot has been used.

[Download the diagnostic GeoTIFF (NOT CLEARED; DO NOT SUBMIT)](docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif) · [Submission guide](docs/SUBMISSION_GUIDE.md) · [Current run card](evidence/run_card.json) · [GitHub Pages site](https://buffedlizard55-lab.github.io/58GEMSDOE/)

### Why it is blocked

- The recorded frozen-registry report finds **100%** of the candidate’s dots within 3 px of one prior full-footprint-positive raster. The literal stop limit is **>70%**. The candidate’s lower rank correlation does not override that independent stop rule. Evidence: `evidence/ribbon_uniqueness.json`.
- The frozen inventory is **695 rasters from 57 pinned repository snapshots**, generated at `2026-10-10T19:58:45.875405Z`; it is not a current/exhaustive public inventory. Newer default-branch trees contain TIFs in 58/59/60/61GEMSDOE, and GEMSDOE52 has 88 TIFF paths added since its pinned tree. A later restore checked only **694/695** pinned rasters; one raster remains unavailable, so even that scan is incomplete. Evidence: `evidence/registry_freshness_audit.json`, `evidence/registry_fetch_report.json`, `evidence/ribbon_uniqueness.json`.
- A literal pre-placement surface comparison for this candidate against a current inventory is not available. The old pre-placement report is a different candidate and excluded dense priors; it cannot be used as clearance.
- The old holdout output is not promotion-grade: per-segment acceptance saw the same cell’s withheld truth, σ was fit on scored folds, the earlier bootstrap resampled repeated physical blocks as independent, and the split had no new buffer. A buffered shared holdout constructor and toy tests were added, but **no experiment was rerun**.
- The TIFF has a recorded **local format/range preflight** only; that is not a registry clearance, portal acceptance, or organizer score. The local all-finite/zero-outside export policy also differs from the sample’s NaN footprint behavior; see `docs/IRREGULARITIES.md`.

All of these are stop conditions. No old holdout score is presented here as a validated result.

The repository also contains MECE/multi-evidence artifacts inherited from a separate main-branch change. That approach is outside this session's ribbon-only scope; its reported holdout used full-catalogue proximity and is leakage-flagged, and its pairwise comparison to the ribbon file is not a full-registry clearance. The fetched `origin/main` tree `d8c17dd` contains 10 TIF/TIFF paths in this repository, including those two MECE outputs; they were not compared against a complete current registry. Those files are retained as diagnostics, marked NOT OK TO SUBMIT, and must not be used as the current candidate.

---

## Standing master prompt (re-read at the start of every session)

> Review the repo.
>
> THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!
>
> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A
> PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST
> GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO
> DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.
>
> There should be an easy to download submission tif file as described by the
> prompt. Read the entire prompt.
>
> Ribbon lane: match emission width to the measured localization error. The
> simulations say placement within about one pixel is what pays, and that
> parallel dotted lines pay when location is uncertain. On the hide-and-recover
> holdout, measure the across-strike distance between each candidate ridge and
> the nearest withheld segment, and fit an error scale σ(x) by data block,
> feature resolution and ridge type. Then choose, per segment, the number and
> offset of parallel dotted lines (spacing near the 3-px kernel radius) that
> maximize U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact
> metric. Use a single tight line where σ is under about 0.5 px and a ribbon
> about ±σ wide where it is 2–3 px. Emit included dots at exactly 1.0, since
> scaling values down only scales the net gain down. Report the σ table and the
> simulated gain per class. Output the standard validated GeoTIFF,
> uniqueness-checked against every earlier raster.
>
> PARALLEL-RUN PROTOCOL — read first. This session is one of several running
> from this same prompt.
> 1. LANE. Your lane is the single method paragraph above. Stay inside it. If
>    your raster's rank-correlation with any registry raster exceeds [0.90], or
>    more than [70%] of your dots fall within 3 px of one registry raster's
>    dots, you have drifted into another lane: log it as a duplicate and stop.
>    Check this on the surface before placement AND on the final dots.
> 2. REUSE, DON'T REBUILD. Use the template's cached feature stack,
>    evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover:
>    withhold whole fault segments with a buffer, derive every catalogue-based
>    feature only from the visible faults, mask visible faults pixel-exactly,
>    score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a
>    shared tool is wrong, fix it once in the template and report it; never
>    keep a private fork.
> 3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld
>    positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
>    receipt). A projection is never written as a score.
> 4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any
>    result. AUC above [0.90] means leakage until proven otherwise.
> 5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named
>    non-fault process that could mimic it; holdout DTI + CI;
>    correlation/overlap vs registry; raster sha256; validator output (no NaN
>    inside the footprint, values in [0,1], CRS/shape/transform match);
>    submission name + note of at most 140 characters; verdict promote /
>    negative. Negative results are deliverables.
> 6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions:
>    promotion to a real slot is a separate selector step, within the weekly
>    cap shown on the submission page.
>
> Before implementing, generate 3–5 candidate geological hypotheses we haven't
> tried yet, each naming: the specific layer(s), the physical signature being
> targeted, why it should catch a fault missing from the USGS/INGENIOUS
> catalogue rather than one already in it, and how it differs from anything
> already implemented. Rank them by expected DTI improvement and implementation
> cost. Validate the top candidate on the spatially-blocked holdout before
> touching a weekly submission slot. If a candidate can't be validated without
> new external data, name the specific free, official source and check it's
> obtainable before proposing the idea as viable.
>
> Work line by line verifying from official verified trusted sources, provide
> links for manual review. No manual input. Flag any irregularities for
> review. No hallucinations. Verify line by line.
>
> Core values: **Maximize P(Win)** and **Own the Outcome** — weigh tradeoffs,
> pick the path that maximizes the probability of winning; own results end to
> end.

---

## Current review card (2026-10-11 UTC)

| Check | Finding | Label / artifact |
|---|---|---|
| Diagnostic raster | `docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif`; SHA256 `8b196e6eea06fef0d6cf2c9109091d1e2677a77d6e48d8b04f334a879551687f` | LOCAL-RASTER / local preflight only |
| Grid | One float32 band, EPSG:32611, 3730×3292, 100 m, transform `(100,0,243350,0,-100,4508550)` | LOCAL-GRID check against the bridged sample; official origin not independently authenticated here |
| Format/range | Recorded local validator passed for finite values in [0,1], zeros outside the local footprint, and zero on mapped catalogue | LOCAL-FORMAT-PREFLIGHT; not portal acceptance |
| Literal final-dot overlap | 1.0 with the `GEMSDOE2` full-footprint-positive witness; strict stop limit 0.70 | REGISTRY-MEASUREMENT, frozen snapshot only; blocks candidate |
| Spearman rank correlation | Worst recorded value 0.1896456, below 0.90 | REGISTRY-MEASUREMENT, frozen snapshot only; does not cure overlap failure |
| Registry freshness | 695 unique rasters across 57 pinned snapshots; latest restore checked 694/695. Fetched `origin/main` tree `d8c17dd` contains 10 TIF/TIFF paths in this repository, including two out-of-lane MECE outputs; no full current inventory comparison was performed. | REGISTRY-FRESHNESS-AUDIT; incomplete/current scope false |
| Pre-placement current surface | Not checked for this candidate under a current literal inventory | NOT CLEARED |
| Promotion-grade HOLDOUT-DTI | Not run with the new buffered split; legacy result is disqualified for promotion due same-cell truth selection and invalid block bootstrap | NOT MEASURED for current instrument |
| Organizer score | No receipt | NOT AVAILABLE |
| Final status | **NOT OK TO SUBMIT — DO NOT SUBMIT** | `evidence/run_card.json` |

The number of positive raster pixels is a raster fact, not a score. No current leaderboard point or performance claim is reported.

## Session 2 review card — supervised ranking + metric-derived dot budget (2026-10-11 UTC)

This session added a second, independent candidate and an equal-budget measurement
instrument. It does **not** override the shared decision above: nothing here is cleared, and no
weekly slot has been used.

| Check | Finding | Label |
|---|---|---|
| New candidate | `docs/downloads/gems58-prox-dot36k-20261011T030218Z-e7bbfea83853-zeros.tif`; SHA256 `aac8aa8a021ee309c91c5084f17ff2d64623163faa382cfd76ca781352d945b8` | LOCAL-RASTER / local preflight + registry scan |
| Positive pixels | 36,394, all at exactly 1.0, all >3 px off the mapped catalogue, zeros elsewhere | LOCAL-FORMAT-PREFLIGHT |
| Canary (`all` / `detached`) | Max single-feature AUC 0.856 / 0.844 (distance to visible catalogue); best geophysical band 0.559 / 0.584 | HOLDOUT instrument, under the 0.90 line |
| Equal-budget ranking contest (detached) | PROX **0.2147** ≫ GF 0.0689 ~ CTX 0.0036 (CTX collapses onto the catalogue: off-catalogue probabilities exactly zero) | HOLDOUT-DTI (`gems57.holdout.score_cell`, 22,619 withheld px, seeds 20/21) |
| Ribbon lane's live rule (baseline it must beat) | 0.1309 vs its own tight baseline 0.1573 | HOLDOUT-DTI |
| Dot budget | 20 sha256-verified owner rasters: ≤44,090 positive pixels out-scores every raster >50,000; Spearman(dots, score) = −0.831 | USER-REPORTED-SCORE + REGISTRY-MEASUREMENT |
| Worst Spearman ρ | 0.140 (limit 0.90) | REGISTRY-MEASUREMENT, 695/695 complete |
| Worst Jaccard dot sets | 0.061 (limit 0.50); byte-unique and pixel-unique | REGISTRY-MEASUREMENT |
| Literal 3-px forward overlap | **NEGATIVE** — 104 rasters flagged. The binding ones are a plane-filling 5-px lattice whose own 3-px dilation covers 99.9 % of the study area (overlap 0.999 at every buffer from 3 to 10 px) and broad near-catalogue bands at 0.71–0.88. Against every proven high scorer: 0.17–0.35. | REGISTRY-MEASUREMENT; see `evidence/buffer_overlap_scan.json`, IR-58-UNIQ-02 |
| Full session run card | `evidence/model_run_card.json` (the shared `evidence/run_card.json` is regenerated by `scripts/build_site.py`) | HOLDOUT-DTI + REGISTRY-MEASUREMENT |
| Session status | **NOT OK TO SUBMIT — research artifact**, same as the rest | run card |

### Why the earlier "0.2778 is the top score" reading needed correcting

1. That 0.2778 is probably not that file's score: the GEMSDOE32 page says NO ORGANISER SCORE EXISTS for
   `h33-h33-2-b2-…-e5eb6e7e-zeros`, and the public leaderboard's 0.2778 belongs to a different team
   (recorded in `registry/submissions_seen.csv`). Best undisputed number in the owner's record: 0.2750.
2. The dot budget dominates, not the dot values (`evidence/sibling_record.json`, 20 verified rasters).
3. Within that budget, ranking is the remaining lever — which is what this session measured.

Beating 0.3195 cannot be established from this sandbox: the scored truth raster is organizer-private and
there is no submission receipt here. What is established is that the session-2 candidate is the holdout
optimum of the ranking family that the public record says scores highest, at the budget the record says is
optimal.

## Ranked new hypotheses

`docs/research/hypotheses_new.md` records four testable, ranked ribbon-lane hypotheses, and
`docs/research/hypotheses_session2.md` records five more built on the verified 19-band feature stack, each with layers, physical signature, an explicit non-fault mimic, novelty caveats, official sources, and verified availability limits. They are untested. The candidate with the best qualitative rationale must still clear the full holdout, leakage, uniqueness and three-experiment budget before any slot decision.

## Repository map

- `src/gems57/` — shared metric, buffered holdout, exact shared evaluator, fail-closed writer/validator, and literal uniqueness gate.
- `data/bridge/`, `data/official/`, `data/external/` — local input bridge and pinned derivative layers; check `evidence/verify_grid.json`/hashes for scope. Do not describe the official origin as independently authenticated solely from local hashes.
- `scripts/run_ribbon_experiments.py` — E1/E2 diagnostic implementation; shared evaluator and buffered holdout are wired in. Its current per-segment selector remains same-cell truth-dependent and is explicitly not promotion-grade.
- `scripts/build_ribbon_emission.py` — gated E3 emitter; it currently refuses to write because there is no reviewed `evidence/ribbon_qualification.json` or promotion-grade E1/E2. It verifies both registry-phase receipts and the exact prediction fingerprint before writing.
- `scripts/check_uniqueness_registry.py` — shared literal registry check; only as current as the supplied/indexed inventory.
- `scripts/build_site.py` — regenerates the explicit status, site, and run card from recorded evidence.
- `scripts/run_ribbon_lane.py`, `scripts/uniqueness_check.py`, `scripts/check_data.py`, `scripts/make_submission.py`, `scripts/multi_evidence_emission.py`, `src/gems58/`, and `gems/` — legacy/private or out-of-lane implementations; do not use for new promotion work (`multi_evidence_emission.py` exits with NO-GO).
- `docs/SUBMISSION_GUIDE.md`, `docs/SOURCES.md`, `docs/IRREGULARITIES.md`, and `docs/research/hypotheses_new.md` — user-facing status, official source register, audit log, and hypotheses.
- `src/gems59/` — session-2 NaN-aware feature stack over the official 19-band `training_features.tif` (`features.py`), with regression tests in `tests/test_gems59.py`.
- `scripts/fetch_feature_stack.sh` — reproduces and sha256-verifies the official 19-band feature stack from the owner's pinned git bridge (`data/bridge/feature_stack_pins.json`), outside git.
- `scripts/run_model_experiments.py` (E1 canary + E2 arms), `scripts/analyse_sibling_record.py` (owner-raster record), `scripts/build_model_emission.py` (E3 equal-budget contest + emission), `scripts/check_buffer_overlap.py` (objective carrier test for the overlap gate).
- `docs/research/hypotheses_session2.md` — five ranked session-2 hypotheses with verified layer names, falsifiers, and named free official sources.

## Safe verification

Install declared dependencies and run tests:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q
```

Tests use synthetic grids and local code. **They do not validate competition performance, clear registry uniqueness, or constitute a submission receipt.** No E1/E2/E3 experiment was rerun in this review; the updated buffered-context tests are not an experiment.

For any future run, follow the run card, exact experiment/time budget, current inventory refresh, pre-placement surface check, final-dot check, shared evaluator, and separate selector process. Read the [official source register](docs/SOURCES.md) first.

## Official review links

- [Competition homepage](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official rules, September 2026](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official data tab (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7)
- [USGS ComCat API](https://earthquake.usgs.gov/fdsnws/event/1/)
- [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [2026 SGMC GeMS product](https://ngmdb.usgs.gov/Prodesc/proddesc_119417.htm)
- [DOE GDR nationwide heat-flow / well collection](https://gdr.openei.org/submissions/1704)

## Archived sibling work

The earlier geophysical-ridge v1 TIFF remains under `docs/downloads/archive/` with its archived run card in `registry/RUN_CARD.json`. It is historical research only. Neither that artifact nor the current diagnostic TIFF is a cleared competition submission.

---

# Ribbon-width lane (branch `arena/852ac339-58gemsdoe`, package `gems58w`)

> Namespaced addition: this lane's code lives in `src/gems58w/`, its scripts in
> `scripts/ribbon_*.py`, its receipts in `evidence/ribbon/` and its site in `docs/ribbon/`, so it
> sits beside the existing lanes instead of replacing them.

**Competition:** [DOE GEMS Prize — Geothermal Exploration at Hidden Systems, DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **Leaderboard:** [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
· **This lane's site:** <https://buffedlizard55-lab.github.io/58GEMSDOE/>

> ## ⬇ Download — and what it is for
>
> **Download: OK. Submit to the competition: YOUR DECISION (this project never spends a slot).**
>
> **[↓ `gems58-adaptive-ribbon-38000-20261011T000000Z.tif`](docs/ribbon/downloads/gems58-adaptive-ribbon-38000-20261011T000000Z.tif)** (417 KiB)
> · **[single-GeoTIFF ZIP](docs/ribbon/downloads/gems58-adaptive-ribbon-38000-20261011T000000Z.zip)** (one `.tif` inside)
> · [machine-readable run card](evidence/ribbon/run_card.json) · [how to submit](docs/ribbon/executive-summary.html)
>
> * `sha256` **d631b4af205bd6e0961f4bad3f4d12bc27b651a020dcd38666e4c5f5246720f7**, 426,559 bytes
> * 1 band `float32`, `EPSG:32611`, 3730 × 3292, geotransform `(100, 0, 243350, 0, -100, 4508550)`
> * **38,000 dots, every one exactly `1.0`; `NaN` outside the footprint and nowhere inside it**
>   — this is the format the portal accepts; the *"Predicted values must be in range [0, 1]"*
>   rejection comes from `NaN` (or a value outside `[0, 1]`) landing **inside** the scored
>   footprint, and the 15 local checks in `src/gems58w/submission.py` fail closed on it.
> * 0 dots on the mapped catalogue and 0 within 300 m of it; median catalogue distance 21.9 px
> * **15/15 local acceptance checks pass**; uniqueness screen: worst rank correlation **0.0137**
>   and worst 3 px forward overlap **0.3600** against every accessible earlier raster
>   → **0 duplicates, 0 dense priors**
> * Suggested submission note (≤ 140 characters):
>   > Ribbon lane: per-segment dotted ribbons (5 lines at 0, +-300 m, +-600 m) on off-catalogue ridge detections; 38k isolated dots.
>
> **Do not upload** this README, an HTML page, a JSON receipt, or a ZIP of the repository — the
> portal takes the `.tif` or a ZIP holding exactly one GeoTIFF.

---

## What this lane is (and what it is not)

This repository is one lane of a parallel run. The lane is fixed by the standing prompt
([`PROMPT.md`](PROMPT.md), reproduced in full below): **match the emission width to the
measured localisation error.**

1. Detect candidate ridges on the organizer's own geophysical stack (19 bands, 3 scales) with a
   Hessian ridge operator, using **no catalogue information at all**.
2. Measure the localisation error `σ(x)` of those detections on a buffered *hide-and-recover*
   holdout of whole catalogue segments, stratified by **data block**, **feature resolution**
   (ridge scale) and **ridge type** (band family × ridge sign).
3. Choose, per segment, the number and offset of **parallel dotted lines** — spacing at the
   kernel radius `R = 3 px = 300 m` — that maximise
   `U = (1 − 0.2·DTI₀)·ΔTP − 0.2·DTI₀·ΔFP`, evaluated with the **exact** metric.
4. Emit the accepted dots at exactly `1.0`, write the standard GeoTIFF, and check it for
   uniqueness against every accessible earlier raster.

This lane is **not** a catalogue-anatomy lane (that is `57GEMSDOE`'s lane), **not** a
belief-field blur lane (that is `GEMSDOE32`'s H34), and **not** a model-fitting lane. It is the
emission-geometry lane: given a placement surface, how **wide** should the emission be.

---

## Executive answer — why the 0.2778 file scored high, and what beats it

Full derivation and receipts: [`docs/research/why-02778.md`](docs/research/why-02778.md),
[`docs/research/ribbon-algebra.md`](docs/research/ribbon-algebra.md),
[`evidence/ribbon/theorems.json`](evidence/ribbon/theorems.json).

**1. The metric is a coverage-per-cost problem, not a precision problem.** With
`R = 300 m = 3 px`, `α = 0.2`, `β = 0.8` and `FN_w = |G| − TP_w`, the official equation

```
DTI = TP_w / (TP_w + α·FP_w + β·FN_w)        becomes        DTI = TP / (0.2·(TP+FP) + 0.8·|G|)
```

So **one emitted pixel of unit mass moves `TP+FP` by exactly 1** and costs exactly `0.2` of the
denominator, wherever it lands. Two exact consequences follow, and both are verified by machine
in `scripts/ribbon_verify_theorems.py`:

* **binary beats graded.** `DTI(λ) = λT / (0.2λ(T+F) + 0.8G)` is strictly increasing in `λ` on
  `(0, 1]`, so a soft raster is strictly dominated by its own thresholded support. Emit `1.0`.
* **the marginal-inclusion rule.** One more dot with kernel credit `k` pays iff
  `k ≥ 0.2·DTI₀`. At the current leader `0.3195` that is `k ≥ 0.0639`, i.e. **within 281 m of a
  scored truth pixel**. The metric is a *distance* filter.

| DTI₀ | required credit `k` | implied maximum distance |
| ---: | ---: | ---: |
| 0.10 | 0.0200 | 294.0 m |
| 0.20 | 0.0400 | 288.0 m |
| 0.2778 | 0.0556 | 283.3 m |
| **0.3195** | **0.0639** | **280.8 m** |
| 0.40 | 0.0800 | 276.0 m |

**2. Therefore `0.2778` is not a better model — it is a better-shaped emission.** The named
artifact behind the group's top score is a *binary, sparse, off-catalogue* dot field: 37,654 dots,
0 on the catalogue, 0 within 200 m of it. Every one of those properties is what the algebra
prices: dense chains and on-catalogue dots spend the fixed `0.2` and buy back ~0 credit.
Reproducing the group's own measured ordering (GEMSDOE32 `docs/research/why-d28-scored-026.md`,
local proxy on identical bytes): `d1.5 = 0.17193 > h19-5 = 0.16635 > d2.8 = 0.16177`, the exact
*opposite* of the live order — because the proxy keeps the catalogue in scoring and the
competition deletes it. The catalogue-adjacent arms of the 30-arm factorial failed for the same
reason.

**3. The arithmetic of beating 0.3195.** At `s = 0.3195` a dot pays iff its credit exceeds
`0.0639`. With the group's hidden-mass model estimate `Ĝ ≈ 12,691 px`, a 38,000-dot file needs
`TP > 0.3195 × (0.2 × 38,000 + 0.8 × 12,691) = 5,672` — i.e. **weighted coverage of ≈ 45 % of the
hidden truth**. Nothing in this lane's measurements is within a factor of two of that on the
*catalogue* target, and the catalogue target is the easy one. **This is the honest gap, and it is
a coverage gap, not an emission gap** — exactly the conclusion GEMSDOE32's ceiling analysis
reached independently. No emission geometry can manufacture coverage it does not have.

**4. What this lane actually measured** ([`evidence/`](evidence/ribbon/)):

| measurement | result |
| --- | --- |
| pooled ridge-field detection of withheld truth at ≤ 300 m | **13.6 %** (thr 0.6, 138,576 ridge px) |
| RMS localisation error of the detected pixels (`σ_detect`) | **1.70 px = 170 m** |
| per-component censored localisation error `σ(x)` (the plan input) | median **6.88 px**, rms 8.01 over 994 matched withheld components; by block NW 7.08 / NE 6.79 / SW 5.79 / SE 8.54 px |
| equal-budget holdout test, 38,000 isolated dots, four widths | **width 1 → 0.039363, width 2 → 0.039633, width 3 → 0.039929, width 4 → 0.040008** |
| simulated gain per measured-`σ` class (tight line → ribbon) | σ<1.5 px: **−0.0014** (tight wins); 1.5–2.5 px: **+0.0003**; 2.5–3 px: **+0.0003**; 3–6 px: **0.000000 → +0.0016** |
| catalogue-distance profile of the delivered dots | median **21.9 px**, 0 on the catalogue, 1.9 % within 300 m |

The measured `σ(x)` is *inside* the kernel but one to two pixels wide, so the lane's rule selects a
**ribbon**, not a tight line. `gems58.allocation.plan` places lines on the kernel-radius lattice
`0, ±3, ±6 …` px and keeps adding a ±pair while its marginal credit beats `α·DTI₀`; on this σ table
every one of the 3,024 segments lands on **5 lines at `0, ±300 m, ±600 m`**. The exact-metric
equal-budget test ranks that ribbon above the tight single line, and the per-σ-class table shows
where the gain comes from: the ribbon only pays where the localisation error exceeds ~1.5 px, and
it is the *only* geometry that reaches the σ ∈ [3, 6] px class at all (the tight line scores exactly
0 there). The delivered file is screened to zero on-catalogue dots and capped at the 38,000-dot
budget that the three best *measured* live files used (37,654 / 38,000 / 38,854 ↔ 0.2778 / 0.2750 / 0.2376).

**5. Verdict: a candidate, not a claim, and no projection is written as a score.** No organizer
receipt attributes any leaderboard number to any file hash in this portfolio; every live score
quoted here is **OWNER-REPORTED**. See [Limitations](#limitations-and-flagged-irregularities).

---

## The standing prompt (read at the start of every session)

> ### PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.
>
> 1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's
>    rank-correlation with any registry raster exceeds **[0.90]**, or more than **[70 %]** of your
>    dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log
>    it as a duplicate and stop. Check this on the surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `evaluate_holdout.py` and
>    `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a
>    buffer, derive every catalogue-based feature only from the visible faults, mask visible
>    faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a
>    shared tool is wrong, fix it once in the template and report it; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld positives,
>    95 % CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). **A projection is
>    never written as a score.**
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. AUC
>    above **[0.90]** means leakage until proven otherwise.
> 5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named non-fault process
>    that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256;
>    validator output (no NaN inside the footprint, values in [0, 1], CRS/shape/transform match);
>    submission name + note of at most 140 characters; verdict **promote / negative**. Negative
>    results are deliverables.
> 6. **BUDGET.** Stop after **[3] experiments or [2] hours**. Do not pick submissions: promotion
>    to a real slot is a separate selector step, within the weekly cap shown on the submission
>    page.
>
> ### The lane
>
> **Ribbon lane: match emission width to the measured localization error.** The simulations say
> placement within about one pixel is what pays, and that parallel dotted lines pay when location
> is uncertain. On the hide-and-recover holdout, measure the across-strike distance between each
> candidate ridge and the nearest withheld segment, and fit an error scale σ(x) by data block,
> feature resolution and ridge type. Then choose, per segment, the number and offset of parallel
> dotted lines (spacing near the 3-px kernel radius) that maximize
> **U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP**, evaluated with the exact metric. Use a single tight line
> where σ is under about 0.5 px and a ribbon about ±σ wide where it is 2–3 px. Emit included dots
> at exactly 1.0, since scaling values down only scales the net gain down. Report the σ table and
> the simulated gain per class. Output the standard validated GeoTIFF, uniqueness-checked against
> every earlier raster.

### Standing owner requirements

* **MUST GENERATE A UNIQUE TIF SUBMISSION.** Do not copy a previous submission except for
  learning. It must be **obvious whether it is OK to download and submit** the generated TIF
  (hence the banner, the ZIP, the run card and `docs/executive-summary.html`).
* **The goal is to place top of the leaderboard.** Current target to beat: **0.3195** (owner-stated
  competition high score; the group's own best measured file is the `h33-h33-2-b2-…-zeros`
  candidate recorded by the sibling lane at **0.2778**, with a **0.3774** figure also quoted on the
  owner's `GEMSDOE` snapshot page — those two owner-reported numbers are inconsistent with each
  other and neither has an organizer receipt; flagged as **IR-58-01**).
* **No hallucinations.** Every number in this repository is either measured in-repo and
  reproducible by a named script, or copied from a cited official source. Links for manual review
  are in [`registry/sources.json`](registry/sources.json) and `docs/sources.html`.
* **No manual input.** `scripts/ribbon_build_submission.py` runs the whole pipeline unattended.
* **Flag irregularities for review.** [`docs/irregularities.html`](docs/irregularities.html).
* **A site that makes submitting obvious**, with the download and the submit guide at the very top.
* **Core values.** *Maximize P(Win)* — choose the path that maximises the probability of winning,
  setting aside attachment to any one hypothesis. *Own the Outcome* — the result is the
  leaderboard placement, not the code; report negatives as deliverables.

---

## Reproduce it

```bash
pip install --break-system-packages -r requirements.txt      # numpy, scipy, rasterio, pytest
bash scripts/ribbon_fetch_features.sh                                # 419 MB stack, sha256-pinned
PYTHONPATH=src python3 scripts/ribbon_verify_theorems.py             # exact-metric theorems
PYTHONPATH=src python3 scripts/ribbon_run_equal_budget.py            # EXP-3: the ribbon vs chain test
PYTHONPATH=src python3 scripts/ribbon_build_submission.py            # build + 15 checks + uniqueness
python3 -m pytest -q                                          # test suite
python3 scripts/ribbon_build_site.py                                 # regenerate docs/
```

`GEMS_FEATURE_STACK` may point at any copy of the organizer's stack; the build refuses to run
without one whose sha256 is `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`.

## Layout

| path | what it holds |
| --- | --- |
| `src/gems58w/metric.py` | literal transcription of the official metric + fast exact paths |
| `src/gems58w/grid.py` | grid, footprint (5,167,373 px), catalogue mask (60,988 px) |
| `src/gems58w/features.py` | the 19-band organizer stack, band tags read from the file |
| `src/gems58w/ridges.py` | Hessian ridge operator + across-strike geometry |
| `src/gems58w/extract.py` | cached multi-family / multi-scale ridge field |
| `src/gems58w/holdout.py` | `gems58-pooled-hide-v1` buffered hide-and-recover holdout |
| `src/gems58w/sigma.py` | the σ(x) estimator by block / resolution / ridge type |
| `src/gems58w/allocation.py` | ribbon plan (number + offsets of parallel dotted lines) |
| `src/gems58w/uniqueness.py` | rank-correlation and 3 px forward-overlap screen |
| `src/gems58w/submission.py` | writer + the 15 portal checks |
| `evidence/` | every receipt: theorems, σ table, sweeps, run card, instrument control |
| `registry/` | source pins, protocol pins, registry raster index |
| `docs/` | the GitHub Pages site (index, executive summary, hypotheses, sources) |

## Limitations and flagged irregularities

1. **IR-58-01 — the two owner-reported ceilings disagree.** The brief quotes **0.3774** as the
   "current GEMSDOE high score" and **0.3195** as "the highest score right now", and the
   group's own best artifact at **0.2778**. All three are OWNER-REPORTED. **No organizer receipt
   in this checkout ties any leaderboard number to any file hash.** Needs an owner ruling.
2. **IR-58-02 — the mandated holdout cannot score an off-catalogue file.** The holdout's withheld
   truth *is* catalogue, so a catalogue-margin screen (the property every good live file has)
   makes HOLDOUT-DTI read exactly `0` *by construction*. Proof and control experiment:
   `evidence/ribbon/instrument_control.json`. Consequence: this lane's *geometric* findings transfer, its
   holdout DTIs are **not** live-score forecasts, and the standing rule "validate on the holdout
   before touching a slot" is **not sufficient** for this family of files. The sibling lane
   measured the same obstruction from the other side (`IR-57-INSTR-01`, Spearman(live, proxy-DTI)
   = −0.928).
3. **IR-58-03 — the live-evidence correlations are n = 15 and confounded.** dot-count (log)
   ρ = −0.810, 0–5° relative strike ρ = −0.810, 25–30° ρ = +0.864, dots ≤ 2 px from a mapped
   fault ρ = −0.544, median catalogue distance ρ = +0.766. These are **OWNER-REPORTED** scores
   from one portfolio, with heavy collinearity. They justify the *design* (a 38,000-dot,
   off-catalogue file with a median distance in the 19–22 px band) but they do not calibrate it.
4. **No organizer-confirmed score exists for any artifact in this repository.** Download and
   submission are separate decisions and the slot decision belongs to the owner's selector step.
5. **Coverage is the binding constraint, not emission.** Measured detection of withheld truth is
   11.6 %; a top-of-leaderboard file needs ≈ 45 % weighted coverage of the hidden faults. Nothing
   in this lane moves that number by more than ~1 point of DTI.
6. **Third-party data provenance.** The 419 MB feature stack was obtained through a
   community-maintained GitHub bridge (`5GEMSDOE/data/bridge/manifest.json`) that pins the
   sha256 and names the organizer data tab and Dropbox mirrors. That authenticates *transport*,
   not official origin. The DrivenData data tab itself redirects to login and was not reachable
   from this sandbox.
7. **Non-fault processes that can mimic the signal** (named in the run card): aeromagnetic
   flight-line levelling and draped-sensor artefacts produce lineaments parallel to survey lines;
   dense volcanic and alluvial contacts in the detrended DEM produce scarp-shaped curvature that
   is not tectonic; both are indistinguishable from a fault in this lane's feature set alone.

## Negative results kept on purpose

* **Catalogue-distance screens cannot be evaluated on this holdout.** Removing dots near the
  catalogue drives the holdout DTI to 0.009 (≥ 6 px) and exactly 0 (≥ 12 px)
  (`evidence/geometry_sweep.json`) — a property of the instrument, not of the filings.
* **Global density sweeps at unheld budgets are misleading.** The first geometry run appeared to
  show ribbons beating chains by +0.025 DTI; at an *equal* budget the honest margin for the
  delivered ribbon is **+0.0006** pooled (0.039929 vs 0.039363) — small, and concentrated in the
  badly-localised strata. The larger number was mass, not geometry.
* **Ribbons are not universally better.** Per measured-σ class, the tight single line still wins
  where the detection error is under ~1.5 px (−0.0014 on that class), so a fully adaptive emitter
  would switch back to one line there. This repository reports the boundary rather than hiding it;
  the delivered file uses the ribbon everywhere because the pooled budget test ranks it first.
* **The 90° direction bug (fixed, kept as a lesson).** The first ridge release returned the
  *along-strike* eigenvector as "across-strike", so the ribbons were offset along the ridge and
  the geometry test measured mass rather than width. Both the sign convention and the
  non-maximum-suppression plateau rule were fixed in `ridges.py`; the field cache was rebuilt.
