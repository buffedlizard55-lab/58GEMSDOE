# Leaderboard and prior-submission numbers

Two kinds of number live on this page and they must never be mixed.

- **ORGANIZER-CONFIRMED** — read directly from a DrivenData page by `fetch_page` on 2026-10-11, and
  recorded verbatim in [`evidence/organizer_confirmed.json`](../evidence/organizer_confirmed.json).
- **USER-REPORTED-SCORE** — quoted in the project brief or on a sibling repository's own page. No
  receipt exists for any of them. The full list, with site URLs, is
  [`registry/live_scores_owner_reported.csv`](../registry/live_scores_owner_reported.csv); 66 of
  those files were matched to verified bytes and re-measured in
  [`evidence/live_evidence_fit.json`](../evidence/live_evidence_fit.json).

> Correction to the previous version of this page: it stated that the leaderboard and the sibling
> submission pages were unreachable from this sandbox. That is only true for `bash` egress.
> `fetch_page` reaches both, and the live table below was read from it on 2026-10-11.

## Live public leaderboard — ORGANIZER-CONFIRMED (fetched 2026-10-11, page 1 of 3)

Source: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>

| Rank | Score (DW-Tversky) | Team |
|---|---|---|
| 1 | **0.4133** | xiaofanhu (16 submissions) |
| 2 | 0.3418 | JerryDataWorks |
| 3 | 0.3361 | alexoktaba |
| 4 | 0.3333 | joeyfezster |
| 5 | 0.3300 | Batik Shirt Brothers |
| 6 | 0.3262 | nchuzhoy |
| 7 | 0.3261 | kinghorton42 |
| 8 | **0.3195** | DARD |
| 9+ | 0.3129 → 0.2797 | further rows on the same page |

**IR-58-TARGET-01.** The owner's standing target is "beat 0.3195". On the live board 0.3195 is
**rank 8**, not rank 1, and the leader is **0.4133**. Every statement in this repository about
"beating the target" is therefore restated against 0.4133. The two figures the brief quoted as
conflicting leaderboard tops (0.3774 and 0.3195) do not appear as rank 1 on the live table.

Staff answers that change how any score must be read
([thread 11550](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550)):
the public leaderboard is **pooled** over public-subset pixels, the final round re-evaluates on the
**whole GeoDAWN area**, and **subset membership will not be disclosed**. So each row above is a
single pooled index over an undisclosed pixel subset — and the same is true of every
USER-REPORTED-SCORE below, which is why no dot-field statistic predicts them
(best |Spearman| 0.258 over 66 verified rasters, IR-58-LIVE-01).

## What the leader's score implies arithmetically — PROJECTION

From the official metric (`DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε)`, kernel
`k(d) = max(1 − d/300 m, 0)`), reproduced in `evidence/ribbon/theorems.json`:

| Assumed operating score | A dot pays only if its kernel credit ≥ α·score | Max distance that still pays |
|---|---|---|
| 0.4133 (live leader) | 0.0827 | 2.752 px = 275 m |
| 0.3195 (owner's target) | 0.0639 | 2.872 px = 287 m |
| 0.2778 (best owner-reported sibling) | 0.0556 | 2.902 px = 290 m |

Random placement over the ~12,691-pixel public truth gives DTI ≈ 0.063; 0.2600 with 44,090 dots
needs ≈4,933 weighted true positives (~39 % weighted coverage); **0.4133 implies ≈0.36 weighted
coverage with near-zero wasted mass**. The delivered ribbon file reaches 0.0561 weighted coverage of
*catalogue* truth on the local holdout (HOLDOUT-DTI 0.043651). The gap is coverage, not geometry —
see the status page.

## Owner-reported sibling scores — USER-REPORTED-SCORE (no receipt)

The subset most relevant to the analysis; the full 78-row list with URLs is in
[`registry/live_scores_owner_reported.csv`](../registry/live_scores_owner_reported.csv).

| Submission (as quoted) | Score | Site | Verified bytes? |
|---|---|---|---|
| (live leaderboard top, as stated in the brief) | 0.3774 / 0.3195 — **conflicting, and both superseded by 0.4133** | — | n/a |
| h33-2-b2-e5eb6e7e-zeros | 0.2778 | GEMSDOE32 | yes |
| anderson-geothermal-pinn-38854-9b9ea4e6-zeros | 0.2750 | GEMSDOE36 | yes |
| h36-1-rung30-blind-r1-b531dae0a36f-nan | 0.2710 | GEMSDOE28 | yes |
| h27-4-solo-d28-8acb75e1-nan | 0.2708 | GEMSDOE31 | yes |
| h38-1-hf-euler-r30-r1-56a9f473edc7-nan | 0.2707 | GEMSDOE28 | yes |
| dotted-h19-5-d2-8-e56ea318af89-nan | 0.2600 | GEMSDOE25 | yes |
| d28-poisson300m-offcat-44090-91eae1ca | 0.2600 | GEMSDOE30 | yes |
| h25-1-dotted-h19-5-d1-5-989f59505db1-nan | 0.2477 | GEMSDOE24 | yes |
| gate_ortho_w0.25-40k-nan | 0.2376 | GEMSDOE49 | yes |
| h59-cover-ds-belief-b2xh33d-b79c4c61d8d8 | 0.2296 | GEMSDOE48 | yes |
| h19-5-powerlaw-budget-multiline-e27054cf-nan | 0.1922 | 19GEMSDOE | yes |
| gems-submission-20260925T001403Z-7f00890a | 0.1563 | GEMSDOE | yes |
| repo-c0-habitat-emission | 0.0041 | — | yes |
| gems6_hgb88-topk03 | 0.0286 | 6GEMSDOE | yes |

The two attributions 0.2778 (GEMSDOE32) and 0.3774 remain disputed in
`registry/submissions_seen.csv`; neither is used as a calibration target here.

**The one pattern that survives measurement:** every file scoring ≥ 0.2449 has **0 dots on the
mapped catalogue**, 37,654–61,328 dots, and a median catalogue distance of 14–20 px, while
catalogue-hugging files score 0.004–0.03. The delivered candidate matches that family by
construction (0 on-catalogue dots, 40,768 dots, median distance 19.7 px). That is a family
comparison — **not** a forecast, and the staff masking answer explains why it is plausible rather
than proving it.
