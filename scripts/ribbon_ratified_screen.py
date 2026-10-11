#!/usr/bin/env python3
"""Apply the ratified uniqueness protocol (RATIFIED-UNIQ-v1) to the session-4 raster.

Rules (PROMPT.md protocol item 1, ratified in session 5):

    rule A   literal forward 3 px overlap O > 0.70 against a witness whose chance
             expectation E < 0.70
    rule B   chance-corrected lift  (O - E) / (1 - E) > 0.50  against any witness
             with E < 0.99 (at E -> 1 the lift degenerates to ~1 for every
             nonempty candidate, so saturated witnesses cannot inform either rule)

E is the share of the study footprint lying within 3 px of the witness's dots:
the overlap a candidate would score by chance alone.  This script re-reads the
same 694 byte-verified witnesses already scanned by ``ribbon_screen_final.py`` and
merges the E / lift columns into a copy of those rows, so the ratified numbers sit
beside the literal ones on the same witnesses.  It never touches either gate's
definition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems57.uniqueness import RADIUS_PX, _dots, _near   # noqa: E402
from gems58w import grid as g58                          # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / "evidence" / "ribbon_v3" / "uniqueness_rows.json"
OUT = ROOT / "evidence" / "ribbon_v3" / "ratified_uniqueness.json"
SATURATED_E = 0.99
E_LIMIT = 0.70
LIFT_LIMIT = 0.50
OVERLAP_LIMIT = 0.70


def main() -> None:
    tif = Path(sys.argv[1])
    rows = json.loads(ROWS.read_text())
    fp = g58.footprint()
    fp_n = int(fp.sum())
    with rasterio.open(tif) as src:
        mine = src.read(1).astype(np.float32)
    M = _dots(mine) & fp
    n_my = int(M.sum())

    out = []
    for i, r in enumerate(rows):
        p = Path(r["file"])
        try:
            with rasterio.open(p) as src:
                t = _dots(src.read(1)) & fp
        except Exception as exc:                                # noqa: BLE001
            out.append({**r, "error": str(exc)})
            continue
        near = _near(t, RADIUS_PX)
        E = float(near[fp].sum()) / fp_n
        obs = float(near[M].mean()) if n_my else 0.0
        lift = (obs - E) / (1.0 - E) if E < 1.0 else float("nan")
        out.append({**r, "chance_expected_overlap": E, "chance_corrected_lift": lift,
                    "saturated": bool(E >= SATURATED_E)})
        if i % 50 == 0:
            print(f"  {i}/{len(rows)}  obs={obs:.3f} E={E:.3f} lift={lift:.3f} "
                  f"{r['submission'][:44]}", flush=True)

    scored = [r for r in out if "error" not in r]
    disc = [r for r in scored if (r.get("chance_expected_overlap") or 1.0) < E_LIMIT]
    rule_a = [r for r in disc if (r.get("my_dots_within_3px_of_theirs") or 0.0) > OVERLAP_LIMIT]
    lifts = [r for r in scored if r.get("chance_corrected_lift") == r.get("chance_corrected_lift")
             and (r.get("chance_expected_overlap") or 1.0) < SATURATED_E]
    rule_b = [r for r in lifts if r["chance_corrected_lift"] > LIFT_LIMIT]
    worst_a = max(disc, key=lambda r: r.get("my_dots_within_3px_of_theirs", 0.0), default=None)
    worst_b = max(lifts, key=lambda r: r["chance_corrected_lift"], default=None)
    rep = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        protocol="RATIFIED-UNIQ-v1 (ratified 2026-10-11 in session 5)",
        candidate=str(tif), candidate_dots_in_footprint=n_my,
        n_witnesses=len(rows), n_scored=len(scored), n_errors=len(out) - len(scored),
        e_limit=E_LIMIT, lift_limit=LIFT_LIMIT, overlap_limit=OVERLAP_LIMIT,
        n_discriminating=len(disc),
        worst_overlap_discriminating=(worst_a or {}).get("my_dots_within_3px_of_theirs"),
        worst_overlap_discriminating_E=(worst_a or {}).get("chance_expected_overlap"),
        worst_overlap_discriminating_submission=(worst_a or {}).get("submission"),
        rule_a_firings=len(rule_a),
        rule_a_submissions=[r["submission"] for r in rule_a][:10],
        max_lift=(worst_b or {}).get("chance_corrected_lift"),
        max_lift_submission=(worst_b or {}).get("submission"),
        max_lift_submission_E=(worst_b or {}).get("chance_expected_overlap"),
        rule_b_firings=len(rule_b),
        rule_b_submissions=[r["submission"] for r in rule_b][:10],
        ratified_ok=(len(rule_a) == 0 and len(rule_b) == 0),
        literal_firings=len([r for r in scored
                             if (r.get("my_dots_within_3px_of_theirs") or 0.0) > OVERLAP_LIMIT]),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=1, default=str))
    (OUT.with_name("ratified_uniqueness_rows.json")).write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: rep[k] for k in (
        "n_scored", "n_discriminating", "worst_overlap_discriminating",
        "worst_overlap_discriminating_E", "rule_a_firings", "max_lift",
        "max_lift_submission", "rule_b_firings", "ratified_ok", "literal_firings")}, indent=1))


if __name__ == "__main__":
    main()
