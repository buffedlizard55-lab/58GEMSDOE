# Standing user prompt — verbatim record (session 7, 2026-10-11)

> The README embeds this file. `PROMPT.md` distils it into the operating contract;
> where the two differ, this verbatim record plus the ratified protocol in
> `PROMPT.md` govern. Read both at the start of every session.

---

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt. Read the entire prompt.

Ribbon lane: match emission width to the measured localization error. The simulations say placement within about one pixel is what pays, and that parallel dotted lines pay when location is uncertain. On the hide-and-recover holdout, measure the across-strike distance between each candidate ridge and the nearest withheld segment, and fit an error scale σ(x) by data block, feature resolution and ridge type. Then choose, per segment, the number and offset of parallel dotted lines (spacing near the 3-px kernel radius) that maximize U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact metric. Use a single tight line where σ is under about 0.5 px and a ribbon about ±σ wide where it is 2–3 px. Emit included dots at exactly 1.0, since scaling values down only scales the net gain down. Report the σ table and the simulated gain per class. Output the standard validated GeoTIFF, uniqueness-checked against every earlier raster.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph above. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot.

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point.

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Create a github page for this repo that has clean ui, user friendly, simple and easy to use. The site should be able to generate a TIF file that is required for submission. It should be as easy as download to click a File to submit into the competition. This needs to be in the executive summary or the very beginning of the site. It should be obvious when you visit the site.

Also we need to give it a unique name and a short comment (at most 140 characters) to help tell submissions apart later.

Fix the portal error "Predicted values must be in range [0, 1]" — see docs/submit.html for the measured fix (all-finite float32, values in [0,1], no nodata tag).

The goal of this project is to place top of the leaderboard in this competition (DrivenData #306, DOE GEMS Prize Challenge). 0.3195 is the target to beat; the newest verified public-board read is in docs/LEADERBOARD.md.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.

Core values (kept as a focal point): **Maximize P(Win)** and **Own the Outcome**.
