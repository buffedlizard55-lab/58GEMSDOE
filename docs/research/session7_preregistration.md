# Session 7 pre-registration — novelty-constrained sparse concordance emission (H58-S7-N)

Written **before** any candidate for this design is generated, scored, or scanned. Every number
below is either a measured receipt written by the script named in the table, or is labelled as a
pre-registered parameter. Nothing here is a leaderboard score.

## 1. Question

Can a sparse (≈15 k dot) emission that is **placed away from the informative registry witnesses**
clear the ratified uniqueness gate (RATIFIED-UNIQ-v1, `PROMPT.md` item 1) while keeping a positive
catalogue-free HOLDOUT-DTI? Session 5 (`REMAINING_WORK.md` S5.1 item 2) asked for exactly this
variant and for the final-dot gate to be simulated **before** emitting.

## 2. Layers and physical signature

* **Placement surface**: `evidence/ribbon/concordance_surface.tif` (H58-X1, session 5). A catalogue-free
  multi-family Hessian ridge field of the organizer's 19-band stack, gated so a ridge pixel survives
  only where ≥ 2 independent geophysical families (magnetic, gravity, topographic, subsurface, geodetic,
  seismic) agree (τ_family = 0.30, τ = 0.35). Physical signature: a linear, multi-family, sub-kilometre
  ridge-like response in potential-field and topographic derivatives — the expected signature of a
  fault trace under thin cover, as opposed to a single-family artefact.
* **Witness registry**: 703 accessible public prediction rasters (`registry/registry_merged.json`),
  byte-verified into `.cache/registry/<sha256>.tif` this session.

## 3. Named non-fault mimic

Drainage incisions and alluvial-fan fronts, which also produce multi-family ridge responses in
topography and magnetics. A multi-family ridge that is actually an erosional edge is the failure
mode this emission is most exposed to; the local holdout cannot distinguish it from a fault.

## 4. Why this should not just copy a registry raster

The uniqueness rule (A: literal forward 3-px overlap > 0.70 against a witness with chance E < 0.70;
B: chance-corrected lift > 0.50 against a witness with E < 0.99) fires on the *dots*. For any
witness with E < 0.70, its 3-px neighbourhood is excluded from the candidate pool **before** selection,
so no candidate dot can lie within 3 px of that witness's dots and rule A cannot fire for it by
construction. This is a *placement* constraint, not a post-hoc edit, and it is a deliberate trade:
any truth that happens to sit where an informative witness predicted is given up.

## 5. Pre-registered parameters (fixed before running)

| parameter | value | source |
|---|---|---|
| dot budget K | **15,000** | `REMAINING_WORK.md` S5.1 item 2 (k ≈ 10–15 k) |
| minimum separation | **3 px** (accepted dots are ≥ 3 px apart) | S5.1 item 2 |
| ranking | descending surface value, ties by raster index | deterministic |
| excluded from pool | mapped catalogue pixels (organizer-masked; writer forbids them) | `gems57.submission_writer` |
| excluded from pool | the union of 3-px neighbourhoods of every witness with E < 0.70 | this file §4 |
| informative-witness set | chance E < 0.70 **and** not saturated (E < 0.99) | RATIFIED-UNIQ-v1 |
| emitted value | exactly 1.0 at each included dot; 0 elsewhere | `docs/research/ribbon-algebra.md` |
| outside footprint | 0 (the shared writer's representation; the official reference writer also emits finite values across the grid — see IR-S7-03) | `gems57.submission_writer` |
| holdout | `gems57.holdout.build_buffered_holdout_context`, seeds (20, 21), 4 LOQO folds; `gems57.holdout.evaluate` on the **exact final bytes** | shared tool |
| metric | α = 0.2, β = 0.8, 300 m (3 px) triangular kernel | `gems57.metric` |
| uniqueness | final dots scanned by `scripts/check_uniqueness_registry.py` (shared gate) — EXP-3 | protocol |

## 6. Experiments (budget: three, two hours)

| # | what | receipt |
|---|---|---|
| EXP-1 | Full 703-witness uniqueness scan of the **already-published, never-screened** file `58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif` | `evidence/s7/uniqueness_existing_sparse.json` — **NOT COMPLETED.** The witness cache (703/703 byte-verified) was restored and the scan was launched, but the process ended without writing a receipt, and the sandbox was then reset (venv and cache lost). Status: the file remains **unscreened**. |
| EXP-2 | Build H58-S7-N, simulate the final-dot gate from the same witness masks **before** writing, and measure the exact-bytes holdout (plus the leaky existing file as a control) | `evidence/s7/emission_novel_sparse.json` |
| EXP-3 | Full 703-witness scan of the H58-S7-N file with the shared gate | `evidence/s7/uniqueness_novel_sparse.json` |

## 7. Stop rules (pre-registered)

Stop and record a duplicate if the shared final-dot scan fires rule A, rule B, rank correlation
> 0.90, Jaccard > 0.50, byte/pixel identity, or an incomplete scan. Stop on leakage-canary failure
(AUC > 0.90 for any single feature). A nonpositive holdout DTI is a negative result and is reported
as one. No experiment is added because a result is weak.

## 8. What would count as success

Success is narrow and measurable: EXP-3 passes every gate **and** the exact-bytes holdout is
positive with its withheld-positive count and interval reported. Success does **not** mean a
leaderboard score. No organizer receipt can exist for an unsubmitted file, and the local holdout
cannot see off-catalogue faults (see `docs/research/why-02778-corrected.md`).
