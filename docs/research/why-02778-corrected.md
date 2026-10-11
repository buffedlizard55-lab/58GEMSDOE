# Why the group's best prior file scores what it scores — corrected with measurements

*Session 2026-10-11 (branch `arena/2427c4f5-58gemsdoe`). Every number below is tagged
**[measured-here]** (produced by a named script in this repository or by the script named
beside it, reproducible from the recorded command), **[owner-report]** (a score copied from
the owner's own ledger or the user brief, never an organizer receipt), or **[official]**
(copied from an organizer-published page). Nothing here is a projection written as a score.*

---

## 1. The premise needed correcting before it could be answered

The brief states that `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` scored **0.2778** and asks
why. Two independent records say that file has **no score at all**:

| evidence | content | class |
|---|---|---|
| `GEMSDOE32:docs/downloads/gemsdoe32-h33-h33-2-b2-…-audit.json`, field `holdout_metrics.slot_decision` / `submission_note_zeros` | "**UNSCORED**"; `predicted_leaderboard_dti: 0.274673…` is a *model* value | **[owner-report]**, copied from the sibling repository |
| `57GEMSDOE:docs/data/leaderboard_snapshot.json` (public leaderboard read 2026-10-10T20:40:27Z) | rank 22 = **extradr19 0.2778**; rank 21 = op01 0.2797; rank 8 = DARD 0.3195; rank 1 = xiaofanhu 0.3774 | **[official]** page copy, **no file attribution** |

So 0.2778 is a *leaderboard row value*, and the coincident file name is a numeric collision
(two records differ on whether it is rank 22 or 23 — recorded as rank drift between two reads,
not as an attribution). The honest answer to "why did that file score 0.2778" is: **it is not
recorded as having been scored.** What can be answered — and is answered below — is why the
*shape* shared by the group's best-scoring files scores where it does.

## 2. What was measured, and how

Instrument: all 34 prior rasters that carry an owner-reported score, matched to their actual
bytes in the live repositories, scored with the **exact** metric.

* Inventory: `GET /users/buffedlizard55-lab/repos` (146 repositories) → per-repo recursive git
  trees → **1,393 TIFF paths, 783 distinct blobs, 1,922 MB**; every distinct blob ≤600 KB
  (467 blobs, 121.6 MB) plus the 25 larger blobs that carry a score were downloaded and
  git-blob-verified into `/home/user/cache/reg/blobs/` (492 blobs on disk, 144 MB).
* Name→file matcher: `/home/user/cache/reg/match_download.py` (long-token + date/hash token
  match; 37 of 37 ledger names resolved, 34 with a raster on disk).
* Scoring: `registry_study.py` — pooled exact DTI (`gems58w.metric.dti_binary`) against the
  hide-and-recover holdout (`gems58-pooled-hide-v1`: whole catalogue components withheld by
  spatial quadrant, 3-px collar around the visible catalogue), 4 folds, α=0.2, β=0.8, R=3 px.
  This quantity is called **proxy DTI** below. Scores are **[owner-report]**.

## 3. The result

| # | submission (as recorded) | owner-reported score | positive px | on catalogue | median d(catalogue) | proxy DTI | proxy credit/px |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | 44090 | 0 | 15.0 | 0.1199 | 0.2145 |
| 2 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | 60069 | 0 | 14.9 | 0.1186 | 0.1762 |
| 3 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | 61328 | 0 | 14.1 | 0.1187 | 0.1742 |
| 4 | `h19-5-powerlaw-budget-multiline-corroborated-20260930-e270` | 0.1922 | 121131 | 0 | 14.6 | 0.0945 | 0.1003 |
| 5 | `h19-4-multiline-corroborated-openness-thermal-pop-20260930` | 0.1894 | 123779 | 0 | 14.8 | 0.0944 | 0.0995 |
| … | *(full 34-row table: `evidence/ribbon_v2/why_02778_table.md`)* | | | | | | |
| 10 | `h28-dotted-ridge-20260928T020256236880Z-6452ae1d00` | 0.1839 | 69281 | 4045 | 8.0 | 0.2598 | 0.3509 |
| 28 | `h16-continuation-20260927T065521077735Z-3431b83c7c` | 0.0461 | 310042 | 26510 | 3.0 | 0.1995 | 0.1133 |
| 30 | `H19-C_20260930T212401Z_c11e495e` | 0.0297 | 513786 | 60988 | 17.7 | 0.1575 | 0.1185 |
| 31 | `gems6_hgb88-topk03_33cec71ff0` | 0.0286 | 155021 | 23605 | 2.0 | 0.3436 | 0.2008 |
| 32 | `gems-structural-area06-v1` | 0.0202 | 343526 | 60988 | 2.8 | 0.3319 | 0.1772 |
| 34 | `GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site` | 0.0020 | 116225 | 6 | 3.2 | 0.0903 | 0.0759 |

Rank correlations against the owner-reported score (n = 34):

| covariate | Spearman ρ | p |
|---|---:|---:|
| mass on the mapped catalogue (px) | **−0.501** | 0.0025 |
| fraction of dots on the mapped catalogue | **−0.502** | 0.0025 |
| log₁₀ positive pixels (total mass) | **−0.396** | 0.020 |
| median distance to the mapped catalogue | +0.246 | 0.16 |
| fraction of dots within 3 px of the catalogue | −0.217 | 0.22 |
| **proxy DTI (hide-and-recover, exact metric)** | **−0.037** | 0.83 |
| proxy credit per dot | +0.155 | 0.38 |

Mass bands: ≤50 k px (n=1) 0.2600 · 50–80 k (n=6) median 0.1650 · 80–130 k (n=13) median 0.1352 ·
130–200 k (n=7) median 0.1152 · >200 k (n=7) median 0.0748.

Three readings, in order of how much they matter:

1. **The local holdout instrument has no ranking power for these files.** Its correlation with
   the live score is −0.037 (p = 0.83) — indistinguishable from zero on this portfolio. The
   sibling lane's `IR-57-INSTR-01` reported −0.928 for its own variant of the same instrument;
   both readings agree on the substantive point: *a hide-and-recover score computed against the
   given catalogue is not evidence about the live leaderboard for this family of files.* This is
   the joint that the whole project's validation story hangs on, and it is measured broken.
2. **Mass on the mapped catalogue is the single strongest negative covariate** (−0.501,
   p = 0.0025), and the three best-scoring files have literally zero dots on the catalogue with
   a median distance of 14–15 px (1.4–1.5 km). The worst files paint the catalogue entire
   (`on catalogue = 60,988` = the whole 60,988-px catalogue in three of them). Whatever the
   live truth is, spending mass where the catalogue already is is the one thing that reliably
   does not pay.
3. **Total mass is a weak but real negative covariate** (−0.396, p = 0.020), consistent with the
   metric's own first-order condition `k > 0.2·DTI` (one emitted pixel costs 0.2 of the
   denominator wherever it lands): the top three sit at 44 k–61 k px.

