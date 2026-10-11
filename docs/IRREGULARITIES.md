# Irregularities, blockers and audit trail

This file records observed issues, not assumptions. **Current submit decision: NOT OK TO SUBMIT / DO NOT SUBMIT.** No experiment was rerun, no slot was used, and no organizer receipt was obtained in this review.

1. **Literal final-dot duplicate stop.** The frozen 695-raster audit flags 123 rasters under the literal rho/forward-overlap safeguards. More importantly, its `GEMSDOE2` full-footprint-positive raster is a direct witness: all candidate dots are within 3 px (`overlap = 1.0`, threshold 0.70). The candidate rank correlation with that raster is only 0.146662; the independent overlap rule still blocks it. The audit report is `evidence/ribbon_uniqueness.json`.
2. **Frozen inventory is stale and not exhaustive/current.** `registry/registry_refreshed.json` is dated `2026-10-10T19:58:45.875405Z` and contains 57 pinned repository snapshots / 695 unique TIFFs. GitHub default-branch tree queries on 2026-10-11 found TIFFs in 58GEMSDOE, 59GEMSDOE, 60GEMSDOE, and 61GEMSDOE, none of which appears in the manifest. GEMSDOE52 is present, but its current tree differs from the pinned commit and contains 88 added TIFF paths. No new artifacts were locally downloaded or uniqueness-scanned. Exact evidence: `evidence/registry_freshness_audit.json`.
3. **Current pre-placement gate is unverified.** `registry/uniqueness_surface_pre-placement_summary.json` reports a different 38,163-dot candidate surface, 731 comparisons, 25 flags, and exclusions for dense priors. That differs from the current candidate and from the literal no-exemption rule. It cannot clear the pre-placement surface phase. Current candidate surface comparison against a current inventory has not been run.
4. **Previous holdout experiment is not promotion-grade.** The stored legacy ribbon diagnostics used a per-segment acceptance step that consulted the same cell's withheld truth; σ was fit on the scored folds. The earlier block bootstrap concatenated repeated seed/fold contributions and resampled them as though they were independent physical blocks. The earlier split also did not satisfy the newly required whole-component feature-context buffer. Those stored values are explicitly marked invalid/not reportable in `evidence/ribbon_e2_arms.json`; do not cite them as an independent validation score or performance claim.
5. **Buffered constructor is code-only so far.** `build_buffered_holdout_context` was added to `src/gems57/holdout.py`; toy tests verify whole-component withholding, a 3-px feature collar, exact known-fault masking and construction of shared `Cell` objects. No experiment was rerun using it. Its presence does not validate the existing candidate.
6. **Legacy scripts/packages are not the shared pipeline.** `scripts/run_ribbon_lane.py`, `scripts/uniqueness_check.py`, `scripts/check_data.py`, `scripts/make_submission.py`, `src/gems58`, and `gems/` contain earlier private metrics, folds, or writers. Their promotion/upload CLIs are disabled or deprecated. The active shared evaluator is `gems57.evaluate_holdout` (`gems57-pooled-hide-v2`); the active writer is `gems57.submission_writer`.
7. **Official metric and format page are now directly verified.** DrivenData page 967 specifies DTI with α=0.2, β=0.8, 300 m triangular support and the GeoTIFF coordinate/resolution/value requirements. The September 2026 official rules PDF is reachable. This does not provide a leaderboard score or upload receipt.
8. **Nodata interpretation remains an open format issue.** The local sample template has NaNs outside the finite study footprint, while the project's conservative writer/validator policy accepts all-finite zeros outside it. The official problem page says values outside bounds are null/NaN. The portal's earlier range error has not been proven to be caused by NaNs. The candidate's local check is internal only; no organizer acceptance was observed.
9. **Deadline discrepancy is official and unresolved.** The DrivenData homepage displays Dec. 3, 2026 at 11:59 p.m. UTC. Appendix A of the Sept. 2026 rules says 5:00 p.m. ET on the deadline date (22:00 UTC on Dec. 3, given standard time). Until clarified, plan for 5:00 p.m. ET. No organizer inquiry was made.
10. **Submission/slot rules.** Official rules §3.4 allow up to three feedback-scoring submissions per week but require one final submission selected across both prize rounds. The current workflow has not selected or used a weekly slot.
11. **Generative-AI disclosure is required.** Official rules §3.2 requires a narrative description, when applicable, of the extent and manner of generative-AI use. Read the official PDF and comply; this is not organizer legal advice.
12. **Future external-data availability is mixed.** ComCat API and a constrained M≥2.5 query were confirmed reachable; its 20,000-result cap blocks the broader M≥1.5 query without partitioning. USGS 3DEP returned 1,856 1 m DEM product records over the study bounding box, but no tiles were downloaded. USGS lists an updated 2026 GeMS SGMC GIS payload, but the GIS link returned HTTP 500. DOE GDR page 1704 exposes a public 21.6 GB bundle with Nevada resources, but no archive was downloaded. See `docs/SOURCES.md` and `docs/research/hypotheses_new.md`.
13. **No current public leaderboard was checked.** There is no organizer receipt and no score may be labelled ORGANIZER-CONFIRMED.
14. **Supplemental pinned-raster restore remains incomplete.** *(Superseded 2026-10-11 by item 26,
    IR-58-REG-01: the missing pin `927dc17f…` was recovered from `55GEMSDOE` commit `d92606c2…` and
    re-hashed, so the restore is now 695/695 and a current-default-branch delta brings the witness
    inventory to 703 byte-verified rasters. The text below is kept as written.)* The latest ribbon scan reports 694/695 pinned blobs checked, with an error row for `55GEMSDOE:docs/downloads/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif`; `complete_accessible_scan` is false. The separate fetch report also records an inaccessible `57GEMSDOE-PR6` clone. Neither fact clears the existing literal overlap failure. See `evidence/ribbon_uniqueness.json` and `evidence/registry_fetch_report.json`.
