import numpy as np

from stripqc import geometry, seam, blindread, tifxyz


def cylinder(R=500.0, rows=10, cols=40, dz=20.0, dth=0.02):
    th = np.arange(cols) * dth
    z = np.arange(rows) * dz + 1000
    T, Zz = np.meshgrid(th, z)
    P = np.stack([R * np.cos(T), R * np.sin(T), Zz], -1)
    return P, np.ones(T.shape, bool)


UMB = (np.array([0.0, 5000.0]), np.array([0.0, 0.0]), np.array([0.0, 0.0]))


def test_displace_moves_exactly_d_outward():
    P, ok = cylinder()
    Q, okq, frac = geometry.displace(P, ok, UMB, d=8.0)
    dist = np.linalg.norm((Q - P)[okq], axis=-1)
    assert np.allclose(dist, 8.0) and frac > 0.99
    r0, r1 = np.hypot(P[..., 0], P[..., 1]), np.hypot(Q[..., 0], Q[..., 1])
    assert np.allclose((r1 - r0)[okq], 8.0, atol=1e-3)       # outward = away from the axis


def test_xpad_keeps_rows_and_extrapolates_a_plane_exactly():
    c, r = np.meshgrid(np.arange(30.0), np.arange(12.0))
    P = np.stack([c * 20, np.full_like(c, 100.0), r * 20], -1)
    ok = np.ones(c.shape, bool)
    Q, okq = geometry.xpad(P, ok, 3, 8, k=2)
    assert np.array_equal(Q[2:7], P[3:8])
    assert np.allclose(Q[0], P[1]) and np.allclose(Q[-1], P[9])


def test_xpad_steps_over_a_hole_next_to_a_boundary_row():
    c, r = np.meshgrid(np.arange(30.0), np.arange(12.0))
    P = np.stack([c * 20, np.full_like(c, 100.0), r * 20], -1)
    ok = np.ones(c.shape, bool)
    P[6, 5], ok[6, 5] = -1.0, False                          # hole next to the strip's last row (7) in column 5
    Q, okq = geometry.xpad(P, ok, 3, 8, k=2)
    assert np.allclose(Q[-2, 5], P[8, 5]) and np.allclose(Q[-1, 5], P[9, 5])   # the plane is still extrapolated exactly
    assert not okq[2 + 3, 5]                                  # the hole stays a hole


def test_normals_central_are_nan_on_border():
    P, ok = cylinder()
    N = tifxyz.normals_central(P, ok)
    assert np.isnan(N[0]).all() and np.isnan(N[:, 0]).all() and np.isfinite(N[1:-1, 1:-1]).all()


def test_seam_geometry_and_circular_null():
    P, ok = cylinder()
    A, B = seam.surface_points(P, ok), seam.surface_points(P, ok)
    assert seam.coincident_fraction(A, B)['frac'] == 1.0
    P2 = P.copy()
    P2[..., 0] *= 1.03                                        # 15 vox off: another sheet
    assert seam.coincident_fraction(A, seam.surface_points(P2, ok))['frac'] == 0.0
    rng = np.random.default_rng(0)
    Bm = rng.random((50, 400))
    rows, cols = rng.integers(0, 50, 3000), rng.integers(0, 400, 3000)
    a = Bm[rows, cols]
    r0, nul, p = seam.circular_null_r(a, Bm, rows, cols, range(20, 380, 10))
    assert abs(r0 - 1.0) < 1e-9 and p < 0.05 and np.abs(nul).max() < 0.2


def test_circular_null_gives_no_p_for_an_undefined_r():
    rng = np.random.default_rng(1)
    Bm = rng.random((50, 400))
    Bm[:, :10] = 0.5                                         # constant at the matched points: r is undefined
    rows, cols = rng.integers(0, 50, 500), rng.integers(0, 10, 500)
    r0, nul, p = seam.circular_null_r(rng.random(500), Bm, rows, cols, range(20, 380, 10))
    assert np.isnan(r0) and nul.size > 0 and p is None


def test_blindread_order_auc_roc():
    names = ['pos_a', 'pos_b', 'neg_a', 'neg_b', 'unk']
    key = blindread.coded_order(names)
    assert key == blindread.coded_order(list(reversed(names)))
    conf = {c: (0.9 if n.startswith('pos') else 0.1) for c, n in key.items()}
    assert blindread.reader_auc(conf, key, lambda n: n.startswith('pos'), lambda n: n.startswith('neg')) == 1.0
    pts = blindread.roc_points(np.array([0.9, 0.8]), np.array([0.1, 0.2]))
    assert pts[0] == (0.0, 0.0) and pts[-1] == (1.0, 1.0)
