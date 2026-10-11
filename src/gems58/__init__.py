"""GEMS58 — ribbon lane.

Emission-width calibration for the DOE GEMS Prize (DrivenData competition 306).

The package implements one lane, end to end:

    ridges  ->  holdout  ->  sigma  ->  allocation  ->  submission

Every score the package prints is labelled either HOLDOUT-DTI (with the
evaluator version, the number of withheld positives and a 95% CI) or
ORGANIZER-CONFIRMED (a receipt copied from the submission page).  Nothing in
this package turns a projection into a score.
"""

__version__ = "58.0.0"
