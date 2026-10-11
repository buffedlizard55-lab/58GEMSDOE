#!/usr/bin/env python3
"""Parallel uniqueness scan of the candidate raster against the pinned registry.

Uses the shared gems57.uniqueness definitions (rho limit 0.90, forward 3-px dot
overlap limit 0.70, Jaccard diagnostic-only) and its summarize_registry_rows
gate (fail-closed on an incomplete scan).  The per-record arithmetic mirrors
gems57.uniqueness.compare_array_to_registry, reusing its helpers; the only new
code here is multiprocessing chunking (the REST-API-based shared tool was
rate-limited this session; the registry was restored over the git protocol with
every file sha256-verified before caching).
"""
from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57.uniqueness import (JACCARD_LIMIT, OVERLAP_LIMIT, RHO_LIMIT,
                               RADIUS_PX, SATURATED_E, _dots, _jaccard, _near,
                               chance_expected_overlap, representation_class,
                               summarize_registry_rows)
from scipy.stats import rankdata

_CAND = {}
_FP = {}
_RANK = {}
_EXPECTED_GRID = None


def _init(candidate_path: str):
    global _EXPECTED_GRID
    from gems57.grid import load_grid
    grid = load_grid(ROOT / "data" / "bridge")
    with rasterio.open(ROOT / "data" / "official" / "sample_submission.tif") as ref:
        _EXPECTED_GRID = (ref.shape, ref.crs, ref.transform)
    with rasterio.open(candidate_path) as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != _EXPECTED_GRID:
            raise ValueError("candidate CRS/shape/transform differs from sample submission")
        mine = src.read(1).astype(np.float32)
    # The organizer's own sample_submission.tif carries NaN outside the study
    # footprint (nodata=nan) and finite values inside it, so that is the official
    # representation and a delivered candidate may legitimately contain it. A
    # non-finite value INSIDE the footprint is exactly the portal rejection the
    # owner already hit ("Predicted values must be in range [0, 1]"), so it stays
    # a hard error; outside the footprint it is normalised to 0, which changes
    # nothing because every statistic below is footprint-restricted.
    fp = grid.footprint
    if not np.isfinite(mine[fp]).all():
        raise ValueError("candidate has non-finite values inside the scored footprint; "
                         "the portal rejects these ('Predicted values must be in range [0, 1]')")
    _CAND["nan_inside_footprint"] = 0
    _CAND["nan_outside_footprint"] = int((~np.isfinite(mine) & ~fp).sum())
    mine = np.where(np.isfinite(mine), mine, 0.0).astype(np.float32)
    if (mine < 0).any() or (mine > 1).any():
        raise ValueError("candidate must be in [0,1] before registry comparison")
    _CAND["a"] = mine
    _FP["a"] = fp
    values = mine[grid.footprint]
    ranks = rankdata(values).astype(np.float64)
    ranks -= ranks.mean()
    _RANK["a"] = (ranks, float(np.linalg.norm(ranks)), hashlib.sha256(np.ascontiguousarray(mine).tobytes()).hexdigest())
    _CAND["file_sha"] = hashlib.sha256(Path(candidate_path).read_bytes()).hexdigest()


