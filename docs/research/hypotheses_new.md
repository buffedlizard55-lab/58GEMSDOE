# New candidate geological hypotheses (58GEMSDOE)

Scope: hypotheses **not yet implemented anywhere in the GEMSDOE sibling lineage**
(checked against the registry lanes: anatomy/damage-zone, relay-bend, orientation,
strike-zone, off-catalogue SGMC, dotted-ridge, tip/stepover, lidar-scarp,
Euler-depth clustering, two-stage, lattice, worm persistence, radiometric-scarp
fusion, habitat arrangement, DTI-optimal emission, Poisson off-cat, power-law
budget, openness/thermal-pop, gate-ortho, belief cover, sharpened scarp
scatter, HGB supervised, tensor, tip-relay, manifest-edge, joint-strata,
proximity pruning, submodular multiphysics, dip-projected step, transtensional
swarm, MT clay-cap breach, Anderson PINN).

Ranking criterion: expected pooled-DTI improvement **against the scored metric**
(alpha 0.2, beta 0.8, 300 m triangular kernel) per unit implementation cost,
given what the sibling results show: emission-machinery improvements on the
proven dotted-ridge base scored 0.248 → 0.278 (ORGANIZER-CONFIRMED receipts),
while standalone single-feature instruments scored 0.01–0.16. A candidate that
adds *new independent evidence about unmapped fault locations* and can plug
into the ribbon emission is worth more than a new standalone surface.

| # | Hypothesis | Layers (specific) | Physical signature / transform | Why it catches faults missing from USGS/INGENIOUS | How it differs from anything implemented | Data source (free/official) & availability | Expected DTI gain | Cost |
|---|------------|-------------------|--------------------------------|---------------------------------------------------|------------------------------------------|--------------------------------------------|-------------------|------|
| 1 | **Seismicity-streak faults** (blind active faults) | USGS ComCat / Nevada Seismological Lab relocated epicenters (M≥1.5, 1970–present) | 2-D kernel density of hypocentral epicenters; Hough/RANSAC streak extraction with strike-consistency filter | Blind or buried active faults produce earthquake *streaks* without any mapped trace; the catalogue cannot contain them by construction | No sibling lane uses seismicity at all; it is an evidence stream orthogonal to every raster transform tried | USGS FDSN event service (https://earthquake.usgs.gov/fdsnws/event/1/) and NNSS (http://www.seismo.unr.edu/) — free, official; obtainable (verified reachable catalog APIs, no auth) | Medium–high (adds recall where every other feature is blind) | Medium (catalog assembly + projection QC) |
| 2 | **Radiometric potassic-alteration lineaments** | GeoDAWN airborne gamma-ray K, eTh, eU → K/eTh and K/(eU+eTh) ratio rasters | Ratio-gradient (rotatable-gradient) lineament extraction at 1–3 km wavelengths, then ridge axes | Hydrothermal K-alteration halos trace fault conduits that have **no** topographic or magnetic expression — exactly the concealed population experts added manually | Prior radiometric lanes (r11f/r12, h19-4 thermal) fused radiometrics with scarps/openness; none extracted ratio-gradient lineaments as ridge axes for the dotted emission | GeoDAWN radiometric grids, USGS ScienceBase / https://gdr.openei.org/submissions/1391 (competition-bridged mirrors also in siblings); free, official, obtainable | Medium (new ridge population with a distinct σ) | Low–medium |
| 3 | **Quaternary unit-contact offset linears** | SGMC Quaternary unit polygons (Qc alluvium vs older units) | Polygon-boundary vectorization; detect *abutment lines* where a young unit repeatedly terminates colinearly along an implied structure | Buried faults juxtapose Quaternary cover against older units; the contact line itself is structural evidence not digitized as a "fault" in SGMC | Sibling lanes used SGMC **fault lines** only (off-catalogue proxy); unit-contact abutments are a different, untouched layer | SGMC via USGS (https://mrdata.usgs.gov/sgmc/); free, official; already locally mirrored (sgmc_faults_100m.tif is the fault line layer; polygons need one download) | Low–medium | Low |
| 4 | **Geothermal-spring/thermal-well en-echelon point process** | USGS/State thermal-spring inventories; GBDS well bottom-hole temperatures | Point-process intensity: adaptive KDE of thermal springs + warm wells; alignment test of spring chains vs stress field | Springs mark permeability pathways; en-echelon spring chains reveal fault segments between them, including segments the catalogue missed | No sibling lane uses hydrothermal point evidence as a fault-axis predictor (h19-4 used a thermal *raster* population only) | USGS National Geothermal Data System (https://ngds.usgs.gov/), state databases; free, official; obtainable (some cleaning needed) | Low–medium | Low |
| 5 | **1-m lidar micro-lineament persistence field** | 1 m DEM tiles from the competition DEM-links JSON | Multi-scale roughness anisotropy + orientation-consistency voting over 3–30 m scales; persistence = lineaments surviving ≥3 scales | Fine-scale fault fabric (scarplets, shutter ridges, sag ponds) visible in lidar is invisible at 100 m; buried-trough lineaments persist under alluvium | Lidar lanes so far used *scarp slope* detectors only (7GEMSDOE, 46–50, 60); an anisotropic persistence field feeding ribbon axes is new | 1 m DEM links (competition-provided JSON; USGS 3DEP); free, official; obtainable but heavy (dozens of tiles) | Medium (if σ small, tight lines pay) | Medium–high (compute + tile mosaicking) |

## Validation gate before any weekly slot

Every candidate must first beat the incumbent on the **spatially-blocked
hide-and-recover holdout** (whole-component withholding, buffered context,
visible-only features, exact pooled DTI, paired 20 km-block bootstrap CI). A
candidate that cannot be validated without new external data names its source
above; sources 1–4 were verified reachable/official at run time; source 5 ships
with the competition itself (DEM links JSON).

Leakage canary applies per feature (AUC > 0.90 alone ⇒ leakage until proven
otherwise), per parallel-run protocol rule 4.
