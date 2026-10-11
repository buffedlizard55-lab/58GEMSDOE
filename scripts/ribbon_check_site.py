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

    card_path = ROOT / "evidence" / "58gemsdoe_unique_ribbon" / "run_card.json"
    audit_path = ROOT / "evidence" / "58gemsdoe_unique_ribbon" / "audit.json"
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        card, audit = {}, {}
        errors.append(f"cannot read session-7 run card/audit: {exc}")
    if card.get("submission_identifier_authorized_for_portal") is not False:
        errors.append("current run card must not authorize the proposed portal identifier")
    if card.get("verdict") != "negative" or card.get("stop_required") is not True:
        errors.append("session-7 run card does not preserve the negative stop")
    if card.get("slots_used") != 0 or card.get("experiments_this_review") != 0:
        errors.append("session-7 run card reports an experiment or slot")
    final = (((audit.get("correlation_overlap_vs_registry") or {}).get("final_dots") or {})
             .get("witness_measurement", {}) or {})
    if (final.get("direct_current_file_measurement") is not True
            or float(final.get("observed_candidate_dot_overlap_within_3_px", 0.0)) <= 0.70):
        errors.append("session-7 audit does not preserve the direct literal final-dot overlap stop")
    if audit.get("format_pass") is not True or audit.get("format_checks_passed") != 19:
        errors.append("session-7 local format audit is missing or has changed")

    root_index = DOCS / "index.html"
    if not root_index.is_file():
        errors.append("missing current root status page docs/index.html")
    else:
        body = root_index.read_text(encoding="utf-8")
        try:
            site_card = json.loads((DOCS / "RUN_CARD.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            site_card = {}
            errors.append(f"cannot read docs/RUN_CARD.json: {exc}")
        if site_card.get("site_verdict") != "NOT_OK_TO_SUBMIT":
            errors.append("current site card does not say NOT_OK_TO_SUBMIT")
        for required in ("NOT OK TO SUBMIT — DO NOT SUBMIT", "1.0000",
                         "58GEMSDOE-ribbon-sparse-review-only-20261011T182511Z.tif",
                         "LEADERBOARD.md"):
            if required not in body:
                errors.append(f"root status page lacks required session-7 evidence: {required}")

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
