# Session-7 DOE GEMS review — 2026-10-11 UTC

**Decision: NOT OK TO SUBMIT — DO NOT SUBMIT.** This is a research/code review in the existing ribbon-width/localization-error lane. No new TIFF, width experiment, promotion-grade holdout, competition submission, or slot selection was performed. The only candidate still under review is
[`gems58-concordance-ribbon-40768-20261011T160514Z.tif`](../downloads/gems58-concordance-ribbon-40768-20261011T160514Z.tif), SHA-256
`f709b6f12d5188e34aa3aed3b83d785b97a232224692dcdfffedaa009dee9d0d` (40,768 positive pixels).

The existing file passes local format checks. That is not portal acceptance. Its recorded final-dot
scan has **83 literal >70% overlap triggers** over the saved **703-raster** public-inventory snapshot;
the separate freshness audit remains **`BLOCKED_NOT_EXHAUSTIVE`**. The exact-candidate qualification
receipt `evidence/ribbon_qualification.json` is absent. Current reportable HOLDOUT-DTI, its
withheld-positive count, and a defensible 95% CI are **NOT MEASURED**.

## Three review passes completed

### Pass 1 — attribution and source review

- Reviewed the source facts and claims recorded in [`docs/SOURCES.md`](../SOURCES.md),
  [`evidence/organizer_confirmed.json`](../../evidence/organizer_confirmed.json), and
  [`registry/sources.csv`](../../registry/sources.csv). Those records distinguish directly fetched
  pages/PDF excerpts from citations, owner-maintained statements, and sources not fetched; this
  report does not claim every linked source was independently fetched in full.
- Confirmed the task is geothermal-indicative fault mapping, not vent detection. The official task
  page describes incomplete and potentially misaligned public fault truth, a pooled distance-weighted
  Tversky index, and an expert-labeled set of new faults. The metric's asymmetric penalties
  (α=0.2, β=0.8) and 300 m triangular support imply a general preference for nearby coverage, but
  they do **not** explain any specific participant's public score.
- Rechecked the public board at approximately `2026-10-11T18:33:10Z` (UTC clock sampled immediately
  after fetching the page text; not a server timestamp). The saved
  [`PUBLIC-LEADERBOARD-SNAPSHOT`](../../evidence/official_leaderboard_observation_20261011_review.json)
  records xiaofanhu rank 1 / 0.4133, DARD rank 9 / 0.3195, and extradr19 rank 23 / 0.2778. The
  dynamic board supplies participant rows, not TIFF hashes or organizer score receipts.
- The requested H33 attribution is not supported: the 0.2778 row belongs to `extradr19`; the
  [GEMSDOE32 owner page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) says
  H33-2-B2 is unscored and labels 0.2747 a projection. No organizer receipt/hash crosswalk links
  H33 to the 0.2778 participant row. We can correct the attribution, but cannot scientifically
  explain why `extradr19` obtained that result without its scored artifact, submission record,
  hidden public subset, and organizer evidence. The exact origin of the H33 misattribution is unknown.

### Pass 2 — protocol and code-path audit

- Found the critical builder defect: `scripts/build_site.py` had an independent legacy `evaluate_gates`
  path. It could display G4/G5 as passing from an old feature AUC and a legacy holdout result, despite
  the current fail-closed `scripts/qualification_gates.py` requiring hash-bound current receipts,
  fresh inventory, pre-placement clearance, a promotion-grade feature-alone canary, and a shared
  buffered holdout with a reportable 95% interval.
- Replaced the builder's gate implementation with a delegation to
  `scripts/qualification_gates.py`. The public pages now show G1 local-format PASS only; G2P/G3/G4/G5
  fail. G2/G5i/G6 are explicitly informational and do not look like required failures or passes.
  `--strict` retains exit 2 while a required gate is open.
- Removed legacy holdout values, block min–max ranges, and legacy canary AUC from the current status
  pages. These results remain in their original evidence receipts for audit, but the site does not
  promote them or quote a numeric candidate HOLDOUT-DTI without the required evaluator/version,
  protocol, withheld-positive count, and defensible 95% CI.
