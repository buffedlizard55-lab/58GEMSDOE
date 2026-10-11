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


def test_uniqueness_readings_recompute_under_the_ratified_rule() -> None:
    """RATIFIED-UNIQ-v1 must be applied to the screen, not asserted in prose.

    The counts in ``uniqueness_readings.json`` are recomputed here from the raw
    ``uniqueness_full.json`` rows, so a receipt that drifts from the ratified
    thresholds fails the build.  The pre-ratification readings are required to be
    present as well: hidden or deleted literals fail the build too.
    """
    screen = json.loads((EV / "uniqueness_full.json").read_text())
    readings = json.loads((EV / "uniqueness_readings.json").read_text())
    assert screen["pin_size_mismatches"] == 0, "a witness that does not match its pin must fail the build"
    assert readings["n_pinned"] >= 600, "the governing screen must cover the restored inventory"
    assert readings["rule_id"] == "RATIFIED-UNIQ-v1", readings["rule_id"]

    rows = [r for r in screen["rows"] if r.get("forward_overlap") is not None]
    fwd = lambda r: r.get("forward_overlap") or 0.0
    E = lambda r: r.get("their_dilated_frac_of_footprint") or 0.0
    lift = lambda r: r.get("chance_corrected_lift") or 0.0
    rule_a = [r for r in rows if fwd(r) > 0.70 and E(r) < 0.70]
    rule_b = [r for r in rows if lift(r) > 0.50 and E(r) < 0.99]
    rho = [r for r in rows if (r.get("rho_full_footprint") or 0.0) > 0.90]
    jac = [r for r in rows if (r.get("jaccard") or 0.0) > 0.50]
    assert readings["rule_a"]["n"] == len(rule_a), "rule A count must equal the screen"
    assert readings["rule_b"]["n"] == len(rule_b), "rule B count must equal the screen"
    assert readings["rho"]["n"] == len(rho) and readings["jaccard"]["n"] == len(jac)
    expected_cleared = not (rule_a or rule_b or rho or jac)
    assert readings["governing"]["cleared"] is expected_cleared, readings["governing"]
    assert ("UNIQUE" in readings["governing"]["verdict"]) is expected_cleared

    # the pre-ratification readings stay published, exactly and with their scope
    assert readings["literal"]["n"] == screen["n_forward_firings"] > 0
    assert readings["literal"]["n_vacuous"] > 0
    assert readings["e_strict_variant"]["n"] == len(
        [r for r in rows if fwd(r) > 0.70 and E(r) <= 0.61])
    assert readings["max_chance_corrected_lift"] <= 0.50
    for firing in readings["rule_a"]["firings"]:
        assert firing.get("witness") and firing.get("E") is not None


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
    readings = json.loads((EV / "uniqueness_readings.json").read_text())
    overlap = card["registry_overlap"]
    cleared = readings["governing"]["cleared"]
    assert overlap["governing_rule_id"] == "RATIFIED-UNIQ-v1"
    assert overlap["governing_cleared"] is cleared, "the card must repeat the governing verdict"
    assert overlap["rule_a_firings"] == readings["rule_a"]["n"]
    assert overlap["rule_b_firings"] == readings["rule_b"]["n"] == 0
    assert overlap["e_strict_variant_firings"] == readings["e_strict_variant"]["n"]
    assert overlap["worst_rank_correlation_all"] < 0.90
    assert card["validator"]["verify_passed"] == card["validator"]["verify_total"]
    assert card["validator"]["on_catalogue_positive_pixels"] == 0
    note = card["submission"]["note"]
    assert 0 < len(note) <= 140
    decision = card["verdict"]["decision"]
    if cleared:
        assert decision.startswith("PROMOTE")
    else:
        assert decision.startswith("STOP") and "RATIFIED-UNIQ-v1" in decision, decision
    unverified = card["verdict"]["what_is_not_verified"].lower()
    assert "no organizer receipt" in unverified and "holdout" in unverified, \
        "the card must state that the leaderboard value is unverified"


def test_published_pages_carry_the_same_banner_as_the_gates() -> None:
    page = ROOT / "docs" / "gems60.html"
    index = ROOT / "docs" / "index.html"
    if not page.exists():
        pytest.skip("page not built in this checkout")
    text = page.read_text()
    readings = json.loads((EV / "uniqueness_readings.json").read_text())
    cleared = readings["governing"]["cleared"]
    assert ("OK TO DOWNLOAD AND SUBMIT" in text) is cleared, \
        "the rendered banner must agree with the governing readings"
    assert ("NOT CLEARED" in text) is not cleared
    assert re.search(r"big-btn[^>]*downloads/gems60-convergence-ribbon6-.*\.tif", text), \
        "the one-click download button must point at the pinned raster"
    if index.exists():
        # Historical session-5 status must not be injected into the current front door.
        current = index.read_text()
        assert "<!-- session5:begin -->" not in current
        assert "NOT OK TO SUBMIT" in current
        assert "DO NOT SUBMIT" in current
