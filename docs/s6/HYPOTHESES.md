# Session 6 — candidate hypotheses, ranked before measurement

Every hypothesis below names the layer(s), the physical signature, why it should catch a
fault that is **missing** from the USGS/INGENIOUS catalogue rather than one already in it,
and how it differs from what this repository already implements. Ranking is by expected DTI
improvement per unit of implementation cost, *before* any measurement.

## Why the catalogue is incomplete here (the physical setting)

The GeoDAWN area sits in the northern Walker Lane / western Great Basin: a broad zone of
incipient dextral transform faulting superimposed on Basin-and-Range extension. Faults there
are young, distributed, low-slip-rate, and many are **buried** — the USGS release for this
survey states it directly:

> "Most faults in the GeoDAWN region of Nevada are more subtle, and many are hidden below the
> surface, requiring geophysical data to detect."
> — [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

The competition's own problem page repeats the consequence: the public fault set "is known
that this set of faults is not complete and may even contain some inaccurate data", and the
test set is faults that experts found **outside** it
([page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).
So the target class is: *real structures that a pre-lidar, 1:250 k-scale compilation missed*.
Three mechanisms produce that class, and each maps to a different measurable signature:

1. **buried / basin-margin faults** with no scarp — visible only as a step in the basement
   surface or a gravity/magnetic lineament crossing alluvium;
2. **short, low-slip-rate scarps** below the compilation's length threshold — visible only in
   high-resolution topography;
3. **seismically active structures with no geomorphic expression at all** — visible only as
   microseismicity lineations.

---

## H1 — 1 m lidar scarp detection from the organizer's own DEM links  ★ highest expected value

* **Layers.** `1m_DEM_links.csv` from the competition data tab (1 m DEM tiles, USGS 3DEP /
  GeoDAWN coordinated lidar), resampled to the 100 m competition grid as scarp-normal
  curvature, slope asymmetry and "surface roughness" rasters. The competition ships **only the
  links**; the tiles themselves are not in this repository.
* **Physical signature.** A Quaternary fault scarp is a sub-metre to few-metre vertical step in
  the ground surface. At 1 m posting it appears as a narrow, continuous band of high
  across-strike curvature whose sign is constant along strike, plus a characteristic
  slope-asymmetry (the up-thrown block's hillslopes differ from the down-thrown block's).
* **Why it catches *missing* faults.** This is the single most important point in the whole
  project: the experts who produced the test labels are fracture/fault mappers working from
  high-resolution topography, and the USGS Quaternary compilation for much of Nevada predates
  lidar. A structure invisible at 1:250 k is routinely obvious at 1 m. Every other hypothesis
  below is a *proxy* for what the lidar shows directly.
* **Difference from this repository.** No DEM-derived raster exists here at all. The delivered
  19-band stack contains only a 100 m `det_elev` / `det_elev_slope`, which cannot resolve a
  metre-scale scarp. This lane has never used an external raster except
  `data/external/sgmc_faults_100m.tif`.
* **Cost / blocker.** High. The tiles are hundreds of GB. **Specific free official source:**
  the competition's own `1m_DEM_links.csv` (data tab,
  [drivendata.org/.../data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/))
  which points at USGS-hosted 3DEP/lidar delivery (catalogued through
  [ScienceBase item 657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7)).
  **Not obtainable from this sandbox**: outbound egress is limited to `github.com`,
  `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`,
  `files.pythonhosted.org`. This is a real blocker and the reason H1 is not measured below.

## H2 — Basement-step (buried range-front) edges from `depth_to_base_surf` + `iso_grav_anom`

* **Layers.** `depth_to_base_surf` (depth to basement / sedimentary-cover thickness) and
  `iso_grav_anom` (isostatic residual gravity), plus their horizontal gradients.
* **Physical signature.** A buried normal fault offsets the basement surface, producing a
  *monoclinal step* — an asymmetric edge, not a symmetric ridge. The right operator is
  therefore a **step/asymmetry detector** (first derivative with a sign-consistent maximum,
  i.e. an odd-symmetric edge filter), not the even-symmetric Hessian ridge detector this
  repository already runs.
* **Why it catches *missing* faults.** Buried basin-margin faults are precisely the population
  a surface-scarps compilation cannot map. Gravity and the basement depth see them through the
  alluvium.
* **Difference from this repository.** `gems58w.ridges` computes the Hessian eigenvalue
  **magnitude difference** `2*min(|tr|/2, disc)` — an even-symmetric, sign-blind curvature
  measure. A step detector is odd-symmetric and sign-sensitive. Same bands, different operator,
  different target population.
* **Cost.** Low: both bands are already local; the operator is a 10-line change.

## H3 — Geodetic strain-couplet classification (`geod_2ndinv`, `geod_shearrate`, `geod_dilaterate`)

* **Layers.** The three geodetic (GNSS/InSAR-derived) strain-rate bands.
* **Physical signature.** Active faults localize strain. A strike-slip fault produces **shear
  with little volume change**; a normal fault produces **dilatation**. The ratio
  `shear / (|dilatation| + eps)` is therefore a *fault-style discriminant* and the second
  invariant `geod_2ndinv` a *localizer*. Using the couplet (localize on 2nd-invariant ridges,
  then keep only where the style ratio is self-consistent along strike) is a two-stage test.
* **Why it catches *missing* faults.** Geodetic strain sees currently-loading structures
  regardless of whether they have a mapped scarp; a young fault that has not yet accumulated a
  scarp still concentrates strain.
* **Difference from this repository.** The geodetic bands are currently entries in the
  ridge-field family list and nothing more (`gems58w.features.FAMILIES["geodetic"]`); no
  ratio/couplet test exists.
* **Cost.** Very low.

## H4 — Microseismicity lineaments (`ieq_n100a15`, `deq_n100a15`)

* **Layers.** The two earthquake bands (density/distance kernels, n = 100 km, 15° azimuth).
* **Physical signature.** Relocated earthquake catalogues in the Walker Lane form narrow,
  persistent lineations that mark active faults with no surface expression.
* **Why it catches *missing* faults.** Directly targets mechanism (3) above.
* **Measured support (this session, `evidence/s6/canary.json`):** these two bands have the
  **highest single-feature AUC of all 19 bands** on the buffered hide-and-recover holdout —
  `ieq_n100a15` **0.6064**, `deq_n100a15` **0.5884**, against a 0.90 leakage bar. They are the
  most informative single layers available locally, and they are *not* the catalogue, so they
  are exactly the "sees something the map does not" signal we want.
* **Difference from this repository.** Present as ridge bands; never used as the primary
  detector or as a gate.
* **Cost.** Very low.

## H5 — Conductivity-surface / fluid-pathway anomalies (`cond_surf`)

* **Layers.** `cond_surf` (electrical conductivity of the subsurface) and
  `depth_to_base_surf`.
* **Physical signature.** Faults that host geothermal circulation produce clay alteration and
  saline fluid along the damage zone → elevated conductivity linear anomalies.
* **Why it catches *missing* faults.** Geothermally active faults are over-represented in the
  expert label set (the whole competition is a geothermal exploration prize), and alteration
  is not a mapping criterion for a Quaternary fault compilation.
* **Measured support:** weak. `cond_surf` AUC **0.4690** — indistinguishable from chance on
  the holdout; mean percentile at the dots of the 0.2376–0.2778 registry rasters is 0.476,
  i.e. *below* the footprint median.
* **Cost.** Very low, expected value low. Ranked last.

---

## Ranking (expected DTI improvement / implementation cost)

| # | Hypothesis | Expected DTI gain | Cost | Measured this session |
|---|---|---|---|---|
| H1 | 1 m lidar scarps | **high** (targets the label-generating process directly) | high — **blocked, needs DEM download** | no |
| H4 | seismicity lineaments | moderate | very low | partial — AUC only |
| H2 | basement-step edges | moderate | low | no |
| H3 | geodetic strain couplet | low–moderate | very low | no |
| H5 | conductivity/alteration | low | very low | partial — AUC only (negative) |

## What was actually measured instead, and why

The lane protocol for this session fixes the detector (multi-family / multi-scale Hessian
ridges) and asks only for the **emission geometry** matched to the measured localisation error.
H2–H5 would change the detector, which is a different lane. They are written down here with
their sources so the next session can pick them up, and H1 is flagged as the one idea that
addresses the label-generating process rather than a proxy for it.

### The detector-side finding that dominates everything else

Measured this session on the shared buffered hide-and-recover holdout
(`evidence/s6/geom.json`):

* **random 38,000-dot control: HOLDOUT-DTI 0.052737**;
* the multi-family / multi-scale Hessian ridge field at the same 38,000-dot budget:
  **HOLDOUT-DTI 0.044208, weighted coverage 0.0577, credit per dot 0.0231.**

The ridge detector is **below** a spatially uniform random control on this instrument. That is
the honest headline of session 6 and it is a property of the *instrument* as much as of the
detector: the holdout withholds **catalogue** faults, while the leaderboard scores **new,
off-catalogue** faults, and the reverse-engineering in
[`LIVE_CALIBRATION.md`](LIVE_CALIBRATION.md) shows the two are not the same population
(higher-scoring registry rasters are systematically *farther* from the catalogue, Spearman
+0.73 over 12 files). The geometry conclusions below are still valid — they are measured
*within* one detector, where the catalogue-distance bias cancels — but no detector ranking
from this holdout may be carried to the leaderboard.
