"""Duplicate check of a candidate GeoTIFF against every raster in this repo.

Covers the rasters the registry screen (19 registry + 4 downloads) does NOT
cover: our own control/evidence rasters. Reports Spearman rho on the
footprint, fraction of candidate dots within 3 px of the other raster's dots,
and Jaccard of the positive sets. Read-only; writes JSON evidence.

Usage: python scripts/check_own_rasters.py <candidate.tif> <out.json>
"""
import glob
import hashlib
import json
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

RHO_MAX, OVERLAP_MAX, RADIUS = 0.90, 0.70, 3.0
FOOTPRINT = "data/official/sample_submission.tif"
EXCLUDE_SELF = True


def load(path):
    with rasterio.open(path) as s:
        return s.read(1)


def compare(cand, other, footprint):
    cp, op = cand == 1, other == 1
    m = footprint & np.isfinite(cand) & np.isfinite(other)
    rho = spearmanr(np.nan_to_num(cand[m]), np.nan_to_num(other[m])).correlation
    within = (distance_transform_edt(~op)[cp] <= RADIUS).mean() if cp.any() and op.any() else 0.0
    jac = (cp & op).sum() / max(1, (cp | op).sum())
    return dict(rho=float(rho), frac_dots_within_3px_of_other=float(within), jaccard=float(jac),
                n_other_positives=int(op.sum()))


def main(cand_path, out_path):
    cand = load(cand_path)
    footprint = np.isfinite(load(FOOTPRINT))
    paths = sorted(glob.glob("evidence/**/*.tif", recursive=True)
                   + glob.glob("docs/downloads/*.tif")
                   + glob.glob("docs/ribbon/downloads/*.tif")
                   + glob.glob("data/registry/rasters/*.tif"))
    cand_sha = hashlib.sha256(open(cand_path, "rb").read()).hexdigest()
    rows, seen_sha = [], set()
    for p in paths:
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if sha == cand_sha:
            rows.append(dict(path=p, status="IDENTICAL_BYTES_TO_CANDIDATE"))
            continue
        if sha in seen_sha:
            continue  # byte-identical copies are reported once
        seen_sha.add(sha)
        other = load(p)
        if other.shape != cand.shape:
            rows.append(dict(path=p, status="shape_mismatch"))
            continue
        r = compare(cand, other, footprint)
        r.update(path=p, sha256=sha,
                 flagged=bool(r["rho"] >= RHO_MAX or r["frac_dots_within_3px_of_other"] >= OVERLAP_MAX))
        rows.append(r)
    flagged = [r for r in rows if r.get("flagged") or r.get("status")]
    worst = max((r for r in rows if "rho" in r), key=lambda r: r["rho"])
    out = dict(candidate=cand_path, candidate_sha256=cand_sha, rho_max=RHO_MAX,
               overlap_max=OVERLAP_MAX, radius_px=RADIUS, n_rasters=len(rows),
               n_flagged=len(flagged), worst_rho=worst["rho"], worst_rho_path=worst["path"],
               max_overlap=max(r["frac_dots_within_3px_of_other"] for r in rows if "rho" in r),
               verdict="DUPLICATE_OR_DRIFT" if flagged else "NO_FLAG_IN_LOCAL_SET",
               scope_note="Local rasters only. The 695-raster frozen registry is NOT in this checkout "
                          "(evidence/registry_cache_restore.json: restored 0).", rows=rows)
    json.dump(out, open(out_path, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
