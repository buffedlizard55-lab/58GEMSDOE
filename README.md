# 58GEMSDOE — DOE GEMS Prize Challenge

Core values: **Maximize P(Win)** and **Own the Outcome** — report the actual result, including a negative one.

> **Submission ready:** `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif`
> — 45,355 binary predictions at exactly 1.0, detected by RandomForest on 20 geophysical gradient features.
> All format checks pass. Download and submit at [docs/executive-summary.html](docs/executive-summary.html).

## Quick Start — Submit Your Prediction

1. **Download** the TIF file: [`docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif`](docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif)
2. **Go to** [competition submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/) (login required)
3. **Upload** the TIF file and add note: `ML RandomForest binary ridge detection on 20 geophysical gradient features; 45K dots at 1.0`
4. **Submit** and check your score on the [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See the full [Executive Summary](docs/executive-summary.html) for detailed instructions.

---

## Project Mission

**Goal:** Maximize probability of winning the DOE GEMS Prize and own the outcome. The target is faults indicative of geothermal resources, not geothermal vents. Predict unseen geological faults from geophysical and topographic rasters scored by the Distance-Weighted Tversky Index (α=0.2, β=0.8, R=300m).

**Current submission:** ML RandomForest binary ridge detection on 20 gradient features from 10 key GeoDAWN bands.

**Official links:**
| Purpose | Link |
|---|---|
| Competition home | https://www.drivendata.org/competitions/306/competition-doe-gems/ |
| Problem description & DTI formula | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ |
| Public leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ |
| Data (login required) | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ |
| Rules (PDF) | https://docs.nlr.gov/docs/fy26osti/96647.pdf |
| Reference solution | https://github.com/drivendataorg/gems-prize-reference-solution |
| GeoDAWN survey (USGS) | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and |
| INGENIOUS (GBCGE) | https://gbcge.org/current-projects/ingenious/ |
| EPSG:32611 | https://epsg.io/32611 |
| Tversky index | https://en.wikipedia.org/wiki/Tversky_index |

## Current Submission Details

| Field | Value |
|---|---|
| File | `gems58-ml-binary-ridge-20261012T000000Z.tif` |
| SHA256 | `40c2518802a9a220fa362be0b152f2c4c7ca753c3919624eed22a556c5769366` |
| Format | Float32, EPSG:32611, 3730×3292, 100m |
| Values | All in [0, 1], zero outside footprint, no NaN |
| Positive pixels | 45,355 (all at exactly 1.0) |
| On catalogue | 0 |
| Method | RandomForest (100 trees, depth 8) on 20 gradient features |
| Validation AUC | 0.7152 |
| Submission note | `ML RandomForest binary ridge detection on 20 geophysical gradient features; 45K dots at 1.0` |

## Leaderboard Context (as of 2026-10-11)

| Rank | Participant | Score |
|---:|---|---:|
| 1 | xiaofanhu | 0.4133 |
| 8 | DARD | 0.3195 |
| 23 | extradr19 | 0.2778 |

Source: [official DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## Method Analysis

### Why high-scoring submissions work

The DTI metric: `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`

- **α=0.2** (FP penalty) vs **β=0.8** (FN penalty): coverage is 4× more valuable than precision
- The **kernel** (300m = 3px radius) gives credit for predictions *near* truth, not just at truth
- The **marginal bar** for a non-redundant dot: `k > 0.2·DTI` — at DTI=0.25, even a dot with kernel credit 0.05 (within ~2.85px of truth) is worth placing

### What the best submissions do differently

1. **0.4133 (xiaofanhu):** Likely a trained UNet/deep learning model producing continuous probability fields that detect both mapped and unmapped faults
2. **0.3195 (DARD):** Strong feature engineering + ML
3. **0.27-0.28 range:** Dotted/ridge approaches placing ~40K dots along structural lineaments
4. **0.15-0.25:** Simpler ridge detection, catalog-derived predictions

### Our approach

RandomForest classifier trained on 20 gradient features from 10 key GeoDAWN bands. The model learns the geophysical signature of faults from the USGS/INGENIOUS catalogue, then identifies similar structural features across the entire study area — including unmapped faults that the competition tests against.

### Key scientific references

- **GeoDAWN survey:** USGS airborne magnetic and radiometric surveys of NW Great Basin, Nevada
- **INGENIOUS project:** GBCGE fault database for the GeoDAWN region
- **Distance-Weighted Tversky Index:** Asymmetric similarity metric penalizing false negatives 4× more than false positives
- **Structural indicators:** Gradient magnitude on magnetic, gravity, and conductivity rasters detects lithological discontinuities associated with faulting

## Hypotheses for Improvement

### H1: Multi-scale edge detection with ensemble model
- **Layer:** All 19 GeoDAWN bands
- **Signature:** Multi-scale gradient magnitude, Hessian eigenvalues, Laplacian-of-Gaussian
- **Why it catches unmapped faults:** Different scales detect faults of different displacements
- **Difference:** Uses full band stack + ensemble instead of single-scale gradients

### H2: Cross-band coherence detection
- **Layer:** All geophysical families
- **Signature:** Agreement of gradient directions across independent feature families
- **Why it catches unmapped faults:** True faults disrupt multiple geophysical fields simultaneously
- **Difference:** Requires multi-family agreement, reducing false positives from single-band artifacts

### H3: Proximity-weighted emission near catalogue faults
- **Layer:** Catalogue faults + structural features
- **Signature:** Distance-decay predictions from known faults along structural trends
- **Why it catches unmapped faults:** Faults have damage zones, extensions, and splays not in the catalogue
- **Difference:** Uses catalogue as seeds for structural extension, not just labels

### H4: DEM-derived topographic analysis (external data required)
- **Layer:** 1m DEM from CSV links provided by competition
- **Signature:** High-resolution fault scarps, displaced stream channels, triangular facets
- **Why it catches unmapped faults:** Topographic expression of faults at 1m is far more detailed than 100m features
- **Data source:** `1m_DEM_links.csv` on competition data page (requires login + download)

### H5: Earthquake clustering analysis
- **Layer:** Band 15 (earthquake density) + structural features
- **Signature:** Linear clusters of seismicity aligned with structural discontinuities
- **Why it catches unmapped faults:** Active faults produce seismicity even when unmapped at the surface
- **Difference:** Uses seismicity as primary indicator instead of secondary feature

## Limitations

- **No organizer receipt exists** — no competition score is claimed; the local validation AUC measures catalogue-fault detection, not new-fault detection
- **AUC 0.715 is moderate** — the model has meaningful but not strong discrimination; a UNet would likely perform better
- **Holdout measures catalogue recovery** — the competition scores NEW faults not in any public database
- **No external data used** — the 1m DEM, aeroradiometric, and seismicity data could significantly improve results but require download from the competition data page (login required)
- **CPU-only training** — GPU would enable UNet training for much better spatial pattern recognition
- **2 CPUs, ~4 GB RAM** — limits model complexity and feature computation

## Reproduction

```bash
# Install dependencies
pip install numpy scipy scikit-learn rasterio scikit-image pandas pytest

# Fetch the19-band feature stack (~419 MB)
bash scripts/fetch_feature_stack.sh

# Run the ML submission pipeline (~5 minutes)
PYTHONPATH=src python3 scripts/generate_submission_v2.py

# Verify format
PYTHONPATH=src python3 -c "
import rasterio, numpy as np
with rasterio.open('docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif') as src:
    a = src.read(1)
    assert a.dtype == np.float32
    assert a.shape == (3730, 3292)
    assert np.isfinite(a).all()
    assert a.min() >= 0 and a.max() <= 1
    print('All checks passed')
"
```

## Project Files

| File | Description |
|---|---|
| `docs/executive-summary.html` | Download page with submission instructions |
| `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.tif` | Verified submission GeoTIFF |
| `docs/downloads/gems58-ml-binary-ridge-20261012T000000Z.zip` | Same file as ZIP |
| `scripts/generate_submission_v2.py` | ML submission pipeline |
| `src/gems57/` | Shared template (metric, holdout, writer) |
| `PROMPT.md` | Full operating contract |
| `REMAINING_WORK.md` | Status and next steps |

---

## Arena AI Core Values

**Maximize P(Win):** In every decision, weigh tradeoffs, assess risk, and choose the path that maximizes probability of success. Set aside emotions and make tough decisions.

**Own the Outcome:** Own results end to end — not just our individual slice. When problems arise and we have the means to act, do so without waiting for permission. Treat failure and success as signals and use them to improve.

---

*Last updated: 2026-10-12. All format checks verified against `sample_submission.tif` template.*