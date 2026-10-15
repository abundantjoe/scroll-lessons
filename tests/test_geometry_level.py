# Provenance: Project HERCULES | owner the owner | [id removed]
"""level_mesh tests on a synthetic cylinder (radius 300 vox, axis along z,
(u, v) rotated 30 deg relative to iso-z)."""

import numpy as np
import pytest

from hercules.geometry import level_mesh as L
from hercules.geometry import tifxyz as T
from hercules.geometry.render_synth import cylinder_grid

R = 300.0
C = (400.0, 400.0)


@pytest.fixture(scope="module")
def cyl():
    p = cylinder_grid(R, C, (40, 40), 20.0, 30.0, s0=-400.0, z0=100.0)
    p[10:15, 20:26] = -1.0  # a hole
    return p


@pytest.fixture(scope="module")
def levelled(cyl):
    return L.level_mesh(cyl, step_vox=20.0)


def test_angle_estimate(cyl):
    # z = 20 (u sin30 + v cos30) -> gradient direction atan2(cos30, sin30) = 60 deg
    a_med, spread = L.estimate_level_angle(cyl, "median")
    a_lsq, _ = L.estimate_level_angle(cyl, "lsq")
    assert a_med == pytest.approx(60.0, abs=0.01)
    assert a_lsq == pytest.approx(60.0, abs=0.01)
    assert spread < 0.01


def test_angle_estimate_robust_to_outliers(cyl):
    rng = np.random.default_rng(1)
    q = cyl.copy()
    idx = rng.choice(np.flatnonzero(T.valid_mask(q)), 20, replace=False)
    q.reshape(-1, 3)[idx, 2] += rng.normal(0, 200, 20).astype(np.float32)
    a_med, _ = L.estimate_level_angle(q, "median")
    assert a_med == pytest.approx(60.0, abs=1.0)


def test_iso_z_horizontal(levelled):
    q = levelled.points
    ok = T.valid_mask(q)
    assert ok.sum() > 1000
    assert L.iso_z_tilt_deg(q) < 1.0
    # z increases down the rows and is constant along each row
    z = np.where(ok, q[..., 2], np.nan)
    assert np.nanmax(np.nanstd(z, axis=1)) < 0.05
    dz = np.diff(z, axis=0)
    assert np.nanmin(dz) > 0


def test_edge_lengths(levelled):
    assert T.edge_fraction_within(levelled.points, 20.0, 2.0) >= 0.95


def test_points_on_cylinder(levelled):
    q = levelled.points
    ok = T.valid_mask(q)
    r = np.hypot(q[..., 0] - C[0], q[..., 1] - C[1])[ok]
    assert np.max(np.abs(r - R)) < 0.5


def test_invalid_propagates(cyl, levelled):
    ok = T.valid_mask(levelled.points)
    # levelled nodes whose source position lies inside the hole's quads are invalid
    su, sv = levelled.src_u, levelled.src_v
    in_hole = (sv > 9) & (sv < 15) & (su > 19) & (su < 26)
    assert in_hole.any()
    assert not ok[in_hole].any()
    # every valid node maps back into a valid source quad
    s = T.sample_grid(cyl, sv[ok], su[ok])
    np.testing.assert_allclose(s, levelled.points[ok], atol=1e-3)


def test_round_trip_level_then_map_back(cyl, levelled):
    back = levelled.map_back(cyl.shape[:2])
    both = T.valid_mask(back) & T.valid_mask(cyl)
    assert both.sum() > 0.8 * T.valid_mask(cyl).sum()
    err = np.linalg.norm(back[both] - cyl[both], axis=-1)
    assert err.max() < 0.5


def test_angle_override_and_to_mesh(cyl):
    lv = L.level_mesh(cyl, step_vox=10.0, angle_deg=60.0)
    assert L.iso_z_tilt_deg(lv.points) < 1.0
    assert T.edge_fraction_within(lv.points, 10.0, 2.0) >= 0.95
    m = lv.to_mesh("lev")
    assert m.scale == (0.1, 0.1) and m.step_vox == pytest.approx((10.0, 10.0))


def test_level_preserves_handedness(cyl, levelled):
    cc = L.CentreCurve.straight(*C)
    assert L.chirality(cyl, cc) == L.chirality(levelled.points, cc) == 1
