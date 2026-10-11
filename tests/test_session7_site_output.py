"""The public session-7 pages must expose the current negative gates, not stale scores."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from scripts import build_session7_pages as site

ROOT = Path(__file__).resolve().parents[1]


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).lower()


def _pages() -> dict[str, str]:
    return {
        name: (site.DOCS / name).read_text(encoding="utf-8")
        for name in ("index.html", "executive-summary.html", "submit.html", "evidence.html")
    }


def test_current_pages_match_hash_bound_negative_status():
    card, audit, tif = site.audit_data()
    assert card["verdict"] == "negative"
    assert card["stop_required"] is True
    assert tif.is_file()
    assert audit["artifact_sha256"] == card["raster_sha256"]
    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_session7_pages.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    for name, source in _pages().items():
        flat = _flat(source)
        assert "not ok to submit" in flat or "unreviewed artifact" in flat, name
        assert "do not submit" in flat, name
        assert card["raster_sha256"] in source or name == "evidence.html", name


def test_g4_and_g5_are_explicit_failures_in_current_site_output():
    card, audit, _tif = site.audit_data()
    rows = {row["id"]: row for row in site.gate_rows(card, audit)}
    assert rows["G4"]["ok"] is False
    assert rows["G5"]["ok"] is False
    assert rows["G4"]["name"].startswith("G4 —")
    assert rows["G5"]["name"].startswith("G5 —")
    assert rows["G4"]["status"] == "NOT RUN"
    assert rows["G5"]["status"] == "NOT MEASURED"

    for name in ("index.html", "executive-summary.html", "submit.html"):
        flat = _flat((site.DOCS / name).read_text(encoding="utf-8"))
        assert "g4 — promotion-grade feature-alone leakage canary" in flat, name
        assert "g5 — buffered spatial holdout-dti with defensible 95% ci" in flat, name
        assert "not run" in flat and "not measured" in flat, name
        assert "fail" in flat, name


def test_current_decision_does_not_present_legacy_values_as_current():
    pages = _pages()
    card = json.loads((site.DOCS / "RUN_CARD.json").read_text(encoding="utf-8"))
    banner_match = re.search(r'<section class="s7-alert"[^>]*>.*?</section>',
                             pages["index.html"], re.S)
    assert banner_match is not None
    banner = _flat(banner_match.group(0))
    assert "not ok to submit" in banner and "do not submit" in banner
    assert "ratified" not in banner and "83" not in banner
    assert "ratified" not in card["verdict_reason"].lower()
    assert "83" not in card["verdict_reason"]

    legacy_card = json.loads((ROOT / "evidence/ribbon/run_card_v2.json").read_text())
    old_scores: list[float] = []
    for result in (legacy_card.get("holdout_dti", {}) or {}).values():
        if not isinstance(result, dict):
            continue
        old_scores.extend(value for key, value in result.items()
                          if key in {"value", "control_R0"}
                          and isinstance(value, (int, float)) and value > 0.01)
        for key in ("per_fold", "ci"):
            detail = result.get(key, {})
            if isinstance(detail, dict):
                old_scores.extend(value for value in detail.values()
                                  if isinstance(value, (int, float)) and value > 0.01)
    current_output = " ".join(_flat(page) for page in pages.values()) + json.dumps(card)
    for score in old_scores:
        assert f"{score:.6f}" not in current_output

    sigma = json.loads((ROOT / "evidence/ribbon/adaptive_sigma.json").read_text())
    canary = sigma.get("leakage_canary", {}) or {}
    worst_auc = max((item.get("auc_max", 0) for item in canary.values()
                     if isinstance(item, dict)), default=0)
    assert f"{worst_auc:.4f}" not in current_output


def test_leaderboard_rows_are_snapshot_not_artifact_score_evidence():
    index = _flat((site.DOCS / "index.html").read_text(encoding="utf-8"))
    summary = _flat((site.DOCS / "executive-summary.html").read_text(encoding="utf-8"))
    for page in (index, summary):
        assert "public-leaderboard-snapshot" in page
        assert "not an organizer-confirmed artifact score" in page
        assert "extradr19" in page
