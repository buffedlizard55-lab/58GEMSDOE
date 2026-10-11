# Standing prompt (read at the start of every session)

The full text is reproduced in [README.md](README.md#the-standing-prompt-read-at-the-start-of-every-session).
Short form, for orientation:

**Lane.** Ribbon lane — match the emission width to the measured localisation error.

**Protocol.**
1. Stay inside the lane. Rank-correlation above 0.90 with any registry raster, or more than 70 % of
   dots within 3 px of one registry raster's dots, means drift: log it as a duplicate and stop.
   Check the placement surface *and* the final dots.
2. Reuse the template's cached feature stack, holdout evaluator and submission writer. Fix a shared
   tool once, in the template; never keep a private fork.
3. Label every number HOLDOUT-DTI (evaluator version, withheld positives, 95 % CI) or
   ORGANIZER-CONFIRMED. A projection is never written as a score.
4. Leakage canary: test each feature alone on the holdout; AUC above 0.90 is leakage until proven
   otherwise.
5. End with one JSON run card: hypothesis, mechanism, the named non-fault process that could mimic
   it, holdout DTI + CI, correlation/overlap vs registry, raster sha256, validator output,
   submission name + a note of at most 140 characters, verdict promote / negative.
6. Stop after 3 experiments or 2 hours. Do not pick submissions; promotion to a real slot is a
   separate selector step inside the weekly cap.

**Standing owner requirements.** Generate a *unique* TIF submission and make it obvious whether it
is OK to download and submit. Aim for the top of the leaderboard (currently 0.3195 owner-reported).
No hallucinations; every number traced to a named script or an official link. No manual input.
Flag irregularities. Keep the site obvious about how to submit. Core values: *Maximize P(Win)* and
*Own the Outcome* — negative results are deliverables.
