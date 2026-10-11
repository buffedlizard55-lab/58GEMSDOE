# Session 3 — five ranked hypotheses that are new to this repository

*2026-10-11, branch `arena/2427c4f5-58gemsdoe`.* Each entry names the layer(s), the physical
signature, why it should catch a fault the USGS/INGENIOUS catalogue omits, and how it differs
from everything already implemented here. Ranked by **expected leaderboard gain per unit of
implementation cost**. Hypotheses that cannot be tested with data already on this machine name
the free official source and record whether that source has been checked from this sandbox.

Prior art that these must not duplicate: `docs/HYPOTHESES.md`, `docs/research/hypotheses_new.md`,
`docs/research/hypotheses_session2.md`, and the sibling repositories' H19/H23/H25/H28/H33/H34/
H53/H60 families (which the registry now holds as 1,393 measured TIFF paths).

---

## H58-S1 — Signed (asymmetric) ribbon offsets
**Status this session: implemented and measured.** `scripts/ribbon_run_signed_sigma.py`,
`scripts/ribbon_build_submission.py --shift-json`.

* **Layers.** The whole 19-band stack, through the existing Hessian ridge operator (`tc`,
  `tmi_hg`, `iso_grav_anom_hg`, `det_elev` and `det_elev_slope` dominate the winning codes).
* **Signature.** The *signed* across-strike offset μ of a withheld catalogue component from its
  nearest ridge pixel, expressed in the emitter's own across-strike convention
  (`rr = r + o·ay`, `cc = c + o·ax`). A non-zero stratum mean means the detector is **biased**,
  not merely noisy.
* **Why it should catch a missing fault.** The offset is a *property of the detector*, not of
  which faults are in the catalogue. If the DEM scarp crest sits systematically on the upthrown
  side of the mapped trace, or a magnetic lineament sits dip-shifted from the fault plane, then
  every detection is displaced the same way, and correcting the displacement raises the kernel
  credit of every emitted dot without changing which structures are targeted.
* **Differs from prior work.** Every previous emission in this portfolio is symmetric about the
  detected ridge (`0, ±R, ±2R`). No earlier session measured the sign of the error; the shared
  `gems58w.sigma` quantity is a Euclidean distance and is sign-blind by construction.
* **Cost.** Low (one measurement pass + a translation of the existing geometry).

## H58-S2 — Along-strike dot spacing under the max-over-predictions rule
**Status this session: implemented as `--along-spacing`.**

* **Layers.** Same ridge field.
* **Signature.** The metric credits each truth pixel with the **maximum** kernel value over all
  predictions, so two adjacent dots on the same centreline are redundant: the second buys
  `max(k₁,k₂) − k₁`, which is ~0 for 1-px spacing. The kernel is triangular with R = 3 px, so
  the credit a dotted line preserves falls roughly linearly in the spacing until it reaches
  `2R`.
* **Why it matters for catalogue-missing faults.** Nothing about the *target*; it is a pure
  budget reallocation. If spacing 1 is wasteful, the freed mass can pay for a second across-strike
  line, i.e. it buys accuracy about *where* the hidden fault is at the cost of resolution *along*
  it — and the hidden truth is scattered perpendicular to the structures (sibling H34/H28).
* **Differs from prior work.** The shipped emitters take every ridge pixel; `ALONG_SPACINGS` is
  defined in `allocation.py` but the shipped build never varies it.
* **Cost.** Very low (one parameter).

## H58-S3 — Kernel-matched scale selection instead of magnitude-max selection
**Status: not yet run.**

* **Layers.** Same stack, same ridge operator, all three scales (1.5 / 3 / 6 px).
* **Signature.** Today a pixel is assigned the (band, scale) with the largest *normalised
  magnitude*. The scoring kernel, however, is fixed at R = 3 px, so the *useful* scale is the one
  whose ridge half-width best matches 3 px. A matched-filter criterion would pick the scale that
  maximises expected kernel credit, not the scale with the biggest response.
