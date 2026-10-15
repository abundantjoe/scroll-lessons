# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for tools/sib/tracer/p4n/metrics.py primitives (pure numpy, no data)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/sib/tracer/p4n"))
import metrics as M  # noqa: E402


def test_point_tri_dist_matches_dense_sampling():
    rng = np.random.default_rng(0)
    for _ in range(200):
        tri = rng.normal(size=(1, 3, 3)) * 5
        p = rng.normal(size=(1, 3)) * 8
        u, v = np.meshgrid(np.linspace(0, 1, 401), np.linspace(0, 1, 401))
        m = (u + v) <= 1
        s = tri[0, 0] + u[m, None] * (tri[0, 1] - tri[0, 0]) + v[m, None] * (tri[0, 2] - tri[0, 0])
        brute = np.linalg.norm(s - p, axis=1).min()
        got = M.point_tri_dist(p, tri)[0]
        assert got <= brute + 1e-9 and brute - got < 0.05


def _sheet(z0, n=40, step=2.0):
    y, x = np.mgrid[0:n, 0:n] * step
    return np.stack([x, y, np.full_like(x, z0, dtype=float)], -1).astype(float)


def test_clearance_two_parallel_sheets():
    a, b = _sheet(0.0), _sheet(10.0)
    ids_a = np.stack(np.mgrid[0:40, 0:40], -1).astype(float)
    ids_b = ids_a + np.array([0.0, 1000.0])          # other winding: far in grid units
    ta, ra = M.tri_mesh(a, ids_a)
    tb, rb = M.tri_mesh(b, ids_b)
    pts = np.concatenate([a.reshape(-1, 3), b.reshape(-1, 3)])
    prc = np.concatenate([ids_a.reshape(-1, 2), ids_b.reshape(-1, 2)])
    tris = np.concatenate([ta, tb]); trc = np.concatenate([ra, rb])
    q = a[10:30, 10:30].reshape(-1, 3)
    cl = M.clearance(q, ids_a[10:30, 10:30].reshape(-1, 2), pts, prc, tris, trc)
    assert np.allclose(cl, 10.0, atol=1e-6)       # own sheet excluded, other sheet exactly 10 away


def test_seam_zero_on_straight_continuation():
    g = _sheet(0.0, n=12)
    new = np.zeros(g.shape[:2], bool); new[:3] = True
    s = M.seam(g, new, 3, 0, (9, 12))
    assert s["n_seam_columns"] > 0 and s["normal_residual_vox"]["median"] < 1e-9


def test_seam_detects_planted_normal_step():
    g = _sheet(0.0, n=12)
    g[:3, :, 2] += 5.0                                 # extension rows displaced 5 vox along the normal
    new = np.zeros(g.shape[:2], bool); new[:3] = True
    s = M.seam(g, new, 3, 0, (9, 12))
    assert abs(s["normal_residual_vox"]["median"] - 5.0) < 1e-6
    assert s["pass_median_normal_le_2vox"] is False
