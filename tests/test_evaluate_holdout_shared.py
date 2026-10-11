import numpy as np

from gems57.evaluate_holdout import evaluate, from_terms
from gems57.metric import dti_exact


def test_shared_evaluator_matches_exact_metric_and_merges_global_blocks():
    h, w = 18, 21
    prediction = np.zeros((h, w), dtype=np.float32)
    prediction[4, 4:12:3] = 1.0
    prediction[9, 11:18:3] = 0.5
    truth = np.zeros((h, w), dtype=bool)
    truth[5, 5:14:4] = True
    active = np.ones((h, w), dtype=bool)
    active[0, :] = False
    visible = np.zeros_like(active)
    fold = dict(truth=truth, region=np.ones_like(active),
                visible=visible, masked_known=visible)

    result, terms = evaluate(
        prediction, fold, valid=active, block_side=5,
        origin=(100, 200), global_shape=(150, 250))
    expected = dti_exact(prediction, truth, valid=active)

    for key in ("tp", "fp", "fn", "dti"):
        assert result[key] == expected[key]
    assert result["evaluator_version"] == "gems57-pooled-hide-v2"
    assert terms.shape == (30 * 50 // (1 * 1), 4)
    np.testing.assert_allclose(
        terms.sum(axis=0),
        [result["tp"], result["fp"], result["fn"], result["n_truth"]],
        rtol=1e-11, atol=1e-7)
    assert np.isclose(from_terms(terms.sum(axis=0)), result["dti"])


def test_shared_evaluator_rejects_invalid_predictions_even_outside_active_region():
    prediction = np.zeros((8, 8), dtype=np.float32)
    prediction[0, 0] = np.nan
    truth = np.zeros((8, 8), dtype=bool)
    truth[4, 4] = True
    mask = np.ones_like(truth)
    fold = dict(truth=truth, region=mask, visible=np.zeros_like(mask))
    try:
        evaluate(prediction, fold, valid=mask)
    except ValueError:
        pass
    else:
        raise AssertionError("non-finite input must fail closed before masking")
