"""Extended evidence layers on the study grid (organizer stack + owner-published mirrors).

Provenance, stated exactly
--------------------------
1. **Organizer stack** -- ``training_features.tif`` (19 bands), restored by
   ``scripts/ribbon_fetch_features.sh`` from the five-part public bridge and
   verified against sha256
   ``4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5``.
   Band order and meaning are read from the file's own band descriptions.
2. **Owner-published mirrors** -- under ``~/.cache/gems58/src60/data`` (restored
   by ``scripts/gems61_fetch_extended.sh`` from the public repository
   ``buffedlizard55-lab/60GEMSDOE``, commit-verified by sparse clone):

   ============================ ==========================================
   file                         bands
   ============================ ==========================================
   ``external/geodawn_rad_u8.tif``        K, Th, U, TC
   ``external/geodawn_extensions_u8.tif`` ThK, UK, UTh, TMI_up150
   ``external/lidar_scarp_features_u8.tif`` ex_max, ex_mean, step_max,
                                          lapneg_max, lappos_max,
                                          downface_max, upface_max,
                                          cross_max, relief, coh100,
                                          strike, valid
   ``geodawn_dem_a2_100m.tif``            elevation (float32, -999999 nodata)
   ``external/dem10_chi_100m_u8.tif``     chan_n, knick_n, raised_n, valid_n
   ============================ ==========================================

   These mirrors are 8-bit encodings.  **The scaling from physical units to
   uint8 is not published in this checkout**, so they are used *ordinal-only*:
   :func:`band` rank-transforms them inside the footprint before any derivative
   is taken, which is invariant to any unknown monotone encoding.  Radiometric
   and lidar values are therefore never interpreted as physical units and never
   quoted as such.  Their origin is the USGS/DOE GeoDAWN acquisition that the
   organizers describe on the competition problem page; the bytes here come from
   the owner's mirror, which authenticates the *transport*, not the origin.

Nothing in this module reads ``data/official/labels.tif``: the layer set is
catalogue-free by construction, which is what makes the hide-and-recover
measurement in :mod:`gems61.lane` leakage-free.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import rasterio

from gems58w import features as O19
from gems58w.paths import cache_dir

#: Extra 8-bit bands (ordinal-only), grouped into families.
MIRROR_BANDS: dict[str, tuple[str, int]] = {
    # name -> (file, band index 1-based)
    "rad_K": ("external/geodawn_rad_u8.tif", 1),
    "rad_Th": ("external/geodawn_rad_u8.tif", 2),
    "rad_U": ("external/geodawn_rad_u8.tif", 3),
    "rad_TC": ("external/geodawn_rad_u8.tif", 4),
    "ext_ThK": ("external/geodawn_extensions_u8.tif", 1),
    "ext_UK": ("external/geodawn_extensions_u8.tif", 2),
    "ext_UTh": ("external/geodawn_extensions_u8.tif", 3),
    "lid_ex_max": ("external/lidar_scarp_features_u8.tif", 1),
    "lid_step_max": ("external/lidar_scarp_features_u8.tif", 3),
    "lid_lapneg_max": ("external/lidar_scarp_features_u8.tif", 4),
    "lid_lappos_max": ("external/lidar_scarp_features_u8.tif", 5),
    "lid_downface_max": ("external/lidar_scarp_features_u8.tif", 6),
    "lid_upface_max": ("external/lidar_scarp_features_u8.tif", 7),
    "lid_cross_max": ("external/lidar_scarp_features_u8.tif", 8),
    "lid_relief": ("external/lidar_scarp_features_u8.tif", 9),
    "dem10_chan": ("external/dem10_chi_100m_u8.tif", 1),
    "dem10_knick": ("external/dem10_chi_100m_u8.tif", 2),
    "dem10_raised": ("external/dem10_chi_100m_u8.tif", 3),
}

#: Families used as the "ridge type" stratum.  ``lidar`` and ``radiometric`` are the
#: new ones; the rest are the organizer's own ``data_category`` tags.
EXT_FAMILIES: dict[str, tuple[str, ...]] = {
    "magnetic": ("mag_anom", "rtp", "tmi_hg", "tmi_vg", "tc", "tmi"),
    "gravity": ("iso_grav_anom", "iso_grav_anom_hg", "iso_grav_anom_vg", "iso_grav_anom_slope"),
    "topographic": ("det_elev", "det_elev_slope", "dem100"),
    "subsurface": ("depth_to_base_surf", "cond_surf"),
    "geodetic": ("geod_2ndinv", "geod_shearrate", "geod_dilaterate"),
    "seismic": ("deq_n100a15", "ieq_n100a15"),
    "radiometric": ("rad_K", "rad_Th", "rad_U", "rad_TC", "ext_ThK", "ext_UK", "ext_UTh"),
    "lidar": ("lid_ex_max", "lid_step_max", "lid_lapneg_max", "lid_lappos_max",
              "lid_downface_max", "lid_upface_max", "lid_cross_max", "lid_relief"),
    "channel": ("dem10_chan", "dem10_knick", "dem10_raised"),
}

#: Band list the ridge field is built from (families above, in order).
EXT_BANDS: tuple[str, ...] = tuple(b for f in EXT_FAMILIES.values() for b in f)

#: Extra bands are high-resolution morphology/DEM products, so they are resolved at
#: the two finer scales; the organizer bands keep the original three.
SCALES_EXT: tuple[float, ...] = (1.5, 3.0)
SCALES_O19: tuple[float, ...] = (1.5, 3.0, 6.0)


def family_of(band: str) -> str:
    for fam, bands in EXT_FAMILIES.items():
        if band in bands:
            return fam
    return "other"


def mirror_root() -> Path:
    """Directory holding the owner-published mirrors (outside git).

    Resolved from ``GEMS61_MIRRORS`` when set, else ``<cache>/src60/data``, where
    ``<cache>`` is the lane cache directory (``.cache/gems58`` by default).  The
    restore script ``scripts/gems61_fetch_extended.sh`` writes exactly there.
    """
    import os

    env = os.environ.get("GEMS61_MIRRORS")
    if env:
        return Path(env).expanduser()
    return cache_dir() / "src60" / "data"


@lru_cache(maxsize=1)
def _footprint() -> np.ndarray:
    from gems57.grid import load_grid
    from pathlib import Path as _P

    root = _P(__file__).resolve().parents[2]
    return load_grid(root / "data" / "bridge").footprint


@lru_cache(maxsize=32)
def _raw(band: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (values float32, valid bool) for one extended band, unranked."""
    fp = _footprint()
    demp = mirror_root() / "geodawn_dem_a2_100m.tif"
    if band == "dem100":
        if not demp.exists():
            raise FileNotFoundError(f"{demp} missing; run scripts/gems61_fetch_extended.sh")
        with rasterio.open(demp) as src:
            a = src.read(1).astype(np.float32)
            nod = src.nodata
        v = np.isfinite(a) & fp
        if nod is not None:
            v &= a != np.float32(nod)
        return a, v
    if band in MIRROR_BANDS:
        rel, idx = MIRROR_BANDS[band]
        p = mirror_root() / rel
        if not p.exists():
            raise FileNotFoundError(f"{p} missing; run scripts/gems61_fetch_extended.sh")
        with rasterio.open(p) as src:
            a = src.read(idx).astype(np.float32)
        # uint8 mirrors use 0 as nodata/background
        return a, fp & (a > 0)
    return O19.band(band), fp


def band(name: str) -> np.ndarray:
    """One extended band as an ordinal float32 field, NaN outside its valid area.

    Ordinal rank transform inside the valid mask: invariant to any unknown
    monotone uint8 encoding, and identical to the raw values when the band is
    already continuous (organizer bands are left untouched).
    """
    a, valid = _raw(name)
    if name in MIRROR_BANDS:
        out = np.full(a.shape, np.nan, np.float32)
        v = a[valid]
        if v.size == 0:
            return out
        order = np.argsort(v, kind="stable")
        ranks = np.empty(v.size, np.float64)
        ranks[order] = np.linspace(0.0, 1.0, v.size)
        out[valid] = ranks.astype(np.float32)
        return out
    return np.where(valid, a, np.nan).astype(np.float32)


def inventory() -> list[dict]:
    """Audit table of the extended layer set with per-band valid-pixel counts."""
    rows = []
    for name in EXT_BANDS:
        a = band(name)
        rows.append(dict(band=name, family=family_of(name),
                         valid_px=int(np.isfinite(a).sum()),
                         ordinal_only=name in MIRROR_BANDS))
    return rows
