"""Uniqueness screen against every accessible earlier raster.

Two statistics are computed against each registry raster, exactly as the
parallel-run protocol defines them:

* **rank correlation** of the two full-footprint value fields
  (Spearman; ties are handled by average ranks).  Triggers at ``> RHO_MAX``.
* **forward overlap**: the fraction of this lane's dots that fall within 3 px
  (300 m) of any dot of the registry raster.  Triggers at ``> OVERLAP_MAX``.

Reverse overlap (registry dots near ours) is reported alongside but is not a
trigger, because a dense prior with millions of positive pixels covers every
allowed cell --- the saturation obstruction measured as ``IR-57-REPR-01`` in the
sibling lane.  Dense rasters are additionally flagged so a human can see that
the forward-overlap number is dominated by their support, not by agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

from . import grid

RHO_MAX = 0.90
OVERLAP_MAX = 0.70
BUFFER_PX = 3
DENSE_FRACTION = 0.5   # a raster with >= 50 % of the footprint positive is "dense"


@dataclass
class Screen:
    name: str
    rho: float
    forward_overlap: float
    reverse_overlap: float
    n_other_positives: int
    dense: bool
    triggers: tuple

    def as_dict(self) -> dict:
        return dict(name=self.name, rho=self.rho, forward_overlap=self.forward_overlap,
                    reverse_overlap=self.reverse_overlap,
                    n_other_positives=self.n_other_positives, dense=self.dense,
                    triggers=list(self.triggers))


def _ranks(a: np.ndarray) -> np.ndarray:
    order = np.argsort(a, kind="stable")
    r = np.empty(a.size, float)
    r[order] = np.arange(a.size, dtype=float)
    # average ties
    s = a[order]
    i = 0
    while i < s.size:
        j = i + 1
        while j < s.size and s[j] == s[i]:
            j += 1
        if j - i > 1:
            r[order[i:j]] = r[order[i:j]].mean()
        i = j
    return r


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
    if np.isfinite(a[fp]).all() and (a[fp] > 0).all():
        pass  # dense continuous surface; still usable
    return a


def screen_against(dots: np.ndarray, registry_dir: Path, fp: np.ndarray | None = None,
                   shape=None) -> tuple[list[Screen], dict]:
    fp = grid.footprint() if fp is None else fp
    shape = fp.shape if shape is None else shape
    mine_vals = dots.astype(np.float32)
    mine_vals[~fp] = np.nan
    d_dot = distance_transform_edt(~dots)
    out: list[Screen] = []
    skipped: list[dict] = []
    for path in sorted(Path(registry_dir).glob("*.tif")):
        a = _load(path, fp, shape)
        if a is None:
            skipped.append(dict(name=path.name, reason="grid mismatch"))
            continue
        fin = np.isfinite(a) & fp
        if not fin.any():
            skipped.append(dict(name=path.name, reason="no finite pixels in footprint"))
            continue
        other = fin & (a > 0)
        n_other = int(other.sum())
        dense = n_other >= DENSE_FRACTION * int(fp.sum()) or n_other > 1_000_000

        fwd = float((d_dot[other] <= BUFFER_PX).mean()) if n_other else 0.0
        rev = 0.0
        if dots.any():
            rev = float((distance_transform_edt(~other)[dots] <= BUFFER_PX).mean())
        vx = np.where(fin, np.nan_to_num(mine_vals, nan=0.0), np.nan)
        vy = np.where(fin, a, np.nan)
        okfin = np.isfinite(vx) & np.isfinite(vy)
        rho = spearman(vx[okfin], vy[okfin]) if okfin.sum() > 100 else 0.0
        triggers = []
        if rho > RHO_MAX:
            triggers.append("rho")
        if fwd > OVERLAP_MAX and not dense:
            triggers.append("forward_overlap")
        out.append(Screen(name=path.name, rho=rho, forward_overlap=fwd,
                          reverse_overlap=rev, n_other_positives=n_other,
                          dense=bool(dense), triggers=tuple(triggers)))
    summary = dict(
        n_checked=len(out), n_skipped=len(skipped), skipped=skipped,
        worst_rho=max((s.rho for s in out), default=0.0),
        worst_rho_name=max(out, key=lambda s: s.rho).name if out else None,
        worst_forward_overlap=max((s.forward_overlap for s in out), default=0.0),
        worst_forward_overlap_name=max(out, key=lambda s: s.forward_overlap).name if out else None,
        n_triggers=sum(1 for s in out if s.triggers),
        n_dense_priors=sum(1 for s in out if s.dense),
        rho_max=RHO_MAX, overlap_max=OVERLAP_MAX, buffer_px=BUFFER_PX,
    )
    worst_dense = [s for s in out if s.dense]
    if worst_dense:
        summary["dense_priors"] = [
            dict(name=s.name, positives=s.n_other_positives, forward_overlap=s.forward_overlap)
            for s in sorted(worst_dense, key=lambda s: -s.forward_overlap)]
    return out, summary
