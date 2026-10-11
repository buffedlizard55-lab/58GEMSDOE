# 58GEMSDOE — GEMS competition (DrivenData #306)

**Purpose of this repo**: produce unique, validated, high-scoring GeoTIFF
submissions for the [DOE GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/),
with every number labelled and every claim traceable to evidence JSON in
`evidence/`.

**➡ The current submission file lives at
[`docs/downloads/`](docs/downloads/) and on the site:
<https://buffedlizard55-lab.github.io/58GEMSDOE/> — the green DOWNLOAD button
at the top of that page is always the file to submit. Read
[docs/executive-summary.html](https://buffedlizard55-lab.github.io/58GEMSDOE/executive-summary.html)
for the 60-second submission instructions (fixes the portal error
"Predicted values must be in range [0, 1]").**

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
> tried yet, each naming: the specific layer(s) involved, the physical
> signature being targeted, why it should catch a fault missing from the
> USGS/INGENIOUS catalogue rather than one already in it, and how it differs
> from anything already implemented. Rank them by expected DTI improvement and
> implementation cost. Validate the top candidate on the spatially-blocked
> holdout before touching a weekly submission slot. If a candidate can't be
> validated without new external data, name the specific free, official source
> and check it's obtainable before proposing the idea as viable.
>
> Work line by line verifying from official verified trusted sources, provide
> links for manual review. No manual input. Flag any irregularities for
> review. No hallucinations. Verify line by line.
>
> Core values: **Maximize P(Win)** and **Own the Outcome** — weigh tradeoffs,
> pick the path that maximizes the probability of winning; own results end to
> end.

---

## Current status (this session, ribbon lane)

| Item | Value | Label |
|---|---|---|
| σ(cat-axis), pooled | see `evidence/ribbon_e1_sigma.json` (~2.5–3.2 px by block) | HOLDOUT-STRUCTURE |
| σ(sgmc-axis), pooled | see same (~3.0–3.5 px by block) | HOLDOUT-STRUCTURE |
| Leakage canary | PASS (max single-feature AUC 0.63 / 0.68 < 0.90) | HOLDOUT-DTI instrument |
| Tight baseline vs ribbon vs ribbon-pool | `evidence/ribbon_e2_arms.json` | HOLDOUT-DTI |
| Per-class simulated gains | `evidence/ribbon_e2_arms.json` | HOLDOUT-DTI |
| Uniqueness vs registry (695 rasters, 57 repos) | `evidence/ribbon_uniqueness.json` | REGISTRY-MEASUREMENT |
| Submission raster + receipt | `docs/downloads/*zeros.tif/.json` | local validator output |
| Run card | `evidence/run_card.json` | verdict promote/negative |

Reference receipts (ORGANIZER-CONFIRMED, copied from prior sites' pages only):
`h33-h33-2-b2-...-zeros: 0.2778` (GEMSDOE32), `dotted-h19-5-d2-8: 0.2600`,
`h27-4-solo-d28: 0.2708`, `h36-1-rung30: 0.2710`,
`anderson-geothermal-pinn: 0.2750`. Current known leaderboard high: **0.3195**
(unverified here; see the leaderboard link below). No projection in this repo
is a score.

## Layout

- `src/gems57/` — shared template package (metric, holdout, evaluator, writer,
  validator, uniqueness gates), restored verbatim from the pinned sibling
  template (57GEMSDOE) and hash-tracked by `evaluate_holdout.implementation_hashes`.
- `data/official|bridge/` — hash-pinned competition bridge rasters
  (`existing_faults` ≡ public `labels`, `sample_submission`).
- `data/external/sgmc_faults_100m.tif` — pinned SGMC fault raster (independent public mapping).
- `scripts/ribbon_lane.py` + `scripts/run_ribbon_experiments.py` — E1 σ fit +
  canary, E2 arms (exact metric).
- `scripts/build_ribbon_emission.py` — E3 live emission through the fail-closed writer.
- `scripts/fetch_registry_sparse.py`, `scripts/check_uniqueness_registry.py` — registry restore + scan.
- `scripts/build_site.py` — run card + site builder (all numbers injected from evidence).
- `docs/` — GitHub Pages site (index + executive summary + downloads).
- `docs/research/hypotheses_new.md` — 5 ranked new hypotheses with sources.

## Reproduce

```bash
pip install -r requirements.txt
python3 scripts/run_ribbon_experiments.py      # E1+E2 (writes evidence JSONs)
python3 scripts/build_ribbon_emission.py       # E3 (writes docs/downloads/*)
python3 scripts/fetch_registry_sparse.py       # restore 695 registry rasters (git protocol)
python3 scripts/check_uniqueness_registry.py docs/downloads/<candidate>-zeros.tif
python3 scripts/build_site.py                  # run card + site
python3 -m pytest tests/test_metric.py         # shared metric oracle tests
```

## Verification pointers (official sources)

- Competition & rules: https://www.drivendata.org/competitions/306/competition-doe-gems/ ·
  problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ ·
  data tab (login): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- GeoDAWN airborne mag+radiometric survey (USGS): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS (GBCGE): https://gbcge.org/current-projects/ingenious/ ·
  OpenEI GDR submission 1391: https://gdr.openei.org/submissions/1391
- Grid CRS: https://epsg.io/32611 · Metric family: https://en.wikipedia.org/wiki/Tversky_index
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

## Irregularities log

See `docs/research/irregularities.md`.