15. **Chance-corrected overlap is diagnostic only.** The REGISTRY-MEASUREMENT diagnostic separates saturated comparisons from informative ones, but reports up to 1.0 lift for some informative rows. No replacement threshold or density exemption is authorized; the user's literal >0.70 dot-overlap stop remains in force. See `evidence/ribbon_uniqueness_chance_corrected.json`.
16. **MECE/multi-evidence artifacts are out of lane.** They arrived in an intervening main-branch change, compare uniqueness only against the ribbon candidate, and use a full-catalogue proximity holdout that is explicitly leakage-flagged. This work remains ribbon-only; those artifacts are marked diagnostic/NOT OK TO SUBMIT, and the MECE script's command-line entry point now exits with a NO-GO message. None is evidence for a promotion decision.

---

# Session 2 addendum (2026-10-11) — supervised-ranking lane


9. **IR-58-FEAT-01 — the official feature stack IS reachable from this sandbox, via the owner's pinned git bridge.**
   `data/fetch_log.json` records TLS failures for every Dropbox mirror, and the earlier README concluded
   that "the single remaining blocker to training is data placement". That conclusion was too pessimistic.
   The competition `training_features.tif` is published, sha256-pinned and split into five parts inside
   `GEMSDOE:data/bridge/` (GitHub's 100 MB blob limit forces the split);
   <https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/data/bridge/manifest.json> pins the whole file
   at 418,912,844 B / `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`.
   Action: `scripts/fetch_feature_stack.sh` fetches and verifies all five part pins **and** the whole-file
   pin; the local reassembly reproduced `4371c82e...` exactly, and `rasterio` reports 19 float32 bands,
   EPSG:32611, 3730x3292, transform (100, 0, 243350, 0, -100, 4508550) — the same six numbers
   `gems57.grid` pins from `sample_submission.tif`. The 419 MB file is written to `~/.cache/gems/`, outside
   the repository, and is not committed.

10. **IR-58-NAN-01 — SciPy's recursive 1-D filters let one nodata cell poison an entire row.**
    The first run of `scripts/run_model_experiments.py` died with
    `Found array with 0 sample(s) (shape=(0, 35))`. Cause, verified by direct experiment: `ndi.uniform_filter`
    and `ndi.gaussian_filter` produced **100 % NaN** output over a block in which 51 % of cells were nodata,
    because their 1-D passes are recursive/sliding, so a single NaN propagates along the whole line. All six
    `std3`, both `std7` and (silently, by zeroing rather than NaN-ing) the coherence features were affected.
    Action: replaced with NaN-aware masked estimators `G(a*w)/G(w)` and `sum(a*w)/sum(w)`
    (`src/gems59/features.py::_gsmooth`, `::_lmean_var`), and the Laplacian is de-biased for missing
    neighbours. Regression tests in `tests/test_gems59.py` assert (a) one NaN no longer destroys a row,
    (b) the local mean/variance are exact on a valid run, (c) coherence of a pure ramp is ~1, and
    (d) no derived feature is entirely NaN. 51 tests pass.

11. **IR-58-STACKMASK-01 — the feature stack's nodata mask is not exactly the study-area footprint.**
    Band 1's sentinel mask differs from `~footprint` (from `sample_submission.tif`) in **4,601 of
    12,279,160** cells (0.037 %); the stack masks 7,113,308 cells, the footprint has 7,111,787 non-finite.
    Splitting the symmetric difference: **3,061** cells are inside the footprint but carry no geophysical
    data, and **1,540** cells are outside the footprint but do carry data. Action: they are
    dropped from training (`np.isfinite(X).any(axis=1)`) and cannot be predicted, so they receive 0.0 and
    are never emitted. Flagged for review: any sibling pipeline that assumes the two masks are identical
    will read sentinel values (-3.4e38) as data on those cells.

12. **IR-58-HOLD-01 — the "detached" holdout mode is barely more conservative than "all".**
    `gems57.holdout` offers `mode="detached"` (withhold only segments whose component lies >= 4 px from
    every other component) as the conservative instrument. Measured: it withholds **22,619** positive pixels
    versus **22,641** for `mode="all"` — a 0.1 % difference — and the withheld pixels' distance to the
    visible catalogue is median 4.47 px (detached) vs 4.12 px (all). The filter is nearly a no-op because
    most mapped fault components are already more than 400 m apart. Honest reading: about a third of
    withheld truth lies beyond the 300 m kernel of any visible trace in either mode (31.0 % / 34.3 % are
    more than 6 px away), so the instrument is a fair but not a strict analogue of a genuinely unmapped
    splay. Reported on both modes rather than choosing the flattering one.

13. **IR-58-REG-02 — a registry-pinned repository no longer exists on GitHub.**
    `scripts/fetch_registry_sparse.py` reports `57GEMSDOE-PR6: clone rc=128: remote: Repository not found`.
    Its rasters were still restored from their alternate pinned sources, so the scan stayed complete
    (695/695, 0 hash mismatches) — but only because every affected record has more than one source.
    Flagged for review: a registry scan that keeps only the first source per raster would silently shrink.

14. **IR-58-REG-03 — one registry-pinned blob is absent from its repo's current `main` (recurring).**
    `55GEMSDOE:docs/downloads/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif` (pin `927dc17f...`)
    is only present at the registry's pinned commit `d92606c2...`. Fetched that commit directly, verified
    sha256 equals the pin, cached it. Same class of problem as IR-58-REG-01; the shared fetch tool does not
    fall back to pinned commits, so this session did it by hand and records it here.

15. **IR-58-BUDGET-01 — within the owner's own record the dot budget dominates the score.**
    Measured from 20 sha256-verified owner rasters paired with the scores quoted on their pages
    (`evidence/sibling_record.json`): the 13 rasters with 37,654-44,090 positive pixels score
    0.2376-0.2778 (median 0.2632); the 7 rasters with 60,069-227,507 pixels score 0.1294-0.2477
    (median 0.1894); Spearman(dots, score) = **-0.831**. Those scores are USER-REPORTED, not organizer
    receipts, and at least one attribution in that record is already known to be wrong (item in
    `registry/submissions_seen.csv`), so this is a strong prior rather than a calibration. It is why the
    shipped budget comes from the record and only the *ranking* is validated on the holdout.

16. **IR-58-RIBBON-01 — the ribbon lane's shipped raster scored below its own baseline; archived.**
    Session 1 shipped `gems58-ribbon-concordant-...-zeros.tif` with an oracle arm at 0.3583 in the header
    while its truth-free live rule measured **0.1309** pooled, below the single-tight-line baseline of
    **0.1573** (`evidence/ribbon_e2b_liverule.json`, `evidence/ribbon_e2c_liverule_variants.json`). The
    oracle number was labelled correctly in the body but led the page. Action: the raster is moved to
    `docs/downloads/archive/` with a README stating why, so `docs/downloads/` holds exactly one candidate
    and the site cannot offer the wrong file.

17. **IR-58-UNIQ-02 — the literal 3-px forward-overlap gate is also degenerate against plane-filling rasters.**
    IR-58-UNIQ-01 already recorded that dense soft surfaces (>=200k positive cells) overlap 1.00 with ANY
    near-catalogue emission, because their support covers the whole study area. The full scan of the
    session-2 candidate (`evidence/model_uniqueness.json`, 695/695 rasters, 0 hash mismatches) shows a
    second, stronger form of the same defect: `13GEMSDOE:docs/downloads/13gems_20261001_r13-lattice-s5_v2_zerofill.tif`
    has **206,895** positive cells, a density of **0.0400 = 1/5²** — a 5-px square lattice across the whole
    footprint. Measured: dilating that raster's support by the 3-px kernel disk covers **0.999** of the
    footprint, so *every* emission whatsoever has ~100 % of its dots within 3 px of its dots. Measured
    overlap of this candidate with it: **0.999 at buffers 3, 4, 5, 6, 7, 8 and 10 px**
    (`evidence/buffer_overlap_scan.json`) — a constant, and therefore information-free.
    `5GEMSDOE:data/evidence/leaderboard_anchor/pindrop-v4-discovery-37f9d5b855.tif` (155,021 cells) is a
    weaker case of the same thing: its 3-px dilation covers 0.734 of the footprint.
    Consequence: no near-catalogue emission can pass the literal 70 % forward-overlap rule while that
    lattice is in the registry, whatever lane it is in. Action: the verdict is reported as **negative on
    the literal gate**, with both the literal number and the gate's behaviour against rasters that *can*
    discriminate (3-px dilation covering <= 0.70 of the footprint) recorded. Even restricted that way the
    candidate flags at 0.71-0.88 against nine broad near-catalogue bands — including
    `pindrop-v4-discovery` (0.0830 on the user-reported leaderboard) — which is a statement that the
    candidate is in the same *family* as those bands, not that it reuses a lane. The decisive gates pass
    by wide margins: worst Spearman **0.140** (limit 0.90), worst Jaccard dot-set overlap **0.061**
    (limit 0.50), byte-unique and pixel-unique among all 695 checked, and forward overlap against every
    one of the proven high scorers is 0.17-0.35 (h27-4 0.264, h36-1 0.257, h32-1 0.293, h38-1 0.260,
    anderson 0.226, d28 0.311, h19-5 0.346, Hedge-v2 0.428). Suggested protocol fix for the owner:
    exclude carrier rasters (maximum_filter-free test: their 3-px dilation covers > 0.70 of the footprint)
    from the forward-overlap rule, exactly as dense soft surfaces should be excluded.

18. **IR-58-CTX-01 — distance-to-catalogue as a model feature collapses the classifier onto the catalogue.**
    The CTX family adds `distance to the visible catalogue` to the 35 geophysical features. Its holdout
    canary AUC is the highest of any single feature (0.856 in `all`, 0.844 in `detached` — under the 0.90
    leakage line), so it was expected to be the strongest arm. Measured instead: the fitted model's
    off-catalogue probability field is **exactly zero everywhere** (max 0.0000; the whole footprint mean is
    0.0107, i.e. all the mass sits on the ~61k catalogue cells). Any emission rule that excludes the
    catalogue therefore emits nothing from CTX, which is why its equal-budget DTI is 0.0036-0.0059.
    Interpretation: with a strongly separable feature the boosted trees saturate to 0/1 and never learn to
    place mass *beside* the catalogue. Action: CTX is reported as a negative result (it is still in the
    evidence as an arm), the PROX family is used instead, and the collapse is flagged so that a future
    lane does not re-derive it.

19. **IR-58-TARGET-01 — the owner's target score is stale, and the live leader is 0.4133.**
    The standing brief says "beat 0.3195". The live public leaderboard, read with `fetch_page` on
    2026-10-11 (<https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>),
    has **0.4133 (xiaofanhu, 16 submissions)** at rank 1 and **0.3195 (DARD) at rank 8**. The two
    figures the brief quoted as conflicting tops (0.3774, 0.3195) are not rank 1 on the live table.
    Consequence: every margin, every "beat the target" statement and the marginal-inclusion bar
    (α·DTI₀ = 0.2 × 0.4133 = **0.0827**, i.e. a dot only pays within **2.752 px = 275 m**) are
    recomputed against 0.4133 in this session's evidence. Recorded verbatim in
    `evidence/organizer_confirmed.json` and `docs/LEADERBOARD.md`. Also corrected: the previous
    version of `docs/LEADERBOARD.md` claimed the leaderboard was unreachable from this sandbox —
    that is true only for `bash` egress, not for `fetch_page`.

20. **IR-58-DATA-01 — the delivered feature stack contains no aeroradiometric bands, although the
    organizers say they were acquired.**
    Page 968 (<https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/>) states
    that GeoDAWN combines USGS EarthMRI and DOE Office of Geothermal **aeromagnetic and
    aeroradiometric** surveys with coordinated **3DEP lidar**, and that "most faults in the GeoDAWN
    region of Nevada are more subtle, and many are hidden below the surface, requiring geophysical
    data to detect". The 19 bands actually delivered in `training_features.tif`
    (sha256 `4371c82e…123bc5`, verified locally) are cond_surf, depth_to_base_surf, det_elev(+slope),
    geod_dilaterate/shearrate/2ndinv, iso_grav_anom(+slope/hg/vg), deq/ieq_n100a15, rtp/tmi/tmi_hg/
    tmi_vg/tc, mag_anom and earthquake density/distance — **no eK, eU, eTh or total-count channel and
    no 1 m lidar derivative**. Potassium metasomatism, silicification and Fe-oxide staining are the
    classic radiometric expression of a hidden fault, and scarp morphology is the classic 1 m lidar
    one, so the physically strongest discriminator named by the organizers is absent from the data
    they provided. The releases exist and are linked
    (<https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>,
    <https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7>,
    <https://www.usgs.gov/3d-elevation-program/about-3dep-products-services>) but **cannot be fetched
    from this sandbox**: `bash` egress is limited to github.com/codeload/api.github.com/pypi, and
    `fetch_page` returns text only, so no binary product can be retrieved or verified. Action:
    recorded as an **owner-download hypothesis with verified links** (H58-R3), never as a validated
    candidate, and no number in this repository is derived from it.

21. **IR-58-UNIQ-04 — the lane's uniqueness screen measured both overlap directions backwards.**
    The parallel-run protocol defines the stop statistic as "more than 70 % of **my** dots within
    3 px of **one** registry raster's dots", and requires it to be checked on the pre-placement
    surface *and* on the final dots. `src/gems58w/uniqueness.py` computed the fraction of *their*
    dots within 3 px of *mine* and called that `forward_overlap`, naming the protocol's actual
    statistic `reverse_overlap`; the dense-prior exemption was consequently applied to the wrong leg.
    The definitions now live once, in `src/gems57/uniqueness.py`, and the lane module imports them
    (no private fork). Consequence: **every overlap number this lane published before 2026-10-11 was
    measured with the two directions exchanged** — including the "worst 3 px forward overlap 0.3600"
    quoted for the earlier 38,000-dot ribbon file — and has been re-measured with the corrected
    instrument in `evidence/ribbon/emission.json`. The template-level registry scanner
    (`scripts/check_uniqueness_registry.py`, `_near(support)[my_support].mean()`) already had the
    direction right, so the sibling lane's frozen-inventory numbers were unaffected. Regression test:
    `tests/test_uniqueness_informative.py::test_forward_overlap_is_my_dots_near_theirs`.

22. **IR-58-UNIQ-03 — the literal 0.70 gate cannot be cleared by any candidate, so a literal firing
    is not evidence of duplication.**
    Extends IR-58-UNIQ-01/02 with a decisive measurement: for a blanket or lattice witness the
    *chance-level* expected overlap `E` — the fraction of the footprint within 3 px of the witness's
    dots — is ≥ 0.99, so **every** nonempty candidate overlaps it by more than 0.70 and the gate
    fires on information-free witnesses (`evidence/buffer_overlap_scan.json`: worst 0.99997, no buffer
    from 3 to 10 px clears 0.70). The shared summariser now reports, per witness, `E`, the
    chance-corrected lift `(observed − E)/(1 − E)`, a `saturated` flag (`E ≥ SATURATED_E = 0.99`), a
    representation class, and two readings side by side: the **literal** one the protocol names and
    an **informative** one that excludes saturated witnesses. `lane_drift_evidence` distinguishes
    `none` / `vacuous-only` / `informative`, and a file can only be `cleared` when no *informative*
    witness fires — a vacuous firing is labelled, never used as clearance and never used as
    condemnation. Verified by `tests/test_uniqueness_informative.py` (7 tests, synthetic blanket and
    sparse witnesses built from footprint-safe blocks).

23. **IR-58-UNIQ-05 — the shared scanner rejected the organizer's own submission representation.**
    `data/official/sample_submission.tif` carries **7,111,787 NaN pixels outside the study footprint**
    with `nodata=nan` and finite values inside it, which is exactly what page 967 requires ("outside
    the study area: null/NaN"). `scripts/check_uniqueness_registry.py:_init` demanded an all-finite
    candidate, so earlier artifacts had to be published as `*-zeros.tif` variants that do **not**
    match the official representation. Fixed once in the shared tool: a non-finite value **inside**
    the footprint stays a hard error (that is precisely the portal rejection
    `Predicted values must be in range [0, 1]` the owner already hit), a non-finite value **outside**
    it is normalised to 0 for statistics that are footprint-restricted anyway, and the receipt
    records both counts. The delivered candidate uses the official representation
    (NaN outside, 0 inside, 1.0 at dots).

24. **IR-58-LIVE-01 — no dot-field statistic predicts the owner-quoted live scores.**
    78 owner-quoted scores (`registry/live_scores_owner_reported.csv`) were matched to registry
    rasters and re-measured from sha256-verified bytes. The first attempt was garbage because the
    matcher used `re.findall(r"[0-9a-f]{8,}")` on the label, which also matches ISO dates
    (`20261003`), collapsing 78 labels onto 33 rasters with up to 102 "matches" each and producing
    R² = −0.999. The matcher is now repository-scoped and fail-closed (hash tokens ≥ 10 hex chars
    with ≥ 3 letters, repository inferred from the quoted site URL, ambiguous rows dropped, rasters
    with conflicting quoted scores excluded): **66 distinct rasters measured, 12 rows dropped, 0
    score conflicts**. Result (`evidence/live_evidence_fit.json`, verdict **NEGATIVE**): the
    two-parameter catalogue-proximity model `s = κM′/(0.2n′ + 0.8G)` fits with **R² = −1.27** and G
    pinned at its search bound, and **no covariate reaches |Spearman| 0.30** (best: median
    off-catalogue distance +0.258, frac ≤5 px −0.235, dots on catalogue −0.211). The earlier
    session-2 claim `Spearman(dots, score) = −0.831` is an n=20 artifact; over the corrected 66
    files it weakens to +0.044 and must not be reused. Because the organizers will not disclose
    public-subset membership (thread 11550), this is unfixable locally. Action: the emission budget
    is taken from the measured **family** (median dot count of the owner-reported ≥ 0.24 files =
    **40,768**, n = 12) and labelled USER-REPORTED-SCORE, never as a calibrated optimum, and no
    holdout-calibrated credit bar is used to set a live budget.

25. **IR-58-SIGMA-01 — the lane's tight-line branch is unreachable, and σ was previously fitted on
    the folds it scored.**
    `gems58w.sigma` floors σ at 0.5 px, and every measured stratum sits far above it: pooled median
    σ **6.88 px** (rms 8.01, 994 matched components), block medians NW 7.08 / NE 6.79 / SW 5.79 /
    SE 8.54. The rule "single tight line where σ < ~0.5 px" can therefore never fire, and the
    adaptive planner returned 5 lines for 5,794 of 6,286 segments and 3 lines for 492
    (`evidence/ribbon/emission.json`). Separately, the published `evidence/ribbon/holdout_sigma.json`
    table rests on **n_pairs = 14** and was fitted on the same folds it scored. Both defects are
    fixed for this session's numbers: σ is now **leave-one-block-out cross-fitted** (the table used
    to score block *b* is fitted on the other three) and reported with per-stratum counts in
    `evidence/ribbon/adaptive_sigma.json`. Honest reading of the equal-budget contest: the gain is
    "ribbon beats tight line where σ is large" (+0.0045 in σ ∈ [3,6] px, where the tight line scores
    exactly 0) and "ribbon loses where σ is small" (−0.0014 below 1.5 px) — not "per-segment
    adaptivity", which was measured at exactly 0.000000 against a uniform 5-line ribbon
    (`AD_vs_W3` pooled delta 0.0, `evidence/ribbon/adaptive_arms.json`).

26. **IR-58-REG-01 — the pinned inventory was one raster short; it is now complete (and item 14's
    claim needed re-verification).**
    `registry/registry_refreshed.json` pins 695 rasters over 57 repository snapshots
    (generated 2026-10-10T19:58:45Z). Item 14 states that the missing pin `927dc17f…`
    (`55GEMSDOE:docs/downloads/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif`, blob
    `3b4dca15…`) had already been fetched and cached. **It had not:** the cache on disk at the start
    of this session held 694 rasters and that pin was absent, so every "complete inventory" claim in
    this repository was, until now, qualified by one missing witness. It was recovered today by
    `git fetch --depth 1 origin d92606c28dc5e93ee1bce5148b92ccbb5225d023` in a fresh clone of
    `55GEMSDOE` followed by `git cat-file blob 3b4dca15…`, and the decoded bytes were verified to
    hash to the pin (1,516,449 B), so the cache now holds **695/695 pinned rasters**. A freshness delta (`scripts/registry_delta_inventory.py`) then walked the **current**
    default branches of all 56 reachable clones plus this repository's own working tree: it found
    **no** new grid-format raster in any sibling repository and 8 in this one, giving the merged
    witness inventory `registry/registry_merged.json` (**703 rasters, all byte-verified**). The
    freshness caveat in the README banner is therefore closed for the reachable public trees; it
    remains true that this is a public *sibling-repository* inventory, not an organizer registry.
