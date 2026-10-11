# Standing project prompt — 58GEMSDOE

Read this file, `README.md`, and `REMAINING_WORK.md` at the start of each session. This prompt is the operating contract; when an unconditional request to produce a TIFF conflicts with a required no-go gate, preserve the gate, publish the negative decision, and do not manufacture a false clearance.

## Mission and scope

Work on the DOE GEMS Prize Challenge (DrivenData competition 306), whose target is geological faults indicative of geothermal resources—not geothermal vents themselves. The strategic goal is to maximize the probability of winning and own the outcome. This checkout's lane is **ribbon width calibrated to measured localization error**. Do not switch to detection-model, alternate-feature, or submission-slot lanes.

A unique, downloadable GeoTIFF is the goal, but **uniqueness and validation are gates, not labels**. A TIFF must be prominently marked **NOT OK TO SUBMIT — DO NOT SUBMIT** unless every required holdout, pre-placement surface, final-dot, inventory, format, and validation gate passes. Never copy a prior submission except for learning. Never select or use a weekly slot during research.

## Evidence labels and score attribution

- A model result is reportable only as **HOLDOUT-DTI**, with the shared evaluator version, withheld-positive count, protocol, and defensible 95% CI.
- A competition score is **ORGANIZER-CONFIRMED** only when tied to the exact artifact by an organizer submission receipt/hash crosswalk. A live public-board row may be recorded separately as a dated **PUBLIC-LEADERBOARD SNAPSHOT**, but never attributed to a TIFF without that crosswalk.
- A projection, local proxy, raster property, format preflight, or public leaderboard row is not a score for this repository's TIFF.
- As observed on the official public leaderboard on 2026-10-11 UTC: xiaofanhu was rank 1 at 0.4133; DARD was rank 8 at 0.3195; extradr19 was rank 23 at 0.2778. The 0.2778 row is not evidence for the GEMSDOE32 H33 TIFF. The current GEMSDOE32 owner-maintained page says that artifact has **no organizer score** and calls 0.2747 a model projection. None of these rows supplies a file hash/receipt for that artifact. Board ranks are dynamic; use `docs/LEADERBOARD.md` for the dated record.

## Current user-brief clarification (2026-10-11)

The latest instruction states the literal stop explicitly: **if >70% of our dots fall within
3 px of one registry raster, log a duplicate and stop**, even if that witness is dense.
For eligibility, this literal check is a mandatory hard stop alongside the previously ratified
chance-corrected reading. The historical RATIFIED-UNIQ-v1 rule below and its rationale stay
published for audit, but cannot waive the current literal requirement. With plane-filling
witnesses in the saved inventory this may prevent clearing every nonempty raster; do not
misrepresent an impossible clearance or emit merely to produce a downloadable file.

## PARALLEL-RUN PROTOCOL — mandatory

1. **Lane and uniqueness gates (historical RATIFIED-UNIQ-v1, ratified 2026-10-11, session 5 — IR-58-UNIQ-07; literal hard stop reinstated in current brief).** Compare the candidate placement surface before emission and the final dots against the registry. Stop and record a duplicate if rank correlation is greater than 0.90, if dot-set Jaccard exceeds 0.50, if bytes or decoded pixels are identical to a witness, if the scan is incomplete/stale, or if an overlap firing is *informative*: literal forward 3 px overlap above 0.70 against a witness whose chance-level expectation E is below 0.70 (rule A), or chance-corrected lift `(O − E)/(1 − E)` above 0.50 against any witness whose E is below 0.99 (rule B; as E → 1 the lift degenerates to ~1.0 for any nonempty candidate, the same saturation rationale as `gems57.uniqueness.SATURATED_E`). The literal reading (raw 70% rule against every witness, including those whose 3 px dilation covers the whole footprint and therefore fire on every nonempty candidate) is now a **mandatory additional hard stop**. It must still be computed and published beside the ratified reading — never deleted or silently down-weighted. Rationale: a witness with E = 1 fires on every nonempty candidate, so the raw rule has zero discriminating power for lane drift; the lift form reduces to the literal 70% rule exactly when E = 0.
2. **Reuse shared tools.** Reuse the cached feature stack, `gems57.evaluate_holdout`, and `gems57.submission_writer`. Do not create or use a private scoring/evaluation/writer fork. If a shared tool is wrong, fix the shared implementation and tests once. Holdout must withhold buffered whole fault segments, derive catalogue-based features only from visible faults, mask visible faults pixel-exactly, and compute pooled DTI using α=0.2, β=0.8 and the 300 m triangular kernel.
3. **Metric-aware width calibration.** Measure localization error by spatial block, feature resolution, and ridge type on training-only blocks. Compare the placement surface before emission and final dots to registry rasters. Choose ribbon width/offsets only with exact max-credit metric changes, including interactions and redundant predictions. For a pattern change use
   `U = (1 − αs)·ΔTP − αs·ΔFP`, where `s` is current DTI and `ΔTP`,`ΔFP` are exact marginal changes. The shortcut `k > αs` is valid only for one added, non-redundant dot with fresh truth credit `ΔTP=k` and FP increment `ΔFP=1−k`.
4. **Leakage canary.** Test each feature alone on the holdout before trusting it. AUC >0.90 is leakage until explained.
5. **Hypotheses before implementation.** Review prior-session status, then rank 3–5 genuinely untried within-lane hypotheses by expected relative benefit, uncertainty, and cost. Name the feature layers and physical signature, explain why wider/shifted emission could capture a nearby unmapped fault rather than a known trace, compare with existing code, and define the official data source if any new data is required. Do not claim a ribbon can discover a fault whose ridge detector entirely missed.
6. **Experiment budget and stopping.** Run at most three experiments and stop at two hours. Stop immediately on a literal uniqueness trigger, stale/incomplete inventory, leakage canary failure, or nonpositive/uncertain primary result under the preregistered rule. Do not add experiments just because a result is weak.
7. **Run card.** End the work with one JSON card containing the hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI/evaluator/count/95% CI or explicit NOT MEASURED, surface and final registry results, raster SHA256, local validator output, submission name and note of at most 140 characters, and an unmistakable `promote` or `negative` verdict. Negative results are deliverables.
8. **No slot selection.** Qualification and a real competition submission are separate decisions. Never choose or use a competition slot in this workflow.

## Current status (session 5, 2026-10-11)

The long-standing blocker — the unresolved scope of the literal 70 % overlap stop — was resolved by ratifying **RATIFIED-UNIQ-v1** (protocol item 1 above; IR-58-UNIQ-07 in `docs/research/irregularities.md`). The current candidate is `gems58-concordance-ribbon-40768-20261011T160514Z` (H58-X1 cross-family concordance gate; EXP-2 winner at equal budget, pooled HOLDOUT-DTI 0.043575 cross-fitted vs incumbent 0.040105). Its governing verdict — OK or NOT OK, rendered as the banner on `docs/index.html` — is computed by `scripts/build_site.py` from the complete 703-witness inventory scan receipt and is never hand-written. The literal reading is published beside it (gate G3L). No weekly slot has been used; slot selection stays a separate human decision.

Official references: [competition problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), and the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf). The source register is `docs/SOURCES.md`.
