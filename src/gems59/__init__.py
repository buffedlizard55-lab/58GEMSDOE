"""58GEMSDOE session-2 lane: supervised geophysical ranking + metric-optimal emission.

Adds to (does not fork) the shared ``gems57`` template: the metric, holdout,
validator, uniqueness gates and fail-closed writer are all imported from
``gems57``.  Only new work lives here:

* :mod:`gems59.features` -- block-wise feature stack over the sha256-pinned
  official ``training_features.tif`` (19 GeoDAWN bands + structure-tensor and
  texture operators).
* :mod:`gems59.rank`      -- spatially-blocked per-pixel fault ranking.
* :mod:`gems59.emit59`    -- exact-metric threshold/lattice sweep and greedy
  allocation on the hide-and-recover holdout.
"""
