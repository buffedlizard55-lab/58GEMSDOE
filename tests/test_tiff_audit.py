from __future__ import annotations

from scripts.audit_current_tiff import (
    DEFAULT_EXPECTED_DECODED_SHA256,
    DEFAULT_EXPECTED_POSITIVES,
    DEFAULT_EXPECTED_SHA256,
    DEFAULT_SAMPLE,
    DEFAULT_TIF,
    audit_candidate,
)


def test_current_tiff_and_zip_pass_independent_local_audit():
    report = audit_candidate(
        DEFAULT_TIF,
        DEFAULT_SAMPLE,
        DEFAULT_TIF.with_suffix(".zip"),
        expected_sha256=DEFAULT_EXPECTED_SHA256,
        expected_decoded_sha256=DEFAULT_EXPECTED_DECODED_SHA256,
        expected_positives=DEFAULT_EXPECTED_POSITIVES,
    )
    assert report["all_checks_passed"] is True
    assert report["positive_pixels"] == 40_768
    assert report["candidate_metadata"]["crs"] == "EPSG:32611"
    assert report["inside_unique_values"] == [0.0, 1.0]
    assert report["checks"]["zip_contains_exactly_this_tiff_and_roundtrips"] is True
    assert "Does not establish portal acceptance" in report["scope_note"]
