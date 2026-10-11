# Source register

Checked from the sandbox on **2026-10-11 (UTC)**. "HTTP" is the status code returned to this sandbox.
Only GitHub, PyPI, and npm are reachable. Every other host returned no response (`000`).
Blocked does not mean the page is down. Re-check from a normal network before relying on any fact.

| # | Source | Used for | HTTP here | Status |
|---|---|---|---|---|
| S1 | https://github.com/drivendataorg/gems-prize-reference-solution | Official reference notebook: grid 3292×3730, EPSG:32611, 100 m, float32, 19 bands; submission written with the label CRS/transform | 200 (cloned, commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`, 2026-06-16) | **VERIFIED (official, read directly).** No LICENSE file in the repo, so reuse terms are unknown. We copied no code from it. |
| S2 | https://www.drivendata.org/competitions/306/competition-doe-gems/ | Competition homepage, deadline, rules | 000 | UNREACHABLE. Facts only via third-party guide (S8). |
| S3 | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | Problem description, metric, submission format | 000 | UNREACHABLE. Metric formula only via S8. |
| S4 | https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/ | About page | 000 | UNREACHABLE |
| S5 | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ | Data download (login required) | 000 | UNREACHABLE; login required per project brief |
| S6 | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ | Leaderboard | 000 | UNREACHABLE. Leaderboard numbers in this repo are user-supplied (see LEADERBOARD.md). |
| S7 | https://docs.nlr.gov/docs/fy26osti/96647.pdf | Official rules | 000 | UNREACHABLE. Eligibility, deadline, and AI-disclosure terms not verified. |
| S8 | https://github.com/Aayushk333/gems-prize-challenge (third-party collaborative workspace) | Metric formula (DTI, α=0.2, β=0.8, R=300 m), validator checklist, grid bounds/transform from a data inventory | fetched (not re-verified) | **THIRD-PARTY, UNVERIFIED.** It cites the DrivenData page for the metric. Its transform (243350, 4508550) comes from a teammate's inventory, not from a file we hold. |
| S9 | https://github.com/drivendataorg/metrics | Official DrivenData metrics library | 200 (cloned) | Checked: contains `metrics.py` only, with **no GEMS/DTI implementation**. |
| S10 | https://api.github.com/orgs/drivendataorg/repos | Searched the org for GEMS-specific tooling | 200 | No official GEMS scorer or sample submission found. |
| S11 | https://github.com/ItIsCuthNotCup/DrivenData-GEMS-Prize-Challenge | Third-party repo | 200 (empty repository) | Empty. Not used. |
| S12 | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and | GeoDAWN source data release | 000 | UNREACHABLE |
| S13 | https://gdr.openei.org/submissions/1391 | Competition data (OpenEI GDR) | 000 | UNREACHABLE |
| S14 | Four Dropbox links in the project brief (example_submission.tif, existing_faults.tif, gems-geodawn-numerical-features.tif, GEMS_96647.pdf) | Competition data | TLS EOF from sandbox (`scripts/fetch_data.py`, logged in `data/fetch_log.json`) | UNREACHABLE from sandbox |
| S15 | https://epsg.io/32611 | UTM 11N definition | 000 | UNREACHABLE. EPSG:32611 is taken from S1. |
| S16 | https://en.wikipedia.org/wiki/Tversky_index | Tversky index background | 000 | UNREACHABLE |
| S17 | https://gbcge.org/current-projects/ingenious/ | INGENIOUS project | 000 | UNREACHABLE |
| S18 | https://community.drivendata.org/c/gems-prize-challenge/111 | Forum (clarifications) | 000 | UNREACHABLE. S8 says it had no substantive threads at its 13 Sep 2026 check. |
| S19 | https://pypi.org/project/rasterio/ | rasterio 1.4.4 (GDAL 3.10.3) installed from PyPI | 200 | VERIFIED install |
| S20 | https://buffedlizard55-lab.github.io/... (all GEMSDOE submission sites) | Prior submissions and scores | 000 | UNREACHABLE. Uniqueness cannot be checked, and the h33 (0.2778) raster cannot be read. |

## Open verification items
1. Official metric page (S3) and worked example (~0.60, per S8). Needed to validate `gems/metric.py`.
2. Official rules (S7): deadline (S8 reports the homepage says 3 Dec 2026 11:59 p.m. UTC, while the rules say 5 p.m. ET on the deadline date; unverified), eligibility, AI disclosure.
3. example_submission.tif (S14): authoritative grid, transform, and NaN footprint.
4. Registry rasters (S20): needed for the correlation and dot-overlap uniqueness checks.
