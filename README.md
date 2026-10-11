# 58GEMSDOE — GEMS Prize Challenge workspace

**Goal:** a top-of-leaderboard submission for the DrivenData **GEMS Prize Challenge** (DOE Office of Geothermal; administered by NLR). The output is one float32 GeoTIFF of fault probabilities, EPSG:32611, 100 m, values in [0,1], NaN outside the footprint. Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/

> **Read first:** [`docs/MISSION.md`](docs/MISSION.md) (condensed project prompt, requirements, core values, ribbon-lane method). It is read at the start of every session.

## Status (2026-10-11)

| Item | Status |
|---|---|
| Submission TIF | **Not generated.** Competition data is behind a DrivenData login and unreachable from the build sandbox. See [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md). |
| Validator and writer | Ready and tested (`gems/submission.py`). 21 unit tests pass on synthetic data. |
| Metric (DTI) | Approximation from a third-party guide. **Unverified** against the official scorer. |
| Holdout + leakage canary | Code ready (`gems/holdout.py`). **Not run on real data.** |
| Holdout DTI | **None measured.** Nothing in this repo is a score. |
| Uniqueness vs. GEMSDOE rasters | **Not checked** (registry unreachable). |
| Leaderboard numbers | User-supplied, **unverified**. See [`docs/LEADERBOARD.md`](docs/LEADERBOARD.md). |
| Run card | [`docs/RUN_CARD.json`](docs/RUN_CARD.json): negative (not evaluated; not promoted). |

Pages site (once GitHub Pages is enabled for `main`, `/docs`): the executive summary and submission guide are at `docs/index.html`.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install numpy scipy rasterio pytest
python -m pytest -q tests                       # 21 tests, synthetic data only

python scripts/fetch_data.py                    # tries public links; logs to data/fetch_log.json
#   DrivenData files (training features, labels, sample submission) need a registered login:
#   download them yourself into data/.
python scripts/check_data.py                    # grid alignment, label counts, leakage canary -> data/inventory.json
python scripts/make_submission.py prob.npy submissions/NAME.tif --reference data/example_submission.tif
```

Expected local filenames: `gems-geodawn-numerical-features.tif`, `existing_faults.tif`, `example_submission.tif`. The official notebook uses different names (`numeric_features.tif`, `labels.tif`). See `docs/IRREGULARITIES.md` item 3.

## Repository layout

```
gems/metric.py         distance-weighted Tversky (DTI), approximation, unverified
gems/holdout.py        hide-and-recover folds, visible-only distance, pooled DTI, CI, AUC, leakage canary
gems/submission.py     writer + validator (CRS, transform, shape, NaN footprint, [0,1])
scripts/fetch_data.py  public-link downloader with audit log (no login bypass)
scripts/check_data.py  inventory and per-band leakage canary
scripts/make_submission.py  prob.npy -> validated GeoTIFF
tests/                 metric (incl. brute-force cross-check), submission, holdout
docs/                  index.html (Pages), SUBMISSION_GUIDE, SOURCES, IRREGULARITIES, HYPOTHESES,
                       ANALYSIS_H33, LEADERBOARD, RUN_CARD.json, AI_USAGE, MISSION
```

Competition rasters and generated TIFs are **not committed** (`.gitignore`): DrivenData terms prohibit redistribution, and large artifacts stay out of Git.

## Why the top prior submission scored what it did
See [`docs/ANALYSIS_H33.md`](docs/ANALYSIS_H33.md). Short version: unverified. The GEMSDOE32 raster is unreachable, so the causal analysis is a hypothesis list (tolerance-aware dots, calibration of false-positive mass, footprint handling), not a finding.

## Candidate hypotheses (not validated)
See [`docs/HYPOTHESES.md`](docs/HYPOTHESES.md). Top candidate: a strike-coherent tilt-angle ridge (magnetic band 6), cheapest to test. No candidate may use a submission slot until it beats the holdout best.

## Limitations
1. **No data in the build sandbox.** Everything beyond the code is blocked on the competition files.
2. **Metric not verified.** The DTI formula comes from a third-party guide. The official worked example (~0.60, per that guide) has not been reproduced.
3. **Uniqueness and correlation checks** need the registry rasters, which are unreachable.
4. **Deadline conflict** (3 Dec 2026 11:59 p.m. UTC vs 5 p.m. ET in the rules). Plan to the earlier one.
5. **Rules and eligibility** could not be read. The official rules PDF is unreachable.
6. **Reference solution has no LICENSE file.** We copied no code from it.

## What we need access to (free and official where possible)
| Need | Why | Source | Status |
|---|---|---|---|
| Competition feature raster, labels, sample submission | everything | DrivenData data page (login) | needs a registered participant |
| Official metric and worked example | validate `metric.py` | DrivenData problem page | unreachable here |
| Official rules | eligibility, deadline, AI disclosure | https://docs.nlr.gov/docs/fy26osti/96647.pdf | unreachable here |
| USGS GeoDAWN release | raw data provenance | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and | unreachable here |
| Registry GEMSDOE rasters | uniqueness checks | GitHub Pages sites listed in the brief | unreachable here |
| Earthquake catalogue (for H5 only) | earthquake lineation | USGS earthquake catalogue (not verified) | **not checked**; do not rely on it yet |

## Next steps (for the next session)
1. Place the competition files in `data/` and run `scripts/check_data.py`. Record the inventory and every flagged band.
2. Verify the metric against the official worked example. Do not use any DTI number until this is done.
3. Build the holdout (`gems/holdout.py`) and run the leakage canary on every band. Drop any band above AUC 0.90 until it is explained.
4. Test H1 (tilt-ridge) on the holdout. Only if it beats the current holdout best, implement the ribbon-lane width fit (σ table and per-class simulated gain).
5. Compare the candidate against the registry rasters when they are reachable. Run the correlation and 3-px overlap checks.
6. Write the run card and promote only if the holdout result holds.

## Core values
- **Maximize P(Win):** weigh trade-offs and choose the path most likely to succeed.
- **Own the Outcome:** own results end to end, act when we can, and learn from failure and success.

## Verification and AI disclosure
Every source is checked and logged in [`docs/SOURCES.md`](docs/SOURCES.md) with its HTTP status from the build sandbox. Irregularities are in [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md). AI use is logged in [`docs/AI_USAGE.md`](docs/AI_USAGE.md).
