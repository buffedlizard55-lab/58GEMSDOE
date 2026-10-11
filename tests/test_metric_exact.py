import numpy as np
import pytest

from gems58.metric import (ALPHA, BETA, dti_binary, dti_bruteforce, dti_from_components,
                         dti_soft, utility_U)
from gems57.metric import (ALPHA as SHARED_ALPHA, dti_binary as shared_dti_binary,
                         kernel as shared_kernel, marginal_accept as shared_marginal_accept)


def test_rules_worked_example_numbers():
    # Official rules/problem page worked example: TP=3.00, FP=1.89, FN=2.00 -> 0.60
    tp, fp, fn = 3.00, 1.89, 2.00
    assert round(tp / (tp + 0.2 * fp + 0.8 * fn), 2) == 0.60
    assert dti_from_components(tp, fp, n_truth=int(round(tp + fn))) == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn), rel=1e-9)


def test_constants_match_official_definition():
    assert ALPHA == 0.2 and BETA == 0.8


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_vectorised_matches_bruteforce(seed):
    rng = np.random.default_rng(seed)
    truth = np.zeros((14, 16), bool)
    truth[rng.integers(0, 14, 12), rng.integers(0, 16, 12)] = True
    pred = np.zeros((14, 16))
    m = rng.random((14, 16)) < 0.25
    pred[m] = rng.random(m.sum())
    fast = dti_soft(pred, truth)
    slow = dti_bruteforce(pred, truth)
    assert fast.tp == pytest.approx(slow["tp"], abs=1e-9)
    assert fast.fp == pytest.approx(slow["fp"], abs=1e-9)
    assert fast.dti == pytest.approx(slow["dti"], abs=1e-9)


def test_binary_matches_soft_on_binary_input():
    rng = np.random.default_rng(3)
    truth = rng.random((20, 20)) < 0.05
    pred = rng.random((20, 20)) < 0.2
    a = dti_binary(pred, truth)
    b = dti_soft(pred.astype(float), truth)
    assert a.dti == pytest.approx(b.dti, abs=1e-12)


def test_known_mask_removes_pixels_from_score():
    truth = np.zeros((9, 9), bool)
    truth[4, :] = True
    pred = np.zeros((9, 9))
    pred[0, :] = 1.0  # far from the truth line: pure FP
    base = dti_soft(pred, truth)
    known = np.zeros((9, 9), bool)
    known[0, :] = True
    masked = dti_soft(pred, truth, known=known)
    assert base.fp > 0 and masked.fp == 0.0


def test_out_of_range_predictions_rejected():
    with pytest.raises(ValueError):
        dti_soft(np.full((4, 4), 1.5), np.zeros((4, 4), bool))


def test_U_is_linearisation_sign():
    # Adding a dot that lands on truth (dTP=1, dFP=0) must increase U; a pure FP must decrease it.
    assert utility_U(1.0, 0.0, 0.3) > 0
    assert utility_U(0.0, 1.0, 0.3) < 0


def test_redundant_dot_does_not_use_isolated_threshold():
    """A high self-credit dot can lower DTI when an earlier dot owns the truth credit."""
    truth = np.zeros((7, 7), bool)
    truth[3, 3] = True
    before = np.zeros_like(truth)
    before[3, 3] = True
    after = before.copy()
    after[3, 4] = True  # self-credit 2/3, but the central dot already earns TP=1

    r0 = shared_dti_binary(before, truth)
    r1 = shared_dti_binary(after, truth)
    k_self = float(shared_kernel(1.0))
    assert k_self > SHARED_ALPHA * r0["dti"]  # the isolated-dot shortcut would accept it
    assert r1["tp"] == pytest.approx(r0["tp"])
    assert r1["fp"] > r0["fp"]
    assert r1["dti"] < r0["dti"]
    assert not shared_marginal_accept(
        dT=r1["tp"] - r0["tp"], k_self=k_self, T=r0["tp"], M=1.0, n=1, K=1.0
    )


def test_pattern_utility_identity_matches_shared_metric():
    """Exact setwise ΔTP/ΔFP predict the sign of full DTI change, with interactions."""
    truth = np.zeros((9, 10), bool)
    truth[4, 3] = True
    truth[4, 7] = True
    before = np.zeros_like(truth)
    before[4, 3] = True
    after = before.copy()
    after[4, 6] = True  # adds credit to the second truth pixel
    after[4, 4] = True  # redundant/overlapping with credit around the first pixel

    r0 = shared_dti_binary(before, truth)
    r1 = shared_dti_binary(after, truth)
    d_tp, d_fp = r1["tp"] - r0["tp"], r1["fp"] - r0["fp"]
    utility = (1.0 - SHARED_ALPHA * r0["dti"]) * d_tp - SHARED_ALPHA * r0["dti"] * d_fp
    assert utility > 0
    assert r1["dti"] > r0["dti"]

    redundant = before.copy()
    redundant[4, 4] = True
    r2 = shared_dti_binary(redundant, truth)
    d_tp2, d_fp2 = r2["tp"] - r0["tp"], r2["fp"] - r0["fp"]
    utility2 = (1.0 - SHARED_ALPHA * r0["dti"]) * d_tp2 - SHARED_ALPHA * r0["dti"] * d_fp2
    assert utility2 < 0
    assert r2["dti"] < r0["dti"]
