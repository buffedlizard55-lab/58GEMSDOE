# Ribbon lane review — 2026-10-11 (no new experiment or upload)

**Decision: NEGATIVE. No new TIFF was emitted.** The user asks for a unique downloadable TIFF,
but also requires an immediate stop on >70% forward dot overlap or rank correlation >0.90, a
surface check before placement, and a complete registry scan. The current review-only TIFF is
an existing independently derived artifact, not a new submission or a verified unique one.
The emitter was tested and refused to create a file (exit 2: qualification receipt missing).
Making cosmetic changes to existing bytes or a zero-field TIFF to claim uniqueness would defeat
both the scientific goal and the stop rule. No weekly slot was used.

## Why 0.2778 is not a verified H33 result

The [official public board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
showed **extradr19** at 0.2778 in the dated observation. It does not publish the filename or hash
of that team's submission. The [GEMSDOE32 H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
marks H33 **UNSCORED** and calls 0.2747 a projection. No hash-bound organizer receipt joins those
sources. Consequently the highest-score explanation in the question is a **misattribution, not an
H33 mechanism demonstrated to beat 0.2778**. See [attribution register](../LEADERBOARD.md) and
[owner-vs-board audit](why-02778.md). The official 2026-10-11 board snapshot showed the actual
public leader at 0.4133 (xiaofanhu); the quoted 0.3195 belonged to DARD at rank 9 in the later
snapshot. Both are *participant rows*, not scores of any TIFF in this project.

## Physical rationale and what this lane cannot establish

The [official problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
target **faults**, not geothermal vents: expert-added unmapped faults supply the initial test labels.
The submission is a 100 m EPSG:32611 single-band float32 grid, finite [0,1] within the footprint,
with null/NaN outside. The DTI uses a 300 m triangular kernel. Across-strike ribbon broadening can
recover a ridge displaced from a fault by 1–3 pixels, but extra dots cost FP and nearby predictions
compete through max-credit. Exact marginal utility must include both ΔTP and ΔFP; more lines do not
universally help. A ridge method cannot discover a fault where the detector has no adjacent ridge.
Independent magnetic/gravity/topographic signatures can also arise from lithologic contacts,
alluvial-fan margins, erosion, road cuts, or survey levelling rather than slip.

The existing H58-X1 cross-family arm was a **historical diagnostic**, not a promotion-grade result:
`evidence/ribbon/concordance_arms.json` gives old pooled DTI 0.043575 vs control 0.040105 on
60,988 withheld positives (gems58w.metric/v1, gems58-pooled-hide-v1); its min/max of four spatial
folds is *not* a 95% confidence interval, and re-deriving the arithmetic with the shared metric
cannot repair its design. No new HOLDOUT-DTI or CI is claimed in this review. The exact values,
sigma tables, and per-class simulated gains belong to the archived receipts, not a new raster.
The top **untried within-lane** idea remains H58-U1 (relief-conditioned ribbon width); U2
(basin-cover context) and U3 (centerline curvature) are ranked, with layers, non-fault mimics,
falsifiers, and costs in [hypotheses_new.md](hypotheses_new.md). They were documented before this
implementation review; none was validated and none authorizes a slot.

## Independent checks and change made

- The primary existing file hashes to `f709b6f12d5188e34aa3aed3b83d785b97a232224692dcdfffedaa009dee9d0d`;
  `scripts/audit_current_tiff.py` re-read it and its ZIP: **10/10 local checks** passed.
  The mask matches the sample, there are **no NaNs inside**, inside values are 0/1, shape
  3730×3292, transform `(100,0,243350,0,-100,4508550)`, CRS EPSG:32611. NaNs *outside*
  match the sample but the reported portal `[0,1]` rejection cannot be resolved without a
  hash-bound portal error; this check is not a submission receipt.
- Saved final-dot scan `evidence/ribbon/uniqueness_full_inventory.json`: 703 indexed witnesses,
  **83 literal overlap firings** and a `stop_required` flag. It is a snapshot, not a current or
  organizer-wide registry. `evidence/registry_freshness_audit.json` states `BLOCKED_NOT_EXHAUSTIVE`.
  Neither zero rank-correlation firings nor file-byte uniqueness negates the 70% overlap stop.
- Site build now places one primary red verdict before the archived gems60 review box, requires
  the current shared-evaluator qualification and fresh registry (G7), and treats the literal
  overlap as a hard stop (G3L). The older diagnostic G5 stays visible but cannot green-light
  the page. A self-declared min/max of four quadrants can no longer masquerade as a 95% CI in
  the shared qualification validator. The public leader's participant row is labelled
  `PUBLIC-LEADERBOARD-SNAPSHOT`, not `ORGANIZER-CONFIRMED`; the disputed H33 value is displayed
  as disputed in the historical fit table.

## Next actions, in order

1. Rebuild a genuinely *current* hash-pinned public witness inventory (including every changed
   repository and this repo), measure both **pre-placement surface** and final-dot similarity in
   the candidate→witness direction, and publish all missing/stale entries. Private submissions
   cannot be inventoried from public GitHub; no global uniqueness claim is possible.
2. Restore the hash-pinned 19-band feature stack via `scripts/fetch_feature_stack.sh` from the
   owner's GitHub bridge (not an independent organizer download). Fit H58-U1 σ strata using
   training-only buffered whole-segment folds and a spatial-cluster bootstrap with defensible
   cluster count. Validate individual-feature AUC; **do not touch a weekly slot** unless a new
   candidate beats a comparable incumbent on the exact pooled DTI with a positive paired CI.
3. Only after clearance, emit through `gems57.submission_writer`, recheck grid/values/footprint
   and decoded hash, and capture the portal acceptance/error plus the exact submitted file hash
   at a separately authorized selector step. The user's previous portal error is unresolved.

No additional external data was added: organizer features are already specified at the
[official problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
The DrivenData data tab requires participant login in this environment; no credential is requested.
The USGS [GeoDAWN source](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
and [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) are background references,
not proof that a new dataset has been obtained or used. All facts above are attributable to these
official sources or to named local receipts; geological mechanisms are hypotheses, not observations
of previously unknown faults.
