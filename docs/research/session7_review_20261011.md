# Session 7 review — sparse raster audit, literal stop, and next hypotheses

**Review date:** 2026-10-11 UTC. **Verdict:** `negative`. **No experiment, new prediction raster, weekly slot, or upload was made in this review.** The prior session's raster was renamed `review-only` (pixel bytes unchanged), independently audited, and stopped under the literal overlap rule in the user's current protocol.

## 1. Front-door decision

**Do not submit:** [`58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif`](../downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif) · [single-TIFF ZIP](../downloads/58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.zip).

The filename previously contained `unique`; that was not supported by a registry scan. The file is now labeled **REVIEW ONLY — NOT OK TO SUBMIT**. The name change did not alter its pixel bytes.

### Local format audit — not a score and not portal acceptance

The shared `gems57.validate` checks, an independent sample-grid comparison, and a one-TIFF ZIP round trip pass **19/19 LOCAL-FILE-AUDIT checks**. The on-disk file is one-band float32, EPSG:32611, 3730 × 3292, with the sample's CRS, shape and affine transform; values are finite and in [0,1], every positive is exactly 1.0, all values outside the footprint are zero, and no positive pixel overlaps the bridged mapped-fault catalogue. Raster SHA-256 is `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`; decoded-pixel SHA-256 is `21178ff6da8eef1bc286826deb963224a7909c0ee4f318dc4feac7a9e1ff5b15`.

**IR-58-S7-01 — nodata metadata is not identical to the sample.** The TIFF has `nodata=null`; the bridged sample has `nodata=NaN`. Candidate data itself is all finite, including outside the footprint. The competition format text in the supplied brief specifies a single-band GeoTIFF and matching CRS, shape and geotransform; the local audit does not establish the portal's handling of nodata metadata. No candidate-specific portal response or organizer receipt is present. Do not claim this file will be accepted or that it resolves a prior `[0,1]` rejection.

### Literal uniqueness stop — one hash-verified witness is sufficient to stop

A direct current-file measurement used one public-registry witness:

- Witness: `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`.
- **REGISTRY-MEASUREMENT:** SHA-256 `03d619fa75689b48bd3eb4f74c3fa529a9b04c19bd716e15640d910baf3d5a90` matches the pinned registry record and the bytes restored from its public GitHub blob.
- Its positive support covers all **5,167,373** cells in the bridged footprint; the 3-px dilation leaves **0** footprint cells uncovered.
- **REGISTRY-MEASUREMENT:** **1.0000** of this candidate's positive dots fall within 3 px of that witness, exceeding the user's literal **0.70** stop threshold. The candidate is therefore logged as a duplicate/drift stop under the protocol. This is **not** a claim of byte or pixel copying.
- The witness is constant over the footprint, so rank correlation is undefined; the independent overlap trigger is decisive.

This is a direct failing measurement against a prior raster, so the protocol says stop; scanning more rasters cannot reverse the stop. Separately, the current registry freshness record is `BLOCKED_NOT_EXHAUSTIVE`; the older 703-raster scan is complete only for its frozen scope and is not a current-inventory clearance. No complete-current-registry uniqueness claim is made.

**Pre-placement surface:** `NOT MEASURED`. The artifact has no saved pre-placement scalar surface, generating script, or candidate-specific surface receipt. Final-dot failure already stops this artifact; the absence of the surface prevents claiming that the two-phase protocol was completed.

## 2. Holdout, σ and leakage are not results for this artifact

- **HOLDOUT-DTI:** `NOT MEASURED`; evaluator run, withheld-positive count and 95% CI are all absent for this TIFF. No zero score or projection is substituted.
- **σ table:** `NOT MEASURED` for this raster.
- **Simulated gain by class:** `NOT MEASURED`.
- **Feature-alone leakage canary:** `NOT RUN` for this raster.
- **ORGANIZER-CONFIRMED score:** none; no receipt/hash crosswalk exists.

