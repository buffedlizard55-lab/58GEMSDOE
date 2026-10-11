"""sigma lookup, ribbon geometry and the U rule."""

from __future__ import annotations

import numpy as np
import pytest

from gems58w import allocation, metric, sigma


def test_sigma_fallback_chain_is_recorded():
    table = dict(pooled=dict(median=2.0), by_block={"NW": dict(median=1.0)},
                 by_scale={"3px": dict(median=1.5)},
                 by_type={"gravity/crest": dict(median=1.2)},
                 by_type_scale={"gravity/crest/3px": dict(median=0.9)})
    v, which = sigma.sigma_for("gravity", 3.0, -1, "NW", table)
    assert which == "type_scale:gravity/crest/3px" and v == pytest.approx(0.9)
    v, which = sigma.sigma_for("magnetic", 1.5, 1, "SE", table)
    assert which == "scale:1.5px" or which == "block:SE" or which == "pooled"
    assert v >= sigma.SIGMA_FLOOR


def test_sigma_is_clamped_to_the_floor():
    table = dict(pooled=dict(median=0.01))
    v, _ = sigma.sigma_for("x", 3.0, 1, "NW", table)
    assert v == pytest.approx(sigma.SIGMA_FLOOR)


def test_sigma_table_hides_small_strata():
    items = [sigma.CompSigma(block="NW", comp_px=20, frac_within=1.0, sigma=1.0,
                             band="tmi", family="magnetic", scale=3.0, sign=-1, ridge_px=10)]
    t = sigma.sigma_table(items)
    assert t["n_matched"] == 1
    assert t["by_type"] == {}          # below MIN_PAIRS, must not be published
    assert t["pooled"]["median"] == pytest.approx(1.0)


def test_plan_grows_the_ribbon_when_sigma_is_large():
    tight = allocation.plan(sigma=0.2, dti0=0.3195, max_k=3)
    measured = allocation.plan(sigma=1.68, dti0=0.3195, max_k=3)
    very_wide = allocation.plan(sigma=4.5, dti0=0.3195, max_k=3)
    assert tight.n_lines == 1, tight
    assert tight.offsets == (0.0,)
    assert measured.n_lines == 3, measured          # the delivered geometry
    assert measured.offsets == (-3.0, 0.0, 3.0)
    assert very_wide.n_lines == 5, very_wide
    assert very_wide.offsets == (-6.0, -3.0, 0.0, 3.0, 6.0)


def test_plan_is_symmetric_about_the_ridge():
    for sig in (0.5, 1.0, 1.7, 3.0):
        pl = allocation.plan(sig, 0.2, max_k=3)
        assert sum(pl.offsets) == pytest.approx(0.0)
        assert pl.n_lines % 2 == 1


def test_plan_stops_when_the_marginal_rule_says_no():
    """A high reference score raises the bar, so fewer lines are justified."""
    lo = allocation.plan(sigma=1.7, dti0=0.0, max_k=4)
    hi = allocation.plan(sigma=1.7, dti0=5.0, max_k=4)   # absurd DTI0 -> nothing pays
    assert lo.n_lines >= hi.n_lines
    assert hi.n_lines == 1


def test_normal_credit_matches_monte_carlo():
    rng = np.random.default_rng(7)
    d = rng.normal(0.0, 1.7, size=400000)
    for mu in (0.0, 1.0, 3.0, 6.0):
        mc = float(np.maximum(0.0, 1.0 - np.abs(d - mu) / metric.RADIUS_PX).mean())
        assert allocation.normal_credit(mu, 1.7) == pytest.approx(mc, abs=2e-3)


def test_narrow_helpers_agree_with_the_exact_metric():
    """The marginal rule used by the planner is the derivative of the exact index."""
    n = 61
    truth = np.zeros((n, n), bool)
    truth[n // 2, n // 2] = True
    base = np.zeros((n, n), bool)
    base[5, 5] = True
    s = metric.dti_binary(base, truth).dti
    thr = metric.marginal_inclusion_threshold(s)
    k = allocation.normal_credit(0.0, 0.0)          # a dot exactly on the truth
    assert k == pytest.approx(1.0)
    assert k > thr


def test_dedupe_speckles_removes_touching_dots():
    m = np.zeros((7, 7), bool)
    m[3, 3] = True
    m[3, 4] = True          # touching
    m[5, 5] = True          # isolated
    out = allocation.dedupe_speckles(m, min_cluster=2)
    assert out[3, 3] == False and out[3, 4] == False  # noqa: E712
    assert out[5, 5] == True  # noqa: E712
