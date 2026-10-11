from __future__ import annotations

from scripts.audit_sparse_candidate import (
    WITNESS_SHA256,
    should_preserve_direct_witness_receipt,
)


CANDIDATE_SHA256 = "a" * 64


def _receipt(*, candidate_sha=CANDIDATE_SHA256, direct=True, witness_sha=WITNESS_SHA256):
    measurement = {
        "direct_current_file_measurement": direct,
        "expected_sha256": witness_sha,
        "sha256_verified": direct,
        "literal_overlap_trigger": direct,
        "observed_candidate_dot_overlap_within_3_px": 1.0 if direct else None,
    }
    return {
        "artifact_sha256": candidate_sha,
        "correlation_overlap_vs_registry": {
            "final_dots": {
                "witnesses_directly_checked": 1 if direct else 0,
                "witness_measurement": measurement,
            }
        },
    }


def test_inference_only_rerun_does_not_replace_a_direct_receipt_for_same_bytes():
    prior = _receipt()
    inference_only = _receipt(direct=False)
    assert should_preserve_direct_witness_receipt(prior, inference_only)


def test_changed_candidate_or_repeated_direct_scan_can_replace_receipt():
    prior = _receipt()
    assert not should_preserve_direct_witness_receipt(
        prior, _receipt(candidate_sha="b" * 64, direct=False))
    assert not should_preserve_direct_witness_receipt(
        prior, _receipt(direct=True))


def test_unverified_or_nontriggering_prior_is_not_protected_as_a_direct_stop():
    prior = _receipt(witness_sha="b" * 64)
    assert not should_preserve_direct_witness_receipt(prior, _receipt(direct=False))
    prior = _receipt()
    prior["correlation_overlap_vs_registry"]["final_dots"]["witness_measurement"][
        "literal_overlap_trigger"] = False
    assert not should_preserve_direct_witness_receipt(prior, _receipt(direct=False))
