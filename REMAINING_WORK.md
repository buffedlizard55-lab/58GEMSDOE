# Remaining work and limitations — 58GEMSDOE session 1 (2026-10-11)

**Status of the delivered artifact** `gems58-ribbon-sigma168-w3-38000-20261011T000000Z.tif`:
download **OK**, submit **your decision**, **zero competition slots spent by this project**.
15/15 local acceptance checks pass, 0 duplicates against the registry, 38,000 dots, all exactly
`1.0`, no `NaN` inside the footprint.

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
   (`evidence/instrument_control.json`). The standing rule "validate on the holdout before touching
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
* The Pages site is static HTML rendered by `scripts/build_site.py` from `evidence/*.json`;
  `scripts/check_site.py` re-derives the hashes and fails closed.
* Changing Pages settings needs repository administration scope, which this integration does not
  have; the site is served from `docs/` on the default branch.
