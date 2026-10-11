"""58GEMSDOE session-5 lane: cross-family structural convergence -> dotted emission.

Adds to (does not fork) the shared ``gems57`` template.  The metric, holdout,
validator, uniqueness gates and fail-closed writer are all imported from
``gems57``; only the new work lives here:

* :mod:`gems60.convergence` -- a *cross-family* lineament field over the
  sha256-pinned official 19-band ``training_features.tif``.  A candidate pixel
  scores higher when independent physical families (magnetic, gravity,
  topographic, subsurface) independently place a lineament there with a
  consistent strike.
* :mod:`gems60.pattern`     -- exact-metric simulation of dotted emission
  geometries as a function of the measured localization error ``sigma``.
* :mod:`gems60.dots`        -- lattice emitter that turns a ranked lineament
  surface into an isolated-dot field.

Rationale (one sentence): the official metric is
``DTI = T / (0.2*(T + sum(1-k_i)) + 0.8*|G|)``, so at fixed dot count the score
is strictly proportional to the *precision* of the emitted dots, and the single
highest-leverage local quantity is therefore a detector that fires on real
faults and not on single-field artefacts.
"""
