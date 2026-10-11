"""Fail-closed status, archived ribbon pages, and artifact-attribution checks."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generated_status_is_an_unambiguous_negative():
    """The rendered status must stay red while the literal uniqueness stop stands."""
    card = json.loads((ROOT / "docs" / "RUN_CARD.json").read_text())
    assert card["site_verdict"] == "NOT_OK_TO_SUBMIT"
    assert card["verdict"] == "negative"
    assert card["slots_used"] == 0
    gates = {g["id"]: g["ok"] for g in card["site_gates"]}
    assert gates["G3"] is False, "the literal uniqueness gate must stay closed"
    assert "G3L" not in gates, "the retired pre-ratification gate is not part of current status"
    assert gates["G4"] is False, "the required feature-alone canary is missing"
    assert gates["G5"] is False, "no promotion-grade holdout receipt exists"
    assert gates["G6"] is False, "no organizer receipt may be claimed from this sandbox"

    inv = json.loads((ROOT / "evidence" / "ribbon" / "uniqueness_full_inventory.json").read_text())
    reading = inv["informative_reading"]
    assert inv["unique"] is False and inv["stop_required"] is True
    assert reading["overlap_firings"] > 0
    # The published copy must quote the same trigger count as the receipt it cites.
    index_html = (ROOT / "docs" / "index.html").read_text()
    assert str(reading["overlap_firings"]) in index_html


def test_legacy_run_card_top_labels_do_not_promote_diagnostic_metrics():
    """The archived sigma-adaptive cards keep their measurements but not a promotion label."""
    for name in ("run_card_v2.json", "run_card_final.json"):
        card = json.loads((ROOT / "evidence" / "ribbon" / "archive-s3" / name).read_text())
        assert card["holdout_dti_label"] == "LEGACY-DIAGNOSTIC-ONLY"
        assert isinstance(card["holdout_dti"], (int, float))
        assert card["holdout_dti_evaluator"].startswith("gems58w.metric/v1")
        assert card["holdout_dti_withheld_positives"] == 60869
        assert "not a promotion-grade" in card["holdout_dti_label_note"]


def test_current_candidate_tif_matches_the_run_card_sha256():
    card = json.loads((ROOT / "docs" / "RUN_CARD.json").read_text())
    p = ROOT / "docs" / "downloads" / f"{card['submission_name']}.tif"
    assert p.exists(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == card["raster_sha256"]


def test_local_file_audit_is_bound_to_the_current_candidate():
    audit = json.loads((ROOT / "evidence" / "ribbon" / "file_audit.json").read_text())
    emi = json.loads((ROOT / "evidence" / "ribbon" / "emission.json").read_text())
    assert audit["all_checks_passed"] is True
    assert audit["file"] == emi["file"]
    assert audit["sha256"] == emi["sha256"]
    assert audit["positive_pixels"] == emi["validator"]["n_positives"]
    assert "does not establish portal acceptance" in audit["scope_note"].lower()


def test_every_public_raster_carries_its_own_submit_verdict():
    index = (ROOT / "docs" / "downloads" / "index.html").read_text()
    files = [p for p in (ROOT / "docs" / "downloads").rglob("*")
             if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
    assert files, "expected public rasters to index"
    for path in files:
        assert path.relative_to(ROOT / "docs" / "downloads").as_posix() in index, path
    legacy = [p for p in (ROOT / "docs" / "deliverable" / "downloads").rglob("*")
              if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
    for path in legacy:
        assert f"legacy/{path.relative_to(ROOT / 'docs' / 'deliverable' / 'downloads').as_posix()}" in index
    assert "NOT OK TO SUBMIT — REVIEW ONLY" in index


def test_archived_deliverable_pages_cannot_grant_download_permission():
    for name in ("index.html", "executive-summary.html"):
        text = (ROOT / "docs" / "deliverable" / name).read_text()
        assert "ARCHIVED" in text and "NOT OK TO SUBMIT" in text, name
        assert "download ok" not in text.lower(), name


def test_legacy_ribbon_pages_are_red_and_do_not_say_download_ok():
    pages = ["index.html", "executive-summary.html", "hypotheses.html", "research.html",
             "sources.html", "irregularities.html"]
    for page in pages:
        text = (ROOT / "docs" / "ribbon" / page).read_text()
        assert "NOT OK TO SUBMIT" in text or "DO NOT SUBMIT" in text, page
        assert "Download: OK" not in text, page
        assert "NOT CLEARED" in text or "NOT OK TO SUBMIT" in text, page


def test_legacy_submission_and_site_builders_fail_closed():
    for script in (
        "scripts/ribbon_build_submission.py", "scripts/ribbon_build_site.py",
        "scripts/ribbon_refresh_feed.py", "scripts/ribbon_verify_theorems.py",
        "scripts/ribbon_run_equal_budget.py", "scripts/ribbon_run_final_sweep.py",
        "scripts/ribbon_run_geometry_sweep.py", "scripts/ribbon_run_holdout_eval.py",
        "scripts/ribbon_run_holdout_sigma.py", "scripts/ribbon_run_instrument_control.py",
        "scripts/ribbon_run_leakage_canary.py",
        "scripts/run_ribbon_experiments.py",
    ):
        proc = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                              capture_output=True, text=True, timeout=30)
        assert proc.returncode != 0, script
        combined = proc.stdout + proc.stderr
        assert "DEPRECATED/NO-GO" in combined, (script, combined)


def test_archived_feed_cannot_grant_download_permission():
    feed = json.loads((ROOT / "docs" / "ribbon" / "data" / "feed.json").read_text())
    assert feed["status"] == "NOT OK TO SUBMIT — DO NOT SUBMIT"
    assert feed["legacy_downloads_offered"] is False
    assert feed["holdout"]["promotion_grade_result"] is None
    assert not (ROOT / ".github" / "workflows" / "ribbon-feed.yml").exists()


def test_score_attribution_and_standing_prompt_are_current():
    prompt = (ROOT / "PROMPT.md").read_text()
    readme = (ROOT / "README.md").read_text()
    leaderboard = (ROOT / "docs" / "LEADERBOARD.md").read_text()
    seen = (ROOT / "registry" / "submissions_seen.csv").read_text()
    assert "PARALLEL-RUN PROTOCOL" in prompt
    assert "0.3195" in prompt and "0.4133" in prompt and "0.2778" in prompt
    assert "Maximize P(Win)" in readme and "DO NOT SUBMIT" in readme
    assert "extradr19" in leaderboard and "UNSCORED" in leaderboard
    assert "no verified evidence shows that H33 scored 0.2778" in leaderboard
    assert "NO ORGANIZER SCORE" in seen
    assert "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9" in seen
