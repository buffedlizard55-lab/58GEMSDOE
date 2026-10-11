#!/usr/bin/env python3
"""Package the session-6 GeoTIFF as a one-TIFF ZIP plus a download receipt.

The portal accepts a single-band GeoTIFF *or* a .zip containing exactly one
GeoTIFF; the ZIP is ~1000x smaller and is the safer upload. The receipt binds the
name, the note and both hashes to the bytes.
"""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "s6"

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def main() -> int:
    emit = json.loads((EV / "emit.json").read_text())
    tif = ROOT / "docs" / "downloads" / emit["file"]
    stem = tif.stem
    zpath = tif.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        info = zipfile.ZipInfo(tif.name, date_time=(2026, 10, 11, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, tif.read_bytes())
    with zipfile.ZipFile(zpath) as z:
        assert z.namelist() == [tif.name], z.namelist()
        assert z.read(tif.name) == tif.read_bytes()
    card = json.loads((EV / "run_card.json").read_text()) if (EV / "run_card.json").is_file() else {}
    receipt = dict(
        file=tif.name, sha256=sha(tif), bytes=tif.stat().st_size,
        zip_file=zpath.name, zip_sha256=sha(zpath), zip_bytes=zpath.stat().st_size,
        submission_name=stem, note=emit.get("note", ""),
        note_chars=len(emit.get("note", "")),
        n_dots=emit.get("n_dots"), validator_passed=emit.get("validator", {}).get("passed"),
        holdout_dti=emit.get("holdout", {}).get("dti"),
        evaluator=emit.get("holdout", {}).get("evaluator"),
        protocol=emit.get("holdout", {}).get("protocol"),
        withheld_positive_pixels=emit.get("holdout", {}).get("withheld_positive_pixels"),
        uniqueness_verdict=card.get("registry", {}).get("verdict"),
        run_card_verdict=card.get("verdict"),
        approved_for_weekly_slot=False, promoted=False, submission_slots_used=0,
        status=("local format/range preflight and registry screen only; organizer acceptance and "
                "slot approval are separate decisions and are not claimed"))
    (tif.with_suffix(".json")).write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps(receipt, indent=1))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