No holdout was run because the literal uniqueness criterion produced a hard stop before any candidate qualification. No experiment slot was touched. Existing holdout tables for earlier rasters are not transferable to this sparse file.

## 3. Highest-score attribution: what can and cannot be answered

The `0.2778` entry in the dated local **PUBLIC-LEADERBOARD-SNAPSHOT** is attached to participant `extradr19` (rank 23 in one saved observation). The owner-maintained GEMSDOE32 page and audit record summarized in this repository label H33-2-B2 **UNSCORED** and label `0.2747` as a projection. No organizer receipt, submission ID, or hash crosswalk connects H33-2-B2 to the `extradr19` row. Therefore the claim that the H33 TIFF scored `0.2778` is **unsubstantiated**; its cause cannot be inferred from the public participant score.

The repository's 2026-10-11 public-board observations recorded a higher row at **0.4133** and a `0.3195` row below it. The board is dynamic and same-day rank observations differ. This session did not retrieve a fresh DrivenData page, so those figures are dated snapshots, not a claim about today's live board and not scores for any TIFF here. See [`LEADERBOARD.md`](../LEADERBOARD.md), [`why-02778.md`](why-02778.md), and the dated records under `evidence/` in the repository.

**Why did the actual `extradr19` submission score 0.2778? Unknown from the available records.** A score alone does not identify its TIFF, number/placement of predictions, feature pipeline, or validation path. The DTI form in the competition materials weights false negatives more heavily than false positives (β=0.8 versus α=0.2), with spatial credit from the kernel; this explains why broad coverage can matter in principle, not what `extradr19` did. The hidden evaluation faults, exact submitted file, and hash-bound organizer receipt are needed for a causal account.

**Can this repo claim a score above 0.2778 or 0.3195? No.** There is no organizer score for this artifact and no valid holdout result for it. Neither a raster format pass nor a high-scoring public leaderboard row predicts its score. No score projection is reported.

## 4. Three within-lane hypotheses ranked before further implementation

These are proposals for ribbon-width calibration only. They keep an existing ridge surface fixed; none can discover a fault that the ridge detector entirely missed. Their rationale for an uncatalogued fault is conditional: a missing catalogue trace may still have a nearby existing topographic or geophysical ridge, and the hypothesis tests whether the location error around such ridges is condition-dependent. Catalogue holdout estimates localization on known segments; its transfer to genuinely uncatalogued faults remains uncertain.

| Rank | Hypothesis and layers | Physical signature / why it might help on an uncatalogued fault | Difference from implemented work | Relative expected DTI benefit (qualitative, not a projection) | Cost | New external data? |
|---:|---|---|---|---|---|---|
| 1 | **H58-U1 relief-conditioned σ:** `det_elev`, `det_elev_slope`, local relief around already-detected topographic ridge centerlines | Bedrock scarps may be sharply located while erosion, colluvium and low-relief basin fill broaden or displace the surface expression. If a not-yet-catalogued fault already produces a ridge, a relief-conditioned offset distribution could place dots nearer its trace. | Existing calibration stratifies by block, feature resolution/ridge type and magnitude; no tested rule conditions ribbon width on local relief. Ridge detection and centerline stay fixed. | Highest of these three, but only low-to-moderate potential with high uncertainty; no numeric DTI estimate. | Low–medium, roughly 1–2 engineering hours after gates clear. | No. The required bands are in the pinned 19-band stack. |
| 2 | **H58-U2 basin-cover-conditioned σ:** `depth_to_base_surf`, `cond_surf` as width context around fixed existing ridges | Thick sedimentary cover or conductive basin fill may attenuate or broaden a fault's surface expression. This could widen the ribbon for an uncatalogued fault only where an existing ridge is already present. | Prior basement/conductivity detector ideas change the detection surface and are not this test. This proposal only conditions width, which current ribbon calibration does not test. | Low-to-moderate potential; high uncertainty and risk of learning regional geology rather than localization error. | Medium, roughly 2–3 engineering hours after gates clear. | No new third-party layer. The context bands are in the pinned stack. |
| 3 | **H58-U3 along-strike-curvature σ:** centerline geometry/tangents from the existing Hessian ridge field | Bends, relay-like kinks and intersections may have larger cross-strike localization error. A hidden fault can benefit only if its ridge is already in the fixed field. | Hessian transverse curvature is used in ridge detection; the untried variable is along-strike centerline curvature used only after extraction. No centerline pixels are added or removed. | Low potential, high uncertainty; inexpensive falsification. | Low–medium, roughly 1–2 engineering hours after gates clear. | No; derived from the cached stack and existing ridge geometry. |

