# Official public leaderboard snapshot and file attribution

**Observed: 2026-10-11 UTC.** The official public leaderboard is dynamic. This is a dated observation, not a final private prize-round result and not a submission receipt for any local TIFF.

| Rank | Participant | Public DTI | Evidence class |
|---:|---|---:|---|
| 1 | xiaofanhu | 0.4133 | PUBLIC-LEADERBOARD-SNAPSHOT |
| 8 | DARD | 0.3195 | PUBLIC-LEADERBOARD-SNAPSHOT |
| 23 | extradr19 | 0.2778 | PUBLIC-LEADERBOARD-SNAPSHOT |

Source: [official DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). The selected rows and retrieval date are preserved in `evidence/official_leaderboard_observation_20261011.json`. A previous 2026-10-04 snapshot under `registry/leaderboard_history.jsonl` showed an earlier ordering; do not present that old ordering as current.

## The 0.2778 attribution

The 0.2778 number is present on the official public board for `extradr19` at rank 23 in the observed snapshot. That does **not** establish which of that participant's files earned the score, and it does **not** link the score to the similarly quoted GEMSDOE32 H33 TIFF.

The GEMSDOE32 owner-maintained [H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) states **“NO ORGANISER SCORE EXISTS”** for `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` and calls **0.2747** a model projection, not a score. The public GitHub source for that page is [`GEMSDOE32/docs/index.html`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/index.html). Neither source supplies an organizer receipt or hash crosswalk attributing 0.2778 to that H33 file.

Therefore:

- Do **not** say “the H33 TIFF scored 0.2778.” Its attribution is unverified and the current owner page explicitly says it is unscored.
- Do **not** say “0.2747 is the H33 organizer score.” The owner page labels it a model projection.
- Do **not** call 0.3195 the current leader: in the observed snapshot it is DARD at rank 8. The observed rank-1 public row is 0.4133 for xiaofanhu.
- No public-board row here is tied to the current 58GEMSDOE diagnostic raster. No submission was made, no slot was selected, and no organizer receipt exists for that raster.

A public leaderboard observation is recorded separately from an artifact score. For this repository, model-quality claims must still be labelled **HOLDOUT-DTI** with evaluator/version, withheld-positive count, protocol, and valid 95% CI, or **ORGANIZER-CONFIRMED** only from a receipt/hash crosswalk.

## Official references

- [Competition problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [GEMSDOE32 owner-maintained H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
- [GEMSDOE32 source page on GitHub](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/index.html)

---

## What the leader's score implies arithmetically — PROJECTION, never a score

From the official metric (`DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε)`, kernel
`k(d) = max(1 − d/300 m, 0)`), re-verified in `evidence/ribbon/theorems.json`:

| Assumed operating score | A dot pays only if its kernel credit ≥ α·score | Max distance that still pays |
|---|---|---|
| 0.4133 (observed rank 1) | 0.0827 | 2.752 px = 275 m |
| 0.3195 (observed rank 8) | 0.0639 | 2.872 px = 287 m |
| 0.2778 (observed rank 23) | 0.0556 | 2.902 px = 290 m |

Random placement over the ~12,691-pixel public truth gives DTI ≈ 0.063; 0.2600 with 44,090 dots needs
≈4,933 weighted true positives (~39 % weighted coverage); **0.4133 implies ≈0.36 weighted coverage with
near-zero wasted mass**. The session-3 candidate reaches **0.0561** weighted coverage of *catalogue*
truth on the local holdout (HOLDOUT-DTI 0.043651). The gap is coverage, not geometry.

## Owner-quoted sibling scores — USER-REPORTED-SCORE, no receipt

The full 78-row list with the site URL each came from is
[`registry/live_scores_owner_reported.csv`](../registry/live_scores_owner_reported.csv); 66 of those
files were matched to sha256-verified bytes and re-measured in
[`evidence/live_evidence_fit.json`](../evidence/live_evidence_fit.json). None of these numbers is an
organizer receipt for any file, and none is tied to a public-board row.

| Quoted file | Quoted score | Dots | Dots on catalogue | Median catalogue distance |
|---|---|---|---|---|
| d28-poisson300m-offcat-44090 | 0.2600 | 44,090 | 0 | 14–20 px |
| anderson-geothermal-pinn-38854 | 0.2750 | 38,854 | 0 | 14–20 px |
| h36-1-rung30-blind-r1 | 0.2710 | — | 0 | 14–20 px |
| gate_ortho_w0.25-40k | 0.2376 | 40,000 | 0 | — |
| h19-5-powerlaw-budget-multiline | 0.1922 | — | 0 | — |
| gems6_hgb88-topk03 | 0.0286 | 155,021 | 23,605 | 2.0 px |
| repo-c0-habitat-emission | 0.0041 | — | high | — |

**The one pattern that survives measurement:** every quoted file scoring ≥ 0.2449 has **0 dots on the
mapped catalogue**, 37,654–61,328 dots and a median catalogue distance of 14–20 px, while
catalogue-hugging files score 0.004–0.03. The session-3 candidate matches that family by construction
(0 on-catalogue dots, 40,768 dots, median distance 19.7 px). That is a **family comparison, not a
forecast**: over the same 66 rasters no covariate reaches |Spearman| 0.258 against the quoted scores
(IR-58-LIVE-01), because the organizers will not disclose public-subset membership.
