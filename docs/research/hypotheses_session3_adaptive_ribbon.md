# Session 3 hypotheses (adaptive-ribbon lane) — ranked by expected DTI gain against implementation cost

> **Naming note.** Two sessions ran in parallel on 2026-10-11 and both numbered their hypothesis lists
> "session 3". This file is the **adaptive-ribbon lane** list; the sibling scatter-cover lane's lists
> are [`hypotheses_session3.md`](hypotheses_session3.md) and
> [`hypotheses_session4.md`](hypotheses_session4.md). Nothing here supersedes those, and nothing there
> supersedes this.

Required by the standing prompt *before* implementing: new geological hypotheses, each with the layers
it uses, the physical signature it looks for, why it can catch a fault **missing** from the
USGS/INGENIOUS catalogue, how it differs from what this repository already does, and a named
non-fault process that mimics it. Availability of any external data was verified before ranking —
a hypothesis whose data cannot be obtained is ranked on that fact, not on its geology.

Ranking criterion: **expected DTI gain per hour of implementation**, where the gain is measured
against the binding constraint this session established. That constraint is *coverage*: the
organizer-confirmed leader score 0.4133 implies ≈0.36 weighted coverage of the new-fault truth, the
delivered ribbon surface reaches 0.0561 weighted coverage of catalogue truth on the local holdout
(HOLDOUT-DTI 0.043651), and the calibrated per-stratum credit k̂ spans 0.000–0.035 against a
marginal-inclusion bar of α·0.4133 = **0.0827**. Emission geometry inside this lane is worth
+0.005 HOLDOUT-DTI at equal budget; detection is worth roughly six times that. So every hypothesis
below is a *detection* hypothesis unless stated otherwise.

| Rank | ID | Expected DTI gain | Implementation cost | Data available here? |
|---|---|---|---|---|
| 1 | H58-R4 | high (coverage) | medium (2–4 h) | **yes** — the 19-band stack |
| 2 | H58-R6 | medium-high (removes false ridges, frees budget) | low-medium (1–2 h) | **yes** |
| 3 | H58-R5 | low-medium (geometry, not coverage) | medium (2–3 h) | **yes** |
| 4 | H58-R3 | potentially the highest of all | high, and **blocked** | **no** — owner download required |
| 5 | H58-R7 | low (already measured as a dead end for calibration) | low | yes, but do not re-run |

---

## 1. H58-R4 — cross-fitted supervised detector with a per-stratum detection rate

**Layers.** All 19 delivered bands (`cond_surf`, `depth_to_base_surf`, `det_elev`, `det_elev_slope`,
`geod_dilaterate`, `geod_shearrate`, `geod_2ndinv`, `iso_grav_anom` + slope/hg/vg, `deq_n100a15`,
`ieq_n100a15`, `rtp`, `tmi` + hg/vg, `tc`, `mag_anom`, earthquake density and distance) plus the
multi-scale Hessian ridge field already cached in `.cache/gems58/ridge_field_v2.npz`, plus derived
across-strike and along-strike profile statistics of each ridge.

**Physical signature.** Not a single anomaly but a *combination*: a linear curvature/dilatation
feature in the detrended DEM coincident with a magnetic-gradient or gravity-gradient lineament and a
dilatational strain axis from the geodetic bands. Hidden faults in the Walker Lane express as exactly
this coincidence, because the fault is a rheological boundary that perturbs the near-surface strain
field and the basement topography even where no scarp survives.

**Why it catches a fault missing from the catalogue.** The catalogue is compiled from *mapped
surface expression*. A fault buried under young alluvium has no mapped trace but still perturbs the
potential fields and the shallow strain field, which is what the organizer's own About page says:
"most faults in the GeoDAWN region of Nevada are more subtle, and many are hidden below the surface,
requiring geophysical data to detect". A supervised detector trained on the *visible* catalogue learns
the multiband coincidence pattern, and that pattern generalises to buried segments because the
physics does not stop at the map boundary.

**How it differs from this repository.** Session 2 already fitted boosted trees
(`evidence/model_e1e2.json`, `model_e3.json`) but scored them on a *detached* contest and used the
model's probability field directly as the emission surface. The new element is the **per-stratum
detection rate**: instead of emitting where p is high, estimate `P(truth within 300 m | stratum)` by
block cross-fitting, and emit only in strata where that probability times the kernel credit exceeds
α·DTI₀ = 0.0827. That converts a ranking into a *calibrated* decision rule, which is the thing the
ribbon lane has never had.

