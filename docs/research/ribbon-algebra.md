# Ribbon algebra — current decision rule and legacy evidence warning

> **Current status: no promotion-grade width result exists.** `evidence/ribbon/` contains historical diagnostics from the legacy `gems58w` pipeline. Its unbuffered/same-cell selection and inference are not valid promotion evidence; do not quote those HOLDOUT-DTI values or the generated `docs/ribbon/` site as current results. The current submission decision is **NOT OK TO SUBMIT — DO NOT SUBMIT**.

## The metric must be applied to the whole ribbon pattern

The organizer's distance-weighted Tversky index uses the 300 m triangular kernel, α=0.2, β=0.8. For a current prediction set `P` and a proposed changed set `P′`, define `ΔTP = TP(P′)−TP(P)` and `ΔFP = FP(P′)−FP(P)` using the exact maximum-credit metric, including all overlap between lines. If the current score is `s`, the exact sign of the score change is the sign of

```text
U = (1 − αs)·ΔTP − αs·ΔFP.
```

This is the correct general rule for a ribbon-width change. Do not add single-dot utilities as if each line gained independent truth credit.

The shortcut `k > αs` is valid only for one fresh, non-redundant binary dot with `ΔTP=k` and `ΔFP=1−k`. A dot within kernel radius of truth may still be harmful when prior predictions have already captured the same truth credit. `docs/research/metric.md` contains the full derivation; `tests/test_metric_exact.py` includes a regression case.

## What remains a hypothesis

A symmetric ribbon might help when a detected ridge's localization error has a broad distribution; a shifted/asymmetric ribbon might help if that error is directionally biased. Neither effect is established by the legacy measurements. Any future comparison must:

1. measure localization error with buffered whole-component outer folds;
2. estimate width/offset parameters using training folds only;
3. use shared `gems57.evaluate_holdout` and exact `ΔTP`/`ΔFP` for candidate patterns;
4. pass the feature-alone leakage canary and the pre-placement registry surface gate before placement;
5. run the final-dot uniqueness gate against the current complete accessible inventory;
6. report HOLDOUT-DTI only with evaluator version, withheld-positive count, protocol, and a defensible 95% CI.

## Stopping decision

The current candidate's final-dot scan records 1.0 overlap within 3 px against one prior full-footprint-positive raster, above the literal 0.70 stop limit; the scan is also stale/incomplete. No exception for dense or “carrier” rasters has been authorized. Therefore no new width experiment or submission TIFF is cleared until the inventory/gate issue is resolved. See `evidence/run_card.json`, `evidence/ribbon_uniqueness.json`, and [`REMAINING_WORK.md`](../../REMAINING_WORK.md).
