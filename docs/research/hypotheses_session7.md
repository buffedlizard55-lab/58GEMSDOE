# Session-7 candidate hypotheses — generated before implementation (2026-10-11 UTC)

**Protocol compliance.** This list was written *before* any session-7 experiment ran, as the
standing prompt requires. Every row names the layer(s), the physical signature (edge / curvature
transform), why the signature should catch a fault **missing from the USGS/INGENIOUS catalogue**
rather than one already in it, and how it differs from anything implemented in this repository
(including `src/gems57`, `src/gems58`, `src/gems58w`, `src/gems59`, `src/gems60`) and from every
public attempt recorded in `registry/submissions_seen.csv` and the GEMSDOE-family result ledgers.
Ranked by expected HOLDOUT-DTI improvement per unit of implementation cost. **No number in this
document is a score.** Validation happens only on the spatially-blocked hide-and-recover holdout,
and only the top candidate is run within this session's 3-experiment budget.

**Official layers used below** are the organizer-provided 19 bands of `training_features.tif`
(listed verbatim on the DrivenData problem description,
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ , "Provided features"):
surface conductivity and depth to conductive base surface; detrended elevation and its slope;
dilatation rate, shear strain rate, second invariant of strain rate; isostatic gravity anomaly and
its slope; reduced-to-pole magnetic anomaly, total magnetic intensity, vertical and horizontal
slope of TMI, top-of-crustal magnetic source depth estimate; density of earthquakes. Band-name →
layer mapping is read from the file's own band descriptions (`src/gems58w/features.py`), not inferred.

## Why the current public plateau exists (context for the ranking)

Across the GEMSDOE-family ledgers (~40 public attempts), one geometry family dominates the top of
the *own-reported* band: dotted thinning of a Hessian-ridge structural field at 2–3 px spacing
(`d2-8` / `d2-8`-derived), ~44k dots, zero dots on the mapped catalogue, owner-reported 0.2600–0.2778
(`GEMSDOE25 dotted-h19-5-d2-8` 0.2600; `GEMSDOE28 h27-4-solo-d28` 0.2708; `GEMSDOE32 H33-2-B2`
"projected 0.2747", the 0.2778 board row is **not** hash-bound to that file — see
`docs/research/why-02778.md`). Everything outside that family scores lower. The mechanism is
settled (see `docs/research/why-the-score-and-how-to-beat-it.md`): the metric pays at most one unit
of cover per truth pixel, so thick surfaces waste FP mass; dots at spacing ≈ the 3-px kernel radius
keep cover while cutting mass; the initial-round truth is *new* faults only, so catalogue-adjacent
mass is almost pure FP. What the plateau family cannot do is put mass where **its own ridge surface
has no ridge** — its recall is capped by the Hessian-ridge detector built from pooled families.

## Ranked candidates

