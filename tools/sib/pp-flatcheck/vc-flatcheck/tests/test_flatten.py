import math

import numpy as np
import pytest

import flatcheck as fc
from synth import STEP, cylinder_grid, sphere_grid


@pytest.mark.parametrize("angle", [0.0, 30.0])
@pytest.mark.parametrize("method", ["slim", "arap"])
def test_cylinder_is_flattened_isometrically(method, angle):
    # developable surface, R = 300 vox, grid at 0 and 30 deg to the generators
    p = cylinder_grid(300.0, (60, 60), STEP, angle, s0=-600.0, z0=100.0)
    uv, info = fc.flatten(p, method, step=STEP)
    e = fc.metrics(p, uv)
    assert e["pct_quads_within_1pct"] >= 99.9, (method, angle, e["pct_quads_within_1pct"])
    assert e["flipped_triangles"] == 0
    assert e["area_scale_factor"] == pytest.approx(1.0, abs=2e-3)
    assert not fc.collapse_flags(e)["collapsed"]


@pytest.mark.parametrize("method", ["slim", "arap"])
def test_sphere_distortion_is_bounded_by_theory(method):
    n = 60
    L = (n - 1) * STEP
    prev = None
    for R in (6000.0, 3000.0, 1000.0):
        p = sphere_grid(R, n)
        uv, _ = fc.flatten(p, method, step=STEP)
        e = fc.metrics(p, uv)
        er = e["edge_ratio_pctl"]
        spread = max(er["99.5"] - 1.0, 1.0 - er["0.5"])
        s_grid = 1.0 - math.cos(L / 2 / R)  # strain of the latitude grid itself
        assert s_grid / 8 <= spread <= s_grid, (R, spread, s_grid)
        assert e["flipped_triangles"] == 0
        if prev is not None:
            assert e["pct_quads_within_1pct"] <= prev + 1e-9  # monotone in curvature
        prev = e["pct_quads_within_1pct"]
    assert prev < 50.0


def test_slim_beats_grid_on_curved_patch():
    p = sphere_grid(1000.0, 60)
    uv_s, _ = fc.flatten(p, "slim", step=STEP)
    es, eg = fc.metrics(p, uv_s), fc.metrics(p, fc.grid_uv(p, STEP))
    assert es["sym_dirichlet_area_weighted"] < eg["sym_dirichlet_area_weighted"]
    assert es["edge_abs_log_ratio_mean"] < eg["edge_abs_log_ratio_mean"]


def test_nominal_step_and_holes():
    p = cylinder_grid(2000.0, (30, 40), STEP, 0.0)
    assert fc.nominal_step(p) == pytest.approx(STEP, rel=1e-3)
    p[10:14, 10:14] = -1.0
    uv, _ = fc.flatten(p, "slim")
    e = fc.metrics(p, uv)
    assert e["pct_quads_within_1pct"] >= 99.9 and e["n_triangles_uv_undefined"] == 0


def test_bad_method():
    with pytest.raises(ValueError):
        fc.flatten(sphere_grid(1000.0, 5), "abf")
