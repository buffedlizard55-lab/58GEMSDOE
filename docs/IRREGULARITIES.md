# Current irregularities, evidence and stop decision

**Last reviewed: 2026-10-11 UTC. Current decision: NOT OK TO SUBMIT — DO NOT SUBMIT.** This page and [`evidence/run_card.json`](../evidence/run_card.json) are the current status. No experiment, new TIFF, or competition-slot selection was performed in this review. Historical ribbon records are not current evidence.

## Verified blockers

1. **Literal final-dot overlap stop — REGISTRY-MEASUREMENT (frozen inventory).** The existing diagnostic `docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif` has 67,379 positive pixels. The pinned scan records **1.000** of its candidate dots within 3 px of `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif`, above the mandated **0.70** limit. Its worst Spearman correlation, about **0.190**, is below 0.90; that does not override the independent overlap failure. Evidence: [`evidence/run_card.json`](../evidence/run_card.json) and [`evidence/ribbon_uniqueness.json`](../evidence/ribbon_uniqueness.json).
2. **Inventory is incomplete and stale.** The latest pinned scan checked **694/695** rasters; one is missing or invalid. The pinned snapshot is not a complete current inventory of accessible public repository trees. Therefore no uniqueness clearance can be inferred from the scan. Evidence: [`evidence/registry_fetch_report.json`](../evidence/registry_fetch_report.json) and [`evidence/registry_freshness_audit.json`](../evidence/registry_freshness_audit.json).
3. **Candidate-specific pre-placement surface gate is not cleared.** The older pre-placement summary describes another build and is not reusable. No current complete-inventory comparison exists for this candidate's placement surface. Do not emit a different candidate until the required gate is run and passes.
4. **No promotion-grade holdout exists for the current instrument.** The current buffered/nested outer-block HOLDOUT-DTI, withheld-positive count, and valid 95% CI are all **NOT MEASURED**. Historical E1/E2 outputs used truth-informed selection and/or an obsolete split/bootstrap; they are not promotion-grade and must not be reported as current model scores. See [`evidence/run_card.json`](../evidence/run_card.json) and [`docs/research/irregularities.md`](research/irregularities.md), whose banner marks it historical.
5. **No current leakage clearance.** A promotion-grade, buffered-fold feature-alone canary is not recorded. The required AUC >0.90 rule remains active; no legacy canary is a current clearance.
6. **Local file validation is not organizer acceptance.** The diagnostic passes the internal single-band, float32, grid, finite/range, outside-footprint-zero, and mapped-catalogue checks. That is only a local format/range preflight. Nodata interpretation, portal acceptance, uniqueness, and an organizer receipt remain unconfirmed.
7. **The cached feature-stack provenance is limited.** The local stack's bytes match the SHA256 pins in the owner-maintained GitHub bridge. This establishes integrity against those pins, not independent organizer provenance. No new external data was required or downloaded for the width-only review.
8. **Public score attribution was corrected.** The dated **PUBLIC-LEADERBOARD-SNAPSHOT** observed on 2026-10-11 showed xiaofanhu at rank 1 / 0.4133, DARD at rank 8 / 0.3195, and extradr19 at rank 23 / 0.2778. These dynamic board rows are not scores for this TIFF. The GEMSDOE32 owner-maintained H33 page says that file has no organizer score and labels 0.2747 a model projection; no receipt/hash crosswalk ties 0.2778 to H33. See [`docs/LEADERBOARD.md`](LEADERBOARD.md), [`evidence/official_leaderboard_observation_20261011.json`](../evidence/official_leaderboard_observation_20261011.json), and [`registry/submissions_seen.csv`](../registry/submissions_seen.csv).
9. **Legacy publication paths were unsafe.** The old ribbon site/feed and private submission/experiment CLIs could publish stale permission wording or non-promotion-grade values. Their downloadable artifacts are archived under `evidence/ribbon/archive-downloads/`; the old feed workflow and unsafe CLI paths are disabled. Current pages make no clearance claim.
10. **Official deadline sources disagree.** The competition homepage and September 2026 rules PDF display different cutoff times. Until the organizer clarifies, follow the earlier cutoff. Source checks are recorded in [`docs/SOURCES.md`](SOURCES.md); this is a planning precaution, not legal advice.

