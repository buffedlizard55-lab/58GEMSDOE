- **IR-58-S6-06 — `main`'s front door advertised an unscanned ML candidate as "Submission ready".**
  PR #30 (merged into `main` as `089d4b2`) rewrote `README.md` to say *"**Submission ready:** …
  Download and submit"* for `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif`
  (sha256 `40c2518802a9a220fa362be0b152f2c4c7ca753c3919624eed22a556c5769366`, 45,355 pixels at 1.0,
  RandomForest on 20 gradient features). That artifact has a **format-only** receipt
  (`docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.evidence.json`): no RATIFIED-UNIQ-v1
  screen against the 703-raster registry, no holdout receipt, no organizer receipt, and a validation
  AUC 0.7152 measured against the *catalogue* on a non-spatial split. Under the standing contract
  (gates, not labels) it is **NOT OK TO SUBMIT — REVIEW ONLY**, which is how
  [`docs/downloads/index.html`](downloads/index.html) lists it. The artifact is kept for review; the
  README and both front doors are restored to the fail-closed banner. Anyone reviewing this
  repository should read the banner and the per-file table, not a prose claim.

## Session 7 (2026-10-11) — logged while running the H7-A deep-edge sigma-ribbon lane

- **IR-58-S7-01 — the problem page's "top-of-crustal magnetic source depth estimate" band is not present under that name in the pinned stack.** The 19-band `training_features.tif` (sha256 `4371c82e…3bc5`) band descriptions name band 6 `tc` as *"Tilt angle or total curvature — magnetic field derivative for edge detection"*. The session-7 hypothesis H7-A was amended before any measurement to use `tc` as described by the file itself (a magnetic edge-detection derivative), not as a source-depth surface. The problem-description wording (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and the file's own descriptions disagree; the file's descriptions govern. Whether one of the remaining bands is the source-depth estimate under a different name is unresolved.
- **IR-58-S7-02 — the "current holdout best 0.043575" is not comparable to session-7 HOLDOUT-DTI numbers.** That value was measured with `gems58-pooled-hide-v1` (evaluator `gems58w.metric/v1`, 60,988 withheld positives, quadrant-block withholding); session 7 uses `gems61-buffered-hide-v1` (`gems57.holdout.build_buffered_holdout_context`, seeds (20,21), 22,893 withheld positives). Cross-instrument absolute DTIs are not like-for-like. The preregistered promote bar "A1 > 0.043575" was therefore **amended before EXP-3** to the same-instrument comparison (A1 vs the published session-5 concordance file re-scored on the session-7 instrument). Both readings stay published.
- **IR-58-S7-03 — the EXP-2 "budget-matched" A0 control label was wrong.** The matching loop could not reach the ribbon arm's mass (single 3-px-spaced lines across all 5,234 segments yield 20,530 dots per fold mask; the U-selected ribbon arm emitted ≈59,700). The arms differ in mass as well as geometry; the paired contrast is therefore a **whole-rule** comparison (include rule + ribbon patterns vs single-line-all), not a matched-mass one. The A1−A0 delta (+0.01553, 95% CI [0.01195, 0.01913], 4/4 quadrants) is labelled accordingly in the run card and on the site.
- **IR-58-S7-04 — the registry witness cache is complete except one unreachable raster.** 694 of 695 pinned witnesses restored byte-verified (0 hash mismatches); 1 pinned raster lives in repository `57GEMSDOE-PR6`, which returns 404 on GitHub and cannot be restored or screened. The uniqueness scan is reported as covering every *reachable* earlier raster, with the unreachable one named. A strict reading of "incomplete scan is not clearance" treats this as residual uncertainty; it cannot be resolved by re-scanning because the bytes are not published anywhere reachable.
- **IR-58-S7-05 — the first EXP-3 emission was degenerate and its clearance vacuous.** The
  implemented H7-C gap pass trimmed the lowest-strength dots inside *every* witness whose forward
  overlap exceeded 0.68 — including saturated witnesses (E ≥ 0.99 whole-footprint surfaces) that
  fire on any nonempty candidate. 76 witnesses × per-witness trims removed all 40,000 dots; the
  writer emitted a 0-dot (all-zero) raster, the screen returned UNIQUE trivially, and the run card
  initially read `promote`. Both facts are logged; that raster is retained in `docs/downloads/` as
  a labelled historical diagnostic and is not a candidate. Fixes applied before the final emission:
  the gap pass now targets only INFORMATIVE RATIFIED-UNIQ-v1 firings (rule A: O>0.70 with E<0.70;
  rule B: lift>0.50 with E<0.99), and the promote rule requires ≥ 1000 dots so a vacuous
  clearance on a degenerate raster can never read as a candidate. The preregistered H7-C text
  (tie-break preference for gap-complement dots) is narrower than the first implementation;
  the tie-break preference is what the final code enforces.

