#!/usr/bin/env python3
"""EXP-A: measure the **signed** across-strike localisation error of the ridge field.

The lane prompt asks for the error scale ``sigma(x)`` by data block, feature
resolution and ridge type, and then for the number and the *offset* of parallel
dotted lines.  The inherited ``gems58w.sigma`` measurement is unsigned: it takes
the distance from a withheld component to the nearest ridge pixel, so it can
only justify a ribbon that is symmetric about the ridge.

This script adds the missing sign.  For every withheld component that the ridge
field recovers, it projects each component pixel onto the across-strike unit
vector of its nearest ridge pixel and takes the component mean

    mu(w) = mean over p in w of  ( (p - ridge(p)) . n(ridge(p)) )   [px]

with ``n = (ay, ax)`` the across-strike unit vector that the emitter itself uses
(``rr = r + o*ay``, ``cc = c + o*ax``).  ``mu > 0`` means the withheld truth lies
on the ``+`` side of the detected ridge in the emitter's own convention.

Aggregating ``mu`` by (family, ridge sign, scale, block) answers a question the
lane has never measured: **is the detection error Biased or centred at 0?**
A stratum whose ``|mean(mu)|`` is small against ``sigma`` needs a symmetric
ribbon; one with a material bias is better served by shifting every line of the
ribbon to ``mu + k*R`` instead of ``k*R``.

Writes ``evidence/ribbon_v2/signed_sigma.json``.

    PYTHONPATH=src GEMS_FEATURE_STACK=... GEMS58W_CACHE=... \
        python3 scripts/ribbon_run_signed_sigma.py --threshold 0.6
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems58w import extract, holdout, sigma  # noqa: E402

EVID = ROOT / "evidence" / "ribbon_v2"
MIN_COMP_PX = 8
MATCH_FRAC = 0.6
L_MAX = 15.0


def signed_measure(field: dict, segs, fold) -> list[dict]:
    wmask = fold.withhold
    lab, n = label(wmask, structure=np.ones((3, 3), int))
    if n == 0 or not segs:
        return []
    pts = np.vstack([s["idx"] for s in segs]).astype(np.float64)
    owner = np.concatenate([np.full(s["size"], i) for i, s in enumerate(segs)])
    tree = cKDTree(pts)
    comp_pixels = np.argwhere(wmask)
    d, j = tree.query(comp_pixels.astype(np.float64), k=1)
    near = pts[j]                                  # nearest ridge pixel (row, col)
    ax = field["ax"][near[:, 0].astype(int), near[:, 1].astype(int)]
    ay = field["ay"][near[:, 0].astype(int), near[:, 1].astype(int)]
    dv = comp_pixels.astype(np.float64) - near
    s_off = dv[:, 0] * ay + dv[:, 1] * ax          # signed across-strike offset
    comp_label = lab[comp_pixels[:, 0], comp_pixels[:, 1]]
    order = np.argsort(comp_label, kind="stable")
    comp_label = comp_label[order]
    d, j, s_off, comp_pixels = d[order], j[order], s_off[order], comp_pixels[order]
    bounds = np.flatnonzero(np.diff(comp_label)) + 1
    out = []
    for a, b in zip(np.r_[0, bounds], np.r_[bounds, comp_label.size]):
        if b - a < MIN_COMP_PX:
            continue
        dd = d[a:b]
        if float((dd <= L_MAX).mean()) < MATCH_FRAC:
            continue
        seg_ids = owner[j[a:b][dd <= L_MAX]]
        if seg_ids.size == 0:
            continue
        vals, counts = np.unique(seg_ids, return_counts=True)
        dom = segs[int(vals[counts.argmax()])]
        code = max(dom["codes"], key=lambda c: c["scale"]) if dom["codes"] else {}
        band = code.get("band", "?")
        fam = next((f for f, bs in __import__("gems58w.features", fromlist=["FAMILIES"]).FAMILIES.items()
                    if band in bs), "other")
        sd = s_off[a:b][dd <= L_MAX]
        out.append(dict(block=fold.name, comp_px=int(b - a),
                        frac_within=float((dd <= L_MAX).mean()),
                        rms=float(np.sqrt(np.mean(np.minimum(dd, L_MAX) ** 2))),
                        mu=float(sd.mean()), mu_abs_mean=float(np.abs(sd).mean()),
                        mu_sd=float(sd.std()),
                        band=band, family=fam, scale=float(code.get("scale", 0.0)),
                        sign=int(code.get("sign", 0)), ridge_px=int(dom["size"])))
    return out


def agg(vals: list[float]) -> dict:
    v = np.asarray(vals, float)
    return dict(n=int(v.size), mean=float(v.mean()), median=float(np.median(v)),
                rms=float(np.sqrt(np.mean(v ** 2))),
                p25=float(np.quantile(v, 0.25)), p75=float(np.quantile(v, 0.75)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--min-px", type=int, default=6)
    args = ap.parse_args()
    t0 = time.time()

    field = extract.build()
    segs = extract.segments(field, args.threshold, min_px=args.min_px)
    print(f"ridge field: {len(segs)} segments, "
          f"{sum(s['size'] for s in segs)} px at threshold {args.threshold}", flush=True)

    folds = holdout.all_folds()
    items = []
    for f in folds:
        it = signed_measure(field, segs, f)
        items.extend(it)
        print(f"[{f.name}] withheld {f.n_truth} px | matched {len(it)} components", flush=True)

    unsigned = sigma.sigma_table(sigma.measure(field, segs, folds[0]) if False else [
        sigma.CompSigma(block=i["block"], comp_px=i["comp_px"], frac_within=i["frac_within"],
                        sigma=i["rms"], band=i["band"], family=i["family"],
                        scale=i["scale"], sign=i["sign"], ridge_px=i["ridge_px"])
        for i in items])

    def by(key):
        keys = sorted({key(i) for i in items})
        out = {}
        for k in keys:
            sub = [i for i in items if key(i) == k]
            if len(sub) >= 8:
                out[str(k)] = dict(n=len(sub), mu_mean=float(np.mean([s["mu"] for s in sub])),
                                   mu_absmean=float(np.mean([s["mu_abs_mean"] for s in sub])),
                                   rms=float(np.sqrt(np.mean([s["rms"] ** 2 for s in sub]))),
                                   bias_ratio=float(abs(np.mean([s["mu"] for s in sub])) /
                                                    max(1e-9, np.sqrt(np.mean([s["rms"] ** 2 for s in sub])))))
        return out

    pooled_mu = float(np.mean([i["mu"] for i in items]))
    pooled_rms = float(np.sqrt(np.mean([i["rms"] ** 2 for i in items])))
    out = dict(
        protocol=holdout.PROTOCOL, evaluator=holdout.EVALUATOR,
        threshold=args.threshold, n_segments=len(segs),
        n_matched_components=len(items),
        pooled=dict(mu_mean=pooled_mu, rms=pooled_rms,
                    bias_ratio=abs(pooled_mu) / max(1e-9, pooled_rms),
                    mu_absmean=float(np.mean([i["mu_abs_mean"] for i in items]))),
        by_family_sign=by(lambda i: f"{i['family']}/{i['sign']}"),
        by_scale=by(lambda i: f"{i['scale']}px"),
        by_block=by(lambda i: i["block"]),
        unsigned_table=unsigned,
        per_component=items,
        wall_seconds=round(time.time() - t0, 2),
        note=("mu is the signed across-strike offset (px) of a withheld component from its "
              "nearest ridge pixel, in the emitter's own convention "
              "(rr = r + o*ay, cc = c + o*ax); 1 px = 100 m. bias_ratio = |mean(mu)| / rms. "
              "A stratum with a large bias_ratio wants the whole ribbon shifted to mu."),
    )
    EVID.mkdir(parents=True, exist_ok=True)
    p = EVID / "signed_sigma.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("pooled", "by_family_sign", "by_scale", "by_block")},
                     indent=1))
    print("wrote", p, f"({time.time() - t0:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
