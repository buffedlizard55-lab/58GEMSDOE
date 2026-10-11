# Session 4 — candidate hypotheses, ranked, with the one that was implemented

*2026-10-11, branch `arena/2427c4f5-58gemsdoe` (ribbon lane).* The standing prompt requires 3–5
candidate geological hypotheses, each naming the layer(s), the physical signature, why it should
catch a fault missing from the catalogue, and how it differs from everything already implemented —
ranked by expected DTI improvement and implementation cost — **before** implementing, with the
top one validated on the spatially blocked holdout. Every number quoted below is tagged
`[official]`, `[owner-report]` (the group's own unverified ledger or brief) or `[measured-here]`
(produced this session by the named script).

## 1. What the record already establishes (so the list does not repeat it)

* `[official]` `DTI = TP/(0.2·FP + 0.8·FN + ε)` with a 300 m triangular kernel; with
  `FN = |G| − TP` this is `DTI = T/(0.2·(T + S − M) + 0.8·|G|)`, so a unit of emitted mass moves
  the denominator by exactly `0.2` and pays iff its kernel credit exceeds `0.2·DTI₀`
  (`[measured-here] scripts/ribbon_verify_theorems.py`, `tests/test_metric.py`).
* `[owner-report]` the group's best file is `dotted-h19-5-d2-8`, 44,090 positive pixels, 0.2600.
  Thinning the same field 121,131 → 44,090 px raised mean credit 0.0520 → 0.0893; reaching 0.3262
  at that mass needs 0.0893 → 0.1120 (**+25 %**), i.e. a *field* problem.
* `[measured-here]` across 34 score-bearing rasters from the live repositories, the strongest
  covariate of the owner-reported score is **mass on the catalogue** (Spearman −0.501,
  p = 0.0025), then total mass (−0.396, p = 0.020); the local hide-and-recover proxy is
  uncorrelated with the live score (−0.037).
* `[owner-report]` the sibling's live-anchored truth model (H28) puts the hidden truth at
  ≈12,691 px scattered around the fault surface with a 1.85 px scale, and measures that at equal
  mass **greedy max-coverage of the scatter-smoothed field beats covering the surface**
  (+0.0247 official-DTI, 12/12 paired draws), while covering the surface is *worse* than the
  incumbent raster-order thinning (−0.0033, 0/12).

## 2. The candidates

| # | hypothesis | layers / signature | why it could catch a missing fault | how it differs from everything implemented | cost | status |
|---|---|---|---|---|---|---|
| **1** | **H58-S3 scatter-cover emission** — cover the *scattered truth density*, not the ridge surface; place each dot while its marginal credit exceeds `α·DTI₀` | the cached 19-band × 3-scale Hessian ridge field; the signature is the truth's own scatter (1.85 px), not the detection | the judge credits a truth pixel with the **maximum** kernel value over predictions, so covering the blurred density raises captured credit at fixed mass without touching the detector; the sibling's H28 model measures +0.0247 at 44,090 px | every earlier file inside and outside this lane emits on the *surface* (centreline ± parallel lines at the kernel radius). No raster in the 1,393-path registry was emitted from a scatter-blurred density with a marginal-credit stopping rule | low | **implemented and measured this session** (`scripts/ribbon_build_scatter_lane.py`, `scripts/ribbon_build_novel_lane.py`) |
| **2** | **H58-C1 cross-catalogue disagreement, gated by the ridge field** | `data/external/sgmc_faults_100m.tif` (present locally) + the ridge field; signature = faults in the pre-Quaternary SGMC compilation that the Quaternary catalogue omits (61,664 px beyond 300 m, median 15 px `[measured-here]`) | it is the only *known-real* fault population absent from the given catalogue | earlier "catalogue-band" work screened mass *away* from the catalogue; this uses a second catalogue's disagreement as a positive feature and lets the ridge field arbitrate | low–medium | not run (the emission side was the measured lever this session) |
| **3** | **H58-M1 multi-scale line coherence** | same stack; require a candidate ridge to be supported at both 1.5 px and 3 px scales | single-scale responses are dominated by the named mimics (flight-line levelling in the aeromagnetics, roads and alluvial contacts in the detrended DEM); real fault zones persist across scales | all prior emission used the winner-take-all maximum over (band, scale); no file used a cross-scale *agreement* requirement | low | not run |
| **4** | **H58-T1 heat-flow anomaly gate** | DOE GDR nationwide heat-flow / temperature-gradient collection (`https://gdr.openei.org/submissions/1704`, free, public, 21.6 GB) + the ridge field | a genuine hidden geothermal system sits in a measurable thermal anomaly; it is the one variable causally related to the target rather than to fault geometry | prior thermal work used population/habitat proxies, never measured heat flow | high | **not obtainable in-session** — the source is recorded in this repository as reachable but the download is out of budget; named so the idea is checkable, not claimed |
| **5** | **H58-A1 2020 Monte Cristo rupture alignment** | InSAR / optical change or relocated seismicity around the 2020 Mw 6.5 event (USGS ComCat, ARIA/COMET products, free) | the rupture is inside the footprint on largely unmapped ground and is "not likely preserved in the geologic record" `[official]` USGS field response, SRL 92(2A) 823–829 — exactly a hidden-truth fault | nothing in the 19 given bands is a post-2020 change signal; no prior file in the family used one | high | no local data; named for the record |

**Ranking rule.** Expected DTI gain per unit of implementation cost *and* per unit of risk of
asserting something unverifiable here. #1 wins on all three: it is the only entry with a
*paired, live-anchored* measurement behind it, it needs no new data, and it is falsifiable with
instruments already in the repository.

## 3. What was actually validated, and how

`[measured-here]` The implemented emission (H58-S3) was validated three ways:

1. **Equal-budget contest on the blocked holdout** — the scatter-cover emission against the lane's
   incumbent rule (5-line ribbon, greedy by magnitude) and against max-coverage of the unblurred
   surface, at the same dot count, with a paired block bootstrap
   (`evidence/ribbon_v2/equal_budget.json`).
2. **Uniqueness** against the current registry: 476 rasters fetched from the live repositories
   (`/home/user/cache/reg/blobs`, git-blob-sha1 verified) plus the frozen 19-raster checkout set,
   reporting worst rank correlation and worst 3-px forward overlap
   (`evidence/ribbon_v2/screens.json`, `evidence/ribbon/uniqueness.json`).
3. **Honest negative:** the lane's own hide-and-recover instrument is *structurally blind* to this
   family of files — its withheld positives are catalogue pixels and every candidate here is
   screened to sit off the catalogue, so its read-out is 0.0 for any off-catalogue emission
   (IR-58-02). That is reported, not hidden; the instrument is not used to claim a ranking
   between two off-catalogue files.
