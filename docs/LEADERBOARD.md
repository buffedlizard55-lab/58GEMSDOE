# Public leaderboard observations and H33 attribution

**Evidence class:** `PUBLIC-LEADERBOARD-SNAPSHOT`. These are participant rows from a dynamic public
board; they do not identify a TIFF, file hash, private score, or organizer receipt.

## Snapshot observed 2026-10-11

The official [DrivenData GEMS public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
was fetched during the 2026-10-11 review. The UTC clock was sampled immediately after fetching the page text (approximate observation marker `2026-10-11T18:33:10Z`, not a server timestamp). The reviewed rows were:

| Rank | Public participant row | DTI | What it establishes |
|---:|---|---:|---|
| 1 | `xiaofanhu` | 0.4133 | Public-board participant row only. |
| 2 | `cfld__` | 0.3585 | Public-board participant row only. |
| 8 | `kinghorton42` | 0.3261 | Public-board participant row only. |
| 9 | `DARD` | 0.3195 | Public-board participant row only. |
| 23 | `extradr19` | 0.2778 | Public-board participant row only. |
| 30–32 | three other participant rows | 0.2747 | Repeated public value; not a unique artifact identifier. |

An earlier same-day fetch recorded DARD at rank 8. The board is dynamic; rank movement between
same-day observations is not a score change and neither snapshot is a hash-bound artifact receipt.
The current review record is [`../evidence/official_leaderboard_observation_20261011_review.json`](../evidence/official_leaderboard_observation_20261011_review.json);
the earlier capture is preserved separately at
[`../evidence/official_leaderboard_observation_20261011.json`](../evidence/official_leaderboard_observation_20261011.json).

## Why GEMSDOE32 H33 did not establish a score of 0.2778

The disputed statement conflates a public participant row with a separate owner-maintained artifact:

1. The live official board attributes **0.2778 to `extradr19`, rank 23**. It provides no H33 filename,
   submission ID, TIFF hash, or crosswalk to the GEMSDOE32 project.
2. The GEMSDOE32 [H33-2-B2 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
   labels the artifact `UNSCORED` and states no artifact in that repository has an organizer score.
   It describes 0.2747 as a model projection.
3. The owner-maintained [H33 audit record](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json)
   binds H33-2-B2 to SHA-256
   `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` and records a predicted
   leaderboard DTI of 0.27467315976932155. It is an owner format/audit receipt, not an organizer
   score receipt. Its `SLOT_ELIGIBLE` decision is not a score.
4. The public board observed during review contains other participants at 0.2747 (ranks 30–32), so
   that rounded value is not a unique artifact identifier either.

**Conclusion:** no verified evidence shows that H33 scored 0.2778. A participant-row mix-up is one
possible explanation, but the available evidence does not establish how the attribution arose or why
`extradr19` received 0.2778. Do not report 0.2778 or the owner's 0.2747 projection as an H33 organizer
score. An `ORGANIZER-CONFIRMED` score would require a receipt/hash crosswalk from DrivenData.

## Attribution register

[`../registry/submissions_seen.csv`](../registry/submissions_seen.csv) intentionally records no
numeric score for the H33 artifact. The 0.2778 row is preserved only in the dated participant
snapshot. Additional sources, retrieval notes, and the official competition task description are in
[`SOURCES.md`](SOURCES.md) and [`../docs/research/why-02778.md`](research/why-02778.md).
