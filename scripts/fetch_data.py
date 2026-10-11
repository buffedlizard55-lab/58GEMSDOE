"""Try to download the public competition files listed in the project brief.

Only public, unauthenticated links are attempted. DrivenData requires login, and this script
does NOT attempt to bypass it. Files that cannot be fetched must be placed in data/ by hand
by a registered participant. Every attempt is logged to data/fetch_log.json with the HTTP
status and sha256, so the result is auditable.
"""

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

# Links copied verbatim from the project brief (Dropbox, dl=1 for direct download).
SOURCES = {
    "example_submission.tif": "https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=1",
    "existing_faults.tif": "https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=1",
    "gems-geodawn-numerical-features.tif": "https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=1",
    "GEMS_96647.pdf": "https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=1",
}


def main() -> int:
    DATA.mkdir(exist_ok=True)
    log = {}
    ok = 0
    for name, url in SOURCES.items():
        dest = DATA / name
        if dest.exists():
            log[name] = {"status": "already_present"}
            ok += 1
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gems-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                h = hashlib.sha256()
                while chunk := r.read(1 << 20):
                    f.write(chunk)
                    h.update(chunk)
            log[name] = {"status": "downloaded", "sha256": h.hexdigest(), "url": url}
            ok += 1
        except (urllib.error.URLError, OSError) as e:
            if dest.exists():
                dest.unlink()
            log[name] = {"status": "failed", "error": str(e), "url": url}
    (DATA / "fetch_log.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    print(f"\n{ok}/{len(SOURCES)} files present. training_features/labels/sample_submission from "
          "DrivenData require a registered login: place them in data/ manually.")
    return 0 if ok == len(SOURCES) else 1


if __name__ == "__main__":
    sys.exit(main())
