"""Tests for examples/window_label_stats.py: synthetic labels on a canvas just larger than the quick-start window
(15 x 3644 x 4144), with known supervised and ink fractions inside the window and decoys outside it."""
import os, sys
import numpy as np, zarr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "examples"))
import window_label_stats as W  # noqa: E402


def make_labels(d, ink_fill, sup_fill):
    paths = []
    for name, fill in (("ink.zarr", ink_fill), ("sup.zarr", sup_fill)):
        g = zarr.open_group(os.path.join(d, name), mode="w")
        a = g.create_array("0", shape=(15, W.Y1 + 8, W.X1 + 8), chunks=(1, 512, 512), dtype="uint8", fill_value=0)
        fill(a)
        paths.append(os.path.join(d, name))
    return paths


def test_fractions_and_unit_phi_are_measured_on_the_window_and_slice_only(tmp_path, capsys):
    s = W.SIDE_05

    def ink(a):
        a[W.SLICE, W.Y0:W.Y0 + s, W.X0:W.X0 + s // 2] = 255       # unit (0,0): half ink
        a[W.SLICE, W.Y0 + s:W.Y0 + 2 * s, W.X0:W.X0 + s] = 100     # unit (1,0): below the ink threshold
        a[W.SLICE, 0:100, 0:100] = 255                             # outside the window: ignored
        a[W.SLICE - 1, W.Y0:W.Y1, W.X0:W.X1] = 255                 # another slice: ignored

    def sup(a):
        a[W.SLICE, W.Y0:W.Y0 + s, W.X0:W.X0 + s] = 1                # exactly unit (0,0) supervised

    ink_p, sup_p = make_labels(str(tmp_path), ink, sup)
    assert W.main([ink_p, sup_p]) == 0
    out = capsys.readouterr().out
    n = (W.Y1 - W.Y0) * (W.X1 - W.X0)
    assert "supervised: %d px = %.6f %%" % (s * s, 100.0 * s * s / n) in out
    k = s * (s // 2)
    assert "labelled ink: %d px = %.6f %%" % (k, 100.0 * k / n) in out
    assert "ink outside the supervision mask: 0 px" in out
    assert "unit (0,0) phi %.6f (%d / %d px)" % (k / (s * s), k, s * s) in out
    assert "unit (1,0) phi 0.000000" in out and "unit (1,1) phi 0.000000" in out
