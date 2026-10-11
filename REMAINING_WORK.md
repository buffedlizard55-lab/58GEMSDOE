# Remaining work and limitations — 58GEMSDOE

> **Session 3 (2026-10-11 UTC) is the current state; session 1's list is preserved verbatim below it.**
> Read the standing prompt in `README.md` first — every session must.

## S3.0 Where the work stands right now

| Item | State |
|---|---|
| Delivered candidate | `docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`, sha256 `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd`, 433,419 B, 40,768 dots at exactly 1.0, NaN outside the footprint exactly like `sample_submission.tif`, 0 dots on the catalogue |
| Local portal preflight | **15/15 pass** (`evidence/ribbon/emission.json` → `validator`) |
| HOLDOUT-DTI of the delivered bytes | **0.043651** pooled; NW 0.046854 / NE 0.036240 / SW 0.056175 / SE 0.033176; 60,869 withheld positives; `gems58-pooled-hide-v1`; evaluator `gems58w.metric/v1`; interval 0.033176–0.056175 (min–max over 4 blocks — no bootstrap CI is claimed, because a 4-block bootstrap resamples repeated physical blocks as independent) |
| Uniqueness, local witnesses (corrected instrument) | 27 witnesses incl. this repo's own 8: worst ρ **0.1824**, worst 3 px forward overlap **0.6027** (both vs this repo's own earlier ribbon file), 0 informative firings, 0 saturated, drift `none` |
| Uniqueness, public inventory (gate G3) | **DONE and NEGATIVE.** 702 witnesses scanned (`registry/registry_merged.json`: 695/695 pinned + current-tree delta, minus the candidate's own entry), complete, 0 missing/invalid, 0 source errors. Byte-unique, pixel-unique, worst ρ **0.1824** (limit 0.90, **0** firings), worst dot-set Jaccard **0.1041** (limit 0.50, **0** firings) — but the literal 3 px forward-overlap rule fires against **81** witnesses: **54** vacuous (E ≥ 0.99, they overlap every nonempty candidate) and **27** informative, all broad dot fields of 155,021–3,380,827 dots (18 from 13GEMSDOE's near-duplicate variants). Worst informative overlap **0.8750** at E = 0.8611 (lift 0.100); max lift among the 81 firings **0.3752**; against the witnesses that can discriminate (E < 0.30) the worst observed overlap is **0.6115** (GEMSDOE50 coincidence8-80000, lift 0.4898), while at E < 0.70 there are still **7** firings (worst 0.7777 at E = 0.6456). Verdict `negative`, `stop_required` true → **logged as a duplicate and stopped**, per the standing instruction. Receipt: `evidence/ribbon/uniqueness_full_inventory.json`; final run card: `evidence/ribbon/run_card_final.json`. |
| Site | `python3 scripts/build_site.py` → `docs/index.html` (banner + download at the top), `docs/executive-summary.html` (7-step how-to-submit), `docs/submit.html` (portal checklist + the range-error fix), `docs/RUN_CARD.json` |
| Slots used | **0**. The agent never uploads or selects. |

## S3.1 Remaining work, in priority order

