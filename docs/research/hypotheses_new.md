# Four genuinely untried ribbon-width hypotheses

**Audit date:** 2026-10-11 UTC. **Status:** proposals only; none has been implemented or measured in
this checkout. **Top candidate:** H58-U1, relief-conditioned width — **NOT VALIDATED**. No holdout
run is authorized while the final-dot uniqueness hard stop, inventory-freshness requirement and
qualification gates remain blocked.

These hypotheses keep the detected ridge surface fixed. They can alter only ribbon support/width
around an existing ridge; they cannot discover a fault where the fixed surface has no nearby ridge.
There are no projected scores or claimed improvements.

## Prior-art audit: what is not “untried”

The ranked list was replaced after searching the current code and evidence, including the legacy
`gems58w` pipeline and shared `gems57` modules. The following ideas are **excluded** from the novel
list:

| Existing idea or measurement | Repository evidence | Why excluded |
|---|---|---|
| Magnetic **and geodetic signed-normal offset / bias** | `scripts/ribbon_run_signed_sigma.py`, `scripts/ribbon_build_submission.py` (`--shift-json`), `evidence/ribbon_v2/signed_sigma.json` | Implemented and measured under legacy `gems58-pooled-hide-v1`; this is not promotion-grade evidence, but it is not untried. The diagnostic includes multiple families, so geodetic signed bias must not be relabelled as novel. |
| Adaptive scalar σ, family/scale/sign strata, and magnitude-bin calibration | `src/gems58w/sigma.py`, `scripts/ribbon_run_adaptive.py`, `evidence/ribbon/adaptive_sigma.json`, `evidence/ribbon/adaptive_arms.json` | Already implemented/measured. The old evaluator/split does not qualify the current candidate. |
| Equal-budget along-strike spacing and ribbon geometry sweeps | `scripts/ribbon_run_equal_budget_v2.py`, `scripts/ribbon_run_geometry_sweep.py`, `evidence/ribbon_v2/` | H58-S2 and related spacing/geometry variants already have code or measurements. |
| Anisotropic error/covariance or broad empirical radial/quantile models | `src/gems57/faultzone.py`, `src/gems57/fit.py`, `src/gems57/damagezone_envelope.py` | Related mechanisms exist elsewhere in this repository and are outside this ribbon-width review. Do not relabel or import them as a new ribbon hypothesis. |
| Cross-scale agreement, new ridge detection, supervised fault detection, or flight-line removal | Prior session proposals and detection scripts | These change the detected surface or research lane, contrary to the fixed-surface ribbon-only rule. |

“Untried” below means no implementation or evaluation of the **specific proposed conditioning variable
in the ribbon-width path** was found in this checkout on the audit date. It is not a claim about
unseen branches or external repositories.

## Ranked summary

Ranking is qualitative expected value per implementation effort, not a score forecast. Every
hypothesis requires training-only fitting, a frozen rule, individual feature-leakage checks, and the
prescribed blocked holdout; all work is currently blocked before experiment by the registry stop.

| Rank | Hypothesis | Existing bands / layers | Physical signature and route to a missed fault | Expected DTI value / uncertainty | Engineering cost | Official data availability / new source |
|---:|---|---|---|---|---|---|
| **1** | **H58-U1: relief-conditioned width for existing topographic ridges** | `det_elev`, `det_elev_slope`; fixed existing topographic ridge centerlines | Relief/scarp preservation may stratify localization error. If a fixed ridge is already near an unmapped or mislocated trace, extra width in a high-error relief regime could cover the offset; it cannot create a ridge where none was detected. | Low–moderate potential; high uncertainty and weak transfer evidence from known catalogue faults to unmapped faults. No numeric forecast. | Low–medium, about 1–2 engineering hours after inputs are available. | Existing 19-band `training_features.tif`; restore its pinned mirror. No new external layer. Official feature/task description and USGS GeoDAWN context linked below. |
| 2 | **H58-U4: cross-strike profile-shape-conditioned width** | Existing `tmi_hg`, `iso_grav_anom_slope`, `det_elev_slope` ridge-source profiles and fixed centerlines | Broad, asymmetric, or multi-lobed cross-strike profiles may mark a poorly localized structural axis; greater width could cover nearby unmapped traces only where the fixed ridge already lies near them. Source depth and non-fault contacts can produce the same signature. | Low–moderate potential; high uncertainty. Profile shape may proxy source depth or lithology rather than axis error. No numeric forecast. | Medium, about 2–3 engineering hours after inputs are available. | Existing 19-band stack only; no new data. Exact channel semantics must be checked against the official stack metadata before preregistration. |
| 3 | **H58-U2: basin-cover / basement-context-conditioned width** | `depth_to_base_surf`, `cond_surf`; widths around already-existing ridges only | Cover thickness/conductivity may change how sharply a fault-related surface expression is localized. Conditional width could help near a concealed/misaligned trace only if an existing ridge is already nearby. | Low–moderate potential; high uncertainty; context may be merely regional geology. No numeric forecast. | Medium, about 2–3 engineering hours after inputs are available. | Existing organizer-described surface-conductivity/depth-to-base bands; no new external layer. Verify band mapping in the restored stack. |
| 4 | **H58-U3: along-strike centerline-curvature-conditioned width** | Curvature/tangent geometry of the fixed Hessian ridge centerlines; no new raster layer | Localization error may rise at bends, relay-like kinks, or intersections. Extra width could cover a nearby omitted/misaligned segment at a detected kink, but cannot discover an absent centerline. | Low potential; high uncertainty; a geometric error-stratum test only. No numeric forecast. | Low–medium, about 1–2 engineering hours after inputs are available. | Derived from the existing ridge field; no new external data. |

