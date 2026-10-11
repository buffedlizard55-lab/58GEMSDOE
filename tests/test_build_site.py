"""Fail-closed tests for exact-candidate site qualification and status wording."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts import build_site


def _write(path: Path, data: bytes = b"candidate bytes") -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _valid_evidence(tmp_path):
    tif = tmp_path / "downloads" / "candidate.tif"
    file_sha = _write(tif)
    decoded_sha = "c" * 64
    index_sha = "d" * 64
    freshness_sha = "e" * 64
    inventory_sha = "f" * 64
    surface_sha = _write(tmp_path / "candidate_surface.bin", b"frozen candidate surface")
    surface_receipt_sha = _write(tmp_path / "preplacement_scan.json", b"preplacement receipt")
    canary_receipt_sha = _write(tmp_path / "canary.json", b"feature-alone receipt")
    holdout_receipt_sha = _write(tmp_path / "holdout.json", b"shared holdout receipt")
    freshness = {
        "fresh_current_inventory": True,
        "decision": "CURRENT_EXHAUSTIVE",
        "registry_index_sha256": index_sha,
        "checked_utc": "2026-10-11T12:00:00Z",
    }
    inv = {
        "candidate_file_sha256": file_sha,
        "candidate_decoded_sha256": decoded_sha,
        "unique": True,
        "stop_required": False,
        "complete_accessible_scan": True,
        "missing_or_invalid": 0,
        "source_errors": [],
        "registry_rasters_checked": 702,
        "index": "registry/registry_merged.json",
        "index_generated_utc": "2026-10-11T12:00:00Z",
        "worst_spearman_full_footprint": 0.42,
        "worst_dot_overlap": 0.55,
        "rho_limit": build_site.RHO_LIMIT,
        "overlap_limit": build_site.OVERLAP_LIMIT,
        "informative_reading": {
            "overlap_firings": 0,
            "overlap_firings_informative": 0,
            "overlap_firings_vacuous": 0,
        },
    }
    qualification = {
        "schema_version": 1,
        "submission_status": "OK_TO_SUBMIT",
        "candidate_file": "downloads/candidate.tif",
        "candidate_file_sha256": file_sha,
        "candidate_decoded_sha256": decoded_sha,
        "registry": {
            "fresh_current_inventory": True,
            "index_sha256": index_sha,
            "freshness_receipt_sha256": freshness_sha,
            "index_generated_utc": inv["index_generated_utc"],
        },
        "preplacement_surface_gate": {
            "passed": True,
            "candidate_surface_path": str(tmp_path / "candidate_surface.bin"),
            "candidate_surface_sha256": surface_sha,
            "receipt_path": str(tmp_path / "preplacement_scan.json"),
            "receipt_sha256": surface_receipt_sha,
            "registry_index_sha256": index_sha,
            "freshness_receipt_sha256": freshness_sha,
        },
        "final_dot_gate": {
            "passed": True,
            "candidate_file_sha256": file_sha,
            "candidate_decoded_sha256": decoded_sha,
            "receipt_sha256": inventory_sha,
            "registry_index_sha256": index_sha,
            "freshness_receipt_sha256": freshness_sha,
        },
        "leakage_canary": {
            "passed": True,
            "n_features_tested": 4,
            "max_single_feature_auc": 0.74,
            "features": [
                {"feature": f"feature-{i}", "auc_by_fold": {"NW": 0.61, "SE": 0.62},
                 "auc_max": 0.62, "leaks": False}
                for i in range(3)
            ] + [{"feature": "feature-3", "auc_by_fold": {"NW": 0.70, "SE": 0.74},
                  "auc_max": 0.74, "leaks": False}],
            "protocol": {"feature_alone": True, "buffered_spatial_folds": True,
                         "whole_fault_segments": True},
            "receipt_path": str(tmp_path / "canary.json"),
            "receipt_sha256": canary_receipt_sha,
            "candidate_file_sha256": file_sha,
            "candidate_decoded_sha256": decoded_sha,
            "registry_index_sha256": index_sha,
            "freshness_receipt_sha256": freshness_sha,
        },
        "promotion_grade_holdout": {
            "passed": True,
            "evidence_class": "HOLDOUT-DTI",
            "evaluator": build_site.HOLDOUT_EVALUATOR,
            "evaluator_version": build_site.HOLDOUT_VERSION,
            "pooled_dti": 0.061,
            "withheld_positive_pixels": 1200,
            "ci95": [0.052, 0.069],
            "ci95_reportable": True,
            "ci95_method": "paired physical spatial-cluster percentile bootstrap",
            "bootstrap": {"clusters": 18, "draws": 1000, "confidence": 0.95,
                          "method": "paired physical spatial-cluster percentile"},
            "protocol": {
                "buffered_whole_fault_segments": True,
                "catalogue_features_visible_only": True,
                "visible_faults_masked_pixel_exactly": True,
                "pooled": True,
                "alpha": 0.2,
                "beta": 0.8,
                "triangular_kernel_radius_m": 300,
            },
            "receipt_path": str(tmp_path / "holdout.json"),
            "receipt_sha256": holdout_receipt_sha,
            "candidate_file_sha256": file_sha,
            "candidate_decoded_sha256": decoded_sha,
            "registry_index_sha256": index_sha,
            "freshness_receipt_sha256": freshness_sha,
        },
    }
    emi = {
        "name": "candidate",
        "file": str(tif),
        "zip": str(tif.with_suffix(".zip")),
        "sha256": file_sha,
        "decoded_prediction_sha256": decoded_sha,
        "validator": {
            "passed": True,
            "bytes": tif.stat().st_size,
            "n_positives": 100,
            "checks": {
                "single_band": {"ok": True, "detail": "one band"},
                "float32": {"ok": True, "detail": "float32"},
                "values_in_unit_interval": {"ok": True, "detail": "min=0 max=1"},
            },
        },
        "uniqueness_local": {"cleared": True, "n_checked": 12},
        "holdout_dti": {"pooled": 0.04365, "protocol": "gems58-pooled-hide-v1",
                        "evaluator": "gems58w.metric/v1"},
    }
    xcheck = {"verdict": "AGREE", "pooled": {"shared_gems57_binary": 0.043651086}}
    return {
        "tif": tif,
        "emi": emi,
        "inv": inv,
        "freshness": freshness,
        "qualification": qualification,
        "xcheck": xcheck,
        "inventory_index_sha256": index_sha,
        "inventory_receipt_sha256": inventory_sha,
        "freshness_receipt_sha256": freshness_sha,
    }


def evaluate(evidence, **override):
    item = {**evidence, **override}
    original_root = build_site.ROOT
    build_site.ROOT = Path(item["tif"]).resolve().parent.parent
    try:
        return build_site.evaluate_gates(
            item["emi"], {}, item["inv"], Path(item["tif"]), item.get("xcheck"),
            item["qualification"], item["freshness"],
            inventory_index_sha256=item["inventory_index_sha256"],
            inventory_receipt_sha256=item["inventory_receipt_sha256"],
            freshness_receipt_sha256=item["freshness_receipt_sha256"],
        )
    finally:
        build_site.ROOT = original_root


def by_id(gates):
    return {gate["id"]: gate for gate in gates}


def test_exact_hash_bound_qualification_passes_only_preupload_gates(tmp_path):
    evidence = _valid_evidence(tmp_path)
    gates, eligible = evaluate(evidence)
    gate = by_id(gates)
    assert eligible is True, [g["id"] for g in gates if not g["ok"] and not g["informational"]]
    assert all(gate[key]["ok"] for key in build_site.REQUIRED_GATES)
    assert gate["G6"]["ok"] is False
    assert gate["G6"]["informational"] is True
    assert gate["G2"]["informational"] is True


def test_missing_qualification_fails_closed(tmp_path):
    evidence = _valid_evidence(tmp_path)
    evidence["qualification"] = {}
    gates, eligible = evaluate(evidence)
    gate = by_id(gates)
    assert eligible is False
    assert all(gate[key]["ok"] is False for key in ("G2P", "G3", "G4", "G5"))


def test_literal_uniqueness_thresholds_and_inventory_completeness(tmp_path):
    evidence = _valid_evidence(tmp_path)
    inv = json.loads(json.dumps(evidence["inv"]))
    inv["worst_spearman_full_footprint"] = build_site.RHO_LIMIT
    inv["worst_dot_overlap"] = build_site.OVERLAP_LIMIT
    evidence["inv"] = inv
    evidence["qualification"]["final_dot_gate"]["passed"] = True
    gates, eligible = evaluate(evidence)
    assert by_id(gates)["G3"]["ok"] is True, "exact threshold values do not exceed the stop"
    assert eligible is True

    inv["worst_dot_overlap"] = build_site.OVERLAP_LIMIT + 1e-9
    inv["unique"] = False
    inv["stop_required"] = True
    evidence["inv"] = inv
    evidence["qualification"]["final_dot_gate"]["passed"] = False
    gates, eligible = evaluate(evidence)
    assert by_id(gates)["G3"]["ok"] is False
    assert eligible is False

    inv["unique"] = True
    inv["stop_required"] = False
    inv["worst_dot_overlap"] = 0.55
    inv["complete_accessible_scan"] = False
    evidence["inv"] = inv
    gates, eligible = evaluate(evidence)
    assert by_id(gates)["G3"]["ok"] is False
    assert eligible is False


def test_stale_inventory_never_clears_even_when_final_scan_looks_unique(tmp_path):
    evidence = _valid_evidence(tmp_path)
    evidence["freshness"]["fresh_current_inventory"] = False
    gates, eligible = evaluate(evidence)
    gate = by_id(gates)
    assert gate["G2P"]["ok"] is False
    assert gate["G3"]["ok"] is False
    assert eligible is False


def test_literal_stop_firings_are_not_waived_by_informative_or_chance_fields(tmp_path):
    evidence = _valid_evidence(tmp_path)
    evidence["inv"]["unique"] = False
    evidence["inv"]["stop_required"] = True
    evidence["inv"]["informative_reading"] = {
        "overlap_firings": 81,
        "overlap_firings_informative": 27,
        "overlap_firings_vacuous": 54,
        "worst_chance_corrected_lift": 0.01,
    }
    gates, eligible = evaluate(evidence)
    assert by_id(gates)["G3"]["ok"] is False
    assert eligible is False


def test_tampered_candidate_bytes_fail_all_hash_bound_gates(tmp_path):
    evidence = _valid_evidence(tmp_path)
    evidence["tif"].write_bytes(b"tampered candidate bytes")
    gates, eligible = evaluate(evidence)
    gate = by_id(gates)
    assert gate["G1"]["ok"] is False
    assert gate["G2P"]["ok"] is False
    assert gate["G3"]["ok"] is False
    assert gate["G4"]["ok"] is False
    assert gate["G5"]["ok"] is False
    assert eligible is False


def test_failed_local_check_blocks_but_local_subset_is_informational(tmp_path):
    evidence = _valid_evidence(tmp_path)
    evidence["emi"]["validator"]["checks"]["values_in_unit_interval"]["ok"] = False
    evidence["emi"]["uniqueness_local"]["cleared"] = False
    gates, eligible = evaluate(evidence)
    gate = by_id(gates)
    assert gate["G1"]["ok"] is False
    assert gate["G2"]["ok"] is False
    assert gate["G2"]["informational"] is True
    assert eligible is False


def test_holdout_gate_requires_shared_version_spatial_protocol_and_defensible_ci(tmp_path):
    for mutate in (
        lambda h: h.update(evaluator="gems58w.metric/v1"),
        lambda h: h.update(evaluator_version="old-version"),
        lambda h: h.update(ci95_reportable=False),
        lambda h: h.update(withheld_positive_pixels=0),
        lambda h: h["protocol"].update(visible_faults_masked_pixel_exactly=False),
    ):
        evidence = _valid_evidence(tmp_path)
        mutate(evidence["qualification"]["promotion_grade_holdout"])
        gates, eligible = evaluate(evidence)
        assert by_id(gates)["G5"]["ok"] is False
        assert eligible is False


def test_canary_at_limit_and_unbound_receipts_fail(tmp_path):
    evidence = _valid_evidence(tmp_path)
    evidence["qualification"]["leakage_canary"]["max_single_feature_auc"] = 0.90
    gates, eligible = evaluate(evidence)
    assert by_id(gates)["G4"]["ok"] is False
    assert eligible is False

    evidence = _valid_evidence(tmp_path)
    evidence["qualification"]["final_dot_gate"]["receipt_sha256"] = "0" * 64
    gates, eligible = evaluate(evidence)
    assert by_id(gates)["G3"]["ok"] is False
    assert eligible is False


def test_preemission_checker_requires_all_hard_gates(tmp_path, monkeypatch):
    evidence = _valid_evidence(tmp_path)
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    failures = build_site.preemission_qualification_failures(
        evidence["qualification"], evidence["inv"], evidence["freshness"],
        inventory_index_sha256=evidence["inventory_index_sha256"],
        inventory_receipt_sha256=evidence["inventory_receipt_sha256"],
        freshness_receipt_sha256=evidence["freshness_receipt_sha256"],
    )
    assert failures == []

    evidence["inv"]["unique"] = False
    evidence["inv"]["stop_required"] = True
    evidence["inv"]["informative_reading"]["overlap_firings"] = 1
    failures = build_site.preemission_qualification_failures(
        evidence["qualification"], evidence["inv"], evidence["freshness"],
        inventory_index_sha256=evidence["inventory_index_sha256"],
        inventory_receipt_sha256=evidence["inventory_receipt_sha256"],
        freshness_receipt_sha256=evidence["freshness_receipt_sha256"],
    )
    assert any("literal final-dot" in failure for failure in failures)
    assert any("trigger(s) remain" in failure for failure in failures)


def test_qualification_receipts_must_be_repo_local(tmp_path):
    evidence = _valid_evidence(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-external-receipt.json"
    try:
        digest = _write(outside, b"receipt outside the evidence tree")
        canary = evidence["qualification"]["leakage_canary"]
        canary["receipt_path"] = str(outside)
        canary["receipt_sha256"] = digest
        gates, eligible = evaluate(evidence)
        assert by_id(gates)["G4"]["ok"] is False
        assert eligible is False
    finally:
        outside.unlink(missing_ok=True)


def test_validated_sigma_and_shared_evaluator_holdout_contract():
    sigma = {
        "promotion_grade": True,
        "buffered_whole_component_context_used": True,
        "evaluator": build_site.HOLDOUT_EVALUATOR,
        "evaluator_version": build_site.HOLDOUT_VERSION,
        "evidence_class": "HOLDOUT-STRUCTURE",
        "sigma_table_rows": [
            {"evidence_class": "HOLDOUT-STRUCTURE", "block": block,
             "ridge_type": ridge, "sigma_px": 2.0, "n_matched": 50}
            for block in ("NW", "NE", "SW", "SE")
            for ridge in ("cat-axis", "sgmc-axis")
        ],
    }
    assert len(build_site.validated_sigma_table(sigma)) == 8

    protocol = {"buffered_whole_fault_segments": True,
                "catalogue_features_visible_only": True,
                "visible_faults_masked_pixel_exactly": True,
                "pooled": True, "alpha": 0.2, "beta": 0.8,
                "triangular_kernel_radius_m": 300}
    def reportable(score):
        return {"evidence_class": "HOLDOUT-DTI", "dti": score,
                "withheld_positive_pixels": 100,
                "ci95": [score - 0.005, score + 0.005],
                "ci95_reportable": True,
                "ci95_method": "paired physical spatial-cluster percentile bootstrap",
                "bootstrap": {"clusters": 12, "draws": 1000,
                              "confidence": 0.95,
                              "method": "paired physical spatial-cluster percentile"}}
    e2 = {
        "promotion_grade": True,
        "buffered_whole_component_context_used": True,
        "evaluator": build_site.HOLDOUT_EVALUATOR,
        "evaluator_version": build_site.HOLDOUT_VERSION,
        "promotion_grade_result": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": build_site.HOLDOUT_VERSION,
            "candidate_arm": "ribbon",
            "protocol": protocol,
            "scores": {"ribbon": reportable(0.05)},
            "per_class_gains": {"topographic": {**reportable(0.01), "gain": 0.01}},
        },
    }
    assert build_site.validated_holdout_result(e2)["dti"] == 0.05
    assert build_site.validated_per_class_gains(e2)["topographic"]["gain"] == 0.01


def test_legacy_receipts_do_not_satisfy_promotion_validators():
    legacy_sigma = build_site.load(build_site.RIB / "adaptive_sigma.json")
    legacy_arms = build_site.load(build_site.RIB / "adaptive_arms.json")
    assert build_site.validated_sigma_table(legacy_sigma) == []
    assert build_site.validated_holdout_result(legacy_arms) is None
    assert build_site.validated_per_class_gains(legacy_arms) is None


def test_site_copy_does_not_claim_sample_nans_prove_portal_acceptance(tmp_path):
    evidence = _valid_evidence(tmp_path)
    gates, eligible = evaluate(evidence)
    html = build_site.build_index(
        evidence["emi"], {}, evidence["inv"], evidence["freshness"],
        evidence["qualification"], gates, eligible,
        {"rows": [{"rank": 23, "participant": "extradr19", "score": 0.2778}]},
    )
    assert "extradr19" in html
    assert "NOT OK TO SUBMIT" not in html  # the synthetic exact qualification passes
    assert "matching that sample representation does not prove" in html
    assert "portal acceptance" in html.lower()


def test_current_repository_candidate_is_not_qualified():
    emi = build_site.load(build_site.RIB / "emission.json")
    inv = build_site.load(build_site.RIB / "uniqueness_full_inventory.json")
    freshness = build_site.load(build_site.EV / "registry_freshness_audit.json")
    q = build_site.load(build_site.EV / "ribbon_qualification.json")
    tif = build_site._file_path(emi["file"])
    gates, eligible = build_site.evaluate_gates(
        emi, {}, inv, tif, build_site.load(build_site.RIB / "shared_metric_crosscheck.json"), q, freshness,
        inventory_index_sha256=(build_site.sha256(build_site.ROOT / "registry/registry_merged.json")),
        inventory_receipt_sha256=build_site.sha256(build_site.RIB / "uniqueness_full_inventory.json"),
        freshness_receipt_sha256=build_site.sha256(build_site.EV / "registry_freshness_audit.json"),
    )
    gate = by_id(gates)
    assert eligible is False
    assert gate["G1"]["ok"] is True
    assert gate["G3"]["ok"] is False
    assert gate["G2P"]["ok"] is False
    assert gate["G4"]["ok"] is False
    assert gate["G5"]["ok"] is False
    assert "81" in gate["G3"]["detail"]
