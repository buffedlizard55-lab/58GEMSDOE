# H33 attribution review — 2026-10-11 evidence

The claim that GEMSDOE32's H33-2-B2 TIFF scored **0.2778** is unsupported by the verified evidence
reviewed here.

- The official public leaderboard snapshot observed on 2026-10-11 shows **extradr19 at rank 23 / 0.2778**. It is a participant row and does not name H33, a submission ID, or a TIFF hash.
- GEMSDOE32's owner-maintained page marks H33-2-B2 **UNSCORED** and calls 0.2747 a model projection. Its audit JSON binds the owner artifact to SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, but is not an organizer score receipt or a crosswalk to the public row.
- The public board also showed unrelated participants at 0.2747; rounded numerical agreement cannot identify the H33 file.

The best-supported explanation is a participant-row misattribution. The origin of the disputed claim is
unknown; this is not proof that an undisclosed private score could never exist. No artifact score is
`ORGANIZER-CONFIRMED` without a hash-bound organizer receipt.

See [`research/why-02778.md`](research/why-02778.md), [`LEADERBOARD.md`](LEADERBOARD.md), and the
[official public board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
