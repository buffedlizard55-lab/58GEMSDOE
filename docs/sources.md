# Sources — verification ledger

Every row says **how** it was checked. Nothing here is cited from memory.

Verification levels:
- **FETCHED** — opened by the sandbox this session (GitHub hosts are the only ones reachable; the sandbox allow-list is github.com, api.github.com, codeload.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org).
- **SEARCH-EXCERPT** — the page text was returned by the web search tool this session, but the page itself could not be opened from the sandbox. Open the link yourself for manual review.
- **UNREACHABLE** — neither opened nor searched; cited only from the user's brief or a repo file. Treat as unverified.
- **SECOND-HAND** — stated in another project's repo; not checked against the original.

Link check run 2026-10-11 (curl, HTTP status): GitHub links returned 200; drivendata.org, docs.nlr.gov, gdr.openei.org, doi.org, usgs.gov, sciencebase.gov, epsg.io and en.wikipedia.org returned 000 (no connection from the sandbox).

## A. Competition and rules

| # | Source | Used for | Verification | Link |
|---|---|---|---|---|
| A1 | DrivenData, GEMS Prize problem description (page 967) — DTI definition, R = 300 m (3 px), α = 0.2, β = 0.8, TP_w/FP_w/FN_w formulas | Metric | SEARCH-EXCERPT (formulas match `src/gems58/dti.py`) | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ |
| A2 | DrivenData competition page | Overview, submission limits | UNREACHABLE (not opened) | https://www.drivendata.org/competitions/306/competition-doe-gems/ |
| A3 | DrivenData leaderboard | Public scores | UNREACHABLE. The score ledger in another repo records a 2026-10-03 snapshot (rank 1 = 0.3195) — SECOND-HAND | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ |
| A4 | DrivenData data tab | Input file list | UNREACHABLE (login-gated per the user's brief) | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ |
| A5 | Official rules, NLR document 96647 (Sept 2026) | Submission format, what is scored, §3.5 "distance-weighted Tversky index" | UNREACHABLE. A text extraction is in the GEMSDOE repo (`data/evidence/rules_extracted_text.txt`) — SECOND-HAND | https://docs.nlr.gov/docs/fy26osti/96647.pdf |
| A6 | DrivenData forum thread 11516 — whether known USGS/INGENIOUS faults are masked when scoring | Holdout mask design | UNREACHABLE. Cited by two other repos (GEMSDOE32 `src/gems32/metric.py`; LEARNGEMSDOE PR #3, which quotes a staff reply that the mask is "pixel-exact"). **Not verified here — the holdout uses the mask as an assumption.** | https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516 |
| A7 | Reference solution (John Lipor, PSU) — README + `unet-mc-cv-reference-solution.ipynb` | Output format (single-band GeoTIFF from `labels.tif` georeferencing), Tversky loss α = 0.2, β = 0.8, patch size 128 | FETCHED (commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`, 2026-06-16) | https://github.com/drivendataorg/gems-prize-reference-solution |

## B. Data (the competition rasters are not downloadable from the sandbox)

| # | Source | Used for | Verification | Link |
|---|---|---|---|---|
| B1 | INGENIOUS — Great Basin Regional Dataset Compilation (GBCGE, NBMG, UNR, 2022), DOI 10.15121/1881483. This is the source of the training labels. | Known faults (`labels.tif` = `existing_faults.tif`) | SEARCH-EXCERPT (DOI and citation). The GDR record is not reachable from the sandbox. | https://gdr.openei.org/submissions/1391 · https://doi.org/10.15121/1881483 · https://gbcge.org/current-projects/ingenious/ |
| B2 | USGS data release, GeoDAWN airborne magnetic and radiometric surveys, northwestern Great Basin NV/CA, DOI 10.5066/P93LGLVQ (Glen & Earney, 2024). Pub. date 2024-03-01; data 2021-08-01 to 2022-11-20. Includes .zip grids (`22103_area1_grids.zip` 42.43 MB; `22103_area2_grids.zip` 227.39 MB) and .gdb files. | Source of the 19-band feature stack (magnetic, gravity, strain, DEM-derived, seismic) | SEARCH-EXCERPT. **Not reachable from the sandbox — this is the single most useful unexploited free source (raw, finer-than-100 m grids), and it cannot be downloaded from here.** | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and · https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7 · https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7 |
| B3 | USGS Quaternary Fault and Fold Database (QFFD) — about 2,000 Quaternary faults, US (USGS Fact Sheet 2004-3033) | Candidate independent fault catalogue (not used in this build) | SEARCH-EXCERPT (the 2004 fact sheet text). Current database at the USGS earthquake hazards site was not reachable. | https://pubs.usgs.gov/fs/2004/3033/fs-2004-3033.html · https://earthquake.usgs.gov/hazards/qfaults/ |
| B4 | Feature-stack band descriptions (19 bands, EPSG:32611, 100 m, 3292 × 3730) | Band definitions in this build | FETCHED from the file tags of `training_features.tif` (sha256 pinned, see `data/bridge/manifest.json` in the GEMSDOE repo) | https://github.com/buffedlizard55-lab/GEMSDOE (`data/bridge/manifest.json`) |
| B5 | Competition rasters as reproduced in the GEMSDOE repo's `data/bridge/` (split parts, sha256 pins) | Inputs for this build | FETCHED; all three whole-file hashes match the manifest pins. These hashes prove the bytes match the pins, **not** that the pins match DrivenData. | https://github.com/buffedlizard55-lab/GEMSDOE/tree/main/data/bridge |
| B6 | EPSG:32611 (WGS 84 / UTM zone 11N) | CRS of every raster | Read from the GeoTIFF headers in this build (FETCHED). epsg.io is UNREACHABLE. | https://epsg.io/32611 |

## C. Method references

| # | Source | Used for | Verification | Link |
|---|---|---|---|---|
| C1 | Tversky index (Wikipedia) | Background on α/β asymmetry | UNREACHABLE from sandbox; statement is textbook-level and not load-bearing | https://en.wikipedia.org/wiki/Tversky_index |
| C2 | scikit-image `sato` ridge filter; `remove_small_objects` (0.26.0 API: `max_size`) | Candidate ridges | FETCHED from installed package docs/warnings (scikit-image 0.26.0) | https://pypi.org/project/scikit-image/ |
| C3 | SciPy `distance_transform_edt`, `cKDTree` | Exact metric and overlap tests | FETCHED (SciPy 1.17.1 installed from PyPI) | https://pypi.org/project/scipy/ |

## D. Other GEMS repos (third-party; SECOND-HAND unless stated)

| # | Repo | What it is | Why it matters | Link |
|---|---|---|---|---|
| D1 | `buffedlizard55-lab/GEMSDOE32` (FETCHED) | Source of the 0.2778 submission and its audit JSON; score ledger; holdout code | Source for the analysis of the top submission; its holdout reports DTI 0.0046 for the 0.2778 file (see irregularities) | https://github.com/buffedlizard55-lab/GEMSDOE32 |
| D2 | `buffedlizard55-lab/GEMSDOE` (FETCHED) | Holds the competition rasters in `data/bridge/` and 80+ registry TIFs | Input source and the uniqueness registry | https://github.com/buffedlizard55-lab/GEMSDOE |
| D3 | `Gameassassin777/gems-eval` (SEARCH-EXCERPT) | Says it implements the published DTI and a held-out-segment protocol. Its README reports the reference model at 0.0435 held-out vs 0.0387 leaderboard — SECOND-HAND, one data point | Independent second implementation of the DTI and a calibration point | https://github.com/Gameassassin777/gems-eval |
| D4 | `buffedlizard55-lab/LEARNGEMSDOE` PR #3 (SEARCH-EXCERPT) | Claims the mask is pixel-exact (quoting forum post 4) | Central to the holdout mask assumption; SECOND-HAND | https://github.com/buffedlizard55-lab/LEARNGEMSDOE/pull/3 |
| D5 | `Svyable/GEMS-CONTEST` (SEARCH-EXCERPT) | Says the competition closes 2026-12-03 23:59 UTC | Deadline is SECOND-HAND; confirm on the DrivenData page | https://github.com/Svyable/GEMS-CONTEST |
