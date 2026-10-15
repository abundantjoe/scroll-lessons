# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for the census geometry helpers (synthetic data only, no network)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "sib", "census"))

from centre import gauss_smooth, robust_smooth  # noqa: E402
from m7_centre import weighted_line_centre  # noqa: E402
from plan_seeds import Mask, surface_distance  # noqa: E402
from sync_plan import seed_ranges  # noqa: E402


def _disc_mask(tmp_path, r_px=100, n=200, nz=4):
    yy, xx = np.mgrid[0:n, 0:n]
    m = (xx - n / 2) ** 2 + (yy - n / 2) ** 2 <= r_px ** 2
    packed = np.stack([np.packbits(m, axis=None)] * nz)
    fn = tmp_path / "m.npz"
    np.savez(fn, packed=packed, shape=np.array([nz, n, n]), level=4)
    return Mask(str(fn))


def test_ray_radius_disc(tmp_path):
    mk = _disc_mask(tmp_path)
    c = 100 * 16 + 7.5  # level-0 centre of the disc
    for th in np.linspace(0, 2 * math.pi, 9):
        R, inside = mk.ray_radius(c, c, 7.5, th)
        assert inside
        assert abs(R - 1600) < 40  # 100 px x 16, within 2.5 level-4 px


def test_inside_eroded(tmp_path):
    mk = _disc_mask(tmp_path)
    c = 100 * 16 + 7.5
    assert mk.inside(c + 1500, c, 7.5, eroded=False)
    assert not mk.inside(c + 1580, c, 7.5, eroded=True)  # within 48 vox of the rim
    assert mk.inside(c + 1400, c, 7.5, eroded=True)


def test_weighted_line_centre_exact():
    rng = np.random.default_rng(0)
    c0 = np.array([300.0, -120.0])
    th = rng.uniform(0, 2 * np.pi, 400)
    r = rng.uniform(50, 900, 400)
    p = c0 + np.c_[r * np.cos(th), r * np.sin(th)]
    d = np.c_[np.cos(th), np.sin(th)]  # normals point radially
    c, cond = weighted_line_centre(p, d, np.ones(400))
    assert np.allclose(c, c0, atol=1e-6)
    assert cond < 3


def test_smoothers_preserve_constant_and_reject_spike():
    z = np.arange(0, 3200, 16.0)
    v = np.full(z.size, 5.0)
    assert np.allclose(gauss_smooth(z, v), 5.0)
    v2 = v.copy()
    v2[100] = 5000.0
    assert abs(robust_smooth(z, v2)[100] - 5.0) < 1e-6


def test_surface_distance_arc_and_z():
    curve = (np.array([0.0, 1e5]), np.array([0.0, 0.0]), np.array([0.0, 0.0]))
    a = (1000.0, 0.0, 0.0)
    b = (0.0, 1000.0, 0.0)
    assert abs(surface_distance(curve, a, b) - 1000 * math.pi / 2) < 1e-6
    c = (1000.0, 0.0, 800.0)
    assert abs(surface_distance(curve, a, c) - 800.0) < 1e-6


def test_seed_ranges_clip_and_shrink():
    r = seed_ranges((100, 5000, 50), (5000, 5000), 1500, (20000, 8000, 8000), typical=False)
    assert r["xy"] == (0, 1551) and r["yz"] == (0, 1601) and r["xz"] == (3499, 6501)
    t = seed_ranges((100, 5000, 5000), (5000, 5000), 1500, (20000, 8000, 8000), typical=True)
    # radial direction is x -> x (yz files) shrunk to +-(0.402 R + 1)
    assert t["yz"] == (0, 704) and t["xz"] == (3499, 6501)
