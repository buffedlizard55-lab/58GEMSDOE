#!/usr/bin/env python3
"""Second reading of the uniqueness scan: how much of the flag is degeneracy?

The literal protocol gate is *forward* overlap:  share of MY dots within 3 px of
THEIR dots > 0.70.  A witness raster whose positive set covers essentially the
whole 5,167,373-pixel study footprint scores 1.00 against **every possible**
candidate, including a uniformly random one: there is nowhere left to stand that
is not within 3 px of one of its dots.  Such a witness carries no information
about duplication, so counting it as a duplicate silently forbids every future
submission.

This script does not re-scan rasters and does not change the gate.  It reads the
per-witness rows already produced by ``gems57.uniqueness.compare_array_to_registry``
and reports, for each flagged witness, whether its forward test is degenerate and
what the chance-corrected statistics say instead.
"""
from __future__ import annotations

import json
from pathlib import Path

from gems58w import grid as g58

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / "evidence" / "ribbon_v3" / "uniqueness_rows.json"
OUT = ROOT / "evidence" / "ribbon_v3" / "uniqueness_reading.json"
DENSE_FRAC = 0.50   # witness covers half or more of the footprint with dots


def main() -> None:
    rows = json.loads(ROWS.read_text())
    fp = int(g58.footprint().sum())
    flagged = [r for r in rows if (r.get("my_dots_within_3px_of_theirs") or 0) > 0.70]
    dense = [r for r in flagged if (r.get("their_dots") or 0) >= DENSE_FRAC * fp]
    sparse = [r for r in flagged if r not in dense]
    rep = dict(
        evidence_class="PUBLIC-SIBLING-INVENTORY",
        question=("of the witnesses flagged by the literal forward-overlap rule, how many are "
                  "dense rasters for which that rule is degenerate (it returns 1.00 for every "
                  "candidate, random or not)?"),
        footprint_pixels=fp,
        degenerate_threshold_frac_of_footprint=DENSE_FRAC,
        n_witnesses=len(rows),
        n_flagged_literal=len(flagged),
        n_flagged_degenerate=len(dense),
        n_flagged_informative=len(sparse),
        worst_spearman_among_flagged=max((r.get("spearman_full_footprint") or 0)
                                         for r in flagged) if flagged else None,
        worst_jaccard_among_flagged=max((r.get("jaccard_dot_sets") or 0)
                                        for r in flagged) if flagged else None,
        worst_spearman_among_informative_flagged=(
            max((r.get("spearman_full_footprint") or 0) for r in sparse) if sparse else None),
        worst_jaccard_among_informative_flagged=(
            max((r.get("jaccard_dot_sets") or 0) for r in sparse) if sparse else None),
        informative_flagged=[dict(repo=r.get("repo"),
                                  submission=r.get("submission"),
                                  their_dots=r.get("their_dots"),
                                  forward=round(r.get("my_dots_within_3px_of_theirs"), 4),
                                  jaccard=round(r.get("jaccard_dot_sets") or 0, 4),
                                  spearman=round(r.get("spearman_full_footprint") or 0, 4))
                             for r in sorted(sparse, key=lambda x: -(x.get("jaccard_dot_sets") or 0))[:20]],
        degenerate_examples=[dict(repo=r.get("repo"), submission=r.get("submission"),
                                  their_dots=r.get("their_dots"),
                                  coverage=round((r.get("their_dots") or 0) / fp, 4),
                                  forward=round(r.get("my_dots_within_3px_of_theirs"), 4),
                                  jaccard=round(r.get("jaccard_dot_sets") or 0, 4))
                             for r in dense[:10]],
        reading=("Under the literal rule the artifact is a duplicate of "
                 f"{len(flagged)} witnesses. {len(dense)} of them are dense rasters whose dots "
                 f"cover >= {DENSE_FRAC:.0%} of the study footprint, so their forward test is "
                 "1.00 for every candidate and cannot discriminate. The remaining "
                 f"{len(sparse)} are informative; against them the worst dot-set Jaccard is "
                 "reported above. Deciding whether to treat the degenerate witnesses as "
                 "duplicates is the owner's call, not a measurement this script can make."))
    OUT.write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: rep[k] for k in ("n_flagged_literal", "n_flagged_degenerate",
                                          "n_flagged_informative",
                                          "worst_jaccard_among_flagged",
                                          "worst_spearman_among_flagged",
                                          "worst_jaccard_among_informative_flagged",
                                          "worst_spearman_among_informative_flagged")}, indent=1))


if __name__ == "__main__":
    main()
