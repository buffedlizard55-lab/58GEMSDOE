"""Cached ridge field plumbing (no feature stack required)."""

from __future__ import annotations

import numpy as np

from gems58w import extract


def test_segments_is_vectorised_and_correct():
    mag = np.zeros((20, 20), np.float32)
    mag[5:9, 5] = 2.0            # 4-px vertical ridge
    mag[15, 2:8] = 1.5           # 6-px horizontal ridge
    code = np.ones((20, 20), np.int16)
    ax = np.ones((20, 20), np.float32)
    ay = np.zeros((20, 20), np.float32)
    field = dict(mag=mag, code=code, ax=ax, ay=ay,
                 codes=[dict(band="tmi", scale=3.0, sign=-1, q=1.0)])
    segs = extract.segments(field, 1.0, min_px=4)
    sizes = sorted(s["size"] for s in segs)
    assert sizes == [4, 6], sizes
    segs2 = extract.segments(field, 1.8, min_px=4)
    assert [s["size"] for s in segs2] == [4]


def test_segments_drops_short_components():
    mag = np.zeros((10, 10), np.float32)
    mag[1, 1:4] = 5.0
    field = dict(mag=mag, code=np.ones((10, 10), np.int16),
                 ax=np.ones((10, 10), np.float32), ay=np.zeros((10, 10), np.float32),
                 codes=[dict(band="tmi", scale=3.0, sign=1, q=1.0)])
    assert extract.segments(field, 1.0, min_px=8) == []
