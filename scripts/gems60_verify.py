#!/usr/bin/env python3
"""Independent verification of the delivered GeoTIFF (no writer code involved).

Checks, from the bytes on disk only:

* sha256, byte size, single band, ``float32``, CRS EPSG:32611, shape and
  geotransform identical to the official ``sample_submission.tif``;
* every value finite and inside [0, 1] (the portal's own rule; the value set is
  checked to be exactly {0.0, 1.0});
* zero positive mass outside the study footprint and zero positive mass on the
  mapped catalogue (the organizer masks those pixels out of scoring);
* the ZIP twin contains exactly the same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tif")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    tif = Path(args.tif)
    sample = ROOT / "data" / "official" / "sample_submission.tif"
    faults = ROOT / "data" / "official" / "existing_faults.tif"

    checks: list[tuple[str, bool, str]] = []
    with rasterio.open(tif) as src, rasterio.open(sample) as ref:
        a = src.read(1)
        pred = src.read(1, masked=False)
        checks.append(("single band", src.count == 1, f"count={src.count}"))
        checks.append(("float32", src.dtypes[0] == "float32", f"dtype={src.dtypes[0]}"))
        checks.append(("crs matches sample", str(src.crs) == str(ref.crs), f"{src.crs} vs {ref.crs}"))
        checks.append(("shape matches sample", src.shape == ref.shape, f"{src.shape} vs {ref.shape}"))
        checks.append(("transform matches sample", src.transform == ref.transform,
                       f"{src.transform} vs {ref.transform}"))
        checks.append(("finite everywhere", bool(np.isfinite(a).all()),
                       f"non-finite={int((~np.isfinite(a)).sum())}"))
        checks.append(("values in [0,1]", bool((a >= 0).all() and (a <= 1).all()),
                       f"min={float(a.min())} max={float(a.max())}"))
        uniq = np.unique(a)
        checks.append(("binary values", bool(uniq.size == 2 and uniq[0] == 0.0 and uniq[1] == 1.0),
                       f"unique={uniq.tolist()}"))
        with rasterio.open(sample) as sref:
            fp = np.isfinite(sref.read(1))
        with rasterio.open(faults) as fref:
            cat = fref.read(1) == 1
        pos = a > 0
        checks.append(("no positive mass outside the footprint", bool(not (pos & ~fp).any()),
                       f"positives outside={int((pos & ~fp).sum())}"))
        checks.append(("no positive mass on the mapped catalogue", bool(not (pos & cat).any()),
                       f"positives on catalogue={int((pos & cat).sum())}"))
        checks.append(("positive support inside the footprint", bool(pos.any()),
                       f"n_positives={int(pos.sum())}"))
        n_pos = int(pos.sum())
        del a, pred

    zpath = tif.with_suffix(".zip")
    if zpath.exists():
        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            same = names == [tif.name] and z.read(tif.name) == tif.read_bytes()
        checks.append(("zip twin contains exactly this TIFF", bool(same), f"names={names}"))
    else:
        checks.append(("zip twin present", False, "missing"))

    receipt = dict(
        file=tif.name, sha256=sha256(tif), bytes=tif.stat().st_size, n_positives=n_pos,
        checks=[dict(name=n, ok=bool(ok), detail=d) for n, ok, d in checks],
        passed=int(sum(1 for _, ok, _ in checks if ok)), total=len(checks),
        verdict="LOCAL FORMAT OK" if all(ok for _, ok, _ in checks) else "FORMAT PROBLEM",
        caveat=("local format validity is not organizer acceptance, not a uniqueness "
                "clearance outside the screened inventory, and not a score"),
    )
    if args.out:
        Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n")
    for n, ok, d in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n:44s} {d}")
    print(f"{receipt['verdict']}: {receipt['passed']}/{receipt['total']} checks, "
          f"{receipt['n_positives']} positive pixels, sha256 {receipt['sha256']}")
    return 0 if receipt["passed"] == receipt["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
