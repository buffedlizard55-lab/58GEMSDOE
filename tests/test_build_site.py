import hashlib

from scripts import build_site


def good_evidence():
    return {
        "e1": {
            "promotion_grade": True,
            "buffered_whole_component_context_used": True,
            "promotion_grade_sigma_table": [
                {"evidence_class": "HOLDOUT-STRUCTURE", "block": "NW", "ridge_type": "cat-axis", "sigma_px": 1.8, "n_matched": 12}
            ],
            "leakage_canary": {"max_auc_by_type": {"cat-axis": 0.90, "sgmc-axis": 0.81}},
        },
        "e2": {
            "promotion_grade": True,
            "promotion_grade_result": {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": "gems57-pooled-hide-v2",
                "withheld_positive_pixels": 1200,
                "dti": 0.42,
                "ci95": [0.37, 0.47],
                "ci_method": "paired spatial-block bootstrap",
                "per_class_gains": {
                    "cat-axis": {
                        "evidence_class": "HOLDOUT-DTI",
                        "evaluator_version": "gems57-pooled-hide-v2",
                        "withheld_positive_pixels": 1200,
                        "gain": 0.03,
                        "ci95": [-0.01, 0.07],
                        "ci_method": "paired physical-block bootstrap",
                    }
                },
            },
        },
        "uniq": {
            "unique": True,
            "rho_limit": 0.90,
            "overlap_limit": 0.70,
            "preplacement_surface_gate": {
                "passed": True,
                "worst_spearman_full_footprint": 0.90,
                "worst_dot_overlap": 0.70,
            },
            "final_dot_gate": {
                "passed": True,
                "worst_spearman_full_footprint": 0.90,
                "worst_dot_overlap": 0.70,
                "overlap_limit": 0.70,
            },
        },
        "freshness": {"fresh_current_inventory": True},
    }


def good_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(build_site, "DL", tmp_path)
    data = b"qualification gate test raster bytes"
    (tmp_path / "candidate.tif").write_bytes(data)
    return {
        "file": "candidate.tif",
        "sha256": hashlib.sha256(data).hexdigest(),
        "promotion_grade": True,
        "submission_name": "candidate-001",
        "note": "qualified local candidate; selector remains separate",
        "validator": {"all_checks_passed": True},
    }


def test_qualification_gaps_accept_only_complete_evidence_at_inclusive_limits(tmp_path, monkeypatch):
    e = good_evidence()
    receipt = good_receipt(tmp_path, monkeypatch)
    assert build_site.qualification_gaps(
        e["e1"], e["e2"], e["uniq"], e["freshness"], receipt
    ) == []


def test_literal_thresholds_are_strictly_greater_than():
    e = good_evidence()
    e["uniq"]["preplacement_surface_gate"]["worst_spearman_full_footprint"] = 0.900001
    gaps = build_site.qualification_gaps(
        e["e1"], e["e2"], e["uniq"], e["freshness"], {"file": "missing.tif"}
    )
    assert any("pre-placement surface rank-correlation" in gap for gap in gaps)

    e = good_evidence()
    e["uniq"]["final_dot_gate"]["worst_dot_overlap"] = 0.700001
    gaps = build_site.qualification_gaps(
        e["e1"], e["e2"], e["uniq"], e["freshness"], {"file": "missing.tif"}
    )
    assert any("final dots literal-dot gate" in gap for gap in gaps)


def test_holdout_score_requires_shared_version_positive_count_and_valid_ci():
    e2 = good_evidence()["e2"]
    assert build_site.validated_holdout_result(e2)["evidence_class"] == "HOLDOUT-DTI"

    e2["promotion_grade_result"]["ci95"] = [0.5, 0.4]
    assert build_site.validated_holdout_result(e2) == {}


def test_bad_canary_and_stale_inventory_fail_closed(tmp_path, monkeypatch):
    e = good_evidence()
    e["e1"]["leakage_canary"]["max_auc_by_type"]["cat-axis"] = 0.91
    e["freshness"]["fresh_current_inventory"] = False
    receipt = good_receipt(tmp_path, monkeypatch)
    gaps = build_site.qualification_gaps(
        e["e1"], e["e2"], e["uniq"], e["freshness"], receipt
    )
    assert any("exceeds AUC 0.90" in gap for gap in gaps)
    assert any("stale/incomplete" in gap for gap in gaps)
