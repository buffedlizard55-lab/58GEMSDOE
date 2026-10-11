"""The site builder must fail closed: a banner can only turn green on complete evidence.

These tests replace the previous ``qualification_gaps`` suite (the gate engine was
rewritten around the current receipts) and keep every guarantee it encoded:
inclusive stop limits, no pass without a receipt, no pass on a canary at the
limit, and — new — no pass when the bytes on disk do not match the recorded
sha256.  Gate G6 (an organizer receipt) can never pass from this sandbox and is
asserted to stay open even when everything else clears.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import build_site


def _write_bytes(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


@pytest.fixture()
def evidence(tmp_path):
    """A complete, internally consistent set of receipts plus the raster bytes."""
    tif = tmp_path / "downloads" / "candidate.tif"
    sha = _write_bytes(tif, b"not really a geotiff; the gate engine only hashes bytes")
    emi = {
        "name": "candidate",
        "file": str(tif),
        "sha256": sha,
        "validator": {
            "passed": True,
            "bytes": tif.stat().st_size,
            "n_positives": 40768,
            "checks": {
                "finite_inside_footprint": {"ok": True, "detail": "NaN inside footprint = 0"},
                "values_in_unit_interval": {"ok": True, "detail": "min=0.000 max=1.000"},
                "positive_is_exactly_one": {"ok": True, "detail": "unique positives = [1.0]"},
            },
        },
        "uniqueness_local": {
            "cleared": True, "n_checked": 27, "worst_rho": 0.18, "worst_forward_overlap": 0.60,
            "worst_forward_overlap_name": "own-earlier-file", "n_overlap_firings_informative": 0,
            "n_saturated_witnesses": 0, "lane_drift_evidence": "none",
        },
        "holdout_dti": {"pooled": 0.043651, "per_fold": {"NW": 0.046, "NE": 0.036},
                        "n_withheld_positives": 60869, "protocol": "gems58-pooled-hide-v1",
                        "evaluator": "gems58w.metric/v1", "ci": {"lo": 0.033, "hi": 0.056},
                        "coverage": 0.0561},
        "catalogue_distance_profile": {"on_catalogue": 0, "median_px": 19.7, "frac_le_3px": 0.106,
                                       "frac_le_10px": 0.309},
        "design": {"threshold": 0.45, "dti0": 0.4133,
                   "lines_per_segment_histogram": {3: 492, 5: 5794},
                   "budget": {"budget": 40768, "n_files": 12,
                              "rule": "median dot count of the owner-reported >= 0.24 family"}},
        "credit_calibration": {"khat_min": 0.0, "khat_max": 0.0345,
                               "marginal_bar_at_dti0": 0.08266, "n_ridge_px": 396795,
                               "khat_by_stratum": {"magnetic|q0": 0.0107, "all|q9": 0.0122}},
        "generated_utc": "2026-10-11T05:29:42Z",
    }
    card = {"submission_note": "Ribbon lane: adaptive dotted ribbons; 40768 isolated dots at 1.0.",
            "name": "candidate", "raster_sha256": sha}
    sig = {"threshold": 0.6, "n_segments": 3024, "ridge_pixels": 163782,
           "leakage_canary": {"combined_ridge_field": {"auc_mean": 0.529, "auc_max": 0.5955,
                                                       "n_folds": 4, "leaks": False}},
           "marginal_inclusion_bar": {"dti0": 0.4133, "alpha": 0.2, "required_credit": 0.08266,
                                      "max_distance_px": 2.752, "max_distance_m": 275.2},
           "sigma_table_all_folds": {"n_matched": 994,
                                     "pooled": {"n": 994, "median": 6.879, "mean": 7.09,
                                                "p25": 4.18, "p75": 10.3, "rms": 8.01},
                                     "by_block": {"NW": {"n": 578, "median": 7.08}},
                                     "recovery": {"median_frac_within": 1.0}}}
    inv = {"unique": True, "complete_accessible_scan": True, "n_compared": 702,
           "worst_spearman_full_footprint": 0.42, "worst_dot_overlap": 0.55,
           "worst_rho_submission": "some-repo", "worst_overlap_submission": "some-repo",
           "duplicate_count": 0, "verdict": "unique", "index": "registry/registry_merged.json",
           # RATIFIED-UNIQ-v1 additionally requires byte/pixel uniqueness flags and
           # row-level chance measurements (E) so firings can be classified.
           "byte_unique_among_checked": True, "pixel_unique_among_checked": True,
           "worst_jaccard_dot_sets": 0.05,
           "rows": [{"submission": "some-repo", "my_dots_within_3px_of_theirs": 0.55,
                     "chance_expected_overlap": 0.30, "chance_corrected_lift": 0.357,
                     "jaccard_dot_sets": 0.05, "spearman_full_footprint": 0.42}]}
    arms = {"budget": 38000, "min_sep": 1, "ranking": "k_hat", "screen": "visible+3px",
            "dti0": 0.4133, "n_withheld_positives": 60988, "evaluator": "gems58w.metric/v1",
            "results": {"W1": {"pooled": 0.042462, "coverage": 0.0554,
                               "agg": {"tp": 3369.3, "fp": 149904.7, "n_dots": 152000}},
                        "AD2": {"pooled": 0.047655, "coverage": 0.0622,
                                "agg": {"tp": 3785.1, "fp": 149876.5, "n_dots": 152000}}},
            "deltas_vs_W1": {"AD2": {"pooled_delta": 0.005194,
                                     "paired_bootstrap": {"lo": 0.00448, "hi": 0.00637, "n": 4}}},
            "simulated_gain_per_sigma_class": {
                "sigma-3-6px": {"W1": {"dti": 0.0, "n_truth": 6492}, "W3": {"dti": 0.004451},
                                "AD": {"dti": 0.004451}, "AD2": {"dti": 0.006469}}}}
    xcheck = {"verdict": "AGREE",
              "pooled": {"abs_delta_lane_vs_shared": 0.0, "shared_gems57_binary": 0.043651086,
                         "recorded_in_emission_json": 0.043651086,
                         "abs_delta_shared_vs_recorded": 0.0}}
    return dict(tif=tif, emi=emi, card=card, sig=sig, inv=inv, arms=arms, xcheck=xcheck)


def gates(evidence, **over):
    emi = json.loads(json.dumps(evidence["emi"]))
    sig = json.loads(json.dumps(evidence["sig"]))
    inv = json.loads(json.dumps(evidence["inv"]))
    if over.get("inv") is False:          # receipt absent entirely
        inv = {}
    elif "inv" in over:
        inv = over["inv"]
    if "emi" in over:
        emi = over["emi"]
    if "sig" in over:
        sig = over["sig"]
    xcheck = evidence["xcheck"]
    if over.get("xcheck") is False:
        xcheck = None
    elif "xcheck" in over:
        xcheck = over["xcheck"]
    tif = Path(over.get("tif", evidence["tif"]))
    return build_site.evaluate_gates(emi, sig, inv, tif, xcheck)


def by_id(gs):
    return {g["id"]: g for g in gs}


def test_complete_evidence_turns_the_banner_green_except_the_receipt(evidence):
    gs, ok = gates(evidence)
    g = by_id(gs)
    assert ok is True, [x["id"] for x in gs if not x["ok"]]
    assert all(g[i]["ok"] for i in ("G1", "G2", "G3", "G4", "G5", "G5i"))
    # an organizer receipt can never exist here, and must never be claimed
    assert g["G6"]["ok"] is False


def test_missing_inventory_receipt_fails_closed(evidence):
    gs, ok = gates(evidence, inv=False)
    assert ok is False
    assert by_id(gs)["G3"]["ok"] is False
    assert "missing" in by_id(gs)["G3"]["detail"]


def test_stop_limits_are_inclusive_and_strictly_enforced(evidence):
    at = json.loads(json.dumps(evidence["inv"]))
    at["worst_spearman_full_footprint"] = build_site.RHO_LIMIT
    at["worst_dot_overlap"] = build_site.OVERLAP_LIMIT
    gs, ok = gates(evidence, inv=at)
    assert by_id(gs)["G3"]["ok"] is True, "exactly at the limit is not a duplicate"
    assert ok is True

    over = json.loads(json.dumps(at))
    over["worst_dot_overlap"] = build_site.OVERLAP_LIMIT + 1e-9
    gs, ok = gates(evidence, inv=over)
    assert by_id(gs)["G3"]["ok"] is False
    assert ok is False

    over2 = json.loads(json.dumps(at))
    over2["worst_spearman_full_footprint"] = build_site.RHO_LIMIT + 1e-9
    gs, ok = gates(evidence, inv=over2)
    assert by_id(gs)["G3"]["ok"] is False
    assert ok is False

    incomplete = json.loads(json.dumps(at))
    incomplete["complete_accessible_scan"] = False
    gs, ok = gates(evidence, inv=incomplete)
    assert by_id(gs)["G3"]["ok"] is False, "an incomplete inventory can never certify uniqueness"
    assert ok is False


def test_canary_at_or_above_the_limit_fails_closed(evidence):
    for auc, expect in ((0.90, False), (0.9001, False), (0.8999, True)):
        sig = json.loads(json.dumps(evidence["sig"]))
        sig["leakage_canary"]["combined_ridge_field"]["auc_max"] = auc
        gs, ok = gates(evidence, sig=sig)
        assert by_id(gs)["G4"]["ok"] is expect, auc
        assert ok is expect


def test_bytes_that_do_not_match_the_receipt_fail_closed(evidence, tmp_path):
    other = tmp_path / "tampered.tif"
    _write_bytes(other, b"different bytes entirely")
    gs, ok = gates(evidence, tif=other)
    assert by_id(gs)["G1"]["ok"] is False
    assert "DOES NOT MATCH" in by_id(gs)["G1"]["detail"]
    assert ok is False


def test_missing_raster_fails_closed(evidence, tmp_path):
    gs, ok = gates(evidence, tif=tmp_path / "nope.tif")
    assert by_id(gs)["G1"]["ok"] is False
    assert ok is False


def test_local_uniqueness_must_be_cleared_and_non_empty(evidence):
    emi = json.loads(json.dumps(evidence["emi"]))
    emi["uniqueness_local"]["cleared"] = False
    gs, ok = gates(evidence, emi=emi)
    assert by_id(gs)["G2"]["ok"] is False
    assert ok is False

    emi2 = json.loads(json.dumps(evidence["emi"]))
    emi2["uniqueness_local"] = {"cleared": True, "n_checked": 0}
    gs, ok = gates(evidence, emi=emi2)
    assert by_id(gs)["G2"]["ok"] is False, "zero witnesses is not clearance"
    assert ok is False


def test_any_failed_local_format_check_fails_closed(evidence):
    emi = json.loads(json.dumps(evidence["emi"]))
    emi["validator"]["checks"]["values_in_unit_interval"] = {"ok": False, "detail": "max=1.5"}
    gs, ok = gates(evidence, emi=emi)
    assert by_id(gs)["G1"]["ok"] is False
    assert ok is False


def test_shared_metric_crosscheck_is_required_and_must_agree(evidence):
    """main archived the gems58w path, so the number must be re-derived with gems57."""
    gs, ok = gates(evidence, xcheck=False)
    assert by_id(gs)["G5i"]["ok"] is False
    assert ok is False

    disagree = {"verdict": "DISAGREE",
                "pooled": {"abs_delta_lane_vs_shared": 0.01,
                           "shared_gems57_binary": 0.05}}
    gs, ok = gates(evidence, xcheck=disagree)
    assert by_id(gs)["G5i"]["ok"] is False
    assert ok is False
