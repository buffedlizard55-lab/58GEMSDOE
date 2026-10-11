# Archived session-3 canonical receipts (candidate gems58-ribbon-sigma-adaptive-40768-20261011T052942Z)

Copied verbatim on 2026-10-11 (session 5) before the canonical filenames were re-pointed at the
session-5 candidate `gems58-concordance-ribbon-40768-20261011T160514Z`. These are the receipts the
session-3 run card and REMAINING_WORK.md §S3 refer to.

Session 6 made exactly two changes here, both labelling rather than measurement (IR-58-S6-02/03):

- `run_card_v2.json` and `run_card_final.json`: `holdout_dti_label` changed from `HOLDOUT-DTI` to
  `LEGACY-DIAGNOSTIC-ONLY`, with a `holdout_dti_label_note` explaining why. The 0.043651 value,
  per-fold numbers, evaluator, protocol, withheld-positive count, registry screen and receipts are
  untouched. A four-block min–max range is not a defensible 95 % CI, so this diagnostic must not be
  read as a promotion-grade `HOLDOUT-DTI` result.
- `file_audit_sigma_adaptive.json` added: the independent on-disk TIFF/ZIP audit of the session-3
  raster (11/11 checks, SHA-256 `ecf833f8…2711dd`), moved here when `scripts/audit_current_tiff.py`
  was re-pointed at whatever `evidence/ribbon/emission.json` names. Local file verification only.
