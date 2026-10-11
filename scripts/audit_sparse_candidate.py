#!/usr/bin/env python3
"""Audit the prior session's sparse TIFF without granting submit eligibility.

This script only re-reads the existing bytes. It does not emit or rewrite a TIFF,
run a holdout, fit sigma, choose ribbon geometry, use a slot, or upload anything.
A local format pass and a measured overlap trigger are reported separately.

Run from the repository root:
    PYTHONPATH=src python scripts/audit_sparse_candidate.py

For an independent, hash-pinned witness measurement, restore the named witness
from the public GitHub blob into .cache/registry/universal-blocker.tif first.
The file is deliberately not committed; its SHA-256 and source are recorded in
the resulting evidence receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import load_grid  # noqa: E402
from gems57.uniqueness import dot_overlap, saturation_certificate  # noqa: E402
from gems57.validate import validate  # noqa: E402

CARD_PATH = ROOT / "evidence/58gemsdoe_unique_ribbon/run_card.json"
INDEX_PATH = ROOT / "registry/registry_merged.json"
PRIOR_SCAN_PATH = ROOT / "evidence/ribbon/uniqueness_full_inventory.json"
FRESHNESS_PATH = ROOT / "evidence/registry_freshness_audit.json"
DEFAULT_WITNESS = ROOT / ".cache/registry/universal-blocker.tif"
DEFAULT_OUTPUT = ROOT / "evidence/58gemsdoe_unique_ribbon/audit.json"
WITNESS_SHA256 = "03d619fa75689b48bd3eb4f74c3fa529a9b04c19bd716e15640d910baf3d5a90"
WITNESS_SOURCE = "GEMSDOE2:data/evidence/runs/turbo-simple-20260925T042003Z/submission.tif"
OVERLAP_RADIUS_PX = 3.0
OVERLAP_LIMIT = 0.70


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes(order="C")).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reference_grid(sample: Path) -> tuple[tuple[int, int], object, object]:
    with rasterio.open(sample) as src:
        return src.shape, src.crs, src.transform


def _inventory_witness_record() -> dict:
    """Bind the known universal blocker to the prior complete-accessible scan."""
    prior = read_json(PRIOR_SCAN_PATH)
    index = read_json(INDEX_PATH)
    rows = [row for row in prior.get("rows", [])
            if row.get("sha256") == WITNESS_SHA256
            and row.get("submission") == WITNESS_SOURCE]
    pins = [row for row in index.get("rasters", [])
            if row.get("sha256") == WITNESS_SHA256
            and WITNESS_SOURCE in row.get("sources", [])]
    if len(rows) != 1 or len(pins) != 1:
        raise ValueError("the pinned witness is not uniquely bound in the prior scan and registry index")
    row = rows[0]
    if float(row.get("chance_expected_overlap", -1.0)) != 1.0:
        raise ValueError("the prior inventory no longer records exact footprint coverage for the witness")
    return {
        "prior_scan_complete_accessible_scan": prior.get("complete_accessible_scan"),
        "prior_scan_rasters_checked": prior.get("registry_rasters_checked"),
        "prior_scan_generated_utc": prior.get("generated_utc"),
        "registry_index_generated_utc": index.get("generated_utc"),
        "witness_source": WITNESS_SOURCE,
        "witness_sha256": WITNESS_SHA256,
        "witness_positive_cells_in_prior_receipt": row.get("their_dots"),
        "chance_expected_overlap_in_prior_receipt": row.get("chance_expected_overlap"),
        "prior_row_candidate_overlap": row.get("my_dots_within_3px_of_theirs"),
        "prior_row_overlap_is_not_reused_for_current_candidate": True,
        "index_pin_matches_source": True,
    }


def audit_candidate(tif: Path, sample: Path, witness: Path | None) -> dict:
    tif, sample = Path(tif), Path(sample)
    if not tif.is_file() or not sample.is_file():
        raise FileNotFoundError("candidate TIFF or sample grid is missing")
    card = read_json(CARD_PATH)
    grid = load_grid(ROOT / "data/bridge")
    with rasterio.open(sample) as src:
        sample_meta = (src.count, src.dtypes[0], src.shape, src.crs, src.transform)
        footprint_from_sample = np.isfinite(src.read(1))
    if not np.array_equal(footprint_from_sample, grid.footprint):
        raise ValueError("the bridged sample footprint and shared grid footprint disagree")

    with rasterio.open(tif) as src:
        candidate = src.read(1)
        candidate_meta = (src.count, src.dtypes[0], src.shape, src.crs, src.transform)
        meta = {
            "band_count": src.count,
            "dtype": src.dtypes[0],
            "shape": [src.height, src.width],
            "crs": str(src.crs),
            "transform": list(tuple(src.transform)[:6]),
            "nodata": None if src.nodata is None else float(src.nodata),
        }
    if candidate.shape != grid.shape:
        raise ValueError("candidate shape does not match the shared study grid")

    local = validate(tif, footprint=grid.footprint, catalogue=grid.catalogue)
    sample_grid_match = candidate_meta[2:] == sample_meta[2:]
    positive = np.isfinite(candidate) & (candidate > 0)
    positive_in_footprint = positive & grid.footprint
    file_sha = sha256_file(tif)
    pixel_sha = sha256_array(candidate)
    positives = int(positive.sum())
    decoded_positive_values = np.unique(candidate[positive]).tolist()

    zip_path = tif.with_suffix(".zip")
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.namelist()
        zip_exactly_one_tif = len(members) == 1 and members[0].lower().endswith((".tif", ".tiff"))
        zip_roundtrip = bool(zip_exactly_one_tif and archive.read(members[0]) == tif.read_bytes())

    format_checks = dict(local["checks"])
    format_checks["matches_sample_grid_metadata"] = bool(sample_grid_match)
    format_checks["positive_pixels_are_exactly_one"] = bool(
        positives > 0 and np.array_equal(np.unique(candidate[positive]), np.array([1.0], dtype=candidate.dtype)))
    format_checks["single_tiff_zip_roundtrip"] = zip_roundtrip
    expected_file_sha = card.get("raster_sha256") or card.get("sha256")
    expected_file_name = card.get("artifact_file") or card.get("file")
    format_checks["recorded_file_sha256_matches"] = (
        file_sha == expected_file_sha and tif.name == Path(str(expected_file_name)).name)
    format_pass = all(bool(value) for value in format_checks.values())

    prior_witness = _inventory_witness_record()
    expected_grid = _reference_grid(sample)
    witness_result = {
        "source": WITNESS_SOURCE,
        "expected_sha256": WITNESS_SHA256,
        "prior_inventory_evidence": prior_witness,
        "direct_current_file_measurement": False,
    }
    if witness is not None and Path(witness).is_file():
        witness = Path(witness)
        witness_sha = sha256_file(witness)
        if witness_sha != WITNESS_SHA256:
            raise ValueError(f"witness SHA-256 mismatch: {witness_sha} != {WITNESS_SHA256}")
        coverage = saturation_certificate(
            witness, grid.footprint, expected_grid=expected_grid)
        with rasterio.open(witness) as witness_ds:
            witness_array = witness_ds.read(1)
        overlap = dot_overlap(candidate, witness_array, OVERLAP_RADIUS_PX)
        witness_result.update({
            "direct_current_file_measurement": True,
            "witness_file": str(witness.relative_to(ROOT)) if witness.is_relative_to(ROOT) else str(witness),
            "sha256_verified": True,
            "coverage_certificate": coverage,
            "observed_candidate_dot_overlap_within_3_px": float(overlap),
            "literal_overlap_threshold": OVERLAP_LIMIT,
            "literal_overlap_trigger": bool(overlap > OVERLAP_LIMIT),
            "rank_correlation": "undefined for an all-positive constant witness; overlap independently triggers",
        })
    else:
        witness_result.update({
            "direct_current_file_measurement": False,
            "observed_candidate_dot_overlap_within_3_px": None,
            "literal_overlap_trigger": None,
            "inference": (
                "Prior byte-pinned inventory records that this witness has positive support on every "
                "footprint cell (E=1). If its hash-pinned contents are unchanged, any nonempty "
                "in-footprint candidate has overlap 1.0. This is an implication, not a fresh candidate scan."
            ),
        })

    freshness = read_json(FRESHNESS_PATH)
    prior_scan = read_json(PRIOR_SCAN_PATH)
    current_inventory_complete = bool(freshness.get("fresh_current_inventory") is True)
    overlap_value = witness_result.get("observed_candidate_dot_overlap_within_3_px")
    overlap_trigger = (overlap_value > OVERLAP_LIMIT if overlap_value is not None
                       else bool(prior_witness["witness_positive_cells_in_prior_receipt"]
                                 == int(grid.footprint.sum())))

    checks = {
        "local_format_range_audit": format_pass,
        "one_hash_pinned_registry_witness_tested": bool(witness_result["direct_current_file_measurement"]),
        "final_dot_overlap_gate_clear": not overlap_trigger,
        "preplacement_surface_gate_measured": False,
        "current_registry_freshness_clear": current_inventory_complete,
    }
    verdict = "negative" if not all(checks.values()) else "promote"
    return {
        "evidence_class": "LOCAL-FILE-AUDIT + REGISTRY-MEASUREMENT",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact": str(tif.relative_to(ROOT)) if tif.is_relative_to(ROOT) else str(tif),
        "public_review_record": (str(tif.with_suffix(".audit.json").relative_to(ROOT))
                                 if tif.is_relative_to(ROOT / "docs" / "downloads") else None),
        "artifact_sha256": file_sha,
        "decoded_prediction_sha256": pixel_sha,
        "artifact_bytes": tif.stat().st_size,
        "positive_pixels_local_format_audit": positives,
        "positive_values": decoded_positive_values,
        "candidate_metadata": meta,
        "format_checks": format_checks,
        "format_checks_passed": sum(bool(value) for value in format_checks.values()),
        "format_checks_total": len(format_checks),
        "format_pass": format_pass,
        "footprint_cells_local_grid": int(grid.footprint.sum()),
        "catalogue_positive_overlap_local_format_audit": int((positive & grid.catalogue).sum()),
        "zip_members": members,
        "zip_roundtrip": zip_roundtrip,
        "correlation_overlap_vs_registry": {
            "preplacement_surface": {
                "status": "NOT MEASURED",
                "reason": "No placement-surface raster, generating script, or candidate-specific pre-placement receipt exists for this artifact.",
            },
            "final_dots": {
                "status": "FAIL — literal overlap stop",
                "overlap_radius_px": OVERLAP_RADIUS_PX,
                "overlap_limit": OVERLAP_LIMIT,
                "witnesses_directly_checked": 1 if witness_result["direct_current_file_measurement"] else 0,
                "witness_measurement": witness_result,
                "inventory_snapshot": {
                    "rasters_checked_in_prior_full_scan": prior_scan.get("registry_rasters_checked"),
                    "prior_scan_complete_for_its_frozen_scope": prior_scan.get("complete_accessible_scan"),
                    "fresh_current_inventory": freshness.get("fresh_current_inventory"),
                    "freshness_decision": freshness.get("decision"),
                },
                "byte_or_pixel_copy_claim": False,
                "interpretation": (
                    "This is a fail/stop under the user's literal lane-drift criterion, not a claim of byte- or pixel-copying."
                ),
            },
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "NOT MEASURED",
            "value": None,
            "evaluator_version_required": "gems57-pooled-hide-v2",
            "protocol": "buffered whole-segment hide-and-recover with exact visible-catalogue mask; not run",
            "withheld_positive_count": None,
            "ci95": None,
            "reason": "No promotion-grade holdout receipt exists for this artifact; experiment stopped at the literal uniqueness gate.",
        },
        "sigma_table": "NOT MEASURED",
        "simulated_gain_per_class": "NOT MEASURED",
        "leakage_canary": {"status": "NOT RUN", "feature_alone_auc": None},
        "submission_name": "58GEMSDOE-ribbon-sparse-diagnostic-20261011T182511Z",
        "submission_note": "Diagnostic only; uniqueness and holdout gates are not cleared.",
        "submission_note_characters": len("Diagnostic only; uniqueness and holdout gates are not cleared."),
        "submission_identifier_is_authorized": False,
        "verdict": verdict,
        "stop_required": True,
        "experiments_run_this_review": 0,
        "slots_used": 0,
        "limitations": [
            "The registry scan is a dated public owner-repository snapshot; freshness is blocked.",
            "The pre-placement surface and its generating lineage are absent.",
            "The locally restored feature stack is pinned to an owner-maintained GitHub bridge, not independently authenticated as an organizer download.",
            "A format pass is not DrivenData portal acceptance or an organizer score.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tif", type=Path, default=None,
                        help="default: file named by the existing local run card")
    parser.add_argument("--sample", type=Path,
                        default=ROOT / "data/official/sample_submission.tif")
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS,
                        help="optional downloaded, sha256-pinned registry witness")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    card = read_json(CARD_PATH)
    file_name = card.get("artifact_file") or card.get("file")
    if not file_name:
        raise SystemExit("run card does not name an artifact file")
    default_tif = ROOT / str(file_name)
    if not default_tif.is_file():
        default_tif = ROOT / "docs/downloads" / str(file_name)
    tif = args.tif or default_tif
    witness = args.witness if args.witness and args.witness.is_file() else None
    try:
        report = audit_candidate(tif, args.sample, witness)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, rasterio.errors.RasterioError) as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
    args.output.write_text(serialized, encoding="utf-8")
    public_record = report.get("public_review_record")
    if public_record:
        (ROOT / public_record).write_text(serialized, encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "format_pass": report["format_pass"],
        "format_checks": f"{report['format_checks_passed']}/{report['format_checks_total']}",
        "direct_witness_measurement": report["correlation_overlap_vs_registry"]["final_dots"]["witnesses_directly_checked"],
        "overlap": report["correlation_overlap_vs_registry"]["final_dots"]["witness_measurement"].get("observed_candidate_dot_overlap_within_3_px"),
        "stop_required": report["stop_required"],
        "receipt": str(args.output),
    }, indent=2))
    return 0 if report["format_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
