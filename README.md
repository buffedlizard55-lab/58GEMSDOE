# 58GEMSDOE — GEMS competition (DrivenData #306)

## 🚫 Submission decision: **NOT OK TO SUBMIT — DO NOT SUBMIT**

The current TIFF is retained for research/audit only; **it is not a unique, promotion-grade or organizer-approved submission**. There is no organizer receipt, and no weekly submission slot has been used.

[Download the diagnostic GeoTIFF (NOT CLEARED; DO NOT SUBMIT)](docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif) · [Submission guide](docs/SUBMISSION_GUIDE.md) · [Current run card](evidence/run_card.json) · [GitHub Pages site](https://buffedlizard55-lab.github.io/58GEMSDOE/)

### Why it is blocked

- The recorded frozen-registry report finds **100%** of the candidate’s dots within 3 px of one prior full-footprint-positive raster. The literal stop limit is **>70%**. The candidate’s lower rank correlation does not override that independent stop rule. Evidence: `evidence/ribbon_uniqueness.json`.
- The frozen scan is **695 rasters from 57 pinned repository snapshots**, generated at `2026-10-10T19:58:45.875405Z`; it is not a current/exhaustive public inventory. Newer default-branch trees contain TIFs in 58/59/60/61GEMSDOE, and GEMSDOE52 has 88 TIFF paths added since its pinned tree. No complete scan of those artifacts was made. Evidence: `evidence/registry_freshness_audit.json`.
- A literal pre-placement surface comparison for this candidate against a current inventory is not available. The old pre-placement report is a different candidate and excluded dense priors; it cannot be used as clearance.
- The old holdout output is not promotion-grade: per-segment acceptance saw the same cell’s withheld truth, σ was fit on scored folds, the earlier bootstrap resampled repeated physical blocks as independent, and the split had no new buffer. A buffered shared holdout constructor and toy tests were added, but **no experiment was rerun**.
- The TIFF has a recorded **local format/range preflight** only; that is not a registry clearance, portal acceptance, or organizer score. The local all-finite/zero-outside export policy also differs from the sample’s NaN footprint behavior; see `docs/IRREGULARITIES.md`.

All of these are stop conditions. No old holdout score is presented here as a validated result.

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
| Registry freshness | 695 unique rasters across 57 pinned snapshots, but current default branches contain unscanned/changed TIFs | REGISTRY-FRESHNESS-AUDIT; incomplete/current scope false |
| Pre-placement current surface | Not checked for this candidate under a current literal inventory | NOT CLEARED |
| Promotion-grade HOLDOUT-DTI | Not run with the new buffered split; legacy result is disqualified for promotion due same-cell truth selection and invalid block bootstrap | NOT MEASURED for current instrument |
| Organizer score | No receipt | NOT AVAILABLE |
| Final status | **NOT OK TO SUBMIT — DO NOT SUBMIT** | `evidence/run_card.json` |

The number of positive raster pixels is a raster fact, not a score. No current leaderboard point or performance claim is reported.

## Ranked new hypotheses

`docs/research/hypotheses_new.md` records four testable, ranked ribbon-lane hypotheses, each with layers, physical signature, an explicit non-fault mimic, novelty caveats, official sources, and verified availability limits. They are untested. The candidate with the best qualitative rationale must still clear the full holdout, leakage, uniqueness and three-experiment budget before any slot decision.

## Repository map

- `src/gems57/` — shared metric, buffered holdout, exact shared evaluator, fail-closed writer/validator, and literal uniqueness gate.
- `data/bridge/`, `data/official/`, `data/external/` — local input bridge and pinned derivative layers; check `evidence/verify_grid.json`/hashes for scope. Do not describe the official origin as independently authenticated solely from local hashes.
- `scripts/run_ribbon_experiments.py` — E1/E2 diagnostic implementation; shared evaluator and buffered holdout are wired in. Its current per-segment selector remains same-cell truth-dependent and is explicitly not promotion-grade.
- `scripts/build_ribbon_emission.py` — gated E3 emitter; it currently refuses to write because there is no reviewed `evidence/ribbon_qualification.json` or promotion-grade E1/E2. It verifies both registry-phase receipts and the exact prediction fingerprint before writing.
- `scripts/check_uniqueness_registry.py` — shared literal registry check; only as current as the supplied/indexed inventory.
- `scripts/build_site.py` — regenerates the explicit status, site, and run card from recorded evidence.
- `scripts/run_ribbon_lane.py`, `scripts/uniqueness_check.py`, `scripts/check_data.py`, `scripts/make_submission.py`, `src/gems58/`, and `gems/` — legacy/private implementations, deprecated or disabled for new promotion work.
- `docs/SUBMISSION_GUIDE.md`, `docs/SOURCES.md`, `docs/IRREGULARITIES.md`, and `docs/research/hypotheses_new.md` — user-facing status, official source register, audit log, and hypotheses.

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
