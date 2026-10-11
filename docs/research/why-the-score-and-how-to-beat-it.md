# Why the group's best file scores what it scores — and the one measured way to beat it

*Session 2026-10-11, branch `arena/2427c4f5-58gemsdoe` (ribbon lane). Every number is tagged
`[measured-here]` (produced in this workspace by the named script), `[owner-report]` (the group's
own ledger/brief; never independently authenticated) or `[official]` (a public page). No
projection is written as a score.*

---

## 0. Which file, and what its score actually is

| quantity | value | provenance |
|---|---|---|
| the group's best file | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan`, **44,090 positive pixels**, all off the catalogue | `[owner-report]` |
| its score | **0.2600** | `[owner-report]` (no organizer receipt exists anywhere in this family) |
| public leaderboard, retrieved 2026-10-10T20:40:27Z | #1 xiaofanhu **0.3774**, #2 JerryDataWorks 0.3418, #8 DARD **0.3195**, #22 extradr19 0.2778 | `[official]` public page, no file attribution |
| the file the brief calls "0.2778" | `h33-h33-2-b2-…-e5eb6e7e-zeros` has **no organizer score**; the 0.2778 row belongs to `extradr19` | `[owner-report]` deletion of an attribution error; see `docs/ANALYSIS_H33.md` |

So "the highest score" in the brief is a **leaderboard row** (0.2778), not a file, and the
group's own best *file* is 0.2600. Everything below is about why a ~44 k-pixel binary dot field
sits at ~0.26 and what the measurements say about moving it.

## 1. The metric is a budget, and the budget rule is one line

`[official]` `DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw)` with a 300 m triangular kernel
(`R = 3 px` at 100 m). Because the kernel is normalised, `FNw = |G| − TPw` exactly
(`[measured-here] tests/test_metric.py`, brute-force check at 1e-9), so with `S` = emitted mass

```
DTI = T / ( 0.2·(T + S − M) + 0.8·|G| )
```

and the marginal rule is simply

```
a unit of mass pays  ⟺  its kernel credit  >  0.2 · DTI
```

`[measured-here] scripts/ribbon_verify_theorems.py`. At the group's 0.2600 the bar is **0.0520**;
at the leader's 0.3774 it is **0.0755**; at the DARD target 0.3195 it is **0.0639**. This is not a
heuristic — it is the metric's own first-order condition, and it is why *emission*, not model
architecture, has been the family's strongest lever.

## 2. Why the *thinnest* member of the family won

`[owner-report]` The same H19-5 field was emitted at three densities:
121,131 px → 0.1922, 60,069 px → 0.2477, **44,090 px → 0.2600**. Thinning raised the mean
realised credit of the surviving mass from 0.0520 to **0.0893** (+72 %) by deleting the pixels
whose credit was already below the bar — each of those was *costing* `0.2 − w` per unit.

`[measured-here]` The registry study over **34** score-bearing rasters fetched from the live
repositories (`evidence/ribbon_v2/registry_study.json`, `why_02778_table.md`) shows the same law
across independent files, with exact Spearman rank correlations against the owner-reported score:

| covariate | ρ | p |
|---|---:|---:|
| mass on the mapped catalogue (px) | **−0.501** | 0.0025 |
| positive pixels (total mass) | **−0.396** | 0.0203 |
| median distance to the catalogue | +0.246 | 0.161 |
| credit per dot (proxy) | +0.155 | 0.380 |
| **the local hide-and-recover proxy DTI** | **−0.037** | 0.834 |

Mass bands: ≤50 k px (n=1) 0.2600 · 50–80 k (n=6) median 0.1650 · 80–130 k (n=13) 0.1352 ·
130–200 k (n=7) 0.1152 · >200 k (n=7) 0.0748. The single worst file
(`Hedge-v2`, 0.1563→0.0748-band member) paints **all 60,988 catalogue pixels**; the three best
paint **zero** of them and sit a median 14–15 px (≈1.4–1.5 km) away.

Two conclusions survive this, and they are the spine of the strategy:

1. **The metric charges every emitted pixel `0.2` and only pays for proximity.** The optimal
   emission is therefore small, binary, and *off* the mapped catalogue.
