#!/usr/bin/env python3
"""Build a freshness delta for the registry witness inventory.

``registry/registry_refreshed.json`` is the pinned historical inventory (695
sha256s over 57 sibling repos, generated 2026-10-10).  The clones under
``/tmp/reg`` are the repos' **current** default branches, so they can contain
grid-format TIFs that the pinned inventory never saw.  This script finds them,
sha256-verifies them, keeps only files that are on the competition grid, and
writes a merged inventory:

    registry/registry_merged.json = pinned 695 + current-tree delta
    .cache/registry/<sha256>.tif  = byte-verified witness cache (both sources)

Fail-closed by construction: a file is only added as a witness if it opens as a
single-band raster whose shape, CRS and affine transform match
``data/bridge/sample_submission.tif`` exactly.

    python3 scripts/registry_delta_inventory.py [--clones /tmp/reg]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]
PINNED = ROOT / "registry" / "registry_refreshed.json"
MERGED = ROOT / "registry" / "registry_merged.json"
CACHE = ROOT / ".cache" / "registry"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grid_match(p: Path, ref: dict) -> tuple[bool, str]:
    try:
        with rasterio.open(p) as s:
            if s.count != 1:
                return False, "bands=%d" % s.count
            if (s.height, s.width) != (ref["height"], ref["width"]):
                return False, "shape=%d,%d" % (s.height, s.width)
            if str(s.crs) != ref["crs"]:
                return False, "crs=%s" % s.crs
            if [round(v, 6) for v in s.transform[:6]] != ref["transform"]:
                return False, "transform-mismatch"
            return True, "ok"
    except Exception as exc:  # noqa: BLE001 - unreadable files are reported, never guessed
        return False, "unreadable:%s" % str(exc)[:60]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clones", default="/tmp/reg", type=Path)
    args = ap.parse_args()

    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as s:
        ref = dict(height=s.height, width=s.width, crs=str(s.crs),
                   transform=[round(v, 6) for v in s.transform[:6]])

    pinned = json.loads(PINNED.read_text())
    pinned_shas = {r["sha256"]: r for r in pinned["rasters"]}
    known = set(pinned_shas)
    print(f"[pinned] {len(pinned_shas)} rasters over {len(pinned['repos_scanned'])} repos",
          flush=True)

    delta: list[dict] = []
    seen_paths = 0
    rejected: dict[str, int] = {}
    own_roots = [ROOT / "docs" / "downloads", ROOT / "docs" / "ribbon" / "downloads",
                 ROOT / "evidence", ROOT / "data" / "registry" / "rasters"]
    candidates = sorted(args.clones.rglob("*.tif"))
    for r in own_roots:
        candidates += sorted(r.rglob("*.tif"))
    for tif in candidates:
        seen_paths += 1
        ok, why = grid_match(tif, ref)
        if not ok:
            rejected[why.split(":")[0]] = rejected.get(why.split(":")[0], 0) + 1
            continue
        h = sha256(tif)
        if h in known:
            continue
        known.add(h)
        try:
            rel = tif.relative_to(args.clones)
            repo = rel.parts[0]
            inner = str(rel.relative_to(Path(repo)))
            commit = head_commit(args.clones / repo)
        except ValueError:                       # this repo's own working tree
            repo = "58GEMSDOE(this-repo)"
            inner = str(tif.relative_to(ROOT))
            rel = Path("OWN") / inner
            commit = head_commit(ROOT)
        delta.append(dict(sha256=h, bytes=tif.stat().st_size, blob=None,
                          cache_file=f".cache/registry/{h}.tif",
                          sources=[f"{repo}:{inner}"], repo_first=repo,
                          source_commit=commit,
                          provenance="current-default-branch-delta",
                          observed_utc=fetched_at(tif)))
        CACHE.mkdir(parents=True, exist_ok=True)
        dest = CACHE / f"{h}.tif"
        if not dest.exists():
            shutil.copy2(tif, dest)
        if sha256(dest) != h:
            raise SystemExit(f"cache copy failed sha256 verification: {dest}")
        print(f"[delta] + {repo}:{inner} sha256={h[:12]} {tif.stat().st_size} B", flush=True)

    merged = dict(
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        basis=dict(pinned=str(PINNED.relative_to(ROOT)), pinned_generated=pinned.get("generated_utc"),
                   pinned_rasters=len(pinned_shas), clones=str(args.clones),
                   tif_paths_seen=seen_paths, rejected=rejected),
        rasters=list(pinned["rasters"]) + delta,
        repos_scanned=pinned["repos_scanned"],
        counts=dict(pinned=len(pinned_shas), delta=len(delta), total=len(pinned_shas) + len(delta)),
    )
    MERGED.write_text(json.dumps(merged, indent=1) + "\n")
    n_cache = len(list(CACHE.glob("*.tif")))
    print(f"[merged] pinned {len(pinned_shas)} + delta {len(delta)} = {len(merged['rasters'])} "
          f"witnesses -> {MERGED.relative_to(ROOT)}", flush=True)
    print(f"[cache] {n_cache} byte-verified rasters in {CACHE.relative_to(ROOT)}; "
          f"complete={n_cache >= len(merged['rasters'])}", flush=True)
    return 0


def head_commit(repo: Path) -> str:
    git = repo / ".git"
    if not git.exists():
        return "unknown"
    head = (git / "HEAD").read_text().strip()
    if head.startswith("ref: "):
        ref = git / head[5:]
        return ref.read_text().strip() if ref.exists() else head
    return head


def fetched_at(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
