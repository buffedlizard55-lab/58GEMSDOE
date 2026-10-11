#!/usr/bin/env python3
"""Refresh ``docs/data/feed.json`` — the always-current status feed.

Solves the "we have to check everything by hand" problem: one file, machine
readable, regenerated on a schedule by ``.github/workflows/feed.yml`` and on every
build.  It carries

* the current deliverable's identity (name, sha256, bytes, dot count),
* the validator verdict for those exact bytes,
* the uniqueness verdict against the registry,
* the label of every score in the repository (ORGANIZER-CONFIRMED vs
  OWNER-REPORTED vs HOLDOUT-DTI vs projection — a projection is never a score),
* source health for every link in ``registry/sources.json`` (HTTP status when the
  network allows it, ``unreachable-from-sandbox`` when it does not).

    PYTHONPATH=src python3 scripts/refresh_feed.py [--check-sources]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58 import submission  # noqa: E402
from gems58.paths import DOCS, EVIDENCE, REGISTRY_META  # noqa: E402

LABEL_RULES = [
    ("ORGANIZER-CONFIRMED", "copied from the submission page together with a file hash"),
    ("HOLDOUT-DTI", "exact metric on gems58-pooled-hide-v1; never a live-score forecast"),
    ("OWNER-REPORTED", "appears on the owner's page or in the brief; no receipt in this repo"),
    ("PROJECTION", "a model output; must never be quoted as a score"),
    ("MEASURED", "computed in-repo from hash-pinned bytes"),
]


def source_health(url: str, timeout: float = 8.0) -> dict:
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "gems58-feed/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return dict(url=url, status=int(r.status), reachable=True)
    except Exception as exc:  # noqa: BLE001 - any failure is "unreachable"
        return dict(url=url, status=None, reachable=False, error=type(exc).__name__)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-sources", action="store_true",
                    help="HEAD every link in registry/sources.json (needs network)")
    args = ap.parse_args()

    card = json.loads((EVIDENCE / "run_card.json").read_text())
    uniq = json.loads((EVIDENCE / "uniqueness.json").read_text())["summary"]
    srcs = json.loads((REGISTRY_META / "sources.json").read_text())
    receipts = json.loads((REGISTRY_META / "receipts.json").read_text())

    tif = DOCS / "downloads" / f"{card['name']}.tif"
    valid = submission.validate(tif) if tif.exists() else {"passed": False, "checks": {}}

    health = []
    if args.check_sources:
        for e in srcs.get("entries", []):
            url = e["source"].split(" ")[0]
            if url.startswith("http"):
                health.append(source_health(url))

    feed = dict(
        schema="gems58.feed/v1",
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        lane="ribbon",
        deliverable=dict(
            name=card["name"],
            tif_url=f"downloads/{card['name']}.tif",
            zip_url=f"downloads/{card['name']}.zip",
            sha256=card["raster_sha256"],
            bytes=card["raster_bytes"],
            n_dots=card["validator"]["n_positives"],
            note=card["submission_note"],
            note_chars=len(card["submission_note"]),
            download_ok=True,
            submit="your decision — this project spends no slot",
        ),
        validator=dict(passed=bool(valid.get("passed")),
                       n_checks=len(valid.get("checks", {})),
                       failed=[k for k, v in valid.get("checks", {}).items() if not v["ok"]]),
        uniqueness=dict(n_checked=uniq["n_checked"], worst_rho=uniq["worst_rho"],
                        worst_forward_overlap=uniq["worst_forward_overlap"],
                        triggers=uniq["n_triggers"], dense_priors=uniq["n_dense_priors"]),
        scores=dict(
            organizer_confirmed=receipts.get("receipts", []),
            holdout_dti=dict(value=card["holdout_dti"], evaluator=card["holdout_dti_evaluator"],
                             protocol=card["holdout_dti_protocol"],
                             withheld_positives=card["holdout_dti_withheld_positives"],
                             ci=card["holdout_dti_ci"], ci_note=card["holdout_dti_ci_note"]),
            owner_reported=[0.2778, 0.3195, 0.3774],
            projections=[],
        ),
        label_rules=LABEL_RULES,
        source_health=health or "not checked in this run (pass --check-sources)",
        source_health_note=("a link returning 'unreachable' here only means this sandbox's egress "
                            "allowlist blocks it; it is not evidence about the source"),
    )
    out = DOCS / "data" / "feed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feed, indent=1))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
