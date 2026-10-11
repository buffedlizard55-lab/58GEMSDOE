#!/usr/bin/env python3
"""Render a per-file download/eligibility index for every public TIFF and ZIP.

One downloadable artifact per row, each with its own SHA-256 and its own submit
verdict, so no file can inherit clearance from another. The current review-only
artifact is identified from ``evidence/58gemsdoe_unique_ribbon/run_card.json`` and
its direct overlap receipt; every other public raster is review-only regardless of
any local format pass.

    python3 scripts/build_downloads_index.py
"""
from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOWNLOADS = DOCS / "downloads"
LEGACY_DOWNLOADS = DOCS / "deliverable" / "downloads"
RASTER_SUFFIXES = {".tif", ".tiff", ".zip"}
REVIEW_ONLY = "NOT OK TO SUBMIT — REVIEW ONLY — DO NOT SUBMIT"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def collect() -> list[dict]:
    """Every public raster, with the label its own receipts allow."""
    emission = load(ROOT / "evidence" / "ribbon" / "emission.json")
    run_card = load(DOCS / "RUN_CARD.json")
    review_card = load(ROOT / "evidence" / "58gemsdoe_unique_ribbon" / "run_card.json")
    current_tif = (ROOT / str(emission["file"])).resolve() if emission.get("file") else None
    current_zip = (ROOT / str(emission["zip"])).resolve() if emission.get("zip") else None
    review_file = review_card.get("artifact_file") or review_card.get("file")
    if review_file:
        review_tif = (ROOT / str(review_file)).resolve()
        if not review_tif.is_file():
            review_tif = (DOWNLOADS / Path(str(review_file)).name).resolve()
    else:
        review_tif = None
    review_zip = review_tif.with_suffix(".zip") if review_tif else None
    overlap_record = (review_card.get("correlation_overlap_vs_registry", {})
                      .get("final_dots", {}))
    observed_overlap = overlap_record.get("candidate_specific_overlap_within_3px")
    overlap_limit = overlap_record.get("threshold", 0.70)
    literal_failure = (observed_overlap is not None and observed_overlap > overlap_limit)
    site_verdict = run_card.get("site_verdict", "NOT_OK_TO_SUBMIT")
    current_hashes = {current_tif, current_zip} - {None}
    review_hashes = {review_tif, review_zip} - {None}

    rows: list[dict] = []
    for base, prefix, archived in ((DOWNLOADS, "", False), (LEGACY_DOWNLOADS, "legacy/", True)):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*"), key=lambda p: p.relative_to(base).as_posix().lower()):
            if not path.is_file() or path.suffix.lower() not in RASTER_SUFFIXES:
                continue
            relative = path.relative_to(base).as_posix()
            is_current = path.resolve() in current_hashes
            is_latest_review = path.resolve() in review_hashes
            is_archived = archived or "archive" in path.relative_to(base).parts
            if is_latest_review:
                if literal_failure:
                    label = (REVIEW_ONLY + f" (literal 3 px overlap {observed_overlap:.4f} "
                             f"> {overlap_limit:.2f}; DO NOT SUBMIT)")
                else:
                    label = REVIEW_ONLY + " (latest diagnostic; required gates not cleared)"
                kind = "Latest generated review artifact"
            elif is_current and site_verdict == "OK_TO_DOWNLOAD_AND_SUBMIT":
                label = "Current candidate — local gates pass; no organizer receipt exists"
                kind = "Current candidate"
            elif is_current:
                label = REVIEW_ONLY + " (historical candidate; site verdict " + esc(site_verdict) + ")"
                kind = "Historical candidate"
            else:
                label = REVIEW_ONLY
                kind = "Archived historical artifact" if is_archived else "Historical diagnostic"
            rows.append({
                "kind": kind,
                "href": ("../deliverable/downloads/" + relative) if archived else relative,
                "name": f"{prefix}{relative}",
                "label": label,
                "sha256": sha256(path) if path.suffix.lower() in {".tif", ".tiff"} else "",
            })
    return rows


def render(rows: list[dict]) -> str:
    body = []
    for row in rows:
        digest = f"<code>{esc(row['sha256'])}</code>" if row["sha256"] else "—"
        body.append(
            "<tr>"
            f"<td>{esc(row['kind'])}</td>"
            f'<td><a href="{esc(row["href"])}" download>{esc(row["name"])}</a></td>'
            f"<td><b>{esc(row['label'])}</b></td>"
            f"<td>{digest}</td>"
            "</tr>"
        )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Downloads — individual eligibility labels</title>
<link rel="stylesheet" href="../assets/site.css"></head><body><div class="wrap">
<header><h1>Downloads — one verdict per file</h1>
<div class="banner" role="alert"><strong>NO FILE HERE IS AN APPROVED COMPETITION SUBMISSION.</strong>
<p>A download link is not permission to use a weekly slot. No organizer submission receipt exists
for any raster in this repository, so no file can be labeled accepted or scored. Historical files
are never cleared by a current candidate's local gates.</p></div>
<p><a href="../index.html">Current status and gates</a> ·
<a href="../SUBMISSION_GUIDE.md">Submission guide</a> ·
<a href="../IRREGULARITIES.md">Blockers and corrections</a></p></header>
<section><h2>Every public TIFF and ZIP</h2>
<table><thead><tr><th>artifact class</th><th>file</th><th>submit eligibility</th>
<th>TIFF SHA-256</th></tr></thead>
<tbody>
{chr(10).join(body)}
</tbody></table>
<p class="small">Generated {esc(generated)} by <code>scripts/build_downloads_index.py</code> from
<code>evidence/58gemsdoe_unique_ribbon/run_card.json</code>, <code>docs/RUN_CARD.json</code> and the bytes on disk.
Local file audits verify grid, range, mask, hashes and ZIP round-trip only; they are not portal
acceptance, uniqueness clearance, or eligibility.</p>
</section>
</div></body></html>
"""


def main() -> int:
    rows = collect()
    if not rows:
        print("no public TIFF/ZIP found; nothing to index")
        return 1
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    (DOWNLOADS / "index.html").write_text(render(rows), encoding="utf-8")
    cleared = [row["name"] for row in rows if not row["label"].startswith(REVIEW_ONLY)]
    print(f"wrote docs/downloads/index.html: {len(rows)} files labeled, "
          f"{len(cleared)} not review-only {cleared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