1. **The owner's protocol decision is now the blocking item.** Gate G3 is measured and negative on the
   literal rule; gates G1, G2, G4, G5 pass and G6 can never pass here. Two options, both stated on the
   site: (a) ratify a chance-corrected uniqueness rule — in its lift form ("fire only if
   (observed − E)/(1 − E) > 0.50") this file yields **2 firings, both this repository's own
   earlier ribbon files**, and the highest lift against any other repository is **0.4898**; in its
   E-limit form the threshold must be ≤ **0.61** for zero firings; or (b) keep the literal rule,
   under which no
   ridge-based emitter in this repository family can ever be submitted, because the registry already
   holds near-plane-filling witnesses. If (a) is ratified, `scripts/build_site.py` needs one change:
   pass the ratified threshold into `evaluate_gates` G3 instead of the raw `unique` flag, then the
   banner turns green and the exit status becomes 0. Do **not** re-run the 35-minute scan to decide
   this; the receipt already contains both readings.
2. **The owner's selector step.** Only the owner can spend a slot. If they do, copy the score from the
   submission page into `registry/submissions_seen.csv` with the date and the file's sha256 — that is
   the first ORGANIZER-CONFIRMED number this lane will ever have, and it retroactively validates or
   kills every projection in `docs/LEADERBOARD.md`.
3. **Coverage is the only lever that matters.** The leader's 0.4133 implies ≈0.36 weighted coverage;
   this surface reaches 0.0561 on catalogue truth, and the calibrated per-stratum credit k̂
   (0.000–0.035) sits entirely below the marginal-inclusion bar α·0.4133 = 0.0827. Ribbon geometry is
   worth +0.005 HOLDOUT-DTI at equal budget; coverage is worth ~6×. Any next session should spend its
   three experiments on *detection*, not on emission geometry.
4. **Aeroradiometric + 1 m lidar evidence (owner download required).** The stack has no eK/eU/eTh/total
   count and no lidar derivative, although page 968 says GeoDAWN acquired both. Links are verified in
   `evidence/organizer_confirmed.json`; the sandbox cannot fetch binaries. If the owner drops the
   products into `data/external/`, hypothesis H58-R3 (K-metasomatism / silicification / Fe-oxide
   staining + scarp morphology) becomes testable and is the highest-value untried idea in the repo.
5. **Cross-fitted supervised detector with per-stratum detection rate.** The ridge field is unsupervised
   and its detection rate at ≤300 m is 11.6–13.6 % of withheld truth. A supervised detector trained on
   visible faults with block cross-fitting, emitting where its calibrated detection rate exceeds the
   marginal bar, is the obvious coverage play. Session 2's PROX arm (0.2147 vs GF 0.0689 on the
   detached contest) says proximity-to-catalogue dominates geophysics *on the holdout*, which is
   exactly the trap IR-58-02 describes — do not read that as a live-score predictor.
6. **Directional σ (an error tensor instead of a scalar).** σ is currently isotropic across strike.
   Along-strike error and dip-dependent expression are unmodelled; a 2×2 tensor per stratum would let
   `allocation.plan` place lines anisotropically.
7. **Regenerate the ribbon subsite.** `docs/ribbon/` still describes the v1 38,000-dot file and was
   built by `scripts/ribbon_build_site.py` from `evidence/ribbon/run_card.json`. It is now an archive;
   the main site is authoritative. Either re-point that builder at `run_card_v2.json` (its expected
   schema differs: `raster_bytes`, `registry`, `catalogue_distance_profile`, `validator.checks`) or
   leave it clearly labelled as the v1 archive.
8. **`scripts/chance_coverage.py` is stale** (hardcodes `~/.cache/gems-data/sample_submission.tif` and
   an old CSV schema) and `scripts/chance_corrected_uniqueness.py` is hardcoded to one candidate and
   `row["file"]`. Rewrite or delete; neither is used by the current pipeline.

## S3.2 Limitations of everything above

- **No organizer receipt exists**, so no score is claimed anywhere. HOLDOUT-DTI measures recovery of
  catalogue truth; the competition scores new faults whose provenance the organizers will not
  disclose (thread 11527). The two are not the same quantity and no bridge between them is measurable
  locally.
- **The mandated holdout cannot score an off-catalogue file** (IR-58-02): withheld truth *is*
  catalogue, so a full-catalogue 3 px margin gives HOLDOUT-DTI exactly 0. The delivered file drops
  only *on*-catalogue dots (inert per thread 11516), which is why its HOLDOUT-DTI is non-zero.
- **σ is large and censored.** Pooled median 6.88 px with an estimator that floors at 0.5 and caps at
  6.0 px; components whose nearest withheld segment is beyond the search window are recorded as
  unreachable. The lane's "tight line where σ < 0.5 px" branch is unreachable by construction
  (IR-58-SIGMA-01).
