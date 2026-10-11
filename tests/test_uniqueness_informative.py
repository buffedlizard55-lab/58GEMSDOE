"""The uniqueness instrument must report the protocol direction and separate
informative overlap firings from vacuous ones (IR-58-UNIQ-03, IR-58-UNIQ-04).

Synthetic grids only.  These tests validate the *instrument*, not any submission:
passing them is not registry clearance and not a competition score.
"""
from __future__ import annotations

import numpy as np
import pytest
import rasterio

from gems58w import grid, uniqueness
from gems57.uniqueness import (SATURATED_E, chance_expected_overlap, dot_overlap,
                               representation_class, summarize_registry_rows)


def _write(path, values, fp, g):
    a = np.full(fp.shape, np.nan, np.float32)
    a[fp] = 0.0
    a[values] = 1.0
    with rasterio.open(path, "w", driver="GTiff", height=g.height, width=g.width,
                       count=1, dtype="float32", crs=g.crs,
                       transform=rasterio.Affine(*g.transform), nodata=float("nan")) as s:
        s.write(a, 1)


def _two_far_blocks(fp, size=10):
    """Two ``size x size`` blocks that are entirely inside the footprint and far apart.

    The competition footprint is an irregular polygon covering 5,167,373 of the
    12,279,160 cells, so a hard-coded corner such as ``(3000, 3000)`` can land
    outside it; a witness that does not cover the candidate's dots then reads
    overlap 0 for the wrong reason.  Blocks are taken from an 11-erosion of the
    footprint and separated by more than 50 px.
    """
    from scipy.ndimage import binary_erosion

    er = binary_erosion(fp, structure=np.ones((11, 11), bool))
    ys, xs = np.nonzero(er)
    assert ys.size > 2
    i0 = 0
    dist = np.hypot(ys - ys[i0], xs - xs[i0])
    i1 = int(np.argmax(dist))
    assert dist[i1] > 50.0, "footprint too small to build a far-apart witness pair"
    blocks = []
    for i in (i0, i1):
        r, c = int(ys[i]) - 5, int(xs[i]) - 5
        b = np.zeros(fp.shape, bool)
        b[r:r + size, c:c + size] = True
        assert (b & ~fp).sum() == 0
        blocks.append(b)
    return blocks


@pytest.fixture(scope="module")
def witnesses(tmp_path_factory):
    d = tmp_path_factory.mktemp("wit")
    fp = grid.footprint()
    g = grid.grid()
    mine, far = _two_far_blocks(fp)             # 100 dots each, >50 px apart
    blanket = fp.copy()                         # every footprint pixel positive
    _write(d / "sparse_same.tif", mine, fp, g)
    _write(d / "blanket.tif", blanket, fp, g)
    return d, mine, far, blanket


def test_forward_overlap_is_my_dots_near_theirs():
    """Direction check: the protocol statistic is |my dots within 3 px of theirs| / |my dots|."""
    fp = grid.footprint()
    theirs_b, far_b = _two_far_blocks(fp)
    theirs = theirs_b.astype(np.float32)      # 100 witness dots
    ys, xs = np.nonzero(theirs_b)
    mine_in = np.zeros(fp.shape, np.float32)
    mine_in[ys[0], xs[0] + 2] = 1.0           # one of my dots, inside their block
    mine_far = far_b.astype(np.float32)       # 100 of my dots, >50 px away
    assert dot_overlap(mine_in, theirs, 3) == pytest.approx(1.0)
    assert dot_overlap(mine_far, theirs, 3) == pytest.approx(0.0)
    # the reverse statistic is a different number: only some of their 100 dots are
    # within 3 px of my single dot, so the two directions are not interchangeable
    rev = dot_overlap(theirs, mine_in, 3)
    assert 0.0 < rev < 1.0


def test_blanket_witness_fires_literally_but_is_saturated(witnesses):
    d, mine, _far, blanket = witnesses
    rows, summary = uniqueness.screen_against(mine, d)
    by = {r.name: r for r in rows}
    assert by["blanket.tif"].forward_overlap == pytest.approx(1.0)
    assert by["blanket.tif"].saturated is True
    assert by["blanket.tif"].chance_expected_overlap >= SATURATED_E
    assert "forward_overlap" in by["blanket.tif"].triggers
    assert "forward_overlap_informative" not in by["blanket.tif"].triggers
    assert summary["n_overlap_firings_vacuous"] >= 1