---

---

# Session 6, ribbon-width lane (2026-10-11 UTC) — new irregularities (IR-58-S6W-*)

Each item is measured in this session; the receipts are under `evidence/s6/`.

**IR-58-S6W-01 — the shipped `labels.tif` is byte-identical to `existing_faults.tif`.**
Both are sha256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`
(425,830 B, int8, values `{-1,0,1}`, 60,988 positives). So the "labels" in this checkout are the
public USGS/INGENIOUS catalogue itself and carry **no independent label information**. This is
consistent with the organizer's statement that the training labels come from the USGS quaternary
fault maps and INGENIOUS, and with the fact that the scored truth is a *different, private* set of
newly identified faults — but any code or prose that treats `labels.tif` as a second, checkable
label set is wrong. `src/gems58w/grid.py` already documents the identity.

**IR-58-S6W-02 — the mandated holdout is blind to off-catalogue emission by construction.**
The protocol's holdout withholds *catalogue* segments. A delivered raster must exclude the
*whole* catalogue (plus a collar), so its HOLDOUT-DTI is exactly `0.0` — measured, not assumed:
the first session-6 emission returned `tp = 0` on all four folds for this reason. The HOLDOUT-DTI
reported for this session's file is therefore measured on a **holdout-domain emission** (identical
support, ranking and geometry; only the exclusion mask differs). The two are labelled separately in
`evidence/s6/emit.json`.

**IR-58-S6W-03 — the ridge detector is at or below a uniform random control on this instrument.**
At an identical 38,000-dot budget per block, pooled over four folds
(`gems57.metric`, protocol `gems58-pooled-hide-v1`): uniform random **0.052737**; the
multi-family/multi-scale Hessian ridge field **0.044208** before dot isolation and **0.058061**
after. The instrument withholds catalogue faults while the leaderboard scores new, off-catalogue
faults, and the sign of the catalogue-distance term is opposite in the two populations
(`docs/s6/LIVE_CALIBRATION.md`). No detector ranking from this holdout may be carried to the
leaderboard; the geometry conclusions are safe because the bias is common to all arms.

**IR-58-S6W-04 — the registry screen covers 694 of 703 pinned witnesses, not "every earlier raster".**
`scripts/fetch_registry_sparse.py` restored 694/703 (9 unreachable in this sandbox), and the screen
also screened the 19 locally committed registry rasters; 692 unique, sha256-verified witnesses were
actually compared. The scope is recorded in `evidence/s6/uniqueness.json`.

**IR-58-S6W-05 — band 10 (`deq_n100a15`) has an extreme heavy tail, and every band has 3,061 NaNs
inside the competition footprint.** Raw `deq_n100a15`: median 621.9, 99th percentile 50,237,
maximum 4,962,515 — a mean z-score of +20 at a dot set means almost nothing, which is why the
session-6 feature scan uses percentile ranks rather than z-scores. All 19 bands share exactly
3,061 NaN pixels inside the 5,167,373-pixel footprint (0.06 %), which any per-band statistic must
handle explicitly.

**IR-58-S6W-06 — the uniqueness thresholds are dominated by plane-filling witnesses.** 54 of 692
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

**IR-58-S6W-07 — shared-tool performance defect fixed in place.** `s6_ribbon.emit` recomputed
`mask.sum()` once per ridge segment (O(budget × 12.3 M)), which made each geometry arm take ~150 s
instead of ~20 s. Replaced with a running counter in the shared script; no scoring behaviour
changed.

**IR-58-S6W-08 — `gems58w.submission.write` produces no ZIP.** The portal accepts a `.zip`
containing exactly one GeoTIFF and it is ~1,000× smaller than the uncompressed raster, so
`scripts/s6_package.py` was added to write the one-TIFF ZIP and the download receipt and to verify
the round-trip. The writer itself was left alone (it is shared).