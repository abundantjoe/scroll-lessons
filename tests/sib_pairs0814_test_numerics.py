# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for the pairs0814 sibling tools (synthetic data only)."""
import importlib.util
import os

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "tools", "sib", "pairs0814")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sa = _load("stage_a")
sb = _load("stage_b")


def test_area_avg_block_exact_block_means():
    rng = np.random.default_rng(1)
    G = rng.integers(0, 256, (400, 400)).astype(np.float64)
    # 9 um pixel P covers 2.4 um pixels [4P, 4P+3]: c9 = (c2 - 1.5) / 4
    A = np.array([[0.25, 0.0, -0.375], [0.0, 0.25, -0.375]])
    v = sb.area_avg_block(G, 0, 0, A, 10, 20, 30, 40)
    ref = G.reshape(100, 4, 100, 4).mean(axis=(1, 3))[20:60, 10:40]
    assert np.max(np.abs(v - ref)) < 1e-9


def test_area_avg_block_fractional_footprint_bruteforce():
    # exact footprint average of the piecewise-constant image vs dense supersampling of the footprint
    rng = np.random.default_rng(7)
    G = rng.integers(0, 256, (200, 200)).astype(np.float64)
    A = np.array([[0.2570789, 0.0, -7.8007], [0.0, 0.2569270, -7.8023]])
    v = sb.area_avg_block(G, 0, 0, A, 3, 4, 20, 20)
    Mi = np.linalg.inv(A[:, :2]); ti = -Mi @ A[:, 2]
    hx, hy = 0.5 * abs(Mi[0, 0]), 0.5 * abs(Mi[1, 1])
    n = 400
    for (yy, xx) in ((4, 3), (10, 11), (23, 22), (15, 7)):
        cx = Mi[0, 0] * xx + ti[0]; cy = Mi[1, 1] * yy + ti[1]
        us = cx - hx + (np.arange(n) + 0.5) * (2 * hx / n)
        vs = cy - hy + (np.arange(n) + 0.5) * (2 * hy / n)
        bf = G[np.floor(vs + 0.5).astype(int)][:, np.floor(us + 0.5).astype(int)].mean()
        assert abs(v[yy - 4, xx - 3] - bf) < 0.5  # supersampling error only (1/400 px steps)


def test_stage_a_area_average_matches_stage_b():
    rng = np.random.default_rng(2)
    img = rng.integers(0, 256, (260, 300)).astype(np.uint8)
    A = np.array([[0.2570789, 0.0, -7.8007], [0.0, 0.2569270, -7.8023]])
    ref, cov = sa.area_average(img, lambda a, b: np.ones((b - a, img.shape[1]), np.uint8), A, (60, 70), band=16)
    v = sb.area_avg_block(img.astype(np.float64), 0, 0, A, 0, 0, 70, 60)
    inner = (slice(2, 58), slice(2, 68))
    assert np.max(np.abs(ref[inner] - v[inner])) < 1e-3
    assert np.allclose(cov[inner], 1.0)


def _smooth_field(n, seed):
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.standard_normal((n, n)))
    ky, kx = np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n), indexing="ij")
    return f * np.exp(-(kx ** 2 + ky ** 2) / (2 * 0.08 ** 2)), ky, kx


@pytest.mark.parametrize("sy,sx", [(0.0, 0.0), (0.4, -0.3), (0.9, 0.2), (-1.6, 0.7)])
def test_window_shift_recovers_subpixel_shift(sy, sx):
    f, ky, kx = _smooth_field(256, 3)
    ref = np.real(np.fft.ifft2(f))
    ours = np.real(np.fft.ifft2(f * np.exp(2j * np.pi * (ky * sy + kx * sx))))  # ours(y) = ref(y + s)
    w = sb.window_shift(ours, ref, 64, 64, 128)
    assert abs(w["dy"] - sy) < 0.15 and abs(w["dx"] - sx) < 0.15
    assert w["aligned"] == (np.hypot(sy, sx) <= 1.0)


