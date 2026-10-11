#!/usr/bin/env python3
"""DEPRECATED/NO-GO: do not generate the legacy catalogue-boundary diagnostic.

The former implementation sampled 15,000 pixels from a 3x3 dilation of the
complete mapped-fault catalogue. It was not a ribbon-width/localization-error
experiment, did not use the cached feature stack or blocked hide-and-recover
holdout, and its filename/note made unsupported uniqueness claims. The emitted
file is retained only as a negative review artifact. This command now exits
without creating or changing any file.

See ``docs/REVIEW_20261011.md`` and ``evidence/58gemsdoe_unique_ribbon/run_card.json``.
"""

import sys


def main() -> int:
    print(
        "DEPRECATED/NO-GO: this legacy generator is disabled. It sampled mapped "
        "catalogue boundaries and cannot produce a ribbon-lane submission. "
        "No TIFF, ZIP, receipt, or run card was written. See the review and run card."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
