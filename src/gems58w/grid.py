"""The official scoring surface: grid, footprint, catalogue mask, exact DTI.

Everything here is derived from the pinned official rasters
(``data/official/*.tif``); provenance and sha256 pins are in ``data/README.md``.

Official geometry (read from ``sample_submission.tif``):

* 3730 x 3292 pixels, ``EPSG:32611`` (WGS 84 / UTM zone 11N), 100 m pixels
* geotransform ``(100, 0, 243350, 0, -100, 4508550)``
* nodata = NaN *outside* the competition footprint
* the footprint is exactly the finite support of the example submission:
  5,167,373 pixels
* ``existing_faults.tif`` (== ``labels.tif``, byte-identical) carries the
  60,988 mapped USGS/INGENIOUS catalogue pixels, coded ``1``; ``-1`` outside.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import rasterio

from .paths import OFFICIAL

NODATA_OUTSIDE = np.nan


@dataclass(frozen=True)
class Grid:
    height: int
    width: int
    crs: str
    transform: tuple
    shape: tuple

    @property
    def n_cells(self) -> int:
        return self.height * self.width


@lru_cache(maxsize=1)
def grid() -> Grid:
    with rasterio.open(OFFICIAL / "sample_submission.tif") as s:
        return Grid(s.height, s.width, str(s.crs), tuple(s.transform)[:6], (s.height, s.width))


@lru_cache(maxsize=1)
def footprint() -> np.ndarray:
    """Boolean mask: True inside the competition footprint (finite in the template)."""
    with rasterio.open(OFFICIAL / "sample_submission.tif") as s:
        a = s.read(1)
    return np.isfinite(a)


@lru_cache(maxsize=1)
def catalogue() -> np.ndarray:
    """Boolean mask of the mapped USGS/INGENIOUS fault catalogue (60,988 pixels)."""
    with rasterio.open(OFFICIAL / "existing_faults.tif") as s:
        a = s.read(1)
    return a > 0


@lru_cache(maxsize=1)
def catalogue_labels() -> np.ndarray:
    """The raw int8 catalogue raster (``1`` on catalogue, ``0`` in domain, ``-1`` outside)."""
    with rasterio.open(OFFICIAL / "existing_faults.tif") as s:
        return s.read(1)


def scored_domain() -> np.ndarray:
    """Pixels the organizer scores: inside the footprint and not on the catalogue.

    The catalogue is removed from both the prediction and the truth before the
    kernel is applied (organizer clarification, community thread 11516), so a
    prediction on a known fault is inert and cannot radiate credit.
    """
    return footprint() & ~catalogue()


def project_root_catalogue_count() -> int:
    return int(catalogue().sum())
