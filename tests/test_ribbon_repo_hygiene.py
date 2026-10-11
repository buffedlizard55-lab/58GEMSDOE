"""Fail-closed status, archived ribbon pages, and artifact-attribution checks."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_run_card_is_an_unambiguous_negative():
    status = json.loads((ROOT / "evidence" / "site_status.json").read_text())
    assert status["decision"] == "NOT_OK_TO_SUBMIT"
    assert status["portal_acceptance"].startswith("UNRESOLVED")
    assert status["final_dot_scan_verdict"] == "negative"
    assert status["final_dot_scan_stop_required"] is True
    assert status["literal_overlap_firings"] == 81
    assert status["top_hypothesis_status"].startswith("NOT VALIDATED")
    assert status["weekly_slot_selected"] is False
    assert status["upload_performed"] is False


def test_legacy_run_card_top_labels_do_not_promote_diagnostic_metrics():
    for name in ("run_card_v2.json", "run_card_final.json"):
        card = json.loads((ROOT / "evidence" / "ribbon" / name).read_text())
        assert card["holdout_dti_label"] == "LEGACY-DIAGNOSTIC-ONLY"
        assert isinstance(card["holdout_dti"], (int, float))
        assert card["holdout_dti_evaluator"].startswith("gems58w.metric/v1")
        assert card["holdout_dti_withheld_positives"] == 60869


def test_current_diagnostic_tif_matches_site_status_sha256():
    status = json.loads((ROOT / "evidence" / "site_status.json").read_text())
    p = ROOT / status["candidate_file"]
    assert p.exists(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == status["candidate_file_sha256"]


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
        "scripts/ribbon_run_leakage_canary.py", "scripts/ribbon_emit_adaptive.py",
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
