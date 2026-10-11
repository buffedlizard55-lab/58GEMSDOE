"""Exact incremental accounting for binary dot emission under the official DTI.

Why this module exists
----------------------
The ribbon lane has to decide, per ridge segment, **how many parallel dotted
lines to emit and at what across-strike offsets**.  The decision rule is the
official metric's own marginal test, ``U = (1 - alpha*DTI0)*dTP - alpha*DTI0*dFP > 0``,
evaluated on *exact* ``dTP``/``dFP``.  Approximations (a Normal model of the
across-strike offset, or a per-pair FP term that ignores interaction between
lines) were the documented failure mode of the archived ``gems58w.allocation``
allocator, so this module keeps the accounting exact and shared:

* ``dTP`` is computed against a running per-truth-pixel max credit, i.e. the
  official ``max_x p(x) k(d(x,g))`` is reproduced pixel by pixel;
* ``dFP`` uses the official per-dot self-credit ``max_g k(d(x,g))``, so two
  lines that reach the same truth pixel are costed independently and their
  redundancy shows up in ``dTP``, exactly as the metric does it;
* the acceptance test is delegated to :func:`gems57.metric.marginal_accept`,
  which recomputes the DTI before and after rather than re-deriving algebra.

Nothing here is a scoring fork: the final score of any pattern produced by this
module must still be measured by :func:`gems57.evaluate_holdout.evaluate` /
:func:`gems57.metric.dti_binary`.  This module only *proposes* patterns.

Conventions
-----------
* A "dot" is one grid cell emitted at value ``1.0``.  Scaling an included dot
  down only scales the net gain down (see ``gems57.submission_writer``), so the
  only decision is inclusion at 1.0.
* ``active`` is the scored domain: inside the competition footprint and not on
  the organiser-masked known faults.  Both dots and truth are restricted to it,
  matching ``gems57.evaluate_holdout``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt

from .metric import (ALPHA, BETA, EPS, OFF_DX, OFF_DY, OFF_K, kernel,
                     marginal_accept)

__all__ = ["DotLedger", "arm_deltas", "PlanStep", "greedy_arms",
           "sorted_greedy_arms"]


class DotLedger:
    """Running exact ``(T, M, n)`` ledger for a binary dot field on one fold.

    Attributes
    ----------
    T
        ``TP_w = sum_g max_x k(d(x,g))`` over the truth pixels of the fold.
    M
        ``sum_x max_g k(d(x,g))`` over the emitted dots (self-credit mass).
    n
        number of emitted dots.
    K
        ``|G|``, the number of truth pixels in the scored domain.

    ``FP_w = n - M`` and ``FN_w = K - T`` by construction, so the exact DTI is
    recovered by :meth:`dti` without touching the raster again.
    """

    def __init__(self, truth: np.ndarray, active: np.ndarray):
        truth = np.asarray(truth, bool) & np.asarray(active, bool)
        self.active = np.asarray(active, bool)
        self.truth = truth
        self.shape = truth.shape
        self.K = int(truth.sum())

        # ordinal -> (row, col) for truth cells; -1 elsewhere
        self._index = np.full(truth.shape, -1, np.int32)
        yy, xx = np.nonzero(truth)
        self._index[yy, xx] = np.arange(yy.size, dtype=np.int32)
        self.best = np.zeros(yy.size, np.float64)

        # per-cell self-credit q(x) = max_g k(d(x,g)); zero where no truth in range
        dg = distance_transform_edt(~truth) if self.K else np.full(truth.shape, np.inf)
        self.q = np.where(self.active, kernel(dg), 0.0).astype(np.float64)

        self.T = 0.0
        self.M = 0.0
        self.n = 0

    # ------------------------------------------------------------------
    def dti(self) -> float:
        den = self.T + ALPHA * (self.n - self.M) + BETA * (self.K - self.T) + EPS
        return float(self.T / den)

    def terms(self) -> tuple[float, float, float, int]:
        """``(TP_w, FP_w, FN_w, |G|)`` of the current ledger."""
        return float(self.T), float(self.n - self.M), float(self.K - self.T), self.K

    # ------------------------------------------------------------------
    def delta(self, rows: np.ndarray, cols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Exact ``(dT, k_self)`` for each candidate dot, against the *current* state.

        ``dT`` is the increase in ``TP_w`` if that dot alone were added; it is
        zero wherever an already-emitted dot reaches the same truth pixel with
        at least as much credit.  ``k_self`` is the official per-dot self-credit
        ``max_g k(d(x,g))``.  Candidates outside the active domain return
        ``(0, 0)``.
        """
        rows = np.asarray(rows, np.int64)
        cols = np.asarray(cols, np.int64)
        h, w = self.shape
        dT = np.zeros(rows.shape, np.float64)
        kself = np.zeros(rows.shape, np.float64)
        inb = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
        if not inb.any():
            return dT, kself
        rr, cc = rows[inb], cols[inb]
        pos = np.flatnonzero(inb)
        live = self.active[rr, cc]
        kself[inb] = np.where(live, self.q[rr, cc], 0.0)
        sub = np.zeros(rr.shape, np.float64)
        for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
            ny = rr + dy
            nx = cc + dx
            ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
            if not ok.any():
                continue
            ti = self._index[ny[ok], nx[ok]]
            hit = ti >= 0
            if not hit.any():
                continue
            gain = np.maximum(k - self.best[ti[hit]], 0.0)
            np.add.at(sub, pos[ok][hit], gain)
        dT[inb] = np.where(live, sub, 0.0)
        return dT, kself

    def apply(self, rows: np.ndarray, cols: np.ndarray, dT: np.ndarray,
              kself: np.ndarray, mask: np.ndarray | None = None) -> int:
        """Commit the dots selected by ``mask`` (default: all) to the ledger."""
        rows = np.asarray(rows, np.int64)
        cols = np.asarray(cols, np.int64)
        sel = np.ones(rows.shape, bool) if mask is None else np.asarray(mask, bool)
        if not sel.any():
            return 0
        r, c = rows[sel], cols[sel]
        h, w = self.shape
        for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
            ny = r + dy
            nx = c + dx
            ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
            if not ok.any():
                continue
            ti = self._index[ny[ok], nx[ok]]
            hit = ti >= 0
            if not hit.any():
                continue
            np.maximum.at(self.best, ti[hit], k)
        self.M += float(kself[sel].sum())
        self.n += int(sel.sum())
        # recompute T from the ledger to avoid accumulating float error
        self.T = float(self.best.sum())
        return int(sel.sum())

    def delta_batch(self, rows: np.ndarray, cols: np.ndarray
                    ) -> tuple[float, np.ndarray]:
        """Exact ``(dT_total, k_self)`` for a **batch** of dots added together.

        A batch cannot be scored by summing the per-dot ``delta``: two dots of
        the same parallel line reach the same truth pixel, and the official
        ``max_x`` would count that pixel once.  This routine therefore forms
        ``reach[g] = max over (dot, offset) of k`` and returns
        ``sum_g max(reach[g] - best[g], 0)``, which is exactly the increment
        :meth:`apply` realises.
        """
        rows = np.asarray(rows, np.int64)
        cols = np.asarray(cols, np.int64)
        h, w = self.shape
        inb = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
        if not inb.any():
            return 0.0, np.zeros(rows.shape, np.float64)
        rr, cc = rows[inb], cols[inb]
        live = self.active[rr, cc]
        if not live.any():
            return 0.0, np.zeros(rows.shape, np.float64)
        rr, cc = rr[live], cc[live]
        reach = np.zeros(self.best.shape, np.float64)
        for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
            ny = rr + dy
            nx = cc + dx
            ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
            if not ok.any():
                continue
            ti = self._index[ny[ok], nx[ok]]
            hit = ti >= 0
            if not hit.any():
                continue
            np.maximum.at(reach, ti[hit], float(k))
        dT = float(np.maximum(reach - self.best, 0.0).sum())
        kself = np.zeros(rows.shape, np.float64)
        kself[np.flatnonzero(inb)[live]] = self.q[rr, cc]
        return dT, kself

    def accept(self, dT: float, k_self: float) -> bool:
        """The official marginal test for **one** dot.

        Delegates to :func:`gems57.metric.marginal_accept`, which recomputes the
        DTI before and after instead of re-deriving the algebra.
        """
        return bool(marginal_accept(float(dT), float(k_self), self.T, self.M, self.n,
                                    self.K, alpha=ALPHA, beta=BETA))

    def accept_batch(self, dT: float, k_sum: float, m: int) -> bool:
        """The same test for a batch of ``m`` dots (one parallel line, or one arm).

        ``marginal_accept`` hard-codes ``n -> n + 1``; a whole line moves the
        denominator by ``alpha*(dT + m - k_sum)`` instead, so the two-sided test
        is recomputed here against the very same components.
        """
        dT = float(dT)
        k_sum = float(k_sum)
        m = int(m)
        D0 = self.T + ALPHA * (self.n - self.M) + BETA * (self.K - self.T) + EPS
        D1 = ((self.T + dT) + ALPHA * ((self.n + m) - (self.M + k_sum))
              + BETA * (self.K - self.T - dT) + EPS)
        return bool((self.T + dT) / D1 > self.T / D0)