def test_sparse_duplicate_is_informative_and_blocks(witnesses):
    d, mine, _far, _blanket = witnesses
    rows, summary = uniqueness.screen_against(mine, d)
    by = {r.name: r for r in rows}
    assert by["sparse_same.tif"].forward_overlap == pytest.approx(1.0)
    assert by["sparse_same.tif"].saturated is False
    assert "forward_overlap_informative" in by["sparse_same.tif"].triggers
    assert summary["cleared"] is False
    assert summary["lane_drift_evidence"] == "informative"


def test_disjoint_candidate_clears_on_informative_witnesses(witnesses):
    """A candidate >50 px from a sparse witness clears it; the blanket witness can
    only produce a vacuous firing, which is labelled, never used as clearance."""
    d, _mine, far, _blanket = witnesses
    rows, summary = uniqueness.screen_against(far, d)
    by = {r.name: r for r in rows}
    assert by["sparse_same.tif"].forward_overlap == pytest.approx(0.0)
    assert by["blanket.tif"].forward_overlap == pytest.approx(1.0)
    assert by["blanket.tif"].saturated is True
    assert summary["worst_forward_overlap_informative"] == pytest.approx(0.0)
    assert summary["n_rho_firings"] == 0
    # the blanket witness still fires literally; that firing is labelled vacuous
    assert summary["lane_drift_evidence"] == "vacuous-only"
    assert summary["cleared"] is True


def test_chance_expected_overlap_matches_definition():
    fp = np.zeros((40, 40), bool)
    fp[5:35, 5:35] = True
    sup = np.zeros((40, 40), bool)
    sup[20, 20] = True
    e = chance_expected_overlap(sup, fp, 3.0)
    # a single witness dot covers the 3-px disk around it: 29 cells of 900
    assert e == pytest.approx(29.0 / int(fp.sum()))
    assert chance_expected_overlap(np.zeros((40, 40), bool), fp, 3.0) == 0.0


def test_representation_class_splits_dots_from_surfaces():
    assert representation_class(100, 10_000)["kind"] == "dot_field"
    assert representation_class(9_000, 10_000)["kind"] == "continuous_surface"


def test_summarize_registry_rows_reports_both_readings():
    """The shared template keeps the literal gate and adds the informative reading."""
    rows = [
        dict(submission="blanket", sha256="a" * 64, their_dots=5_000_000,
             my_dots_within_3px_of_theirs=1.0, spearman_full_footprint=0.01,
             jaccard_dot_sets=0.0, identical_bytes=False, identical_decoded_predictions=False,
             duplicate_by_rho=False, duplicate_by_overlap=True, duplicate_by_jaccard=False,
             chance_expected_overlap=0.999, chance_corrected_lift=0.1,
             representation="continuous_surface"),
        dict(submission="sparse", sha256="b" * 64, their_dots=40_000,
             my_dots_within_3px_of_theirs=0.20, spearman_full_footprint=0.10,
             jaccard_dot_sets=0.01, identical_bytes=False, identical_decoded_predictions=False,
             duplicate_by_rho=False, duplicate_by_overlap=False, duplicate_by_jaccard=False,
             chance_expected_overlap=0.10, chance_corrected_lift=0.11,
             representation="dot_field"),
    ]
    out = summarize_registry_rows(
        rows, registry_rasters_expected=2, complete_accessible_scan=True, source_errors=[],
        candidate_meta=dict(my_dots=40_000, candidate_rank_variation=True,
                            candidate_file_sha256="c" * 64, candidate_decoded_sha256="d" * 64),
        scope="test")
    ir = out["informative_reading"]
    assert ir["rasters_saturated"] == 1 and ir["rasters_informative"] == 1
    assert ir["overlap_firings"] == 1
    assert ir["overlap_firings_informative"] == 0
    assert ir["overlap_firings_vacuous"] == 1
    assert ir["lane_drift_evidence"] == "vacuous-only"
    assert ir["worst_forward_overlap_informative"] == pytest.approx(0.20)
    # the literal gate is unchanged: a firing still blocks and still reports worst 1.0
    assert out["worst_dot_overlap"] == pytest.approx(1.0)
    assert out["stop_required"] is True
