# Archived earlier attempts - DO NOT SUBMIT
The current validated submission lives in docs/downloads/ (linked from docs/index.html).

## gems58-ribbon-concordant-20261011T011033Z-b8d1faa5-zeros (archived 2026-10-11, session 2)
The ribbon lane's own holdout measurement is why it is archived, not a format problem: its truth-free
live rule scored 0.1309 pooled (HOLDOUT-DTI, `evidence/ribbon_e2c_liverule_variants.json`), BELOW its own
single-tight-line baseline of 0.1573, because it emitted on every candidate ridge with no ranking.
Evidence: `evidence/ribbon_e1_sigma.json`, `evidence/ribbon_e2_arms.json`, `evidence/ribbon_uniqueness.json`.

## 2026-10-11, session 2 — intermediate copies of the PROX emission were deleted, not archived
`gems58-prox-dot36k-…T023751Z…` and `…T025831Z…` were byte-identical rebuilds of the shipped
`docs/downloads/gems58-prox-dot36k-…T030218Z-…-zeros.tif` (same sha256
`aac8aa8a021ee309c91c5084f17ff2d64623163faa382cfd76ca781352d945b8`; only the receipt's note text differed).
They were removed so that the Downloads section cannot be mistaken about which file to submit. The
evidence chain for all three is `evidence/model_e3.json`.
