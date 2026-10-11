# Candidate hypotheses (ranked) — not yet validated unless marked

Ranking = expected DTI improvement x (1 / implementation cost). "Holdout" = hide-and-recover on the
catalogue, four quadrant blocks, leave-one-block-out. No hypothesis below has a holdout result yet
except H0 (the ribbon lane, validated and NEGATIVE).

| id | layer(s) | physical signature | why it could catch a fault missing from USGS/INGENIOUS | how it differs from the repo's existing work | cost | status |
|---|---|---|---|---|---|---|
| H0 | tmi_hg, iso_grav_anom_hg, det_elev_slope | Bright-ridge (Hessian) lineaments, NMS, top-quantile candidates; per-class sigma; dotted/ribbon emission | Geophysical edges need no catalogue | The "ribbon lane" as specified in the session prompt | done | VALIDATED, NEGATIVE: nested holdout DTI 0.037 (CI 0.006-0.068); sigma ~3-4 px, far from the 0.5 px tight-line regime |
| H1 | geod_2ndinv, geod_shearrate, geod_dilaterate | Geodetic strain-rate maxima (GPS/InSAR-derived) localise on active slip; strain highs off the catalogue may mark unmapped active faults | Strain is independent of the mapped trace; unmapped faults with active slip should show it | Current candidates use magnetic/gravity/topo ridges only; strain is never used as a ridge type | low (layers already in stack) | canary alone: mean AUC 0.75, max 0.896 (watch: close to 0.90) — NOT validated |
| H2 | deq_n100a15, ieq_n100a15 | Earthquake density / intensity lineations (distance-to-quake, n=100 km) | Microseismicity aligns with unmapped active structures | Not used as a ridge type; used only as a raw feature in prior work | low | canary mean AUC ~0.70, max 0.89 — NOT validated |
| H3 | 1 m USGS 3DEP DEM (scarp detection) | Fault scarps: step/curvature at 1 m then aggregated to 100 m | Scarps are the surface expression of faults not in the catalogue | Competition gives only links (1m_DEM_links.csv) in the DrivenData data tab (login) | high (download + processing) | NOT validated; data gated |
| H4 | depth_to_base_surf | Basement steps bounding basins | Basin-bounding faults often unmapped | Not used as ridge type | low | canary mean AUC 0.52 — weak; NOT validated |

Decision rule (protocol §6): a hypothesis is promoted only if its nested holdout DTI beats the
current holdout best AND it passes the leakage canary AND the uniqueness check. Negative results are kept.
