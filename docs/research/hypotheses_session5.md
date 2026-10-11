# Session 5 — five ranked candidate hypotheses not yet tried in this repository

*2026-10-11, branch `arena/d7d3ba0a-58gemsdoe` (ribbon lane).* Written **before** any session-5
implementation, as the standing prompt requires. Each entry names the specific layer(s), the
physical signature targeted, why it should catch a fault missing from the USGS/INGENIOUS
catalogue rather than one already in it, how it differs from everything already implemented in
this repo and its siblings, the expected DTI improvement, and the implementation cost. Tags:
`[official]` organizer-published, `[owner-report]` the group's own unverified ledger,
`[measured-here]` produced in this repository by a named script.

Prior art these must not duplicate: `docs/HYPOTHESES.md`, `docs/research/hypotheses_new.md`,
`docs/research/hypotheses_session2.md`, `hypotheses_session3.md` (H58-S1..S5, S1/S2 run),
`hypotheses_session3_adaptive_ribbon.md`, `hypotheses_session4.md` (H58-S3 scatter-cover run;
C1/M1/T1/A1 not run), and the sibling families H19/H23/H25/H28/H33/H34/H53/H56/H57/H59/H61.

---

## H58-X1 — Cross-family concordance gate ("concordance ribbon")  ← TOP CANDIDATE

* **Layers.** The organizer's own 19-band stack, grouped by the file's `data_category` tags
  (`gems58w.features.FAMILIES`): topographic (`det_elev`, `det_elev_slope`), gravity
  (`iso_grav_anom`, `_hg`, `_vg`, `_slope`), magnetic (`mag_anom`, `rtp`, `tmi`, `tmi_hg`,
  `tmi_vg`, `tc`), subsurface (`depth_to_base_surf`, `cond_surf`), geodetic, seismic.
* **Physical signature.** Coincident (≤1 px = 100 m) NMS Hessian-ridge responses from **two or
  more independent physical families**. A real Basin-and-Range normal fault with finite throw
  juxtaposes rock density and magnetization across the plane *and* leaves a topographic scarp,
  so its trace expresses simultaneously in the horizontal-gradient of gravity, the magnetic
  derivatives, and the detrended DEM. The named non-fault mimics are each **single-family**:
  flight-line levelling residuals live only in the magnetic grids; roads, canal berms and
  alluvial-fan contacts live only in the topographic grids; smooth basin-conductivity edges
  live only in the subsurface grids.
* **Why it should catch a *missing* fault.** A fault absent from the Quaternary catalogue is
  typically absent because its surface expression is subdued (buried, eroded, or young-alluvium
  covered) — but burial does not remove the density/magnetization contrast, so the
  potential-field ridge persists where the mapped trace does not. Gating on cross-family
  agreement reallocates the fixed dot budget *away* from guaranteed-false single-family
  lineaments and toward multi-evidence structures, which is precisely where unmapped faults
  must sit. The budget algebra (`docs/research/metric.md`) says each dot pays only if its
  kernel credit exceeds `0.2·DTI₀`; raising mean credit per dot at fixed budget is the one
  measured lever (`[measured-here]` thinning 121k→44k px raised mean credit 0.052→0.089 and the
  owner-reported score 0.192→0.260 `[owner-report]`).
