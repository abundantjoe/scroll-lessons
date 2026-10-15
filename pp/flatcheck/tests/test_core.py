import math

import numpy as np
import pytest

from flatcheck import core as FL
from flatcheck.level import level_mesh, estimate_level_angle
from conftest import STEP, abf, cylinder_grid, plane_grid, sphere_grid


def flatten(p, method, init="grid"):
    m = FL.grid_to_mesh(p)
    UV0 = FL.grid_init_uv(m, STEP) if init == "grid" else FL.tutte_init_uv(m)
    if method == "slim":
        UV, _ = FL.flatten_slim(m.V, m.F, UV0)
    elif method == "arap":
        UV, _ = FL.flatten_arap(m.V, m.F, UV0)
    else:
        UV = UV0
    return FL.uv_to_grid(m, UV, p.shape[:2]), m


def test_metric_identity_scale_and_stretch():
    p = plane_grid(20, 30)
    m = FL.grid_to_mesh(p)
    uv = FL.uv_to_grid(m, FL.grid_init_uv(m, STEP), p.shape[:2])
    e = FL.evaluate(p, uv, m.quads)
    assert e["pct_quads_within_5pct"] == 100.0 and e["flipped_triangles"] == 0
    e = FL.evaluate(p, uv * 1.06, m.quads)
    assert e["pct_quads_within_5pct_raw"] == 0.0 and e["pct_quads_within_5pct_norm"] == 100.0
    uv2 = uv.copy()
    uv2[..., 0] *= 1.12
    assert FL.evaluate(p, uv2, m.quads)["pct_quads_within_5pct"] == 0.0


def test_undefined_uv_fails_and_flip_detected():
    p = plane_grid(10, 10)
    m = FL.grid_to_mesh(p)
    uv = FL.uv_to_grid(m, FL.grid_init_uv(m, STEP), p.shape[:2])
    uv[4, 4] = np.nan
    assert FL.evaluate(p, uv, m.quads)["pct_quads_within_5pct"] == pytest.approx(100.0 * 77 / 81)
    uv = FL.uv_to_grid(m, FL.grid_init_uv(m, STEP), p.shape[:2])
    uv[4, 4] += 30.0
    assert FL.evaluate(p, uv, m.quads)["flipped_triangles"] > 0
    e = FL.evaluate(p, np.full(p.shape[:2] + (2,), np.nan), m.quads)
    assert e["pct_quads_within_5pct"] == 0.0 and e["n_triangles_good"] == 0


@pytest.mark.parametrize("angle", [0.0, 30.0])
@pytest.mark.parametrize("method", ["slim", "arap"])
@pytest.mark.parametrize("init", ["grid", "tutte"])
def test_cylinder_developable(method, angle, init):
    p = cylinder_grid(300.0, (400.0, 400.0), (60, 60), STEP, angle, s0=-600.0, z0=100.0)
    uv, m = flatten(p, method, init)
    e = FL.evaluate(p, uv, m.quads)
    assert e["pct_quads_within_1pct"] >= 99.9 and e["flipped_triangles"] == 0


@pytest.mark.parametrize("method", ["slim", "arap"])
def test_sphere_expected_distortion(method):
    n, prev = 60, None
    L = (n - 1) * STEP
    for R in (6000.0, 3000.0, 1000.0):
        p = sphere_grid(R, n)
        uv, m = flatten(p, method)
        e = FL.evaluate(p, uv, m.quads)
        er = e["edge_ratio_pctl"]
        spread = max(er["99.5"] - 1.0, 1.0 - er["0.5"])
        s_grid = 1.0 - math.cos(L / 2 / R)
        assert s_grid / 8 <= spread <= s_grid
        if prev is not None:
            assert e["pct_quads_within_1pct"] <= prev + 1e-9
        prev = e["pct_quads_within_1pct"]
    assert prev < 50.0


def test_rectangle_rule():
    p = cylinder_grid(2000.0, (0.0, 0.0), (220, 300), STEP, 0.0, z0=100.0)
    p[40:60, 100:180] = -1.0
    r1 = FL.choose_rectangle(p, 9.362, STEP, np.random.default_rng([1, 2]))
    assert r1 == FL.choose_rectangle(p, 9.362, STEP, np.random.default_rng([1, 2]))
    assert abs(r1["area_cm2"] - 4.0) <= 0.04 and 1.0 <= r1["aspect"] <= 2.0


def test_level_mesh_rotated_cylinder():
    p = cylinder_grid(300.0, (400.0, 400.0), (40, 40), STEP, 30.0, s0=-400.0, z0=100.0)
    a, spread = estimate_level_angle(p)
    assert a == pytest.approx(60.0, abs=0.01) and spread < 0.01
    L = level_mesh(p, step_vox=STEP)
    z = L.points[..., 2]
    ok = np.all(L.points != -1, axis=-1)
    rows_ok = [np.ptp(z[i][ok[i]]) for i in range(z.shape[0]) if ok[i].sum() > 2]
    assert max(rows_ok) < 0.05
