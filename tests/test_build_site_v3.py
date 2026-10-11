"""Fail-closed tests for the session-4 site generator.

The properties tested here are the ones the owner's prompt makes non-negotiable:

* a gate whose receipt is *missing* is a FAIL, so the banner can never be green
  over an unmeasured gate;
* the organizer receipt (G5) can never contribute to a green banner, because no
  such receipt exists for any raster in this repository;
* the chance-corrected uniqueness reading (G2i) is always open -- it is a
  decision for the owner, not a measurement a script may close;
* the raster sha256 is taken from the bytes on disk, never from a receipt, so a
  receipt that describes a file that has since changed cannot pass;
* the stop limits are inclusive (exactly at the limit is still a stop).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location("build_site_v3", ROOT / "scripts" / "build_site_v3.py")
assert _spec and _spec.loader
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

DOC_BYTES = b"the bytes that are really on disk"
DOC_SHA = hashlib.sha256(DOC_BYTES).hexdigest()
CANON = dict(
    file="x.tif", sha256=DOC_SHA, bytes=1, submission_name="n", note="n", note_chars=1,
    validator=dict(all_checks_passed=True,
                   checks={"single_band": True, "no_nan_anywhere": True}),
    template_report=dict(ok=True, problems=[]))
EMI = dict(receipt=CANON, validate={}, format_report=dict(ok=True, problems=[]),
           stats=dict(n_dots=1, on_catalogue=0),
           holdout=dict(summary=dict(bootstrap=dict(draws=1000, clusters=636),
                                     scores=dict(delivered=dict(dti=0.01, ci95=[0.0, 0.02],
                                                                withheld_positive_pixels=60869)))))
UNIQ = dict(n_compared=694, n_witnesses=694, missing_or_invalid=0, inventory_complete=True,
            worst_spearman_full_footprint=0.05, worst_dot_overlap=0.10,
            worst_jaccard_dot_sets=0.01, byte_unique_among_checked=True,
            pixel_unique_among_checked=True, duplicate_count=0, unique=True, verdict="negative")
CANARY = dict(n_features=20, n_leaking=0, worst_auc=0.80)
RATIFIED = dict(n_scored=694, n_discriminating=618, rule_a_firings=0, rule_b_firings=0,
                e_limit=0.70, lift_limit=0.50, max_lift=0.30,
                worst_overlap_discriminating=0.20, worst_overlap_discriminating_E=0.10,
                max_lift_submission="x")
READING = dict(n_flagged_literal=81, n_flagged_degenerate=53, n_flagged_informative=28,
               worst_jaccard_among_flagged=0.01, worst_spearman_among_flagged=0.04,
               footprint_pixels=5167373)


@pytest.fixture(autouse=True)
def _docs_dir(tmp_path, monkeypatch):
    """A docs/downloads tree holding the one file the receipt describes."""
    (tmp_path / "downloads").mkdir(parents=True)
    (tmp_path / "downloads" / "x.tif").write_bytes(DOC_BYTES)
    monkeypatch.setattr(b3, "DOCS", tmp_path)
    return tmp_path


def gates(emi=None, uniq=None, canary=None, reading=None, ratified=None):
    return b3.evaluate_gates(emi if emi is not None else EMI,
                             uniq if uniq is not None else UNIQ,
                             canary if canary is not None else CANARY,
                             reading if reading is not None else READING,
                             ratified if ratified is not None else RATIFIED)


def ok_of(gs):
    return {g["id"]: bool(g["ok"]) for g in gs}


def gid(gs, i):
    return next(g for g in gs if g["id"] == i)


def test_g5_organizer_receipt_is_always_open_and_never_counts():
    gs, passing = gates()
    st = ok_of(gs)
    assert st["G5"] is False
    # every other gate is satisfiable, so G5 must be excluded from `passing`
    assert st["G1"] and st["G2"] and st["G2L"] and st["G3"] and st["G4"]
    assert passing is True


def test_missing_uniqueness_receipt_fails_closed():
    st = ok_of(gates(uniq={})[0])
    assert st["G2"] is False and st["G2L"] is False


def test_missing_ratified_measurement_fails_closed():
    """The ratified rule governs since 2026-10-11; without its rows, fail closed."""
    st = ok_of(gates(ratified={})[0])
    assert st["G2"] is False


def test_ratified_rule_a_firing_blocks():
    st = ok_of(gates(ratified={**RATIFIED, "rule_a_firings": 7,
                               "worst_overlap_discriminating": 0.7887,
                               "worst_overlap_discriminating_E": 0.6456})[0])
    assert st["G2"] is False


def test_ratified_rule_b_firing_blocks():
    st = ok_of(gates(ratified={**RATIFIED, "rule_b_firings": 1, "max_lift": 0.5624})[0])
    assert st["G2"] is False


def test_literal_reading_is_a_hard_stop_even_when_ratified_passes():
    """Both readings are mandatory stops; clearing one does not clear the banner."""
    st = ok_of(gates(uniq={**UNIQ, "worst_dot_overlap": 1.0, "duplicate_count": 81,
                           "unique": False, "verdict": "negative"})[0])
    assert st["G2"] is True          # ratified A/B both clean
    assert st["G2L"] is False        # literal reading still fires
    assert gates(uniq={**UNIQ, "worst_dot_overlap": 1.0, "duplicate_count": 81,
                       "unique": False, "verdict": "negative"})[1] is False


def test_missing_canary_fails_closed():
    st = ok_of(gates(canary={})[0])
    assert st["G3"] is False


def test_chance_corrected_reading_never_closes_itself():
    st = ok_of(gates(reading=READING)[0])
    assert st["G2i"] is False


def test_stop_limits_are_inclusive():
    assert gid(gates(uniq={**UNIQ, "worst_spearman_full_footprint": 0.90})[0], "G2")["ok"] is False
    assert gid(gates(uniq={**UNIQ, "worst_dot_overlap": 0.70})[0], "G2L")["ok"] is False
    assert gid(gates(canary={**CANARY, "worst_auc": 0.90})[0], "G3")["ok"] is False


def test_incomplete_inventory_cannot_pass():
    st = ok_of(gates(uniq={**UNIQ, "inventory_complete": False})[0])
    assert st["G2"] is False and st["G2L"] is False


def test_sha_taken_from_disk_not_from_the_receipt(tmp_path: Path):
    """A receipt describing one file while another sits at that path must FAIL."""
    (tmp_path / "downloads" / "x.tif").write_bytes(b"swapped bytes")
    assert ok_of(gates()[0])["G1"] is False


def test_a_receipt_for_a_file_that_is_not_there_fails(tmp_path: Path):
    (tmp_path / "downloads" / "x.tif").unlink()
    assert ok_of(gates()[0])["G1"] is False


def test_unmeasured_holdout_score_fails_g4():
    st = ok_of(gates(emi={**EMI, "holdout": {}})[0])
    assert st["G4"] is False


def test_rendered_pages_carry_the_verdict_strings(tmp_path: Path, monkeypatch):
    """The banner on every page must agree with the gate state, in both directions."""
    docs = tmp_path / "docs"
    docs.mkdir()
    monkeypatch.setattr(b3, "DOCS", docs)
    monkeypatch.setattr(b3, "EV", ROOT / "evidence" / "ribbon_v3")

    gs, passing = gates()
    idx = b3.build_index(EMI, UNIQ, {}, gs, passing, "")
    assert ("OK TO DOWNLOAD AND SUBMIT" in idx) == passing
    assert ("NOT OK TO SUBMIT" in idx) is not passing

    gs_bad, bad = gates(uniq={**UNIQ, "worst_dot_overlap": 1.0, "unique": False,
                              "duplicate_count": 81, "verdict": "negative"})
    idx_bad = b3.build_index(EMI, UNIQ, {}, gs_bad, bad, "")
    assert "NOT OK TO SUBMIT" in idx_bad and "DO NOT SUBMIT" in idx_bad
    assert "OK TO DOWNLOAD AND SUBMIT" not in idx_bad
    for page in (b3.build_exec(EMI, gs_bad, bad),
                 b3.build_evidence(EMI, UNIQ, {}, {}, {}, gs_bad, bad)):
        assert "NOT OK TO SUBMIT" in page
        assert "OK TO DOWNLOAD AND SUBMIT" not in page


def test_download_buttons_are_present_on_both_owner_screens():
    gs, passing = gates()
    for page in (b3.build_index(EMI, UNIQ, {}, gs, passing, ""),
                 b3.build_exec(EMI, gs, passing)):
        assert "Download the GeoTIFF" in page
        assert "big-btn" in page
        assert ".tif" in page and ".zip" in page


def test_executive_summary_states_the_portal_steps():
    gs, passing = gates()
    page = b3.build_exec(EMI, gs, passing)
    assert "New submission" in page
    assert "Create submission" in page
    assert "140" in page
    assert "range [0, 1]" in page
    # a NOT OK verdict must say so in the download area too
    bad = gates(uniq={**UNIQ, "worst_dot_overlap": 1.0, "unique": False})[1]
    assert "Do not submit this file yet" in b3.build_exec(
        EMI, gates(uniq={**UNIQ, "worst_dot_overlap": 1.0, "unique": False})[0], bad)


def test_empty_state_renders_when_no_artifact_exists(tmp_path: Path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    monkeypatch.setattr(b3, "DOCS", docs)
    monkeypatch.setattr(b3, "EV", tmp_path)
    assert b3.main([]) == 2
    assert "NOT OK TO SUBMIT" in (docs / "index.html").read_text()
