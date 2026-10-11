#!/usr/bin/env python3
"""Independently audit the current TIFF bytes and ZIP against the official sample grid.

This is a local file-format/value audit only. It does not run a holdout, registry
scan, portal validation, slot decision, or upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIF = ROOT / "docs/downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif"
DEFAULT_SAMPLE = ROOT / "data/official/sample_submission.tif"
DEFAULT_OUTPUT = ROOT / "evidence/ribbon/file_audit.json"
DEFAULT_EXPECTED_SHA256 = "ecf833f8ea7a6698636b48b0dcd0d03aa925d603753e60e03d9d1660922711dd"
DEFAULT_EXPECTED_DECODED_SHA256 = "420cb56fcddb0b26d568d7eb61c477275671d230712c54ef03fbc9f4e5d3008d"
DEFAULT_EXPECTED_POSITIVES = 40768


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_candidate(tif: Path, sample: Path, zip_path: Path,
                    *, expected_sha256: str | None = None,
                    expected_decoded_sha256: str | None = None,
                    expected_positives: int | None = None) -> dict:
    tif, sample, zip_path = Path(tif), Path(sample), Path(zip_path)
    if not tif.is_file() or not sample.is_file() or not zip_path.is_file():
        raise FileNotFoundError("candidate TIFF, official sample, or ZIP is missing")
    with rasterio.open(sample) as ds:
        sample_array = ds.read(1)
        sample_meta = {
            "count": ds.count, "dtype": ds.dtypes[0], "crs": str(ds.crs),
            "shape": [ds.height, ds.width], "transform": list(tuple(ds.transform)[:6]),
            "nodata_is_nan": ds.nodata is not None and math.isnan(float(ds.nodata)),
        }
    footprint = np.isfinite(sample_array)
    with rasterio.open(tif) as ds:
        array = ds.read(1)
        meta = {
            "count": ds.count, "dtype": ds.dtypes[0], "crs": str(ds.crs),
            "shape": [ds.height, ds.width], "transform": list(tuple(ds.transform)[:6]),
            "nodata_is_nan": ds.nodata is not None and math.isnan(float(ds.nodata)),
        }
    if array.shape != footprint.shape:
        raise ValueError(f"candidate shape {array.shape} does not match sample {footprint.shape}")
    decoded_sha256 = sha256_bytes(np.ascontiguousarray(array).tobytes(order="C"))
    inside = array[footprint]
    outside = array[~footprint]
    positives = int((inside > 0).sum())
    inside_values = np.unique(inside)
    data = tif.read_bytes()
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        zip_has_one_candidate = names == [tif.name]
        zip_roundtrip = zip_has_one_candidate and archive.read(tif.name) == data
    file_sha256 = sha256_bytes(data)
    checks = {
        "single_band_float32": meta["count"] == 1 and meta["dtype"] == "float32",
        "crs_shape_transform_match_sample": (
            meta["crs"] == sample_meta["crs"]
            and meta["shape"] == sample_meta["shape"]
            and meta["transform"] == sample_meta["transform"]
        ),
        "nodata_nan_metadata_matches_sample": meta["nodata_is_nan"] == sample_meta["nodata_is_nan"],
        "inside_footprint_finite": bool(np.isfinite(inside).all()),
        "inside_footprint_values_in_unit_interval": bool(
            np.isfinite(inside).all() and (inside >= 0).all() and (inside <= 1).all()),
        "inside_footprint_unique_values_zero_one": np.array_equal(
            inside_values, np.array([0.0, 1.0], dtype=inside_values.dtype)),
        "outside_footprint_nan_like_sample": bool(
            np.isnan(sample_array[~footprint]).all() and np.isnan(outside).all()),
        "positive_pixel_count_matches_record": expected_positives is None or positives == expected_positives,
        "tiff_sha256_matches_record": expected_sha256 is None or file_sha256 == expected_sha256,
        "decoded_pixel_sha256_matches_record": (
            expected_decoded_sha256 is None or decoded_sha256 == expected_decoded_sha256),
        "zip_contains_exactly_this_tiff_and_roundtrips": bool(zip_roundtrip),
    }
    return {
        "evidence_class": "LOCAL-FILE-AUDIT",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file": str(tif.relative_to(ROOT)) if tif.is_relative_to(ROOT) else str(tif),
        "zip_file": str(zip_path.relative_to(ROOT)) if zip_path.is_relative_to(ROOT) else str(zip_path),
        "sample_file": str(sample.relative_to(ROOT)) if sample.is_relative_to(ROOT) else str(sample),
        "sha256": file_sha256,
        "decoded_prediction_sha256": decoded_sha256,
        "zip_sha256": sha256_file(zip_path),
        "bytes": len(data),
        "positive_pixels": positives,
        "inside_unique_values": inside_values.tolist(),
        "candidate_metadata": meta,
        "sample_metadata": sample_meta,
        "zip_members": names,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "scope_note": (
            "Local TIFF/ZIP grid and value audit only. Does not establish portal acceptance, "
            "registry uniqueness, promotion-grade holdout, organizer score, or submit eligibility."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tif", type=Path, default=DEFAULT_TIF)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-sha256", default=DEFAULT_EXPECTED_SHA256)
    parser.add_argument("--expected-decoded-sha256", default=DEFAULT_EXPECTED_DECODED_SHA256)
    parser.add_argument("--expected-positives", type=int, default=DEFAULT_EXPECTED_POSITIVES)
    args = parser.parse_args(argv)
    zip_path = args.zip_path or args.tif.with_suffix(".zip")
    try:
        report = audit_candidate(
            args.tif, args.sample, zip_path,
            expected_sha256=args.expected_sha256,
            expected_decoded_sha256=args.expected_decoded_sha256,
            expected_positives=args.expected_positives,
        )
    except (OSError, ValueError, zipfile.BadZipFile, rasterio.errors.RasterioError) as exc:
        print(f"LOCAL FILE AUDIT FAILED: {exc}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"LOCAL FILE AUDIT {'PASSED' if report['all_checks_passed'] else 'FAILED'}: "
          f"{report['positive_pixels']:,} positives; SHA-256 {report['sha256']}; "
          f"{sum(report['checks'].values())}/{len(report['checks'])} checks.")
    print(report["scope_note"])
    return 0 if report["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
