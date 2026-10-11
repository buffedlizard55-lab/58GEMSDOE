#!/usr/bin/env bash
# Restore the organizer's 19-band numerical feature stack.
#
# The stack is 418,912,844 bytes, so it is not committed.  It is fetched from the
# hash-pinned community bridge (five GitHub-splittable parts) and verified against
# the sha256 recorded in that bridge's manifest:
#
#   4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5
#
# Transport provenance only: the bridge authenticates the bytes, not their origin.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${ROOT}/.cache/gems58"
mkdir -p "${DEST}"
cd "${DEST}"
if [ -f gems-geodawn-numerical-features.tif ] && \
   [ "$(sha256sum gems-geodawn-numerical-features.tif | cut -d' ' -f1)" = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5" ]; then
  echo "feature stack already present and verified"; exit 0
fi
if [ ! -f .bridge/manifest.json ]; then
  rm -rf .bridge
  git clone --depth 1 https://github.com/buffedlizard55-lab/5GEMSDOE.git .bridge
fi
cat .bridge/data/bridge/gems-geodawn-numerical-features.tif.part-00{0,1,2,3,4} \
  > gems-geodawn-numerical-features.tif
echo "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5  gems-geodawn-numerical-features.tif" \
  | sha256sum -c -
echo "ok: ${DEST}/gems-geodawn-numerical-features.tif"
