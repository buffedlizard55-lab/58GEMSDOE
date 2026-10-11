# GEMS DOE — geothermal fault localization

> **Current status (2026-10-11 UTC): NOT OK TO SUBMIT — DO NOT SUBMIT, UPLOAD, OR SELECT A SLOT.**
> The downloadable TIFF is retained for review and reproducibility only. Its local GeoTIFF
> preflight passed, but the final-dot uniqueness stop fired, the required pre-placement and
> promotion-grade qualification evidence is absent, and a reported portal `[0,1]` rejection is
> unresolved. A sample TIFF with NaNs outside its footprint does not prove this candidate will pass.

## Project goal

**Maximize P(Win), Own the Outcome.** Improve the chance of winning the DOE GEMS competition by
accurately localizing **geological faults indicative of geothermal resources** in the GeoDAWN test
region. The target is geological
faults, **not geothermal vents**. Preserve negative findings and make claims only at the evidence
level supported by a hash-bound receipt.

This review stays strictly in the **localization-error / ribbon-width lane**: it may change the
width or support assigned to already-detected ridge evidence. It may not add a detection model,
switch research lanes, or claim to recover a fault that is absent from the fixed ridge surface.
The project objective, constraints and operating protocol are recorded in [`PROMPT.md`](PROMPT.md).

## Current artifact and eligibility

- **Candidate:** `gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`
- **SHA-256:** `ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd`
- **Positive pixels:** 40,768.
- **Local checks:** the emission receipt records 15/15 format checks, and the independent on-disk
  TIFF/ZIP audit records 11/11 checks passing against the official sample grid. Both are local file
  checks only—not portal acceptance, uniqueness clearance, an organizer score, or submit authorization.
- **Final-dot registry scan:** 702 indexed rasters checked in the recorded public-inventory
  snapshot; **81 literal forward-overlap triggers** (27 informative and 54 saturated/vacuous),
  `unique: false`, `stop_required: true`. A separate freshness audit does not certify a current,
  exhaustive organizer-wide inventory. The trigger is a hard stop; no chance-corrected waiver is
  authorized.
- **Pre-placement surface gate:** no qualifying candidate-specific receipt.
- **Promotion-grade leakage canary and buffered holdout:** not qualified. The top proposed
  hypothesis is **not validated**.
- **Portal `[0,1]` error:** unresolved. No portal log/receipt is bound to this TIFF's SHA-256.
  Matching the official sample's NaN-outside representation is not proof of acceptance.

**Download only for audit/review:** [current TIFF — NOT OK TO SUBMIT](docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif) ·
[review ZIP — NOT OK TO SUBMIT](docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.zip) ·
[all downloadable artifacts and their status](docs/downloads/index.html) ·
[current website status and gates](docs/index.html) ·
[submission guide](docs/SUBMISSION_GUIDE.md).

## Disputed GEMSDOE32 H33 “0.2778” claim

The evidence does **not** show that H33 scored 0.2778. In the live public leaderboard snapshot
observed on 2026-10-11, **extradr19** was rank 23 with 0.2778; the row identifies a participant,
not a TIFF or hash. GEMSDOE32's owner page marks the named H33-2-B2 artifact **UNSCORED** and calls
0.2747 a projection. Its audit record binds H33-2-B2 to SHA-256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, but is not an organizer
score receipt and contains no crosswalk to the 0.2778 leaderboard row. The contemporaneous board
also contained unrelated 0.2747 rows. The most supportable explanation is **participant-row
misattribution**, not a verified H33 score. See the [dated attribution analysis](docs/research/why-02778.md),
[leaderboard record](docs/LEADERBOARD.md), and [official board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## Research protocol

The full rules are in [`PROMPT.md`](PROMPT.md). The operative requirements are:

1. Stay in the fixed localization-error/ribbon-width lane; keep the detected ridge surface fixed.
2. Freeze hypotheses and split logic before scoring. Test individual feature contributions for
   leakage using spatially separated, buffered folds.
3. For holdout work, buffer and withhold **whole fault segments**; derive catalogue features only
   from visible faults; mask visible faults pixel-exactly; score with shared
   `gems57.evaluate_holdout` and `gems57.submission_writer`; use pooled DTI with α=0.2, β=0.8,
   and a 300 m triangular kernel.
4. A numeric result is reportable only as **HOLDOUT-DTI** with evaluator/version, withheld-positive
   count and a defensible 95% confidence interval. Use **ORGANIZER-CONFIRMED** only for a score
   receipt with an artifact/hash crosswalk.
5. Uniqueness is a hard two-stage gate: compare the pre-placement surface and final dots to the
   registry; stop if rank correlation is greater than 0.90 or if more than 70% of candidate dots
   are within 3 px of any single registry raster. An incomplete or stale inventory is not
   clearance. Do not waive a literal trigger or substitute a chance-adjusted statistic.
6. Stop at three experiments or two hours, and sooner on a uniqueness trigger, stale/incomplete
   inventory, leakage, or unsupported/nonpositive result. Do not select a weekly slot or upload.
   A negative result is an acceptable deliverable.

## Ranked hypotheses

[`docs/research/hypotheses_new.md`](docs/research/hypotheses_new.md) ranks three **unimplemented and
unmeasured in this checkout** ribbon-width hypotheses, with layer and feature definitions,
physical signature, rationale, differences from prior code, cost, and official data availability.
They are proposals only. Signed magnetic/geodetic offsets, along-strike spacing, and adaptive
scalar-width variants have prior code or measurements and are explicitly excluded from the
“untried” list. The current top proposal is **not validated** because the hard uniqueness and
qualification gates block any holdout run.

## Key records

| Record | Purpose |
|---|---|
| [`docs/index.html`](docs/index.html) | Generated public-facing status, download warning and eligibility gates. |
| [`docs/IRREGULARITIES.md`](docs/IRREGULARITIES.md) | Current blockers and evidence corrections. |
| [`docs/LEADERBOARD.md`](docs/LEADERBOARD.md) | Dated public-board snapshots; separates participant rows from artifact scores. |
| [`docs/SOURCES.md`](docs/SOURCES.md) | Official/trusted source register and scope caveats. |
| [`REMAINING_WORK.md`](REMAINING_WORK.md) | Safe next steps; no experiment or slot action is authorized now. |
| [`evidence/ribbon/emission.json`](evidence/ribbon/emission.json) | Current candidate's local emission receipt and measured diagnostic fields. |
| [`evidence/ribbon/file_audit.json`](evidence/ribbon/file_audit.json) | Independent local TIFF/ZIP audit (11/11 checks); explicitly not portal/submit validation. |
| [`evidence/ribbon/uniqueness_full_inventory.json`](evidence/ribbon/uniqueness_full_inventory.json) | Candidate-matched final-dot scan; negative hard-stop result. |
| [`evidence/ribbon_qualification.json`](evidence/ribbon_qualification.json) | Required promotion qualification receipt; currently absent. |
| [`evidence/site_status.json`](evidence/site_status.json) | Generated exact-candidate status: local format, portal uncertainty, inventory stop and non-validation kept separate. |
| [`docs/research/qualification_gates.md`](docs/research/qualification_gates.md) | Exact hash-bound qualification contract enforced before any future emission. |

## Reproduce checks

From the repository root, install the project dependencies as documented in the packaging files,
then run:

```bash
PYTHONPATH=src:scripts python scripts/audit_current_tiff.py
pytest
python scripts/build_site.py
python scripts/ribbon_check_site.py
```

The website builder is expected to remain red while the qualification gates are blocked; generating
a status page is not a new experiment, TIFF emission, slot decision, upload, or portal validation.
