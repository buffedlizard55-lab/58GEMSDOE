# 58GEMSDOE — DOE GEMS Prize Challenge

**Current decision: NOT OK TO SUBMIT — DO NOT SUBMIT.** This repository's active lane is ribbon-width
calibration against localization error for already-detected geophysical ridges. No experiment or new
candidate was run in this review. Read [`PROMPT.md`](PROMPT.md), this README, and
[`REMAINING_WORK.md`](REMAINING_WORK.md) before any future research.

The long-range research objective remains **Maximize P(Win)** through defensible localization-error
improvements. That objective is not a score forecast or permission to bypass the literal uniqueness,
leakage, holdout, and submission-evidence gates below.

## Current candidate and gates

The artifact currently under review is
[`gems58-concordance-ribbon-40768-20261011T160514Z.tif`](docs/downloads/gems58-concordance-ribbon-40768-20261011T160514Z.tif)
(and its [single-TIFF ZIP](docs/downloads/gems58-concordance-ribbon-40768-20261011T160514Z.zip)).
It has 40,768 positive pixels and SHA-256
`f709b6f12d5188e34aa3aed3b83d785b97a232224692dcdfffedaa009dee9d0d`.

- Its local format preflight passes; local format QA is **not** portal acceptance, uniqueness clearance,
a score, or submit permission. The previously reported portal `[0,1]` rejection remains unresolved.
- The saved final-dot scan records **83 literal >70% forward-overlap triggers** in a
**703-raster saved snapshot**. The snapshot is not current clearance; the independent registry audit is
**`BLOCKED_NOT_EXHAUSTIVE`**. A literal trigger is a stop, even when another statistic or chance
correction looks favorable.
- `evidence/ribbon_qualification.json` is missing. The current shared fail-closed evaluator reports
G1 local-format PASS and G2P/G3/G4/G5 FAIL. Current promotion-grade HOLDOUT-DTI, withheld-positive
count, and defensible 95% CI are **NOT MEASURED**.
- Do not upload the TIFF, select a submission slot, or treat a download link as permission. No slot was
selected or used in this review.

The live status pages are generated from the shared evaluator by `scripts/build_site.py`:
[`docs/index.html`](docs/index.html), [`docs/executive-summary.html`](docs/executive-summary.html),
[`docs/submit.html`](docs/submit.html), and [`docs/evidence.html`](docs/evidence.html). The complete
machine-readable negative decision is [`docs/RUN_CARD.json`](docs/RUN_CARD.json). Every downloadable
file is individually marked in [`docs/downloads/index.html`](docs/downloads/index.html).

A separate Session-4 R5_d3 artifact and its measured session-specific record remain archived at
[`docs/session4.html`](docs/session4.html) and [`docs/RUN_CARD_SESSION4.json`](docs/RUN_CARD_SESSION4.json).
Those results belong only to that different artifact; they are not transferred to H58-X1 or used as
this review's current HOLDOUT-DTI.

## Research status and next work

