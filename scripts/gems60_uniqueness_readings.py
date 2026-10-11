#!/usr/bin/env python3
"""Turn the raw uniqueness screen into the readings the ratified protocol needs.

The standing instruction was literal: stop and log a duplicate when more than 70 %
of our dots lie within 3 px of one registry raster, or when the rank correlation
with it exceeds 0.90.  Measured over the whole byte-verifiable inventory, the
literal reading is **unsatisfiable by any nonempty file**: 35 witnesses are
near-plane-filling surfaces whose own 3 px dilation covers 100 % of the scored
footprint, so they overlap every candidate in the repository family.

Session 5 ratified **RATIFIED-UNIQ-v1** (``PROMPT.md`` item 1, IR-58-UNIQ-07):
a firing is *informative* only when

* **rule A** — literal forward 3 px overlap > 0.70 against a witness whose own
  chance-level expectation ``E`` is below 0.70; or
* **rule B** — chance-corrected lift ``(O − E) / (1 − E)`` above 0.50 against any
  witness whose ``E`` is below 0.99 (as ``E → 1`` the lift degenerates, the same
  saturation rationale as ``gems57.uniqueness.SATURATED_E``).

Bytes/pixels identical, rank correlation > 0.90 or dot-set Jaccard > 0.50 also
stop a file.  The pre-ratification readings are still computed and published
beside the governing verdict — the literal rule (all witnesses, with the vacuous
ones flagged) and the ``E <= 0.61`` variant — because they are part of the audit
trail and must never be deleted or silently down-weighted.

Writes ``evidence/gems60/uniqueness_readings.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence" / "gems60"

OVERLAP_LIMIT = 0.70
RHO_LIMIT = 0.90
LIFT_LIMIT = 0.50
JACCARD_LIMIT = 0.50
#: RATIFIED-UNIQ-v1 rule A: a witness below this coverage can actually fail to fire.
E_INFORMATIVE = 0.70
#: The pre-ratification variant the owner had proposed (kept for the audit trail).
E_STRICT = 0.61
#: Above this the witness's dilation covers the footprint and rule B degenerates.
E_SATURATED = 0.99


def label_index() -> dict[str, str]:
    """sha256 -> ``repo:path`` for the pinned inventory, when the index is present."""
    path = ROOT / "evidence" / "registry_scan_index.json"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for e in json.loads(path.read_text()):
        sha = e.get("sha256")
        src = (e.get("sources") or [None])[0]
        if sha and src:
            out[sha] = str(src)
    return out


def main() -> int:
    src = json.loads((EV / "uniqueness_full.json").read_text())
    rows = [r for r in src.get("rows", []) if r.get("forward_overlap") is not None]
    labels = label_index()

    def brief(r: dict) -> dict:
        return dict(
            witness=r["witness"], witness_sha256=r.get("witness_sha256"),
            source=(labels.get(r["witness"]) or labels.get(str(r["witness"]).removesuffix(".tif"))),
            their_dots=r.get("their_dots"),
            forward_overlap=r.get("forward_overlap"), reverse_overlap=r.get("reverse_overlap"),
            jaccard=r.get("jaccard"), E=r.get("their_dilated_frac_of_footprint"),
            saturated=r.get("saturated"), lift=r.get("chance_corrected_lift"),
            representation=r.get("representation"),
        )

    fwd = lambda r: r.get("forward_overlap") or 0.0
    cov = lambda r: r.get("their_dilated_frac_of_footprint") or 0.0
    lift_of = lambda r: r.get("chance_corrected_lift") or 0.0

    literal = [r for r in rows if fwd(r) > OVERLAP_LIMIT]
    vacuous = [r for r in literal if r.get("saturated") or cov(r) >= E_SATURATED]
    informative_pool = [r for r in rows if cov(r) < E_INFORMATIVE]
    rule_a = [r for r in informative_pool if fwd(r) > OVERLAP_LIMIT]
    rule_b = [r for r in rows if cov(r) < E_SATURATED and lift_of(r) > LIFT_LIMIT]
    e_strict = [r for r in rows if cov(r) <= E_STRICT and fwd(r) > OVERLAP_LIMIT]
    rho = [r for r in rows if (r.get("rho_full_footprint") or 0.0) > RHO_LIMIT]
    jac = [r for r in rows if (r.get("jaccard") or 0.0) > JACCARD_LIMIT]

    cleared = not (rule_a or rule_b or rho or jac)

    out = dict(
        evidence_class="LOCAL-UNIQUENESS-READINGS",
        rule_id="RATIFIED-UNIQ-v1",
        source="evidence/gems60/uniqueness_full.json",
        candidate=src.get("candidate"),
        candidate_sha256=src.get("candidate_sha256"),
        n_witnesses_screened=src.get("n_screened"),
        n_pinned=src.get("n_pinned"),
        pin_size_mismatches=src.get("pin_size_mismatches"),
        n_witnesses_with_E_below_rule_A=len(informative_pool),
        scan_note=("668 of 670 byte-available witnesses screened at pinned sha256; the inventory "
                   "kept growing during session 5 (703 rasters on main), so these firing counts are "
                   "a lower bound — every added witness can only add firings, never remove one."),
        limits=dict(overlap=OVERLAP_LIMIT, rho=RHO_LIMIT, lift=LIFT_LIMIT,
                    jaccard=JACCARD_LIMIT, e_rule_a=E_INFORMATIVE, e_strict_variant=E_STRICT,
                    e_saturated=E_SATURATED),
        rule_a=dict(n=len(rule_a), rule="forward 3 px overlap > 0.70 and witness E < 0.70",
                    worst=(max((fwd(r) for r in rule_a), default=0.0)),
                    firings=[brief(r) for r in sorted(rule_a, key=lambda r: -fwd(r))]),
        rule_b=dict(n=len(rule_b), rule="(obs - E) / (1 - E) > 0.50 against witnesses with E < 0.99",
                    worst_lift=(max((lift_of(r) for r in rule_b), default=0.0)),
                    firings=[brief(r) for r in sorted(rule_b, key=lambda r: -lift_of(r))]),
        literal=dict(n=len(literal), n_vacuous=len(vacuous), n_nonvacuous=len(literal) - len(vacuous),
                     rule="forward 3 px overlap > 0.70 against every screened witness (pre-ratification)",
                     worst=(max((fwd(r) for r in literal), default=0.0)),
                     note=("every literal firing is against a witness whose own 3 px dilation covers at "
                           "least %.3f of the scored footprint, so those witnesses overlap every "
                           "nonempty footprint-respecting candidate" %
                           (min((cov(r) for r in literal), default=0.0))),
                     firings=[brief(r) for r in sorted(literal, key=lambda r: -fwd(r))[:12]]),
        e_strict_variant=dict(n=len(e_strict), rule="fire only against witnesses with E <= 0.61 "
                                                    "(pre-ratification variant, kept for audit)",
                              firings=[brief(r) for r in e_strict]),
        rho=dict(n=len(rho), worst=(max((r.get("rho_full_footprint") or 0.0 for r in rows), default=0.0))),
        jaccard=dict(n=len(jac), worst=(max((r.get("jaccard") or 0.0 for r in rows), default=0.0))),
        max_chance_corrected_lift=max((lift_of(r) for r in rows), default=0.0),
        governing=dict(
            cleared=bool(cleared),
            rule=("duplicate iff rule A (forward overlap > 0.70 vs a witness with E < 0.70), or rule B "
                  "(lift > 0.50 vs a witness with E < 0.99), or rho > 0.90, or Jaccard > 0.50, or bytes/"
                  "pixels identical"),
            verdict=("UNIQUE under RATIFIED-UNIQ-v1" if cleared else
                     "DUPLICATE under RATIFIED-UNIQ-v1: %d rule-A firing(s), %d rule-B firing(s) — "
                     "stop and log, download for review only" % (len(rule_a), len(rule_b))),
        ),
    )
    (EV / "uniqueness_readings.json").write_text(json.dumps(out, indent=1, default=str) + "\n")

    print(f"screened           : {len(rows)} witnesses, {len(informative_pool)} with E < {E_INFORMATIVE}")
    print(f"rule A firings     : {len(rule_a)} (worst {out['rule_a']['worst']:.4f})")
    for r in out["rule_a"]["firings"]:
        print(f"    {r['witness'][:12]} fwd {r['forward_overlap']:.4f} E {r['E']:.4f} "
              f"lift {r['lift']:.4f}  {r['source']}")
    print(f"rule B firings     : {len(rule_b)} (max lift {out['max_chance_corrected_lift']:.4f})")
    print(f"literal firings    : {len(literal)} (vacuous {len(vacuous)}), worst "
          f"{out['literal']['worst']:.4f}")
    print(f"E <= {E_STRICT} variant  : {len(e_strict)} firings")
    print(f"rho / jaccard      : {len(rho)} / {len(jac)} (worst "
          f"{out['rho']['worst']:.4f} / {out['jaccard']['worst']:.4f})")
    print(f"governing verdict  : cleared={out['governing']['cleared']}  ({out['governing']['verdict']})")
    print(f"wrote {EV / 'uniqueness_readings.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
