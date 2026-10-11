"""Cross-family structural-convergence lineament field over the pinned stack.

Physics / hypothesis
--------------------
A real fault (mapped or not) is a *planar* discontinuity.  It perturbs several
independent physical fields at once: the magnetic field (magnetite / susceptibility
contrast), the isostatic gravity field (density contrast), topography (scarp,
range front, ridge-and-valley lineament) and, where basin fill is thick, the
conductivity / depth-to-basement structure.  Single-field lineament detectors
therefore also fire on features that exist in exactly one field: aeromagnetic
flight-line levelling, roads and canals in the DEM, agricultural and regolith
texture changes, and gravity-grid interpolation artefacts.

This module computes a lineament response per (band, scale), reduces it to one
response per physical family, and then scores every pixel by **how many distinct
families independently agree** that a lineament passes through it with a
consistent strike.  That count, not the amplitude of any single band, is the
ranking statistic.  It never reads the fault catalogue, so the holdout leakage
canary in ``gems57`` stays meaningful.

Everything is computed block-wise with a halo, so peak memory is a few hundred
MB rather than the ~1 GB a whole-grid float64 stack would need.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems57.grid import HEIGHT, WIDTH

from gems59.features import gsmooth, open_stack, read_block_halo

#: Physical families.  Names are the organizer's own band prefixes; the grouping
#: is by the physics that produces the anomaly, not by the order in the file.
FAMILIES: dict[str, tuple[str, ...]] = {
    "magnetic": ("rtp", "tmi", "tmi_hg", "tmi_vg", "tc"),
    "gravity": ("iso_grav_anom", "iso_grav_anom_hg", "iso_grav_anom_vg",
                "iso_grav_anom_slope"),
    "topographic": ("det_elev", "det_elev_slope"),
    "subsurface": ("depth_to_base_surf", "cond_surf"),
}

#: Structure-tensor scales in pixels.  ``2`` is the sharpest scale that is still
#: above the 100 m grid's own smoothing; ``4`` is the fault-zone width scale.
SCALES: tuple[float, ...] = (2.0, 4.0)

#: Derivative smoothing before the tensor is formed (pixels).
DERIV_SIGMA = 1.0

HALO = 16              # >= 3 * max scale, so filters see the true neighbourhood
BLOCK_ROWS = 512


@dataclass(frozen=True)
class Convergence:
    """Ranked convergence surface plus its per-family / per-scale receipts."""

    score: np.ndarray          # float32, families agreeing (0..len(FAMILIES))
    strength: np.ndarray       # float32, best normalised lineament response
    ax: np.ndarray             # float32 across-strike unit vector (x)
    ay: np.ndarray             # float32 across-strike unit vector (y)
    fam_ix: np.ndarray         # int8  family index that won the pixel (-1 none)
    scale_ix: np.ndarray       # int8  scale index that won the pixel (-1 none)
    band_ix: np.ndarray        # int8  band index that won the pixel (-1 none)
    families: tuple[str, ...]
    scales: tuple[float, ...]
    bands: tuple[str, ...]
    agreement: np.ndarray      # float32 in [0,1]; worst pairwise strike agreement
                               # among the agreeing families (1 = parallel)


def _normalise(a: np.ndarray, valid: np.ndarray, q: float = 0.99) -> np.ndarray:
    """Divide by the ``q``-quantile of ``a`` over ``valid`` (NaN-safe)."""
    v = a[valid & np.isfinite(a)]
    if v.size == 0:
        return np.zeros_like(a, np.float32)
    ref = float(np.quantile(v, q))
    if not np.isfinite(ref) or ref <= 0:
        return np.zeros_like(a, np.float32)
    return (a / ref).astype(np.float32)


def _lineament(a: np.ndarray, scale: float) -> dict:
    """Structure-tensor lineament response of one NaN-carrying field.

    Returns ``coherence`` in [0,1], ``energy`` (tensor trace), the across-strike
    unit vector (largest-eigenvector direction, i.e. the gradient / across-strike
    direction of the linear feature) and a validity mask.
    """
    finite = np.isfinite(a)
    s = gsmooth(a, DERIV_SIGMA)
    s = np.where(np.isfinite(s), s, 0.0)
    gy, gx = np.gradient(s)
    jxx = gsmooth(gx * gx, scale)
    jyy = gsmooth(gy * gy, scale)
    jxy = gsmooth(gx * gy, scale)
    with np.errstate(invalid="ignore"):
        tr = jxx + jyy
        det = jxx * jyy - jxy * jxy
        root = np.sqrt(np.maximum(tr * tr - 4.0 * det, 0.0))
        l1 = 0.5 * (tr + root)
        l2 = 0.5 * (tr - root)
        den = l1 + l2
        coh = np.where(den > 0, (l1 - l2) / np.where(den > 0, den, 1.0), 0.0)
    # eigenvector of l1: (jxy, l1 - jxx) is orthogonal to the gradient direction
    ey = jxy
    ex = l1 - jxx
    norm = np.hypot(ex, ey)
    bad = ~np.isfinite(norm) | (norm <= 0)
    ex = np.where(bad, 1.0, ex / np.where(bad, 1.0, norm))
    ey = np.where(bad, 0.0, ey / np.where(bad, 1.0, norm))
    energy = np.where(np.isfinite(tr), tr, 0.0)
    return dict(coherence=np.clip(coh, 0.0, 1.0).astype(np.float32),
                energy=np.sqrt(np.maximum(energy, 0.0)).astype(np.float32),
                ax=ex.astype(np.float32), ay=ey.astype(np.float32),
                valid=finite)


def _response_block(blk_bands: dict[str, np.ndarray], foot: np.ndarray,
                    bands: tuple[str, ...]) -> dict:
    """Per-family response for one halo-padded block.

    ``blk_bands`` maps short band name -> 2-D float32 array with NaN outside the
    survey coverage.  Returns per-family ``score``/``strength``/``ax``/``ay``
    plus the winning (band, scale) index arrays for the receipts.
    """
    shape = next(iter(blk_bands.values())).shape
    n_fam = len(FAMILIES)
    fam_resp = np.zeros((n_fam,) + shape, np.float32)
    fam_ax = np.zeros((n_fam,) + shape, np.float32)
    fam_ay = np.zeros((n_fam,) + shape, np.float32)
    fam_band = np.full((n_fam,) + shape, -1, np.int8)
    fam_scale = np.full((n_fam,) + shape, -1, np.int8)
    fam_valid = np.zeros((n_fam,) + shape, bool)

    for fi, (fam, names) in enumerate(FAMILIES.items()):
        for si, scale in enumerate(SCALES):
            for name in names:
                bi = bands.index(name)
                a = blk_bands[name]
                if not np.isfinite(a).any():
                    continue
                r = _lineament(a, scale)
                resp = _normalise(r["coherence"] * np.sqrt(np.maximum(r["energy"], 0.0)),
                                  r["valid"])
                better = resp > fam_resp[fi]
                fam_resp[fi] = np.where(better, resp, fam_resp[fi])
                fam_ax[fi] = np.where(better, r["ax"], fam_ax[fi])
                fam_ay[fi] = np.where(better, r["ay"], fam_ay[fi])
                fam_band[fi] = np.where(better, np.int8(bi), fam_band[fi])
                fam_scale[fi] = np.where(better, np.int8(si), fam_scale[fi])
                fam_valid[fi] |= r["valid"]
        del fi
    # A family is only allowed to "vote" where it has survey coverage.
    fam_fire = fam_valid & (fam_resp >= 1.0)          # >= the 0.99 quantile of itself
    score = fam_fire.sum(axis=0).astype(np.float32)

    # strike agreement: worst pairwise |cos| angle between agreeing families
    strength = fam_resp.max(axis=0)
    best = fam_resp.argmax(axis=0)
    fam_ix = np.where(score > 0, best.astype(np.int8), np.int8(-1))
    ax = np.take_along_axis(fam_ax, best[None], axis=0)[0]
    ay = np.take_along_axis(fam_ay, best[None], axis=0)[0]
    band_ix = np.take_along_axis(fam_band, best[None], axis=0)[0]
    scale_ix = np.take_along_axis(fam_scale, best[None], axis=0)[0]

    agreement = np.ones(shape, np.float32)
    for i in range(n_fam):
        for j in range(i + 1, n_fam):
            both = fam_fire[i] & fam_fire[j]
            if not both.any():
                continue
            c = np.abs(fam_ax[i] * fam_ax[j] + fam_ay[i] * fam_ay[j])
            agreement = np.where(both, np.minimum(agreement, c), agreement)
    return dict(score=score, strength=strength, ax=ax, ay=ay, agreement=agreement,
                fam_ix=fam_ix, band_ix=band_ix, scale_ix=scale_ix)


def compute(stack, footprint: np.ndarray, writers=None) -> Convergence:
    """Full-grid convergence field from the pinned 19-band stack.

    ``writers`` optionally receives ``(r0, r1)`` in a ``mm:ss`` log line via a
    callable; it is only used for progress reporting in the CLI.
    """
    bands = tuple(stack.bands)
    shape = (HEIGHT, WIDTH)
    score = np.zeros(shape, np.float32)
    strength = np.zeros(shape, np.float32)
    ax = np.zeros(shape, np.float32)
    ay = np.zeros(shape, np.float32)
    agreement = np.zeros(shape, np.float32)
    fam_ix = np.full(shape, -1, np.int8)
    band_ix = np.full(shape, -1, np.int8)
    scale_ix = np.full(shape, -1, np.int8)

    for r0 in range(0, HEIGHT, BLOCK_ROWS):
        r1 = min(HEIGHT, r0 + BLOCK_ROWS)
        feats, top, bot = read_block_halo(stack, r0, r1, HALO)
        blk = {b: feats[i, top:bot + 0] for i, b in enumerate(bands)}
        res = _response_block(blk, footprint, bands)
        top, bot = 0, r1 - r0
        sl = (slice(top, bot), slice(0, WIDTH))
        dst = (slice(r0, r1), slice(0, WIDTH))
        for name, arr in (("score", score), ("strength", strength), ("ax", ax),
                          ("ay", ay), ("agreement", agreement), ("fam_ix", fam_ix),
                          ("band_ix", band_ix), ("scale_ix", scale_ix)):
            arr[dst] = res[name][sl]
        del res, feats, blk
        if writers is not None:
            writers(r0, r1)
    return Convergence(score=score, strength=strength, ax=ax, ay=ay, fam_ix=fam_ix,
                       scale_ix=scale_ix, band_ix=band_ix, families=tuple(FAMILIES),
                       scales=SCALES, bands=bands, agreement=agreement)


def save(conv: Convergence, path: Path) -> dict:
    """Cache the field as a compressed npz (outside git) with its receipts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path, score=conv.score, strength=conv.strength, ax=conv.ax, ay=conv.ay,
        agreement=conv.agreement, fam_ix=conv.fam_ix, band_ix=conv.band_ix,
        scale_ix=conv.scale_ix, bands=np.array(conv.bands))
    return dict(path=str(path), families=list(conv.families),
                scales=list(conv.scales), bands=list(conv.bands))


def load(path: Path) -> Convergence:
    z = np.load(path)
    return Convergence(score=z["score"], strength=z["strength"], ax=z["ax"],
                       ay=z["ay"], fam_ix=z["fam_ix"], band_ix=z["band_ix"],
                       scale_ix=z["scale_ix"], families=tuple(FAMILIES),
                       scales=SCALES, bands=tuple(str(b) for b in z["bands"]),
                       agreement=z["agreement"])
