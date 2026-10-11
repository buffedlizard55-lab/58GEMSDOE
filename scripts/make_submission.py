"""Write and validate a submission GeoTIFF from a probability raster.

usage: python scripts/make_submission.py PROB.npy OUT.tif --reference data/example_submission.tif
PROB.npy must be a (H, W) float array in [0,1] inside the footprint.
"""

import argparse
import json
import sys

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gems.submission import write


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prob")
    ap.add_argument("out")
    ap.add_argument("--reference", required=True)
    a = ap.parse_args()
    prob = np.load(a.prob)
    rep = write(prob, a.out, a.reference)
    print(json.dumps(rep, indent=2, default=str))
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