- **The adaptive plan barely adapts.** 5,794 of 6,286 segments got 5 lines and 492 got 3; AD was
  *identical* to a uniform 5-line ribbon (pooled delta 0.000000). The measured gain is "ribbon vs
  tight line", not "per-segment adaptivity".
- **Live-score calibration is a measured dead end** (IR-58-LIVE-01): R² = −1.27, no covariate above
  |Spearman| 0.258 over 66 verified rasters, because subset membership is undisclosed. The 40,768-dot
  budget is the median of the owner-reported ≥0.24 family — a family match, not a calibrated optimum.
- **The witness inventory is a public sibling-repository inventory**, not an organizer registry: 703
  byte-verified rasters from 56 reachable clones' current default branches plus this repository's own
  working tree. Private, renamed or deleted repositories are out of scope by construction.
- **Two CPUs, ~3 GB RAM.** The full scan takes ~30–40 minutes at `--workers 2`; anything wider
  thrashes. The feature stack must be streamed, never loaded twice.

## S3.3 Do not re-run (measured negatives)

- Two-parameter catalogue-proximity calibration of live scores (R² = −1.27).
- SGMC-differential as held-out truth: provenance unverified (GeMS link HTTP 500, the sibling file is
  a ~1 px dilation carried by 5+ repos) and `gemsdoe29-sgmc-off-catalogue-44k` scored **0.0512** ≈ random.
- Unheld-budget density sweeps (+0.025 claimed vs +0.0006 at equal budget).
- Blurring a belief field before a max-coverage emitter (sibling H34, negative).
- CTX (distance-to-catalogue as a feature): the model collapses onto the catalogue (IR-58-CTX-01).
- Any catalogue margin on the delivered file: it zeroes the holdout by construction (IR-58-02).
- Re-introducing the 90° across-strike bug in `src/gems58w/ridges.py`, the swapped overlap directions
  in `src/gems58w/uniqueness.py`, or a private fork of any `src/gems57/` tool.

---

# Remaining work and limitations — 58GEMSDOE session 1 (2026-10-11)

**Status of the delivered artifact**
`docs/ribbon/downloads/gems58-adaptive-ribbon-38000-20261011T000000Z.tif`
(sha256 `d631b4af205bd6e0961f4bad3f4d12bc27b651a020dcd38666e4c5f5246720f7`):
download **OK**, submit **your decision**, **zero competition slots spent by this project**.
15/15 local acceptance checks pass, 0 duplicates against the registry, 38,000 dots, all exactly
`1.0`, no `NaN` inside the footprint.

## 0. Merge status and scope of the uniqueness claim

