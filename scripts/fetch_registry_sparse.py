#!/usr/bin/env python3
"""Restore the pinned public registry rasters via git sparse clones (blob filter).

The GitHub REST API rate budget is shared across parallel sessions and was
exhausted at run time, so this tool fetches the same pinned bytes over the git
protocol instead: per sibling repo, ``git clone --depth 1 --filter=blob:none
--no-checkout`` + a no-cone sparse checkout restricted to the registry-listed
paths.  Every file is copied to ``.cache/registry/<sha256>.tif`` ONLY if its
SHA256 equals the pinned value; mismatches and missing files are recorded and
reported, never skipped silently (fail-closed, mirroring
``scripts/restore_registry_cache.py``).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "registry_refreshed.json"
CACHE = ROOT / ".cache" / "registry"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_repo(repo: str, paths: list[str]) -> dict:
    dest = Path("/tmp/reg") / repo
    t0 = time.time()
    try:
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none",
                            "--no-checkout", f"https://github.com/buffedlizard55-lab/{repo}.git",
                            str(dest)], capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return dict(repo=repo, ok=False, error=f"clone rc={r.returncode}: {r.stderr.strip()[:200]}")
        subprocess.run(["git", "sparse-checkout", "init", "--no-cone"], cwd=dest, check=True,
                       capture_output=True, text=True)
        r = subprocess.run(["git", "sparse-checkout", "set", "--no-cone", *paths], cwd=dest,
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return dict(repo=repo, ok=False, error=f"sparse set rc={r.returncode}: {r.stderr.strip()[:200]}")
        r = subprocess.run(["git", "checkout", "main"], cwd=dest, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return dict(repo=repo, ok=False, error=f"checkout rc={r.returncode}: {r.stderr.strip()[:200]}")
        return dict(repo=repo, ok=True, seconds=round(time.time() - t0, 1))
    except Exception as exc:  # noqa: BLE001
        return dict(repo=repo, ok=False, error=f"{type(exc).__name__}: {exc}")


def main() -> int:
    reg = json.loads(REGISTRY.read_text())
    rasters = reg["rasters"]
    CACHE.mkdir(parents=True, exist_ok=True)
    repo_paths: dict[str, set[str]] = {}
    for r in rasters:
        for s in r["sources"]:
            repo, _, path = s.partition(":")
            repo_paths.setdefault(repo, set()).add(path)

    repos = sorted(repo_paths)
    print(f"repos: {len(repos)}; rasters pinned: {len(rasters)}", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_repo, repo, sorted(repo_paths[repo])): repo for repo in repos}
        done = 0
        for fut in as_completed(futs):
            res = fut.result()
            results[res["repo"]] = res
            done += 1
            print(f"[{done}/{len(repos)}] {res['repo']}: ok={res['ok']} {res.get('seconds','')}"
                  f"{'' if res['ok'] else ' ERR ' + res.get('error','')[:120]}", flush=True)

    # verify + cache
    n_ok = n_mismatch = n_missing = 0
    per_raster = []
    for r in rasters:
        got = None
        err = None
        for s in r["sources"]:
            repo, _, path = s.partition(":")
            if not results.get(repo, {}).get("ok"):
                continue
            f = Path("/tmp/reg") / repo / path
            if f.is_file():
                got = f
                break
        if got is None:
            n_missing += 1
            per_raster.append(dict(sha256=r["sha256"], status="missing",
                                   sources=r["sources"]))
            continue
        digest = sha256_file(got)
        if digest != r["sha256"]:
            n_mismatch += 1
            per_raster.append(dict(sha256=r["sha256"], status="hash_mismatch",
                                   found=digest, source=s))
            continue
        out = CACHE / f"{digest}.tif"
        if not out.exists():
            shutil.copy2(got, out)
        n_ok += 1
        per_raster.append(dict(sha256=r["sha256"], status="ok", bytes=r["bytes"]))
    report = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        method="git sparse clone (blob:none) over github.com; sha256 verified before caching",
        registry_snapshot_sha256=hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
        pinned_rasters=len(rasters), restored=n_ok, missing=n_missing, hash_mismatch=n_mismatch,
        repos={k: {kk: vv for kk, vv in v.items() if kk != 'repo'} for k, v in results.items()},
        complete_accessible_scan=(n_missing == 0 and n_mismatch == 0),
        cache_dir=str(CACHE),
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    (ROOT / "evidence" / "registry_fetch_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"restored={n_ok} missing={n_missing} mismatch={n_mismatch} "
          f"complete={report['complete_accessible_scan']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