def _scan_chunk(records: list[dict]) -> list[dict]:
    mine = _CAND["a"]
    fp = _FP["a"]
    ranks, norm, decoded_digest = _RANK["a"]
    my_support = _dots(mine) & fp
    my_dot_count = int(my_support.sum())
    rows = []
    for rec in records:
        p = ROOT / rec["cache_file"]
        base = dict(repo=rec.get("repo_first"), submission=rec["sources"][0], file=str(p))
        try:
            if not p.exists():
                raise FileNotFoundError("registry raster not restored; cannot certify")
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest != rec["sha256"]:
                raise ValueError("registry sha256 pin mismatch")
            with rasterio.open(p) as src:
                if src.count != 1 or (src.shape, src.crs, src.transform) != _EXPECTED_GRID:
                    raise ValueError("registry CRS/shape/transform or band-count mismatch")
                theirs = src.read(1).astype(np.float32)
            theirs = np.where(np.isfinite(theirs), theirs, 0.0)
            theirs[~fp] = 0
            tv = theirs[fp]
            support = (theirs > 0) & fp
            tb = support[fp]
            if norm == 0 or np.ptp(tv) == 0:
                rho = None
            elif np.all((tv == 0) | (tv == 1)):
                nt = int(tb.sum()); n = len(tv)
                rho = float(ranks[tb].sum() / (norm * np.sqrt(nt * (n - nt) / n))) if 0 < nt < n else None
            else:
                tr = rankdata(tv).astype(np.float64)
                tr -= tr.mean()
                rho = float(np.dot(ranks, tr) / (norm * np.linalg.norm(tr)))
            ov = float(_near(support)[my_support].mean()) if my_dot_count else 0.0
            jac = _jaccard(my_support, support)
            # chance-corrected reading (shared template): E is the overlap a randomly
            # placed candidate would show; a witness with E >= SATURATED_E overlaps
            # every nonempty candidate, so its literal firing carries no information.
            e = chance_expected_overlap(support, fp, RADIUS_PX)
            lift = float((ov - e) / (1.0 - e)) if e < 1.0 else float('nan')
            rep = representation_class(int(support.sum()), int(fp.sum()))['kind']
            their_decoded = hashlib.sha256(np.ascontiguousarray(theirs).tobytes()).hexdigest()
            rows.append({**base, "sha256": digest, "decoded_sha256": their_decoded,
                         "their_dots": int(support.sum()),
                         "chance_expected_overlap": e,
                         "chance_corrected_lift": lift,
                         "saturated": bool(e >= SATURATED_E),
                         "representation": rep,
                         "my_dots_within_3px_of_theirs": ov,
                         "spearman_full_footprint": rho,
                         "jaccard_dot_sets": jac,
                         "identical_bytes": bool(_CAND["file_sha"] == digest),
                         "identical_decoded_predictions": bool(their_decoded == decoded_digest),
                         "duplicate_by_rho": bool(rho is not None and rho > RHO_LIMIT),
                         "duplicate_by_overlap": bool(ov > OVERLAP_LIMIT),
                         "duplicate_by_jaccard": bool(jac > JACCARD_LIMIT)})
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            rows.append({**base, "error": str(exc)})
    return rows


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", help="path to the candidate -zeros.tif")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="ribbon_uniqueness.json",
                    help="evidence file to write (default keeps the ribbon lane's name)")
    ap.add_argument("--index", default=None,
                    help="registry index JSON (default: registry/registry_merged.json when it "
                         "exists, else registry/registry_refreshed.json)")
    a = ap.parse_args()

    index_path = Path(a.index) if a.index else (
        ROOT / "registry" / "registry_merged.json"
        if (ROOT / "registry" / "registry_merged.json").exists()
        else ROOT / "registry" / "registry_refreshed.json")
    reg = json.loads(index_path.read_text())
    cand_sha = hashlib.sha256(Path(a.candidate).read_bytes()).hexdigest()
    idx, self_excluded = [], []
    for r in reg["rasters"]:
        if r["sha256"] == cand_sha:            # the candidate's own entry is not a witness
            self_excluded.append(r["sources"][0] if r.get("sources") else r["sha256"])
            continue
        idx.append({**r, "cache_file": f".cache/registry/{r['sha256']}.tif"})
    (ROOT / "evidence" / "registry_scan_index.json").write_text(json.dumps(idx) + "\n")

    restored = sum(1 for r in idx if (ROOT / r["cache_file"]).exists())
    print(f"index: {index_path.relative_to(ROOT)} | registry rasters: {len(idx)} "
          f"({len(self_excluded)} self-entries excluded); restored in cache: {restored}",
          flush=True)

    chunks = [idx[i::a.workers] for i in range(a.workers)]
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init,
                             initargs=(a.candidate,)) as ex:
        for sub in ex.map(_scan_chunk, chunks):
            rows.extend(sub)
            print(f"scanned {len(rows)}/{len(idx)}", flush=True)

    from gems57.grid import load_grid
    grid = load_grid(ROOT / "data" / "bridge")
    with rasterio.open(a.candidate) as src:
        mine = src.read(1)
    # _CAND is populated in the worker processes only, so the parent recomputes
    # what it reports; the raw rows are persisted before the summary is built so a
    # later crash can never throw away a completed scan.
    finite = np.isfinite(mine)
    nan_inside = int((~finite & grid.footprint).sum())
    nan_outside = int((~finite & ~grid.footprint).sum())
    if nan_inside:
        raise ValueError("candidate has non-finite values inside the scored footprint")
    rows_path = ROOT / "evidence" / "registry_scan_rows.json"
    rows_path.write_text(json.dumps(rows, default=float) + "\n")
    my_dots = int(((mine > 0) & grid.footprint).sum())
    summary = summarize_registry_rows(
        rows,
        registry_rasters_expected=len(idx),
        complete_accessible_scan=bool(len(idx) == restored and restored > 0),
        source_errors=[],
        candidate_meta=dict(my_file=str(a.candidate), my_dots=my_dots,
                            candidate_file_sha256=hashlib.sha256(Path(a.candidate).read_bytes()).hexdigest(),
                            candidate_decoded_sha256=hashlib.sha256(np.ascontiguousarray(mine).tobytes()).hexdigest(),
                            candidate_rank_variation=True,
                            candidate_nan_inside_footprint=nan_inside,
                            candidate_nan_outside_footprint=nan_outside,
                            candidate_representation=("official sample_submission format: "
                                                      "NaN outside the study footprint, finite "
                                                      "values inside")),
        scope=("All sha256-verified accessible entries of the public owner-repository "
               "inventory in %s (%d witnesses, %d repos scanned, self-entries excluded: %s). "
               "This is the public sibling-repository inventory, not an organizer registry."
               % (index_path.relative_to(ROOT), len(idx), len(reg.get("repos_scanned", [])),
                  self_excluded or "none")),
    )
    summary["index"] = str(index_path.relative_to(ROOT))
    summary["index_generated_utc"] = reg.get("generated_utc")
    summary["self_entries_excluded"] = self_excluded
    out = ROOT / "evidence" / a.out
    out.write_text(json.dumps(summary, indent=1, default=float) + "\n")
    print(f"verdict: {summary['verdict']} | worst rho {summary['worst_spearman_full_footprint']} "
          f"({summary['worst_rho_submission']}) | worst overlap {summary['worst_dot_overlap']} "
          f"({summary['worst_overlap_submission']}) | duplicate_count {summary['duplicate_count']} "
          f"| complete={summary['complete_accessible_scan']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
