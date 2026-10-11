#!/usr/bin/env python3
"""Deprecated private submission writer; intentionally disabled.

Use ``gems57.submission_writer.write_submission`` via the guarded ribbon
emission pipeline. Never use this script for a competition upload.
"""


def main() -> int:
    import sys
    print(
        "DEPRECATED/NO-GO: this script uses the legacy gems.submission writer. "
        "Use gems57.submission_writer only after all qualification gates pass.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