| Rank | Hypothesis | Layers | Physical signature (transform) | Why it catches catalogue-*missing* faults | Why it is not already in this repo | Expected Δ vs holdout best | Cost |
|---:|---|---|---|---|---|---|---|
| **1** | **H7-A: deep-structure step-edge ribbons.** Emit the lane's σ-adaptive parallel dotted lines on **step edges** (first-derivative maxima) of the subsurface structure surfaces, not Hessian ridges of raw bands. | `depth_to_base_surf`, `cond_surf` (subsurface family); `tc` (top-of-crustal magnetic source depth) as a corroborating family | Canny-style step-edge transform: gradient-magnitude maxima after Gaussian scale-mixture (σ_s ∈ {1.5, 3.0}), thinned by non-maximum suppression along the gradient azimuth. A fault is a *step* in the depth-to-conductive-base / depth-to-magnetic-source surfaces: the juxtaposition of basin fill against basement is a first-derivative edge; a Hessian ridge of the raw surface peaks at the step *corner*, one to two pixels off the structure itself | The USGS/INGENIOUS catalogue is compiled from **surface traces** (airphoto/DEM lineaments and mapped Quaternary offsets). Blind faults under basin fill have no surface trace to map but *do* displace the conductive-base and magnetic-basement surfaces — the exact target the sponsor's experts labelled as "new faults" for the test set. A step-edge detector on those surfaces is blind to the catalogue's content by construction | `src/gems58w/ridges.py` extracts **2nd-derivative Hessian ridges of raw bands** (the `subsurface` family is pooled into the same ridge surface as everything else); no module computes a first-derivative step-edge surface, and no submission in this repository emits from one. `gems60.convergence` pooled four Hessian families — not edges. The legacy `allocation.py` is archived as *not* an exact-metric rule and was never run on edge surfaces | High (best available uncapped recall lever) | Medium (one afternoon: `edges.py` + wiring) |
| **2** | **H7-B: relief-conditioned ribbon width (registered H58-U1, folded into the mandated σ(x) fit).** | `det_elev`, `det_elev_slope` as a *conditioning* variable only; no new ridge surface | Local relief (IQR of `det_elev` in a 21-px window) re-stratifies the localization-error scale: sharp bedrock scarps locate within <0.5 px (single tight line), low-relief basin fill carries 2–3 px error (±σ ribbon) | Indirect: corrects *placement* of every emitted line, the lever the lane brief says pays ("placement within about one pixel is what pays") | Registered in `docs/research/hypotheses_new.md` as **untried** (the current σ table uses family × scale × sign × block only) | Low–moderate | Low |
| **3** | **H7-C: registry-gap complement selection inside the lane's pattern choice.** | Same surfaces as H7-A/H7-B; adds the byte-verified registry witness set as a *selection* input | For ties among patterns with similar exact-metric U, prefer the offset/segment whose dots fall where **no earlier raster has dots** (forward 3-px overlap cap with margin under the 0.70 stop) | Where ~50 independent methods all fail to fire but a weak deep edge exists, an unmapped fault is least contested; it is also the only in-lane way to clear the standing uniqueness gate, which currently stops every nonempty emission | `gems58w.uniqueness` / `chance_corrected_uniqueness.py` are *screens* (post-hoc gates); no emission path has ever consumed the witness set before placement | Low (DTI) / decisive (uniqueness) | Medium |
| **4** | **H7-D: kinematic dilatation-hinge tips.** | `geod_dilaterate`, `geod_shearrate`, `geod_2ndinv`, `det_elev_slope` | Positive-dilatation extrema (fault-tip extension, releasing bends) intersected with detrended-elevation curvature; emit ribbons along the strain ridge through the hinge | Young Walker-Lane faults hosting geothermal systems are kinematically expressed in the strain-rate field where their geomorphic trace is eroded or buried; the catalogue is geomorphic, not kinematic | `h20-1 sarnnpu … wingcrack` (0.1890, another repo) used tilt/wing-crack physics; `h16-1 topo-geophys-baseline` pooled families. No repo emission gates on dilatation-sign *extrema as fault tips* with exact-U ribbons | Moderate | Medium |
| **5** | **H7-E: microseismic lineament shadows ∩ gravity-slope concordance.** | `deq_n100a15`, `ieq_n100a15`, `iso_grav_anom_slope` | Anisotropic lineation filter (structure-tensor coherence) on the earthquake-density bands; keep lineations collinear with gravity-slope ridges | Microseismicity outlines buried active faults, including ones with no mapped geomorphic expression | `h18-3a topo-geophys-x-complexity-prior` (0.0976, another repo) used a complexity prior; `h8-euler-lineament-depthcluster` used Euler depths. No repo emission uses seismicity-band lineations as the primary surface | Low–moderate (mimic risk high) | High |

**Named non-fault mimics (for the run card of the chosen candidate).**
H7-A: lithologic contacts (graben fill pinch-outs), dike swarms, alteration fronts around extinct
systems, and the edge of the survey footprint itself. These produce step edges in the conductive-base
and magnetic-source-depth surfaces with no fault. They are the principal FP risk and the reason the
exact-metric U rule (α·DTI₀ break-even) must decide per segment instead of emitting on every edge.

**Falsifiers (preregistered).**
- H7-A is falsified for promotion if cross-fitted HOLDOUT-DTI does not beat the incumbent arm at
  matched dot budget on ≥ 3 of 4 blocks with a paired 95 % CI that excludes 0 on the pooled delta,
  or if any single feature surface scores AUC ≥ 0.90 on the leakage canary (leakage until proven
  otherwise).
- H7-B is falsified if the out-of-fold localization-error distributions do not differ across the
  preregistered relief classes (21-px IQR terciles).

**Free official sources used (no new external data required).**
All layers above are organizer-provided bands of `training_features.tif` (DrivenData data tab,
login-gated; byte-identical mirror pinned at
https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/data/bridge/manifest.json , sha256
`4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`). No candidate needs new
external data; H7-E would benefit from a free USGS ComCat epicentre export (not required, and the
sandbox cannot reach usgs.gov — therefore H7-E is **not** proposed as viable for this session).

**Decision (recorded before the run):** implement and validate **H7-A** (with H7-B as the
conditioning variable inside the σ table and H7-C as the uniqueness-constrained tie-break in
pattern selection). Budget: 3 experiments (EXP-1 σ+canary, EXP-2 exact-U pattern selection +
cross-fitted holdout, EXP-3 emission + validators + uniqueness), then one run card.
