#!/usr/bin/env python3
"""Fast uniqueness screen over every cached registry witness.

Definitions are the shared ones (``gems57.uniqueness`` / ``gems58w.uniqueness``):

* forward overlap  = fraction of MY dots within 3 px of THEIR dots   (protocol stat)
* reverse overlap  = fraction of THEIR dots within 3 px of MY dots
* E                = chance-expected overlap = fraction of scored footprint within
                     3 px of THEIR support
* lift             = (forward - E) / (1 - E)
* rho              = Spearman of the two value fields over the footprint

The implementation is vectorised (Euclidean EDT == dilation by the same 3-px disk;
KDTree point tests == the disk test for dot sets; phi-coefficient fast path for
binary fields, mathematically identical to tie-averaged Spearman when both fields
are binary; witness ``E`` cached because it depends only on the witness) so a
694-witness scan is feasible.  ``--crosscheck`` verifies the vectorised numbers
against the shared ``gems58w.uniqueness.screen_paths`` on a deterministic sample
of witnesses and records the max absolute deviation; a deviation > 1e-9 aborts
the fast screen.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w.uniqueness import (OVERLAP_MAX, RHO_MAX, SATURATED_E,  # noqa: E402
                                summarise, Screen)
from gems57.uniqueness import DENSE_SUPPORT_FRACTION  # noqa: E402

BUFFER_PX = 3


def _phi_binary(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman for two binary fields == Pearson on the 0/1 values (average ties)."""
    x = x.astype(np.float64)
    y = y.astype(np.float64)
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    if sx == 0 or sy == 0:
        return 0.0
    return float(((x - mx) * (y - my)).mean() / (sx * sy))


def screen_fast(mine: np.ndarray, witness_paths: list[Path], fp: np.ndarray,
                name_of, crosscheck_paths: list[Path] | None = None,
                cache_dir: Path | None = None) -> dict:
    mine = np.asarray(mine, bool) & fp
    n_fp = int(fp.sum())
    # EDT on ~support == Euclidean dilation by the same 3-px disk, but far faster
    # than generic binary_dilation with a 49-element structure.
    mine_dil = (distance_transform_edt(~mine) <= float(BUFFER_PX)) if mine.any() else mine
    my_yx = np.argwhere(mine)
    my_tree = cKDTree_safe(my_yx)
    out: list[Screen] = []
    skipped: list[dict] = []
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)

    def one(path: Path) -> Screen | None:
        import rasterio
        name = name_of(path)
        try:
            with rasterio.open(path) as s:
                if (s.height, s.width) != fp.shape:
                    skipped.append(dict(name=name, reason="grid mismatch"))
                    return None
                a = s.read(1)
        except Exception as exc:  # noqa: BLE001
            skipped.append(dict(name=name, reason=f"unreadable: {exc}"))
            return None
        fin = np.isfinite(a) & fp
        if not fin.any():
            skipped.append(dict(name=name, reason="no finite pixels in footprint"))
            return None
        other = fin & (a > 0)
        n_other = int(other.sum())
        # E is a property of the witness alone: cached across screening passes.
        cfile = (cache_dir / f"{path.stem}.json") if cache_dir is not None else None
        e = None
        if cfile is not None and cfile.exists():
            try:
                meta = json.loads(cfile.read_text())
                if meta.get("n_other") == n_other and meta.get("v") == 2:
                    e = float(meta["e"])
            except (OSError, ValueError):
                e = None
        if e is None:
            near = distance_transform_edt(~other) <= float(BUFFER_PX)
            e = float(near[fp].mean()) if n_fp else 0.0
            if cfile is not None:
                cfile.write_text(json.dumps(dict(n_other=n_other, e=e, v=2)))
        # forward: MY dots within 3 px of THEIR dots; reverse: THEIR dots within
        # 3 px of MY dots.  For sparse supports a KDTree point test is fastest and
        # exactly equivalent to the shared disk test (d <= 3 inclusive; the query
        # bound is exclusive at the bound so query wider and threshold explicitly).
        # Dense supports avoid building million-point trees: one EDT serves both.
        fwd = 0.0
        rev = 0.0
        if n_other and len(my_yx):
            if n_other <= 150_000:
                other_yx = np.argwhere(other).astype(np.float64)
                if my_tree is not None:
                    d_rev, _ = my_tree.query(other_yx, k=1, workers=-1)
                    rev = float((d_rev <= BUFFER_PX + 1e-9).mean())
                t_other = cKDTree_safe(other_yx)
                if t_other is not None:
                    d_fwd, _ = t_other.query(my_yx.astype(np.float64), k=1, workers=-1,
                                             distance_upper_bound=float(BUFFER_PX) + 0.5)
                    fwd = float((np.isfinite(d_fwd) & (d_fwd <= BUFFER_PX + 1e-9)).mean())
            else:
                d_other = distance_transform_edt(~other)
                fwd = float((d_other[my_yx[:, 0], my_yx[:, 1]] <= BUFFER_PX + 1e-9).mean())
                rev = float((mine_dil[other]).mean())
        # rho over footprint (exact tie-averaged Spearman; phi fast path when the
        # witness field is binary, where the two are mathematically identical)
        vals_other = np.where(fin, a, 0.0)
        vals_mine = mine.astype(np.float32)
        u_other = np.unique(vals_other[fin])
        if u_other.size <= 2:
            rho = _phi_binary(vals_mine[fin], vals_other[fin])
        else:
            from gems58w.uniqueness import spearman
            rho = spearman(vals_mine[fin], vals_other[fin])
        support_fraction = n_other / n_fp if n_fp else 0.0
        dense = support_fraction > DENSE_SUPPORT_FRACTION
        saturated = e >= SATURATED_E
        triggers = []
        if rho > RHO_MAX:
            triggers.append("rho")
        if fwd > OVERLAP_MAX:
            triggers.append("forward_overlap")
            if not saturated:
                triggers.append("forward_overlap_informative")
        lift = float((fwd - e) / (1.0 - e)) if np.isfinite(e) and e < 1.0 else float("nan")
        return Screen(name=name, rho=float(rho), forward_overlap=fwd, reverse_overlap=rev,
                      n_other_positives=n_other, dense=bool(dense),
                      triggers=tuple(triggers), chance_expected_overlap=e,
                      chance_corrected_lift=lift, saturated=bool(saturated), sha256="")

    # optional correctness cross-check against the shared implementation
    cross = None
    if crosscheck_paths:
        from gems58w.uniqueness import screen_paths
        mine_vals = mine.astype(np.float32)
        max_dev = 0.0
        details = []
        for p in crosscheck_paths:
            screens, _ = screen_paths(mine_vals, [p], fp=fp, shape=fp.shape)
            if not screens:
                continue
            s_ref = screens[0]
            s_fast = one(p)
            if s_fast is None:
                continue
            dev = max(abs(s_ref.rho - s_fast.rho),
                      abs(s_ref.forward_overlap - s_fast.forward_overlap),
                      abs(s_ref.reverse_overlap - s_fast.reverse_overlap),
                      abs(s_ref.chance_expected_overlap - s_fast.chance_expected_overlap))
            max_dev = max(max_dev, dev)
            details.append(dict(name=s_ref.name, dev=dev))
        cross = dict(n_checked=len(details), max_abs_deviation=max_dev, details=details)
        if max_dev > 1e-9:
            return dict(error="fast screen deviates from shared definition", crosscheck=cross)

    t0 = time.time()
    for i, p in enumerate(witness_paths):
        s = one(p)
        if s is not None:
            out.append(s)
        if (i + 1) % 100 == 0:
            print(f"  screened {i + 1}/{len(witness_paths)} ({time.time() - t0:.0f}s)", flush=True)
    summary = summarise(out, skipped, n_fp, rho_subsample=None)
    summary["rho_statistic"] = ("exact tie-averaged Spearman (phi fast path when the witness "
                               "field is binary)")
    summary["runtime_s"] = round(time.time() - t0, 1)
    if cross is not None:
        summary["crosscheck_vs_shared_implementation"] = cross
    return dict(screens=[s.as_dict() for s in out], summary=summary)


