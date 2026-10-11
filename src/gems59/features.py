"""Block-wise feature stack over the pinned official ``training_features.tif``.

Provenance (verified this session, no inference)
------------------------------------------------
The 19-band feature stack is the competition's ``training_features.tif``.  It is
not downloadable from this sandbox (the DrivenData data tab needs a login), but
it *is* published, sha256-pinned, inside the owner's ``GEMSDOE`` repository as a
five-part git bridge:

* manifest: ``GEMSDOE:data/bridge/manifest.json``
  (https://github.com/buffedlizard55-lab/GEMSDOE/blob/main/data/bridge/manifest.json)
* reassembly contract: ``GEMSDOE:scripts/assemble_data_bridge.py``
* whole-file pin: ``4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5``
  (418,912,844 bytes, canonical name ``training_features.tif``)

``scripts/fetch_feature_stack.sh`` reproduces the file here and verifies every
part pin *and* the whole-file pin before anything downstream reads it.

Grid contract
-------------
EPSG:32611, 3730 x 3292, transform (100, 0, 243350, 0, -100, 4508550) -- the same
six numbers ``gems57.grid`` pins from the two small bridge rasters.  This module
re-checks them at load time and refuses to proceed on a mismatch.

Feature families
----------------
Only geophysical operators are computed here.  **No feature in this module sees
the fault catalogue**, which is what keeps the leakage canary meaningful: any
catalogue-derived context is added explicitly by the caller and must be canaried
separately (parallel-run protocol rule 4).

* ``raw/<band>``            -- the 19 published GeoDAWN bands, unmodified.
* ``coh_s1/<field>``        -- structure-tensor coherence ((l1-l2)/(l1+l2))^2 at
                               sigma = 1 px.  High on locally linear structures;
                               the classical lineament detector (Frohlich &
                               Schilling; Forstner/Rohr operator).
* ``coh_s3/<field>``        -- the same at sigma = 3 px (the 300 m kernel scale).
* ``std3/<band>``, ``std7/<band>`` -- local standard deviation (texture).
* ``lap/<field>``           -- Laplacian (profile curvature).

Structure-tensor fields: ``rtp``, ``tmi``, ``iso_grav_anom``, ``det_elev``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57.grid import EPSG, HEIGHT, TRANSFORM, WIDTH

STACK_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
STACK_BYTES = 418_912_844
DEFAULT_STACK = Path.home() / ".cache" / "gems" / "training_features.tif"

# structure-tensor source fields, by band description prefix
COH_S1 = ("rtp", "tmi", "iso_grav_anom", "det_elev")
COH_S3 = ("rtp", "det_elev")
STD3 = ("rtp", "tmi", "det_elev", "iso_grav_anom", "tmi_hg", "iso_grav_anom_hg")
STD7 = ("rtp", "det_elev")
LAP = ("det_elev", "iso_grav_anom")

BLOCK_ROWS = 384
HALO = 24          # >= total filter radius: gsmooth(1)=4 + gradient=1 + gsmooth(3)=12


@dataclass(frozen=True)
class Stack:
    path: Path
    bands: tuple[str, ...]          # 19 short band names
    names: tuple[str, ...]          # full feature index (raw + derived)
    nodata: float

    @property
    def n_raw(self) -> int:
        return len(self.bands)

    def index(self, name: str) -> int:
        return self.names.index(name)


def open_stack(path: Path | None = None) -> Stack:
    """Open the pinned stack and verify its grid against ``gems57.grid``."""
    p = Path(path) if path else DEFAULT_STACK
    if not p.is_file():
        raise FileNotFoundError(
            f"feature stack not found at {p}; run scripts/fetch_feature_stack.sh")
    if p.stat().st_size != STACK_BYTES:
        raise ValueError(f"{p} is {p.stat().st_size} B, expected {STACK_BYTES} B "
                         "(run scripts/fetch_feature_stack.sh to re-verify)")
    with rasterio.open(p) as src:
        if str(src.crs) != f"EPSG:{EPSG}":
            raise ValueError(f"stack CRS {src.crs} != EPSG:{EPSG}")
        if (src.height, src.width) != (HEIGHT, WIDTH):
            raise ValueError(f"stack shape {src.height}x{src.width} != {HEIGHT}x{WIDTH}")
        if tuple(src.transform)[:6] != tuple(TRANSFORM)[:6]:
            raise ValueError(f"stack transform {tuple(src.transform)} != {tuple(TRANSFORM)[:6]}")
        if src.count != 19:
            raise ValueError(f"stack has {src.count} bands, expected 19")
        bands = tuple((d or f"band{i+1}").split(" - ")[0].strip()
                      for i, d in enumerate(src.descriptions))
        nodata = float(src.nodatavals[0])
    names = [f"raw/{b}" for b in bands]
    names += [f"coh_s1/{f}" for f in COH_S1]
    names += [f"coh_s3/{f}" for f in COH_S3]
    names += [f"std3/{b}" for b in STD3]
    names += [f"std7/{b}" for b in STD7]
    names += [f"lap/{f}" for f in LAP]
    return Stack(path=p, bands=bands, names=tuple(names), nodata=nodata)


def read_block(stack: Stack, r0: int, r1: int) -> np.ndarray:
    """Read rows ``[r0, r1)`` of all 19 bands as float32 with the nodata -> NaN map."""
    with rasterio.open(stack.path) as src:
        blk = src.read(window=rasterio.windows.Window(0, r0, WIDTH, r1 - r0))
    blk = blk.astype(np.float32, copy=False)
    blk[blk == np.float32(stack.nodata)] = np.float32("nan")
    return blk


def _gsmooth(a: np.ndarray, sigma: float) -> np.ndarray:
    """NaN-aware Gaussian smoothing: ``G(a*w) / G(w)`` with ``w = isfinite(a)``.

    ``scipy.ndimage.gaussian_filter`` and ``uniform_filter`` both let a single
    NaN poison a whole line of output (their 1-D passes are recursive/sliding),
    which silently destroyed every texture feature over the study area.  The
    weighted form below is the standard local-mean estimator and returns a
    finite value wherever the window holds at least one valid pixel.
    """
    w = np.isfinite(a)
    z = np.where(w, a, 0.0)
    num = ndi.gaussian_filter(z, sigma, mode="nearest")
    den = ndi.gaussian_filter(w.astype(np.float64), sigma, mode="nearest")
    out = np.full(a.shape, np.nan)
    ok = den > 1e-6
    out[ok] = num[ok] / den[ok]
    return out


def _lmean_var(a: np.ndarray, size: int) -> tuple[np.ndarray, np.ndarray]:
    """NaN-aware local mean and variance over a ``size`` x ``size`` box."""
    w = np.isfinite(a).astype(np.float64)
    z = np.where(w > 0, a, 0.0)
    sw = ndi.uniform_filter(w, size, mode="nearest")
    s1 = ndi.uniform_filter(z, size, mode="nearest")
    s2 = ndi.uniform_filter(z * z, size, mode="nearest")
    mean = np.full(a.shape, np.nan)
    var = np.full(a.shape, np.nan)
    ok = sw > 1e-6
    mean[ok] = s1[ok] / sw[ok]
    var[ok] = np.maximum(s2[ok] / sw[ok] - mean[ok] ** 2, 0.0)
    return mean, var


def _coh(a: np.ndarray, sigma: float) -> np.ndarray:
    """Structure-tensor coherence ((l1-l2)/(l1+l2))^2 of a 2-D field.

    Derivatives are taken on the validity-weighted smoothed field, and the
    tensor itself is smoothed with :func:`_gsmooth`, so no NaN can leak outside
    its own neighbourhood.  Output is NaN exactly where the input is NaN.
    """
    valid = np.isfinite(a)
    s = _gsmooth(a, 1.0)
    s = np.where(np.isfinite(s), s, 0.0)
    gy, gx = np.gradient(s)
    jxx = _gsmooth(gx * gx, sigma)
    jyy = _gsmooth(gy * gy, sigma)
    jxy = _gsmooth(gx * gy, sigma)
    with np.errstate(invalid="ignore"):
        tr = jxx + jyy
        det = jxx * jyy - jxy * jxy
        root = np.sqrt(np.maximum(tr * tr - 4.0 * det, 0.0))
        l1 = 0.5 * (tr + root)
        l2 = 0.5 * (tr - root)
        denom = l1 + l2
        out = np.where((denom > 0) & np.isfinite(denom),
                       ((l1 - l2) / np.where(denom > 0, denom, 1.0)) ** 2, np.nan)
    return np.where(valid, out, np.nan).astype(np.float32)


def read_block_halo(stack: Stack, r0: int, r1: int, halo: int) -> tuple[np.ndarray, int, int]:
    """Read rows ``[r0 - halo, r1 + halo)`` clipped to the grid.

    Returns ``(block, top, bot)`` where ``block`` covers the padded window and
    the caller keeps ``block[:, top:bot, :]`` to recover rows ``[r0, r1)`` after
    running neighbourhood filters on the padded window.  Added for the session-5
    convergence lane so it reuses this module's verified stack reader instead of
    forking a second one.
    """
    if halo < 0:
        raise ValueError('halo must be non-negative')
    h0, h1 = max(0, r0 - halo), min(HEIGHT, r1 + halo)
    return read_block(stack, h0, h1), r0 - h0, h1 - h0 - (h1 - r1)


#: Public alias of the NaN-aware smoother, so lanes outside this module do not
#: have to import a private name (parallel-run protocol: no private forks).
gsmooth = _gsmooth


def compute_block(stack: Stack, blk: np.ndarray, band_ix: dict[str, int]) -> np.ndarray:
    """Derive the non-raw features for one (halo-padded) block.

    Returns an array of shape ``(n_derived, rows, cols)``.  Every operator is
    NaN-aware: the stack's nodata mask covers the cells outside the study-area
    footprint (verified against ``sample_submission.tif`` -- 4,601 mismatched
    cells out of 12,279,160, i.e. 0.037%), and those NaN must not contaminate
    valid pixels more than one filter radius away.
    """
    out = []
    a = blk.astype(np.float64)
    for f in COH_S1:
        out.append(_coh(a[band_ix[f]], 1.0))
    for f in COH_S3:
        out.append(_coh(a[band_ix[f]], 3.0))
    for b in STD3:
        _, var = _lmean_var(a[band_ix[b]], 3)
        out.append(np.sqrt(var).astype(np.float32))
    for b in STD7:
        _, var = _lmean_var(a[band_ix[b]], 7)
        out.append(np.sqrt(var).astype(np.float32))
    for f in LAP:
        x = a[band_ix[f]]
        z = np.where(np.isfinite(x), x, 0.0)
        w = np.isfinite(x).astype(np.float64)
        lap = ndi.laplace(z, mode="nearest")
        # de-bias the Laplacian for missing neighbours so the footprint edge does
        # not show up as a spurious curvature line
        kern = ndi.laplace(w, mode="nearest")
        out.append(np.where(w > 0, lap / np.where(w > 0, 1.0 - kern / 4.0, 1.0),
                            np.nan).astype(np.float32))
    return np.stack(out, axis=0)


def iter_blocks(stack: Stack, block_rows: int = BLOCK_ROWS):
    """Yield ``(r0, r1, features)`` with ``features`` shape ``(n_features, r1-r0, W)``.

    Each block is computed from a halo-padded read, so the filters see the same
    neighbourhood they would on the full grid; the halo is trimmed before yield.
    """
    band_ix = {b: i for i, b in enumerate(stack.bands)}
    n_der = len(stack.names) - len(stack.bands)
    for r0 in range(0, HEIGHT, block_rows):
        r1 = min(HEIGHT, r0 + block_rows)
        h0, h1 = max(0, r0 - HALO), min(HEIGHT, r1 + HALO)
        blk = read_block(stack, h0, h1)
        der = compute_block(stack, blk, band_ix)
        top, bot = r0 - h0, h1 - h0 - (h1 - r1)
        keep = (slice(top, bot), slice(0, WIDTH))
        feats = np.empty((len(stack.names), r1 - r0, WIDTH), np.float32)
        feats[: len(stack.bands)] = blk[:, top:bot, :]
        feats[len(stack.bands):] = der[(slice(None),) + keep]
        yield r0, r1, feats


def gather_pixels(stack: Stack, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    """Feature rows for arbitrary pixel coordinates, block-wise and memory-safe.

    ``ys``/``xs`` need not be sorted.  Returns ``(len(ys), n_features)`` float32.
    """
    ys = np.asarray(ys, np.int64)
    xs = np.asarray(xs, np.int64)
    if ys.shape != xs.shape:
        raise ValueError("ys and xs must have the same shape")
    out = np.full((ys.size, len(stack.names)), np.nan, np.float32)
    order = np.argsort(ys, kind="stable")
    ys_s, xs_s = ys[order], xs[order]
    pos = 0
    for r0, r1, feats in iter_blocks(stack):
        lo = np.searchsorted(ys_s, r0, side="left")
        hi = np.searchsorted(ys_s, r1, side="left")
        if lo == hi:
            continue
        block_pos = order[lo:hi]
        out[block_pos, :] = feats[:, ys_s[lo:hi] - r0, xs_s[lo:hi]].T
        pos = hi
    if pos != ys.size:
        raise RuntimeError(f"gathered {pos}/{ys.size} pixels; row indices out of range")
    return out


def names_json(stack: Stack) -> str:
    return json.dumps(list(stack.names), indent=0)
