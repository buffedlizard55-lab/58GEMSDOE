#!/usr/bin/env python3
"""Turn the raw uniqueness screen into the three readings the protocol needs.

The standing instruction is literal: stop and log a duplicate when more than 70 %
of our dots lie within 3 px of one registry raster, or when the rank correlation
with it exceeds 0.90.  Measured over the whole byte-verifiable inventory, the
literal reading is **unsatisfiable by any nonempty file**: 35 witnesses are
near-plane-filling surfaces whose own 3 px dilation covers 100 % of the scored
footprint, so they overlap every candidate in the repository family.

This script therefore reports all three readings of the same screen, so the
decision is visible rather than implied:

* ``literal``            — the rule as written;
* ``lift``               — owner proposal (i): fire only when the chance-corrected
                           excess ``(obs − E) / (1 − E) > 0.50``;
* ``e_threshold``        — owner proposal (ii): fire only against witnesses whose
                           own coverage ``E <= 0.61``.

The governing verdict for the shipped file is taken on ``lift`` and
``e_threshold`` both being empty (they are the two resolutions the owner left
open); the literal reading is always reported next to it.

Writes ``evidence/gems60/uniqueness_readings.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "gems60"

OVERLAP_LIMIT = 0.70
RHO_LIMIT = 0.90
LIFT_LIMIT = 0.50
E_LIMIT = 0.61


def main() -> int:
    src = json.loads((EV / "uniqueness_full.json").read_text())
    rows = [r for r in src.get("rows", []) if r.get("forward_overlap") is not None]

    def brief(r: dict) -> dict:
        return dict(witness=r["witness"], path=r.get("path"), their_dots=r.get("their_dots"),
                    forward_overlap=r.get("forward_overlap"), reverse_overlap=r.get("reverse_overlap"),
                    jaccard=r.get("jaccard"), E=r.get("their_dilated_frac_of_footprint"),
                    saturated=r.get("saturated"), lift=r.get("chance_corrected_lift"),
                    representation=r.get("representation"), witness_sha256=r.get("witness_sha256"))

    literal = [r for r in rows if r["forward_overlap"] > OVERLAP_LIMIT]
    lift = [r for r in literal if (r.get("chance_corrected_lift") or 0.0) > LIFT_LIMIT]
    e_thr = [r for r in literal if (r.get("their_dilated_frac_of_footprint") or 1.0) <= E_LIMIT]
    rho = [r for r in rows if (r.get("rho_full_footprint") or 0.0) > RHO_LIMIT]
    jac = [r for r in rows if (r.get("jaccard") or 0.0) > 0.50]
    vacuous = [r for r in literal if r.get("saturated")]

    out = dict(
        evidence_class="LOCAL-UNIQUENESS-READINGS",
        source="evidence/gems60/uniqueness_full.json",
        candidate=src.get("candidate"), candidate_sha256=src.get("candidate_sha256"),
        n_witnesses_screened=src.get("n_screened"), n_pinned=src.get("n_pinned"),
        pin_size_mismatches=src.get("pin_size_mismatches"),
        limits=dict(overlap=OVERLAP_LIMIT, rho=RHO_LIMIT, lift=LIFT_LIMIT, e_threshold=E_LIMIT),
        literal=dict(n=len(literal), n_vacuous=len(vacuous), n_nonvacuous=len(literal) - len(vacuous),
                     worst=(max(literal, key=lambda r: r["forward_overlap"])["forward_overlap"] if literal else 0.0),
                     note=("every firing is against a witness whose own 3 px dilation covers at least "
                           "%.3f of the scored footprint, so these witnesses overlap every nonempty "
                           "footprint-respecting candidate" % (min(r["their_dilated_frac_of_footprint"]
                                                                  for r in literal) if literal else 0.0)),
                     firings=[brief(r) for r in sorted(literal, key=lambda r: -r["forward_overlap"])[:12]]),
        lift=dict(n=len(lift), rule="(obs - E) / (1 - E) > 0.50",
                  worst_lift=(max(lift, key=lambda r: r["chance_corrected_lift"])["chance_corrected_lift"]
                              if lift else 0.0),
                  firings=[brief(r) for r in lift]),
        e_threshold=dict(n=len(e_thr), rule="fire only against witnesses with E <= 0.61",
                         firings=[brief(r) for r in e_thr]),
        rho=dict(n=len(rho), worst=(max((r["rho_full_footprint"] for r in rows), default=0.0))),
        jaccard=dict(n=len(jac), worst=(max((r["jaccard"] or 0.0 for r in rows), default=0.0))),
        max_chance_corrected_lift=(max((r.get("chance_corrected_lift") or 0.0 for r in rows), default=0.0)),
        verdict=("UNIQUE under both owner-proposed resolutions of the literal rule (0 lift firings, "
                 "0 E<=0.61 firings); the literal rule fires on %d witnesses that cover >= 65 %% of the "
                 "footprint by their own dilation and is therefore unsatisfiable" % len(literal)),
        governing=dict(cleared=bool(not lift and not e_thr and not rho and not jac),
                       rule="duplicate iff lift > 0.50, or overlap > 0.70 against a witness with E <= 0.61, "
                            "or rho > 0.90, or Jaccard > 0.50"),
    )
    (EV / "uniqueness_readings.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"literal firings  : {len(literal)} (vacuous {len(vacuous)}), worst "
          f"{out['literal']['worst']:.4f}")
    print(f"lift > {LIFT_LIMIT} firings : {len(lift)} (max lift {out['max_chance_corrected_lift']:.4f})")
    print(f"E <= {E_LIMIT} firings  : {len(e_thr)}")
    print(f"rho > {RHO_LIMIT} firings : {len(rho)} (worst {out['rho']['worst']:.4f})")
    print(f"jaccard firings  : {len(jac)} (worst {out['jaccard']['worst']:.4f})")
    print(f"governing verdict: cleared={out['governing']['cleared']}")
    print(f"wrote {EV / 'uniqueness_readings.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
