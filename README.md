# 58GEMSDOE — DOE GEMS Prize Challenge (DrivenData competition #306)

**Core values: Maximize P(Win) · Own the Outcome.** Every number in this repository is labelled
`HOLDOUT-DTI`, `ORGANIZER-CONFIRMED` or `PUBLIC-LEADERBOARD SNAPSHOT`. A projection is never
written as a score. Negative results are deliverables. A file is never cleared because someone
asked for one — only because the gates pass, and the gates are computed from evidence files, never
typed by hand.

> **Current repo-level verdict: NOT OK TO SUBMIT — DO NOT SUBMIT.**
> No organizer submission receipt exists for any artifact, so nothing here can be labelled
> accepted or scored. The current candidate (`gems58-concordance-ribbon-40768-20261011T160514Z.tif`,
> sha256 `f709b6f1…d0d`) is stopped by the ratified uniqueness gate — rule A fires against 9
> witnesses, rule B against 3 (IR-58-UNIQ-07). The newest artifact merged from `main` (the ML
> RandomForest candidate, PR #30) carries a format receipt **only**: no uniqueness screen, no
> holdout receipt, no organizer receipt (IR-58-S6-06). **The owner has used 0 of the weekly slots.**

---

## ⚡ START HERE — download and submit, once a file is cleared

| | |
|---|---|
| **Step 1 — status & download** | Open **[docs/index.html](docs/index.html)**. The banner at the top is the machine-computed verdict for the current candidate: **OK TO SUBMIT** or **NOT OK TO SUBMIT — DO NOT SUBMIT**. The download button sits directly under it. |
| **Step 2 — how to submit** | Open **[docs/executive-summary.html](docs/executive-summary.html)** (and [docs/submit.html](docs/submit.html) for the portal checklist). It gives the click-by-click upload path, the **submission name**, and the **note (≤ 140 characters)**. |
| **Step 3 — per-file verdicts** | Open **[docs/downloads/index.html](docs/downloads/index.html)**. Every public TIFF/ZIP in this repository is listed with **its own** verdict and SHA-256; no file can inherit another file's clearance. |
| **Step 4 — verify** | Compare the SHA-256 on the page with `sha256sum <file>` on the download. The verdict applies to that hash and nothing else. |

The pages never ask anyone to interpret anything: the banner is one of two sentences, and every
gate behind it is listed with its measured value and the evidence file it came from. An organizer
receipt (`G6`) cannot exist before a file is uploaded, so it is always reported as *open — owner
step*, and the banner states that its verdict covers the local gates `G1–G5` only.

---

## 📜 Standing prompt — the binding contract

The full operating contract lives in **[PROMPT.md](PROMPT.md)** (read it first, every session) with
the verbatim brief in **[docs/MISSION.md](docs/MISSION.md)** and the current decision in
**[REMAINING_WORK.md](REMAINING_WORK.md)**. The clauses that govern every session:

1. **Gates, not labels.** *"A unique, downloadable GeoTIFF is the goal, but uniqueness and
   validation are gates, not labels."* A TIFF must be prominently marked **NOT OK TO SUBMIT — DO
   NOT SUBMIT** unless every holdout, surface, dot, inventory, format and validation gate passes.
   *"Never copy a prior submission except for learning. Never select or use a weekly slot during
   research."* When an unconditional request to produce a TIFF conflicts with a no-go gate,
   preserve the gate, publish the negative decision, and do not manufacture a false clearance.
2. **Evidence labels.** `HOLDOUT-DTI` requires the shared evaluator version, withheld-positive
   count, the prescribed spatially blocked protocol and a defensible 95 % CI.
   `ORGANIZER-CONFIRMED` requires an organizer receipt/hash crosswalk. A projection, local proxy,
   format preflight or leaderboard row is **not** a score for a TIFF.
3. **RATIFIED-UNIQ-v1** (ratified session 5, IR-58-UNIQ-07). Compare the pre-placement surface and
   the final dots against the registry. Stop and record a duplicate if rank correlation > 0.90, if
   dot-set Jaccard > 0.50, if bytes or decoded pixels are identical to a witness, if the scan is
   incomplete/stale, or if an overlap firing is *informative*: literal 3 px forward overlap > 0.70
   against a witness whose chance expectation `E < 0.70` (**rule A**), or chance-corrected lift
   `(O − E)/(1 − E) > 0.50` against any witness with `E < 0.99` (**rule B**). The literal
   pre-ratification reading is always computed and published beside the governing verdict.
4. **Reuse shared tools.** One metric (`src/gems57/metric.py`, transcribed from the official
   metric page), one holdout constructor, one writer, one uniqueness instrument. No private forks;
   if a shared tool is wrong, fix it and its tests once.
5. **Metric-aware width calibration.** `U = (1 − αs)·ΔTP − αs·ΔFP` with `s` the current DTI and
   `ΔTP, ΔFP` the exact marginal changes; the shortcut `k > αs` holds only for one added,
   non-redundant dot. Ribbon width and offsets are chosen only from these exact numbers.
6. **Leakage canary.** *"Test each feature alone on the holdout before trusting it. AUC > 0.90 is
   leakage until explained."*
7. **Hypotheses before implementation.** Rank 3–5 genuinely untried within-lane hypotheses by
   expected benefit, uncertainty and cost; name layers, physical signature, why the signature
   marks an unmapped fault rather than a catalogued trace, and the official data source for any new
   data. A ribbon cannot discover a fault the ridge detector entirely missed — that is a different
   lane, and this checkout stays in the ribbon lane.
8. **Experiment budget and stopping.** At most three experiments, stop at two hours, and stop
   immediately on a literal uniqueness trigger, stale/incomplete inventory, canary failure or a
   nonpositive/uncertain primary result. Do not add experiments because a result is weak.
9. **Run card, no slot selection.** End with one JSON card — hypothesis, mechanism, named non-fault
   mimic, HOLDOUT-DTI/evaluator/count/95 % CI or explicit `NOT MEASURED`, registry results, raster
   SHA-256, validator output, submission name and note ≤ 140 characters, verdict `promote` or
   `negative`. Qualification and a real submission are separate human decisions.

---

## 🧭 Verified competition facts (each with its source)

| Fact | Source |
|---|---|
| Target = **geological faults that are indicative of geothermal resources** — not vents. Expert labels include **faults absent from** the public USGS/INGENIOUS database; the region is split into a **public** and a **private** subset; the Private Prize Round is scored on the private subset and re-scored against an expanded expert label set in the Final Round. | [problem page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (read 2026-10-11) |
| Metric = distance-weighted Tversky index, α = 0.2 (false positives), β = 0.8 (false negatives), triangular kernel **R = 300 m = 3 px**: `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`. | page 967, *Performance metric* |
| Submission = single-band **float32** GeoTIFF in **EPSG:32611**, 100 m, region bounds identical to the training data, **values within [0, 1]**, *"data outside the bounds is null or nan"*. | page 967, *Submission format* |
| Portal rejection *"Predicted values must be in range [0, 1]"* is **unresolved**: no portal response or receipt in this repository is bound to a candidate's SHA-256, so the cause is neither asserted nor explained away. | [docs/SOURCES.md](docs/SOURCES.md) §*Portal `[0,1]` report* |
| Public leaderboard snapshot **2026-10-11**: #1 `xiaofanhu` **0.4133**, #8 `kinghorton42` 0.3261, #9 `DARD` **0.3195**, #23 `extradr19` **0.2778**. Ranks are dynamic (DARD was observed at rank 8 earlier the same day); rows identify no TIFF. | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), recorded in [docs/LEADERBOARD.md](docs/LEADERBOARD.md) |
| The **0.2778** figure is the `extradr19` participant row. The `GEMSDOE32` H33 artifact is marked **UNSCORED** by its own audit (projected 0.2747, sha256 `c55bafc4…`); no hash/receipt crosswalk ties 0.2778 to it. | [docs/LEADERBOARD.md](docs/LEADERBOARD.md), [registry/submissions_seen.csv](registry/submissions_seen.csv) |
| The **0.3774** figure is a historical repository-page figure, not the live board. | 60GEMSDOE README erratum, 2026-10-11 |

**What the numbers imply (measured, not asserted).** Twenty-two-plus participants sit above 0.2778,
so beating it is demonstrated possible. This repository's own emission family (37k–44k off-catalogue
dots at 1.0) occupies the 0.26–0.275 band on the public board, i.e. just under the target, and a
controlled probe inside that family shows the gap is **placement, not density**: `h34-scatter-q50-arr-matched`
matches the family's arrangement statistics to four decimals, shares 644 of 37,654 dots with it
(Jaccard 0.0086) — and scored **0.0778**. Which pixels are chosen is what pays. See
[docs/research/why-02778.md](docs/research/why-02778.md) and [docs/HYPOTHESES.md](docs/HYPOTHESES.md).

### Official links for manual review

| Purpose | Link |
|---|---|
| Competition home | <https://www.drivendata.org/competitions/306/competition-doe-gems/> |
| Problem statement, metric, submission format | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> |
| Live public leaderboard | <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> |
| Official rules (PDF) | <https://docs.nlr.gov/docs/fy26osti/96647.pdf> |
| Official reference solution | <https://github.com/drivendataorg/gems-prize-reference-solution> |
| GeoDAWN airborne magnetic/radiometric survey (USGS) | <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> |
| INGENIOUS fault catalogue (GBCGE) | <https://gbcge.org/current-projects/ingenious/> |
| EPSG:32611 grid definition | <https://epsg.io/32611> |

The full source register, with what each source does and does not establish, is
[docs/SOURCES.md](docs/SOURCES.md) and [registry/sources.csv](registry/sources.csv).

---

## 🗂️ Repository map

```
data/            official competition inputs (sha256-pinned bridge), external mirrors, witness registry
src/gems57/      shared tools: metric, validate, holdout, evaluate_holdout, uniqueness, submission_writer, gates
src/gems58w/     ribbon-lane building blocks: features, ridges, extraction, sigma, holdout, metric
src/gems61/      this session's lane: extended layers, ridge field, sigma table, pattern ladder, emission
scripts/         runners, fetchers, screeners, site builders, validators (gems61_* = current lane)
evidence/        receipts — one JSON per measurement, each carrying its evidence class
docs/            the public site (GitHub Pages), research notes, source register, leaderboard record
registry/        every public raster scanned by this project, with sha256 pins and uniqueness rows
tests/           pytest suite — the shared metric, holdout, writer and gate contracts are all tested
```

Reproduce the current lane end to end:

```bash
bash scripts/ribbon_fetch_features.sh                 # 19-band organizer stack (419 MB, sha256-pinned)
bash scripts/gems61_fetch_extended.sh                 # GeoDAWN radiometric / lidar / DEM mirrors (sha256-pinned)
PYTHONPATH=src python3 scripts/gems61_run.py field    # cached extended ridge field            [run, evidence written]
PYTHONPATH=src python3 scripts/gems61_run.py sigma    # σ(x) by block × resolution × ridge type
PYTHONPATH=src python3 scripts/gems61_run.py pattern  # exact-metric pattern ladder + choices
PYTHONPATH=src python3 scripts/gems61_run.py canary   # single-feature leakage canary
PYTHONPATH=src python3 scripts/gems61_run.py emit     # candidate GeoTIFF + ZIP + receipts
python3 scripts/gems61_screen.py --candidate docs/downloads/<name>.tif \
        --out evidence/gems61/uniqueness.json         # RATIFIED-UNIQ-v1 screen vs 703 witnesses
python3 scripts/build_downloads_index.py              # docs/downloads/index.html (one verdict per file)
python3 scripts/build_site.py                         # docs/index.html gates + banner
python3 scripts/gems60_build_page.py                  # session-5 deliverable box (must run last)
python3 -m pytest tests/ -q
```

At this commit only `field` has been executed in the `gems61` lane (`evidence/gems61/field.json`:
5,167,205 ridge pixels, 41 classes over 9 feature families); `sigma`, `pattern`, `canary` and `emit`
are implemented but **not yet run**, so the lane has produced no candidate and cleared nothing.
Everything runs without the organizer's login wall: inputs are restored from hash-pinned public
mirrors and re-verified at run time, and a mismatch aborts the run.

---

## ⚖️ Rules that keep the numbers honest

1. **Evidence classes.** `HOLDOUT-DTI` (evaluator version, withheld positives, protocol, CI) /
   `ORGANIZER-CONFIRMED` (organizer receipt or hash crosswalk only) / `PUBLIC-LEADERBOARD SNAPSHOT`
   (dated participant rows, never artifact scores). Projections and preflights are never scores.
2. **The instrument is shared.** One metric implementation, cross-checked against a brute-force
   oracle; one holdout; one writer; one uniqueness instrument. A private fork is a defect.
3. **The holdout measures catalogue recovery only.** It is structurally blind to off-catalogue
   truth (IR-58-02): it ranks this repository's own families at ρ ≈ 0.5 and does not explain the 66
   measured live rows (R² negative on the full set). It is a *screen*, never a leaderboard forecast.
4. **Gates, not labels.** Downloads stay available for review; the banner and the per-file table
   carry the verdict; no file is ever promoted to a weekly slot by this repository.
5. **Fail closed.** A stale or incomplete inventory, a canary AUC > 0.90, or any metric mismatch
   stops the lane and is published as a negative result.

---

## 🚧 Known limitations (part of the deliverable)

* The organizer's expert truth is unpublished; every local number here measures *catalogue*
  recovery, and is labelled as such.
* Public/private chunking is undisclosed, so public-board rows carry chunk noise that no local
  statistic models.
* The owner-published radiometric and lidar mirrors are **8-bit** products with no published
  scaling; this lane uses them **ordinal-only** and claims no physical units.
* The registry inventory is a snapshot of public repositories, not an organizer-wide inventory;
  `BLOCKED_NOT_EXHAUSTIVE` still applies to the freshness audit.
* The ML candidate merged from `main` has a format receipt only; its local AUC 0.7152 measures
  catalogue-fault discrimination on a non-spatial split and is not a HOLDOUT-DTI and not a score.
* Weekly slots are an owner decision; this repository never spends one.

See [REMAINING_WORK.md](REMAINING_WORK.md) for ranked next steps and
[docs/IRREGULARITIES.md](docs/IRREGULARITIES.md) for every open blocker and correction.
