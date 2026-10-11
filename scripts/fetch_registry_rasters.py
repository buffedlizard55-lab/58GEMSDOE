#!/usr/bin/env python3
"""Fetch every public GEMSDOE submission TIF (the "registry") for the duplicate check.

Source: GitHub REST API (api.github.com is on the sandbox allow-list). Lists every repo
owned by buffedlizard55-lab whose name matches \d*GEMSDOE\d*, walks each git tree, and
downloads each unique blob once. Output goes OUTSIDE the repo (default /tmp/registry) because
the registry is ~760 MB and must not be committed.

Usage:  python scripts/fetch_registry_rasters.py [--out /tmp/registry] [--workers 8]
Writes: <out>/index.json (repo, path, blob sha, size) and <out>/blobs/<sha>.tif
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import json
import re
import urllib.request
from pathlib import Path

OWNER = "buffedlizard55-lab"
API = "https://api.github.com"
NAME_RE = re.compile(r"\d*GEMSDOE\d*")


def api(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def list_repos() -> list[str]:
    names, page = [], 1
    while True:
        batch = api(f"{API}/users/{OWNER}/repos?per_page=100&page={page}")
        if not batch:
            return names
        names += [r["name"] for r in batch]
        page += 1


def index(out: Path) -> list[dict]:
    rows = []
    for repo in sorted(r for r in list_repos() if NAME_RE.fullmatch(r)):
        tree = api(f"{API}/repos/{OWNER}/{repo}/git/trees/HEAD?recursive=1")
        for node in tree.get("tree", []):
            p = node["path"]
            if p.lower().endswith(".tif") and not p.startswith("data/"):
                rows.append(dict(repo=repo, path=p, sha=node["sha"], size=node.get("size", 0)))
    (out / "index.json").write_text(json.dumps(rows, indent=1))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/registry")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    (out / "blobs").mkdir(parents=True, exist_ok=True)
    rows = index(out)
    unique: dict[str, dict] = {}
    for r in rows:
        unique.setdefault(r["sha"], r)
    print(f"{len(rows)} TIF entries, {len(unique)} unique blobs")
    # blobs are content-addressed; the repo name in the URL is only used to address the API
    jobs = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for sha, r in unique.items():
            dest = out / "blobs" / f"{sha}.tif"
            dest.parent.mkdir(exist_ok=True)
            jobs.append(ex.submit(_fetch, r["repo"], sha, dest))
        for j in cf.as_completed(jobs):
            j.result()
    print("done")


def _fetch(repo: str, sha: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    d = api(f"{API}/repos/{OWNER}/{repo}/git/blobs/{sha}")
    dest.write_bytes(base64.b64decode(d["content"]))


if __name__ == "__main__":
    main()
