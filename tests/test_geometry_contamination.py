# Provenance: Project HERCULES | owner the owner | [id removed]
"""KD-tree identity / contamination tests on densified synthetic sheets."""

import numpy as np
import pytest

from hercules.geometry import contamination as CT
from hercules.geometry import tifxyz as T
from hercules.geometry.render_synth import cylinder_grid

R = 300.0
C = (400.0, 400.0)


def sheet(radius=R, shape=(10, 10), s0=0.0, z0=100.0, angle=0.0, step=20.0):
    return cylinder_grid(radius, C, shape, step, angle, s0=s0, z0=z0)


@pytest.fixture(scope="module")
def trace_b():
    return sheet()  # 180 x 180 vox patch


@pytest.fixture(scope="module")
def dense_b(trace_b):
    pts = T.densify(trace_b, 20)  # ~1 vox spacing
    return pts, T.vertex_normals(pts)


def test_perturbed_retrace_is_same(dense_b):
    b_pts, b_n = dense_b
    # re-trace: same sheet, different grid (rotated 10 deg, offset), shifted so
    # that ~60 % of it overlaps B, plus 0.3 vox isotropic noise
    a = sheet(shape=(11, 11), s0=55.0, z0=103.1, angle=10.0)
    a_cloud = CT.dense_cloud(a, 20.0, 1.0)
    rng = np.random.default_rng(7)
    a_cloud = a_cloud + rng.normal(0, 0.3, a_cloud.shape)
    ov = CT.overlap_fraction(a_cloud, b_pts, 2.0)
    assert ov == pytest.approx(0.60, abs=0.03)
    res = CT.same_papyrus(a_cloud, b_pts, b_n)
    assert res.n_within_2 >= 1000
    assert res.counts[0] >= 2 * res.counts[2]
    assert res.same
    assert res.normal_dist["median"] < 0.5


def test_parallel_sheet_8_vox_away_is_not_same(dense_b):
    b_pts, b_n = dense_b
    a_cloud = CT.dense_cloud(sheet(radius=R + 8.0), 20.0, 1.0)
    res = CT.same_papyrus(a_cloud, b_pts, b_n)
    assert not res.same
    assert res.counts == (0, 0, 0)
    assert CT.overlap_fraction(a_cloud, b_pts, 3.0) == 0.0


def test_near_parallel_sheet_rule_ratio():
    # a sheet 2.5 vox away: many points in [2, 3) and none < 1 -> NOT SAME
    b = CT.dense_cloud(sheet(), 20.0, 1.0)
    a = CT.dense_cloud(sheet(radius=R + 2.5), 20.0, 1.0)
    res = CT.same_papyrus(a, b)
    assert res.counts[0] == 0 and res.counts[2] > 1000 and not res.same


def test_clearance_fails_on_retraced_region(trace_b):
    region = CT.dense_cloud(trace_b, 20.0, 4.0)
    rng = np.random.default_rng(11)
    retrace = CT.dense_cloud(sheet(shape=(6, 6), s0=40.0, z0=140.0, angle=5.0), 20.0, 4.0)
    retrace = retrace + rng.normal(0, 0.3, retrace.shape)
    far = CT.dense_cloud(sheet(z0=100.0 + 180.0 + 300.0), 20.0, 4.0)  # 300 vox above
    cert = CT.clearance_certificate(region, {"train_far": far, "train_retrace": retrace})
    assert not cert.passed
    assert cert.offending_ids == ["train_retrace"]
    assert cert.min_distance < 2.0
    assert cert.threshold == 192.0
    assert cert.per_set_min["train_far"] == pytest.approx(300.0, abs=0.5)


def test_clearance_passes_300_vox_away(trace_b):
    region = CT.dense_cloud(trace_b, 20.0, 4.0)
    far_z = CT.dense_cloud(sheet(z0=100.0 + 180.0 + 300.0), 20.0, 4.0)
    far_r = CT.dense_cloud(sheet(radius=R + 300.0, s0=0.0), 20.0, 4.0)
    cert = CT.clearance_certificate(region, [far_z, far_r])
    assert cert.passed and cert.offending_ids == []
    assert cert.min_distance >= 192.0


def test_clearance_threshold_boundary():
    region = np.zeros((1, 3))
    ok = CT.clearance_certificate(region, [np.array([[192.0, 0, 0]])], min_vox=128, halo_vox=64)
    bad = CT.clearance_certificate(region, [np.array([[191.9, 0, 0]])], min_vox=128, halo_vox=64)
    assert ok.passed and not bad.passed and bad.offending_ids == [0]


def test_overlap_fraction_basic():
    a = np.array([[0.0, 0, 0], [10, 0, 0], [20, 0, 0], [30, 0, 0]])
    b = np.array([[0.5, 0, 0], [20.0, 1.0, 0]])
    assert CT.overlap_fraction(a, b, 1.0) == 0.5
    assert CT.overlap_fraction(a, b, 0.4) == 0.0
    assert CT.overlap_fraction(a, a, 0.0) == 1.0
