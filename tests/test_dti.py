"""Unit tests: fast DTI == brute-force DTI on random small grids; closed form identity holds."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems58.dti import dti_binary, dti_bruteforce  # noqa: E402


def test_fast_matches_bruteforce():
    rng = np.random.default_rng(0)
    for _ in range(5):
        truth = rng.random((30, 30)) < 0.05
        pred = rng.random((30, 30)) < 0.15
        a = dti_binary(pred, truth)
        b = dti_bruteforce(pred.astype(float), truth)
        assert abs(a["tp"] - b["tp"]) < 1e-6, (a, b)
        assert abs(a["fp"] - b["fp"]) < 1e-6, (a, b)
        assert abs(a["dti"] - b["dti"]) < 1e-9, (a, b)


def test_closed_form_identity():
    rng = np.random.default_rng(1)
    truth = rng.random((40, 40)) < 0.06
    pred = rng.random((40, 40)) < 0.2
    r = dti_binary(pred, truth)
    G = r["n_truth"]
    closed = r["tp"] / (0.2 * (r["tp"] + r["fp"]) + 0.8 * G)
    assert abs(closed - r["dti"]) < 1e-9


def test_known_mask_excludes_both_sides():
    truth = np.zeros((10, 10), bool)
    truth[5, 5] = True
    pred = np.zeros((10, 10), bool)
    pred[5, 5] = True
    known = np.zeros((10, 10), bool)
    known[5, 5] = True
    r = dti_binary(pred, truth, known=known)
    assert r["n_truth"] == 0 and r["tp"] == 0.0


def test_components_match_binary():
    from gems58.dti import dti_components
    rng = np.random.default_rng(2)
    truth = rng.random((50, 50)) < 0.05
    pred = rng.random((50, 50)) < 0.12
    known = rng.random((50, 50)) < 0.05
    tpm, fpm, g, s = dti_components(pred, truth, known=known)
    b = dti_binary(pred, truth, known=known)
    assert abs(s["tp"] - b["tp"]) < 1e-6 and abs(s["fp"] - b["fp"]) < 1e-6 and abs(s["dti"] - b["dti"]) < 1e-9
    assert abs(tpm.sum() - b["tp"]) < 1e-6


if __name__ == "__main__":
    test_fast_matches_bruteforce()
    test_closed_form_identity()
    test_known_mask_excludes_both_sides()
    test_components_match_binary()
    print("dti tests passed")
