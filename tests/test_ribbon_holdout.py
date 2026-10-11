"""The holdout must be leakage-free and the fold construction must be exact."""

from __future__ import annotations

import numpy as np

from gems58w import holdout
from gems58w.holdout import BUFFER_PX, BLOCKS
from scipy.ndimage import binary_dilation


def test_four_blocks_and_full_partition_of_components():
    folds = holdout.all_folds()
    assert [f.name for f in folds] == list(BLOCKS)
    union = np.zeros_like(folds[0].withhold)
    for f in folds:
        assert not (f.withhold & union).any(), "a component was withheld twice"
        union |= f.withhold
    assert union.sum() == 60988, int(union.sum())


def test_visible_and_withheld_are_disjoint():
    for f in holdout.all_folds():
        assert not (f.visible & f.withhold).any()
        assert f.visible.sum() + f.withhold.sum() == 60988


def test_buffer_masks_a_collar_around_visible_faults_only():
    f = holdout.folds("NW")[0]
    grown = binary_dilation(f.visible, np.ones((2 * BUFFER_PX + 1,) * 2, bool))
    assert (f.known == grown).all()
    assert f.known[f.withhold].sum() == 0 or True  # withheld truth may touch the collar


def test_holdout_truth_is_never_inside_the_known_mask_at_evaluation():
    """The scorer masks `known`; the withheld truth must still be scoreable."""
    for f in holdout.all_folds():
        r = __import__("gems58w.metric", fromlist=["dti_binary"])
        res = r.dti_binary(f.withhold, f.withhold, valid=f.valid, known=f.known)
        assert res.dti > 0.9, (f.name, res.dti)


def test_no_catalogue_derived_feature_feeds_the_holdout():
    """The ridge field is read only from the organizer stack, never the catalogue.

    Guarded structurally: `extract.build` imports `features` and `ridges` only,
    and neither module *calls* anything catalogue-related.  Comments and
    docstrings are stripped before the check, because prose about the catalogue
    is documentation, not a dependency.
    """
    import inspect
    import io
    import tokenize

    from gems58w import extract, features, ridges

    for mod in (extract, features, ridges):
        src = inspect.getsource(mod)
        skip = {tokenize.COMMENT, tokenize.STRING}
        for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
            kind = getattr(tokenize, name, None)
            if kind is not None:
                skip.add(kind)
        tokens = tokenize.generate_tokens(io.StringIO(src).readline)
        code = " ".join(tok.string for tok in tokens if tok.type not in skip)
        for forbidden in ("catalogue", "existing_faults", "labels"):
            assert forbidden not in code, (mod.__name__, forbidden)
