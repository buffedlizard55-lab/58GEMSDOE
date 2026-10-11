# Session-2 candidate hypotheses (ranked), grounded in the verified feature stack

## What changed that makes these testable now

The official 19-band `training_features.tif` was previously unavailable in this sandbox. It is now
reproduced here from the owner's sha256-pinned git bridge and verified part-by-part **and** whole-file
before use:

* pins: `data/bridge/feature_stack_pins.json`
* fetch + verify: `scripts/fetch_feature_stack.sh`
* manifest of record: <https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/data/bridge/manifest.json>
* whole file: 418,912,844 B, sha256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`

The 19 band names below are read from the raster's own band descriptions (not from any web page), so the
layer references in each hypothesis are verifiable:

| # | Band | Description in the raster |
|---|---|---|
| 1 | `mag_anom` | Magnetic anomaly - deviation from expected Earth's magnetic field |
| 2 | `rtp` | Reduced to pole magnetic data |
| 3 | `tmi_hg` | Total magnetic intensity horizontal gradient |
| 4 | `geod_2ndinv` | Geodetic second invariant - strain-rate tensor magnitude |
| 5 | `iso_grav_anom_slope` | Isostatic gravity anomaly slope |
| 6 | `tc` | Tilt angle or total curvature - magnetic field derivative for edge detection |
| 7 | `geod_shearrate` | Geodetic shear rate |
| 8 | `geod_dilaterate` | Geodetic dilatation rate |
| 9 | `tmi_vg` | Total magnetic intensity vertical gradient |
| 10 | `deq_n100a15` | Distance to earthquake (n=100 km radius, a=15 deg azimuth parameters) |
| 11 | `iso_grav_anom_vg` | Isostatic gravity anomaly vertical gradient |
| 12 | `det_elev` | Detrended elevation |
| 13 | `iso_grav_anom` | Isostatic gravity anomaly |
| 14 | `tmi` | Total magnetic intensity |
| 15 | `depth_to_base_surf` | Depth to basement surface |
| 16 | `ieq_n100a15` | Earthquake intensity or density (n=100 km radius, a=15 deg parameters) |
| 17 | `cond_surf` | Conductivity surface - electrical conductivity of subsurface |
| 18 | `iso_grav_anom_hg` | Isostatic gravity anomaly horizontal gradient |
| 19 | `det_elev_slope` | Detrended elevation slope |

## What is already implemented (so "new" means new)

* `src/gems57/*` (shared template): hide-and-recover holdout, exact DTI, ridge/segment geometry,
  off-catalogue masks, damage-zone envelope, relay/bend anatomy, strand orientation, strike zones,
  uniqueness gates, fail-closed writer.
* `src/gems58/ribbon.py` + `scripts/ribbon_lane.py`: skeleton-axis ridges, sigma fit, parallel dotted
  ribbons (the previous session's lane).
* `src/gems59/*` (this session): NaN-aware structure-tensor coherence at sigma 1 and 3 px, 3/7 px local
  sigma, Laplacian, over the 19 bands, feeding a leave-one-quadrant-out gradient-boosted ranking.

## Candidates, ranked by (expected DTI improvement) / (implementation cost)

### 1. Basement-depth step detection — *blind* faults under alluvium
* **Layers:** `depth_to_base_surf` (15), gated by `cond_surf` (17).
* **Physical signature:** the lateral gradient and second directional derivative of basement depth. A
  range-front or intrabasin normal fault produces a *step* in basement depth even where the surface is a
  smooth alluvial apron.
* **Why it should catch a catalogue gap rather than a catalogue hit:** the public catalogue is compiled
  from surface expression (scarps, lineaments). A fault buried beneath basin fill has no surface trace to
  digitise, so it is systematically absent from QFaults/INGENIOUS while remaining a clear basement
  discontinuity. This is exactly the "hidden fault" population the competition says it scores.
* **Difference from existing code:** nothing in this repo or in the sibling template treats
  `depth_to_base_surf` as an edge-detection target; the current operators are all magnetics/topography
  texture.
* **Cost:** low. One new operator family on one band, reusing the existing block-wise, NaN-aware
  machinery and the same LOQO ranking + budget pipeline.
* **Falsifier:** if the basement-depth step AUC on the holdout does not exceed the tilt-angle band
  (0.584 measured, `evidence/model_e1e2.json`), drop it.

### 2. MT surface-conductivity lineaments — the *geothermal* layer, not just the structural one
* **Layers:** `cond_surf` (17).
* **Physical signature:** narrow, linear, high-conductivity anomalies = hydrothermal clay and alteration
  along fracture zones; also fluid-filled fracture porosity.
* **Why it should catch a catalogue gap:** alteration halos are neither topographic nor magnetic, so they
  are essentially invisible to the mapping that produced the catalogue, yet they are the single layer
  whose physics is about *permeable, altered, fluid-bearing* rock — i.e. about geothermal resource, not
  just structure.
* **Difference:** no repo in the registry uses MT conductivity as a lineament source; it appears in the
  stack and is otherwise unused.
* **Cost:** low-medium (one operator family + canary).
* **Falsifier:** canary AUC must beat the best current single band.

### 3. Strain-partitioning ratio (dilatation vs shear) — dilational jogs and stepovers
* **Layers:** `geod_dilaterate` (8), `geod_shearrate` (7), `geod_2ndinv` (4).
* **Physical signature:** `|dilatation| / shear` isolates volumetric strain from simple shear. Dilational
  jogs and stepovers on Walker Lane structures are where fracture permeability concentrates.
* **Why it should catch a catalogue gap:** the geodetic field is derived from GPS/InSAR and is completely
  independent of geological mapping. A dilational jog with no surface expression cannot be in the
  catalogue by construction.
* **Difference:** the sibling canary measured `geod_shearrate` alone at AUC 0.553 and `geod_dilaterate`
  at 0.563 — weak individually. The *ratio* is a non-linear combination that no repo has tried, and
  tree models can express it but only if the ratio is given as a feature (they cannot divide).
* **Cost:** low.
* **Falsifier:** ratio AUC must exceed both constituents' AUC on the same cells.

### 4. Two-detector concordance gate (magnetic tilt x gravity gradient)
* **Layers:** `tc` (6) with `iso_grav_anom_hg` (18) and `tmi_hg` (3).
* **Physical signature:** the normalised product of two independent potential-field edge detectors; a
  fault that offsets both magnetic and density structure fires in both, whereas a dyke or a lithological
  contact usually fires in one.
* **Why it should catch a catalogue gap:** the failure mode of every single-source lineament extraction is
  false edges, which then consume the dot budget. A concordance gate raises the *ranking* without adding
  candidates — and the sibling record shows ranking, not budget, is what separates 0.24 from 0.28 at
  fixed budget (`evidence/sibling_record.json`).
* **Difference:** siblings used single-source ridges or unions of sources; none used a product gate with
  an explicit false-edge-suppression rationale.
* **Cost:** low-medium.

### 5. Seismicity-tensor alignment (azimuthal anisotropy of earthquake density)
* **Layers:** `ieq_n100a15` (16), `deq_n100a15` (10).
* **Physical signature:** the structure tensor of the earthquake-density field — its *directional
  elongation*, not its magnitude. The layers are published with an explicit azimuth parameter (a = 15
  degrees), so anisotropy is meaningful rather than an artefact.
* **Why it should catch a catalogue gap:** microseismicity aligns along active structures including blind
  ones; alignment persists even where density is low.
* **Difference:** no repo treats the seismicity layers as a tensor field.
* **Cost:** medium (tensor of a sparse, noisy field needs careful smoothing scale selection).
* **Falsifier:** alignment AUC must beat `ieq_n100a15` magnitude alone.

## Validation discipline applied here

The top candidate was not sent to a submission slot on argument alone. The implemented ranking was
scored on the hide-and-recover holdout with the shared exact evaluator, and the leakage canary was run
per feature per holdout mode before any of its numbers were used
(`evidence/model_e1e2.json`). Candidates 1-5 above are ranked, not yet run; each carries an explicit
falsifier so that a negative result is still a deliverable.

## Data that would be needed for anything beyond these five

| Need | Free official source | Obtainable from this sandbox? |
|---|---|---|
| 1 m DEM / LiDAR scarp detection | USGS 3DEP via AWS Open Data, <https://registry.opendata.aws/usgs-lidar/> ; competition `1m_DEM_links.csv` (login) | **No** — the host is not on this sandbox's egress allowlist |
| Full QFaults / INGENIOUS fault lines (vector, with attributes) | USGS QFaults <https://www.usgs.gov/programs/earthquake-hazards/faults> ; INGENIOUS via OpenEI GDR <https://gdr.openei.org/submissions/1391> | **No** — not on the allowlist; only `github.com`, `api.github.com`, `codeload.github.com`, `pypi.org`, `files.pythonhosted.org` are reachable |
| GeoDAWN survey rasters at full resolution | USGS <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> | **No** (same reason); the competition's own resampled 19-band stack is what we verified and use |
| Official DTI worked example / organizer forum thread 11516 | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> | **No** — login-gated. The metric implemented here is transcribed from the published formulas and cross-checked against the reference solution repository and a brute-force oracle (`tests/test_metric.py`) |

Anything requiring those hosts must be run on an unrestricted machine; the pins and scripts here are
written so that a fetched file is sha256-verified before it is trusted.
