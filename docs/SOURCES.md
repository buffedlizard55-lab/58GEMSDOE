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
| [DrivenData submissions page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/) | Redirects to the DrivenData login page. | Fetched directly 2026-10-11. No account action or upload was performed; there is no organizer receipt in this workspace. |

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

- No current public leaderboard number or competitor score was checked.
- No organizer score/receipt was obtained. No number in the local run evidence is `ORGANIZER-CONFIRMED`.
- No raw GeoDAWN, SGMC 2026, 3DEP DEM, or GDR archive was downloaded in this review.
- No organizer confirmation was obtained for the deadline discrepancy, NaN/mask behavior, or whether any candidate file is accepted.
