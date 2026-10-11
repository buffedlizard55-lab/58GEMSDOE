# Sources and evidence classes

**Reviewed:** 2026-10-11 UTC. Links below are for independent review. A source statement, owner page,
local validator, or public participant row is not an organizer score receipt.

## Official competition sources

| Source | Verified fact used here | Limits / local record |
|---|---|---|
| [Competition problem page (967)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | The target is **geological faults indicative of geothermal resources**, not vents. Public USGS/INGENIOUS fault data are incomplete and may be misaligned. The posted metric is pooled DTI with α=0.2, β=0.8 and a 300 m triangular kernel; the competition describes a GeoTIFF output grid/format. | Fetched 2026-10-11. See [`evidence/organizer_confirmed.json`](../evidence/organizer_confirmed.json), [`docs/research/metric.md`](research/metric.md), and [`PROMPT.md`](../PROMPT.md). |
| [Competition About page (968)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | GeoDAWN is described as combining aeromagnetic and aeroradiometric surveys with coordinated 3DEP lidar; many faults are subtle or hidden. | Acquisition context does not mean those raw products are present in this checkout or the 19-band training stack. No outside dataset was added in this review. |
| [Official competition rules (September 2026 PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Rules consulted for competition constraints. | Earlier cutoff times shown on the competition homepage and in the PDF differ; the discrepancy is recorded as unresolved in [`IRREGULARITIES.md`](IRREGULARITIES.md). Follow the earlier cutoff pending organizer clarification. |
| [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) | Reference output/writer and sample-format context. | The organizer's sample uses NaNs outside the footprint; matching that representation does **not** prove that a different TIFF passes portal validation. No candidate-specific portal receipt was found. |
| [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Dynamic public participant rows. | The 2026-10-11 observation is labeled `PUBLIC-LEADERBOARD-SNAPSHOT` and saved in [`evidence/official_leaderboard_observation_20261011_review.json`](../evidence/official_leaderboard_observation_20261011_review.json). It is not a private score or artifact/hash crosswalk. See [`LEADERBOARD.md`](LEADERBOARD.md). |

## H33 owner-maintained sources (not organizer receipts)

| Source | What it supports | What it does not support |
|---|---|---|
| [GEMSDOE32 landing page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | The owner labels H33-2-B2 `UNSCORED` and describes 0.2747 as a projection. | It is not DrivenData scoring evidence. |
| [H33 audit JSON](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json) | Owner-side file/audit hash `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, projected DTI 0.27467315976932155, and owner-side slot-selection metadata. | No organizer score receipt or crosswalk to the public `extradr19` 0.2778 row. `SLOT_ELIGIBLE` is not a score. |
| [GEMSDOE32 saved leaderboard page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/leaderboard.html) | A dated owner-side snapshot. | It says it reflects an October 4 read and is stale relative to the 2026-10-11 public observation. |

See [`research/why-02778.md`](research/why-02778.md) for the attribution analysis.

## Data-stack provenance

The 19-band feature names are read from the raster descriptions and summarized in
[`src/gems58w/features.py`](../src/gems58w/features.py). The expected `training_features.tif` payload
is not committed as an ordinary repository file. The owner-maintained bridge records SHA-256
`4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` in
[`data/bridge/feature_stack_pins.json`](../data/bridge/feature_stack_pins.json). That pin checks mirror integrity; it is
not an independent organizer signature. The raw stack was not downloaded in this review.

## Current local evidence

| Local record | Evidence class and scope |
|---|---|
| [`evidence/ribbon/emission.json`](../evidence/ribbon/emission.json) | Local emission/format receipt for the audit TIFF; 40,768 positive pixels and SHA-256 `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd`. Not portal acceptance, uniqueness clearance, or HOLDOUT-DTI. |
| [`evidence/ribbon/file_audit.json`](../evidence/ribbon/file_audit.json) | Independent on-disk audit passes 11/11 checks: Float32/sample grid, mask and range, decoded/file hashes, positive count, and ZIP round-trip. Local file verification only—not portal acceptance or submit eligibility. |
| [`evidence/ribbon/uniqueness_full_inventory.json`](../evidence/ribbon/uniqueness_full_inventory.json) | Candidate-matched final-dot scan: 702 indexed rasters; 81 literal triggers; `unique: false`, `stop_required: true`. It is scoped to the saved public-inventory snapshot, not an organizer-wide inventory or current freshness certification. |
| [`evidence/registry_freshness_audit.json`](../evidence/registry_freshness_audit.json) | Prior freshness audit records `fresh_current_inventory: false` / `BLOCKED_NOT_EXHAUSTIVE`. It is not superseded by the 702-raster count. |
| [`evidence/ribbon_qualification.json`](../evidence/ribbon_qualification.json) | Required qualification receipt is absent. No promotion-grade pre-placement, canary, or holdout qualification is available. |
| [`evidence/ribbon/shared_metric_crosscheck.json`](../evidence/ribbon/shared_metric_crosscheck.json) | Arithmetic cross-check of a legacy diagnostic only. It does not replace the legacy evaluator, selection protocol, or invalid min/max-as-CI interpretation. |
| [`registry/submissions_seen.csv`](../registry/submissions_seen.csv) | Attribution ledger. H33 has no numeric score recorded because no organizer receipt/hash crosswalk is available. |

## Portal `[0,1]` report — unresolved

A `[0,1]` rejection has been reported for a submission attempt, but this repository contains no
portal response payload, submission ID, or validation receipt bound to the current TIFF's SHA-256.
The local emission receipt and the official sample representation do not establish whether that
specific file passed the portal. The rejection's cause and candidate identity therefore remain
unverified. Do not claim it was caused by outside NaNs, or that matching the sample makes rejection
impossible. If another authorized attempt is ever made, preserve the exact response, timestamp,
submission ID and file hash; no attempt is authorized under the current status.

## Source ledger

The row-level source and retrieval ledger is [`registry/sources.csv`](../registry/sources.csv).
`PUBLIC-LEADERBOARD-SNAPSHOT`, `HOLDOUT-DTI`, and `ORGANIZER-CONFIRMED` are deliberately distinct:
only a hash-bound organizer score receipt can establish the last category for an artifact.
