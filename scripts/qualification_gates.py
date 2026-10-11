#!/usr/bin/env python3
"""Exact-candidate qualification gates for the ribbon lane (fail closed).

This module is the *pre-emission* contract: it validates a manually reviewed
``evidence/ribbon_qualification.json`` against the candidate bytes, the current
registry index, the freshness audit, the feature-alone leakage canary and a
shared-evaluator buffered holdout with a defensible 95% interval. It renders no
HTML; the public site is built by ``scripts/build_site.py``.

Every check fails closed. A stale or incomplete inventory, a literal overlap
trigger, a receipt that is not hash-bound to this candidate, or an interval that
is not produced by a declared physical-cluster method blocks emission.
"""
import hashlib
import html
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
RIB = EV / "ribbon"
DOCS = ROOT / "docs"
DL = DOCS / "downloads"

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
CANARY_LIMIT = 0.90
HOLDOUT_EVALUATOR = "gems57.evaluate_holdout"
HOLDOUT_VERSION = "gems57-pooled-hide-v2"
REQUIRED_GATES = ("G1", "G2P", "G3", "G4", "G5")
INFO_GATES = {"G2", "G5i", "G6"}

CSS = """
<style>
:root{color-scheme:light;--ink:#182432;--muted:#526171;--line:#d7dee6;--red:#a11212;--redbg:#fff5f5;--green:#1d7a45;--greenbg:#f2fbf5;--blue:#285b87;--gold:#85670f}
body{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);margin:0;background:#f6f8fa}
main{max-width:1120px;margin:0 auto;padding:1.25rem}header,section,article{background:#fff;border:1px solid var(--line);border-radius:10px;padding:1rem 1.2rem;margin:.8rem 0}
h1,h2,h3{line-height:1.2}h1{margin:.2rem 0 .6rem}h2{margin-top:1.7rem}nav{margin:.3rem 0 1rem}nav a{display:inline-block;margin:0 .8rem .35rem 0}a{color:#135d99}code{overflow-wrap:anywhere;background:#f1f4f7;padding:.08em .24em;border-radius:3px}
.banner{border:2px solid var(--red);background:var(--redbg);padding:1rem 1.2rem;border-radius:10px;margin:1rem 0}.banner.ok{border-color:var(--green);background:var(--greenbg)}
.pill{display:inline-block;padding:.1em .55em;border-radius:999px;font-size:.76rem;font-weight:750;color:#fff;white-space:nowrap}.pill.pass{background:var(--green)}.pill.fail{background:var(--red)}.pill.info{background:var(--blue)}.pill.warn{background:var(--gold)}
.gates{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:.7rem;margin:.8rem 0}.gate{border:1px solid var(--line);border-left:5px solid #888;border-radius:8px;padding:.7rem .8rem;background:#fff}.gate.pass{border-left-color:var(--green)}.gate.fail{border-left-color:var(--red)}.gate.info{border-left-color:var(--blue);background:#f5f9fc}.gate h3{font-size:1rem;margin:0 0 .35rem}.gate p{font-size:.9rem;margin:.35rem 0;color:#354454}
.actions{display:flex;gap:.65rem;flex-wrap:wrap;margin:1rem 0}.button{display:inline-block;border-radius:7px;background:var(--blue);color:#fff;padding:.65rem .95rem;text-decoration:none;font-weight:700}.button.review{background:var(--red)}.small{font-size:.88rem;color:var(--muted)}.callout{border-left:5px solid var(--gold);background:#fffbea;padding:.8rem 1rem;border-radius:5px;margin:1rem 0}.red-callout{border-left:5px solid var(--red);background:var(--redbg);padding:.8rem 1rem;border-radius:5px;margin:1rem 0}
table{border-collapse:collapse;width:100%;margin:.6rem 0 1rem;font-variant-numeric:tabular-nums}th,td{border:1px solid var(--line);padding:.5rem .6rem;text-align:left;vertical-align:top}th{background:#edf2f6}ul,ol{padding-left:1.35rem}footer{border-top:1px solid var(--line);margin-top:2rem;padding-top:.7rem;color:var(--muted);font-size:.84rem}
@media(max-width:600px){main{padding:.7rem}header,section,article{padding:.8rem}.button{width:100%;text-align:center}}
</style>
"""


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def fmt(value, digits: int = 4, dash: str = "not measured") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return dash if value is None else esc(value)
    if not math.isfinite(number):
        return "undefined"
    return f"{number:.{digits}f}"


