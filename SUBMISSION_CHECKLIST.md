# Submission Checklist - 58GEMSDOE Unique Ribbon

## ✅ Completed Tasks

- [x] Review repository structure and understand requirements
- [x] Analyze existing candidates and their status
- [x] Understand the ribbon lane method from prompt
- [x] Identify uniqueness blocking issue
- [x] Design sparse emission strategy (≤15k dots)
- [x] Implement boundary placement algorithm
- [x] Generate TIF file with proper format
- [x] Validate all format checks (13/13 passed)
- [x] Create ZIP archive
- [x] Generate submission receipt
- [x] Create run card JSON
- [x] Create executive summary HTML
- [x] Create download page HTML
- [x] Create README documentation
- [x] Verify SHA256 hash
- [x] Verify file properties
- [x] Verify all constraints (no catalogue overlap, within footprint, etc.)

## 📋 Files Created

- [x] `docs/downloads/58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif` (47 MB)
- [x] `docs/downloads/58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.zip` (100 KB)
- [x] `docs/downloads/58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.json` (2.1 KB)
- [x] `evidence/58gemsdoe_unique_ribbon/run_card.json` (3.2 KB)
- [x] `docs/downloads/executive-summary.html` (14 KB)
- [x] `docs/downloads/index.html` (14 KB)
- [x] `docs/downloads/README.md` (comprehensive)

## 🔍 Verification Checklist

### Format Validation
- [x] Single band GeoTIFF
- [x] Float32 data type
- [x] Correct dimensions (3730×3292)
- [x] Correct CRS (EPSG:32611)
- [x] Correct transform (matches sample)
- [x] No NaN values
- [x] No Inf values
- [x] No sentinel values
- [x] All values in [0, 1]
- [x] All finite values
- [x] Outside footprint is zero
- [x] Zero dots on catalogue

### Content Verification
- [x] 15,000 dots
- [x] All dots at exactly 1.0
- [x] No dots on catalogue
- [x] No dots outside footprint
- [x] All dots within valid footprint
- [x] SHA256 computed and verified

### Documentation
- [x] Run card with all metadata
- [x] Submission receipt
- [x] Executive summary
- [x] Download page
- [x] README with FAQ
- [x] Review summary

## ⏳ Pending Tasks (Before Submission)

- [ ] Run registry uniqueness scan
  - Command: `python scripts/check_uniqueness_registry.py 58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif`
  - Expected: PASS
  - Time: 30-60 minutes

- [ ] Run pre-placement surface comparison
  - Command: `python scripts/check_uniqueness_registry.py --surface-only 58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif`
  - Expected: PASS
  - Time: 30-60 minutes

- [ ] Run feature-alone leakage canary
  - Command: `python scripts/ribbon_run_leakage_canary.py`
  - Expected: PASS (AUC < 0.90)
  - Time: 5-10 minutes

- [ ] Run holdout evaluation
  - Command: `python scripts/ribbon_run_holdout_eval.py`
  - Expected: HOLDOUT-DTI with CI
  - Time: 10-20 minutes

- [ ] Update verdict in run card
  - File: `evidence/58gemsdoe_unique_ribbon/run_card.json`
  - Change: `"verdict": "negative"` → `"verdict": "promote"`
  - Change: `"promote": false` → `"promote": true`
  - Time: 1 minute

- [ ] Select weekly slot (human decision)
  - Time: Variable

- [ ] Submit to competition
  - Portal: https://www.drivendata.org/competitions/306/competition-doe-gems/
  - File: TIF
  - Name: `58GEMSDOE-ribbon-sparse-unique`
  - Note: `Ribbon lane: sparse boundary dots (15000 dots at 1.0), uniqueness-filtered`

## 📊 Validation Results

### Format Checks: ✅ ALL PASSED
```
✓ single_band: true
✓ dtype_float32: true
✓ dimensions_3730x3292: true
✓ crs_epsg_32611: true
✓ transform_matches_sample_submission: true
✓ no_nan_anywhere: true
✓ no_inf_anywhere: true
✓ no_sentinel_values: true
✓ range_0_1_guaranteed: true
✓ min_ge_0: true
✓ max_le_1: true
✓ in_footprint_all_finite: true
✓ in_footprint_range_0_1: true
✓ outside_footprint_zero: true
✓ zero_dots_on_mapped_catalogue: true
```

### File Properties
- **File**: `58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif`
- **SHA256**: `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448`
- **Size**: 49,139,380 bytes (47 MB)
- **Shape**: 3730 × 3292
- **CRS**: EPSG:32611
- **Dtype**: float32
- **Dots**: 15,000
- **All checks passed**: true

## 🎯 Current Status

| Aspect | Status | Notes |
|--------|--------|-------|
| File Generation | ✅ COMPLETE | All files created |
| Format Validation | ✅ PASSED | 13/13 checks |
| Uniqueness Scan | ⏳ PENDING | Not run yet |
| Surface Comparison | ⏳ PENDING | Not run yet |
| Leakage Canary | ⏳ PENDING | Not run yet |
| Holdout Evaluation | ⏳ PENDING | Not run yet |
| Verdict | ❌ NEGATIVE | Until gates clear |
| Submission Ready | ❌ NO | Gates pending |

## 🚀 Estimated Timeline

| Task | Time Required | Status |
|------|---------------|--------|
| Generate files | 5 minutes | ✅ Done |
| Registry scan | 30-60 minutes | ⏳ Pending |
| Surface comparison | 30-60 minutes | ⏳ Pending |
| Leakage canary | 5-10 minutes | ⏳ Pending |
| Holdout evaluation | 10-20 minutes | ⏳ Pending |
| Update verdict | 1 minute | ⏳ Pending |
| **Total** | **2-3 hours** | **⏳ Pending** |

## 📞 Quick Start

To begin the validation process:

```bash
# Step 1: Registry uniqueness scan
python scripts/check_uniqueness_registry.py docs/downloads/58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif

# Step 2: Pre-placement surface comparison
python scripts/check_uniqueness_registry.py --surface-only docs/downloads/58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif

# Step 3: Leakage canary
python scripts/ribbon_run_leakage_canary.py

# Step 4: Holdout evaluation
python scripts/ribbon_run_holdout_eval.py
```

## 🏆 Expected Outcome

- **Uniqueness**: ✅ PASS (sparse emission design)
- **Surface Gate**: ✅ PASS (unique placement)
- **Leakage**: ✅ PASS (boundary placement)
- **Holdout**: ⚠️ UNKNOWN (needs evaluation)
- **Overall**: ✅ READY FOR SUBMISSION (after gates clear)

## 📝 Notes

1. The file passes all format checks and is technically valid
2. The sparse emission design should pass uniqueness checks
3. All documentation is complete and accurate
4. The submission is ready for the validation pipeline
5. DO NOT SUBMIT until all gates are cleared

---

**Last Updated:** 2026-10-11 18:25:11 UTC
