#!/usr/bin/env python3
"""Session-6 uniqueness screen and shape statistics for the delivered raster.

Screen statistic (the protocol's own wording): for every witness raster W, the
fraction of *this* file's dots that lie within 3 px of one of W's dots
("forward overlap"), plus the two discriminating statistics the previous sessions
published beside it:

* rank correlation of the two rasters over the footprint (limit 0.90);
* dot-set Jaccard (limit 0.50);
* chance-corrected lift ``(O - E) / (1 - E)`` where ``E`` is the fraction of the
  scored footprint covered by W's own 3 px dilation -- a witness that already
  covers most of the plane cannot discriminate, so both readings are reported.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, label
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

CACHE = ROOT / ".cache" / "registry"
LOCAL = ROOT / "data" / "registry" / "rasters"
EV = ROOT / "evidence" / "s6"
RADIUS = 3.0
LITERAL_O = 0.70
RULE_A_E = 0.70
RULE_B_LIFT = 0.50
RHO_LIMIT = 0.90
JACCARD_LIMIT = 0.50


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if src is None:
        emit = json.loads((EV / "emit.json").read_text())
        src = ROOT / "docs" / "downloads" / emit["file"]
    src = Path(src)
    with rasterio.open(src) as s:
        a = s.read(1)
    fp = np.isfinite(a)
    mine = (a > 0) & fp
    ys, xs = np.nonzero(mine)
    pts = np.stack([ys, xs], 1).astype(np.float64)
    n = int(pts.shape[0])
    cat = rasterio.open(ROOT / "data" / "official" / "existing_faults.tif").read(1) > 0
    dcat = distance_transform_edt(~cat)

    # ---- shape statistics, comparable with the registry table ----
    lab, k = label(mine, structure=np.ones((3, 3), int))
    sizes = np.bincount(lab.ravel())[1:]
    tree = cKDTree(pts)
    cnt = np.array([len(z) for z in tree.query_ball_point(pts, RADIUS, workers=-1)]) - 1
    dens = n / fp.sum()
    quad = {}
    h, w = mine.shape
    for name, (r0, r1, c0, c1) in {
        "NW": (0, h // 2, 0, w // 2), "NE": (0, h // 2, w // 2, w),
        "SW": (h // 2, h, 0, w // 2), "SE": (h // 2, h, w // 2, w)}.items():
        quad[name] = int(mine[r0:r1, c0:c1].sum())
    shape = dict(n_dots=n, max_component_px=int(sizes.max()) if sizes.size else 0,
                 clustering_vs_random=float(cnt.mean() / (dens * np.pi * RADIUS ** 2)),
                 median_distance_to_catalogue_px=float(np.median(dcat[mine])),
                 frac_within_3px_of_catalogue=float((dcat[mine] <= 3).mean()),
                 quadrant_counts=quad,
                 footprint_frac_covered_by_own_3px_dilation=
                 float(binary_dilation(mine, np.ones((7, 7), bool))[fp].mean()))

    # ---- witnesses ----
    reg = json.loads((ROOT / "registry" / "registry_merged.json").read_text())
    paths = {}
    for r in reg["rasters"]:
        p = CACHE / f"{r['sha256']}.tif"
        if p.is_file():
            paths[r["sha256"]] = (p, r)
    for p in sorted(LOCAL.glob("*.tif")):
        d = sha256(p)
        paths.setdefault(str(d), (p, dict(sha256=str(d), sources=[f"local:{p.name}"])))

    rows = []
    rng = np.random.default_rng(61011)
    fidx = np.flatnonzero(fp.ravel())
    sub = rng.choice(fidx, size=min(300000, fidx.size), replace=False)
    flat_mine = a.ravel()[sub].astype(np.float64)
    for sha, (p, meta) in sorted(paths.items()):
        try:
            with rasterio.open(p) as s:
                b = s.read(1)
        except Exception as exc:                        # noqa: BLE001
            rows.append(dict(sha256=sha, source=meta["sources"][0], error=str(exc)))
            continue
        if b.shape != a.shape:
            rows.append(dict(sha256=sha, source=meta["sources"][0], error="shape mismatch"))
            continue
        wb = (b > 0) & np.isfinite(b) & fp
        nw = int(wb.sum())
        if nw == 0:
            continue
        wy, wx = np.nonzero(wb)
        wt = cKDTree(np.stack([wy, wx], 1).astype(np.float64))
        # forward overlap: my dots within 3 px of one of theirs
        d, _ = wt.query(pts, k=1, workers=-1)
        O = float((d <= RADIUS).mean())
        # chance level: their 3 px dilation as a fraction of the scored footprint
        E = float(binary_dilation(wb, np.ones((7, 7), bool))[fp].mean())
        lift = float((O - E) / (1 - E)) if E < 1 else 0.0
        inter = int((mine & wb).sum())
        jac = inter / max(1, int((mine | wb).sum()))
        bsub = b.ravel()[sub].astype(np.float64)
        rho = 0.0 if (flat_mine.std() == 0 or bsub.std() == 0) else \
            float(spearmanr(flat_mine, bsub).statistic)
        rho = 0.0 if not np.isfinite(rho) else rho
        rows.append(dict(sha256=sha, source=meta["sources"][0], n_witness_dots=nw,
                         forward_overlap=O, chance_E=E, lift=lift,
                         jaccard=float(jac), shared_pixels=inter, rank_corr=rho,
                         literal_fire=bool(O > LITERAL_O),
                         ruleA_fire=bool(O > LITERAL_O and E < RULE_A_E),
                         ruleB_fire=bool(lift > RULE_B_LIFT and E < 0.99),
                         rho_fire=bool(rho > RHO_LIMIT), jaccard_fire=bool(jac > JACCARD_LIMIT)))
    ok_rows = [r for r in rows if "error" not in r]
    summary = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        screened_file=src.name, sha256=sha256(src), bytes=src.stat().st_size,
        witnesses_screened=len(ok_rows), witnesses_errored=len(rows) - len(ok_rows),
        pinned_witnesses=len(reg["rasters"]),
        worst=dict(
            forward_overlap=max((r["forward_overlap"] for r in ok_rows), default=None),
            lift=max((r["lift"] for r in ok_rows), default=None),
            rank_corr=max((abs(r["rank_corr"]) for r in ok_rows), default=None),
            jaccard=max((r["jaccard"] for r in ok_rows), default=None)),
        firings=dict(literal=sum(r["literal_fire"] for r in ok_rows),
                     ruleA=sum(r["ruleA_fire"] for r in ok_rows),
                     ruleB=sum(r["ruleB_fire"] for r in ok_rows),
                     rank_corr=sum(r["rho_fire"] for r in ok_rows),
                     jaccard=sum(r["jaccard_fire"] for r in ok_rows)),
        byte_identical=any(r["sha256"] == sha256(src) for r in ok_rows),
        shape=shape,
        limits=dict(literal_overlap=LITERAL_O, ruleA_E=RULE_A_E, ruleB_lift=RULE_B_LIFT,
                    rank_corr=RHO_LIMIT, jaccard=JACCARD_LIMIT),
        wall_seconds=round(time.time() - t0, 1))
    summary["verdict"] = ("DUPLICATE" if (summary["firings"]["literal"] or
                                          summary["firings"]["ruleA"] or
                                          summary["firings"]["ruleB"] or
                                          summary["firings"]["rank_corr"] or
                                          summary["firings"]["jaccard"] or
                                          summary["byte_identical"]) else "UNIQUE")
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "uniqueness.json").write_text(json.dumps(summary, indent=1, default=float))
    (EV / "uniqueness_rows.json").write_text(json.dumps(rows, indent=1, default=float))
    print(json.dumps({k: summary[k] for k in
                      ("witnesses_screened", "firings", "worst", "byte_identical",
                       "shape", "verdict")}, indent=1, default=float))
    worst_rows = sorted(ok_rows, key=lambda r: -r["forward_overlap"])[:8]
    print("\nwitnesses with the largest forward overlap:")
    for r in worst_rows:
        print(f"  O={r['forward_overlap']:.4f} E={r['chance_E']:.4f} lift={r['lift']:+.4f} "
              f"rho={r['rank_corr']:+.4f} J={r['jaccard']:.4f}  {r['source'][:78]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
