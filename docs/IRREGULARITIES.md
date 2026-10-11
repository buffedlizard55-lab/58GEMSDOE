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
14. **Supplemental pinned-raster restore remains incomplete.** The latest ribbon scan reports 694/695 pinned blobs checked, with an error row for `55GEMSDOE:docs/downloads/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif`; `complete_accessible_scan` is false. The separate fetch report also records an inaccessible `57GEMSDOE-PR6` clone. Neither fact clears the existing literal overlap failure. See `evidence/ribbon_uniqueness.json` and `evidence/registry_fetch_report.json`.
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