def cKDTree_safe(pts: np.ndarray):
    from scipy.spatial import cKDTree
    if pts.size == 0:
        return None
    return cKDTree(pts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True,
                    help="tif of the candidate (dots = finite > 0), or 'surface:<tif>'")
    ap.add_argument("--out", required=True)
    ap.add_argument("--registry", default=str(ROOT / ".cache" / "registry"))
    ap.add_argument("--crosscheck", type=int, default=8)
    args = ap.parse_args()

    import rasterio
    from gems57.grid import load_grid
    grid = load_grid(ROOT / "data" / "bridge")
    fp = grid.footprint

    with rasterio.open(args.candidate.split(":", 1)[1] if args.candidate.startswith("surface:")
                       else args.candidate) as s:
        a = s.read(1)
    mine = np.isfinite(a) & (a > 0)
    mine &= fp

    reg = json.loads((ROOT / "registry" / "registry_refreshed.json").read_text())
    src_by_sha = {r["sha256"]: ";".join(r.get("sources", [])[:2]) for r in reg["rasters"]}
    paths = sorted(Path(args.registry).glob("*.tif"))

    def name_of(p: Path) -> str:
        sha = p.stem
        return f"{sha[:12]} {src_by_sha.get(sha, '')}"[:160]

    cc_paths = [paths[i] for i in np.linspace(0, len(paths) - 1,
                                              min(args.crosscheck, len(paths))).astype(int)] \
        if args.crosscheck else None
    result = screen_fast(mine, paths, fp, name_of, crosscheck_paths=cc_paths,
                         cache_dir=Path(args.registry).parent / "registry_meta")
    Path(args.out).write_text(json.dumps(result, indent=1) + "\n")
    if "error" in result:
        print(result)
        return 1
    s = result["summary"]
    print(f"checked {s['n_checked']} skipped {s['n_skipped']} | worst rho {s['worst_rho']:.4f} | "
          f"worst forward {s['worst_forward_overlap']:.4f} | "
          f"worst forward informative {s.get('worst_forward_overlap_informative')} | "
          f"runtime {s['runtime_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