@dataclass
class PlanStep:
    """One accepted emission arm (a parallel dotted line offset from a ridge)."""

    seg_id: int
    offset_px: float
    n_dots: int
    dT: float
    k_self: float
    dti_before: float
    dti_after: float


def arm_deltas(ledger: DotLedger, arms: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """``(dT, k_self)`` per arm; an arm is an ``(m, 2)`` array of ``(row, col)``.

    Arms are evaluated one at a time against the *same* ledger state, so the
    returned values are valid simultaneously only when the arms do not compete
    for the same truth credit.  :func:`greedy_arms` re-evaluates after every
    acceptance, which is what makes its result exact.
    """
    dTs = np.zeros(len(arms), np.float64)
    ks = np.zeros(len(arms), np.float64)
    for i, a in enumerate(arms):
        if a.size == 0:
            continue
        a = np.asarray(a, np.int64).reshape(-1, 2)
        dT, kself = ledger.delta_batch(a[:, 0], a[:, 1])
        dTs[i] = float(dT)
        ks[i] = float(np.maximum(kself, 0.0).sum())
    return dTs, ks


def greedy_arms(ledger: DotLedger, arms: list[np.ndarray], keys: list[tuple],
                max_dots: int | None = None, min_gain: float = 0.0,
                order: np.ndarray | None = None) -> list[PlanStep]:
    """Exact lazy greedy (CELF) over whole arms -- one arm is one parallel dotted line.

    Each arm is accepted or rejected with the official batch marginal test
    (:meth:`DotLedger.accept_batch`) applied to its *exact* ``(dT, k_self)``
    against the ledger as it stands at that moment, so redundancy between
    neighbouring lines and between segments is accounted for exactly.

    Because a truth pixel can only switch from uncovered to covered, ``dT`` for
    any fixed arm is non-increasing as other arms are accepted and the DTI bar
    is non-decreasing.  A cached ``dT`` is therefore a valid *upper* bound, and
    re-evaluating only the current best candidate until it is exact is the
    standard lazy-greedy shortcut: it returns the same decisions as a full
    re-sort at every step.
    """
    import heapq

    n = len(arms)
    sizes = np.array([np.asarray(a, np.int64).reshape(-1, 2).shape[0] for a in arms],
                     dtype=np.int64)
    order = list(range(n)) if order is None else [int(i) for i in order]
    bound = np.full(n, np.nan, np.float64)
    stamp = np.full(n, -1, np.int64)
    epoch = 0
    heap: list[tuple[float, int]] = []
    for i in order:
        if sizes[i] == 0:
            bound[i] = -np.inf
            continue
        heapq.heappush(heap, (0.0, i))       # lazy: bound filled on first pop
    steps: list[PlanStep] = []
    emitted = 0
    while heap:
        _, i = heapq.heappop(heap)
        if np.isinf(bound[i]) and bound[i] < 0:
            continue
        if stamp[i] < epoch or np.isnan(bound[i]):
            a = np.asarray(arms[i], np.int64).reshape(-1, 2)
            dT, _ = ledger.delta(a[:, 0], a[:, 1])
            bound[i] = float(dT.sum())          # upper bound: ignores intra-arm overlap
            stamp[i] = epoch
            heapq.heappush(heap, (-bound[i], i))
            continue
        a = np.asarray(arms[i], np.int64).reshape(-1, 2)
        if bound[i] <= min_gain:
            continue
        if max_dots is not None and emitted + a.shape[0] > max_dots:
            continue
        d_sum, kself = ledger.delta_batch(a[:, 0], a[:, 1])
        kself = np.maximum(kself, 0.0)
        k_sum = float(kself.sum())
        before = ledger.dti()
        if not ledger.accept_batch(d_sum, k_sum, int(a.shape[0])):
            bound[i] = -np.inf
            continue
        _, dT = ledger.delta(a[:, 0], a[:, 1])
        ledger.apply(a[:, 0], a[:, 1], dT, kself)
        emitted += int(a.shape[0])
        epoch += 1
        steps.append(PlanStep(seg_id=int(keys[i][0]), offset_px=float(keys[i][1]),
                              n_dots=int(a.shape[0]), dT=d_sum, k_self=k_sum,
                              dti_before=before, dti_after=ledger.dti()))
    return steps


def sorted_greedy_arms(ledger: DotLedger, arms: list[np.ndarray], keys: list[tuple],
                       max_dots: int | None = None, min_gain: float = 0.0,
                       block: int = 4096) -> list[PlanStep]:
    """Single-pass greedy: rank arms by their initial ``dT``, then accept in order.

    This is the same accept/reject rule as :func:`greedy_arms` -- the exact
    batch test :meth:`DotLedger.accept_batch` against the ledger as it stands --
    but the ranking is computed once instead of lazily re-sorted after every
    acceptance.  Because a truth pixel can only go from uncovered to covered, a
    stale ``dT`` is an *upper* bound, so ranking once and re-evaluating exactly
    at the moment of decision is a valid greedy; it yields the same arm set as
    the lazy variant whenever the ranking is not changed by earlier acceptances,
    and costs O(number of arms) ``delta`` calls instead of O(arms x acceptances).

    Use it when the arm count makes the lazy variant intractable.  Both routines
    apply the identical acceptance test, so neither is a scoring fork.
    """
    n = len(arms)
    dTs = np.zeros(n, np.float64)
    for i in range(n):
        a = np.asarray(arms[i], np.int64).reshape(-1, 2)
        if a.size == 0:
            dTs[i] = -np.inf
            continue
        dT, _ = ledger.delta(a[:, 0], a[:, 1])
        dTs[i] = float(dT.sum())            # upper bound (intra-arm overlap ignored)
    order = np.argsort(-dTs, kind="stable")
    steps: list[PlanStep] = []
    emitted = 0
    for i in order:
        if dTs[i] <= min_gain:
            break
        a = np.asarray(arms[i], np.int64).reshape(-1, 2)
        if a.size == 0:
            continue
        if max_dots is not None and emitted + a.shape[0] > max_dots:
            continue
        d_sum, kself = ledger.delta_batch(a[:, 0], a[:, 1])
        kself = np.maximum(kself, 0.0)
        k_sum = float(kself.sum())
        before = ledger.dti()
        if not ledger.accept_batch(d_sum, k_sum, int(a.shape[0])):
            continue
        _, dT = ledger.delta(a[:, 0], a[:, 1])
        ledger.apply(a[:, 0], a[:, 1], dT, kself)
        emitted += int(a.shape[0])
        steps.append(PlanStep(seg_id=int(keys[i][0]), offset_px=float(keys[i][1]),
                              n_dots=int(a.shape[0]), dT=d_sum, k_self=k_sum,
                              dti_before=before, dti_after=ledger.dti()))
    return steps
