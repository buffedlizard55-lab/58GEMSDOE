"""Filesystem layout for the ribbon-width lane (package ``gems58w``).

Outputs are namespaced (``evidence/ribbon``, ``registry/ribbon``, ``docs/ribbon``) so this lane
can live beside the other lanes' artifacts in the shared repository.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Official competition inputs.  See ``data/README.md`` for provenance pins.
OFFICIAL = ROOT / "data" / "official"
#: Prior submission rasters used by the uniqueness screen.
REGISTRY = ROOT / "data" / "registry" / "rasters"
#: Third-party (free, official) external rasters.
EXTERNAL = ROOT / "data" / "external"
EVIDENCE = ROOT / "evidence" / "ribbon"
REGISTRY_META = ROOT / "registry" / "ribbon"
DOCS = ROOT / "docs" / "ribbon"
DOWNLOADS = DOCS / "downloads"


def feature_stack() -> Path:
    """Path to the 19-band GeoDAWN numerical feature stack.

    Resolved, in order, from ``GEMS_FEATURE_STACK``, ``data/official/`` and
    ``.cache/gems58/``.  The file is 419 MB, so it is *not* committed; run
    ``bash scripts/ribbon_fetch_features.sh`` to restore it (git-lfs-free, splits of
    the bridge mirror, sha256-pinned).
    """
    env = os.environ.get("GEMS_FEATURE_STACK")
    if env:
        return Path(env).expanduser()
    for cand in (
        OFFICIAL / "training_features.tif",
        ROOT / ".cache" / "gems58" / "gems-geodawn-numerical-features.tif",
    ):
        if cand.exists():
            return cand
    return ROOT / ".cache" / "gems58" / "gems-geodawn-numerical-features.tif"


def cache_dir() -> Path:
    d = ROOT / ".cache" / "gems58"
    d.mkdir(parents=True, exist_ok=True)
    return d


def evidence_dir() -> Path:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    return EVIDENCE


def downloads_dir() -> Path:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    return DOWNLOADS