This lane is merged into `main` (PR #11, merge commit `967f400`) and namespaced so it sits beside
the other lanes: code in `src/gems58w/`, scripts as `scripts/ribbon_*`, receipts in
`evidence/ribbon/`, registry metadata in `registry/ribbon/`, site in `docs/ribbon/`.

**Scope of "not a duplicate" (the single most important caveat):** the uniqueness screen in this
session ran against the **19 earlier rasters present in this checkout**
(`data/registry/rasters/`), and the worst pair was rank correlation **0.0137** / 3 px forward
overlap **0.3600** — below the 0.90 / 0.70 stop limits. The sibling lane maintains a **695-raster
frozen inventory** and found a candidate there at **100 %** 3 px overlap. This lane's file has
**not** been screened against that larger inventory, so it must not be described as cleared until
`scripts/check_uniqueness_registry.py` (main) is run against it. This is a stop-looking condition:
treat the delivered raster as **downloadable for review, not cleared for submission** until that
scan exists.

## 0b. What the merged file is

38,000 dots at exactly `1.0`, `NaN` outside the footprint, 15/15 local acceptance checks, median
catalogue distance 21.9 px, 0 dots on the catalogue, per-segment 5-line ribbon at `0, ±300 m,
±600 m` (σ-driven), lead-time note 126 characters.

## 1. The one thing that is actually blocking a higher score

**Coverage, not emission.** The lane's own measurement: 11.6 % of withheld catalogue truth falls
within 300 m of the ridge field. A file at 0.3195 with 38,000 dots needs `TP > 5,672` against a
hidden mass of ≈ 12,691 px — about **45 % weighted coverage**. Every geometry in this lane moves
the holdout DTI by at most ~0.003. The gap is a factor of four in coverage. Until a believed
surface with materially higher detection exists, no emission rule can close it. This is the same
conclusion GEMSDOE32's `score-ceiling-analysis.md` reached from the opposite direction.

**Next measurement that would change the answer:** a *cross-fitted* detector over the 19-band
stack with the withheld segments as the target, reported as a detection-rate curve per stratum.
The ridge operator used here is a fixed, unsupervised edge/ridge response; it was chosen because
the lane is about *emission width*, not detection. A supervised detector would move the detection
rate, which is the only number that matters.

## 2. Instrument limits that must be fixed before any further promotion

1. **IR-58-02 — the mandated holdout cannot score an off-catalogue file.** Its withheld truth *is*
   catalogue, so any catalogue-margin screen makes HOLDOUT-DTI read exactly 0 by construction
   (`evidence/ribbon/instrument_control.json`). The standing rule "validate on the holdout before touching
   a slot" is therefore **not sufficient** for this family of files. A holdout whose truth is a
   *held-out inventory* (e.g. a state geological survey compilation the organizer also excluded
   from the catalogue) is needed. Sibling lane `57GEMSDOE`'s `IR-57-INSTR-01`
   (Spearman(live, proxy-DTI) = −0.928) is the same obstruction measured differently.
2. **The live-evidence correlations are n = 15 and collinear** (IR-58-03). They set the *design*
   (38,000 dots, off-catalogue, median distance 19–22 px) and nothing more.
3. **No organizer receipt exists** linking any score to any hash (IR-58-01). One upload of the
   `M1` control file would convert the owner-reported ordering into a measurement, at the cost of
   one slot from the weekly cap.

## 3. Untried, ranked by expected value per hour

1. **Forward-model the aeromagnetic flight-line geometry** and regress it out of `tmi`, `rtp`,
   `tmi_hg`, `tmi_vg`, `tc` before ridge extraction. The survey line spacing is coarser than the
   100 m pixel, so levelling residuals are the dominant non-fault lineament source in the magnetic
   family — the largest single source of false ridges in this lane's support. Needs only the
   survey-line geometry (public USGS GeoDAWN metadata); no new binaries.
2. **Swap the ridge operator for a cross-fitted detector** and re-run the same width test. Strictly
   better detection at the same geometry.
3. **Directional (not scalar) σ.** The kernel is isotropic, so σ as an RMS is the right *scalar*
   for the metric, but a ribbon offset along the *local* gradient direction is only optimal if the
   error is isotropic in the same frame. Measuring the error tensor per stratum and choosing the
   offset direction per segment is a strictly more general version of this lane, still inside it.
4. **Density-decay allocation** (sibling lane's H59-A): replace the flat 38,000 cap with the fitted
   annulus hazard. Cheap, and it makes the budget a measurement rather than a precedent.

## 4. What NOT to re-run (measured negatives, kept)

* Catalogue-distance screens **cannot** be evaluated on this holdout (they zero it).
* Unheld-budget density sweeps: they measure mass, not geometry. The first run overstated the
  ribbon's benefit by an order of magnitude (+0.025 vs the honest +0.0022).
* Width 4 (+6 px lines): beyond the measured σ = 1.68 px, and it does not beat width 3 by more
  than noise.
* Blurring a belief field before a max-coverage emitter (sibling H34): negative there, and this
  lane's failure mode was the geometry convention, now fixed.

## 5. Housekeeping still open

* `data/official/` holds only the two small rasters plus the template. The 419 MB stack is fetched
  by `scripts/fetch_features.sh`; nothing large is committed.
* The Pages site is static HTML rendered by `scripts/ribbon_build_site.py` from `evidence/ribbon/*.json`;
  `scripts/check_site.py` re-derives the hashes and fails closed.
* Changing Pages settings needs repository administration scope, which this integration does not
  have; the site is served from `docs/` on the default branch.
