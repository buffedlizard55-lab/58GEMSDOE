"""gems61 — session-6 ribbon lane: sigma-matched dotted ribbons on extended evidence.

This package is part of **58GEMSDOE** (the repository you are in).  The name is a
version tag, not a reference to the separate public repository ``61GEMSDOE``.

What is new here relative to the earlier lanes in this checkout
----------------------------------------------------------------
Earlier lanes in this repository read only the organizer's 19-band numerical
stack.  This lane adds three evidence families that were documented as missing
(``docs/IRREGULARITIES.md`` IR-58-DATA-01) and that the owner already publishes,
hash-pinned, as mirrors on the study grid:

* ``geodawn_rad_u8.tif``      K, Th, U, TC      -- GeoDAWN aeroradiometric channels
* ``lidar_scarp_features_u8.tif`` 12 bands      -- lidar scarp morphology
* ``geodawn_dem_a2_100m.tif`` + ``dem10_chi_100m_u8.tif`` -- DEM and channel metrics

Every layer is reused, never rebuilt: ridge extraction delegates to
``gems58w.ridges``, scoring to ``gems57.metric`` / ``gems57.evaluate_holdout``,
the holdout split to ``gems58w.holdout`` (``gems58-pooled-hide-v1``), packaging to
``gems57.submission_writer``, and the uniqueness instrument to
``gems57.uniqueness``.  Nothing here forks those tools.

The lane question
-----------------
"Match emission width to the measured localisation error": measure the
across-strike distance between each candidate ridge and the nearest *withheld*
segment by data block, feature resolution and ridge type, fit ``sigma(x)``, and
choose per class the number and offset of parallel dotted lines that maximise the
exact-metric utility ``U = (1 - 0.2*DTI0)*dTP - 0.2*DTI0*dFP``.
"""

__all__ = ["layers", "detect", "lane"]
