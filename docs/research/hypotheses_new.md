# Three genuinely untried ribbon-width hypotheses

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

| Rank | Hypothesis | Existing bands / layers | Physical signature | Expected value / uncertainty | Engineering cost | Official data availability |
|---:|---|---|---|---|---|---|
| **1** | **H58-U1: relief-conditioned width for existing topographic ridges** | `det_elev`, `det_elev_slope`; existing topographic ridge centerlines | Scarp preservation and erosion vary with local relief; the same ridge detector may have different localization error on sharp bedrock scarps versus low-relief basin fill. | Low–moderate potential; high uncertainty. It is the simplest direct test of a plausible within-family error regime. | Low–medium, about 1–2 engineering hours. | Both bands are in the organizer-provided 19-band `training_features.tif`; local use requires restoring the pinned stack. |
| 2 | **H58-U2: basin-cover / basement-context-conditioned width** | `depth_to_base_surf`, `cond_surf`; widths around already-existing ridges (no new ridge detection) | Thick or laterally changing basin fill and conductivity can obscure, broaden, or displace a surface expression relative to a subsurface structural edge. | Low–moderate potential; high uncertainty. The context may be predictive of error or merely regional geology. | Medium, about 2–3 engineering hours. | Both bands are in the organizer-provided 19-band stack; no external layer is required. |
| 3 | **H58-U3: along-strike centerline-curvature-conditioned width** | Centerline geometry of the existing Hessian ridge field from the official 19-band stack; no new feature raster | Localization and segmentation error may rise at bends, relay-like kinks, and line intersections, even after controlling for band, scale, sign, and magnitude. | Low potential; high uncertainty. It is a geometric error-stratum test, not a detector. | Low–medium, about 1–2 engineering hours. | Derived from the existing official-stack ridge field; no additional data required. |

All costs are implementation estimates only; they do not authorize running an experiment.

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
existing 83 literal final-dot firings and the missing fresh-inventory / pre-placement / qualification
receipts prohibit the holdout run. Do not waive the stop to obtain a result.
