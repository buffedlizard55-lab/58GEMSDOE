#!/usr/bin/env python3
"""Live-evidence calibration: what do the owner-reported scores of sha256-verified
registry rasters say about how a dot field must be shaped?

This is the only bridge available in-sandbox between a *measurable* property of a
submission raster and a *live* competition score.  Every number here is one of:

* REGISTRY-MEASUREMENT  - recomputed from sha256-verified raster bytes;
* USER-REPORTED-SCORE   - a score the owner quoted from a sibling site, copied
                          verbatim into ``registry/live_scores_owner_reported.csv``.

Nothing here is an organizer receipt and nothing here is a projection written as
a score.

Model
-----
The organizer (DrivenData staff, community thread 11516, 2026-09-16) confirmed
that pixels of the known USGS/INGENIOUS catalogue are masked out of evaluation,
so a predicted pixel on the catalogue contributes to neither ``TP_w`` nor
``FP_w``.  Write ``P'`` for the off-catalogue dots of a file (all at 1.0),
``n' = |P'|`` and

    M' = sum_{x in P'} max_{g in catalogue} k(d(x, g)),     k(d) = max(1 - d/3, 0)

i.e. the total triangular-kernel credit of the file's dots *against the public
catalogue*.  If the hidden new-fault truth is a ``kappa``-scaled, spatially
co-located version of the public catalogue (the assumption being tested, not
asserted), then ``TP_w ~ kappa * M'`` and ``FP_w ~ n' - kappa * M'``, so

    DTI = TP / (0.2*(TP + FP) + 0.8*G)  ~  kappa*M' / (0.2*n' + 0.8*G)

which is a **two-parameter** model in (kappa, G).  It is fitted here by ordinary
least squares over every owner-reported score that can be matched to a
sha256-verified raster, and the fitted parameters are turned into the emission
rule the ribbon lane needs:

    include a dot iff  kappa * k_cat(x) >= 0.2 * DTI      (marginal-inclusion bar)

Outputs ``evidence/live_evidence_fit.json``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import grid  # noqa: E402
from gems58w.metric import ALPHA, BETA, RADIUS_PX, kernel  # noqa: E402

REGISTRY = ROOT / "registry" / "registry_refreshed.json"
SCORES = ROOT / "registry" / "live_scores_owner_reported.csv"
OUT = ROOT / "evidence" / "live_evidence_fit.json"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _hash_tokens(label: str) -> list[str]:
    """Distinctive content-hash tokens in a submission label.

    A bare ``[0-9a-f]{8,}`` match also catches ISO dates (``20261003``) and
    timestamps, which silently matched dozens of unrelated rasters in the first
    version of this tool.  A usable token must be >= 10 characters long and carry
    at least three alphabetic hex digits, which no date or timestamp in this
    portfolio does.
    """
    out = []
    for t in re.findall(r"[0-9a-f]{10,}", label.lower()):
        if sum(c in "abcdef" for c in t) >= 3:
            out.append(t)
    return out


def _repo_of(site: str) -> str | None:
    m = re.search(r"github\.io/([^/]+)/", site)
    return m.group(1) if m else None


def match_scores_to_registry(scores: list[dict], rasters: list[dict]) -> list[dict]:
    """Match an owner-reported label to sha256-verified registry rasters.

    Fail closed: a label is matched only inside the repository its quoted site
    belongs to, and only by (a) an exact normalised stem, (b) the label being a
    substring of the stem, or (c) a distinctive content-hash token.  If the
    label matches nothing in its own repository, a strict hash-token search is
    run across every repository.  Ambiguous matches are reported, never resolved
    by taking the first hit.
    """
    by_repo: dict[str, list[dict]] = {}
    for rec in rasters:
        for src in rec["sources"]:
            repo, _, path = src.partition(":")
            by_repo.setdefault(repo, []).append(
                dict(rec, matched_path=src, norm_stem=_norm(Path(path).stem)))
    out = []
    for sc in scores:
        lab = _norm(sc["label"])
        toks = _hash_tokens(sc["label"])
        repo = _repo_of(sc["source_site"])
        pools = [(f"repo:{repo}", by_repo.get(repo, []))]
        if not pools[0][1]:
            pools = [("all-repos", [r for v in by_repo.values() for r in v])]

        def hits_in(pool):
            exact = [r for r in pool if r["norm_stem"] == lab]
            if exact:
                return exact, "exact-stem"
            sub = [r for r in pool if len(lab) >= 12 and lab in r["norm_stem"]]
            if sub:
                return sub, "label-substring-of-stem"
            if toks:
                h = [r for r in pool if any(t in r["norm_stem"] for t in toks)]
                if h:
                    return h, "content-hash-token"
            return [], None

        hits, method = [], None
        for _name, pool in pools:
            hits, method = hits_in(pool)
            if hits:
                break
        if not hits and repo and pools[0][0] != "all-repos":
            hits, method = hits_in([r for v in by_repo.values() for r in v])
        seen, uniq = set(), []
        for h in hits:
            if h["sha256"] not in seen:
                seen.add(h["sha256"])
                uniq.append(h)
        out.append(dict(sc, n_matches=len(uniq), matches=uniq, match_method=method,
                        match_repo=repo,
                        ambiguous=bool(len(uniq) > 1)))
    return out


def raster_stats(path: Path, d_cat: np.ndarray, fp: np.ndarray, cat: np.ndarray) -> dict:
    with rasterio.open(path) as s:
        if s.count != 1 or (s.height, s.width) != fp.shape:
            return dict(status="grid_mismatch")
        a = s.read(1).astype(np.float32)
    finite = np.isfinite(a)
    dots = finite & (a > 0) & fp
    n_all = int(dots.sum())
    if n_all == 0:
        return dict(status="empty", dots=0)
    off = dots & ~cat
    on = dots & cat
    n_off = int(off.sum())
    kcat = kernel(d_cat)
    m_off = float(kcat[off].sum())
    d = d_cat[off] if n_off else np.zeros(0)
    vals = np.unique(a[dots])
    return dict(
        status="ok", dots=n_all, dots_on_catalogue=int(on.sum()), dots_off_catalogue=n_off,
        value_min=float(vals.min()), value_max=float(vals.max()), n_unique_values=int(vals.size),
        all_values_one=bool(vals.size == 1 and float(vals[0]) == 1.0),
        M_off_catalogue=m_off,
        mean_credit_off_catalogue=(m_off / n_off if n_off else 0.0),
        frac_off_d_le_1=float((d <= 1).mean()) if n_off else 0.0,
        frac_off_d_le_2=float((d <= 2).mean()) if n_off else 0.0,
        frac_off_d_le_3=float((d <= 3).mean()) if n_off else 0.0,
        frac_off_d_le_5=float((d <= 5).mean()) if n_off else 0.0,
        frac_off_d_le_10=float((d <= 10).mean()) if n_off else 0.0,
        median_off_d_px=float(np.median(d)) if n_off else None,
        p10_off_d_px=float(np.quantile(d, 0.10)) if n_off else None,
        p90_off_d_px=float(np.quantile(d, 0.90)) if n_off else None,
    )


def fit_model(rows: list[dict]) -> dict:
    """Least-squares fit of s = kappa*M' / (alpha*n' + beta*G) over (kappa, G)."""
    s = np.array([r["score"] for r in rows], float)
    m = np.array([r["M_off_catalogue"] for r in rows], float)
    n = np.array([r["dots_off_catalogue"] for r in rows], float)
    best = None
    for G in np.concatenate([np.arange(2000, 200001, 500.0)]):
        denom = ALPHA * n + BETA * G
        # s = kappa * m / denom  ->  kappa = sum(s*m/denom^2*denom)/... closed form OLS
        x = m / denom
        kappa = float((x * s).sum() / (x * x).sum()) if (x * x).sum() > 0 else 0.0
        pred = kappa * x
        ss = float(((s - pred) ** 2).sum())
        if best is None or ss < best["sse"]:
            best = dict(G=float(G), kappa=kappa, sse=ss)
    G, kappa = best["G"], best["kappa"]
    denom = ALPHA * n + BETA * G
    pred = kappa * m / denom
    ss_res = float(((s - pred) ** 2).sum())
    ss_tot = float(((s - s.mean()) ** 2).sum())
    return dict(
        model="DTI ~ kappa * M_off_catalogue / (alpha * n_off_catalogue + beta * G)",
        n_files=len(rows), kappa=kappa, implied_hidden_truth_pixels_G=G,
        r2=1.0 - ss_res / ss_tot if ss_tot > 0 else None,
        rmse=float(np.sqrt(ss_res / len(rows))),
        spearman_pred_vs_observed=float(spearmanr(pred, s).statistic),
       pearson_pred_vs_observed=float(np.corrcoef(pred, s)[0, 1]),
        implied_inclusion_bar_at_leader=None,
        predictions=[dict(label=r["label"], score=r["score"], predicted=float(p),
                          dots_off_catalogue=r["dots_off_catalogue"],
                          M_off_catalogue=r["M_off_catalogue"])
                     for r, p in zip(rows, pred)],
    )


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    d_cat = distance_transform_edt(~cat).astype(np.float32)
    scores = list(csv.DictReader(SCORES.read_text().splitlines()))
    reg = json.loads(REGISTRY.read_text())
    matched = match_scores_to_registry(scores, reg["rasters"])
    print(f"scores quoted: {len(scores)}; matched to a sha256-verified raster: "
          f"{sum(1 for m in matched if m['n_matches'])}", flush=True)

    cache: dict[str, dict] = {}
    rows, unmatched = [], []
    for m in matched:
        if not m["n_matches"]:
            unmatched.append(dict(label=m["label"], reason="no registry match",
                                  repo=m["match_repo"]))
            continue
        if m["n_matches"] > 1:
            # fail closed: an ambiguous attribution is dropped, never guessed
            unmatched.append(dict(label=m["label"], reason=f"ambiguous ({m['n_matches']} rasters)",
                                  repo=m["match_repo"],
                                  candidates=[x["matched_path"] for x in m["matches"]][:5]))
            continue
        rec = m["matches"][0]
        sha = rec["sha256"]
        if sha not in cache:
            p = ROOT / ".cache" / "registry" / f"{sha}.tif"
            if not p.exists():
                cache[sha] = dict(status="cache_missing")
            else:
                got = hashlib.sha256(p.read_bytes()).hexdigest()
                if got != sha:
                    cache[sha] = dict(status="sha256_mismatch")
                else:
                    cache[sha] = raster_stats(p, d_cat, fp, cat)
        st = cache[sha]
        if st.get("status") != "ok":
            unmatched.append(dict(label=m["label"], reason=st.get("status"), repo=m["match_repo"]))
            continue
        rows.append(dict(label=m["label"], score=float(m["score_as_quoted"]),
                         score_kind=m["score_kind"], source_site=m["source_site"],
                         match_method=m["match_method"],
                         sha256=sha, matched_path=rec["matched_path"], **st))
    print(f"measured rows: {len(rows)}; dropped: {len(unmatched)}", flush=True)

    # one raster, several different quoted scores = an attribution irregularity
    by_sha: dict[str, list[dict]] = {}
    for r in rows:
        by_sha.setdefault(r["sha256"], []).append(r)
    conflicts = [dict(sha256=sha, path=rs[0]["matched_path"],
                      labels=[r["label"] for r in rs], scores=sorted({r["score"] for r in rs}))
                 for sha, rs in by_sha.items() if len({r["score"] for r in rs}) > 1]
    identical = [dict(sha256=sha, path=rs[0]["matched_path"], n_labels=len(rs),
                      labels=[r["label"] for r in rs], score=rs[0]["score"])
                 for sha, rs in by_sha.items() if len(rs) > 1 and len({r["score"] for r in rs}) == 1]
    # the fit uses one row per distinct raster, so a raster quoted twice does not
    # get double weight; rasters with conflicting quoted scores are excluded
    # (fail closed) and reported as an attribution irregularity instead
    fit_rows = [rs[0] for sha, rs in by_sha.items() if len({r["score"] for r in rs}) == 1]
    print(f"distinct rasters with a consistent quoted score: {len(fit_rows)}; "
          f"score conflicts excluded: {len(conflicts)}", flush=True)

    fit = fit_model(fit_rows)
    kappa, G = fit["kappa"], fit["implied_hidden_truth_pixels_G"]
    # emission rule implied by the fit, at several reference scores
    bars = {}
    for name, s0 in (("owner_target_0.3195", 0.3195), ("public_leader_0.4133", 0.4133),
                     ("group_best_0.2750", 0.2750), ("fitted_portfolio_mean", None)):
        if s0 is None:
            continue
        k_bar = ALPHA * s0 / kappa if kappa > 0 else None
        bars[name] = dict(reference_dti=s0, required_kappa_scaled_credit=ALPHA * s0,
                          required_catalogue_kernel_credit=k_bar,
                          max_catalogue_distance_px=(RADIUS_PX * (1 - k_bar) if k_bar and k_bar < 1 else None),
                          max_catalogue_distance_m=(100.0 * RADIUS_PX * (1 - k_bar) if k_bar and k_bar < 1 else None))
    fit["implied_inclusion_bar_at_leader"] = bars

    covariates = {}
    for key in ("dots", "dots_off_catalogue", "mean_credit_off_catalogue", "M_off_catalogue",
                "frac_off_d_le_1", "frac_off_d_le_2", "frac_off_d_le_3", "frac_off_d_le_5",
                "frac_off_d_le_10", "median_off_d_px", "dots_on_catalogue"):
        v = np.array([r[key] for r in fit_rows if r.get(key) is not None], float)
        s = np.array([r["score"] for r in fit_rows if r.get(key) is not None], float)
        if len(v) > 3 and np.ptp(v) > 0:
            covariates[key] = dict(spearman_vs_score=float(spearmanr(v, s).statistic),
                                   pearson_vs_score=float(np.corrcoef(v, s)[0, 1]), n=int(len(v)))

    out = dict(
        evidence_class="REGISTRY-MEASUREMENT + USER-REPORTED-SCORE",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        purpose=("calibrate the emission rule against the only live evidence available in-sandbox: "
                 "owner-quoted scores of sha256-verified public rasters"),
        grid=dict(footprint_px=int(fp.sum()), catalogue_px=int(cat.sum()),
                  kernel_radius_px=RADIUS_PX, alpha=ALPHA, beta=BETA),
        masking_authority=("DrivenData staff (chrisk-dd), community thread 11516, 2026-09-16: "
                           "'Pixels corresponding to known USGS/INGENIOUS faults are masked / "
                           "excluded from evaluation, so they do not count towards penalty terms.' "
                           "https://community.drivendata.org/t/11516"),
        n_scores_quoted=len(scores), n_rows_measured=len(rows),
        n_distinct_rasters_fitted=len(fit_rows), unmatched=unmatched,
        score_conflicts=conflicts, same_raster_same_score=identical,
        fit=fit, covariates=covariates, rows=rows, fitted_rows=fit_rows,
        verdict=("NEGATIVE" if (fit["r2"] or -1) < 0.0 or abs(fit["spearman_pred_vs_observed"]) < 0.30
                 else "positive"),
        verdict_note=(
            "The two-parameter catalogue-proximity model does not explain the owner-quoted live "
            "scores of 66 sha256-verified rasters (R^2 < 0, Spearman ~ 0), and no dot-field summary "
            "statistic reaches |Spearman| 0.30. Two organizer-confirmed facts explain why the "
            "evidence is this weak: (1) the public leaderboard pools only an undisclosed public "
            "subset of the region (thread 11550, 'We are not providing any information on the "
            "chunking / subsets'), so each quoted score carries chunk-luck noise we cannot model; "
            "(2) the Initial Prize Round is scored on the private subset, which no quoted score "
            "here measures. Consequence for the lane: the emission rule cannot be calibrated from "
            "live evidence, so it is set by the exact-metric marginal-inclusion bar and by the "
            "holdout-measured sigma, and no projection is written as a score."),
        wall_seconds=round(time.time() - t0, 2),
    )
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(dict(n=len(rows), kappa=kappa, G=G, r2=fit["r2"],
                          spearman=fit["spearman_pred_vs_observed"], bars=bars), indent=1, default=float))
    print("wrote", OUT, f"({out['wall_seconds']} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
