# Session-4 operating prompt (verbatim owner request, 2026-10-11)

Read this file, `PROMPT.md`, `README.md` and `REMAINING_WORK.md` at the start of every session.
It is the verbatim text of the request that opened session 4 and is kept in the repository so the
next session starts from the same contract instead of reconstructing it.

---

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION
UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE
OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire
prompt.

Ribbon lane: match emission width to the measured localization error. The simulations say placement
within about one pixel is what pays, and that parallel dotted lines pay when location is uncertain.
On the hide-and-recover holdout, measure the across-strike distance between each candidate ridge and
the nearest withheld segment, and fit an error scale σ(x) by data block, feature resolution and ridge
type. Then choose, per segment, the number and offset of parallel dotted lines (spacing near the 3-px
kernel radius) that maximize U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact metric.
Use a single tight line where σ is under about 0.5 px and a ribbon about ±σ wide where it is 2–3 px.
Emit included dots at exactly 1.0, since scaling values down only scales the net gain down. Report
the σ table and the simulated gain per class. Output the standard validated GeoTIFF,
uniqueness-checked against every earlier raster.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's
   rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall
   within 3 px of one registry raster's dots, you have drifted into another lane: log it as a
   duplicate and stop. Check this on the surface before placement AND on the final dots.
2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py)
   and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault
   segments with a buffer, derive every catalogue-based feature only from the visible faults, mask
   visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If
   a shared tool is wrong, fix it once in the template and report it; never keep a private fork.
3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or
   ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a
   score.
4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above
   [0.90] means leakage until proven otherwise.
5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could
   mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no
   NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of
   at most 140 characters; verdict promote / negative. Negative results are deliverables.
6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real
   slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF
submissions. These websites are researched, and tested and have generated TIF submissions. But we
need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE
SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:
[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores
higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to
generate a unique TIF submission into the competition. Must be unique submission unlike any within
the GEMSDOE sites above. Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score: 0.3774
[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)
gems-submission-20260925T001403Z-7f00890a: 0.1563

… [full owner-quoted score list is preserved verbatim in `registry/live_scores_owner_reported.csv`
and rendered on `docs/LEADERBOARD.md`; each row is labelled USER-REPORTED-SCORE, not
ORGANIZER-CONFIRMED] …

The goal of this project is to get a full list that follow our requirements. No hallucinations.
Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so
we should be able to figure out a way to score higher on the leaderboard using previous results and
scoring that we have across the sites listed above. We need to come up with distinct and unique
strategies to score higher in this competition leaderboard. We need to start doing heavy and deep
research into the part of the project that matters the most, which is the scientific discovery of
geothermal vents. We should store all of our information and knowledge that we can gather from
official verified sources. This will serve as a starting point for other projects as well. We need
to think outside the box but still be grounded in proper scientific research, we are ultimately
aiming for a top prize that many others are competing for. So it's important to be contrarian but be
smart about it. We need to find sources of data that others are over looking or areas of the project
when it comes to geothermal vents. We need to do deep research and critical thinking and come up
with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing,
analyzing, and generating submission system than the current website. It should be unique, take
unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point
to make sure we are building what we are aiming for and have a strong base to continue building and
improving on making something useful for everyday use. It should solve the problem of having to
manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a
successful project, so let's keep the Core Values and Own the Outcome as a focal point when
building, developing, researching, suggesting upgrades, and implementing the work.

**Our Core Values — Maximize P(Win)** — "Maximize the Probability of Winning": our decision making
framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the
probability that Arena succeeds. We set aside our emotions and make tough decisions in order to
maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena
first.

**Own the Outcome** — We own results end to end — not just our individual slice of the work. When
problems arise and we have the means to act, we do so without waiting for permission or assignment.
We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the
final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.
There should be no manual input, work on your own to complete tasks. Flag any irregularities for
review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations.
Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission. It should be as easy
as download to click a File to submit into the competition. This needs to be in the executive summary
or the very beginning of the site. it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the
submission form: "Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions
apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission — File to submit. You can submit a single-band GeoTIFF (.tif) file, or a .zip file
containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape,
and geotransform. You may wish to review the competition rules first.
Note (optional) — A short comment to help you or your team tell submissions apart later e.g.
clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition. The following is the
competition:
[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard. We need to understand
the problem, collect all the data and organize it into a clean easily auditable table with official
verified links for manual verification.

This is the guidelines we need to follow.
[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,
[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
You might also want to reference additional resources available on the about page,
[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,
[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
tab.

Create and train your own model. This reference solution,
[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project. We will need to
find free publicly available sources and data from official and verified sources if we are to use 3rd
party or external data.

this pdf outlines how submissions must be entered into the competition.
[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize
the knowledge so that we can critically think through the problem and generate a solution through
scientific and free publicly available information. this must be done autonomously and must be
constantly reviewed and improved upon. Provide suggestions and improvements and implement them.

See below for links from the above site. See attached files for links from the above site.
[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from
[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
(requires login) to data/

**Site creation** — Create a github page for this repo that has clean ui, user friendly, simple and
easy to use. It should be organized and clean. It should include all relevant information in an easy
to read format with official verified links as sources for review. Work line by line verify
everything no hallucinations.

**The single remaining blocker to training is data placement**: run
`bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then
`python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to
run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself. Work line by line verifying from official verified
trusted sources, provide links for manual review. There should be no manual input, work on your own
to complete tasks. Flag any irregularities for review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations.
Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix
everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy,
reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify
that the final result fully satisfies the original request. Work line by line verify everything no
hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions
for what work still needs to be done and any limitations that is in the way of a successful project.
It should be worked on in this next session or the next session. Work line by line verify everything
no hallucinations.

---

## Notes for whoever runs the next session

* The lane is fixed: **ribbon width vs measured localisation error**. Do not switch to a detector,
  ensemble, or alternate-feature lane.
* `IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT` is a *labelling* requirement, not a
  licence to clear a file that fails a gate. The banner on `docs/index.html` is generated from
  evidence; it is not hand-set.
* The portal rejection `Predicted values must be in range [0, 1]` is answered by the shared
  template's **all-finite zeros** export (`gems57.grid.write_submission(mode="zeros")`): 0 outside
  the footprint, never NaN anywhere. Session 4 exports that representation.
* `ORGANIZER-CONFIRMED` still has no entry for this repository: no receipt or hash crosswalk exists.
  Nothing on the site may be presented as a score.

---

## Result of this session (appended when the lane finished)

EXP-1 σ table: pooled median σ_across **4.30 px** (p25 2.38, p75 7.01; 1,425 matched components).
EXP-2 equal budget (44,090 dots/fold, same segments): **R5_d3 (0, ±3, ±6 px) 0.059635** beats the
tight line 0.044854 by +33 % relative; the σ-adaptive per-segment width ranks last at 0.038106.
EXP-3 delivered artifact: `docs/downloads/gems58-s4-ribbon-r5-d3-44090-20261011T175553Z.tif`,
44,090 dots, delivered-bytes HOLDOUT-DTI **0.038248** (95 % CI 0.032263–0.043873).

Gates: G1 PASS, G3 (leakage canary, worst single-feature AUC 0.8950) PASS, G4 PASS, G5 open for
ever. **G2 open**: 81 of 694 witnesses show > 70 % forward overlap, of which 53 are dense rasters
for which that test is degenerate. Verdict **NOT OK TO SUBMIT**.

Read `REMAINING_WORK.md` (section "Session 4 — ribbon lane") and
`evidence/ribbon_v3/RUN_CARD.json` before doing anything else. The one thing that matters is the
owner's decision on the uniqueness reading; nothing else is blocked on further experiment.