- Corrected the public-board evidence class: leaderboard rows are
  `PUBLIC-LEADERBOARD-SNAPSHOT`, never `ORGANIZER-CONFIRMED` for a local artifact.
- Removed the unsupported assurance that local format checks prove the reported portal `[0,1]`
  rejection cannot occur. The rejection remains unresolved; the repo has no exact portal response
  payload or receipt bound to the candidate hash.
- Updated the active project protocol. The user-specified literal rule supersedes archived
  RATIFIED-UNIQ-v1 reasoning: stop for rank correlation `>0.90` **or** `>70%` of a candidate's dots
  within 3 px of any one witness. Chance correction, saturated witnesses, or alternate statistics do
  not waive a literal trigger. Stale/incomplete inventory is also a stop.

### Pass 3 — research review, status rebuild, and consistency checks

- Re-ranked four genuinely untried **width-conditioning** hypotheses; H58-U1 remains first. The detailed
  register names input layers, physical signatures, possible unmapped-fault route, existing-code
  differences, non-fault mimics, expected uncertainty, cost estimates, data-source requirements, and
  falsifiers. No hypothesis was fitted or scored.
- Regenerated `docs/index.html`, `docs/executive-summary.html`, `docs/submit.html`,
  `docs/evidence.html`, `docs/RUN_CARD.json`, `evidence/ribbon/run_card_final.json`,
  `evidence/session7_review_run_card.json`, and the candidate checks sidecar from the shared evaluator.
- The per-file downloads index remains review-only. No file is approved, no artifact inherits clearance,
  and the only download named “current” is still explicitly **DO NOT SUBMIT**.
- The feature raster is absent locally. No feature-stack download or registry rescan was attempted:
  the known literal candidate stop and stale inventory already prevent a useful experiment, and no
  width candidate is to be emitted before the pre-placement gate.

## Current gate results and evidence

| Gate / evidence | Current result | Interpretation |
|---|---|---|
| G1 — local format preflight | **PASS** for the exact on-disk candidate; emission receipt and separate local audit available | Format/file check only. Not portal acceptance, a score, or submit clearance. |
| G2 — local witness subset | Informational only | Not a substitute for fresh, exhaustive pre-placement and final-dot scans. |
| G2P — pre-placement surface | **FAIL / not cleared** | No current, hash-bound pre-placement receipt exists against a fresh exhaustive inventory. |
| G3 — final-dot uniqueness | **FAIL / literal stop** | Saved scan: 83 triggers, worst literal overlap 1.0000, worst rank correlation 0.2823. The overlap threshold alone stops this file. The saved scan is snapshot-scoped. |
| G4 — feature-alone leakage canary | **FAIL / missing** | No candidate-, feature-, split-, and inventory-bound current canary receipt. No legacy AUC is a clearance. |
| G5 — buffered spatial HOLDOUT-DTI with defensible 95% CI | **FAIL / NOT MEASURED** | No current candidate-bound shared-evaluator result, withheld-positive count, protocol, and reportable physical-cluster interval. |
| Registry freshness | **`BLOCKED_NOT_EXHAUSTIVE`** | Current public trees changed/unrepresented; pinned restoration/inventory is not a complete current audit. |
| Organizer-confirmed score | **None** | No submission receipt/hash crosswalk for any artifact in this repository. |
| Experiments / slots | **0 / 3; 0 slots** | No holdout, candidate emission, upload, or selection in this review. |

The authoritative generated gate list is in [`docs/RUN_CARD.json`](../RUN_CARD.json); the original
scan and audit receipts remain at
[`evidence/ribbon/uniqueness_full_inventory.json`](../../evidence/ribbon/uniqueness_full_inventory.json),
[`evidence/registry_freshness_audit.json`](../../evidence/registry_freshness_audit.json),
and [`evidence/ribbon/file_audit.json`](../../evidence/ribbon/file_audit.json). Do not interpret the
703 scanned paths as the count of a current exhaustive inventory.

## Ranked width hypotheses — brief research summary