All costs are implementation estimates only; they exclude restoring the missing feature stack and the full registry refresh, and they do not authorize running an experiment. The permitted public feature descriptions are in the [DrivenData problem/data pages](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and the survey context is in the [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). None of these sources proves a proposed width regime transfers from mapped catalogue faults to unmapped faults.

**Scope limit shared by all four:** these change only ribbon width around a frozen, already-detected surface. They can help only if a fixed ridge is within the official 300 m scoring kernel of a missed/mislocated trace; they cannot discover a fault where the ridge detector emits nothing. The required local holdout withholds known catalogue segments, so a positive HOLDOUT-DTI is a proxy for localization—not validation against competition's new-fault truth. This transfer uncertainty remains even if all local gates pass.

## H58-U1 — relief-conditioned width (top candidate, not validated)

- **Layers:** `det_elev` (detrended elevation), `det_elev_slope`, plus the fixed topographic ridge
  centerlines already produced by the ribbon pipeline. Compute a preregistered local-relief statistic
  from `det_elev` at a scale fixed before scoring; do not create or threshold a new ridge surface.
- **Physical signature / rationale:** a sharp bedrock scarp or warped terrace can be sharply located,
  while incision, colluvium, erosion, and low-relief basin fill can broaden or shift the surface
  expression. If localization residuals differ by a training-only relief class, allocating width
  conditionally may avoid spending the same support everywhere.
- **Difference from existing code:** the current ribbon calibration uses family, ridge scale/sign,
  blocks, and magnitude strata; it does not use local relief to assign width. This is not the prior
  topographic signed-offset diagnostic and does not change ridge detection or centerline position.
- **Named non-fault mimics:** drainage channels, alluvial-fan fronts, terrace margins, road cuts, and
  erosion can create relief or slope boundaries.
- **Falsifier:** no stable out-of-fold difference in localization-error distribution by the
  preregistered relief class, or a nonpositive paired HOLDOUT-DTI change with a defensible interval.
- **Availability:** the official feature stack supplies `det_elev` and `det_elev_slope`; it is not
  committed as a raw large file. The bridge pin is a mirror-integrity check, not independent proof of
  organizer provenance. Restore and verify it before a future run.

## H58-U2 — basin-cover / basement-context-conditioned width

- **Layers:** `depth_to_base_surf` (depth to basement) and `cond_surf` (subsurface conductivity) as
  width-context variables, combined with a **fixed, already-detected** ridge from any existing band.
- **Physical signature / rationale:** thick basin fill and conductive cover can attenuate or broaden
  the surface expression of a basement fault. At a fixed ridge, the conditional localization-error
  distribution may therefore differ between basin-cover regimes. The hypothesis changes only the
  width assigned around that ridge; it does not add a basement/conductivity edge detector.
- **Difference from existing code:** the ribbon code treats these as feature families/ridge types but
  has no tested within-family width rule stratified by their local values or gradients. Previous
  basement-step or conductivity-lineament detector proposals are deliberately not reused.
- **Named non-fault mimics:** lithologic boundaries, groundwater/salinity changes, geothermal
  alteration unrelated to a mapped fault, and smooth regional basin geometry.
- **Falsifier:** the context strata do not improve out-of-fold error calibration over family/scale/sign
  alone, fail the individual-feature leakage canary, or have nonpositive paired HOLDOUT-DTI.
- **Availability:** both bands are part of the organizer-provided 19-band `training_features.tif`;
  no new external data is needed.

## H58-U3 — along-strike centerline-curvature-conditioned width

- **Layers:** the component centerlines, tangents, and local centerline geometry of the existing
  multiband Hessian ridge field. Use the same fixed ridge surface; do not add or remove centerline
  pixels.
- **Physical signature / rationale:** small bends, segmentation kinks, and relay-like changes in
  strike may be less precisely localized than long straight sections. A preregistered local
  along-strike curvature class could test whether those existing portions merit different ribbon
  support.
- **Difference from existing code:** Hessian transverse curvature is already used to identify a
  ridge; this hypothesis uses **along-strike centerline curvature as an error-conditioning variable**
  after ridge extraction. Existing σ strata do not use this variable. It is not an anisotropic error
  tensor, a strike-offset model, or along-strike dot-spacing optimization.
- **Named non-fault mimics:** meandering drainages, curved lithologic contacts, road bends, and
  intersecting magnetic/gravity lineaments can all create curved ridge centerlines.
- **Falsifier:** curvature classes have indistinguishable out-of-fold localization error, fail an
  individual-feature canary, or produce a nonpositive paired HOLDOUT-DTI change.
- **Availability:** derived from the existing official-stack ridge field; no additional source data
  are required.

## H58-U4 — cross-strike profile-shape-conditioned width

- **Layers:** cross-strike samples from the fixed ridge-source fields `tmi_hg`,
  `iso_grav_anom_slope`, and `det_elev_slope`, evaluated at existing centerlines only. Candidate
  conditioning variables would be normalized profile full-width-at-half-maximum, left/right
  asymmetry, and a preregistered secondary-lobe indicator. The source-band mapping and units must be
  verified from the restored stack metadata before freezing the feature definition.
- **Physical signature / rationale:** a broad or asymmetric magnetic/gravity/terrain response can
  leave the center of a structural edge less precisely localized than a narrow, symmetric profile.
  A conditional increase in width could cover a nearby omitted or displaced fault trace where the
  ridge is already present. It is plausible for concealed structure, but a broad anomaly is not itself
  evidence of a fault.
- **Difference from existing code:** ridge extraction uses Hessian response and existing σ
  calibration uses family, scale, sign, magnitude, and spatial block. The repo does not use the
  *cross-strike profile shape at the detected axis* as an additional within-ridge width predictor.
  The centerline, threshold, feature family, and emitted budget remain fixed; no new edge detector is
  added.
- **Named non-fault mimics:** mafic dikes and lithologic contacts, remanent magnetization,
  source-depth changes, topographic drainage edges, and overlapping non-tectonic anomalies.
- **Expected benefit / uncertainty:** low–moderate potential with high uncertainty. Profile width can
  encode source depth or contact geometry rather than localization error; it must show incremental,
  stable out-of-fold calibration beyond family/scale/sign/magnitude and pass each feature-alone
  leakage canary. No DTI gain is forecast.
- **Implementation cost:** about 2–3 engineering hours after the feature stack and registry are
  available; estimate only. This includes preregistered sampling/normalization and ablation tests, not
  a new source acquisition.
- **Availability / trusted-source requirement:** the named channels are in the repository's expected
  19-band stack definition; the official task page lists the supplied magnetic, gravity, and
  detrended-elevation products. No extra data are proposed. Confirm exact band order/metadata after
  restoring the pinned stack. The [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
  is source context, not a source for score labels.
- **Falsifier:** profile-shape strata do not improve train-only, cross-fitted localization calibration
  after existing strata; the canary exceeds AUC 0.90; the feature leaks; or paired buffered
  HOLDOUT-DTI improvement is nonpositive/uncertain under its prespecified 95% CI.

## Required protocol before any future experiment

The following sequence is **blocked** until the registry gate clears; no holdout was run for these
proposals in this review.

1. Freeze one primary hypothesis, feature definition, bins, candidate budget, comparator, and analysis
   before looking at outer-block scores. Keep the existing ridge surface fixed.
2. Compare the frozen pre-placement surface against the fresh registry. Compare the final dots
   separately. Stop for rank correlation `>0.90` or if `>70%` of candidate dots fall within 3 px of
   any one registry raster. A stale/incomplete inventory is not clearance; no chance-corrected or
   dense-raster exception can override a literal trigger.
3. Run feature-alone leakage tests individually; AUC `>0.90` is a stop pending an independent
   explanation. Fit feature/context bins from visible training faults only.
4. Use buffered whole-fault-segment folds; compute catalogue features from visible faults only and
   mask visible faults pixel-exactly. Use pooled DTI α=0.2, β=0.8, a 300 m triangular kernel,
   `gems57.evaluate_holdout`, and `gems57.submission_writer`.
5. Report a numeric result only as `HOLDOUT-DTI`, naming the evaluator/version, withheld-positive
   count, and a defensible 95% CI. Do not call an owner projection or public participant row
   `ORGANIZER-CONFIRMED`.
6. Stop by three experiments or two hours, and sooner on uniqueness, stale/incomplete inventory,
   leakage, or unsupported/nonpositive results. Do not select a weekly slot or upload. A negative
   result is valid.

**Current disposition:** H58-U1 is the ranked first hypothesis, but it is **not validated**. The
historical session-6 40,768-dot artifact's frozen 703-raster scan recorded 83 literal firings; that is
not a current-inventory clearance. The current session-7 review TIFF has a directly measured 1.0000
overlap with a hash-pinned witness. That literal stop, together with the missing fresh-inventory,
pre-placement and qualification receipts, prohibits a holdout run. Do not waive the stop to obtain a
result.
