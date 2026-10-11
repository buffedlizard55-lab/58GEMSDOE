# Irregularities log (58GEMSDOE)

Each entry: what was observed, how it was verified, and the action taken.
Newest last. Nothing here is a score.

1. **IR-58-DATA-01 — public `labels.tif` is the catalogue, not hidden truth.**
   `data/official/labels.tif` is byte-identical to `data/official/existing_faults.tif`
   (both sha256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`,
   verified locally at clone time and documented in `src/gems57/grid.py`).
   Consequence: the scored truth raster is not published anywhere public, so all
   model quality numbers in this repo are HOLDOUT-DTI on the hide-and-recover
   instrument, never leaderboard projections.

2. **IR-58-RATE-01 — GitHub REST API budget exhausted at run time.**
   `scripts/restore_registry_cache.py` (the shared template tool) failed with
   "API rate limit exceeded" for all 695 blobs because the token budget is
   shared across parallel sibling sessions. Action: wrote
   `scripts/fetch_registry_sparse.py`, which fetches the same pinned bytes over
   the git protocol (`git clone --depth 1 --filter=blob:none --no-checkout` +
   no-cone sparse checkout). Every file is still sha256-verified against the
   registry pin before caching (695/695 restored, 0 mismatches). The shared
   tool was NOT forked for scoring logic; only the transport was added.

3. **IR-58-REG-01 — one registry-pinned path no longer exists on its repo's `main`.**
   `55GEMSDOE:docs/downloads/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif`
   (pin `927dc17f...`) is absent from 55GEMSDOE's current `main`; the registry
   snapshot pins commit `d92606c2`. Action: fetched the pinned commit directly
   (`git fetch --depth 1 origin d92606c2...`), extracted the blob, verified
   sha256 matches the pin exactly, cached it. Flagged for review: sibling repos
   rewriting/removing rasters on `main` can silently shrink future registry
   scans that, unlike this one, do not fall back to pinned commits.

4. **IR-58-BAR-01 — denominator algebra of the marginal acceptance test.**
   An in-session bug in the local bookkeeping (`CellState.dti` using
   `beta*fn` instead of `beta*K`) was caught by the state-vs-shared-evaluator
   equality check (`score_cell` from `gems57.holdout`) and fixed; final cell
   TP/FP/DTI agree bit-for-bit with the shared exact evaluator. The exact
   acceptance test itself (`exact_accept`) used the correct algebra throughout
   (`D = alpha*(T + FP) + beta*K`, with `FP = n - M`), consistent with
   `src/gems57/metric.py`'s derivation and its brute-force oracle tests.

5. **IR-58-SGMC-01 — inherited finding retained from the template.**
   The template documents (`src/gems57/offcatalogue.py`, IR-57-SGMC-01) that
   `derived_sgmc_faults_100m.tif` in sibling repos is a ~1 px dilation of SGMC,
   not "SGMC minus the mapped union" as described. This lane therefore reads
   the pinned `sgmc_faults_100m.tif` directly and derives
   `sgmc & ~catalogue` itself. No derived file is trusted.

6. **IR-58-PARALLEL-01 — sibling-lane collision risk.**
   The sibling lane h58 (fault-zone anatomy, damage-zone envelope, repo
   57GEMSDOE `docs/data/h58_*`) is a different lane; its run card and uniqueness
   audit were read to avoid duplication. The ribbon lane's ridge sources
   (skeleton axes) and placement (parallel dotted lines) differ from h58's
   length-law damage-zone envelope; the registry scan is the arbiter.

7. **IR-58-UNIQ-01 — the literal 3-px overlap gate is degenerate for fault-adjacent lanes.**
   The candidate (67,379 dots) was scanned against all 695 hash-verified registry
   rasters (complete scan, 0 hash mismatches). Max Spearman rho = 0.190
   (limit 0.90): no surface correlation with any prior raster. But 123 rasters
   flag `duplicate_by_overlap`: 104 are dense soft surfaces (>=200k positive
   cells, e.g. `GEMSDOE2:.../turbo-simple-*` overlap 1.00 with ANY
   near-catalogue emission) and 19 are broad near-catalogue carpets from other
   lanes. Vs the proven dotted-ridge lineage the overlap is far under the 0.70
   limit (h27-4: 0.474, h19-5: 0.375, h32: 0.353, dotted-h19-5: 0.352,
   d28-poisson300m: 0.336, h36-1-rung30: 0.250, anderson: 0.198). The sibling
   h58 lane hit the identical wall (95 flags, worst overlap 1.0 vs the same
   `turbo-simple` rasters, verdict negative) and shipped with the verdict
   documented. Per the template's own uniqueness module docstring, the audit
   reports the problem rather than quietly changing the protocol: the run card
   verdict is therefore NEGATIVE on the literal gate, with the drift forensic
   attached. Suggested protocol fix for the owner: exempt dense soft surfaces
   (>=200k dots) from the forward-overlap gate or scope it to sparse (dot-like)
   registry rasters.

8. **IR-58-PROC-01 — surface-before-placement check was done after placement.**
   Rule 1 asks for the uniqueness check on the pre-placement surface AND on the
   final dots; this lane ran it on the final dots only (the pre-placement soft
   surface was never an artifact here — the lane places binary dots directly).
   Recorded as a process gap; the final-dots check is the binding one and it is
   complete (695/695).
