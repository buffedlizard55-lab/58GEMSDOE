"""Fail-closed current status, historical pages, and artifact-attribution checks."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_CARD = ROOT / "evidence" / "58gemsdoe_unique_ribbon" / "run_card.json"
CURRENT_AUDIT = ROOT / "evidence" / "58gemsdoe_unique_ribbon" / "audit.json"


def test_generated_status_is_an_unambiguous_negative():
    """The session-7 site must reflect the literal overlap stop, not the old ratification."""
    card = json.loads((ROOT / "docs" / "RUN_CARD.json").read_text())
    source_card = json.loads(CURRENT_CARD.read_text())
    audit = json.loads(CURRENT_AUDIT.read_text())
    assert card["site_verdict"] == "NOT_OK_TO_SUBMIT"
    assert card["verdict"] == "negative"
    assert card["slots_used"] == 0
    assert card["experiments_this_review"] == 0
    assert card["raster_sha256"] == source_card["raster_sha256"]
    gates = {g["id"]: g["ok"] for g in card["site_gates"]}
    assert gates["FORMAT"] is True  # local format only
    assert gates["PREPLACEMENT"] is False
    assert gates["FINAL_DOTS"] is False
    assert gates["INVENTORY"] is False
    assert gates["HOLDOUT"] is False
    assert gates["LEAKAGE"] is False
    assert gates["PORTAL"] is False

    final = audit["correlation_overlap_vs_registry"]["final_dots"]["witness_measurement"]
    assert final["direct_current_file_measurement"] is True
    assert final["observed_candidate_dot_overlap_within_3_px"] == 1.0
    assert final["literal_overlap_threshold"] == 0.70
    assert audit["verdict"] == "negative" and audit["stop_required"] is True

    index_html = (ROOT / "docs" / "index.html").read_text()
    assert "NOT OK TO SUBMIT — DO NOT SUBMIT" in index_html
    assert source_card["artifact_file"].removeprefix("docs/") in index_html
    assert "1.0000" in index_html
    assert "RATIFIED-UNIQ-v1" not in index_html


def test_current_candidate_tif_matches_the_session7_run_card_sha256():
    card = json.loads(CURRENT_CARD.read_text())
    p = ROOT / card["artifact_file"]
    assert p.exists(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == card["raster_sha256"]
    site_card = json.loads((ROOT / "docs" / "RUN_CARD.json").read_text())
    assert site_card["artifact_file"] == card["artifact_file"]


def test_session7_audit_is_bound_to_current_tiff_and_witness():
    card = json.loads(CURRENT_CARD.read_text())
    audit = json.loads(CURRENT_AUDIT.read_text())
    assert audit["artifact"] == card["artifact_file"]
    assert audit["artifact_sha256"] == card["raster_sha256"]
    assert audit["decoded_prediction_sha256"] == card["decoded_prediction_sha256"]
    assert audit["format_pass"] is True
    assert audit["format_checks_passed"] == audit["format_checks_total"] == 19
    assert audit["correlation_overlap_vs_registry"]["final_dots"]["witness_measurement"]["sha256_verified"] is True
    assert audit["correlation_overlap_vs_registry"]["preplacement_surface"]["status"] == "NOT MEASURED"
    assert audit["holdout_dti"]["status"] == "NOT MEASURED"


def test_historical_file_audit_is_not_mistaken_for_current_candidate():
    audit = json.loads((ROOT / "evidence" / "ribbon" / "file_audit.json").read_text())
    emi = json.loads((ROOT / "evidence" / "ribbon" / "emission.json").read_text())
    assert audit["all_checks_passed"] is True
    assert audit["file"] == emi["file"]
    assert audit["sha256"] == emi["sha256"]
    assert audit["positive_pixels"] == emi["validator"]["n_positives"]
    assert "does not establish portal acceptance" in audit["scope_note"].lower()
    assert audit["sha256"] != json.loads(CURRENT_CARD.read_text())["raster_sha256"]


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
    assert "literal 3 px overlap 1.0000 &gt; 0.70" in index


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
        "scripts/ribbon_run_leakage_canary.py", "scripts/run_ribbon_experiments.py",
    ):
        proc = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                              capture_output=True, text=True, timeout=30)
        assert proc.returncode != 0, script
        combined = proc.stdout + proc.stderr
        assert "DEPRECATED/NO-GO" in combined, (script, combined)


def test_historical_root_site_builder_refuses_to_replace_session7_pages():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/build_site.py")], cwd=ROOT,
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "session-7" in combined.lower() and "refus" in combined.lower(), combined


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
    start = "<!-- BEGIN FULL PROMPT: PROMPT.md -->"
    end = "<!-- END FULL PROMPT: PROMPT.md -->"
    embedded = readme.split(start, 1)[1].split(end, 1)[0].strip()
    assert embedded == prompt.strip(), "README must include the complete current prompt verbatim"
    assert "PARALLEL-RUN PROTOCOL" in prompt
    assert "literal rule for this task" in prompt
    assert "0.3195" in prompt and "0.4133" in prompt and "0.2778" in prompt
    assert "Maximize P(Win)" in readme and "DO NOT SUBMIT" in readme
    assert "extradr19" in leaderboard and "UNSCORED" in leaderboard
    assert "no verified evidence shows that H33 scored 0.2778" in leaderboard
    assert "NO ORGANIZER SCORE" in seen
    assert "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9" in seen


def test_session7_builder_reports_pages_in_sync():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/build_session7_pages.py"), "--check"],
                          cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_session7_pages_are_current_and_submit_guide_does_not_overclaim():
    for name in ("index.html", "executive-summary.html", "submit.html", "evidence.html"):
        text = (ROOT / "docs" / name).read_text()
        assert "NOT OK TO SUBMIT — DO NOT SUBMIT" in text
        assert "58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif" in text
        assert "RATIFIED-UNIQ-v1" not in text
    guide = (ROOT / "docs" / "SUBMISSION_GUIDE.md").read_text()
    assert "cause is **unknown**" in guide
    assert "1.0000" in guide and ">70%" in guide
    assert "HOLDOUT-DTI:** **NOT MEASURED**" in guide or "HOLDOUT-DTI | **NOT MEASURED**" in guide
