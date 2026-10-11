"""Buffered hide-and-recover holdout for the ribbon lane.

Protocol ``gems58-pooled-hide-v1`` (fixed before the first measurement, see
``evidence/holdout_protocol.json``):

1. The mapped catalogue (``data/official/existing_faults.tif``, 60,988 px,
   3,199 components) is split into 8-connected components --- whole fault
   segments.  Every component, including the 201 specks below 4 px, is
   assigned to exactly one fold, so the partition covers all 60,988 px.
2. Components are assigned to four spatial blocks by centroid quadrant
   (``NW``, ``NE``, ``SW``, ``SE``).  Block ``k`` is withheld in turn.
3. **Withheld truth** = the actual pixels of the withheld components.
   **Visible catalogue** = every other component.
4. **Buffer.**  The prediction domain excludes a ``BUFFER_PX``-pixel collar
   around the *visible* catalogue.  A collar around the visible faults is
   removed pixel-exactly (``known``), so a prediction placed on or beside a
   visible fault earns nothing; the withheld pixels themselves stay scoreable.
5. Catalogue-based features are derived only from the visible faults: this lane
   uses **no** catalogue-based feature at all (the ridge field is read from the
   organizer's geophysical stack), so the requirement is met by construction and
   is asserted by ``tests/test_holdout.py``.
6. Score = pooled exact DTI (``metric.dti_binary``), ``alpha = 0.2``,
   ``beta = 0.8``, 300 m triangular kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.ndimage import binary_dilation, label

from . import grid

BUFFER_PX: int = 3
BLOCKS: tuple[str, ...] = ("NW", "NE", "SW", "SE")
PROTOCOL: str = "gems58-pooled-hide-v1"
EVALUATOR: str = "gems58w.metric/v1"


@dataclass(frozen=True)
class Fold:
    name: str
    withhold: np.ndarray     # bool: withheld truth pixels
    visible: np.ndarray      # bool: visible catalogue pixels
    known: np.ndarray        # bool: masked from prediction (visible + buffer)
    valid: np.ndarray        # bool: scoreable domain (footprint)
    n_truth: int


def _block_of(centroid_rc: tuple[float, float], shape: tuple[int, int]) -> str:
    r, c = centroid_rc
    rows, cols = shape
    south = r >= rows / 2.0
    west = c < cols / 2.0
    return ("N" if not south else "S") + ("W" if west else "E")


@lru_cache(maxsize=4)
def _components(min_px: int) -> tuple[tuple[np.ndarray, str], ...]:
    """(index array, block) per catalogue component, grouped once and cached.

    The catalogue holds 3,199 8-connected components; a per-component
    ``lab == i`` scan over the full raster is O(components x pixels) and took
    ~100 s per fold construction, so the grouping is done once with a single
    ``argsort`` over the non-zero labels instead.
    """
    cat = grid.catalogue()
    lab, _ = label(cat, structure=np.ones((3, 3), int))
    nz = np.flatnonzero(lab)
    order = np.argsort(lab.ravel()[nz], kind="stable")
    nz = nz[order]
    lab_sorted = lab.ravel()[nz]
    counts = np.bincount(lab_sorted)
    offsets = np.cumsum(counts)          # offsets[k] = pixels with label <= k
    out = []
    for lab_id in range(1, counts.size):
        lo, hi = offsets[lab_id - 1], offsets[lab_id]
        if hi - lo < min_px:
            continue
        idx = np.stack(np.unravel_index(nz[lo:hi], cat.shape), axis=1)
        out.append((idx, _block_of(idx.mean(axis=0), cat.shape)))
    return tuple(out)


def block_of(rc) -> str:
    """Spatial block (``NW``/``NE``/``SW``/``SE``) of a (row, col) point or centroid."""
    return _block_of(tuple(float(v) for v in rc), grid.catalogue().shape)


def catalogue_components(min_px: int = 1) -> tuple[np.ndarray, list[np.ndarray], list[str]]:
    """8-connected components of the catalogue with their centroid blocks.

    ``min_px = 1`` by default: the fold partition must cover *every* catalogue
    pixel (201 of the 3,199 components are 1-3 px wide, 514 px in total), so
    nothing is silently dropped from the withheld truth.
    """
    lab, n = label(grid.catalogue(), structure=np.ones((3, 3), int))
    grouped = _components(int(min_px))
    return lab, [idx for idx, _ in grouped], [b for _, b in grouped]


@lru_cache(maxsize=8)
def _folds_cached(block: str | None) -> tuple[Fold, ...]:
    cat = grid.catalogue()
    fp = grid.footprint()
    struct = np.ones((2 * BUFFER_PX + 1,) * 2, bool)
    comps = _components(1)
    out = []
    for b in BLOCKS:
        if block is not None and b != block:
            continue
        withheld_mask = np.zeros(cat.shape, bool)
        visible = np.zeros(cat.shape, bool)
        for idx, cb in comps:
            tgt = withheld_mask if cb == b else visible
            tgt[idx[:, 0], idx[:, 1]] = True
        known = binary_dilation(visible, struct)
        out.append(Fold(name=b, withhold=withheld_mask, visible=visible, known=known,
                        valid=fp, n_truth=int(withheld_mask.sum())))
    return tuple(out)


def folds(block: str | None = None) -> list[Fold]:
    """The four spatial folds (or one named fold); cached after the first build."""
    return list(_folds_cached(block))


def all_folds() -> list[Fold]:
    return folds(None)


# --------------------------------------------------------------------------
# across-strike localisation measurement
# --------------------------------------------------------------------------


def component_strike(idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Principal-axis strike and normal unit vectors of a pixel index array (r, c)."""
    p = idx.astype(np.float64)
    p = p - p.mean(axis=0)
    cov = p.T @ p / max(len(p) - 1, 1)
    w, v = np.linalg.eigh(cov)
    u = v[:, -1]        # along strike (largest variance)
    n = v[:, 0]         # across strike
    return u, n


def signed_offset(points_rc: np.ndarray, ref_idx: np.ndarray,
                  u: np.ndarray, n: np.ndarray) -> np.ndarray:
    """Signed across-strike offset of ``points_rc`` from the axis of ``ref_idx``."""
    ref = ref_idx.astype(np.float64)
    c = ref.mean(axis=0)
    return (points_rc.astype(np.float64) - c) @ n


def angle_between(a: np.ndarray, b: np.ndarray) -> float:
    """Acute angle in degrees between two undirected axis vectors."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    c = abs(float(np.dot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
    return float(np.degrees(np.arccos(np.clip(c, 0.0, 1.0))))
