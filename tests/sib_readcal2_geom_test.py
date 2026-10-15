# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic tests of tools/sib/readcal2/geom.py (CORR-RETRACE-RULE same-papyrus forms, reference mapping)."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'sib', 'readcal2'))
sys.path.insert(0, os.path.join(REPO, 'src'))
import geom as G  # noqa: E402
from hercules.geometry.tifxyz import TifxyzMesh  # noqa: E402


def sheet(H=40, W=40, step=20.0, z=100.0, du=0.0, dv=0.0, wobble=0.0):
    v, u = np.mgrid[0:H, 0:W].astype(np.float64)
    x = (u + du) * step
    y = (v + dv) * step
    zz = z + wobble * np.sin(x / 90.0) * np.cos(y / 70.0)
    return TifxyzMesh(points=np.stack([x, y, zz], -1).astype(np.float32), scale=(0.05, 0.05), uuid='s', meta={})


def test_point_triangle_matches_brute_force():
    rng = np.random.default_rng(0)
    a, b, c = rng.normal(size=(3, 500, 3))
    p = rng.normal(size=(500, 3)) * 2
    d = G.closest_point_triangle(p, a, b, c)
    s, t = np.meshgrid(np.linspace(0, 1, 301), np.linspace(0, 1, 301))
    m = (s + t) <= 1
    s, t = s[m], t[m]
    for i in range(0, 500, 50):
        q = a[i] + s[:, None] * (b[i] - a[i]) + t[:, None] * (c[i] - a[i])
        assert d[i] <= np.linalg.norm(q - p[i], axis=1).min() + 1e-9
        assert d[i] >= np.linalg.norm(q - p[i], axis=1).min() - 0.02


def test_retrace_half_cell_offset_is_same_by_surface_form():
    A = sheet(wobble=3.0)
    B = sheet(du=0.1, dv=0.1, wobble=3.0)  # exact re-trace, offset by half a dense cell (2 vox)
    S = G.Surface(B)
    _, _, xyz, mv = G.canvas_samples(A, stride=4, rect=(100, 100, 500, 500))
    pts = xyz[mv].reshape(-1, 3)
    dv, ds = G.distances(pts, S)
    r = G.same_papyrus(dv, ds)
    assert r['same_b'] and r['same']
    assert np.nanmedian(ds[np.isfinite(ds)]) < 0.5


def test_neighbour_sheet_is_not_same():
    A = sheet()
    for gap in (3.0, 5.0, 12.0):
        B = sheet(z=100.0 + gap)
        S = G.Surface(B)
        _, _, xyz, mv = G.canvas_samples(A, stride=4)
        dv, ds = G.distances(xyz[mv].reshape(-1, 3), S)
        assert not G.same_papyrus(dv, ds)['same']
        f = ds[np.isfinite(ds)]
        if f.size:
            assert f.min() >= gap - 1e-6


def test_surface_distance_exact_on_plane():
    B = sheet()
    S = G.Surface(B)
    rng = np.random.default_rng(1)
    pts = np.c_[rng.uniform(100, 600, 200), rng.uniform(100, 600, 200), 100 + rng.uniform(-5, 5, 200)]
    _, ds = G.distances(pts, S)
    assert np.allclose(ds, np.abs(pts[:, 2] - 100), atol=1e-6)


def test_area_matrix_rows_normalised_and_formula():
    M = G.area_matrix(100, 389)
    rs = np.asarray(M.sum(1)).ravel()
    # the declared offset maps c9 = N9 - 1 to c2 = N2 + 9 r - 10 > N2: the last ~7 canvas px have no source
    n_cov = int(np.floor((389 - 0.5 + 10) / (389 / 100) - 10 + 0.5))
    assert np.allclose(rs[:n_cov - 1], 1.0) and np.all(rs[n_cov + 1:] == 0)
    # a ramp c2 -> value c2 maps to c9 centre: mean over the covered interval = (c9 + 10) r - 10
    ramp = np.arange(389, dtype=np.float64)
    out = M @ ramp
    r = 389 / 100
    i = np.arange(5, n_cov - 3)
    # piecewise-constant source: the area mean equals the continuous centre up to a quantisation term < 0.05 px
    assert np.allclose(out[i], (i + 10) * r - 10, atol=0.05)


def test_map_ref_to_canvas_constant_and_separable():
    ref = np.full((389, 311), 77, np.uint8)
    out = G.map_ref_to_canvas(ref, (100, 80), block=64)
    assert out.shape == (100, 80) and np.allclose(out[3:-10, 3:-10], 77, atol=1e-4) and np.all(out[-3:] == 0)
    rng = np.random.default_rng(2)
    ref = rng.integers(0, 255, (389, 311)).astype(np.uint8)
    out = G.map_ref_to_canvas(ref, (100, 80), block=50)
    exp = (G.area_matrix(100, 389) @ ref.astype(np.float64)) @ G.area_matrix(80, 311).T
    assert np.allclose(out, exp, atol=1e-2)


def test_canvas_samples_follow_renderer_convention():
    A = sheet()
    yy, xx, xyz, mv = G.canvas_samples(A, stride=4)
    # pixel P samples grid (P + 0.5) * 0.05, x = u * 20 -> x = P + 0.5
    ok = mv & np.isfinite(xyz).all(-1) & (xx < 779) & (yy < 779)
    assert np.allclose(xyz[..., 0][ok], xx[ok] + 0.5) and np.allclose(xyz[..., 1][ok], yy[ok] + 0.5)
    assert G.canvas_shape(A) == (800, 800)