* **Differs from all prior work.** Every emission in this family (this repo and all 56 sibling
  clones' rasters in the 703-witness registry) selects pixels by winner-take-all argmax over
  (band, scale) of a single combined magnitude; none requires agreement between independent
  physical families. Session-4's unrun H58-M1 proposed multi-**scale** coherence within one
  band; this is multi-**family** coherence, a strictly stronger physical statement (two
  independent data acquisitions, not two filters of one grid).
* **Expected DTI improvement.** Medium–high: directly raises precision-per-dot, the quantity
  the holdout can measure; falsifiable at equal budget against the incumbent.
* **Cost.** Low–medium: one additional cached pass over the 19×3 Hessian jobs to store
  per-family NMS maxima; the σ machinery, allocator and writer are reused unchanged.

## H58-X2 — Kernel-matched scale selection (promoted from session-3 S3, never run)

* **Layers.** Same stack, same ridge operator, all three scales (1.5 / 3 / 6 px).
* **Signature.** Select the (band, scale) whose ridge half-width best matches the fixed 3-px
  scoring kernel instead of the largest normalised magnitude; 6-px basin-scale responses
  currently win pixels and then pay the 0.2 tax over a 600-m-wide band while the scarp is 1 px.
* **Missing-fault argument.** Indirect only (sharpens emission; does not change targets).
* **Differs.** `gems58w.extract` picks argmax(magnitude) everywhere; no session tested another
  selection rule. **Cost:** low. **Expected gain:** medium.

## H58-X3 — Leak-free strike-prior gate from the visible catalogue

* **Layers.** Ridge field orientation (`ax`/`ay`) + per-fold **visible** catalogue only.
* **Signature.** Basin-and-Range extension (WNW–ESE σ₃) makes fault strikes cluster NNE; the
  per-fold visible-fault strike distribution is measurable without touching withheld truth.
  Ridges striking far outside the local mode (e.g. survey-parallel E–W lineaments) are mimics.
* **Missing-fault argument.** An unmapped fault obeys the same regional stress field as the
  mapped ones; artifacts follow acquisition geometry instead.
* **Risk.** Discards transfer zones and accommodation structures (real, oblique). **Cost:**
  low–medium. **Expected gain:** medium, with a known false-negative tail.

## H58-X4 — SGMC cross-catalogue disagreement, ridge-arbitrated (session-4 C1, never run)

* **Layers.** `data/external/sgmc_faults_100m.tif` (local) + the ridge field.
* **Signature.** Faults present in the pre-Quaternary SGMC compilation but absent from the
  competition catalogue (61,664 px beyond 300 m `[measured-here]`), kept only where the
  geophysical ridge field independently corroborates them.
* **Caution.** The sibling's *direct* SGMC emission scored 0.0512 ≈ random `[owner-report]`
  (`registry/…do-not-rerun` list); this variant is a gate, not an emission, but the prior is
  weak. **Cost:** low. **Expected gain:** low–medium, high variance.

## H58-X5 — Measured heat-flow gate (session-3 S5 / session-4 T1; external data)

* Named free official source: DOE GDR submission 1704 (nationwide heat-flow collection,
  ~21.6 GB), <https://gdr.openei.org/submissions/1704>. `gdr.openei.org` is **not reachable
  from this sandbox** (allowed hosts: github.com, pypi.org, npmjs.org families), so the idea
  remains viable-but-unobtainable here and is ranked last. **Not claimed as testable.**

---

## Ranking and the validation plan

| rank | hypothesis | expected gain | cost | data local | decision |
|---|---|---|---|---|---|
| 1 | X1 cross-family concordance | medium–high | low–medium | yes | **validate on the blocked holdout this session** |
| 2 | X2 kernel-matched scale | medium | low | yes | reserve (within-budget fallback arm) |
| 3 | X3 strike prior | medium | low–medium | yes | not this session |
| 4 | X4 SGMC gate | low–medium | low | yes | not this session (weak prior) |
| 5 | X5 heat-flow gate | high if real | high | **no** | blocked on external download |

Validation rule (preregistered): X1 is emitted as σ-adaptive dotted ribbons under the exact
same budget, ranking, screen and allocator as the incumbent recipe (session-3
`gems58-ribbon-sigma-adaptive`), scored per fold on `gems58-pooled-hide-v1` with the leak-free
visible-catalogue screen, pooled. **Promote only if pooled HOLDOUT-DTI ≥ the incumbent arm's
pooled HOLDOUT-DTI measured in the same run.** No weekly slot is touched either way; slot
selection is a separate human step.

Known instrument limitation (stated in advance): the holdout's withheld truth is the mapped
catalogue, which over-represents faults *with* clear surface expression; a gate that demands
topographic corroboration could therefore score well on the holdout while the organizer's
hidden truth contains scarp-free faults. The concordance gate counts *any* two families, not
specifically topography, which bounds this bias but does not remove it.
