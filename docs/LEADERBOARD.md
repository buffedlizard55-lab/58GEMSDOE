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
