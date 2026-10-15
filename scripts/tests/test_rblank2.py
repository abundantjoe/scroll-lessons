import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rblank2, rule55

UM = 9.362


def canvas(cols, margins, ink_cols, rows=1):
    """cols units wide; margins[c] is the depth margin of column c; ink_cols get a labelled ink block."""
    side = rule55.unit_side(UM)
    H, W = side * rows, side * cols
    fwd = np.zeros((H, W), np.uint8); rev = np.zeros((H, W), np.uint8); lab = np.zeros((H, W), bool)
    for c in range(cols):
        m = margins[c]
        fwd[:, c*side:(c+1)*side] = int(round((0.40 + m/2) * 255))
        rev[:, c*side:(c+1)*side] = int(round((0.40 - m/2) * 255))
        if c in ink_cols:
            lab[0:64, c*side:c*side+64] = True
    return fwd, rev, lab, side


def test_distance_is_conservative_max_pooling_can_only_shrink_it():
    lab = np.zeros((64, 64), bool); lab[32, 32] = True
    dsmall, pool = rblank2.pooled_distance_um(lab, UM, pool=8)
    d = np.kron(dsmall, np.ones((pool, pool), np.float32))[:64, :64]
    true_d = np.hypot(*np.meshgrid(np.arange(64)-32, np.arange(64)-32, indexing="ij")) * UM
    assert (d <= true_d + 1e-3).all(), "pooled distance must never exceed the true distance"
    assert d[32, 32] == 0.0


def test_the_conservative_bound_holds_for_many_random_ink_layouts():
    rng = np.random.default_rng(7)
    ys, xs = np.meshgrid(np.arange(96), np.arange(96), indexing="ij")
    for _ in range(12):
        lab = np.zeros((96, 96), bool)
        pts = rng.integers(0, 96, size=(3, 2))
        for y, x in pts:
            lab[y, x] = True
        dsmall, pool = rblank2.pooled_distance_um(lab, UM, pool=8)
        d = np.kron(dsmall, np.ones((pool, pool), np.float32))[:96, :96]
        true_d = np.min([np.hypot(ys - y, xs - x) for y, x in pts], axis=0) * UM
        assert (d <= true_d + 1e-3).all(), "the pooled distance must be a LOWER bound on the true one"


def test_pooling_keeps_every_row_and_column_of_a_canvas_that_is_not_a_multiple_of_the_pool():
    lab = np.zeros((755, 999), bool); lab[0, 0] = True
    dsmall, pool = rblank2.pooled_distance_um(lab, UM, pool=8)
    assert dsmall.shape == (95, 125)          # ceil(755/8), ceil(999/8): nothing dropped
    dm = rblank2.unit_min_distance(dsmall, pool, (1, 1), 755, (0, 0))
    assert dm[0, 0] == 0.0


def test_bands_are_the_declared_cut_points():
    assert rblank2.BAND_NAMES == ("touching ink", ">0-1 mm", "1-2 mm", "2-4 mm", ">=4 mm")
    assert rblank2.BANDS[3] == (2000.0, 4000.0)
    assert rblank2.MIN_BAND_N == 5 and abs(rblank2.BAR - 0.0042) < 1e-12


def test_a_margin_that_decays_with_distance_returns_FLOOR_EXPLAINED():
    cols = 12
    margins = [0.20] + [0.001] * (cols - 1)       # only the ink column is hot; everything far is at ~0
    fwd, rev, lab, side = canvas(cols, margins, ink_cols=(0,))
    out, dmin, t = rblank2.measure(fwd, rev, lab, UM)
    far = [b for b in out["bands"] if b["n"] >= 5 and b["band"] != "touching ink"]
    assert far, out["bands"]
    assert out["outcome"] == "FLOOR-EXPLAINED-BY-UNLABELLED-INK", out


def test_a_margin_that_does_not_decay_returns_FLOOR_NOT_EXPLAINED():
    cols = 12
    margins = [0.05] * cols                        # every column hot, ink only in column 0
    fwd, rev, lab, side = canvas(cols, margins, ink_cols=(0,))
    out, dmin, t = rblank2.measure(fwd, rev, lab, UM)
    assert out["outcome"] == "FLOOR-NOT-EXPLAINED-BY-PROXIMITY", out


def test_too_few_far_units_is_UNDERPOWERED():
    cols = 2
    fwd, rev, lab, side = canvas(cols, [0.05, 0.05], ink_cols=(0,))
    out, dmin, t = rblank2.measure(fwd, rev, lab, UM)
    assert out["outcome"] == "UNDERPOWERED", out


def test_unit_distance_is_the_minimum_over_its_pixels():
    cols = 6
    fwd, rev, lab, side = canvas(cols, [0.01]*cols, ink_cols=(0,))
    out, dmin, t = rblank2.measure(fwd, rev, lab, UM)
    assert dmin[0, 0] == 0.0                                  # the unit holding the ink touches it
    assert dmin[0, 1] > 0.0 and dmin[0, 1] < dmin[0, 2]       # distance grows away from it


def test_grid_is_the_frozen_grid():
    fwd, rev, lab, side = canvas(6, [0.01]*6, ink_cols=(0,))
    out, _, _ = rblank2.measure(fwd, rev, lab, UM)
    assert out["side_px"] == rule55.unit_side(UM)
