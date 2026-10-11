# Executive summary and submission guide

## Status (2026-10-11)
**No competition submission file has been generated yet.** The competition data is behind a DrivenData login, and this sandbox cannot reach it. Without the feature and label rasters, we cannot produce a real fault-probability map, cannot run the holdout, and cannot run the leakage canary. A file made without the data would not be a prediction, so we did not make one. See `IRREGULARITIES.md`, item 1.

The validator and writer are ready. The model that produces the probability map is not built yet. Once the data is in `data/` and a map exists, writing and validating takes one command (step 4).

## What the submission must be
- One band, **float32**, GeoTIFF (`.tif`), or a `.zip` holding one GeoTIFF.
- **CRS EPSG:32611**, 100 m pixels, the same width, height, and transform as the sample submission (competition page, per S8; unverified here).
- Values in **[0, 1]** inside the scored footprint, **NaN** outside it.
- Each submission gets a **name** and a **note** of 140 characters or fewer, so you can tell submissions apart later (for example, `ribbon-sigma-0.5px-v1: holdout-tuned widths`).

## Steps (with the commands)
1. **Get the data.** Register on DrivenData and download the files into `data/`. Public Dropbox links are tried by `scripts/fetch_data.py`, but they were not reachable from our sandbox. Log in to DrivenData yourself. We do not bypass login.
2. **Check the data.**
   ```bash
   python scripts/check_data.py
   ```
   This writes `data/inventory.json`: grid alignment, label counts, and a leakage canary for each band. Any band flagged as a leakage suspect (AUC above 0.90) must not be used until it is explained.
3. **Make a probability map** (model work is not done yet, see `README.md`). Save it as a `(3730, 3292)` float array in `[0,1]`.
4. **Write and validate.**
   ```bash
   python scripts/make_submission.py prob.npy submissions/NAME.tif --reference data/example_submission.tif
   ```
   This writes `submissions/NAME.tif` and `submissions/NAME.validation.json`. The command exits 0 only when every check passes. Use `--reference` so the grid and NaN footprint come from the official file, not from our spec.
5. **Check the validation report.** `passed` must be `true`, and `failed_checks` must be empty.
6. **Check the rules before you upload.** The rules (S7) could not be read from this sandbox. Confirm eligibility, the deadline, and the AI-disclosure terms yourself first.
7. **Upload.** Go to the submission page, choose the `.tif`, enter the name and note, and submit. Copy the score from the receipt. Only receipt scores may be labelled ORGANIZER-CONFIRMED.

## Things that are not yet true
- The deadline is unclear: 3 Dec 2026 11:59 p.m. UTC on the homepage (per S8) versus 5 p.m. ET in the rules. Plan to the earlier one.
- Uniqueness against earlier GEMSDOE rasters has not been checked (those sites are unreachable).
- The metric is an unverified approximation. Do not treat `gems/metric.py` output as an organizer score.
