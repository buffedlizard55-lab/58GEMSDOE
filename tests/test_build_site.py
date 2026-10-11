"""Integration tests for the public status-site gate wiring and evidence labels."""
from __future__ import annotations

import re
from pathlib import Path

from scripts import build_site
from scripts import qualification_gates


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8"))).lower()


def _current_inputs():
    emi = build_site.load(build_site.RIB / "emission.json")
    sig = build_site.load(build_site.RIB / "adaptive_sigma.json")
    inv = build_site.load(build_site.RIB / "uniqueness_full_inventory.json")
    xcheck = build_site.load(build_site.RIB / "shared_metric_crosscheck.json")
    qualification = build_site.load(build_site.EV / "ribbon_qualification.json")
    freshness = build_site.load(build_site.EV / "registry_freshness_audit.json")
    tif = Path(emi["file"])
    if not tif.is_absolute():
        tif = build_site.ROOT / tif
    return emi, sig, inv, xcheck, qualification, freshness, tif


def test_public_builder_delegates_to_the_emission_qualification_contract():
    assert build_site.current_gates is qualification_gates
    emi, sig, inv, xcheck, qualification, freshness, tif = _current_inputs()
    gates, eligible = build_site.evaluate_gates(
        emi, sig, inv, tif, xcheck, qualification, freshness,
        inventory_index_sha256=build_site.sha256(build_site.ROOT / "registry/registry_merged.json"),
        inventory_receipt_sha256=build_site.sha256(build_site.RIB / "uniqueness_full_inventory.json"),
        freshness_receipt_sha256=build_site.sha256(build_site.EV / "registry_freshness_audit.json"),
    )
    by_id = {gate["id"]: gate for gate in gates}
    assert eligible is False
    assert by_id["G1"]["ok"] is True
    assert all(by_id[key]["ok"] is False for key in ("G2P", "G3", "G4", "G5"))
    assert "83" in by_id["G3"]["detail"]
    assert "literal trigger is never waived" in by_id["G3"]["detail"].lower()


def test_missing_qualification_receipt_fails_closed_even_with_legacy_measurements():
    emi, sig, inv, xcheck, _qualification, freshness, tif = _current_inputs()
    gates, eligible = build_site.evaluate_gates(
        emi, sig, inv, tif, xcheck, {}, freshness,
        inventory_index_sha256=build_site.sha256(build_site.ROOT / "registry/registry_merged.json"),
        inventory_receipt_sha256=build_site.sha256(build_site.RIB / "uniqueness_full_inventory.json"),
        freshness_receipt_sha256=build_site.sha256(build_site.EV / "registry_freshness_audit.json"),
    )
    by_id = {gate["id"]: gate for gate in gates}
    assert by_id["G1"]["ok"] is True
    assert eligible is False
    assert all(by_id[key]["ok"] is False for key in ("G2P", "G3", "G4", "G5"))


def test_informational_gate_cannot_look_like_required_failure_or_pass():
    rendered = build_site.gates_html([
        {"id": "G2", "name": "Local witness", "ok": False, "detail": "diagnostic only",
         "informational": True},
        {"id": "G3", "name": "Final dots", "ok": False, "detail": "literal stop",
         "informational": False},
    ]).lower()
    assert "info — not an eligibility gate" in rendered
    assert "fail — required" in rendered
    assert rendered.count("class=\"gate info\"") == 1


def test_rendered_current_pages_show_no_go_and_do_not_promote_legacy_holdout():
    page_names = ("index.html", "submit.html", "executive-summary.html", "evidence.html")
    pages = {name: _flat(build_site.DOCS / name) for name in page_names}
    for page_name, page in pages.items():
        assert "not ok to submit" in page or "evidence is classified" in page, page_name
        assert "ratified-uniq-v1 governs" not in page
        assert "the error this file cannot produce" not in page
        assert "h33 scored 0.2778" not in page

    # Required canary and holdout gates stay red in the rendered decision pages.
    for page_name in ("index.html", "executive-summary.html"):
        page = pages[page_name]
        assert "g4 · promotion-grade feature-alone leakage canary" in page
        assert "g4 · promotion-grade feature-alone leakage canary fail — required" in page
        assert "g5 · buffered spatial holdout-dti with defensible 95% ci" in page
        assert "g5 · buffered spatial holdout-dti with defensible 95% ci fail — required" in page

    # Legacy measurements remain in their receipts, but are not rendered as current scores.
    legacy_card = build_site.load(build_site.RIB / "run_card_v2.json")
    holdout = legacy_card.get("holdout_dti", {})
    old_scores = []
    for result in holdout.values():
        if not isinstance(result, dict):
            continue
        old_scores.extend(value for key, value in result.items()
                          if key in {"value", "control_R0"}
                          and isinstance(value, (int, float)) and value > 0.01)
        for subkey in ("per_fold", "ci"):
            details = result.get(subkey, {})
            if isinstance(details, dict):
                old_scores.extend(value for value in details.values()
                                  if isinstance(value, (int, float)) and value > 0.01)
    current_output = " ".join(pages.values()) + (build_site.DOCS / "RUN_CARD.json").read_text()
    for score in old_scores:
        assert f"{score:.6f}" not in current_output
    old_auc = build_site.load(build_site.RIB / "adaptive_sigma.json").get("leakage_canary", {})
    worst_auc = max((entry.get("auc_max", 0) for entry in old_auc.values()
                     if isinstance(entry, dict)), default=0)
    assert f"{worst_auc:.4f}" not in current_output

    # Historical uniqueness vocabulary and counts cannot become the current decision.
    card = build_site.load(build_site.DOCS / "RUN_CARD.json")
    assert "ratified" not in card["verdict_reason"].lower()
    assert "83" not in card["verdict_reason"]
    banner = re.search(r'<section class="banner[^>]*>(.*?)</section>',
                       (build_site.DOCS / "index.html").read_text(), re.S)
    assert banner and "ratified" not in banner.group(1).lower() and "83" not in banner.group(1)
    g3 = next(gate for gate in card["site_gates"] if gate["id"] == "G3")
    assert "83" in g3["detail"] and "saved public-inventory snapshot only" in g3["detail"]

    index = pages["index.html"]
    summary = pages["executive-summary.html"]
    assert "public-leaderboard-snapshot" in index and "public-leaderboard-snapshot" in summary
    assert "not an organizer-confirmed artifact score" in summary
    assert "not organizer-confirmed" in index
    assert "no organizer-confirmed score exists for this repository's artifact" in index
    assert "extradr19" in index
    assert "not measured" in index
    assert "blocked_not_exhaustive" in index
    assert "download for review only" in index
    assert "do not submit" in index
    submit = pages["submit.html"]
    assert "unresolved" in submit
    assert "do not infer its cause" in submit