* **Why it should catch a missing fault.** Wide (6 px) responses from thick sedimentary basins
  currently win the pixel and then pay the 0.2-per-pixel tax to cover a 600-m-wide band, while
  the actual scarp is 1 px wide. Re-ranking by kernel match sharpens the emission at fixed mass.
* **Differs from prior work.** The scale is chosen by argmax(magnitude) everywhere in
  `gems58w.extract`; no session has tested an alternative selection rule.
* **Cost.** Low–medium (re-rank the cached field, re-measure σ).

## H58-S4 — Spectral whitening of the magnetic grids against survey fabric
**Status: not run; needs the survey-line geometry.**

* **Layers.** `mag_anom`, `rtp`, `tmi`, `tmi_hg`, `tmi_vg`, `tc`.
* **Signature.** The GeoDAWN aeromagnetic grids carry flight-line levelling and draped-sensor
  residuals whose dominant direction is the survey azimuth. They appear as ridges parallel to
  the flight lines, which no fault occupies — the named non-fault mimic in every run card here.
* **Why it should catch a missing fault.** Not by finding one; by *stopping the emission* from
  spending its 0.2-per-pixel tax on lineaments that are guaranteed false. Precision at the top
  of the ranking is what the metric pays for.
* **Differs from prior work.** Measured negatives here include belief-field blurring and
  catalogue-band screens, but no session has regressed out the acquisition geometry.
* **Cost.** Medium. **Free official source named:** USGS GeoDAWN airborne magnetic and
  radiometric survey release
  <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
  (DOI 10.5066/P93LGLVQ, cited in the rules PDF as the feature source). **Availability check from
  this sandbox: NOT verified this session** — `usgs.gov` and `doi.org` are not on this
  environment's reachable-host list, so obtainability is *unconfirmed* and the hypothesis is
  ranked below the two that need no new data.

## H58-S5 — Thermal-anomaly gate using the DOE GDR Nevada heat-flow collection
**Status: not run; needs an external download.**

* **Layers.** All bands; the gate is applied to the *emission*, not the detector.
* **Signature.** Heat-flow / temperature-gradient well locations and their values: a genuine
  hidden geothermal system should sit in a positive thermal anomaly of the regional field.
* **Why it should catch a missing fault.** It is the one variable in the problem that is
  *causally* related to the target (a geothermal system) rather than to fault geometry, so it
  can discriminate a real unmapped fault from a scarp-shaped alluvial contact.
* **Differs from prior work.** Prior "thermal-pop" work used population/habitat proxies
  (`h19-4-…-thermal-pop`, `h30-arrangement-matched-habitat`), not measured heat flow.
* **Cost.** High. **Free official source named:** DOE Geothermal Data Repository submission 1704
  (nationwide heat-flow / well collection) <https://gdr.openei.org/submissions/1704>. **Availability
  check: recorded in this repository as reachable (a public 21.6 GB bundle exists) and *not*
  downloaded** — see `docs/IRREGULARITIES.md` item 12. It is viable but not obtainable inside
  this session's budget.

---

## Ranking, and what was actually validated

| rank | hypothesis | expected gain | cost | data already local | decision |
|---|---|---|---|---|---|
| 1 | **S1 signed ribbon offsets** | medium — raises mean credit per dot without new data | low | yes | **tested this session** |
| 2 | S2 along-strike spacing | medium — pure budget reallocation | very low | yes | **tested this session** |
| 3 | S3 kernel-matched scale | medium — sharper emission | low | yes | not run (budget) |
| 4 | S4 magnetic whitening | medium–high — removes guaranteed-false mass | medium | needs USGS survey geometry (unverified reachability) | not run |
| 5 | S5 thermal gate | high but unverifiable locally | high | needs 21.6 GB external download | not run |

The lane rule "validate the top candidate on the spatially blocked holdout before touching a
submission slot" was applied to S1 and S2 together, because S1 is a *shift* of the S2 geometry
and they were measured in the same build. The measurement that matters — the exact-metric
holdout read-out at equal budget, and the uniqueness screen against the current 1,393-path
inventory — is recorded in `evidence/ribbon_v2/` and summarised in the run card.