Four specific, untried ribbon-width hypotheses are ranked in
[`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md). **H58-U1**, relief-conditioned
width around the fixed existing topographic ridge surface, ranks first; it is proposed, not
implemented or validated. The three alternatives use profile shape, basin-cover context, and
along-strike centerline curvature. Each hypothesis names its features, physical mechanism, non-fault
mimics, prior-art distinction, expected uncertainty, estimated cost, and falsifiers.

A width-only change cannot discover a fault where the fixed ridge surface has no nearby trace. The
required local holdout masks known catalogue segments and is only a localization proxy; it does not
validate performance on the competition's new-fault truth. Do not start a holdout or writer until the
registry is fresh and the candidate-specific pre-placement surface clears the literal stop.

The remaining actions, in order, are:

1. Refresh and audit the public raster inventory; stop if stale, incomplete, or errored.
2. Compare the frozen placement surface against that fresh inventory. Stop if rank correlation exceeds
   0.90 **or** more than 70% of candidate dots are within 3 px of any one witness. No chance-adjusted
   or saturated-witness exception can waive a literal trigger.
3. Only after surface clearance, restore the pinned feature stack and preregister H58-U1.
4. Run each feature-alone leakage canary and then the shared buffered spatial holdout with exact
   marginal DTI. Report numeric HOLDOUT-DTI only with evaluator/version, protocol,
   withheld-positive count, and a defensible 95% CI.
5. Only after holdout clearance may a shared writer emit a candidate; independently scan final dots
   against the same fresh inventory. Never select or use a competition slot.

Experiment budget used: **0/3**. Maximum remains three experiments or two hours, with earlier stops on
uniqueness, stale inventory, leakage, or unsupported/nonpositive results.

## H33 / 0.2778 attribution and public leaderboard

The disputed **0.2778** is a `PUBLIC-LEADERBOARD-SNAPSHOT` participant row for `extradr19` at rank 23
in the 2026-10-11 observation. It does **not** establish a score for the GEMSDOE32 H33 TIFF. The
owner-maintained H33 page says H33-2-B2 is unscored and describes 0.2747 as a projection; no
submission receipt or artifact-hash crosswalk links H33 to the public row. The repository can resolve
the attribution error but cannot explain why `extradr19` received that result without its scored
artifact, submission record, and organizer evidence. Any deeper account would be speculation.

The same dated public-board observation listed xiaofanhu rank 1 / 0.4133 and DARD rank 9 / 0.3195.
These are dynamic participant rows, not scores for any TIFF in this repository. See the
[attribution review](docs/LEADERBOARD.md), the [H33 analysis](docs/ANALYSIS_H33.md), and
[`evidence/official_leaderboard_observation_20261011_review.json`](evidence/official_leaderboard_observation_20261011_review.json).

## Protocol and evidence classes

- A model result is reportable as **HOLDOUT-DTI** only when the shared evaluator/version, prescribed
  protocol, withheld-positive count, and defensible 95% CI are present.
- **ORGANIZER-CONFIRMED** applies only to a score receipt tied to the exact artifact/hash. A public
  board row is separately classified **PUBLIC-LEADERBOARD-SNAPSHOT**.
- The user's literal uniqueness rule governs. Archived RATIFIED-UNIQ-v1 reasoning is historical and
  cannot waive `rank correlation > 0.90 OR >70% of candidate dots within 3 px of one witness`.
- Use shared tools only: `gems57.evaluate_holdout`, `gems57.submission_writer`, and
  `scripts/qualification_gates.py`. Do not create a private evaluator, metric, or writer fork.
- AUC >0.90 for an individual feature is a leakage warning. Preserve negative results; never create
  an empty or fabricated candidate to bypass a gate.
- The reported portal error is unresolved. Do not infer its cause from local range checks, NaNs, or
  matching the sample raster.

For the official challenge task, DTI definition and file requirements, see the
[DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
and [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/). Survey
context: [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
Rules: [DOE GEMS Official Rules (September 2026)](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
More source notes are in [`docs/SOURCES.md`](docs/SOURCES.md).

## Reproduction and archived evidence

From the repository root, with dependencies installed:

```bash
PYTHONPATH=src python -m pytest -q
python scripts/build_site.py                  # builds red status while required gates are open
python scripts/build_site.py --strict         # expected exit 2 until all required gates pass
python scripts/build_downloads_index.py       # per-file review-only labels
python scripts/ribbon_check_site.py           # generated-site and archived-page checks
```

The current workflow renders the front door only with `scripts/build_site.py`. Do **not** run the
session-specific `gems60_build_page.py` or `build_site_v3.py` as part of the current site build;
they regenerate archived session pages. The session-5 builder retains an old front-page injection
path; the session-4 builder now writes only its archived report. Session-4 and session-5
artifacts/receipts remain for audit, are individually marked review-only in the download index, and
do not qualify the current candidate. Prior negative experiments and their unmodified receipts remain under
`evidence/ribbon/`, `evidence/gems60/`, and the historical sections of
[`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md); they are diagnostic records, not current
promotion-grade HOLDOUT-DTI.

The current fail-closed builder is `scripts/build_site.py`, which delegates gates to
`scripts/qualification_gates.py`. Do not edit generated status pages by hand; update evidence and
rebuild. See [`docs/research/session7_review_20261011.md`](docs/research/session7_review_20261011.md),
[`REMAINING_WORK.md`](REMAINING_WORK.md), and [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md) for
review details.