**Named non-fault mimic.** Volcanic–alluvial contacts and caldera ring fractures produce the same
DEM-curvature + magnetic-gradient coincidence without being faults; so do dikes.

**Cost / risk.** 2–4 h. Risk: the visible catalogue is itself partly misaligned ("portions of the
existing fault data may be misaligned from the true location of the surface fault", page 967), so the
labels are noisy; block cross-fitting is mandatory, and the leakage canary must be re-run (session 2
found distance-to-catalogue at AUC 0.856, under the 0.90 line but close).

## 2. H58-R6 — regress flight-line geometry out of the magnetic bands before ridge detection

**Layers.** `tmi`, `tmi_hg`, `tmi_vg`, `rtp`, `tc`, `mag_anom`, and the *derived* flight-line
direction field estimated from the anisotropy of high-frequency residual power in `tmi`.

**Physical signature.** Aeromagnetic surveys are flown along parallel lines with a fixed spacing; the
draped sensor and the tie-line levelling leave a periodic residual whose wavelength equals the line
spacing and whose strike equals the flight direction. That residual is *not* geology, but it produces
long, straight, ridge-like curvature features that a Hessian detector cannot distinguish from a fault
without a directional prior.

**Why it catches a fault missing from the catalogue.** Indirectly but decisively: it *removes false
positives*, which frees emission budget for real ones. At a fixed budget of ~40,000 dots every dot
spent on a flight-line artifact is a dot not spent on a buried fault, and the metric charges α = 0.2
for each wasted pixel while the β = 0.8 term only rewards coverage. The delivered file's k̂ table
shows the magnetic family's credit is flat across magnitude deciles (0.0107 → 0.0122), which is what
you expect when a large share of high-magnitude ridges are artifacts rather than faults.

**How it differs from this repository.** Nothing in `src/gems58w/ridges.py` or `extract.py` is
directionally aware; the ridge field is a plain multi-scale Hessian. No prior session has estimated
or removed survey geometry.

**Named non-fault mimic.** The mimic *is* the target here: flight-line levelling artifacts and
draped-sensor terrain-following residuals. Secondary: cultural noise (power lines, pipelines) which
is also linear and directional.

**Cost / risk.** 1–2 h (a directional Fourier/wavelet filter per block, then re-detect). Risk: if the
survey geometry cannot be estimated from the data alone, the filter removes real short-wavelength
geology too — measure the held-out detection rate before and after, and keep the filter only if the
rate rises.

## 3. H58-R5 — directional σ: an error tensor instead of a scalar

**Layers.** The cached ridge field, the visible catalogue, and the withheld segments of the
`gems58-pooled-hide-v1` holdout.

**Physical signature.** Localisation error is not isotropic. A ridge detected from a dipping fault
trace is displaced mainly *across* strike and down-dip, and the displacement grows with dip angle and
with the depth of the buried segment; along-strike error is dominated by where the detector's
segmentation splits the trace. A single scalar σ (pooled median 6.88 px) averages two very different
error modes.

**Why it catches a fault missing from the catalogue.** It does not, directly — this is a geometry
hypothesis, and the honest expectation is small: the measured value of adaptivity beyond a uniform
5-line ribbon was **exactly 0.000000** (`AD_vs_W3` pooled delta in
`evidence/ribbon/adaptive_arms.json`). Its value is that it places the same budget where the error
actually is, which is worth something only once coverage improves.

**How it differs from this repository.** `src/gems58w/sigma.py` fits a scalar per stratum and
`src/gems58w/allocation.py` plans symmetric offsets. A 2×2 covariance per stratum would let `plan`
place asymmetric, rotated offsets.

**Named non-fault mimic.** Curved range-front faults and transfer zones, where the across-strike
direction rotates along the trace faster than a per-segment constant can follow.

**Cost / risk.** 2–3 h. Ranked third precisely because the expected gain is bounded by the coverage
problem: perfect geometry on 5.6 % coverage cannot reach 0.4133.

## 4. H58-R3 — aeroradiometric and 1 m lidar evidence (**blocked**: owner download required)

**Layers.** eK, eU, eTh, total count and the ratios K/Th and K/(Th+U) from the GeoDAWN
aeroradiometric survey; 1 m lidar derivatives (slope, aspect, multi-scale curvature, local relief,
and a hillshade difference-of-Gaussians) from 3DEP.

**Physical signature.** Hydrothermal alteration produces **potassium metasomatism** (K-feldspar and
sericite), **silicification** (quartz veining and sinter), and **Fe-oxide staining** (hematite/goethite
bleaching and enrichment). Each has a distinct radiometric expression: elevated eK and K/Th for
potassic alteration, depressed eTh and total count for silicification, and a characteristic eU
enrichment at the oxidised–reduced boundary. Buried faults are the conduits for exactly this
alteration, so the radiometric halo is a *direct* marker of a fault that has no surface expression at
all. Independently, a 1 m DEM resolves scarps of ~0.5 m throw that the 10 m/30 m products in the
delivered stack smooth away.

**Why it catches a fault missing from the catalogue.** This is the strongest of the five, and it is
the organizers' own framing: page 968 states that GeoDAWN combines USGS EarthMRI and DOE Office of
Geothermal **aeromagnetic and aeroradiometric** surveys with coordinated **3DEP lidar**, and that most
faults in the region are hidden below the surface. An alteration halo maps a fault whose trace is
invisible in every other channel.

**How it differs from this repository.** The delivered 19-band stack contains **no** radiometric
channel and **no** lidar derivative (verified locally; see IR-58-DATA-01). Nothing in this repository
has ever used either.

**Named non-fault mimic.** Granitic outcrops and felsic tuffs are naturally high in K and Th without
any alteration; alluvial fans concentrate heavy minerals and produce spurious eTh highs; colluvial
wedges at range fronts mimic scarps in 1 m lidar.

**Availability — verified, and it is the blocker.** The releases exist:
<https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>,
<https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7>,
<https://www.usgs.gov/3d-elevation-program/about-3dep-products-services> (session 1 counted 1,856
1 m DEM tiles over the study bounding box via the TNM Access API). But this sandbox cannot fetch
binaries: `bash` egress is limited to github.com / codeload / api.github.com / pypi, and `fetch_page`
returns text only. **Action for the owner:** download the radiometric GeoTIFFs (or the combined
GeoDAWN product) and 1 m DEM tiles for the study bounding box into `data/external/`, then this
hypothesis becomes testable inside one session. Until then no number in this repository is derived
from it, and it is recorded as an idea with verified links — never as a validated candidate.

