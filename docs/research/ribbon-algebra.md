# Ribbon algebra: why parallel dotted lines pay when the location is uncertain

## Setup

A candidate ridge is a detected curve. The true trace runs roughly parallel to it at an unknown
across-strike offset `delta`, modelled as `Normal(0, sigma^2)` with `sigma` measured on the
hide-and-recover holdout (`src/gems58/sigma.py`). The emitter places `n` dotted lines at
perpendicular offsets `o_1 … o_n` from the ridge. A dot at offset `o` receives kernel credit

    k(delta, o) = max(0, 1 - |delta - o| / R),      R = 3 px

and the metric credits each truth pixel with the **maximum** over dots, so two lines closer than
`R` compete for the same truth pixels rather than adding.

## The two decisions

**Offsets.** The lattice is `{0, ±R, ±2R, …}`. Anything finer spends mass on overlap: two dots 1 px
apart that cover one truth pixel buy `max(k1, k2) ≈ 1` for a cost of `0.4` instead of `0.2`.

**How many lines.** Exactly those maximising the lane's `U` at the running index:

    U = (1 - 0.2 * DTI0) * dTP - 0.2 * DTI0 * dFP

which is the first-order form of (B) in `metric.md`: a change pays iff
`dTP (1 - 0.2 DTI0) > 0.2 DTI0 * dFP`. `src/gems58/allocation.py::plan` evaluates the Normal
expectations `E[max(0, 1 - |delta - o|/R)]` on a lattice and stops when the marginal `U` turns
negative.

## What the measured sigma implies

With `sigma = 1.70 px` (the pooled RMS error of the *detected* pixels) the expected credit of the first line is
`E[k(delta, 0)] ≈ 0.63`. The marginal credit of a line at `o = R` is
`E[max(0, k(delta, R) - k(delta, 0))] ≈ 0.1`, which is **greater than `0.2 · DTI0 = 0.064` at the
owner-stated leader 0.3195**, so the second and third lines pay. A line at `o = 2R = 6 px` is
already in the tail of `Normal(0, 1.68^2)` and its marginal credit falls below the threshold, so
`plan` stops at three lines. The lane's rule of thumb — one tight line below `sigma ≈ 0.5 px`,
a ribbon about `±sigma` wide at `sigma ≈ 2–3 px` — reproduces the same answer.

## What the holdout actually says

At an identical budget of 38,000 isolated dots per fold (`evidence/equal_budget.json`):

| arm (lines at 0, ±R, …) | pooled HOLDOUT-DTI | Δ vs tight |
| ---: | ---: | ---: |
| 1 line | 0.039363 | — |
| 2 lines (0, ±R) | 0.039633 | +0.000270 |
| 3 lines (0, ±R) | 0.039929 | +0.000566 |
| 5 lines (0, ±R, ±2R) | 0.040008 | +0.000645 |

Monotone, small, and — the useful part — **structured by the measured σ**. Re-scoring each width
against only the withheld truth whose nearest ridge pixel sits in a σ class:

| σ class | withheld px | tight line | 3-line ribbon | gain |
| --- | ---: | ---: | ---: | ---: |
| < 1.5 px | 4,975 | 0.086077 | 0.084669 | **−0.001408** |
| 1.5–2.5 px | 1,935 | 0.009904 | 0.010240 | +0.000335 |
| 2.5–3 px | 608 | 0.000280 | 0.000557 | +0.000277 |
| 3–6 px | 6,492 | 0.000000 | 0.001636 | **+0.001636** |

This is the lane's rule reproduced from measurement rather than assumed: a single tight line where
the localisation error is small, a ribbon where it is not, and a class (σ ∈ [3, 6] px) that only the
ribbon reaches at all. The pooled margin is the sum of those small, opposing terms — which is why
the delivered geometry is decided by the σ table and not by a single pooled number.

**Where the honest margin is.** An earlier sweep that did *not* hold the dot budget constant showed
the ribbon beating the tight line by `+0.025` DTI. That number was mass, not geometry: the wide arms
simply carried more dots. At an equal budget the pooled margin is `+0.0006` and the class table
above is the part that generalises. Both runs are kept in `evidence/`.

> **Instrument warning.** `scripts/run_instrument_control.py` rescores the *same* geometry with the
> catalogue-margin screen relaxed: 0 px margin → HOLDOUT-DTI 0.053433 (522 dots on the catalogue),
> 1 px → 0.052112, 3 px → 0.000000. The 3-px screen that the live evidence requires therefore makes
> the holdout blind to this family. Per-class numbers above use no catalogue screen; the delivered
> file does. See IR-58-02.
