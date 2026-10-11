# Source register and verification log

Last checked: **2026-10-11 (UTC)**. Statuses below distinguish official page text, metadata/API availability checks, and data bytes actually downloaded. A public catalogue entry is not proof that a large payload was downloaded or that a layer has complete coverage.

## Competition and submission rules

| Source | Verified from the page | Status / limit |
|---|---|---|
| [DrivenData competition homepage](https://www.drivendata.org/competitions/306/competition-doe-gems/) | Displayed end date: **Dec. 3, 2026, 11:59 p.m. UTC**; instructions say enroll, download from the data tab, create a prediction, then use “Submit” / “Make new submission”. Page says external data is allowed when licensing permits and the data can be shared with organizers for independent verification. | Fetched directly 2026-10-11. The page is public; the data tab redirects to login. |
| [DrivenData problem description, page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | New-fault task; public USGS/INGENIOUS labels are incomplete and can contain inaccuracies; GeoDAWN and INGENIOUS context; DTI with α=0.2, β=0.8 and triangular radius 300 m (3 pixels at 100 m); output is a single-band float32 GeoTIFF in EPSG:32611, 100 m, matching training bounds, values in [0,1], and null/NaN outside the bounds. External data is allowed subject to license and organizer-sharing requirements. | Fetched directly 2026-10-11, both chunks. |
| [Official GEMS Prize Rules (Sept. 2026 PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | §3.4 permits up to three automated-scoring submissions per week; only one final submission is selected across both prize rounds. §3.2 requires generative-AI use to be described in the narrative when applicable. Appendix A says 5:00 p.m. ET on the deadline date. | Fetched directly 2026-10-11. Eligibility, final package, code/documentation, and other terms remain the competitor’s responsibility; read the complete PDF. |
| [DrivenData rules landing page](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) | Links to the official rules resource. | Fetched directly 2026-10-11. |
| [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Redirects to the DrivenData login page. | Fetched directly 2026-10-11. No login was attempted. |
| [DrivenData submissions page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/) | Redirects to the DrivenData login page. | Fetched directly 2026-10-11. No account action or upload was performed; there is no receipt for the current 58GEMSDOE diagnostic TIFF in this workspace. |
| [DrivenData official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Snapshot observed 2026-10-11 UTC: xiaofanhu rank 1 / 0.4133; DARD rank 8 / 0.3195; extradr19 rank 23 / 0.2778. | Fetched directly from the public page. Dynamic public rows; no file/hash crosswalk or submission receipt was exposed. The selected rows and caveat are saved in `evidence/official_leaderboard_observation_20261011.json` and `docs/LEADERBOARD.md`. |
| [GEMSDOE32 owner-maintained H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) and [public GitHub source](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/index.html) | Page states “NO ORGANISER SCORE EXISTS” for the named H33 artifact and labels 0.2747 a model projection. | The page source was fetched live through GitHub's public contents API on 2026-10-11. This is a team-maintained statement, not an organizer receipt; it does not identify which file earned extradr19's 0.2778 leaderboard row. |

### Deadline discrepancy

The public competition homepage states **Dec. 3, 2026, 11:59 p.m. UTC**. Appendix A of the Sept. 2026 official rules states **5:00 p.m. ET** on the deadline date. On Dec. 3, ET is UTC−5, so that is 22:00 UTC—earlier than the homepage display. Until the organizer clarifies, plan to the earlier official-rules cutoff and verify the live page before acting. This repo has not contacted the organizer.

## Official data sources checked for future hypotheses

| Source | Availability check | What is and is not established |
|---|---|---|
| [USGS GeoDAWN data release](https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) | USGS catalog page fetched; it identifies a public USGS/DOE airborne magnetic and radiometric release and links “Get Data and Metadata”. The metadata describes GeoTIFFs and other deliverables. | Public listing/data link verified. The raw GeoDAWN files were not downloaded in this review. Competition-provided feature-stack content is a separate source. |
| [USGS ComCat FDSN Event API documentation](https://earthquake.usgs.gov/fdsnws/event/1/) | API documentation fetched. For the competition-area WGS84 bounding box `-120.038,37.331,-116.140,40.728`, 1970-01-01 onward, the count endpoint returned 15,169 events at M≥2.5; a one-event GeoJSON query succeeded. M≥2.0 returned 37,766 (above the API’s 20,000 result limit); a broader M≥1.5 query returned an HTTP 400 for 102,533 results. | The endpoint is reachable and a constrained slice is obtainable; a complete M≥1.5 catalogue requires pagination/time or magnitude partitioning. The API returns earthquake data, not a validated fault map. |
| [USGS The National Map 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) and [TNM Access API](https://tnmaccess.nationalmap.gov/api/v1/products) | USGS says 3DEP products are free. An AOI query for the study-area bounding box and `Digital Elevation Model (DEM) 1 meter`, GeoTIFF, returned **1,856** product records; the sample record was a Nevada 1 m DEM tile with a direct download URL. | Product coverage/catalogue availability verified; no DEM tile was downloaded or mosaicked. 1 m work is likely substantial and needs seam/coverage checks. |
| [USGS SGMC page](https://www.usgs.gov/data/state-geologic-map-compilation-sgmc-geodatabase-conterminous-united-states), [2026 GeMS product entry](https://ngmdb.usgs.gov/Prodesc/proddesc_119417.htm), DOI [10.5066/P1A3DQZK](https://doi.org/10.5066/P1A3DQZK) | USGS says the legacy SGMC release was updated in 2026 and recommends the newer GeMS-format release. The NGMDB product page (publication 2026) exposes a GIS data link. Fetching that GIS link returned HTTP 500 in this check. | New catalogue entry and download link verified; binary download not verified. Do not describe the updated polygons as already locally available. |
| [DOE Geothermal Data Repository submission 1704](https://gdr.openei.org/submissions/1704) | Page fetched; it identifies a publicly accessible CC-BY collection with 44,000+ US wells, Nevada archives/indexes, and a 21.6 GB / 25-file resource bundle. | Page and resource links verified; files not downloaded. The size makes index-first filtering mandatory. |
| [USGS 3DEP lidar FAQ](https://www.usgs.gov/faqs/what-lidar-data-and-where-can-i-download-it) | Fetched; it directs users to LidarExplorer, The National Map Download Client, and services. | General access confirmed. Exact per-tile coverage was checked separately with the TNM API above. |

## Repository and raster evidence

- Competition/reference repository: [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), cloned/read at commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`. Official data-page contents and the checked-in bridge files are not authenticated by this commit alone.
- Local bridge files are pinned in `src/gems57/grid.py`; local raster metadata/hash checks establish agreement among those files, not independent organizer provenance.
- Frozen public-raster manifest: `registry/registry_refreshed.json`, generated `2026-10-10T19:58:45.875405Z`, 57 repository snapshots, 695 unique raster blobs. See `evidence/registry_freshness_audit.json`: subsequent GitHub tree checks found unrepresented or changed repositories and new TIFFs. This scan is **not current/exhaustive**.
- The current candidate’s legacy frozen-snapshot report is `evidence/ribbon_uniqueness.json`. It has a literal 3-pixel dot-overlap failure; it is not a uniqueness clearance.

## Claims deliberately not made

- The 2026-10-11 public-board snapshot is not an organizer receipt, a final private-round result, or an attribution to a TIFF. No official hash-to-score crosswalk for the GEMSDOE32 H33 file or the current 58GEMSDOE diagnostic was obtained.
- No organizer score/receipt for the current 58GEMSDOE TIFF was obtained. No model result in the local run evidence is `ORGANIZER-CONFIRMED`.
- The GEMSDOE32 owner page's no-score/projection statement is a team-maintained page, not independent organizer confirmation.
- No raw GeoDAWN, SGMC 2026, 3DEP DEM, or GDR archive was downloaded in this review.
- No organizer confirmation was obtained for the deadline discrepancy, NaN/mask behavior, or whether any candidate file is accepted.

---

## Session 3 verification log (2026-10-11) — register rows S17–S24

`bash` egress in this sandbox is limited to github.com / codeload / api.github.com / pypi, but the
`fetch_page` tool reaches DrivenData, the community forum and GitHub. Everything below was read with
`fetch_page` on 2026-10-11 and is recorded verbatim in
[`evidence/organizer_confirmed.json`](../evidence/organizer_confirmed.json) with its URL; the register
rows are S17–S24 of [`registry/sources.csv`](../registry/sources.csv).

| What was verified | Source | Consequence |
|---|---|---|
| **Known USGS/INGENIOUS fault pixels are masked out of evaluation in both rounds** (staff) | [thread 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) | Dots on the catalogue are inert, so the emitter drops only *on*-catalogue dots and keeps a non-zero HOLDOUT-DTI (IR-58-02) |
| The public leaderboard is **pooled**; the final round re-evaluates the **whole GeoDAWN area**; **subset membership will not be disclosed** (staff) | [thread 11550](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550) | No owner-quoted score can be modelled (IR-58-LIVE-01); the budget comes from the measured family, not a fit |
| **Test-fault provenance will not be disclosed**; Phase-2 labels are updated by expert review of all Phase-1 submissions (staff) | [thread 11527](https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527) | No local held-out truth set can be reconstructed; the mandated holdout can only score catalogue recovery |
| The **reference solution**: Tversky α 0.2 / β 0.8 binary surrogate, `labels.tif` ≡ `existing_faults.tif`, writer emits single-band float32 with crs/transform from labels and **no NaN inside the footprint** | [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) (cloned) | Grounds the writer and the NaN rule; the shared scanner was fixed to accept the official NaN-outside-footprint representation (IR-58-UNIQ-05) |
| GeoDAWN acquired **aeromagnetic *and* aeroradiometric** surveys plus coordinated **3DEP lidar**; "most faults … are more subtle, and many are hidden below the surface" | [page 968](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | The delivered 19-band stack has **no** radiometric or 1 m lidar channel (IR-58-DATA-01); recorded as an owner-download hypothesis only |
| The one missing registry pin `927dc17f…` was recovered from `55GEMSDOE` commit `d92606c2…` and re-hashed to the pin (1,516,449 B) | git protocol | The witness inventory is now 695/695 pinned + a current-tree delta = **703** byte-verified rasters (IR-58-REG-01) |
| Owner-quoted sibling scores and their site URLs | sibling GitHub Pages sites | 78 rows in `registry/live_scores_owner_reported.csv`; 66 matched to verified bytes; calibration verdict **NEGATIVE** |

### Claims deliberately not made (session 3)

- No organizer score or receipt was obtained **for any file in this repository**; gate G6 on the site can
  never pass from this sandbox, and no local number is presented as ORGANIZER-CONFIRMED.
- No raw GeoDAWN, SGMC 2026, 3DEP DEM or GDR archive was downloaded; none is fetchable here, so no
  number is derived from them.
- No candidate file has been accepted by the portal: the 15-check preflight reproduces the published
  format rules locally and is not an acceptance.
- The frozen inventory is a **public sibling-repository** inventory, not an organizer registry. Its
  freshness caveat is closed for the 56 reachable clones' current default branches, not for private,
  renamed or deleted repositories.