def table(headers: list[str], rows: list[list], cls: str = "") -> str:
    thead = "".join(f"<th>{esc(head)}</th>" for head in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<table class="{esc(cls)}"><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table>'


def _is_sha256(value) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _receipt_file_ok(record: dict) -> bool:
    """Require a qualification sub-gate to point at a hash-matching local receipt."""
    if not isinstance(record, dict) or not _is_sha256(record.get("receipt_sha256")):
        return False
    path_value = record.get("receipt_path")
    if not path_value:
        return False
    path = Path(str(path_value))
    if not path.is_absolute():
        path = ROOT / path
    try:
        path = path.resolve()
        path.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return False
    return path.is_file() and sha256(path) == record.get("receipt_sha256")


def _candidate_surface_file_ok(record: dict) -> bool:
    if not isinstance(record, dict) or not _is_sha256(record.get("candidate_surface_sha256")):
        return False
    path_value = record.get("candidate_surface_path")
    if not path_value:
        return False
    path = Path(str(path_value))
    if not path.is_absolute():
        path = ROOT / path
    try:
        path = path.resolve()
        path.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return False
    return path.is_file() and sha256(path) == record.get("candidate_surface_sha256")


def _check_ok(check) -> bool:
    if isinstance(check, dict):
        return check.get("ok") is True
    return check is True


def _ci95(record: dict, *, require_reportable: bool = True) -> tuple[bool, str]:
    """Validate a reported 95% interval and its physical-cluster provenance."""
    ci = record.get("ci95", record.get("ci"))
    if isinstance(ci, dict):
        bounds = [ci.get("lo"), ci.get("hi")]
        note = ci.get("method") or ci.get("note")
        reportable = ci.get("reportable", record.get("ci95_reportable"))
        clusters = ci.get("clusters", ci.get("n_clusters", record.get("n_spatial_clusters")))
        confidence = ci.get("confidence", record.get("ci95_confidence"))
    elif isinstance(ci, (list, tuple)) and len(ci) == 2:
        bounds = list(ci)
        note = record.get("ci95_method")
        reportable = record.get("ci95_reportable")
        bootstrap = record.get("bootstrap", {}) if isinstance(record.get("bootstrap"), dict) else {}
        clusters = bootstrap.get("clusters", record.get("n_spatial_clusters"))
        confidence = bootstrap.get("confidence", record.get("ci95_confidence"))
    else:
        return False, "no two-sided 95% interval"
    try:
        lo, hi = map(float, bounds)
        n_clusters = int(clusters)
        conf = float(confidence)
    except (TypeError, ValueError):
        return False, "95% interval lacks valid bounds, cluster count, or confidence"
    valid = (math.isfinite(lo) and math.isfinite(hi) and 0 <= lo <= hi <= 1
             and bool(note) and n_clusters >= 2 and math.isclose(conf, 0.95, abs_tol=1e-9)
             and (reportable is True or not require_reportable))
    if not valid:
        return False, "95% interval is not supported by a declared physical-cluster method"
    return True, f"95% CI [{lo:.6f}, {hi:.6f}] from {n_clusters} spatial clusters ({esc(note)})"


def _holdout_protocol_ok(protocol) -> bool:
    if not isinstance(protocol, dict):
        return False
    try:
        alpha = float(protocol.get("alpha", -1))
        beta = float(protocol.get("beta", -1))
        radius = float(protocol.get("triangular_kernel_radius_m", -1))
    except (TypeError, ValueError):
        return False
    return (
        protocol.get("buffered_whole_fault_segments") is True
        and protocol.get("catalogue_features_visible_only") is True
        and protocol.get("visible_faults_masked_pixel_exactly") is True
        and protocol.get("pooled") is True
        and math.isclose(alpha, 0.2, abs_tol=1e-12)
        and math.isclose(beta, 0.8, abs_tol=1e-12)
        and math.isclose(radius, 300.0, abs_tol=1e-9)
    )


def _reportable_holdout(record: dict, *, require_passed: bool = True) -> tuple[bool, str]:
    if not isinstance(record, dict):
        return False, "promotion-grade holdout receipt is missing"
    if require_passed and record.get("passed") is not True:
        return False, "qualification receipt does not mark the holdout passed"
    if record.get("evidence_class") != "HOLDOUT-DTI":
        return False, "evidence class is not HOLDOUT-DTI"
    if record.get("evaluator") != HOLDOUT_EVALUATOR or record.get("evaluator_version") != HOLDOUT_VERSION:
        return False, "shared evaluator/version is missing or does not match"
    try:
        dti = float(record.get("pooled_dti", record.get("dti")))
        n_pos = int(record.get("withheld_positive_pixels", record.get("n_withheld_positives", 0)))
    except (TypeError, ValueError):
        return False, "pooled DTI or withheld-positive count is invalid"
    if not math.isfinite(dti) or not 0 <= dti <= 1 or n_pos <= 0:
        return False, "pooled DTI or withheld-positive count is invalid"
    if not _holdout_protocol_ok(record.get("protocol")):
        return False, "prescribed buffered, visible-only, pixel-exact holdout protocol is not evidenced"
    ci_ok, ci_detail = _ci95(record, require_reportable=True)
    if not ci_ok:
        return False, ci_detail
    return True, f"HOLDOUT-DTI {dti:.6f}; {n_pos:,} withheld positives; {ci_detail}"


def _normalized_e2_result(e2: dict) -> tuple[dict | None, dict | None]:
    """Return (primary candidate result, per-class gains) from a qualified E2 receipt."""
    if not isinstance(e2, dict) or e2.get("promotion_grade") is not True:
        return None, None
    if e2.get("buffered_whole_component_context_used") is not True:
        return None, None
    if e2.get("evaluator") != HOLDOUT_EVALUATOR or e2.get("evaluator_version") != HOLDOUT_VERSION:
        return None, None
    result = e2.get("promotion_grade_result")
    if not isinstance(result, dict) or result.get("evidence_class") != "HOLDOUT-DTI":
        return None, None
    if result.get("evaluator_version") != HOLDOUT_VERSION:
        return None, None
    candidate_arm = result.get("candidate_arm")
    score = result
    scores = result.get("scores")
    if isinstance(scores, dict):
        if not candidate_arm or not isinstance(scores.get(candidate_arm), dict):
            return None, None
        score = scores[candidate_arm]
    if score.get("evidence_class") != "HOLDOUT-DTI":
        return None, None
    if not _holdout_protocol_ok(result.get("protocol", e2.get("protocol"))):
        return None, None
    if score.get("dti") is None or score.get("withheld_positive_pixels", score.get("n_withheld_positives", 0)) <= 0:
        return None, None
    if not _ci95(score, require_reportable=True)[0]:
        return None, None
    gains = result.get("per_class_gains")
    if not isinstance(gains, (dict, list)) or not gains:
        return score, None
    entries = list(gains.values()) if isinstance(gains, dict) else gains
    if not all(isinstance(row, dict)
               and row.get("evidence_class") == "HOLDOUT-DTI"
               and isinstance(row.get("gain", row.get("delta")), (int, float))
               and math.isfinite(float(row.get("gain", row.get("delta"))))
               and _ci95(row, require_reportable=True)[0]
               for row in entries):
        return score, None
    return score, gains


def validated_sigma_table(e1: dict) -> list[dict]:
    """Accept only complete, buffered shared-evaluator sigma rows for all folds/types."""
    if not isinstance(e1, dict):
        return []
    if (e1.get("promotion_grade") is not True
            or e1.get("buffered_whole_component_context_used") is not True
            or e1.get("evaluator") != HOLDOUT_EVALUATOR
            or e1.get("evaluator_version") != HOLDOUT_VERSION
            or e1.get("evidence_class") != "HOLDOUT-STRUCTURE"):
        return []
    rows = e1.get("promotion_grade_sigma_rows", e1.get("sigma_table_rows"))
    if not isinstance(rows, list) or not rows:
        return []
    clean = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("evidence_class") != "HOLDOUT-STRUCTURE":
            return []
        block, kind = row.get("block"), row.get("ridge_type")
        try:
            sigma_px = float(row.get("sigma_px"))
            n_matched = int(row.get("n_matched", 0))
        except (TypeError, ValueError):
            return []
        if (block not in {"NW", "NE", "SW", "SE"} or not isinstance(kind, str) or not kind
                or not math.isfinite(sigma_px) or sigma_px <= 0 or n_matched <= 0):
            return []
        key = (block, kind)
        if key in seen:
            return []
        seen.add(key)
        clean.append({**row, "sigma_px": sigma_px, "n_matched": n_matched})
    expected = {(block, kind) for block in ("NW", "NE", "SW", "SE")
                for kind in ("cat-axis", "sgmc-axis")}
    return clean if seen == expected else []


def validated_holdout_result(e2: dict) -> dict | None:
    """Return a promotion-grade candidate result or None; never bless legacy diagnostics."""
    score, gains = _normalized_e2_result(e2)
    return score if score is not None and gains is not None else None


def validated_per_class_gains(e2: dict) -> dict | list | None:
    """Return complete per-class gains only when each has a reportable 95% CI."""
    score, gains = _normalized_e2_result(e2)
    return gains if score is not None and gains is not None else None


def _file_path(value) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else ROOT / path


def _writer_receipt_emission(qualification: dict) -> dict | None:
    """Load a future shared-writer candidate only when its adjacent receipt matches its hash."""
    rel = qualification.get("candidate_file")
    expected_sha = qualification.get("candidate_file_sha256")
    if not rel or not _is_sha256(expected_sha):
        return None
    tif = _file_path(rel)
    sidecar = tif.with_suffix(".json")
    receipt = load(sidecar)
    if not tif.is_file() or not receipt or sha256(tif) != expected_sha or receipt.get("sha256") != expected_sha:
        return None
    validator = receipt.get("validator", {}) or {}
    raw_checks = validator.get("checks", {}) or {}
    checks = {name: {"ok": _check_ok(value), "detail": str(value)}
              for name, value in raw_checks.items()}
    return {
        "name": receipt.get("submission_name", tif.stem),
        "file": str(tif.relative_to(ROOT)) if tif.is_relative_to(ROOT) else str(tif),
        "zip": str(tif.with_suffix(".zip").relative_to(ROOT)) if tif.with_suffix(".zip").is_relative_to(ROOT) else str(tif.with_suffix(".zip")),
        "sha256": expected_sha,
        "decoded_prediction_sha256": receipt.get("decoded_prediction_sha256"),
        "bytes": receipt.get("bytes"),
        "n_positives": validator.get("in_footprint_positive_pixels", validator.get("emitted_positive_pixels")),
        "generated_utc": qualification.get("emitted_utc", receipt.get("generated_utc")),
        "submission_note": receipt.get("note", ""),
        "validator": {"passed": validator.get("all_checks_passed") is True, "checks": checks,
                      "sha256": expected_sha, "bytes": receipt.get("bytes"),
                      "n_positives": validator.get("in_footprint_positive_pixels", validator.get("emitted_positive_pixels"))},
        "uniqueness_local": {},
        "holdout_dti": qualification.get("promotion_grade_holdout", {}),
    }


def _current_inventory_ok(freshness: dict, qualification: dict,
                          inventory_index_sha256: str | None,
                          freshness_receipt_sha256: str | None) -> bool:
    qreg = qualification.get("registry", {}) or {}
    return (
        freshness.get("fresh_current_inventory") is True
        and _is_sha256(inventory_index_sha256)
        and _is_sha256(freshness_receipt_sha256)
        and freshness.get("registry_index_sha256") == inventory_index_sha256
        and qreg.get("fresh_current_inventory") is True
        and qreg.get("index_sha256") == inventory_index_sha256
        and qreg.get("freshness_receipt_sha256") == freshness_receipt_sha256
    )


def _valid_canary(canary: dict, candidate_file_sha256: str | None,
                  candidate_decoded_sha256: str | None,
                  inventory_index_sha256: str | None,
                  freshness_receipt_sha256: str | None) -> tuple[bool, str]:
    if not isinstance(canary, dict) or not canary:
        return False, "feature-alone canary receipt is missing"
    features = canary.get("features")
    if isinstance(features, dict):
        rows = list(features.values())
    elif isinstance(features, list):
        rows = features
    else:
        rows = []
    try:
        count = int(canary.get("n_features_tested", 0))
        declared_max = float(canary.get("max_single_feature_auc"))
    except (TypeError, ValueError):
        return False, "canary feature count or AUC is invalid"
    protocol = canary.get("protocol", {})
    protocol_ok = (isinstance(protocol, dict)
                   and protocol.get("feature_alone") is True
                   and protocol.get("buffered_spatial_folds") is True
                   and protocol.get("whole_fault_segments") is True)
    if (canary.get("passed") is not True or count <= 0 or len(rows) != count
            or not math.isfinite(declared_max) or declared_max >= CANARY_LIMIT
            or not protocol_ok
            or not _receipt_file_ok(canary)
            or canary.get("candidate_file_sha256") != candidate_file_sha256
            or canary.get("candidate_decoded_sha256") != candidate_decoded_sha256
            or canary.get("registry_index_sha256") != inventory_index_sha256
            or canary.get("freshness_receipt_sha256") != freshness_receipt_sha256):
        return False, "canary is missing per-feature folds, exceeds the strict AUC limit, or is not hash-bound"
    maxima = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("feature"):
            return False, "a feature-alone canary row is missing its feature identity"
        folds = row.get("auc_by_fold")
        if not isinstance(folds, dict) or len(folds) < 2:
            return False, "each feature must include AUC by at least two buffered spatial folds"
        try:
            aucs = [float(value) for value in folds.values()]
            row_max = float(row.get("auc_max"))
        except (TypeError, ValueError):
            return False, "feature-alone AUC values are invalid"
        if (not all(math.isfinite(value) and 0 <= value < CANARY_LIMIT for value in aucs)
                or not math.isfinite(row_max)
                or not math.isclose(row_max, max(aucs), rel_tol=0.0, abs_tol=1e-9)
                or row.get("leaks") is not False):
            return False, "a feature-alone canary row reaches the leakage limit or lacks a clean result"
        maxima.append(row_max)
    if not math.isclose(declared_max, max(maxima), rel_tol=0.0, abs_tol=1e-9):
        return False, "declared maximum AUC does not match the feature-level rows"
    return True, f"{count} features individually tested; maximum buffered-fold AUC {declared_max:.4f}"


def preemission_qualification_failures(qualification: dict, inv: dict, freshness: dict,
                                      *, inventory_index_sha256: str | None,
                                      inventory_receipt_sha256: str | None,
                                      freshness_receipt_sha256: str | None) -> list[str]:
    """Validate the manual qualification contract before a writer can emit a TIFF."""
    failures = []
    if qualification.get("submission_status") != "OK_TO_SUBMIT":
        failures.append("submission_status is not OK_TO_SUBMIT")
    candidate_file_sha = qualification.get("candidate_file_sha256")
    candidate_decoded_sha = qualification.get("candidate_decoded_sha256")
    if not _is_sha256(candidate_file_sha) or not _is_sha256(candidate_decoded_sha):
        failures.append("candidate file/pixel hashes are missing or invalid")
    if not _current_inventory_ok(freshness, qualification, inventory_index_sha256,
                                  freshness_receipt_sha256):
        failures.append("fresh complete inventory is not bound to the freshness audit")
    if not inv:
        failures.append("candidate-matched final-dot inventory receipt is missing")
    else:
        info = inv.get("informative_reading", {}) or {}
        if inv.get("candidate_file_sha256") != candidate_file_sha:
            failures.append("final-dot scan file hash does not match the qualification")
        if inv.get("candidate_decoded_sha256") != candidate_decoded_sha:
            failures.append("final-dot scan decoded-pixel hash does not match the qualification")
        if inv.get("unique") is not True or inv.get("stop_required") is not False:
            failures.append("literal final-dot uniqueness gate is negative or requires a stop")
        if (inv.get("complete_accessible_scan") is not True
                or int(inv.get("missing_or_invalid", 1) or 0) != 0
                or bool(inv.get("source_errors"))):
            failures.append("final-dot inventory scan is incomplete or has source errors")
        if int(info.get("overlap_firings", inv.get("duplicate_count", 1)) or 0) != 0:
            failures.append("literal forward-overlap trigger(s) remain")
        try:
            if (float(inv.get("worst_spearman_full_footprint", 1.0)) > RHO_LIMIT
                    or float(inv.get("worst_dot_overlap", 1.0)) > OVERLAP_LIMIT):
                failures.append("final-dot uniqueness threshold was exceeded")
        except (TypeError, ValueError):
            failures.append("final-dot uniqueness measurements are invalid")
    registry = qualification.get("registry", {}) or {}
    if registry.get("index_sha256") != inventory_index_sha256:
        failures.append("qualification registry index hash does not match the current index")
    final = qualification.get("final_dot_gate", {}) or {}
    if final.get("passed") is not True:
        failures.append("final_dot_gate is not marked passed")
    if final.get("candidate_file_sha256") != candidate_file_sha:
        failures.append("final-dot gate is not bound to the qualified TIFF hash")
    if final.get("candidate_decoded_sha256") != candidate_decoded_sha:
        failures.append("final-dot gate is not bound to the qualified decoded pixels")
    if final.get("receipt_sha256") != inventory_receipt_sha256:
        failures.append("final-dot gate receipt hash does not match the current scan receipt")
    if final.get("registry_index_sha256") != inventory_index_sha256:
        failures.append("final-dot gate is not bound to the current registry index")
    if final.get("freshness_receipt_sha256") != freshness_receipt_sha256:
        failures.append("final-dot gate is not bound to the current freshness receipt")
    pre = qualification.get("preplacement_surface_gate", {}) or {}
    if (pre.get("passed") is not True or not _candidate_surface_file_ok(pre)
            or not _receipt_file_ok(pre)):
        failures.append("pre-placement surface gate is missing, negative, or lacks hashes")
    if pre.get("registry_index_sha256") != inventory_index_sha256:
        failures.append("pre-placement gate is not bound to the current registry index")
    if pre.get("freshness_receipt_sha256") != freshness_receipt_sha256:
        failures.append("pre-placement gate is not bound to the current freshness receipt")
    canary = qualification.get("leakage_canary", {}) or {}
    canary_ok, _ = _valid_canary(canary, candidate_file_sha, candidate_decoded_sha,
                                  inventory_index_sha256, freshness_receipt_sha256)
    if not canary_ok:
        failures.append("feature-alone leakage canary is missing, failing, or not hash-bound")
    holdout = qualification.get("promotion_grade_holdout", {}) or {}
    holdout_ok, _ = _reportable_holdout(holdout)
    if (not holdout_ok or not _receipt_file_ok(holdout)
            or holdout.get("candidate_file_sha256") != candidate_file_sha
            or holdout.get("candidate_decoded_sha256") != candidate_decoded_sha
            or holdout.get("registry_index_sha256") != inventory_index_sha256
            or holdout.get("freshness_receipt_sha256") != freshness_receipt_sha256):
        failures.append("shared-evaluator HOLDOUT-DTI/95% CI is missing or not hash-bound")
    return failures

def evaluate_gates(emi: dict, sig: dict, inv: dict, tif: Path,
                   xcheck: dict | None = None, qualification: dict | None = None,
                   freshness: dict | None = None, *,
                   inventory_index_sha256: str | None = None,
                   inventory_receipt_sha256: str | None = None,
                   freshness_receipt_sha256: str | None = None) -> tuple[list[dict], bool]:
    """Evaluate the current exact-candidate gates; missing/stale receipts fail closed."""
    qualification = qualification or {}
    freshness = freshness or {}
    gates: list[dict] = []

    def add(gid, name, ok, detail, *, informational=False):
        gates.append(dict(id=gid, name=name, ok=bool(ok), detail=detail,
                          informational=informational))

    validator = emi.get("validator", {}) or {}
    checks = validator.get("checks", {}) or {}
    n_pass = sum(1 for value in checks.values() if _check_ok(value))
    exists = tif.is_file()
    disk_sha = sha256(tif) if exists else None
    recorded_sha = emi.get("sha256")
    file_sha_ok = bool(exists and _is_sha256(recorded_sha) and disk_sha == recorded_sha)
    local_pass = (validator.get("passed") is True and bool(checks)
                  and n_pass == len(checks) and file_sha_ok)
    add("G1", "Local format preflight (not portal acceptance)", local_pass,
        f"{n_pass}/{len(checks)} receipt checks pass; on-disk SHA-256 "
        f"{'matches' if file_sha_ok else 'does not match or is missing'} the emission receipt. "
        "This is only a local format/range result; the reported portal [0,1] rejection is unresolved.")

    local = emi.get("uniqueness_local", {}) or {}
    local_ok = local.get("cleared") is True and int(local.get("n_checked", 0) or 0) > 0
    add("G2", "Local witness subset (diagnostic only)", local_ok,
        f"{local.get('n_checked', 0)} local witnesses checked; pass/fail here is not a full registry "
        "clearance and is not used as a substitute for the pre-placement or final-dot gates.",
        informational=True)

    q_candidate_sha = qualification.get("candidate_file_sha256")
    q_decoded_sha = qualification.get("candidate_decoded_sha256")
    inv_candidate_sha = inv.get("candidate_file_sha256") if inv else None
    inv_decoded_sha = inv.get("candidate_decoded_sha256") if inv else None
    exact_candidate = (file_sha_ok and q_candidate_sha == disk_sha
                       and inv_candidate_sha == disk_sha
                       and _is_sha256(q_decoded_sha)
                       and q_decoded_sha == inv_decoded_sha
                       and (not emi.get("decoded_prediction_sha256")
                            or emi.get("decoded_prediction_sha256") == q_decoded_sha))
    inventory_current = _current_inventory_ok(freshness, qualification,
                                              inventory_index_sha256,
                                              freshness_receipt_sha256)
    qreg = qualification.get("registry", {}) or {}

    pre = qualification.get("preplacement_surface_gate", {}) or {}
    pre_ok = (
        qualification.get("submission_status") == "OK_TO_SUBMIT"
        and pre.get("passed") is True
        and _candidate_surface_file_ok(pre)
        and _receipt_file_ok(pre)
        and pre.get("registry_index_sha256") == inventory_index_sha256
        and pre.get("freshness_receipt_sha256") == freshness_receipt_sha256
        and inventory_current
        and exact_candidate
    )
    add("G2P", "Pre-placement surface gate", pre_ok,
        "A separate hash-bound pre-placement surface receipt is required against the fresh inventory. "
        + ("The qualification receipt is missing or does not bind this candidate/inventory."
           if not pre_ok else "The exact candidate surface and inventory hashes are bound and pass."))

    if not inv:
        g3_ok = False
        detail = "The candidate-matched final-dot inventory receipt is missing. Fail closed."
    else:
        info = inv.get("informative_reading", {}) or {}
        final = qualification.get("final_dot_gate", {}) or {}
        no_source_errors = not inv.get("source_errors")
        no_invalid = int(inv.get("missing_or_invalid", 1) or 0) == 0
        complete = inv.get("complete_accessible_scan") is True and no_invalid and no_source_errors
        within_limits = (
            inv.get("unique") is True
            and inv.get("worst_spearman_full_footprint") is not None
            and float(inv.get("worst_spearman_full_footprint")) <= RHO_LIMIT
            and inv.get("worst_dot_overlap") is not None
            and float(inv.get("worst_dot_overlap")) <= OVERLAP_LIMIT
            and float(inv.get("rho_limit", RHO_LIMIT)) == RHO_LIMIT
            and float(inv.get("overlap_limit", OVERLAP_LIMIT)) == OVERLAP_LIMIT
            and inv.get("stop_required") is False
        )
        final_bound = (
            final.get("passed") is True
            and final.get("candidate_file_sha256") == disk_sha
            and final.get("candidate_decoded_sha256") == q_decoded_sha
            and final.get("receipt_sha256") == inventory_receipt_sha256
            and final.get("registry_index_sha256") == inventory_index_sha256
            and final.get("freshness_receipt_sha256") == freshness_receipt_sha256
        )
        g3_ok = bool(complete and within_limits and inventory_current and exact_candidate and final_bound)
        detail = (
            f"Recorded scan checked {inv.get('registry_rasters_checked', inv.get('n_compared', 0))} "
            f"indexed rasters at {esc(inv.get('index_generated_utc', 'unknown snapshot'))}; "
            f"complete for that accessible snapshot={inv.get('complete_accessible_scan')}, "
            f"missing/invalid={inv.get('missing_or_invalid')}, source errors={len(inv.get('source_errors', []) or [])}. "
            f"Literal forward-overlap firings={info.get('overlap_firings', inv.get('duplicate_count', 'unknown'))} "
            f"({info.get('overlap_firings_informative', 'unknown')} informative, "
            f"{info.get('overlap_firings_vacuous', 'unknown')} saturated/vacuous); worst overlap="
            f"{fmt(inv.get('worst_dot_overlap'))}, worst rank correlation="
            f"{fmt(inv.get('worst_spearman_full_footprint'))}. "
            f"unique={inv.get('unique')}, stop_required={inv.get('stop_required')}. "
            "The scan covers its saved public-inventory snapshot only, not an organizer-wide inventory; "
            f"freshness clearance={inventory_current}. A literal trigger is never waived by chance correction."
        )
    add("G3", "Final-dot uniqueness and inventory gate (literal protocol)", g3_ok, detail)

    canary = qualification.get("leakage_canary", {}) or {}
    canary_ok, canary_detail = _valid_canary(canary, disk_sha, q_decoded_sha,
                                              inventory_index_sha256,
                                              freshness_receipt_sha256)
    canary_ok = canary_ok and inventory_current
    add("G4", "Promotion-grade feature-alone leakage canary", canary_ok,
        canary_detail + " Feature-level results must use the current split and be bound to this candidate and inventory.")

    holdout = qualification.get("promotion_grade_holdout", {}) or {}
    ho_ok, ho_detail = _reportable_holdout(holdout)
    holdout_ok = (
        ho_ok
        and _receipt_file_ok(holdout)
        and holdout.get("candidate_file_sha256") == disk_sha
        and holdout.get("candidate_decoded_sha256") == q_decoded_sha
        and holdout.get("registry_index_sha256") == inventory_index_sha256
        and holdout.get("freshness_receipt_sha256") == freshness_receipt_sha256
        and inventory_current
    )
    if not holdout_ok:
        legacy = emi.get("holdout_dti", {}) or {}
        protocol = legacy.get("protocol")
        legacy_note = (f" Saved candidate measurement uses legacy {esc(protocol)} / "
                       f"{esc(legacy.get('evaluator'))}; it is not a promotion-grade shared-evaluator result." if protocol else "")
        ho_detail = ("No hash-bound, reportable shared-evaluator qualification is present. "
                     + ho_detail + "." + legacy_note)
    else:
        ho_detail = ho_detail + " Candidate, inventory and freshness hashes match the qualification."
    add("G5", "Buffered spatial HOLDOUT-DTI with defensible 95% CI", holdout_ok, ho_detail)

    if xcheck is None:
        crosscheck_ok = False
        crosscheck_detail = "No legacy metric arithmetic cross-check receipt is available; this is informational only."
    else:
        crosscheck_ok = xcheck.get("verdict") == "AGREE"
        crosscheck_detail = (
            f"Legacy metric arithmetic verdict={esc(xcheck.get('verdict'))}. This checks arithmetic only; "
            "its numerical diagnostic is withheld from the public gate panel because it does not carry "
            "the current promotion-grade protocol and defensible 95% CI. It does not upgrade the old "
            "evaluator, split, or selection process."
        )
    add("G5i", "Legacy diagnostic arithmetic cross-check (not promotion evidence)", crosscheck_ok,
        crosscheck_detail, informational=True)

    add("G6", "Organizer receipt (post-upload only)", False,
        "No organizer submission receipt is present. This is not a pre-upload eligibility gate and "
        "cannot be inferred from a local format check; no score is attributed to this TIFF.",
        informational=True)

    by_id = {gate["id"]: gate for gate in gates}
    eligible = all(by_id.get(gid, {}).get("ok") is True for gid in REQUIRED_GATES)
    return gates, eligible


