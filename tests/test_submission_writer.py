from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gems57.submission_writer import write_submission

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "official" / "sample_submission.tif"


def test_writer_receipt_binds_exact_decoded_float32_pixels(tmp_path):
    with rasterio.open(SAMPLE) as src:
        template = src.read(1)
        footprint = np.isfinite(template)
    prediction = np.zeros(footprint.shape, dtype=np.float32)
    # Place a single legal positive deterministically without depending on array
    # view semantics of chained boolean indexing.
    y, x = np.argwhere(footprint)[0]
    prediction[y, x] = 1.0

    path = tmp_path / "writer-hash-test.tif"
    receipt = write_submission(
        path, prediction, SAMPLE, footprint,
        note="test local format only", name="writer-hash-test",
    )

    with rasterio.open(path) as written:
        decoded = written.read(1)
    expected = hashlib.sha256(np.ascontiguousarray(decoded).tobytes(order="C")).hexdigest()
    assert receipt["decoded_prediction_sha256"] == expected
    assert len(expected) == 64
    sidecar = json.loads(path.with_suffix(".json").read_text())
    assert sidecar["decoded_prediction_sha256"] == expected
    assert sidecar["status"].startswith("local format/range preflight only")
    assert sidecar["approved_for_weekly_slot"] is False
    assert sidecar["promoted"] is False
