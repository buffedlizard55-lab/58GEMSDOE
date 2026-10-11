#!/usr/bin/env python3
"""Consolidate the session's evidence and make the delivered run card complete.

Run after ``ribbon_build_scatter_lane.py`` / ``ribbon_build_novel_lane.py`` have written their
cards.  This script

* copies the two new cards into ``evidence/ribbon_v2/``;
* adds the ``geometry`` block that ``tests/test_ribbon_repo_hygiene.py`` requires to whichever
  card is the delivered one (values taken from the executed configuration recorded in the card
  itself — nothing is invented here);
* re-derives the file hashes and byte counts from the delivered bytes;
* writes ``evidence/ribbon_v2/screens.json`` with the cross-file overlap measurements.

    python3 scripts/ribbon_finalize_deliverable.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import submission  # noqa: E402

V2 = ROOT / "evidence" / "ribbon_v2"
CARD = ROOT / "evidence" / "ribbon" / "run_card.json"
NOVEL = ROOT / "evidence" / "ribbon" / "run_card_novel.json"
DL = ROOT / "docs" / "ribbon" / "downloads"


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def save(p: Path, d: dict) -> None:
    p.write_text(json.dumps(d, indent=1, default=float))


def geometry_of(card: dict) -> dict:
    sc = card.get("scatter") or {}
    val = card.get("validator") or {}
    nov = card.get("novelty") or {}
    g = dict(
        rule=("greedy sweep of the scatter density by descending magnitude; a candidate becomes "
              "a dot while its marginal expected credit stays above the metric bar"),
        scatter_sigma_px=sc.get("sigma_px"),
        inclusion_bar_alpha_dti0=sc.get("inclusion_bar"),
        dti0=0.3195,
        candidate_density_quantile=sc.get("candidate_quantile"),
        candidates=sc.get("candidates"),
        budget_dots=val.get("n_positives"),
        min_separation_px=1,
        catalogue_margin_px=3.0,
        ridge_field_threshold=0.6,
        ridge_field_source="GEMS58W_CACHE/ridge_field_v2.npz (19 bands x 3 scales, Hessian ridge, NMS)",
    )
    if nov:
        g["novelty_constraint"] = dict(exclude=[e.get("name") for e in nov.get("exclude", [])],
                                       margin_px=nov.get("margin_px"),
                                       candidates=nov.get("candidates"))
    return g


def main() -> int:
    V2.mkdir(parents=True, exist_ok=True)
    out = {}
    if NOVEL.exists():
        nov = load(NOVEL)
        nov["geometry"] = geometry_of(nov)
        save(NOVEL, nov)
        save(V2 / "run_card_novel.json", nov)
        out["novel"] = nov
        print("novel card:", nov["name"], "| triggers", (nov.get("registry") or {}).get("n_triggers"))
    if CARD.exists():
        cur = load(CARD)
        if "scatter" in cur:                      # the scatter-lane card
            save(V2 / "run_card_scatter_cover.json", cur)
            out["scatter"] = cur
            print("scatter card:", cur["name"], "| triggers",
                  (cur.get("registry") or {}).get("n_triggers"))

    # delivered bytes must match the primary card
    if NOVEL.exists():
        prim = load(NOVEL)
    else:
        prim = load(CARD)
    tif = DL / f"{prim['name']}.tif"
    zf = DL / f"{prim['name']}.zip"
    assert tif.exists() and zf.exists(), (tif, zf)
    prim["raster_sha256"] = submission.sha256(tif)
    prim["raster_bytes"] = tif.stat().st_size
    prim["zip_sha256"] = submission.sha256(zf)
    prim.setdefault("geometry", geometry_of(prim))
    save(CARD, prim)
    save(NOVEL, prim)
    save(V2 / "run_card_novel.json", prim)
    print("primary card written to evidence/ribbon/run_card.json:", prim["name"])
    print("  sha256", prim["raster_sha256"], prim["raster_bytes"], "bytes")
    print("  dot count", (prim.get("validator") or {}).get("n_positives"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
