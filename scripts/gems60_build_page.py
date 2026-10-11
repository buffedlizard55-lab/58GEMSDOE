#!/usr/bin/env python3
"""Render a minimal archival notice for the historical session-5 TIFF.

This is deliberately not a candidate builder or qualification tool. It never
writes to the current session-7 pages, creates a raster, runs an experiment, or
interprets session-5 uniqueness receipts as current clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DL = DOCS / "downloads"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="return 2 if the historical file or its hash receipt is missing/mismatched")
    args = parser.parse_args()

    tifs = sorted(DL.glob("gems60-*.tif"))
    if not tifs:
        raise SystemExit("no historical gems60 TIFF found in docs/downloads")
    tif = tifs[-1]
    actual_sha = sha256(tif)
    verify = load_json(DL / f"{tif.stem}.checks.json")
    expected_sha = str(verify.get("sha256") or "")
    hash_matches = bool(expected_sha and actual_sha == expected_sha)
    passed = verify.get("passed")
    total = verify.get("total")
    local_checks = (f"{passed}/{total} historical local checks passed"
                    if isinstance(passed, int) and isinstance(total, int)
                    else "historical local format receipt unavailable")
    receipt_state = ("matches the historical local receipt" if hash_matches
                     else "does NOT match, or is absent from, the historical local receipt")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    name = html.escape(tif.name)
    digest = html.escape(actual_sha)
    size = tif.stat().st_size
    out = DOCS / "gems60.html"
    out.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Archived session-5 artifact — 58GEMSDOE</title>
<style>
:root{{color-scheme:light;font:16px/1.55 system-ui,sans-serif;color:#18212b;background:#f4f6f8}}
main{{max-width:900px;margin:2rem auto;padding:0 1rem}}.warning{{border:2px solid #a11212;border-left-width:10px;background:#fff0f0;padding:1.2rem;border-radius:8px}}
.badge{{font-weight:800;color:#a11212}}.card{{background:white;border:1px solid #ccd3da;border-radius:8px;padding:1rem;margin:1rem 0}}
code{{overflow-wrap:anywhere}}a{{color:#14569a}}.button{{display:inline-block;background:#a11212;color:white;padding:.7rem 1rem;border-radius:6px;font-weight:700;text-decoration:none}}
</style></head><body><main>
<p><a href="index.html">Current session-7 status</a> · <a href="downloads/index.html">Review-only download index</a> ·
<a href="SUBMISSION_GUIDE.md">Executive submission guide</a></p>
<section class="warning" role="alert">
<p class="badge">ARCHIVED SESSION-5 ARTIFACT — NOT OK TO SUBMIT — DO NOT UPLOAD OR SELECT A SLOT</p>
<h1>Historical TIFF retained for audit only</h1>
<p>This page and file are historical research records, not the current candidate, a uniqueness clearance,
portal acceptance, or evidence of an organizer score. Session-5 chance-corrected readings do not waive
the current prompt's literal uniqueness stop. The current session-7 review TIFF independently measured
1.0000 final-dot overlap within 3 px of a hash-pinned witness and is also stopped; see the
<a href="research/session7_review_20261011.md">current review</a> and
<a href="index.html">current status page</a>.</p>
<p><a class="button" href="downloads/{name}" download>Download historical TIFF for audit only — NOT FOR SUBMISSION · {size:,} bytes</a></p>
</section>
<section class="card"><h2>Historical file identity</h2>
<ul><li>File: <code>{name}</code></li><li>Size: {size:,} bytes</li>
<li>On-disk SHA-256: <code>{digest}</code></li><li>Hash receipt: {html.escape(receipt_state)}</li>
<li>Recorded historical format check: {html.escape(local_checks)} (not organizer validation)</li>
<li>Page rendered: {html.escape(stamp)}</li></ul></section>
<section class="card"><h2>Evidence and limits</h2>
<p>The session-5 run card and uniqueness readings remain available as historical artifacts under
<code>evidence/gems60/</code>. They are not current-session qualification and should not be used to
infer permission to download for submission. No claim is made here about the cause of the reported
portal validation message or about the 0.2778 leaderboard row.</p>
<ul><li><a href="../evidence/gems60/run_card.json">Historical session-5 run card</a></li>
<li><a href="../evidence/gems60/uniqueness_readings.json">Historical session-5 uniqueness readings</a></li>
<li><a href="../evidence/58gemsdoe_unique_ribbon/run_card.json">Current session-7 run card</a></li>
<li><a href="../evidence/58gemsdoe_unique_ribbon/audit.json">Current session-7 artifact audit</a></li></ul>
</section><p>No slot was selected and no upload is authorized by this page.</p>
</main></body></html>""", encoding="utf-8")
    print(f"wrote archival notice {out} ({out.stat().st_size:,} bytes); current session-7 pages were not modified")
    if args.strict and not hash_matches:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
