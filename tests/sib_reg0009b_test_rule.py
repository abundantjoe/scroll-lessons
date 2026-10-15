# Provenance: Project HERCULES | owner the owner | [id removed]
import os, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'sib', 'reg0009b'))
from rules import direction
from hercules.geometry.tifxyz import densify, vertex_normals, valid_mask


def sheet(z0, n=60, step=20.0, tilt=0.0, wobble=0.0, seed=0):
    rng = np.random.default_rng(seed)
    v, u = np.mgrid[0:n, 0:n].astype(float)
    x, y = u * step, v * step
    z = z0 + tilt * x + wobble * rng.normal(size=x.shape)
    p = np.stack([x, y, z], -1)
    dp = densify(p, 5).astype(np.float64); nrm = vertex_normals(dp)
    ok = valid_mask(dp) & np.isfinite(nrm).all(-1)
    return dp[ok], nrm[ok]


def run(a, b):
    return direction(a[0], b[0], b[1], cKDTree(b[0]), workers=1)


def test_retrace_same():
    assert run(sheet(100.3), sheet(100.0))['same']


def test_neighbour_sheet_not_same():
    r = run(sheet(115.0), sheet(100.0))
    assert not r['same'] and r['within2'] == 0


def test_offset_2p5_vox_not_same():
    # a trace offset by 2.5 vox along the normal: all points in [2,3) -> NOT same under the ratio rule
    r = run(sheet(102.5), sheet(100.0))
    assert not r['same'] and r['counts_dn'][2] > r['counts_dn'][0]


def test_crossing_small_contact():
    # a tilted sheet crossing a flat one: contact band only
    r = run(sheet(100.0, tilt=0.05), sheet(100.0))
    assert r['counts_dn'][0] > 0 and r['frac_src_within2'] < 0.2


from rules import TriSurface, failclosed, _closest_on_tri


def grid(z0, n=40, step=20.0, du=0.0, tilt=0.0):
    v, u = np.mgrid[0:n, 0:n].astype(float)
    x, y = u * step + du, v * step + du
    return np.stack([x, y, z0 + tilt * x], -1)


def dense_pts(p):
    dp = densify(p, 5).astype(np.float64); dv = valid_mask(dp)
    return dp, dv


def test_closest_on_tri_bruteforce():
    rng = np.random.default_rng(1)
    a, b, c = (rng.normal(size=(500, 3)) for _ in range(3)); p = rng.normal(size=(500, 3)) * 2
    cp = _closest_on_tri(p, a, b, c)
    s, t = np.meshgrid(np.linspace(0, 1, 201), np.linspace(0, 1, 201)); m = (s + t) <= 1
    s, t = s[m], t[m]
    for i in range(0, 500, 50):
        q = a[i] + s[:, None] * (b[i] - a[i]) + t[:, None] * (c[i] - a[i])
        assert np.linalg.norm(p[i] - cp[i]) <= np.linalg.norm(q - p[i], axis=1).min() + 1e-6


def test_half_cell_retrace_same_under_b():
    # exact re-trace shifted by half a dense cell (2 vox in-plane): form (a) fails, form (b) SAME
    A = dense_pts(grid(100.0, du=2.0)); B = dense_pts(grid(100.0))
    r = failclosed(A[0][A[1]], TriSurface(*B), workers=1)
    assert r['same_b'] and r['same'] and r['counts_b_surface'][0] > 0.9 * sum(r['counts_b_surface'])


def test_neighbour_sheet_failclosed_not_same():
    for dz in (3.0, 5.0, 12.0):
        A = dense_pts(grid(100.0 + dz, du=2.0)); B = dense_pts(grid(100.0))
        assert not failclosed(A[0][A[1]], TriSurface(*B), workers=1)['same'], dz