These are proposals, not results. “Expected benefit” is qualitative; there are no gain forecasts. The
existing ridge/placement surface stays fixed. A wider ribbon can help only if an existing ridge is
already within the official scoring kernel of an unmapped or mislocated trace. It cannot discover a
fault absent from the ridge surface. Because the local holdout is built from known catalogue faults,
its result would remain a proxy for localization, not direct validation against the competition's
hidden new-fault truth.

| Rank | Hypothesis and layers | Physical mechanism / why it could help nearby unmapped structure | Difference from implemented code | Main uncertainty and named mimics | Cost / data |
|---:|---|---|---|---|---|
| 1 | **H58-U1: relief-conditioned width** — `det_elev`, `det_elev_slope`, fixed topographic ridges | Relief/scarp preservation may change axis localization error; widening only high-error regimes could cover a nearby missed/misaligned trace. | Existing calibration stratifies by family, scale/sign, blocks, and magnitude, not local relief; centerline is unchanged. | High uncertainty and uncertain transfer from mapped to unmapped faults. Drainage, fan fronts, terraces, road cuts, erosional scarps. | ~1–2 engineering hours after prerequisites; existing 19-band stack, no new external data. |
| 2 | **H58-U4: cross-strike profile-shape width** — `tmi_hg`, `iso_grav_anom_slope`, `det_elev_slope` profiles | Broad/asymmetric/multi-lobed response may identify a poorly localized existing axis; width could cover a nearby trace. | Profile FWHM/asymmetry/secondary lobes are not current within-ridge width predictors; no new detector. | High uncertainty: source depth and lithology may mimic the signal. Mafic dikes, contacts, remanent magnetization, drainage edges. | ~2–3 hours; same stack. Verify metadata before preregistration. |
| 3 | **H58-U2: basin-cover context width** — `depth_to_base_surf`, `cond_surf` | Cover thickness/conductivity may attenuate or broaden fault expression; conditional width could cover a nearby concealed/misaligned trace. | Uses context only for width around already-detected ridges, not a new basement/conductivity edge detector. | High uncertainty: regional geology, salinity, alteration, and lithology may be non-fault controls. | ~2–3 hours; same stack. |
| 4 | **H58-U3: centerline-curvature width** — fixed ridge centerline/tangent geometry | Bends, kinks, relays, and intersections may have larger localization error; extra support could reach a nearby omitted segment. | Along-strike centerline curvature is not the Hessian's across-strike curvature and is not used in current width assignment. | Low expected value, high uncertainty. Meandering drainage, curved contacts, road bends, overlapping lineaments. | ~1–2 hours; derived from current ridge field. |

Full hypotheses, prior-art exclusions, sources, and falsifiers:
[`docs/research/hypotheses_new.md`](hypotheses_new.md).

## Preregistered path if blockers clear

1. Refresh the public registry and require `fresh_current_inventory: true` with a hash-bound audit.
2. Freeze one H58-U1 feature definition, relief scale/bins, comparator, budget, and decision rule before
   reading outer-block results. Keep the current ridge surface fixed.
3. Pass the candidate-specific pre-placement surface uniqueness scan under the literal stop rule.
   Stop on any trigger or incomplete inventory.
4. Test every feature alone using the current buffered spatial folds; AUC above 0.90 is a leakage
   warning requiring stop/review. Do not use a combined canary to hide a leaking feature.
5. Use `gems57.evaluate_holdout`, buffered whole-fault segments, visible-only catalogue features,
   pixel-exact visible-fault masking, pooled DTI with α=0.2/β=0.8 and a 300 m triangular kernel.
   Report any result with the evaluator/version, protocol, withheld-positive count, and a defensible
   two-sided 95% interval supported by physical spatial clusters.
6. Only if preregistered results are supportable and all holdout/uniqueness gates pass, emit through
   `gems57.submission_writer`; bind file and decoded-pixel hashes and run final-dot uniqueness.
7. Preserve a negative result. Do not select a slot or upload.

## Trusted sources

- [DrivenData competition problem, metric, and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data / GeoDAWN context](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DOE GEMS Official Rules, September 2026](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN airborne magnetic/radiometric release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DrivenData reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)

See [`docs/SOURCES.md`](../SOURCES.md) for the evidence/source register. Public board rows, owner
projections, local file properties, and historical run cards are not organizer-confirmed artifact
scores.
