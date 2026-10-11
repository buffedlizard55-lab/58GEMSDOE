"""``gems61`` — two sibling session-7 lanes share this package name.

The name is a version tag, not a reference to the separate public repository
``61GEMSDOE``.  Two independently developed lanes live side by side here; both
reuse the shared ``gems57`` metric / holdout / writer and fork nothing:

**A. Deep-edge sigma-ribbon** (this session; modules ``surfaces``, ``sigma_fit``,
``patterns``; runner ``scripts/gems61_deepedge_run.py``).  Hypothesis H7-A:
faults buried under basin fill appear as *step edges* (first-derivative maxima)
on the organizer's subsurface/magnetic-structure surfaces (``depth_to_base_surf``,
``cond_surf``, ``tc``); ribbon width is the measured localisation error
(H7-B, relief-conditioned), pattern choice maximises the exact-metric utility
``U = (1 - 0.2*DTI0)*dTP - 0.2*DTI0*dFP`` (H7-C gap-aware).  Receipts:
``evidence/gems61/{exp1_sigma_canary,exp2_holdout_arms,run_card}.json``.

**B. Extended-evidence ridge lane** (modules ``layers``, ``detect``, ``lane``;
runner ``scripts/gems61_run.py``).  Ridge field over the organizer stack plus
hash-pinned GeoDAWN radiometrics, lidar scarp morphology and DEM/chi metrics;
same sigma-matched ribbon question on ``gems58-pooled-hide-v1``.  Field receipt:
``evidence/gems61/field.json``.

Scoring is always ``gems57.metric`` / ``gems57.evaluate_holdout``, packaging
``gems57.submission_writer``, uniqueness ``gems57.uniqueness`` /
``gems58w.uniqueness``.  Nothing here forks a metric, evaluator or writer.
"""

__version__ = "0.2.0"

__all__ = ["surfaces", "sigma_fit", "patterns", "layers", "detect", "lane"]
