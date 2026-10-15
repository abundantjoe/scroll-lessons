import numpy as np
import pytest

import flatcheck as fc
from flatcheck import geometry as G
from synth import STEP, cylinder_grid, plane_grid, sphere_grid


def test_identity_global_scale_and_stretch():
    p = plane_grid(20, 30)
    uv = fc.grid_uv(p, STEP)
    e = fc.metrics(p, uv)
    assert e["pct_quads_within_5pct"] == 100.0 and e["pct_quads_within_1pct"] == 100.0
    assert e["flipped_triangles"] == 0 and e["angle_abs_err_deg"]["max"] < 1e-6
    # a pure global scale fails raw, passes after the single area-matching factor
    e = fc.metrics(p, uv * 1.06)
    assert e["pct_quads_within_5pct_raw"] == 0.0 and e["pct_quads_within_5pct_norm"] == 100.0
    assert e["area_scale_factor"] == pytest.approx(1 / 1.06, rel=1e-9)
    # an anisotropic stretch is real distortion whatever the scale
    uv2 = uv.copy()
    uv2[..., 0] *= 1.12
    e = fc.metrics(p, uv2)
    assert e["pct_quads_within_5pct"] == 0.0


def test_undefined_uv_counts_as_failing_and_flip_detected():
    p = plane_grid(10, 10)
    uv = fc.grid_uv(p, STEP)
    uv[4, 4] = np.nan  # 4 of the 81 quads touch this vertex
    assert fc.metrics(p, uv)["pct_quads_within_5pct"] == pytest.approx(100.0 * 77 / 81)
    uv = fc.grid_uv(p, STEP)
    uv[4, 4] += np.array([30.0, 30.0])  # fold the vertex over its neighbours
    assert fc.metrics(p, uv)["flipped_triangles"] > 0


def test_invalid_vertices_are_excluded():
    p = plane_grid(12, 12)
    p[3:5, 3:5] = -1.0
    e = fc.metrics(p, fc.grid_uv(p, STEP))
    assert e["n_quads"] == 121 - 9  # a 2 x 2 vertex hole touches 3 x 3 quads and e["pct_quads_within_5pct"] == 100.0


def test_all_undefined_uv_reports_zero():
    p = plane_grid(6, 6)
    e = fc.metrics(p, np.full(p.shape[:2] + (2,), np.nan))
    assert e["pct_quads_within_5pct"] == 0.0


def test_gauss_bonnet_curvature():
    for R in (1000.0, 3000.0):
        k = fc.angle_defects(sphere_grid(R, 60))
        assert k["sum_angle_defect_rad"] == pytest.approx(k["area_vox2"] / R ** 2, rel=0.08)
    kc = fc.angle_defects(cylinder_grid(300.0, (60, 60), STEP, 30.0, s0=-600.0, z0=100.0))
    assert abs(kc["sum_angle_defect_rad"]) < 1e-3 * kc["area_vox2"] / 1000.0 ** 2


def test_grid_mesh_triangulation():
    p = plane_grid(3, 4)
    m = G.grid_to_mesh(p)
    assert m.F.shape == (2 * 2 * 3, 3) and m.V.shape == (12, 3)
