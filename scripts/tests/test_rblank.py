import os, sys, numpy as np, pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rblank, rule55


def synth(um=9.362, rows=3, cols=3, margin_blank=0.0, margin_inked=0.20, inked_cols=(2,)):
    side = rule55.unit_side(um)
    H, W = side * rows, side * cols
    fwd = np.zeros((H, W), np.uint8); rev = np.zeros((H, W), np.uint8)
    lab = np.zeros((H, W), bool)
    for r in range(rows):
        for c in range(cols):
            m = margin_inked if c in inked_cols else margin_blank
            base = 0.40
            fwd[r*side:(r+1)*side, c*side:(c+1)*side] = int(round((base + m/2) * 255))
            rev[r*side:(r+1)*side, c*side:(c+1)*side] = int(round((base - m/2) * 255))
            if c in inked_cols:
                lab[r*side:r*side+50, c*side:c*side+50] = True
    return fwd, rev, lab, side


def test_blank_and_inked_sets_are_separated_by_the_labels():
    fwd, rev, lab, side = synth()
    out, phi, t = rblank.measure(fwd, rev, lab, 9.362)
    assert out["n_valid"] == 9
    assert out["n_blank_units"] == 6 and out["n_inked_units"] == 3
    assert out["blank"]["median_phi"] == 0.0
    assert out["inked"]["median_phi"] > 0.0


def test_blank_baseline_is_the_median_margin_of_zero_ink_units():
    fwd, rev, lab, side = synth(margin_blank=0.0)
    out, _, _ = rblank.measure(fwd, rev, lab, 9.362)
    assert abs(out["blank"]["median_margin"]) < 0.005
    assert out["outcome"] == "DETECTOR-FLOOR-AT-OR-BELOW-CORPUS"


def test_a_high_blank_floor_returns_the_other_outcome():
    fwd, rev, lab, side = synth(margin_blank=0.05)
    out, _, _ = rblank.measure(fwd, rev, lab, 9.362)
    assert out["blank"]["median_margin"] > rblank.BASELINE_BAR
    assert out["outcome"] == "DETECTOR-FLOOR-ABOVE-CORPUS"


def test_too_few_blank_units_is_UNDERPOWERED_not_a_conclusion():
    fwd, rev, lab, side = synth(inked_cols=(0, 1, 2))     # every unit carries a label
    out, _, _ = rblank.measure(fwd, rev, lab, 9.362)
    assert out["n_blank_units"] == 0
    assert out["outcome"] == "UNDERPOWERED"
    assert "UNDERPOWER" in out["outcome"] and "conclusion" not in out


def test_the_bar_is_three_times_the_recorded_corpus_margin_and_is_not_computed_from_the_data():
    assert rblank.CORPUS_MARGIN == 0.0014
    assert abs(rblank.BASELINE_BAR - 0.0042) < 1e-12


def test_grid_is_the_frozen_rule55_grid_not_a_new_one():
    fwd, rev, lab, side = synth()
    out, _, _ = rblank.measure(fwd, rev, lab, 9.362)
    onsheet = (fwd > 0) | (rev > 0)
    assert out["side_px"] == rule55.unit_side(9.362)
    assert tuple(out["origin"]) == tuple(rule55.best_origin(onsheet, out["side_px"])[0])


def test_any_over_z_projection_unions_every_slice():
    import zarr, tempfile
    d = tempfile.mkdtemp()
    g = zarr.open_group(os.path.join(d, "l.zarr"), mode="w")
    mk = getattr(g, "create_array", None) or g.create_dataset
    a = mk("0", shape=(4, 8, 8), dtype="uint8", chunks=(1, 8, 8))
    a[1, 0, 0] = 255; a[3, 7, 7] = 255
    m = rblank.labels_any_over_z(os.path.join(d, "l.zarr"), (8, 8))
    assert m[0, 0] and m[7, 7] and m.sum() == 2
