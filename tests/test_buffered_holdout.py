import numpy as np
from scipy import ndimage as ndi

from gems57.grid import Grid
from gems57.holdout import build_buffered_holdout_context


def _toy_grid():
    shape = (100, 100)
    footprint = np.ones(shape, dtype=bool)
    catalogue = np.zeros(shape, dtype=bool)

    # NW has two distinct, parallel 10-pixel components exactly 3 px apart;
    # whichever component is withheld, its mapped neighbour must be removed
    # from the feature-visible context collar.
    catalogue[20, 15:25] = True
    catalogue[23, 15:25] = True

    # Two separated components per remaining quadrant make sure visible context
    # remains available while the randomized draw withholds whole components.
    for rows, cols in [((20, 35), (70, 80)),
                       ((65, 80), (15, 25)),
                       ((65, 80), (70, 80))]:
        for row in rows:
            catalogue[row, cols[0]:cols[1]] = True

    return Grid(footprint=footprint, catalogue=catalogue,
                crs=None, transform=None, height=shape[0], width=shape[1])


def test_buffered_context_holds_whole_components_and_never_leaks_collar():
    grid = _toy_grid()
    context = build_buffered_holdout_context(
        grid, hide_frac=0.20, seeds=(4,), buffer_px=3, boundary_px=12)

    assert len(context.cells) == 4
    labels, n_components = ndi.label(grid.catalogue, structure=np.ones((3, 3), dtype=np.uint8))

    for cell in context.cells:
        hidden = context.hidden_by_cell[cell.key]
        visible = context.visible(cell.key)
        # No connected label component is partially withheld.
        for component_id in range(1, n_components + 1):
            component = labels == component_id
            overlap = int((component & hidden).sum())
            assert overlap in (0, int(component.sum()))

        # Feature-visible traces are at least the declared buffer distance from
        # every withheld positive, while the scoring active mask excludes all
        # still-known catalogue pixels exactly.
        distance_to_hidden = ndi.distance_transform_edt(~hidden)
        assert not np.any(visible & (distance_to_hidden <= 3))
        active = cell.active
        visible_crop = visible[cell.bbox]
        known_crop = (grid.catalogue & ~hidden)[cell.bbox]
        assert not np.any(active & visible_crop)
        assert not np.any(active & known_crop)
        assert cell.n_truth > 0
        assert int(cell.active[cell.truth_yx].sum()) == cell.n_truth

    # The deliberately nearby NW trace is a separate whole component, but is
    # absent from feature context because it lies inside the withheld buffer.
    nw = next(cell for cell in context.cells if cell.fold == 0)
    nw_visible = context.visible(nw.key)
    assert not nw_visible[20, 15:25].any()
    assert not nw_visible[23, 15:25].any()
