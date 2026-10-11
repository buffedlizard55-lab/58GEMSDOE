"""Inventory and sanity-check the competition rasters in data/.

Outputs data/inventory.json: grid metadata, band descriptions, label counts, and a
single-feature leakage canary (AUC of each raw band against held-out fault pixels).
Any band with AUC > 0.90 is flagged as a leakage suspect.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gems.holdout import leakage_canary, make_folds

DATA = Path(os.environ.get("GEMS_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
FEATURES = DATA / "gems-geodawn-numerical-features.tif"
LABELS = DATA / "existing_faults.tif"


def main() -> int:
    if not FEATURES.exists() or not LABELS.exists():
        print(f"missing {FEATURES.name} or {LABELS.name} in data/. Run scripts/fetch_data.py "
              "or place the files manually.")
        return 2
    out = {}
    with rasterio.open(FEATURES) as f, rasterio.open(LABELS) as l:
        out["features"] = {"shape": [f.height, f.width], "bands": f.count, "crs": f.crs.to_string(),
                           "res": f.res, "transform": list(f.transform)[:6], "nodata": f.nodata}
        out["labels"] = {"shape": [l.height, l.width], "crs": l.crs.to_string(), "res": l.res,
                         "transform": list(l.transform)[:6], "nodata": l.nodata}
        out["grid_aligned"] = (f.height, f.width) == (l.height, l.width) and \
            tuple(f.transform)[:6] == tuple(l.transform)[:6] and f.crs == l.crs
        lab = l.read(1)
        lab_bin = (lab == 1) if l.nodata is None else ((lab == 1) & (lab != l.nodata))
        out["label_counts"] = {"fault_pixels": int(lab_bin.sum()),
                               "values": {str(v): int(c) for v, c in
                                          zip(*np.unique(lab, return_counts=True))}}
        feats = f.read().astype(np.float64)
        bands = [f.tags(i + 1) for i in range(f.count)]
        out["band_descriptions"] = [b.get("description", "") for b in bands]
        nd = f.nodata
    feats[feats < -1e38] = np.nan
    valid = np.all(np.isfinite(feats), axis=0)
    folds = make_folds(lab_bin, n_folds=5, buffer_px=3, seed=0)
    f0 = folds[0]
    canary_mask = valid & ~f0.buffer & ~f0.visible
    canary = []
    for i in range(feats.shape[0]):
        r = leakage_canary(feats[i], f0.withheld, canary_mask)
        canary.append({"band": i + 1, **r})
    out["leakage_canary_fold0"] = canary
    out["flagged_bands"] = [c["band"] for c in canary if c["suspect_leakage"]]
    (DATA / "inventory.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({k: out[k] for k in ("grid_aligned", "label_counts", "flagged_bands")},
                     indent=2, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
