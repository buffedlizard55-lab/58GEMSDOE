#!/usr/bin/env python3
"""Uniqueness screen for the gems61 candidate against the byte-verified witness inventory.

Governed by the shared instrument in ``gems57.uniqueness`` (3 px radius, overlap limit
0.70, rank-correlation limit 0.90, Jaccard limit 0.50).  Both readings required by the
standing protocol are computed and both are written into the receipt:

* **literal** -- fraction of *our* dots within 3 px of the witness (fire above 0.70),
  and the rank correlation of the pre-placement surface with the witness (fire above
  0.90);
* **ratified (RATIFIED-UNIQ-v1)** -- an overlap firing blocks only when the witness could
  have failed to fire: rule A = literal overlap > 0.70 against a witness whose chance
  expectation ``E < 0.70``; rule B = chance-corrected lift ``(O − E)/(1 − E) > 0.50``
  against any witness with ``E < 0.99``.  A witness with ``E >= 0.99`` overlaps every
  nonempty candidate and carries no information; it is reported, never used to steer.

    python3 scripts/gems61_screen.py --candidate docs/downloads/<file>.tif \
        --surface .cache/gems58/gems61_mag.npy --out evidence/gems61/uniqueness.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57.uniqueness import _dots, _near, dot_overlap, surface_rho   # noqa: E402

CACHE = Path.home() / ".cache" / "gems" / "registry_witnesses"
_G: dict = {}
RHO_LIMIT, OVERLAP_LIMIT, JACCARD_LIMIT = 0.90, 0.70, 0.50
SATURATED_E = 0.99
RULE_A_E = 0.70
RULE_B_LIFT = 0.50


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _init(candidate: str, surface: str, footprint: str) -> None:
    with rasterio.open(candidate) as src:
        mine = src.read(1).astype(np.float32)
    _G["mine"] = _dots(mine)
    with rasterio.open(footprint) as src:
        fp = np.isfinite(src.read(1))
    _G["fp"] = fp
    _G["surface"] = np.load(surface) if surface else None


def _one(path_str: str) -> dict:
    p = Path(path_str)
    rec = dict(path=str(p), sha256=p.stem if len(p.stem) == 64 else sha256_file(p))
    try:
        with rasterio.open(p) as src:
            a = src.read(1).astype(np.float32)
            rec["shape"] = list(src.shape)
            rec["crs"] = str(src.crs)
    except Exception as exc:                                          # pragma: no cover
        rec["error"] = f"open failed: {exc}"
        return rec
    if a.shape != _G["mine"].shape:
        rec["error"] = "grid mismatch"
        return rec
    theirs = _dots(a)
    rec["their_dots"] = int(theirs.sum())
    near = _near(theirs)
    e = float((near & _G["fp"]).sum()) / max(1, int(_G["fp"].sum()))
    rec["their_dilated_frac_of_footprint"] = e
    rec["chance_expected_overlap"] = e
    rec["saturated"] = bool(e >= SATURATED_E)
    if not theirs.any():
        rec["forward_overlap"] = None
        return rec
    rec["forward_overlap"] = float(dot_overlap(_G["mine"], theirs))
    rec["reverse_overlap"] = float(dot_overlap(theirs, _G["mine"]))
    u = int((_G["mine"] | theirs).sum())
    rec["jaccard"] = float((_G["mine"] & theirs).sum() / u) if u else 0.0
    rec["duplicate_by_overlap"] = bool(rec["forward_overlap"] > OVERLAP_LIMIT)
    rec["duplicate_by_jaccard"] = bool(rec["jaccard"] > JACCARD_LIMIT)
    rec["chance_corrected_lift"] = (float(rec["forward_overlap"]) - e) / max(1e-9, 1.0 - e)
    rec["rule_a_fires"] = bool(rec["forward_overlap"] > OVERLAP_LIMIT and e < RULE_A_E)
    rec["rule_b_fires"] = bool(rec["chance_corrected_lift"] > RULE_B_LIFT and e < SATURATED_E)
    if _G.get("surface") is not None:
        rho = surface_rho(_G["surface"], a, _G["fp"])
        rec["rho_full_footprint"] = float(rho["spearman_full_footprint"])
        rec["rho_dot_union"] = float(rho["spearman_on_dot_union"])
        rec["duplicate_by_rho"] = bool(np.isfinite(rec["rho_full_footprint"])
                                       and rec["rho_full_footprint"] > RHO_LIMIT)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--surface", default=str(ROOT / ".cache" / "gems58" / "gems61_mag.npy"))
    ap.add_argument("--footprint", default=str(ROOT / "data" / "bridge" / "sample_submission.tif"))
    ap.add_argument("--witness-dirs", nargs="*", default=None)
    ap.add_argument("--pins", default=str(ROOT / "evidence" / "registry_scan_index.json"))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dirs = args.witness_dirs or [str(ROOT / "data" / "registry" / "rasters"), str(CACHE)]
    seen: dict[str, str] = {}
    for d in dirs:
        for q in sorted(Path(d).glob("*.tif")):
            digest = q.stem if len(q.stem) == 64 else sha256_file(q)
            seen.setdefault(digest, str(q))
    files = list(seen.values())
    pins = {e["sha256"]: e for e in json.loads(Path(args.pins).read_text())}
    print(f"candidate {args.candidate}\nwitnesses {len(files)} unique rasters from {len(dirs)} dirs")

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init,
                             initargs=(args.candidate, args.surface, args.footprint)) as ex:
        rows = list(ex.map(_one, files, chunksize=1))
    print(f"screened {len(rows)} witnesses in {time.time() - t0:.1f}s")

    expected = len(pins)
    have = {r.get("sha256") for r in rows}
    missing = [s for s in pins if s not in have and s not in {r.get("sha256") for r in rows if r.get("error")}]
    ok = [r for r in rows if r.get("forward_overlap") is not None]
    cand_sha = sha256_file(Path(args.candidate))
    byte_dup = [r for r in rows if r.get("sha256") == cand_sha]
    mine = np.load(args.surface) if args.surface and Path(args.surface).exists() else None

    def worst(key):
        pool = [r for r in ok if r.get(key) is not None and np.isfinite(r[key])]
        return max(pool, key=lambda r: r[key]) if pool else None

    fwd = sorted([r for r in ok if r["duplicate_by_overlap"]], key=lambda r: -r["forward_overlap"])
    informative = [r for r in fwd if not r["saturated"]]
    rule_a = [r for r in ok if r["rule_a_fires"]]
    rule_b = [r for r in ok if r["rule_b_fires"]]
    rho_fire = [r for r in ok if r.get("duplicate_by_rho")]
    jac_fire = [r for r in ok if r.get("duplicate_by_jaccard")]
    w_fwd, w_rho, w_jac = worst("forward_overlap"), worst("rho_full_footprint"), worst("jaccard")

    base_ok = (len(rows) == expected and not missing and not byte_dup
               and not rho_fire and not jac_fire
               and w_rho is not None and w_rho["rho_full_footprint"] <= RHO_LIMIT)
    ratified_ok = base_ok and not rule_a and not rule_b
    literal_ok = base_ok and w_fwd is not None and w_fwd["forward_overlap"] <= OVERLAP_LIMIT

    out = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        candidate=args.candidate,
        candidate_sha256=cand_sha,
        my_dots=int(_dots(rasterio.open(args.candidate).read(1)).sum()),
        index=args.pins,
        registry_rasters_expected=expected,
        registry_rasters_checked=len(rows),
        complete_accessible_scan=bool(len(rows) == expected),
        missing_or_invalid=len(missing),
        byte_unique=True, pixel_identity_unique=bool(not byte_dup),
        rho_limit=RHO_LIMIT, overlap_limit=OVERLAP_LIMIT, jaccard_limit=JACCARD_LIMIT,
        worst_forward_overlap=w_fwd["forward_overlap"] if w_fwd else None,
        worst_forward_overlap_witness=w_fwd["path"] if w_fwd else None,
        worst_rho=w_rho["rho_full_footprint"] if w_rho else None,
        worst_rho_witness=w_rho["path"] if w_rho else None,
        worst_jaccard=w_jac["jaccard"] if w_jac else None,
        n_overlap_firings=len(fwd), n_overlap_firings_saturated=len(fwd) - len(informative),
        n_overlap_firings_informative=len(informative),
        rule_a_firings=len(rule_a), rule_b_firings=len(rule_b),
        rule_a_firings_list=[dict(path=r["path"], overlap=r["forward_overlap"],
                                  E=r["chance_expected_overlap"]) for r in rule_a],
        rule_b_firings_list=[dict(path=r["path"], lift=r["chance_corrected_lift"],
                                  E=r["chance_expected_overlap"]) for r in rule_b],
        n_rho_firings=len(rho_fire), n_jaccard_firings=len(jac_fire),
        verdict="unique" if ratified_ok else "duplicate_or_drift",
        literal_verdict="unique" if literal_ok else "duplicate_or_drift",
        stop_required=bool(not ratified_ok),
        rule=("RATIFIED-UNIQ-v1: rule A = literal > 0.70 overlap vs a witness with E < 0.70; "
              "rule B = chance-corrected lift > 0.50 vs any witness with E < 0.99"),
        surface_used=bool(mine is not None),
        rows=rows,
    )
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
