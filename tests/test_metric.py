import numpy as np
import pytest

from gems.metric import dti, triangular_kernel, utility


def _line(h=40, w=40, row=20):
    lab = np.zeros((h, w), bool)
    lab[row, 5:35] = True
    return lab


def test_kernel_values():
    assert triangular_kernel(0) == 1.0
    assert triangular_kernel(150) == pytest.approx(0.5)
    assert triangular_kernel(300) == 0.0
    assert triangular_kernel(450) == 0.0


def test_perfect_prediction_scores_one():
    lab = _line()
    assert dti(lab.astype(float), lab) == pytest.approx(1.0, abs=1e-6)


def test_all_zero_prediction_scores_zero():
    lab = _line()
    assert dti(np.zeros(lab.shape), lab) == pytest.approx(0.0, abs=1e-6)


def test_one_pixel_offset_tolerance_is_graded():
    lab = _line()
    pred = np.zeros(lab.shape)
    pred[21, 5:35] = 1.0  # 100 m off the trace
    s, parts = dti(pred, lab, return_parts=True)
    # TP credit 2/3 per pixel, FP the remaining 1/3 (sum over 30 px)
    assert parts["TP_w"] == pytest.approx(30 * 2 / 3, rel=1e-6)
    assert parts["FP_w"] == pytest.approx(30 * 1 / 3, rel=1e-6)
    assert s > 0.5


def test_offset_at_300m_gets_no_credit():
    lab = _line()
    pred = np.zeros(lab.shape)
    pred[23, 5:35] = 1.0  # 300 m away
    _, parts = dti(pred, lab, return_parts=True)
    assert parts["TP_w"] == pytest.approx(0.0, abs=1e-9)


def test_nan_is_outside_footprint_and_free():
    lab = _line()
    pred = lab.astype(float)
    pred[:, :3] = np.nan  # outside footprint, no labels there
    assert dti(pred, lab) == pytest.approx(1.0, abs=1e-6)


def test_rejects_out_of_range():
    lab = _line()
    with pytest.raises(ValueError):
        dti(lab.astype(float) * 2, lab)


def test_thin_line_beats_diffuse_map():
    lab = _line()
    thin = lab.astype(float)
    diffuse = np.full(lab.shape, 0.5)
    assert dti(thin, lab) > dti(diffuse, lab)


def test_utility_formula():
    assert utility(0.3, 10, 4) == pytest.approx((1 - 0.06) * 10 - 0.06 * 4)
