#!/usr/bin/env python3
"""Chance-corrected dot-overlap diagnostic against the restored registry.

The literal gate (gems57.uniqueness) flags a candidate when more than 70% of its
dots lie within 3 px of one registry raster's dots. For a BLANKET registry raster
(one whose dots cover the scored footprint, e.g. GEMSDOE2 turbo-simple with
5,167,373 dots = footprint size) that statistic is 1.0 for ANY non-empty candidate,
so the literal gate cannot be passed by construction. This script does NOT change
the literal gate. It reports, next to it, the expected overlap under chance
placement E = fraction of footprint within 3 px of the registry raster's dots, and
the lift (observed - E) / (1 - E). Registry rasters with E >= 0.99 are marked
SATURATED (the statistic carries no information for them).

Output: evidence/ribbon_uniqueness_chance_corrected.json (REGISTRY-MEASUREMENT).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.grid import load_grid  # noqa: E402
from gems57.uniqueness import RADIUS_PX, _dots, _near  # noqa: E402

CANDIDATE = ROOT / "docs/downloads/gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros.tif"
LITERAL = ROOT / "evidence/ribbon_uniqueness.json"
OUT = ROOT / "evidence/ribbon_uniqueness_chance_corrected.json"
SATURATED_E = 0.99


def main() -> int:
    grid = load_grid(ROOT / "data" / "bridge")
    fp = grid.footprint
    with rasterio.open(CANDIDATE) as src:
        mine = src.read(1).astype(np.float32)
    M = _dots(mine) & fp
    n_my = int(M.sum())
    literal = json.loads(LITERAL.read_text())
    rows = literal["rows"]
    fp_n = int(fp.sum())
    out_rows = []
    for r in rows:
        if "error" in r or not r.get("file"):
            out_rows.append({"submission": r.get("submission"), "error": r.get("error", "no file")})
            continue
        path = Path(r["file"])
        if not path.exists():
            out_rows.append({"submission": r["submission"], "error": "cache file missing"})
            continue
        with rasterio.open(path) as src:
            t = _dots(src.read(1)) & fp
        near_t = _near(t, RADIUS_PX)
        E = float(near_t.sum()) / fp_n
        obs = float(near_t[M].mean()) if n_my else 0.0
        lift = (obs - E) / (1.0 - E) if E < 1.0 else float("nan")
        out_rows.append({
            "submission": r["submission"],
            "their_dots_in_footprint": int(t.sum()),
            "literal_overlap_observed": obs,
            "chance_expected_overlap_E": E,
            "chance_corrected_lift": lift,
            "saturated": bool(E >= SATURATED_E),
            "literal_flag_70pct": bool(obs > 0.7),
        })
        print(f"{r['submission'][:60]:60s} obs={obs:.3f} E={E:.3f} lift={lift:.3f}", flush=True)

    scored = [x for x in out_rows if "error" not in x]
    informative = [x for x in scored if not x["saturated"]]
    flagged_literal = [x for x in scored if x["literal_flag_70pct"]]
    flagged_literal_informative = [x for x in flagged_literal if not x["saturated"]]
    summary = {
        "evidence_class": "REGISTRY-MEASUREMENT (diagnostic; literal gate unchanged)",
        "candidate": str(CANDIDATE.relative_to(ROOT)),
        "candidate_dots_in_footprint": n_my,
        "footprint_cells": fp_n,
        "radius_px": RADIUS_PX,
        "saturated_threshold_E": SATURATED_E,
        "rasters_scored": len(scored),
        "rasters_errored": len(out_rows) - len(scored),
        "literal_flagged_70pct": len(flagged_literal),
        "literal_flagged_and_saturated": len(flagged_literal) - len(flagged_literal_informative),
        "literal_flagged_and_informative": len(flagged_literal_informative),
        "max_lift_informative": max((x["chance_corrected_lift"] for x in informative), default=None),
        "top_informative_by_lift": sorted(
            [{k: x[k] for k in ("submission", "their_dots_in_footprint", "literal_overlap_observed",
                                "chance_expected_overlap_E", "chance_corrected_lift")} for x in informative],
            key=lambda x: -x["chance_corrected_lift"])[:12],
        "note": ("Literal gate unchanged. Saturated rasters (E>=0.99) cannot be cleared by any "
                 "non-empty candidate under the literal rule. Whether lift-based clearance is the "
                 "correct rule is a PROJECT-OWNER decision, not made here."),
    }
    OUT.write_text(json.dumps({"summary": summary, "rows": out_rows}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
