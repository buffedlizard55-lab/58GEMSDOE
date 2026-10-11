"""Access to the official 19-band GeoDAWN numerical feature stack.

The stack is the organizer's own ``training_features.tif`` (name in the
DrivenData data tab) mirrored under its published filename
``gems-geodawn-numerical-features.tif``.  It is 418,912,844 bytes and is *not*
committed; ``scripts/fetch_features.sh`` restores it and verifies

    sha256 = 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5

against the pin recorded in the bridge manifest at
https://github.com/buffedlizard55-lab/5GEMSDOE/blob/main/data/bridge/manifest.json

Band order and meaning are read from the file's own band descriptions (see
``band_table()``); they are the organizer's, not an inference.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import rasterio

from .paths import feature_stack

#: Canonical band order of the stack, from the file's TIFF band descriptions.
BANDS = (
    "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
    "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15",
    "iso_grav_anom_vg", "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf",
    "ieq_n100a15", "cond_surf", "iso_grav_anom_hg", "det_elev_slope",
)

#: Grouping used for the "ridge type" stratum.  Families are the organizer's own
#: ``data_category`` tags on the bands.
FAMILIES = {
    "magnetic": ("mag_anom", "rtp", "tmi_hg", "tmi_vg", "tc", "tmi"),
    "gravity": ("iso_grav_anom", "iso_grav_anom_hg", "iso_grav_anom_vg", "iso_grav_anom_slope"),
    "topographic": ("det_elev", "det_elev_slope"),
    "subsurface": ("depth_to_base_surf", "cond_surf"),
    "geodetic": ("geod_2ndinv", "geod_shearrate", "geod_dilaterate"),
    "seismic": ("deq_n100a15", "ieq_n100a15"),
}


@lru_cache(maxsize=1)
def profile() -> dict:
    p = feature_stack()
    if not p.exists():
        raise FileNotFoundError(
            f"feature stack not found at {p}; run: bash scripts/fetch_features.sh"
        )
    with rasterio.open(p) as s:
        desc = [d for d in s.descriptions]
        return dict(path=str(p), shape=(s.height, s.width), count=s.count,
                    crs=str(s.crs), transform=tuple(s.transform)[:6],
                    descriptions=desc, nodata=s.nodata)


def band_index(name: str) -> int:
    if name not in BANDS:
        raise KeyError(f"unknown band {name!r}; known: {BANDS}")
    return BANDS.index(name) + 1


@lru_cache(maxsize=8)
def band(name: str) -> np.ndarray:
    """Read one band as float32 with the stack's nodata (-3.4e38) mapped to NaN."""
    p = feature_stack()
    with rasterio.open(p) as s:
        a = s.read(band_index(name)).astype(np.float32)
        nod = s.nodata
    if nod is not None:
        a = np.where(np.abs(a - np.float32(nod)) < 1e-30, np.nan, a).astype(np.float32)
    return a


def band_table() -> list[dict]:
    """Human-auditable table of band index, name, category and description."""
    p = profile()
    with rasterio.open(feature_stack()) as s:
        rows = []
        for i in range(1, s.count + 1):
            t = s.tags(i)
            rows.append(dict(index=i, band_name=t.get("band_name", s.descriptions[i - 1]),
                             data_category=t.get("data_category", ""),
                             description=t.get("description", "")))
    return rows


def usable_bands() -> tuple[str, ...]:
    """Bands with a finite in-footprint spread; the rest are constants for this extent."""
    from .grid import footprint

    fp = footprint()
    keep = []
    for name in BANDS:
        a = band(name)
        v = a[fp & np.isfinite(a)]
        if v.size and float(np.nanstd(v)) > 0.0:
            keep.append(name)
    return tuple(keep)
