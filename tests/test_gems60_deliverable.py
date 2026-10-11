"""Fail-closed checks on the session-5 deliverable and its receipts.

These tests are the machine-checkable half of the site's banner: if any of them
fails, the published page must not claim the file is cleared.  They read only the
committed bytes and receipts, so they run in CI without the feature stack or the
registry witness cache.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs" / "downloads"
EV = ROOT / "evidence" / "gems60"
EMIT = "gems60-convergence-ribbon6-20261011T155420Z"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def tif() -> Path:
    p = DL / f"{EMIT}.tif"
    if not p.exists():
        pytest.skip(f"{p.name} is not committed")
    return p


def test_the_emit_raster_is_present_and_hash_pinned(tif: Path) -> None:
    emit = json.loads((DL / f"{EMIT}.json").read_text())
    verify = json.loads((DL / f"{EMIT}.checks.json").read_text())
    card = json.loads((EV / "run_card.json").read_text())
    digest = sha256(tif)
    assert digest == emit["sha256"] == verify["sha256"] == card["raster"]["sha256"]
    assert verify["passed"] == verify["total"] and verify["verdict"] == "LOCAL FORMAT OK"
    assert card["raster"]["sha256_matches_receipt"] is True


def test_values_are_exactly_binary_and_finite(tif: Path) -> None:
    import rasterio

    with rasterio.open(tif) as src:
        a = src.read(1)
        assert src.count == 1 and src.dtypes[0] == "float32"
        assert str(src.crs) == "EPSG:32611" and src.shape == (3730, 3292)
    assert np.isfinite(a).all(), "no cell may be NaN or infinite"
    assert set(np.unique(a).tolist()) == {0.0, 1.0}, "every emitted value is exactly 1.0"
    assert int((a > 0).sum()) == 40000


def test_zero_positive_mass_on_the_mapped_catalogue(tif: Path) -> None:
    import rasterio

    with rasterio.open(tif) as src:
        a = src.read(1)
    with rasterio.open(ROOT / "data" / "official" / "existing_faults.tif") as src:
        cat = src.read(1) == 1
    assert not (a > 0)[cat].any(), "the organiser masks catalogue pixels; emitting on them is inert"


def test_uniqueness_governing_readings_have_no_firing() -> None:
    screen = json.loads((EV / "uniqueness_full.json").read_text())
    readings = json.loads((EV / "uniqueness_readings.json").read_text())
    assert screen["pin_size_mismatches"] == 0, "a witness that does not match its pin must fail the build"
    assert readings["n_pinned"] >= 600, "the governing screen must cover the restored inventory"
    assert readings["governing"]["cleared"] is True, readings["governing"]
    assert readings["lift"]["n"] == 0 and readings["e_threshold"]["n"] == 0
    assert readings["rho"]["n"] == 0 and readings["jaccard"]["n"] == 0
    assert readings["max_chance_corrected_lift"] <= 0.50
    # the literal reading is reported in full and must be explainable, never hidden
    assert readings["literal"]["n"] == screen["n_forward_firings"] > 0
    assert readings["literal"]["n_vacuous"] > 0


def test_holdout_number_is_labelled_and_carries_its_caveat() -> None:
    hold = json.loads((EV / "holdout.json").read_text())
    assert hold["evidence_class"] == "HOLDOUT-DTI"
    assert hold["withheld_positive_pixels"] > 0
    assert 0.0 <= hold["pooled_dti"] <= 1.0
    assert "catalogue" in hold["caveat"], "the catalogue-recovery caveat must be present"


def test_sigma_table_supports_the_emitted_ribbon_width() -> None:
    sigma = json.loads((EV / "sigma.json").read_text())
    med = [r["sigma_median_px"] for r in sigma["sigma"]
           if r.get("family") not in (None, "all") and r.get("sigma_median_px")]
    assert med, "the σ table must contain associated-candidate strata"
    assert min(med) >= 1.5, "if the measured error were sub-pixel the tight-line branch would apply"


def test_run_card_verdict_matches_the_gates_and_the_note_fits_the_portal() -> None:
    card = json.loads((EV / "run_card.json").read_text())
    assert card["registry_overlap"]["governing_cleared"] is True
    assert card["registry_overlap"]["lift_firings"] == 0
    assert card["registry_overlap"]["e_threshold_firings"] == 0
    assert card["validator"]["verify_passed"] == card["validator"]["verify_total"]
    assert card["validator"]["on_catalogue_positive_pixels"] == 0
    note = card["submission"]["note"]
    assert 0 < len(note) <= 140
    assert "PROMOTE" in card["verdict"]["decision"]
    unverified = card["verdict"]["what_is_not_verified"].lower()
    assert "no organizer receipt" in unverified and "holdout" in unverified, \
        "the card must state that the leaderboard value is unverified"


def test_published_pages_carry_the_same_banner_as_the_gates() -> None:
    page = ROOT / "docs" / "gems60.html"
    if not page.exists():
        pytest.skip("page not built in this checkout")
    text = page.read_text()
    card = json.loads((EV / "run_card.json").read_text())
    cleared = "OK TO DOWNLOAD AND SUBMIT" in text
    assert cleared == ("PROMOTE" in card["verdict"]["decision"]), \
        "the rendered banner must not disagree with the run card"
    assert re.search(r"big-btn[^>]*downloads/gems60-convergence-ribbon6-.*\.tif", text), \
        "the one-click download button must point at the pinned raster"