Prior-art audit and falsifiers are in [`hypotheses_new.md`](hypotheses_new.md). Ranking is qualitative and is not a score forecast. These hypotheses are not implemented or validated. No experiment should start under the active hard stop.

### Can the top proposal be validated now?

Not under the current protocol. The feature stack is locally available and its five bridge parts plus whole-file SHA-256 match the owner-maintained GitHub manifest (`evidence/feature_stack_restore_20261011.json`). That proves mirror integrity, not organizer provenance. There is no need for new external geology data for H58-U1. However, the current raw overlap rule has an observed universal prior blocker for every nonempty in-footprint emission, so the stopping rule prevents using holdout experiments to qualify a submission. The official competition data tab remains the authoritative manual source if independent organizer provenance is required; it is login-gated in the local project record.

## 5. Repository review findings and actions

1. **The existing 15k TIFF was not actually uniqueness-filtered.** Its own prior run card said `NOT SCREENED`, but several top-level docs claimed “unique,” “uniqueness-filtered,” or expected a PASS. Those claims have been removed or marked superseded.
2. **The downloaded TIFF was not generated by a reproducible in-repo emitter.** No source script or pre-placement surface was found. Do not attribute it to a measured adaptive-σ pipeline.
3. **The download index was not yet regenerated for the renamed artifact.** `scripts/build_downloads_index.py` now renders every TIFF/ZIP separately; at the session-7 review it listed 21 files and labeled the sparse TIFF/ZIP review-only with the measured 1.0000 literal-overlap failure. A later base-branch update added a separate ML-named TIFF/ZIP; the current index lists 23 files and labels those additional files review-only because they were not evaluated or qualified in this review.
4. **The score explanation had overclaimed cause.** The status-page generator previously said the portal's `[0,1]` error was caused by nonfinite/out-of-range values inside the footprint. No hash-bound portal response proved that cause. The generated submission instructions now state the cause is unknown and treat the local all-finite policy as a precaution only.
5. **The previous RATIFIED-UNIQ-v1 resolution is historical for this prompt.** This review follows the current user's unqualified literal rule: rank correlation >0.90 or >70% of candidate dots within 3 px is a stop. The chance-corrected interpretation is not used to clear a file here.
6. **The current status pages present the latest TIFF with a red banner and direct review-only downloads.** `scripts/build_session7_pages.py` replaced stale front-page prose; the download index labels each artifact. A filename or download button is not permission to upload it.

## 6. Official sources for manual review

The links below are the official/primary sources registered in [`SOURCES.md`](../SOURCES.md). The sandbox did not refresh DrivenData, USGS or PDF pages during this review; do not interpret a listed link as a fresh fetch.

- [DrivenData competition problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition About page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData official data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login may be required.
- [Official competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — dynamic; check directly before relying on ranks.
- [USGS GeoDAWN magnetic and radiometric survey data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP program](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [EPSG:32611](https://epsg.io/32611)

## Run card

The machine-readable run card is [`evidence/58gemsdoe_unique_ribbon/run_card.json`](../../evidence/58gemsdoe_unique_ribbon/run_card.json); the artifact audit is [`evidence/58gemsdoe_unique_ribbon/audit.json`](../../evidence/58gemsdoe_unique_ribbon/audit.json). Both preserve `verdict: negative`, `slots_used: 0`, the directly measured overlap stop, and `HOLDOUT-DTI: NOT MEASURED`.
