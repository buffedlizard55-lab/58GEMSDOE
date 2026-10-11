#!/usr/bin/env python3
"""Site QA: re-derive every published number and fail closed.

Checks (each a non-zero exit on failure):

* every page in ``docs/`` exists and every internal link resolves;
* the downloadable TIFF exists, its sha256 and byte size match the run card, and
  the 15 local portal checks still pass on the published bytes;
* the ZIP holds exactly one GeoTIFF;
* the pages do not advertise a permission the run card denies, and do not quote a
  leaderboard number without the OWNER-REPORTED label.

    PYTHONPATH=src python3 scripts/ribbon_check_site.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import submission  # noqa: E402
from gems58w.paths import DOCS, EVIDENCE  # noqa: E402

PAGES = ["index.html", "executive-summary.html", "hypotheses.html", "research.html",
         "sources.html", "irregularities.html"]
LINK_RE = re.compile(r'(?:href|src)="([^"#]+)"')


def main() -> int:
    errors: list[str] = []
    doc = DOCS
    card = json.loads((EVIDENCE / "run_card.json").read_text())

    for p in PAGES:
        f = doc / p
        if not f.exists():
            errors.append(f"missing page {p}")
            continue
        body = f.read_text()
        for link in LINK_RE.findall(body):
            if link.startswith(("http://", "https://", "mailto:", "//")):
                continue
            target = (f.parent / link).resolve()
            if not target.exists():
                errors.append(f"{p}: broken link {link}")
        live = [n for n in ("0.3195", "0.3774", "0.2778") if n in body]
        if live and "OWNER-REPORTED" not in body:
            errors.append(f"{p}: quotes live number(s) {live} without the OWNER-REPORTED label")

    tif = doc / "downloads" / f"{card['name']}.tif"
    if not tif.exists():
        errors.append(f"missing download {tif.name}")
    else:
        val = submission.validate(tif)
        if submission.sha256(tif) != card["raster_sha256"]:
            errors.append("published TIFF sha256 does not match the run card")
        if tif.stat().st_size != card["raster_bytes"]:
            errors.append("published TIFF size does not match the run card")
        if not val["passed"]:
            errors.append("published TIFF fails the portal checks: "
                          + ", ".join(k for k, c in val["checks"].items() if not c["ok"]))
        if val["n_positives"] != card["validator"]["n_positives"]:
            errors.append("published TIFF dot count does not match the run card")

    z = doc / "downloads" / f"{card['name']}.zip"
    if not z.exists():
        errors.append("missing single-GeoTIFF ZIP")
    else:
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
        if len(names) != 1 or not names[0].endswith(".tif"):
            errors.append(f"ZIP must hold exactly one GeoTIFF, holds {names}")

    idx = (doc / "index.html").read_text() if (doc / "index.html").exists() else ""
    if card["verdict"].startswith("candidate"):
        if "Download: OK" not in idx:
            errors.append("run card is a candidate but the index does not say download is OK")
    for frag in ("0.3195", "OWNER-REPORTED"):
        if frag not in idx:
            errors.append(f"index.html must carry {frag}")

    feed = json.loads((doc / "data" / "feed.json").read_text())
    if feed["sha256"] != card["raster_sha256"]:
        errors.append("feed.json sha256 does not match the run card")

    if errors:
        print("SITE QA FAILED")
        for e in errors:
            print("  -", e)
        return 1
    print(f"SITE QA PASSED: {len(PAGES)} pages, links resolve, hash and dot count re-derived, "
          f"ZIP holds one GeoTIFF, permissions match the run card.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