## 5. H58-R7 — calibrating the emission budget from live scores (**measured dead end**)

Listed only so that it is not re-proposed. Hypothesis: owner-quoted live scores are predictable from
dot-field geometry, so the budget and the catalogue offset could be calibrated instead of guessed.
Measured over 66 sha256-verified sibling rasters (`evidence/live_evidence_fit.json`): R² = −1.27 for
the two-parameter model `s = κM′/(0.2n′ + 0.8G)`, G pinned at its search bound, and **no covariate
above |Spearman| 0.258**. The organizers will not disclose public-subset membership (thread 11550),
so each owner-quoted score carries unmodellable chunk luck and the calibration is unfixable locally.
What survives is the family separation at the extremes, which is why the delivered file keeps 0
on-catalogue dots and 40,768 dots (the median of the owner-reported ≥ 0.24 family) — labelled
USER-REPORTED-SCORE, never as a calibrated optimum.

---

## Validation status of each hypothesis

| ID | Validated on the spatially-blocked holdout? | Result |
|---|---|---|
| H58-R2 (adaptive ribbon from measured σ — the lane's own hypothesis) | **yes**, this session | Direction confirmed: +0.005194 HOLDOUT-DTI at equal budget (τ=0.45) with paired bootstrap 0.004482–0.006365 over four blocks; gain concentrated in σ ≥ 1.5 px, **negative** below it; per-segment adaptivity beyond a uniform ribbon measured at exactly 0.000000 |
| H58-R7 (live-score calibration) | **yes**, this session | **NEGATIVE** (R² = −1.27); kept as a deliverable |
| H58-R4, R5, R6 | no | ranked above; none has touched a slot |
| H58-R3 | no — data not obtainable here | blocked on an owner download |

No submission slot was used to validate any of these, and none will be: promotion is a separate owner
selector step within the weekly cap.