## Scope and next action

Stay in the ribbon-width lane: keep the placement surface fixed and test only how calibrated localization error changes ribbon support/width around already-detected ridges. A width change cannot detect a structure absent from that surface. The ranked proposals and preregistered failure/stopping criteria are in [`docs/research/hypotheses_new.md`](research/hypotheses_new.md).

Do **not** start an experiment while the inventory is stale/incomplete or a literal uniqueness stop remains. First resolve the inventory/gate issue without exempting dense rasters. If and only if the pre-placement gate clears, use the shared cached stack, buffered whole-segment holdout, `gems57.evaluate_holdout`, and `gems57.submission_writer`. Never select or use a weekly slot. The diagnostic download remains available only with an unmistakable NOT CLEARED warning; do not submit it.

For current metric algebra and the official DTI definition (α=0.2, β=0.8; 300 m triangular support at 100 m resolution), see [`docs/research/metric.md`](research/metric.md) and the official [competition problem/metric page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

---

# Session 3 (2026-10-11 UTC) — additional irregularities, and two closures

Numbering continues the historical list that this page replaced; each item carries its own ID.

19. **IR-58-TARGET-01 — the owner's target score is stale.** The brief says "beat 0.3195". The live
    board read on 2026-10-11 has **0.4133 (xiaofanhu)** at rank 1 and 0.3195 (DARD) at **rank 8**
    (independently confirmed by `evidence/official_leaderboard_observation_20261011.json`). Every
    margin and the marginal-inclusion bar (α·DTI₀ = 0.2 × 0.4133 = **0.0827**, i.e. a dot pays only
    within **2.752 px = 275 m**) are recomputed against 0.4133 in this session's evidence.
20. **IR-58-DATA-01 — the delivered stack has no aeroradiometric bands, although the organizers say
    they were acquired.** Page 968 states GeoDAWN combines USGS EarthMRI and DOE OG **aeromagnetic and
    aeroradiometric** surveys with coordinated **3DEP lidar**, and that most faults in the region are
    hidden below the surface. The 19 delivered bands contain **no eK/eU/eTh/total-count channel and no
    1 m lidar derivative**. Potassium metasomatism, silicification and Fe-oxide staining — the classic
    radiometric expression of a hidden fault — are therefore unreachable from the provided data, and
    the USGS releases are not fetchable from this sandbox (binary egress is blocked; `fetch_page` is
    text-only). Recorded as an owner-download hypothesis with verified links
    (`evidence/organizer_confirmed.json`, `docs/research/hypotheses_session3.md` H58-R3); no number in
    this repository is derived from it.
21. **IR-58-UNIQ-04 — the lane's uniqueness screen measured both overlap directions backwards.** The
    protocol's stop statistic is the fraction of *my* dots within 3 px of *one witness's* dots;
    `src/gems58w/uniqueness.py` computed the reverse fraction and called it `forward_overlap`, and
    applied the dense-prior exemption to the wrong leg. The definitions now live once in
    `src/gems57/uniqueness.py` and are imported (no private fork). **Every overlap number this lane
    published before 2026-10-11 — including the "worst forward overlap 0.3600" quoted for the earlier
    38,000-dot ribbon file — was measured with the directions exchanged and is superseded.** The
    template-level registry scanner already had the direction right, so frozen-inventory numbers
    published by the sibling lane were unaffected. Regression test:
    `tests/test_uniqueness_informative.py::test_forward_overlap_is_my_dots_near_theirs`.
22. **IR-58-UNIQ-03 — the literal 0.70 gate cannot be cleared by any candidate, so a literal firing is
    not evidence of duplication.** Extends items 1 and IR-58-UNIQ-02 with a full-inventory measurement:
    **54** of the 702 witnesses have a chance-level expected overlap `E ≥ 0.99`, so their 3 px dilation
    covers essentially the whole footprint and they overlap *every* nonempty candidate; no buffer from
    3 to 10 px clears 0.70 against them (`evidence/buffer_overlap_scan.json`). The shared summariser now
    reports `E`, the chance-corrected lift `(observed − E)/(1 − E)`, a `saturated` flag, a
    representation class, and the literal **and** informative readings side by side;
    `lane_drift_evidence` distinguishes `none` / `vacuous-only` / `informative`, and clearance never
    rests on a vacuous firing. Verified by `tests/test_uniqueness_informative.py` (7 tests).
23. **IR-58-UNIQ-05 — the shared scanner rejected the organizer's own submission representation.**
    `data/official/sample_submission.tif` carries **7,111,787 NaN pixels outside the footprint** with
    `nodata=nan` and finite values inside, exactly as page 967 requires, but
    `check_uniqueness_registry.py` demanded an all-finite candidate — which is why earlier artifacts had
    to be published as `*-zeros.tif` variants that do not match the official representation. Fixed once
    in the shared tool: non-finite **inside** the footprint stays a hard error (that is precisely the
    portal rejection `Predicted values must be in range [0, 1]`), non-finite outside is normalised for
    footprint-restricted statistics, and both counts are recorded in the receipt.
24. **IR-58-LIVE-01 — no dot-field statistic predicts the owner-quoted live scores.** 78 owner-quoted
    scores (`registry/live_scores_owner_reported.csv`) were matched to registry rasters and re-measured
    from sha256-verified bytes. The first attempt was garbage: the matcher used
    `re.findall(r"[0-9a-f]{8,}")`, which also matches ISO dates (`20261003`), collapsing 78 labels onto
    33 rasters and giving R² = −0.999. Now repository-scoped and fail-closed (tokens ≥ 10 hex chars with
    ≥ 3 letters, repository inferred from the quoted site, ambiguous rows dropped, conflicting scores
    excluded): **66 rasters measured, 12 rows dropped, 0 conflicts**. Result
    (`evidence/live_evidence_fit.json`, verdict **NEGATIVE**): the two-parameter model
    `s = κM′/(0.2n′ + 0.8G)` fits with **R² = −1.27** and G pinned at its bound, and **no covariate
    reaches |Spearman| 0.30** (best: median off-catalogue distance +0.258). The earlier n=20
    `Spearman(dots, score) = −0.831` weakens to +0.044 over 66 files and must not be reused. Because
    subset membership is undisclosed, this is unfixable locally, so the emission budget is taken from
    the measured **family** (median dot count of the owner-reported ≥ 0.24 files = **40,768**, n = 12)
    and labelled USER-REPORTED-SCORE.
25. **IR-58-SIGMA-01 — the tight-line branch is unreachable, and σ was previously fitted on the folds
    it scored.** `gems58w.sigma` floors σ at 0.5 px while every measured stratum is far above it
    (pooled median **6.88 px**, rms 8.01, 994 components; block medians NW 7.08 / NE 6.79 / SW 5.79 /
    SE 8.54), so "single tight line where σ < 0.5 px" can never fire; the planner returned 5 lines for
    5,794 of 6,286 segments and 3 for 492. Separately the published `evidence/ribbon/holdout_sigma.json`
    table rests on **n_pairs = 14** and was fitted on scored folds. Both are fixed for this session's
    numbers: σ is **leave-one-block-out cross-fitted** with per-stratum counts
    (`evidence/ribbon/adaptive_sigma.json`). Honest reading of the equal-budget contest: the gain is
    "ribbon beats tight line where σ is large" (+0.0065 in σ ∈ [3,6] px, where the tight line scores
    exactly 0) and "ribbon loses where σ is small" (−0.0014 below 1.5 px) — **not** per-segment
    adaptivity, which measured exactly 0.000000 against a uniform ribbon.
26. **IR-58-REG-01 — the pinned inventory was one raster short; it is now complete, which closes
    blocker 2 above for the new scan.** The pin `927dc17f…`
    (`55GEMSDOE:docs/downloads/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif`, blob
    `3b4dca15…`) exists only at the pinned commit `d92606c28dc5e93ee1bce5148b92ccbb5225d023`. It was
    recovered with `git fetch --depth 1 origin d92606c2…` plus `git cat-file blob 3b4dca15…`, and the
    decoded bytes re-hash to the pin (1,516,449 B), so the cache now holds **695/695**. A freshness
    delta (`scripts/registry_delta_inventory.py`) then walked the **current** default branches of all 56
    reachable clones plus this repository's tree and found **no** new grid-format raster in any sibling,
    giving `registry/registry_merged.json` = **703 byte-verified witnesses**. The scan that produced the
    current verdict is therefore complete (0 missing/invalid, 0 source errors). It remains a *public
    sibling-repository* inventory, not an organizer registry: private, renamed or deleted repositories
    are out of scope by construction.
27. **IR-58-ALLO-01 — the ribbon planner's marginal false-positive term is not the official one.** As
    recorded in the archived `src/gems58w/allocation.py` docstring, `_marginal_pair` masks cost where
    existing lines already have truth credit, so it does not reproduce the per-prediction `FP_w` for
    interacting lines; the exact rule is `U = (1 − αs)ΔTP − αsΔFP`. Consequence for session 3: the
    *choice* of line count per segment is a legacy design rule, while every *reported* DTI was computed
    with the exact metric on isolated dots (min separation 1, 3 px lattice), where the `k > αs` shortcut
    is valid. Re-deriving the plan with exact marginal utilities is open work.
28. **IR-58-UNIQ-06 — the sibling lane's published uniqueness clearance is the reverse statistic, and
    its deliverable is offered as "DOWNLOAD OK" on that basis.** The scatter-cover lane delivered
    `docs/deliverable/downloads/gems58-novel-scatter-44090-20261011T0630Z.tif` (sha256
    `5f64b6dc44a3d6639691b679337ec64c1b4bb1b3f1ce63dfe17258ad6fdbf1e0`, 44,090 dots, 15/15 local
    checks) with a screen published as "**473** rasters · worst rank correlation 0.0557 · worst 3 px
    forward overlap **0.3160** · **0 triggers**", and `docs/index.html` on main carries a green
    "✅ NEW CANDIDATE — DOWNLOAD OK" banner for it. That overlap figure is the fraction of each
    **witness's** dots within 3 px of the candidate's — the *reverse* statistic that the archived
    `gems58w.screen_against` triggered on before IR-58-UNIQ-04 was fixed. The protocol's statistic is
    the fraction of the **candidate's** dots within 3 px of one witness's dots. Re-measured that way
    against the same byte-verified inventory (702 witnesses, `.cache/registry` restored and
    sha256-checked), the file has **78 firings** — worst **1.0000** against the plane-filling
    `GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif` — and **0** firings in
    the reverse direction, which is the exact signature of the exchanged directions
    ([`evidence/ribbon/sibling_direction_check.json`](../evidence/ribbon/sibling_direction_check.json)).
    **This is not an accusation of duplication.** The same degeneracy fires on the session-3 candidate
    (81 firings) because those witnesses' 3 px dilations cover 61–100 % of the footprint and therefore
    overlap *every* nonempty candidate; the honest reading is that neither file is cleared by the
    literal rule and both need the same chance-corrected reading. What the irregularity is: a clearance
    published in the wrong direction cannot support a green "download OK" banner, and the two lanes are
    now reporting opposite verdicts from the same registry because they measured different statistics.
    **The corrected full screen has now been run**
    ([`evidence/ribbon/sibling_full_inventory.json`](../evidence/ribbon/sibling_full_inventory.json)):
    703 witnesses, complete, 0 missing/invalid — verdict **negative**, `stop_required` true,
    **79 literal firings** (54 vacuous with E ≥ 0.99, 25 informative; worst informative overlap
    0.8496), while the discriminating statistics all pass by wide margins (byte-unique, pixel-unique,
    worst rank correlation **0.0900** vs 0.90, worst dot-set Jaccard **0.0509** vs 0.50). Its highest
    chance-corrected lift is **1.000** against `5GEMSDOE:data/derived/context_detector_prob_u8.tif`
    (every one of its dots within 3 px of a witness whose own dilation covers ~75 % of the footprint)
    and **0.7143** against this lane's candidate. So the sibling file is in exactly this lane's
    position under the protocol as written — not cleared by the literal rule, and not a copy of
    anything — and its green banner rests on a statistic the protocol does not define. Note also that
    the sibling screen ran over **473** live-fetched rasters while the pinned+delta inventory holds
    **703**; the inventories are not the same set, and `rho_subsample` (a subsampled Spearman) is now
    recorded explicitly in the summary so a subsampled pass can never be reported as an exact one.

    **Cross-lane screen** ([`evidence/ribbon/cross_lane_screen.json`](../evidence/ribbon/cross_lane_screen.json)):
    the two candidates share 3,542 exact pixels out of 40,768 and 44,090 (Jaccard 0.0436), so neither
    copies the other, but the overlap is strongly **asymmetric** — this lane's file has **0.2998** of
    its dots within 3 px of the sibling's support (E = 0.0450, lift 0.2668, **clears**) while the
    sibling's file has **0.7513** of its dots within 3 px of this lane's support (E = 0.1295, lift
    0.7143, **fires**). The cause is geometry: ridge-concentrated emission dilates to 12.95 % of the
    footprint and swallows a sparse scatter emission, whose own dilation covers 4.50 %. Consequence for
    the owner's decision: this lane's reading is unchanged by the sibling file joining the inventory,
    but any ratified chance-corrected threshold must be applied to **both** files at the same value, or
    the two lanes will keep publishing opposite verdicts from the same registry.

---

## Session 4 (2026-10-11 UTC) — verification irregularities

Logged while re-checking the registered candidate and the public record. Nothing here changes the
NOT OK TO SUBMIT verdict. Evidence: [`evidence/session4_verification_20261011.json`](../evidence/session4_verification_20261011.json).

- **IR-58-S4-01 — "0.3774" is not on the official board.** The requester's list gives 0.3774 as the
  GEMSDOE leaderboard high. The official [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
  fetched 2026-10-11, shows ranks 1–49 with no 0.3774 row; rank 1 is xiaofanhu at 0.4133. Not verified
  from any official source. Owner to review the page where 0.3774 came from.
- **IR-58-S4-02 — DARD rank.** The repo records DARD at rank 8 (0.3195). The 2026-10-11 fetch shows
  rank **9**, with kinghorton42 at 0.3261 in rank 8. Board ranks are dynamic; the dated record in
  `evidence/official_leaderboard_observation_20261011.json` is not overwritten.
- **IR-58-S4-03 — rules section for the submission limit.** `docs/SOURCES.md` cites "§3.4" for the
  three-submissions-per-week limit. In the fetched PDF (<https://docs.nlr.gov/docs/fy26osti/96647.pdf>)
  the text sits in §3.2 (Process Overview). Same limit, different section number. Owner to correct the register.
- **IR-58-S4-04 — the 0.2778 attribution.** The request ties 0.2778 to the GEMSDOE32 H33 file. The
  official board ties 0.2778 to `extradr19` (rank 23). The GEMSDOE32 owner page says that H33 file has
  "NO ORGANISER SCORE" and calls 0.2747 a projection. No receipt or hash ties 0.2778 to H33. The
  attribution is unsupported and must not be repeated as fact.

---

## Session 6 (2026-10-11 UTC) — merge-reconciliation irregularities

Logged while merging the session-6 review branch into the session-5 trunk. None of these changes a
verdict; each one removes a claim that the evidence did not support.

- **IR-58-S6-01 — the archived front-door pages still granted download permission.**
  `docs/deliverable/index.html` and `docs/deliverable/executive-summary.html` carried
  "⭑ PRIMARY — download & submit candidate" and "download OK" badges for rasters whose own lanes
  recorded a negative verdict, and quoted `HOLDOUT-DTI 0.000000` beside a green badge. Both pages are
  now red archival notices, their rasters are labeled individually in
  [`docs/downloads/index.html`](downloads/index.html), and `scripts/ribbon_check_site.py` plus
  `tests/test_ribbon_repo_hygiene.py` fail if the affirmative wording returns.
- **IR-58-S6-02 — a legacy diagnostic was labelled promotion-grade.** The archived sigma-adaptive run
  cards (`evidence/ribbon/archive-s3/run_card_v2.json`, `run_card_final.json`) carried
  `holdout_dti_label: "HOLDOUT-DTI"` for 0.043651 measured with the legacy `gems58-pooled-hide-v1`
  instrument and a four-block min–max range. The label is now `LEGACY-DIAGNOSTIC-ONLY` with a note;
  the value, evaluator, protocol, withheld-positive count and receipts are unchanged. A four-block
  min–max range is not a defensible 95 % CI, and the standing protocol requires one.
- **IR-58-S6-03 — the local file audit was pinned to a superseded file.** The audit script hard-coded
  the session-3 TIFF, so after session 5 emitted a new candidate it would have kept certifying the
  old bytes. It now reads the candidate from `evidence/ribbon/emission.json`. The regenerated receipt
  reports 10/10 checks and states that the decoded-pixel binding is *computed*, because that emission
  receipt records no decoded hash — the check is not silently skipped as a pass.
- **IR-58-S6-04 — stale counts in the review documents.** `docs/SOURCES.md`, `docs/MISSION.md`,
  `docs/SUBMISSION_GUIDE.md` and two research notes still quoted the session-3 scan (702 rasters, 81
  triggers, `ecf833f8…`). They now quote the governing receipt (703 rasters, 83 triggers, 29
  informative, `f709b6f1…`) and name the session-3 receipts as archived.
- **IR-58-S6-05 — no qualification receipt exists, so nothing may be emitted.**
  `evidence/ribbon_qualification.json` is absent; `scripts/build_ribbon_emission.py` exits 2 without
  writing a TIFF. The pre-emission contract it enforces is
  [`scripts/qualification_gates.py`](../scripts/qualification_gates.py), documented in
  [`docs/research/qualification_gates.md`](research/qualification_gates.md).

---

# Session 6 (2026-10-11 UTC) — new irregularities

Each item is measured in this session; the receipts are under `evidence/s6/`.

**IR-58-S6-01 — the shipped `labels.tif` is byte-identical to `existing_faults.tif`.**
Both are sha256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`
(425,830 B, int8, values `{-1,0,1}`, 60,988 positives). So the "labels" in this checkout are the
public USGS/INGENIOUS catalogue itself and carry **no independent label information**. This is
consistent with the organizer's statement that the training labels come from the USGS quaternary
fault maps and INGENIOUS, and with the fact that the scored truth is a *different, private* set of
newly identified faults — but any code or prose that treats `labels.tif` as a second, checkable
label set is wrong. `src/gems58w/grid.py` already documents the identity.

**IR-58-S6-02 — the mandated holdout is blind to off-catalogue emission by construction.**
The protocol's holdout withholds *catalogue* segments. A delivered raster must exclude the
*whole* catalogue (plus a collar), so its HOLDOUT-DTI is exactly `0.0` — measured, not assumed:
the first session-6 emission returned `tp = 0` on all four folds for this reason. The HOLDOUT-DTI
reported for this session's file is therefore measured on a **holdout-domain emission** (identical
support, ranking and geometry; only the exclusion mask differs). The two are labelled separately in
`evidence/s6/emit.json`.

**IR-58-S6-03 — the ridge detector is at or below a uniform random control on this instrument.**
At an identical 38,000-dot budget per block, pooled over four folds
(`gems57.metric`, protocol `gems58-pooled-hide-v1`): uniform random **0.052737**; the
multi-family/multi-scale Hessian ridge field **0.044208** before dot isolation and **0.058061**
after. The instrument withholds catalogue faults while the leaderboard scores new, off-catalogue
faults, and the sign of the catalogue-distance term is opposite in the two populations
(`docs/s6/LIVE_CALIBRATION.md`). No detector ranking from this holdout may be carried to the
leaderboard; the geometry conclusions are safe because the bias is common to all arms.

**IR-58-S6-04 — the registry screen covers 694 of 703 pinned witnesses, not "every earlier raster".**
`scripts/fetch_registry_sparse.py` restored 694/703 (9 unreachable in this sandbox), and the screen
also screened the 19 locally committed registry rasters; 692 unique, sha256-verified witnesses were
actually compared. The scope is recorded in `evidence/s6/uniqueness.json`.

**IR-58-S6-05 — band 10 (`deq_n100a15`) has an extreme heavy tail, and every band has 3,061 NaNs
inside the competition footprint.** Raw `deq_n100a15`: median 621.9, 99th percentile 50,237,
maximum 4,962,515 — a mean z-score of +20 at a dot set means almost nothing, which is why the
session-6 feature scan uses percentile ranks rather than z-scores. All 19 bands share exactly
3,061 NaN pixels inside the 5,167,373-pixel footprint (0.06 %), which any per-band statistic must
handle explicitly.

**IR-58-S6-06 — the uniqueness thresholds are dominated by plane-filling witnesses.** 54 of 692
witnesses have a chance level `E` of exactly 1.000 (their own 3 px dilation covers the whole scored
footprint), so they fire on **every** non-empty candidate; 26 more have `E` between 0.72 and 0.99.
Under the literal 70 % rule this session's file fires 81 times, of which exactly one
(`GEMSDOE3:docs/downloads/coverage-v3-wide-20260925T054019Z-0ac095a7ed.tif`, 624,025 dots,
forward overlap 0.7476 at chance level 0.6626) is informative. Every discriminating statistic
clears: worst chance-corrected lift 0.4756 < 0.50, worst rank correlation 0.0563 < 0.90, worst
dot-set Jaccard 0.0318 < 0.50, bytes and decoded pixels unique, 5,526 shared pixels with that
witness (0.9 % of its dots). The standing instruction makes rule A binding, so the file is logged
as a duplicate and NOT cleared; the arithmetic above is published so the owner can see that the
verdict is a threshold artefact, not copying.

**IR-58-S6-07 — shared-tool performance defect fixed in place.** `s6_ribbon.emit` recomputed
`mask.sum()` once per ridge segment (O(budget × 12.3 M)), which made each geometry arm take ~150 s
instead of ~20 s. Replaced with a running counter in the shared script; no scoring behaviour
changed.

**IR-58-S6-08 — `gems58w.submission.write` produces no ZIP.** The portal accepts a `.zip`
containing exactly one GeoTIFF and it is ~1,000× smaller than the uncompressed raster, so
`scripts/s6_package.py` was added to write the one-TIFF ZIP and the download receipt and to verify
the round-trip. The writer itself was left alone (it is shared).
