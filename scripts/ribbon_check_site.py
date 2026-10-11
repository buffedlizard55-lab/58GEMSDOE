#!/usr/bin/env python3
"""QA for the archived ribbon pages and current fail-closed status.

This checker intentionally does not use the legacy ``gems58w`` writer or
re-derive its historical claims. It verifies status copy, links, and the current
run-card stop conditions only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RIBBON = DOCS / "ribbon"
PAGES = ["index.html", "executive-summary.html", "hypotheses.html", "research.html",
         "sources.html", "irregularities.html"]
LINK_RE = re.compile(r'(?:href|src)="([^"#]+)"')


def main() -> int:
    errors: list[str] = []
    for name in PAGES:
        path = RIBBON / name
        if not path.is_file():
            errors.append(f"missing archived page: {name}")
            continue
        body = path.read_text(encoding="utf-8")
        if "NOT OK TO SUBMIT" not in body and "DO NOT SUBMIT" not in body:
            errors.append(f"{name}: missing unmistakable negative status")
        if "Download: OK" in body:
            errors.append(f"{name}: legacy permission text remains")
        for link in LINK_RE.findall(body):
            if link.startswith(("http://", "https://", "mailto:", "//")):
                continue
            if not (path.parent / link).resolve().exists():
                errors.append(f"{name}: broken internal link {link}")

    card_path = ROOT / "evidence" / "run_card.json"
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        card = {}
        errors.append(f"cannot read current run card: {exc}")
    if card.get("submission_status") != "NOT_OK_TO_SUBMIT":
        errors.append("current run card does not deny submission")
    if card.get("verdict") != "negative":
        errors.append("current run card verdict is not negative")
    scan = card.get("correlation_overlap_vs_registry", {})
    gate = scan.get("final_dot_gate", {})
    if gate.get("passed") is not False or float(gate.get("worst_dot_overlap", 0.0)) <= 0.70:
        errors.append("current run card does not preserve the literal final-dot overlap stop")
    if scan.get("latest_pinned_snapshot_scan", {}).get("complete_accessible_scan") is not False:
        errors.append("current run card no longer records the incomplete pinned scan")

    root_index = DOCS / "index.html"
    if not root_index.is_file():
        errors.append("missing current root status page docs/index.html")
    else:
        body = root_index.read_text(encoding="utf-8")
        # The banner must match the current run card, whichever way it points.
        try:
            site_card = json.loads((DOCS / "RUN_CARD.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            site_card = {}
            errors.append(f"cannot read docs/RUN_CARD.json: {exc}")
        verdict = site_card.get("site_verdict")
        if verdict == "OK_TO_DOWNLOAD_AND_SUBMIT":
            if "OK TO DOWNLOAD AND SUBMIT" not in body:
                errors.append("run card says OK but the root page lacks the green banner")
        else:
            if "NOT CLEARED" not in body and "DO NOT SUBMIT" not in body \
                    and "NOT OK TO SUBMIT" not in body:
                errors.append("root status page has no negative submission status")
        if "LEADERBOARD.md" not in body:
            errors.append("root status page does not link the score-attribution record")

    legacy_dir = RIBBON / "downloads"
    if legacy_dir.exists() and any(legacy_dir.iterdir()):
        errors.append("legacy downloadable artifacts remain under docs/ribbon/downloads")

    archive = ROOT / "evidence" / "ribbon" / "archive-downloads"
    if not (archive / "README.md").is_file():
        errors.append("legacy download archive lacks its research-only notice")

    if errors:
        print("RIBBON SITE QA FAILED")
        for error in errors:
            print(" -", error)
        return 1
    print(f"RIBBON SITE QA PASSED: {len(PAGES)} archived pages are red, links resolve, "
          "legacy downloads are archived, and current run-card stop conditions remain intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