2. **The local hide-and-recover instrument cannot rank these files** (ρ = −0.037). It is
   *structurally* blind: its withheld positives are catalogue pixels, while every good live file
   is screened off the catalogue — so an off-catalogue file reads 0.0 on it by construction
   (IR-58-02). Any design decision made on that instrument alone is a coin flip; this is exactly
   the drift that the sibling repository measured as −0.928 with its own variant of the same
   instrument `[owner-report]`.

## 3. What the record says is *not* the missing piece

* **Not mass.** Adding mass is negative on both theory (0.2/px) and evidence (−0.396).
* **Not catalogue proximity.** The best files are the *farthest* from the catalogue.
* **Not a better public catalogue.** QFaults v2 (the newest public compilation) lies within 300 m
  of the given catalogue for 59,064 of its 59,065 pixels `[measured-here]` — the catalogue is
  already complete for Quaternary faults.
* **Not detector sharpness alone.** The sibling's own arithmetic: at 44,090 px, reaching 0.3262
  needs the mean credit of the emitted dots to rise 0.0893 → **0.1120 (+25 %)** — a field
  precision problem, not a rasterisation problem.

## 4. The one emission-side elevation with a paired measurement behind it

`[owner-report]` The sibling's H28 truth model puts the hidden set at ≈12,691 px **scattered
around** the true fault surface with a **1.85 px** scale, and the same repository measures, on
paired draws under the official metric:

| candidate at 44,090 px | mean official DTI (live-anchored model) | paired difference |
|---|---:|---:|
| incumbent: raster-order dot-thinning of the surface | 0.2791 | — |
| greedy max-coverage of the **surface** | 0.2758 | −0.0033 (0/12) |
| **greedy max-coverage of the scatter-smoothed field** | **0.3038** | **+0.0247 ± 0.0005 (12/12)** |

The mechanism is one sentence: *the judge credits each truth pixel with the maximum kernel value
over predictions, so the thing worth covering is the truth's density, not the detector's line.*
Blurring the field by the scatter scale before covering it is the difference between spending
mass on a 1-px line that the truth has left and spending it on the 3–5 px band the truth
actually occupies.

**This is the emission this session implemented** — `scripts/ribbon_build_scatter_lane.py`,
`scripts/ribbon_build_novel_lane.py` — using the lane's own machinery (the cached 19-band ×
3-scale Hessian ridge field, the catalogue margin, the exact metric, the registry screen) and the
metric's own stopping rule (place a dot while its marginal expected credit exceeds `α·DTI₀`).
Two files came out of it, both in `docs/ribbon/downloads/`:

| file | what it is | registry screen |
|---|---|---|
| `gems58-scatter-cover-44090-…` | the rule applied to the whole scatter support | flags against **the lane's own earlier 5-line file** (77 % of dots within 3 px of it) — logged as a duplicate, **not** the deliverable |
| `gems58-novel-scatter-44090-…` | the same rule with a novelty constraint: every dot ≥3 px from every dot of the earlier lane file | the deliverable: it adds mass the lane has never emitted, which is also what the two-round objective pays for |

## 5. What is claimed, and what is not

**Claimed.** The emission rule above is the best-measured one in the family record; the delivered
file is a unique raster (0 % 3-px overlap with the lane's earlier file by construction, screened
against the current registry), format-valid under the portal's own contract, and small enough to
sit in the mass band that scores best (`[owner-report]` 44,090 px ↔ 0.2600).

**Not claimed.** No score. The lane's holdout reads 0.0 for any off-catalogue emission by
construction; the sibling's +0.0247 is a *model* result anchored on owner-reported numbers, and it
is quoted as such. The honest summary is: **this file is the best-understood emission the group
has, and the only way to learn its score is to submit it.**

## 6. Irregularities recorded with this analysis

* `[measured-here]` The lane's earlier deliverable is itself a **duplicate by its own stop rule**
  against the next candidate in the same lane (rank correlation 0.929, 3-px forward overlap
  1.000 with its 44,090-dot sibling) — logged in `evidence/ribbon_v2/run_card_equibudget_adaptive.json`.
* `[measured-here]` The frozen registry used by earlier sessions (695 rasters, 57 snapshots) is
  **stale**: the live trees now hold **1,393 TIFF paths / 783 distinct blobs / 1,922 MB** across
  61 repositories; 476 of the submission-scale blobs were fetched and sha1-verified for this
  session's screens.
* `[owner-report]` No organizer receipt exists for any file in this family; every score quoted on
  our pages is labelled as such.
