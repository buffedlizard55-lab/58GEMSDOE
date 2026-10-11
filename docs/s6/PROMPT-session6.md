# Session-6 task prompt (verbatim, as received)

Stored so that every future session starts from the same contract. Read `README.md`,
`PROMPT.md` and this file at the start of each session.

---

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION
UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST
BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt. Read the
entire prompt.

Ribbon lane: match emission width to the measured localization error. The simulations say
placement within about one pixel is what pays, and that parallel dotted lines pay when location
is uncertain. On the hide-and-recover holdout, measure the across-strike distance between each
candidate ridge and the nearest withheld segment, and fit an error scale σ(x) by data block,
feature resolution and ridge type. Then choose, per segment, the number and offset of parallel
dotted lines (spacing near the 3-px kernel radius) that maximize
U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact metric. Use a single tight line
where σ is under about 0.5 px and a ribbon about ±σ wide where it is 2–3 px. Emit included dots
at exactly 1.0, since scaling values down only scales the net gain down. Report the σ table and
the simulated gain per class. Output the standard validated GeoTIFF, uniqueness-checked against
every earlier raster.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's
   rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots
   fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as
   a duplicate and stop. Check this on the surface before placement AND on the final dots.
2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and
   submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a
   buffer, derive every catalogue-based feature only from the visible faults, mask visible faults
   pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared
   tool is wrong, fix it once in the template and report it; never keep a private fork.
3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI)
   or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written
   as a score.
4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above
   [0.90] means leakage until proven otherwise.
5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that
   could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator
   output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission
   name + note of at most 140 characters; verdict promote / negative. Negative results are
   deliverables.
6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real
   slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF
submissions. These websites are researched, and tested and have generated TIF submissions. But we
need to generate high scoring submissions.

[... the full list of GEMSDOE1..62 sites and their owner-reported scores, and the public
leaderboard, is preserved in `registry/live_scores_owner_reported.csv` and
`docs/LEADERBOARD.md`; the session-6 analysis of it is in `LIVE_CALIBRATION.md`.]

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE
SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:
https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778
Why and how did this get the highest score and are we able to generate a submission that scores
higher than 0.2778? Answer the question using PhD level experience, knowledge, and judgement.
Then use the answer to generate a unique TIF submission into the competition. Must be unique
submission unlike any within the GEMSDOE sites above. Verify working line by line no
hallucinations.

Current competition leaderboard GEMSDOE high score: 0.3774 [and, later in the same brief:] 0.3195
is the highest score right now so we need to design a new strategy, research, testing, analyzing,
and generating submission system than the current website. It should be unique, take unique
approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting
point to make sure we are building what we are aiming for and have a strong base to continue
building and improving on making something useful for everyday use. It should solve the problem of
having to manually check everything ourselves and having an up to date current feed.

[Core values: Maximize P(Win); Own the Outcome.]

Work line by line verifying from official verified trusted sources, provide links for manual
review. There should be no manual input, work on your own to complete tasks. Flag any
irregularities for review. No hallucinations. Verify no hallucinations.

We need to focus on being able to generate a submission into the competition. The site should be
able to generate a TIF file that is required for submission. It should be as easy as download to
click a File to submit into the competition. This needs to be in the executive summary or the very
beginning of the site. it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the
submission form: "Predicted values must be in range [0, 1]"
Also we need to give it a unique name and A short comment to help you or your team tell
submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file
New submission
File to submit — No file chosen
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF,
with your predictions. It must match the submission format's CRS, shape, and geotransform. You may
wish to review the competition rules first.
Note (optional) — A short comment to help you or your team tell submissions apart later e.g.
clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition. The following is
the competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
We need to create a project that can compete and place top of the leaderboard. We need to
understand the problem, collect all the data and organize it into a clean easily auditable table
with official verified links for manual verification.

This is the guidelines we need to follow.
https://www.drivendata.org/competitions/306/competition-doe-gems/
Get familiar with the problem through the overview and problem description
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want
to reference additional resources available on the about page
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).
Download the data from the data tab
(https://www.drivendata.org/competitions/306/competition-doe-gems/data/).
Create and train your own model. This reference solution
(https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.
Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project. We will need to
find free publicly available sources and data from official and verified sources if we are to use
3rd party or external data.

this pdf outlines how submissions must be entered into the competition.
https://docs.nlr.gov/docs/fy26osti/96647.pdf

You must be able to do your own research, deep research, scientific literature research and
organize the knowledge so that we can critically think through the problem and generate a solution
through scientific and free publicly available information. this must be done autonomously and
must be constantly reviewed and improved upon. Provide suggestions and improvements and implement
them.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use. It
should be organized and clean. It should include all relevant information in an easy to read format
with official verified links as sources for review. Work line by line verify everything no
hallucinations.

Run this task through multiple passes.
Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases.
        Fix everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy,
        reliability, completeness, and code quality. Fix any remaining issues.
Do not stop after the first pass. Each pass must build on the previous one. Before finishing,
verify that the final result fully satisfies the original request.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions
for what work still needs to be done and any limitations that is in the way of a successful
project. It should be worked on in this next session or the next session.
