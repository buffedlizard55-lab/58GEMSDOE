#!/usr/bin/env python3
"""Deprecated legacy inventory/leakage check; intentionally disabled.

It used the old ``gems.holdout`` fold constructor and a private canary helper.
Use the current ``gems57`` buffered holdout and shared evaluator instead.
"""


def main() -> int:
    import sys
    print(
        "DEPRECATED/NO-GO: scripts/check_data.py uses an old unbuffered fold and "
        "private canary path. Do not cite its output; use gems57 shared tools "
        "after current inputs and the feature-context buffer are verified.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
