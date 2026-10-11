#!/usr/bin/env python3
"""Deprecated partial-registry checker; intentionally disabled.

Use ``scripts/check_uniqueness_registry.py`` with the shared gems57 literal gate
and an explicitly refreshed inventory. A curated local clone directory cannot
clear the complete/current scope requirement.
"""


def main() -> int:
    import sys
    print(
        "DEPRECATED/NO-GO: the gems58 checker used a private, partial-registry path. "
        "Refresh the inventory and use scripts/check_uniqueness_registry.py with "
        "gems57.uniqueness for the literal pre-placement and final-dot phases.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
