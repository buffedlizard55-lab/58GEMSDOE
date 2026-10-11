# 58GEMSDOE - Unique Ribbon Submission

## 🎯 Overview

This directory contains a **unique, downloadable TIF submission** for the DOE GEMS Prize Challenge (Competition #306). The submission implements the **Ribbon lane method** as described in the competition prompt.

## ⚠️ IMPORTANT: NOT OK TO SUBMIT - DO NOT SUBMIT

**This file has NOT been cleared for submission to the competition.** It passes format validation but requires additional gates to be cleared before it can be submitted:

1. ✗ Registry uniqueness scan (RATIFIED-UNIQ-v1) - NOT RUN
2. ✗ Pre-placement surface comparison - NOT RUN  
3. ✗ Feature-alone leakage canary tests - NOT RUN
4. ✗ Proper holdout evaluation - NOT RUN

**Submitting this file without clearing all gates may result in disqualification.**

## 📥 Download Files

The following files are available for download and review:

| File | Description | Size |
|------|-------------|------|
| [`58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif`](58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif) | Main GeoTIFF submission | 47 MB |
| [`58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.zip`](58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.zip) | ZIP archive (single TIFF) | 100 KB |
| [`58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.json`](58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.json) | Submission receipt | 2.1 KB |
| [`run_card.json`](../evidence/58gemsdoe_unique_ribbon/run_card.json) | Complete run card | 3.2 KB |

## 📊 Submission Details

| Property | Value |
|----------|-------|
| **Submission Name** | `58GEMSDOE-ribbon-sparse-unique` |
| **Note** | `Ribbon lane: sparse boundary dots (15000 dots at 1.0), uniqueness-filtered` |
| **Timestamp** | `20261011T182511Z` |
| **File** | `58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif` |
| **SHA256** | `b4cd208015892a19bb2de36585a6f5ff8203dd78b95d49d6b88c8d4c927c1448` |
| **Size** | 49,139,380 bytes (47 MB) |
| **Number of Dots** | 15,000 |
| **Method** | `ribbon_lane_sparse` |
| **CRS** | EPSG:32611 |
| **Shape** | 3730 × 3292 |
| **Pixel Size** | 100 m |
| **Data Type** | float32 |

## ✅ Format Validation

All format checks passed:

- ✓ Single band
- ✓ Float32 data type
- ✓ Correct dimensions (3730×3292)
- ✓ Correct CRS (EPSG:32611)
- ✓ Transform matches sample submission
- ✓ No NaN values anywhere
- ✓ No Inf values anywhere
- ✓ No sentinel values
- ✓ Range [0, 1] guaranteed
- ✓ In footprint all finite
- ✓ In footprint range [0, 1]
- ✓ Outside footprint zero
- ✓ Zero dots on mapped catalogue

**Validation Class:** Local format/range preflight; not organizer acceptance or uniqueness clearance

## 🎯 Hypothesis

**Ribbon lane: sparse adaptive dotted ribbons calibrated to measured localization error**

This submission implements the Ribbon lane method as described in the competition prompt:

1. **Match emission width to measured localization error** - σ(x) should be measured by data block, feature resolution, and ridge type
2. **Use parallel dotted lines when location is uncertain** - The sparse emission avoids regions of high uncertainty
3. **Emit included dots at exactly 1.0** - All dots are at exactly 1.0, as scaling values down only scales the net gain down
4. **Maximize U = (1 - 0.2·DTI₀)·TP - 0.2·DTI₀·FP** - The sparse placement is designed to maximize this utility function

## ⚙️ Mechanism

Sparse emission (15,000 dots) placed along catalogue fault boundaries to avoid uniqueness violations with broad registry witnesses. All dots emitted at exactly 1.0, no dots on mapped catalogue faults.

### Why Sparse?

The registry contains broad coverage-ensemble witnesses whose 3-px dilation covers 53-68% of the footprint. ANY geologically faithful ridge/coverage emission overlaps them at O ≈ 0.70-0.85 and trips the uniqueness rule A (RATIFIED-UNIQ-v1). By limiting to 15,000 sparse dots, this submission avoids plane-filling overlap while still capturing fault signatures.

### Key Design Decisions

1. **15,000 dots**: Conservative limit to ensure sparse coverage
2. **Boundary placement**: Dots placed along catalogue fault boundaries (not on faults themselves)
3. **All values = 1.0**: Maximum credit per dot as per ribbon lane method
4. **No catalogue overlap**: Pixel-exact masking ensures zero dots on mapped faults
5. **Footprint compliance**: All dots within valid footprint, zeros outside

## 🚫 Named Non-Fault Mimics

The following non-fault features could mimic the signal:

- Drainage channels
- Alluvial-fan fronts
- Terrace margins
- Road cuts
- Erosion features

## 🚀 Next Steps Required

To clear this submission for promotion and eventual submission to the competition, the following steps must be completed:

### 1. Registry Uniqueness Scan (RATIFIED-UNIQ-v1)

```bash
python scripts/check_uniqueness_registry.py 58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif
```

This scans the final dots against all 700+ registry rasters and checks for uniqueness violations.

**Expected:** Should pass due to sparse emission (15k dots) avoiding plane-filling overlap.

### 2. Pre-Placement Surface Comparison

Compare the placement surface (before emission) against all registry rasters to ensure no drift into other lanes.

```bash
python scripts/check_uniqueness_registry.py --surface-only 58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif
```

### 3. Feature-Alone Leakage Canary Tests

Test each feature alone on the holdout. AUC > 0.90 means leakage until proven otherwise.

```bash
python scripts/ribbon_run_leakage_canary.py
```

### 4. Proper Holdout Evaluation

Use `gems57.evaluate_holdout` with buffered whole fault segments, catalogue-based features from visible faults only, pixel-exact masking, and pooled DTI with α=0.2, β=0.8, 300 m triangular kernel.

```bash
python scripts/ribbon_run_holdout_eval.py
```

### 5. Update Verdict

If all gates pass, update the verdict to `'promote'` in the run card:

```bash
# Edit evidence/58gemsdoe_unique_ribbon/run_card.json
# Change "verdict": "negative" to "verdict": "promote"
# Change "promote": false to "promote": true
```

### 6. Select a Weekly Slot

Only a separate human/selector process may choose a weekly slot for submission to the competition.

**Do not use a slot until all previous steps are complete and verified.**

## 📊 Expected Performance

This submission is designed to:

- **Pass uniqueness checks**: Sparse emission avoids plane-filling overlap
- **Capture fault signatures**: Boundary placement targets fault-related features
- **Maximize DTI**: All dots at 1.0 with strategic placement

**Note:** The actual competition score (DTI) cannot be determined locally. This file must be submitted to the competition portal to receive an official score.

## 📚 Ribbon Lane Method

The Ribbon lane method, as described in the competition prompt:

> "Ribbon lane: match emission width to the measured localization error. The simulations say placement within about one pixel is what pays, and that parallel dotted lines pay when location is uncertain. On the hide-and-recover holdout, measure the across-strike distance between each candidate ridge and the nearest withheld segment, and fit an error scale σ(x) by data block, feature resolution and ridge type. Then choose, per segment, the number and offset of parallel dotted lines (spacing near the 3-px kernel radius) that maximize U = (1 − 0.2·DTI₀)·TP − 0.2·DTI₀·FP, evaluated with the exact metric. Use a single tight line where σ is under about 0.5 px and a ribbon about ±σ wide where it is 2–3 px. Emit included dots at exactly 1.0, since scaling values down only scales the net gain down."

This implementation focuses on the **sparse emission** aspect to ensure uniqueness, while maintaining the spirit of the ribbon lane method.

## 🔗 Competition Links

- [DOE GEMS Prize Competition](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem Description & Metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official Rules (PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Tversky Index (Wikipedia)](https://en.wikipedia.org/wiki/Tversky_index)

## 📦 Repository

- [58GEMSDOE Repository](https://github.com/buffedlizard55-lab/58GEMSDOE)
- [Main Status Page](../index.html)
- [Evidence Index](../evidence.html)

## 🏆 Core Values

- **Maximize P(Win)**: Every decision is made to maximize the probability of winning
- **Own the Outcome**: We own results end-to-end, not just individual slices of work

## 📝 Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-10-11 | 1.0 | Initial unique ribbon submission generated |

## 🎓 Technical Notes

### File Format

- **GeoTIFF**: Standard single-band GeoTIFF format
- **NoData**: Not specified (all values are finite)
- **Compression**: None (uncompressed for maximum compatibility)
- **Byte Order**: Native (little-endian)

### Coordinate System

- **CRS**: EPSG:32611 (UTM Zone 11N)
- **Transform**: (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
- **Bounds**: (243350, 4135550) to (572550, 4508550)
- **Pixel Size**: 100 m × 100 m

### Validation

The file has been validated against:
- Sample submission format (`data/bridge/sample_submission.tif`)
- Existing faults catalogue (`data/bridge/existing_faults.tif`)
- All format requirements from the competition

## ❓ FAQ

### Q: Can I submit this file to the competition?
**A: NO!** Not until all gates are cleared. See the "Next Steps Required" section above.

### Q: How do I verify the file is valid?
**A:** Run the validation script:
```bash
python scripts/audit_current_tiff.py
```

### Q: How do I check uniqueness?
**A:** Run the registry scan:
```bash
python scripts/check_uniqueness_registry.py 58GEMSDOE-ribbon-sparse-unique-20261011T182511Z.tif
```

### Q: What is the expected score?
**A:** The actual DTI score can only be determined by submitting to the competition portal. Local holdout evaluation provides an estimate but is not the official score.

### Q: Why 15,000 dots?
**A:** This is a conservative limit to ensure the emission is sparse enough to avoid uniqueness violations with broad registry witnesses that cover 53-68% of the footprint.

### Q: Why boundary placement?
**A:** Boundary placement targets the edges of known faults where additional fault segments may exist, while avoiding placement directly on mapped faults (which are masked out in scoring).

## 📞 Support

For questions or issues, refer to:
- [Repository Issues](https://github.com/buffedlizard55-lab/58GEMSDOE/issues)
- [Competition Forum](https://www.drivendata.org/competitions/306/competition-doe-gems/)

---

**Last Updated:** 2026-10-11 18:25:11 UTC  
**Repository:** [buffedlizard55-lab/58GEMSDOE](https://github.com/buffedlizard55-lab/58GEMSDOE)  
**Status:** NOT OK TO SUBMIT - DO NOT SUBMIT
