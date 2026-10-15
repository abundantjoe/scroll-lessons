# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic checks of tools/sib/reg0841/reg_core.py: shift sign, sub-voxel recovery and affine fit."""
import os, sys
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "sib", "reg0841"))
import reg_core as rc


def _synthetic(d_true):
    rng = np.random.default_rng(1)
    F = rc.F
    th = np.radians(0.3)
    A = F * np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1.0]])
    c = np.array([-3.0, 5.0, -7.0])
    shape9 = (24, 48, 48); o9 = (100, 200, 300)
    # rescan region covering the block grown by 6 vox
    P = rc.block_points(o9, shape9)
    lo = (P.min(0) - 6) @ A.T + c; hi = (P.max(0) + 6) @ A.T + c
    o2 = [int(np.floor(min(lo[2], hi[2]))) - 8, int(np.floor(min(lo[1], hi[1]))) - 8, int(np.floor(min(lo[0], hi[0]))) - 8]
    sh2 = [int(np.ceil(max(lo[k], hi[k]))) + 8 - o2[2 - k] for k in (2, 1, 0)]
    v2 = gaussian_filter(rng.normal(size=sh2).astype(np.float32), 4.0) * 100 + 100
    q = (P + d_true) @ A.T + c
    B = map_coordinates(v2, np.stack([q[:, 2] - o2[0], q[:, 1] - o2[1], q[:, 0] - o2[2]]), order=3).reshape(shape9)
    return B, v2, o2, A, c, P


def test_shift_recovery():
    d_true = np.array([1.37, -0.62, 0.81])
    B, v2, o2, A, c, P = _synthetic(d_true)
    f2 = rc.prefilter(v2)
    d, info = rc.refine(B, f2, o2, A, c, P)
    assert np.linalg.norm(d - d_true) < 0.1, (d, d_true)
    assert info["ncc_after_shift"] > 0.95


def test_affine_fit_exact():
    rng = np.random.default_rng(2)
    A = rc.F * np.eye(3) + rng.normal(scale=0.01, size=(3, 3)); c = rng.normal(scale=100, size=3)
    P = rng.uniform(0, 5000, size=(24, 3)); Q = P @ A.T + c
    A2, c2 = rc.fit_affine(P, Q)
    assert np.allclose(A2, A, atol=1e-8) and np.allclose(c2, c, atol=1e-5)


def test_pitch():
    Z, Y, X = 48, 128, 128
    z, y, x = np.meshgrid(np.arange(Z), np.arange(Y), np.arange(X), indexing="ij")
    n = np.array([0.6, 0.8, 0.0])  # x, y, z
    B = (np.cos(2 * np.pi * (x * n[0] + y * n[1]) / 12.0) * 50 + 100).astype(np.float32)
    nn, pitch, aniso, flag, ac = rc.sheet_normal_pitch(B)
    assert abs(abs(nn @ n) - 1) < 1e-3 and abs(pitch - 12.0) <= 0.5, (nn, pitch)
