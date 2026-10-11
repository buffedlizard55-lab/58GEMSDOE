"""Uniqueness screen against every accessible earlier raster.

Statistics, exactly as the parallel-run protocol defines them:

* **rank correlation** of the two full-footprint value fields (Spearman; ties by
  average ranks).  Triggers at ``> RHO_MAX``.
* **forward overlap**: the fraction of *this lane's* dots that fall within 3 px
  (300 m) of any dot of the registry raster.  Triggers at ``> OVERLAP_MAX``.

.. warning:: direction bug, fixed 2026-10-11 (IR-58-UNIQ-04)

   The previous revision of this module computed ``forward_overlap`` as
   ``(distance_transform_edt(~mine)[their_dots] <= 3).mean()`` --- the fraction
   of *their* dots near *mine*, which is the protocol's **reverse** overlap ---
   and called the protocol's forward statistic ``reverse_overlap``.  Its
   docstring described the correct quantity, so the code silently disagreed with
   both the protocol and its own documentation, and the dense-prior exemption was
   applied to the wrong leg.  Every overlap number this lane published before
   that date was measured with the two directions exchanged.  The definitions are
   now taken from the shared template (``gems57.uniqueness.dot_overlap``) rather
   than re-implemented, so there is one definition in the repository.

Both directions are reported, together with the chance-corrected reading the
shared template defines:

* ``chance_expected_overlap`` ``E`` --- the fraction of the scored footprint
  within 3 px of the witness's support, i.e. the overlap a randomly placed
  candidate would show;
* ``chance_corrected_lift`` ``= (observed - E) / (1 - E)``;
* ``saturated`` --- ``E >= gems57.uniqueness.SATURATED_E`` (0.99).  A saturated
  witness overlaps *every* nonempty candidate, so its literal firing is a
  property of the witness, not evidence of lane drift.  The literal firing is
  still reported and still counted; it is only labelled.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from . import grid

# one definition, in the shared template (protocol item 2: never keep a private fork)
from gems57.uniqueness import (DENSE_SUPPORT_FRACTION, OVERLAP_LIMIT, RHO_LIMIT,
                               SATURATED_E, chance_expected_overlap, dot_overlap)

RHO_MAX = RHO_LIMIT
OVERLAP_MAX = OVERLAP_LIMIT
BUFFER_PX = 3
DENSE_FRACTION = DENSE_SUPPORT_FRACTION


@dataclass
class Screen:
    name: str
    rho: float
    forward_overlap: float
    reverse_overlap: float
    n_other_positives: int
    dense: bool
    triggers: tuple
    chance_expected_overlap: float = float("nan")
    chance_corrected_lift: float = float("nan")
    saturated: bool = False
    sha256: str = ""

    def as_dict(self) -> dict:
        return dict(name=self.name, rho=self.rho, forward_overlap=self.forward_overlap,
                    reverse_overlap=self.reverse_overlap,
                    n_other_positives=self.n_other_positives, dense=self.dense,
                    triggers=list(self.triggers),
                    chance_expected_overlap=self.chance_expected_overlap,
                    chance_corrected_lift=self.chance_corrected_lift,
                    saturated=bool(self.saturated), sha256=self.sha256)


def _ranks(a: np.ndarray) -> np.ndarray:
    """Average ranks, vectorised.

    The previous revision averaged tie groups in a Python ``while`` loop over the
    sorted array.  On a 5,167,373-cell footprint with binary values that loop ran
    millions of iterations per witness (~4 s each), which made a full registry
    scan impractical; ``np.add.reduceat`` computes the same average ranks in one
    pass.  ``tests/test_ribbon_uniqueness.py`` pins the result against the
    scipy/product-moment definition.
    """
    a = np.asarray(a, float)
    if a.size == 0:
        return a.copy()
    order = np.argsort(a, kind="stable")
    r = np.empty(a.size, float)
    r[order] = np.arange(a.size, dtype=float)
    s = a[order]
    ranked = r[order]
    change = np.empty(s.size, bool)
    change[0] = True
    np.not_equal(s[1:], s[:-1], out=change[1:])
    starts = np.flatnonzero(change)
    counts = np.diff(np.r_[starts, s.size])
    means = np.add.reduceat(ranked, starts) / counts
    out = np.empty(a.size, float)
    out[order] = np.repeat(means, counts)
    return out


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = _ranks(x), _ranks(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return float((rx * ry).sum() / den) if den > 0 else 0.0


def _load(path: Path, fp: np.ndarray, shape) -> np.ndarray | None:
    with rasterio.open(path) as s:
        if (s.height, s.width) != shape:
            return None
        a = s.read(1).astype(np.float32)
    return a


def _lift(observed: float, e: float) -> float:
    if not np.isfinite(e) or e >= 1.0:
        return float("nan")
    return float((observed - e) / (1.0 - e))


def screen_paths(dots: np.ndarray, paths, fp: np.ndarray | None = None, shape=None,
                 names: list[str] | None = None, rho_subsample: int | None = None,
                 dot_index: np.ndarray | None = None) -> tuple[list[Screen], dict]:
    """Screen a dot set against an explicit list of raster paths.

    ``rho_subsample`` imposes a deterministic stride over the footprint cells before
    the rank correlation is computed.  ``None`` (the default) keeps the exact
    full-field Spearman.  A subsampled rank correlation is a **weaker** statistic
    than the exact one, so the value actually used is recorded in the summary
    (``rho_subsample`` / ``rho_statistic``) and a subsampled pass must never be
    reported as an exact pass.

    ``dot_index`` is accepted for call compatibility with the sibling lane's
    emitters; this implementation works from the boolean dot field and the distance
    transform, so it does not need the index array.
    """
    fp = grid.footprint() if fp is None else fp
    shape = fp.shape if shape is None else shape
    dots = np.asarray(dots, bool) & fp
    mine_vals = dots.astype(np.float32)
    n_fp = int(fp.sum())
    out: list[Screen] = []
    skipped: list[dict] = []
    paths = list(paths)
    names = list(names) if names is not None else [Path(p).name for p in paths]
    for path, name in zip(paths, names):
        try:
            a = _load(Path(path), fp, shape)
        except (OSError, rasterio.errors.RasterioError) as exc:
            skipped.append(dict(name=name, reason=f"unreadable: {exc}"))
            continue
        if a is None:
            skipped.append(dict(name=name, reason="grid mismatch"))
            continue
        fin = np.isfinite(a) & fp
        if not fin.any():
            skipped.append(dict(name=name, reason="no finite pixels in footprint"))
            continue
        other = fin & (a > 0)
        n_other = int(other.sum())
        support_fraction = n_other / n_fp if n_fp else 0.0
        dense = support_fraction > DENSE_FRACTION
        # protocol direction: MY dots within 3 px of THEIR dots (shared definition)
        fwd = dot_overlap(mine_vals, np.where(other, 1.0, 0.0), BUFFER_PX) if dots.any() else 0.0
        rev = float((distance_transform_edt(~dots)[other] <= BUFFER_PX).mean()) if n_other else 0.0
        e = chance_expected_overlap(other, fp, BUFFER_PX)
        vx = np.where(fin, mine_vals, 0.0)
        vy = np.where(fin, a, 0.0)
        if rho_subsample is not None:
            idx = np.flatnonzero(fp)
            if idx.size > rho_subsample:
                idx = idx[:: max(1, idx.size // rho_subsample)]
            sx, sy = vx.flat[idx], vy.flat[idx]
        else:
            sx, sy = vx[fp], vy[fp]
        rho = spearman(sx, sy) if sx.size > 100 else 0.0
        triggers = []
        if rho > RHO_MAX:
            triggers.append("rho")
        if fwd > OVERLAP_MAX:
            triggers.append("forward_overlap")
            if e < SATURATED_E:
                triggers.append("forward_overlap_informative")
        out.append(Screen(name=name, rho=rho, forward_overlap=fwd, reverse_overlap=rev,
                          n_other_positives=n_other, dense=bool(dense),
                          triggers=tuple(triggers), chance_expected_overlap=e,
                          chance_corrected_lift=_lift(fwd, e),
                          saturated=bool(e >= SATURATED_E),
                          sha256=""))
    return out, summarise(out, skipped, n_fp, rho_subsample=rho_subsample)


def screen_against(dots: np.ndarray, registry_dir: Path, fp: np.ndarray | None = None,
                   shape=None, rho_subsample: int | None = None,
                   dot_index: np.ndarray | None = None) -> tuple[list[Screen], dict]:
    """Screen a dot set against every ``*.tif`` in ``registry_dir``."""
    paths = sorted(Path(registry_dir).glob("*.tif"))
    return screen_paths(dots, paths, fp=fp, shape=shape, rho_subsample=rho_subsample,
                        dot_index=dot_index)


def summarise(out: list[Screen], skipped: list[dict], n_fp: int,
              rho_subsample: int | None = None) -> dict:
    informative = [s for s in out if not s.saturated]
    ov_fire = [s for s in out if s.forward_overlap > OVERLAP_MAX]
    ov_fire_inf = [s for s in ov_fire if not s.saturated]
    rho_fire = [s for s in out if s.rho > RHO_MAX]
    if rho_fire or ov_fire_inf:
        drift = "informative"
    elif ov_fire:
        drift = "vacuous-only"
    else:
        drift = "none"
    summary = dict(
        n_checked=len(out), n_skipped=len(skipped), skipped=skipped,
        footprint_px=n_fp,
        worst_rho=max((s.rho for s in out), default=0.0),
        worst_rho_name=max(out, key=lambda s: s.rho).name if out else None,
        worst_forward_overlap=max((s.forward_overlap for s in out), default=0.0),
        worst_forward_overlap_name=(max(out, key=lambda s: s.forward_overlap).name
                                    if out else None),
        worst_forward_overlap_informative=(
            max((s.forward_overlap for s in informative), default=None)),
        worst_forward_overlap_informative_name=(
            max(informative, key=lambda s: s.forward_overlap).name if informative else None),
        worst_chance_corrected_lift=(
            max((s.chance_corrected_lift for s in informative
                 if np.isfinite(s.chance_corrected_lift)), default=None)),
        worst_reverse_overlap=max((s.reverse_overlap for s in out), default=0.0),
        n_triggers=sum(1 for s in out if s.triggers),
        n_overlap_firings=len(ov_fire),
        n_overlap_firings_informative=len(ov_fire_inf),
        n_overlap_firings_vacuous=len(ov_fire) - len(ov_fire_inf),
        overlap_firings_informative=[s.name for s in ov_fire_inf],
        n_rho_firings=len(rho_fire), rho_firings=[s.name for s in rho_fire],
        n_saturated_witnesses=sum(1 for s in out if s.saturated),
        n_dense_priors=sum(1 for s in out if s.dense),
        lane_drift_evidence=drift,
        cleared=bool(not rho_fire and not ov_fire_inf),
        rho_max=RHO_MAX, overlap_max=OVERLAP_MAX, buffer_px=BUFFER_PX,
        rho_subsample=rho_subsample,
        rho_statistic=("exact full-footprint Spearman" if rho_subsample is None else
                       f"SUBSAMPLED Spearman (stride to ~{rho_subsample} cells): weaker than "
                       "exact, so this screen is not an exact rank-correlation pass"),
        saturated_threshold_E=SATURATED_E, dense_support_fraction=DENSE_FRACTION,
        definitions=("forward_overlap = fraction of MY dots within 3 px of the witness's dots "
                     "(gems57.uniqueness.dot_overlap); reverse_overlap = fraction of the "
                     "witness's dots within 3 px of mine; E = fraction of the footprint within "
                     "3 px of the witness's dots; lift = (observed - E) / (1 - E)."),
    )
    dense_rows = [s for s in out if s.dense or s.saturated]
    if dense_rows:
        summary["saturated_or_dense_witnesses"] = [
            dict(name=s.name, positives=s.n_other_positives, forward_overlap=s.forward_overlap,
                 chance_expected_overlap=s.chance_expected_overlap,
                 chance_corrected_lift=s.chance_corrected_lift, saturated=s.saturated)
            for s in sorted(dense_rows, key=lambda s: -s.forward_overlap)]
    return summary
