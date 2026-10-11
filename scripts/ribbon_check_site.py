#!/usr/bin/env python3
"""QA current status/download language and the archived ribbon pages."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RIBBON = DOCS / "ribbon"
DOWNLOADS = DOCS / "downloads"
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
            errors.append(f"{name}: missing unmistakable negative submission status")
        if "Download: OK" in body:
            errors.append(f"{name}: legacy permission text remains")
        for link in LINK_RE.findall(body):
            if link.startswith(("http://", "https://", "mailto:", "//")):
                continue
            if not (path.parent / link).resolve().exists():
                errors.append(f"{name}: broken internal link {link}")

    try:
        status = json.loads((ROOT / "evidence/site_status.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status = {}
        errors.append(f"cannot read generated site status: {exc}")
    if status.get("decision") != "NOT_OK_TO_SUBMIT":
        errors.append("generated site status does not deny submission")
    if status.get("final_dot_scan_stop_required") is not True:
        errors.append("generated site status no longer records the literal final-dot stop")
    if status.get("literal_overlap_firings") != 81:
        errors.append("generated site status does not preserve the 81 literal overlap triggers")
    if status.get("portal_acceptance", "").startswith("ACCEPTED"):
        errors.append("site status claims portal acceptance without a receipt")
    if status.get("independent_local_file_audit_passed") is not True:
        errors.append("site status does not report a passing independent local TIFF/ZIP audit")
    audit_path = ROOT / "evidence/ribbon/file_audit.json"
    emission_path = ROOT / "evidence/ribbon/emission.json"
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        emission = json.loads(emission_path.read_text(encoding="utf-8"))
        if audit.get("all_checks_passed") is not True or not all((audit.get("checks") or {}).values()):
            errors.append("independent local file audit is not fully passing")
        if audit.get("sha256") != emission.get("sha256"):
            errors.append("independent local file audit is not bound to the emitted TIFF hash")
        if "does not establish portal acceptance" not in audit.get("scope_note", "").lower():
            errors.append("local file audit does not clearly limit its scope")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read independent local file audit/emission: {exc}")
    if status.get("top_hypothesis_status", "").startswith("VALIDATED"):
        errors.append("site status claims the top hypothesis was validated")
    if status.get("weekly_slot_selected") is not False or status.get("upload_performed") is not False:
        errors.append("site status implies a slot or upload action")

    for name in ("index.html", "executive-summary.html"):
        path = DOCS / "deliverable" / name
        if not path.is_file():
            errors.append(f"missing archived deliverable page: docs/deliverable/{name}")
            continue
        body = path.read_text(encoding="utf-8")
        if "ARCHIVED" not in body or "NOT OK TO SUBMIT" not in body:
            errors.append(f"docs/deliverable/{name}: missing archived red-status notice")
        if "download ok" in body.lower() or "download &amp; submit candidate" in body.lower():
            errors.append(f"docs/deliverable/{name}: legacy affirmative download claim remains")
        for link in LINK_RE.findall(body):
            if link.startswith(("http://", "https://", "mailto:", "//")):
                continue
            if not (path.parent / link).resolve().exists():
                errors.append(f"docs/deliverable/{name}: broken internal link {link}")

    for rel, required in (
        ("index.html", ["NOT OK TO SUBMIT", "REVIEW ONLY", "UNRESOLVED", "extradr19", "H33-2-B2", "Independent on-disk TIFF/ZIP audit"]),
        ("executive-summary.html", ["NOT OK TO SUBMIT", "REVIEW ONLY"]),
        ("submit.html", ["NOT OK TO SUBMIT", "UNRESOLVED"]),
    ):
        path = DOCS / rel
        if not path.is_file():
            errors.append(f"missing generated public page: docs/{rel}")
            continue
        body = path.read_text(encoding="utf-8")
        for text in required:
            if text.lower() not in body.lower():
                errors.append(f"docs/{rel}: missing required status text {text!r}")

    downloads_index = DOWNLOADS / "index.html"
    if not downloads_index.is_file():
        errors.append("missing per-file download index docs/downloads/index.html")
    else:
        body = downloads_index.read_text(encoding="utf-8")
        if "NOT OK TO SUBMIT" not in body:
            errors.append("download index lacks an explicit negative submit label")
        for path in DOWNLOADS.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".tif", ".tiff", ".zip"}:
                relative = path.relative_to(DOWNLOADS).as_posix()
                if relative not in body:
                    errors.append(f"download index does not list {relative}")
        legacy_downloads = DOCS / "deliverable" / "downloads"
        for path in (legacy_downloads.rglob("*") if legacy_downloads.is_dir() else []):
            if path.is_file() and path.suffix.lower() in {".tif", ".tiff", ".zip"}:
                relative = f"legacy/{path.relative_to(legacy_downloads).as_posix()}"
                if relative not in body or "NOT OK TO SUBMIT — REVIEW ONLY" not in body:
                    errors.append(f"download index does not red-label archived file {relative}")

    if DOWNLOADS.exists() and any(p.is_dir() and p.name not in {".staging", "archive"}
                                  for p in DOWNLOADS.iterdir()):
        errors.append("unexpected directory under public downloads")
    archive_readme = DOWNLOADS / "archive" / "README.md"
    if archive_readme.is_file():
        text = archive_readme.read_text(encoding="utf-8").lower()
        if "current validated submission" in text or "validated submission" in text:
            errors.append("download archive README still claims a current validated submission")
    legacy_dir = RIBBON / "downloads"
    if legacy_dir.exists() and any(legacy_dir.iterdir()):
        errors.append("legacy downloadable artifacts remain under docs/ribbon/downloads")
    if any(bad in (DOCS / "index.html").read_text(encoding="utf-8") for bad in (
        "makes the reported portal rejection impossible", "NaN inside footprint = 0",
        "G3i chance-corrected reading (needs owner ratification)", "694 of 695")):
        errors.append("root status contains a known false or stale portal/registry claim")

    archive = ROOT / "evidence" / "ribbon" / "archive-downloads" / "README.md"
    if not archive.is_file():
        errors.append("legacy download archive lacks its research-only notice")

    if errors:
        print("RIBBON SITE QA FAILED")
        for error in errors:
            print(" -", error)
        return 1
    print("RIBBON SITE QA PASSED: current status is red, every public TIFF/ZIP is labeled, "
          "archived pages are red, and no stale portal/leaderboard claims remain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
