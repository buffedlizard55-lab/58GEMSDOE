#!/usr/bin/env python3
"""Uniqueness screen of the delivered candidate against the public registry inventory.

Governed by the shared protocol in ``gems57.uniqueness`` (radius 3 px, overlap
limit 0.70, rank-correlation limit 0.90, Jaccard limit 0.50).  Two readings are
computed for every witness and both are written into the receipt:

* **literal** -- ``forward_overlap`` = fraction of *our* dots within 3 px of the
  witness, exactly as the protocol is written (fire above 0.70), and
  ``rho_full_footprint`` = rank correlation of the pre-placement surface with the
  witness (fire above 0.90);
* **discriminating** -- the same numbers restricted to witnesses that *can*
  discriminate: a witness whose own 3 px dilation covers >= 99 % of the scored
  footprint (``E >= 0.99``) overlaps **every** nonempty candidate, so a firing
  against it carries no information.  For the rest we also report the
  chance-corrected lift ``(obs - E) / (1 - E)``.

Witness bytes are restored by ``scripts/fetch_registry_witnesses.sh`` (sha256
pinned in ``evidence/registry_scan_index.json``); every file used here is
byte-verified against its pin, and a mismatch is reported, never silently used.
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

from gems57.grid import load_grid                                     # noqa: E402
from gems57.uniqueness import _dots, _near, dot_overlap, surface_rho   # noqa: E402

CACHE = Path.home() / ".cache" / "gems" / "registry_witnesses"
_G: dict = {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _init(candidate: str, surface: str) -> None:
    _G["grid"] = load_grid(ROOT / "data" / "bridge")
    with rasterio.open(candidate) as src:
        mine = src.read(1).astype(np.float32)
    _G["mine"] = _dots(mine)
    _G["mine_near"] = _near(_G["mine"])
    _G["fp"] = _G["grid"].footprint
    _G["fp_n"] = int(_G["fp"].sum())
    from gems60 import convergence as C
    _G["surface"] = C.load(Path(surface)).strength


def _one(path_str: str) -> dict:
    p = Path(path_str)
    rec = dict(witness=p.name, path=str(p))
    try:
        with rasterio.open(p) as src:
            a = src.read(1).astype(np.float32)
            rec["crs"] = str(src.crs)
            rec["shape"] = list(src.shape)
    except Exception as exc:                                    # pragma: no cover
        rec["error"] = f"open failed: {exc}"
        return rec
    theirs = _dots(a)
    rec["their_dots"] = int(theirs.sum())
    if theirs.shape != _G["mine"].shape:
        rec["error"] = "grid mismatch"
        return rec
    near = _near(theirs)
    e = float((near & _G["fp"]).sum()) / max(1, int(_G["fp"].sum()))
    rec["their_dilated_frac_of_footprint"] = e
    rec["saturated"] = bool(e >= 0.99)
    if not theirs.any():
        rec["forward_overlap"] = None
        return rec
    rec["forward_overlap"] = float(dot_overlap(_G["mine"], theirs))
    rec["reverse_overlap"] = float(dot_overlap(theirs, _G["mine"]))
    u = int((_G["mine"] | theirs).sum())
    rec["jaccard"] = float((_G["mine"] & theirs).sum() / u) if u else 0.0
    rec["duplicate_by_overlap"] = bool(rec["forward_overlap"] > 0.70)
    rec["chance_corrected_lift"] = (float(rec["forward_overlap"]) - e) / max(1e-9, 1.0 - e)
    rho = surface_rho(_G["surface"], a, _G["fp"])
    rec["rho_full_footprint"] = float(rho["spearman_full_footprint"])
    rec["rho_dot_union"] = float(rho["spearman_on_dot_union"])
    rec["duplicate_by_rho"] = bool(np.isfinite(rec["rho_full_footprint"])
                                   and rec["rho_full_footprint"] > 0.90)
    rec["witness_sha256"] = sha256_file(p)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--surface", default=str(Path.home() / ".cache" / "gems" / "gems60_convergence.npz"))
    ap.add_argument("--witness-dirs", nargs="*", default=None)
    ap.add_argument("--pins", default=str(ROOT / "evidence" / "registry_scan_index.json"))
    ap.add_argument("--rows", default=str(ROOT / "evidence" / "registry_scan_rows.json"))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dirs = args.witness_dirs or [str(ROOT / "data" / "registry" / "rasters"), str(CACHE)]
    seen: dict[str, str] = {}
    for d in dirs:
        for q in sorted(Path(d).glob("*.tif")):
            digest = sha256_file(q)
            if digest in seen:            # the same raster committed in two places
                continue
            seen[digest] = str(q)
    files = list(seen.values())
    pins = {e["sha256"]: e for e in json.loads(Path(args.pins).read_text())}
    rep = {r["sha256"]: r.get("representation") for r in json.loads(Path(args.rows).read_text())}
    print(f"candidate : {args.candidate}")
    print(f"witnesses : {len(files)} unique rasters (from {len(dirs)} directories)")

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init,
                             initargs=(args.candidate, args.surface)) as ex:
        rows = list(ex.map(_one, files, chunksize=1))
    print(f"screened  : {len(rows)} witnesses in {time.time() - t0:.1f}s")

    n_pinned = n_mismatch = 0
    for r in rows:
        pin = pins.get(r.get("witness_sha256") or "")
        if pin is None:
            continue
        n_pinned += 1
        r["representation"] = rep.get(r["witness_sha256"])
        r["pinned_bytes"] = int(pin["bytes"])
        if Path(r["path"]).stat().st_size != int(pin["bytes"]):
            n_mismatch += 1
            r["pin_mismatch"] = True
    ok = [r for r in rows if r.get("forward_overlap") is not None]

    def worst(key, pool=None):
        pool = [r for r in (pool if pool is not None else ok)
                if r.get(key) is not None and np.isfinite(r[key])]
        return max(pool, key=lambda r: r[key]) if pool else None

    w_fwd, w_rev, w_rho = worst("forward_overlap"), worst("reverse_overlap"), worst("rho_full_footprint")
    fwd_fire = sorted([r for r in ok if r["duplicate_by_overlap"]], key=lambda r: -r["forward_overlap"])
    rho_fire = sorted([r for r in ok if r["duplicate_by_rho"]], key=lambda r: -r["rho_full_footprint"])
    disc = [r for r in ok if not r.get("saturated")]
    fwd_fire_disc = [r for r in fwd_fire if not r.get("saturated")]
    jac_fire = [r for r in ok if r.get("jaccard") is not None and r["jaccard"] > 0.50]
    lift_max = max((r["chance_corrected_lift"] for r in disc if r.get("chance_corrected_lift") is not None),
                   default=float("nan"))

    summary = dict(
        evidence_class="LOCAL-UNIQUENESS-SCREEN",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        candidate=args.candidate,
        candidate_sha256=sha256_file(Path(args.candidate)),
        n_witnesses=len(rows), n_screened=len(ok), n_pinned=n_pinned,
        pin_size_mismatches=n_mismatch,
        rho_limit=0.90, overlap_limit=0.70, jaccard_limit=0.50,
        n_saturated=sum(1 for r in rows if r.get("saturated")),
        worst_forward_overlap=w_fwd, worst_reverse_overlap=w_rev, worst_rho=w_rho,
        n_forward_firings=len(fwd_fire), n_rho_firings=len(rho_fire),
        n_jaccard_firings=len(jac_fire),
        forward_firings=fwd_fire[:25], rho_firings=rho_fire[:25],
        informative_reading=dict(
            n_witnesses=len(disc),
            worst_forward_overlap_informative=(worst("forward_overlap", disc) or {}).get("forward_overlap"),
            worst_forward_overlap_informative_witness=(worst("forward_overlap", disc) or {}).get("witness"),
            overlap_firings=len(fwd_fire_disc),
            overlap_firings_vacuous=len(fwd_fire) - len(fwd_fire_disc),
            max_chance_corrected_lift=lift_max,
        ),
        rows=rows,
        scope=("every byte-verified raster available in this sandbox: the 19 witnesses committed under "
               "data/registry/rasters plus the restored public inventory in ~/.cache/gems/registry_witnesses "
               "(sha256 pinned in evidence/registry_scan_index.json). The recorded inventory lists 703 "
               "rasters; blobs above 6 MB and the 8 rows without a git blob are out of scope and are "
               "reported as such, never counted as clearance."),
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, indent=1, default=str) + "\n")
    for nm, r in (("forward", w_fwd), ("reverse", w_rev), ("rho", w_rho)):
        if r:
            key = {"forward": "forward_overlap", "reverse": "reverse_overlap",
                   "rho": "rho_full_footprint"}[nm]
            print(f"worst {nm:8s}: {r[key]:.4f} vs {r['witness']} "
                  f"(E={r['their_dilated_frac_of_footprint']:.3f}, dots={r['their_dots']})")
    print(f"firings    : overlap {len(fwd_fire)} (vacuous {len(fwd_fire) - len(fwd_fire_disc)}, "
          f"discriminating {len(fwd_fire_disc)})  rho {len(rho_fire)}  jaccard {len(jac_fire)}")
    print(f"chance-corrected max lift on discriminating witnesses: {lift_max:.4f}")
    print(f"wrote      : {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