def test_window_shift_invalid_window_not_aligned():
    f, _, _ = _smooth_field(256, 4)
    ref = np.real(np.fft.ifft2(f))
    ours = ref.copy()
    ours[64:192, 64:170] = np.nan  # > 50 % of the window invalid
    assert sb.window_shift(ours, ref, 64, 64, 128)["aligned"] is False


def test_fit_affine_with_outliers():
    rng = np.random.default_rng(5)
    src = rng.uniform(0, 20000, (5000, 2))
    A = np.array([[0.2571, 1e-4, -7.8], [-2e-4, 0.2569, -7.8]])
    dst = src @ A[:, :2].T + A[:, 2]
    dst[:100] += rng.uniform(100, 3000, (100, 2))
    Af, res, keep = sa.fit_affine(src, dst)
    assert np.max(np.abs(Af - A)) < 1e-9
    assert keep[100:].all() and not keep[:100].any()


def test_tiled_rows_reader(tmp_path):
    import tifffile
    rng = np.random.default_rng(6)
    a = rng.integers(0, 256, (300, 530)).astype(np.uint8)
    p = str(tmp_path / "t.tif")
    tifffile.imwrite(p, a, tile=(64, 128), compression="zlib")
    t = sa.TiledRows(p)
    for lo, hi in ((0, 1), (0, 300), (63, 65), (250, 300), (100, 229)):
        assert np.array_equal(t[slice(lo, hi)], a[lo:hi])


def test_ncc_basic():
    x = np.arange(200.0).reshape(10, 20)
    assert abs(sb.ncc(x, 3 * x + 1)[0] - 1) < 1e-12
    assert abs(sb.ncc(x, -x)[0] + 1) < 1e-12
    y = x.copy(); y[0, :] = np.nan
    assert sb.ncc(x, y)[1] == 180


sc = _load("stage_c")


def test_closest_on_triangles_regions():
    a = np.array([[0.0, 0, 0]]); b = np.array([[1.0, 0, 0]]); c = np.array([[0.0, 1, 0]])
    cases = {(0.2, 0.2, 3.0): 3.0, (-1.0, -1.0, 0.0): np.sqrt(2), (2.0, 0.0, 0.0): 1.0,
             (0.5, -1.0, 0.0): 1.0, (1.0, 1.0, 0.0): np.sqrt(0.5), (-2.0, 0.5, 1.0): np.sqrt(5)}
    for pnt, d in cases.items():
        got = sc.closest_on_triangles(np.array([pnt]), a, b, c)[0]
        assert abs(got - d) < 1e-9, (pnt, got, d)


def test_surface_distance_exact_retrace_half_cell_offset():
    # CORR-RETRACE-RULE failure case: an exact re-trace offset by half a dense cell must be ~0 vox from the surface
    from scipy.spatial import cKDTree
    from hercules.geometry.tifxyz import densify, valid_mask
    gy, gx = np.mgrid[0:12, 0:12].astype(np.float64) * 20.0
    grid = np.stack([gx, gy, 100 + 0.02 * gx + 0.01 * gy], -1).astype(np.float32)
    dense = densify(grid, 5)
    rr, cc = np.nonzero(valid_mask(dense))
    tree = cKDTree(dense[rr, cc].astype(np.float64))
    qy, qx = np.mgrid[30:190:4, 30:190:4].astype(np.float64)  # 30 = 2 mod 4  # half a 4 vox cell off the dense vertices
    q = np.stack([qx.ravel(), qy.ravel(), 100 + 0.02 * qx.ravel() + 0.01 * qy.ravel()], -1)
    dv, _ = tree.query(q, k=1)
    ds = sc.surface_distance(q, dense, tree, rr, cc, np.ones(len(q), bool))
    assert np.median(dv) > 2.5  # the literal vertex form misses it (counts land in [2, 3))
    assert np.max(ds) < 1e-3
    q2 = q + np.array([0, 0, 5.0])  # a neighbouring sheet 5 vox away is not within 2 vox
    ds2 = sc.surface_distance(q2, dense, tree, rr, cc, np.ones(len(q2), bool))
    assert np.min(ds2) > 4.9
