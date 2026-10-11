# Candidate hypotheses (generated before implementing anything new)

Band numbers are 1-based indices into the official 19-band stack (`training_features.tif`; band
descriptions from the file tags — see `docs/sources.md` B4). Ranking: expected DTI gain × probability
of success ÷ implementation cost. Only the first is the ribbon lane tested in this session.

| Rank | Hypothesis | Layers | Physical signature targeted | Why it should find a fault missing from INGENIOUS | Difference from what exists in this repo | Cost | Validatable here? |
|---|---|---|---|---|---|---|---|
| H1 | **Finer-scale magnetic edges, then ribbon emission.** A fault's magnetic edge at native grid resolution is narrower than the 100 m grid; the 100 m edge response (band 3, "horizontal gradient") smears it. | Raw GeoDAWN magnetic grids (USGS DOI 10.5066/P93LGLVQ) → recompute THD / tilt | Narrow linear magnetic lows/highs along strike; sharp tilt-angle zero crossings | Catalogue-independent: magnetic edges come from the survey, not from mapped traces, so uncatalogued faults are candidates | Current stack is 100 m only; this would be a new feature resolution | Medium (download of 42 MB + 227 MB zips, gridding, re-run) | **No — needs the USGS grids, which the sandbox cannot reach.** The ribbon-lane σ table in this build is the test that decides whether it is worth doing. |
| H2 | **Basement-step lines.** A normal fault offsets the basement; the gradient of depth-to-basement (band 15) traces the step. | Band 15 "Depth to basement surface" (|∇|) | Linear sediment-thickness discontinuity | Uses no fault catalogue, so it can find faults the catalogue lacks | Current ridges use bands 3 and 12 only | Low (one band, one gradient) | Yes, on the holdout (planned). |
| H3 | **Strike-prior from visible faults only.** Orient candidate ridges that lie near *visible* faults to the local visible strike ±20°; use no withheld truth. | Visible catalogue (only the other blocks in hide-and-recover) + candidate ridges | Fault-parallel alignment of ridge candidates within 10 px of known traces | Catalogue-derived, but only from visible faults, so it can extend known traces along strike into the gaps | Current pipeline has no catalogue-derived feature | Low–medium | Yes, under the buffer rule (5 px). |
| H4 | **Coincidence gating across physics.** Keep a ridge only if magnetic edge (band 3) and gravity horizontal gradient (band 18) peaks coincide within 2 px. | Bands 3 + 18 | Co-located magnetic and gravity discontinuities | Physically independent methods agreeing; unlikely to be produced by a single noise source | Other lanes in the GEMSDOE registry use multi-physics unions and corroboration (see the registry); overlap risk high | Low | Yes; check overlap with the registry before placement. |
| H5 | **Radiometric / conductivity edges** (bands 17 "Conductivity surface"; 19 "Detrended elevation slope"). | Bands 17, 19 | Alteration or conductive zones along faults | Independent of magnetic and topographic evidence | Not yet used | Low | Yes. |

## Non-fault processes that could mimic each signature (named, as required)

- H1/H2: lithologic contacts (dykes, plutons, basalt margins) and sediment-thickness changes at basin margins.
- H3: topographic lineaments from erosion and drainage, and mapped-trace extrapolation errors.
- H4: a single noise source appearing in both fields (e.g., flight-line artifacts or gridding edges).
- H5: hydrothermal alteration without faulting, and soil/vegetation cover.

## Priority

1. H2 is the cheapest validatable test; it is planned as the next experiment.
2. H3 has the best chance to add catalogue-aware skill without leaking truth; implement after H2.
3. H1 is the highest expected value, because the ribbon-lane σ table shows that the 100 m ridge candidates
   have no measurable localization skill at all (see `reports/ribbon_lane_report.json`). But it cannot be validated
   in this sandbox, so the action item is data access (see README "Limitations").
