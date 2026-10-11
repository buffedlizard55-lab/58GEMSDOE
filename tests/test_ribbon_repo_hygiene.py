"""Fail-closed status, archived ribbon pages, and artifact-attribution checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_run_card_is_an_unambiguous_negative():
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    assert card["submission_status"] == "NOT_OK_TO_SUBMIT"
    assert card["human_readable_status"] == "NOT OK TO SUBMIT — DO NOT SUBMIT"
    assert card["verdict"] == "negative"
    assert card["correlation_overlap_vs_registry"]["final_dot_gate"]["passed"] is False
    assert card["correlation_overlap_vs_registry"]["final_dot_gate"]["worst_dot_overlap"] > 0.70
    assert card["correlation_overlap_vs_registry"]["latest_pinned_snapshot_scan"]["complete_accessible_scan"] is False
    assert card["submission_note_chars"] <= 140


def test_current_diagnostic_tif_matches_run_card_sha256():
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    p = ROOT / "docs" / "downloads" / f"{card['submission_name']}.tif"
    assert p.exists(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == card["raster_sha256"]


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
        "scripts/ribbon_run_leakage_canary.py", "scripts/run_ribbon_experiments.py",
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
    assert "Maximize" in readme and "DO NOT SUBMIT" in readme
    assert "does **not** link the score to the similarly quoted" in leaderboard
    assert "NO ORGANISER SCORE EXISTS" in leaderboard
    assert "PUBLIC-LEADERBOARD-SNAPSHOT ONLY" in seen
