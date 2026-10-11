"""Submission format: the portal's [0, 1] rule and the example-template contract."""

from __future__ import annotations

import numpy as np
import pytest
import rasterio

from gems58 import grid, submission


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    fp = grid.footprint()
    cat = grid.catalogue()
    dots = np.zeros(fp.shape, bool)
    dots[1000:1010, 1000:1010] = True
    dots &= ~cat
    p = tmp_path_factory.mktemp("sub") / "t.tif"
    submission.write(p, dots)
    return p, dots


def test_written_file_passes_every_check(tiny):
    p, dots = tiny
    v = submission.validate(p, min_dots=10, max_dots=100000)
    assert v["passed"], {k: c for k, c in v["checks"].items() if not c["ok"]}
    assert v["n_positives"] == int(dots.sum()) and v["n_positives"] > 0


def test_finite_mask_equals_the_official_footprint(tiny):
    p, _ = tiny
    with rasterio.open(p) as s:
        a = s.read(1)
    assert (np.isfinite(a) == grid.footprint()).all()
    assert a[grid.footprint()].min() >= 0.0 and a[grid.footprint()].max() <= 1.0


def test_positives_are_exactly_one(tiny):
    p, _ = tiny
    with rasterio.open(p) as s:
        a = s.read(1)
    assert set(np.unique(a[np.isfinite(a)])) <= {0.0, 1.0}


def test_nan_inside_footprint_is_rejected(tmp_path):
    """The portal error the user hit: 'Predicted values must be in range [0, 1]'."""
    from gems58.metric import dti_exact

    fp = grid.footprint()
    pred = np.zeros(fp.shape, float)
    pred[1000, 1000] = np.nan
    truth = np.zeros(fp.shape, bool)
    truth[1001, 1001] = True
    with pytest.raises(ValueError, match="finite"):
        dti_exact(pred, truth, valid=fp)
    pred2 = np.zeros(fp.shape, float)
    pred2[1000, 1000] = 2.0
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        dti_exact(pred2, truth, valid=fp)


def test_out_of_footprint_dots_are_refused():
    fp = grid.footprint()
    dots = np.zeros(fp.shape, bool)
    outside = np.argwhere(~fp)[0]
    dots[outside[0], outside[1]] = True
    with pytest.raises(ValueError, match="outside the competition footprint"):
        submission.write("/tmp/_never_written.tif", dots)


def test_written_file_has_no_positive_on_the_catalogue(tiny):
    p, _ = tiny
    v = submission.validate(p, min_dots=10, max_dots=100000)
    assert v["checks"]["no_positive_on_catalogue"]["ok"]


def test_note_limit():
    assert len(submission.note("a" * 140)) == 140
    with pytest.raises(ValueError):
        submission.note("a" * 141)
