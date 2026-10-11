# 58GEMSDOE

Geophysics-only fault-prediction lane for the GEMS Prize (DrivenData, Nevada, 100 m grid, EPSG:32611).

**Status: negative result. No submission file is cleared.**

- The ribbon-lane candidate (triple parallel dotted lines from magnetic-edge and detrended-elevation ridges) scores a pooled holdout DTI of **0.0160** (95% CI 0.0150–0.0169).
- Random placement with the same number of dots scores **0.0338** on the same holdout, so the lane is below chance.
- The σ68 across-strike error is 5–8 px, not the 1–3 px the design assumed (see `docs/results.html`).
- Every configuration failed the registry uniqueness gate. The worst match is `13GEMSDOE r13-lattice-s5` at 99.6% dot overlap.
- The 0.2778 reference candidate does not reproduce on the local holdout (0.0046 vs 0.2778 reported). See `docs/top-score-analysis.md`.

## Layout

| Path | Contents |
|---|---|
| `src/gems58/` | Shared library: `dti` (exact metric, unit-tested), `validate`, `uniqueness`, `ribbon` |
| `scripts/select_unique_ribbon.py` | Holdout, configuration selection and uniqueness gate. Writes a submission only if a configuration passes |
| `scripts/build_site.py` | Builds the Pages site in `docs/` from the reports |
| `reports/ribbon_lane_report.json` | Machine-readable results, including `config_selection` |
| `docs/` | Site (`index.html`), results, executive summary, hypotheses, irregularities, sources, top-score analysis, `run-card.json` |
| `tests/test_dti.py` | DTI unit tests (`PYTHONPATH=src python tests/test_dti.py`) |

## Reproducing

```
python scripts/select_unique_ribbon.py   # ~25 min; writes nothing if no configuration passes the gate
python scripts/build_site.py             # regenerates docs/ from the reports
```

## Data

`data/` holds three rasters (`labels.tif`, `sample_submission.tif`, `training_features.tif`), sha256-verified. It is git-ignored; `data/README.md` is tracked.

## Caveats

- Holdout numbers are our own hide-and-recover estimates (HOLDOUT-DTI). They are not organizer scores.
- The leaderboard figure in the site (0.3195) comes from another repository's ledger and is not verified.
- The experiment budget for this lane is used up. Any further run needs approval.
