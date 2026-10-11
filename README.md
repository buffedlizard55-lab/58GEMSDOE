# 58GEMSDOE — DOE GEMS Prize Challenge

Core values: **Maximize P(Win)** and **Own the Outcome** — report the actual result, including a negative one.

## Submission decision: **NOT OK TO SUBMIT — DO NOT SUBMIT**

[Download the diagnostic GeoTIFF — NOT CLEARED](docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif) · [Current run card](evidence/run_card.json) · [Submission guide](docs/SUBMISSION_GUIDE.md) · [Public site](https://buffedlizard55-lab.github.io/58GEMSDOE/)

The downloadable file is an existing **research diagnostic**, not a cleared competition submission. No new TIFF was generated in this review, no experiment or slot was used, and no organizer receipt links a score to this file.

### Why it is blocked

- **Literal final-dot duplicate stop:** 67,379 candidate dots; **100%** lie within 3 px of the prior full-footprint-positive raster `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`. The stop threshold is >70%. The candidate's rank correlation being below 0.90 does not override this independent failure. See `evidence/ribbon_uniqueness.json`.
- **Inventory is stale/incomplete:** the pinned 695-raster scan restored 694; one raster is unavailable, and a freshness audit found newer/unrepresented TIFFs. See `evidence/registry_fetch_report.json` and `evidence/registry_freshness_audit.json`.
- **Pre-placement surface gate:** not cleared for this candidate against a current inventory.
- **Promotion-grade holdout:** not measured with the current buffered/nested shared evaluator. Earlier ribbon experiments are legacy, selection-contaminated diagnostics and are not reportable as promotion-grade HOLDOUT-DTI.
- **Format evidence:** local format/range preflight passed for the recorded bytes, but that is not a current uniqueness result, portal acceptance, or organizer score. Nodata semantics remain unresolved.

Do not evade the duplicate stop by omitting dense registry rasters, emitting an empty TIFF, or treating an incomplete inventory as exhaustive. With these gates unresolved, no new experimental raster should be emitted or promoted.

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

## Ranked ribbon-width hypotheses — proposals only

The ranked, untried proposals are in [`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md). They keep the existing ridge surfaces fixed and vary only error calibration / ribbon width and offsets. They do not claim to detect a fault for which the existing ridge field has no candidate. None has been implemented or holdout-validated. The registry stop must be resolved before any experiment.

## Repository status and reproduction

- Current fail-closed status generator: `scripts/build_site.py` → `docs/index.html`, `evidence/run_card.json`, and `docs/RUN_CARD.json`.
- Shared template: `src/gems57/`; use `gems57.evaluate_holdout` and `gems57.submission_writer` only for any future qualified experiment.
- The cached 19-band feature raster is hash-pinned in `data/bridge/feature_stack_pins.json` and stored outside Git at `~/.cache/gems/training_features.tif`. Its SHA256 verifies against the owner-maintained GitHub bridge; that establishes byte integrity, not independent organizer provenance.
- Old `gems58w` ribbon experiment, feed, site, and submission CLIs are archival and disabled because they use private/unbuffered legacy paths and can publish non-promotion-grade numbers or misleading download language.

Run tests in an environment with `requirements.txt` installed:

```bash
PYTHONPATH=src python -m pytest -q
python scripts/build_site.py
python scripts/ribbon_check_site.py
```

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