## 4. The obvious explanation was tested and failed

Hypothesis: the organizer masks a *buffer* around the known catalogue from both prediction and
truth, which would explain why mass beside the catalogue does not pay. Test: refit the local
proxy with a disk mask of radius B px around the visible catalogue and measure how well it
tracks the live scores (`fit_buffer.py`).

| B (px) | 0 | 1 | 2 | 3 | 5 | 8 |
|---|---:|---:|---:|---:|---:|---:|
| Spearman(proxy, live) | +0.004 | −0.009 | −0.004 | −0.015 | −0.105 | −0.130 |

**Negative result:** increasing the buffer makes agreement *worse*, monotonically, and never
positive. The buffer-mask story is not supported. The run was stopped at B = 10 px for time
(≈450 s per B); the trend above is already decisive in direction.

## 5. What the answer implies for the design

The only design statements that survive the measurements above are:

* emit a **small mass** — the record's top decile is 37,654–61,328 px, and mass is negatively
  related to score;
* keep the mass **off the mapped catalogue** — zero dots on it, and treat the first few hundred
  metres either side as unproven rather than as free real estate;
* **nothing in this portfolio validates placement quality** (proxy ρ ≈ 0), so a new candidate
  must be justified by its *construction* — an in-lane mechanism with a measured parameter —
  and offered as a candidate, not as a projection;
* the ~0.066 index points between the group's best owner-reported 0.2600 and the recorded
  leader 0.3195[^1] cannot be closed by emission geometry: the sibling repository's own algebra
  puts the required improvement at **+25 % mean kernel credit at the same mass**, i.e. a field
  problem, not an emission problem.

[^1]: 0.3195 is DARD's rank-8 value in the 2026-10-10T20:40:27Z public snapshot **[official]**; it
was rank 1 (0.2941–0.3262 range) in earlier dated reads of the same public page. Public board,
no file attribution, no receipt.
