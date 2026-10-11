# 58GEMSDOE — ribbon lane

**Competition:** [DOE GEMS Prize — Geothermal Exploration at Hidden Systems, DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **Leaderboard:** [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
· **This lane's site:** <https://buffedlizard55-lab.github.io/58GEMSDOE/>

> ## ⬇ Download — and what it is for
>
> **Download: OK. Submit to the competition: YOUR DECISION (this project never spends a slot).**
>
> **[↓ `gems58-adaptive-ribbon-38000-20261011T000000Z.tif`](docs/downloads/gems58-adaptive-ribbon-38000-20261011T000000Z.tif)** (417 KiB)
> · **[single-GeoTIFF ZIP](docs/downloads/gems58-adaptive-ribbon-38000-20261011T000000Z.zip)** (one `.tif` inside)
> · [machine-readable run card](evidence/run_card.json) · [how to submit](docs/executive-summary.html)
>
> * `sha256` **d631b4af205bd6e0961f4bad3f4d12bc27b651a020dcd38666e4c5f5246720f7**, 426,559 bytes
> * 1 band `float32`, `EPSG:32611`, 3730 × 3292, geotransform `(100, 0, 243350, 0, -100, 4508550)`
> * **38,000 dots, every one exactly `1.0`; `NaN` outside the footprint and nowhere inside it**
>   — this is the format the portal accepts; the *"Predicted values must be in range [0, 1]"*
>   rejection comes from `NaN` (or a value outside `[0, 1]`) landing **inside** the scored
>   footprint, and the 15 local checks in `src/gems58/submission.py` fail closed on it.
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
[`evidence/theorems.json`](evidence/theorems.json).

**1. The metric is a coverage-per-cost problem, not a precision problem.** With
`R = 300 m = 3 px`, `α = 0.2`, `β = 0.8` and `FN_w = |G| − TP_w`, the official equation

```
DTI = TP_w / (TP_w + α·FP_w + β·FN_w)        becomes        DTI = TP / (0.2·(TP+FP) + 0.8·|G|)
```

So **one emitted pixel of unit mass moves `TP+FP` by exactly 1** and costs exactly `0.2` of the
denominator, wherever it lands. Two exact consequences follow, and both are verified by machine
in `scripts/verify_theorems.py`:

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

**4. What this lane actually measured** ([`evidence/`](evidence/)):

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
* **No manual input.** `scripts/build_submission.py` runs the whole pipeline unattended.
* **Flag irregularities for review.** [`docs/irregularities.html`](docs/irregularities.html).
* **A site that makes submitting obvious**, with the download and the submit guide at the very top.
* **Core values.** *Maximize P(Win)* — choose the path that maximises the probability of winning,
  setting aside attachment to any one hypothesis. *Own the Outcome* — the result is the
  leaderboard placement, not the code; report negatives as deliverables.

---

## Reproduce it

```bash
pip install --break-system-packages -r requirements.txt      # numpy, scipy, rasterio, pytest
bash scripts/fetch_features.sh                                # 419 MB stack, sha256-pinned
PYTHONPATH=src python3 scripts/verify_theorems.py             # exact-metric theorems
PYTHONPATH=src python3 scripts/run_equal_budget.py            # EXP-3: the ribbon vs chain test
PYTHONPATH=src python3 scripts/build_submission.py            # build + 15 checks + uniqueness
python3 -m pytest -q                                          # test suite
python3 scripts/build_site.py                                 # regenerate docs/
```

`GEMS_FEATURE_STACK` may point at any copy of the organizer's stack; the build refuses to run
without one whose sha256 is `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`.

## Layout

| path | what it holds |
| --- | --- |
| `src/gems58/metric.py` | literal transcription of the official metric + fast exact paths |
| `src/gems58/grid.py` | grid, footprint (5,167,373 px), catalogue mask (60,988 px) |
| `src/gems58/features.py` | the 19-band organizer stack, band tags read from the file |
| `src/gems58/ridges.py` | Hessian ridge operator + across-strike geometry |
| `src/gems58/extract.py` | cached multi-family / multi-scale ridge field |
| `src/gems58/holdout.py` | `gems58-pooled-hide-v1` buffered hide-and-recover holdout |
| `src/gems58/sigma.py` | the σ(x) estimator by block / resolution / ridge type |
| `src/gems58/allocation.py` | ribbon plan (number + offsets of parallel dotted lines) |
| `src/gems58/uniqueness.py` | rank-correlation and 3 px forward-overlap screen |
| `src/gems58/submission.py` | writer + the 15 portal checks |
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
   `evidence/instrument_control.json`. Consequence: this lane's *geometric* findings transfer, its
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
