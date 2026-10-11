"""Repository hygiene: published pages must not promise what the receipt denies."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_run_card_exists_and_declares_the_download_permission():
    card = json.loads((ROOT / "evidence" / "ribbon" / "run_card.json").read_text())
    for key in ("name", "raster_sha256", "raster_bytes", "validator", "registry",
                "holdout_dti", "geometry", "submission_note", "verdict"):
        assert key in card, key
    assert card["validator"]["passed"] is True
    assert len(card["submission_note"]) <= 140
    assert card["verdict"].startswith("candidate")


def test_downloaded_tif_matches_the_card_hash():
    from gems58w import submission

    card = json.loads((ROOT / "evidence" / "ribbon" / "run_card.json").read_text())
    p = ROOT / "docs" / "ribbon" / "downloads" / f"{card['name']}.tif"
    assert p.exists(), p
    assert submission.sha256(p) == card["raster_sha256"]
    assert p.stat().st_size == card["raster_bytes"]


def test_zip_holds_exactly_one_geotiff():
    import zipfile

    card = json.loads((ROOT / "evidence" / "ribbon" / "run_card.json").read_text())
    p = ROOT / "docs" / "ribbon" / "downloads" / f"{card['name']}.zip"
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
    assert len(names) == 1 and names[0].endswith(".tif")


def test_readme_carries_the_standing_prompt():
    txt = (ROOT / "README.md").read_text() + (ROOT / "PROMPT.md").read_text()
    assert "PARALLEL-RUN PROTOCOL" in txt
    assert "0.3195" in txt
    assert "Maximize P(Win)" in txt
