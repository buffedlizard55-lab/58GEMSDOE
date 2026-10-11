# Why did the 0.2778 submission score highest, and can we beat it?

Subject: `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (GEMSDOE32, the "h33-h33-2-b2" candidate), user-reported score **0.2778**.

## 1. What the file is (FETCHED from GEMSDOE32, `docs/downloads/…-audit.json`)

- Description in its own audit: "0.2708 base with every dot at d(catalogue) <= 2 px deleted (37,654 dots)".
- So it is a dotted-ridge base (score 0.2708 claimed by the same team) with one operation applied: a
  **catalogue-flank prune**: every dot within 2 px (200 m) of a catalogue fault is removed.
- Output: 37,654 positive pixels; 0 on the catalogue; 5,167,373 in-footprint pixels; EPSG:32611; 3730 × 3292;
  float32. Its own checks say all passed. Their zeros and NaN variants carry identical dots.
- Evidence class of the 0.2778 score: **user-report only**. It is absent from the team's score ledger
  (`docs/score-ledger.csv`), which holds user reports and official-snapshot rows dated 2026-10-03 (rank 1 = 0.3195).

## 2. The mechanism, stated as a testable claim

Write the metric as the task brief and the official page give it: `DTI = TP / (0.2(TP+FP) + 0.8|G|)`.
Two consequences matter here (both verified by unit tests in `tests/test_dti.py`):

1. The denominator's floor `0.8|G|` is fixed by the hidden labels. Every unit of predicted mass costs
   `0.2` whether or not it earns credit. A dot earns credit only if it is the nearest strong mass to a
   hidden fault pixel within 3 px.
2. A dot near a **known** trace earns credit only if hidden labels lie within 300 m of that trace, and it costs
   FP if they do not. Removing dots near known traces therefore helps exactly when hidden labels are *away* from
   known traces.

So the 0.2708 → 0.2778 step (+0.007, user-reported) is consistent with removing FP mass in a band where the
hidden labels are absent. **The sign of this effect depends on an assumption that we cannot check here:**
whether new-fault labels lie within 300 m of known traces. A second-hand note (LEARNGEMSDOE PR #3, quoting a
forum post) says they may. The forum thread itself (11516) is unreachable from the sandbox. If that note is right,
the prune removes true credit and the 0.2778 result is partly luck. Resolve this with an organizer-confirmed
receipt, not with a holdout.

## 3. Why this file's holdout disagrees with its score (irregularity — flag for review)

The same team's holdout for this file reports `catalogue_hidden_mean = 0.0046` (its audit JSON). The
`predicted_leaderboard_dti = 0.2747` field is a **projection** (a regression from their own holdout), not a
score. The actual reported score (0.2778) is far from the holdout (0.0046). So their holdout does not predict
the leaderboard, and any selection that relies on it is unreliable until it is calibrated against organizer
receipts. The same caution applies to our holdout (below).

## 4. Can we generate something that scores above 0.2778?

**Not demonstrated, and our evidence points the other way for the lane we tested.**

- Our ribbon-lane candidates score pooled holdout DTI ≈ 0.016 and do **not** beat random placement of the same
  number of dots (pooled ≈ 0.034). See `reports/ribbon_lane_report.json` (holdout, baselines).
- A 0.2778 leaderboard score cannot be compared with our holdout numbers directly. Our holdout is a proxy, and the
  team's own holdout shows that proxies in this competition are badly miscalibrated (3.); we have no organizer
  receipts of our own to calibrate against.
- The three things that could plausibly add score, in order of how well they are supported:
  1. **Calibrate** the holdout against organizer receipts (one or two small submissions inside the weekly cap).
     Without this, no holdout result in this repo can be turned into a leaderboard projection.
  2. **Test the prune assumption** directly: score base vs. base-with-catalogue-prune on a holdout where withheld
     segments are placed near (≤ 300 m) and far from visible traces, and see which wins. This decides whether the
     0.2778 trick generalises.
  3. **Improve localisation** (σ). Our σ measurement says ridge candidates from the 100 m stack land 5–8 px off
     faults, no better than random placement (`docs/results.html`). Finer-scale raw magnetic grids (H1 in
     `docs/hypotheses.md`) are the candidate fix, but they are not reachable from this sandbox.

## 5. Verdict

- The 0.2778 result is user-reported, its mechanism is plausible but unverified, and its own holdout disagrees with
  it by a factor of 60. Treat it as a hypothesis about the prune, not as an established method.
- We have **no** validated submission that beats 0.2778. Our one candidate lane is negative on the holdout.
