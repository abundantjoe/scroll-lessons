# Provenance: Project HERCULES | owner the owner | [id removed]
"""TEST HELPER ONLY: synthetic 9 um / rescan pairs with a known C6 transform.

A high-res "world" texture (band-limited noise at two scales plus curved,
periodic sheet-like surfaces) is laid out in the canonical rescan frame.  The
9 um volume is its exact area mean (summed-area table, trilinear on the
cumulative sum = exact box integral of the piecewise-constant world) at
q(p) = F (p + M (p - Pm) + b - z0 e_z), then blurred by a small PSF, gain /
offset changed and noised.  The rescan is the world cropped to q >= 0,
noised, and stored flipped by ``flip_signs`` (x, y, z).  This is an
independent implementation from ``c6.downsample_area`` on purpose.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy import fft as sfft
from scipy import ndimage as ndi


def rotation_xyz(deg_x=0.0, deg_y=0.0, deg_z=0.0):
    ax, ay, az = np.deg2rad([deg_x, deg_y, deg_z])
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


def world_texture(lo_xyz, shape_zyx, F, sheet_spacing=8.0, sheet_width=0.9, rng=None,
                  noise_sigmas=(0.8, 2.0), noise_amp=0.8):
    """Texture on the canonical hi-res grid q = lo + index (zyx array)."""
    rng = np.random.default_rng(rng)
    nz, ny, nx = shape_zyx
    white = rng.standard_normal((nz, ny, nx), dtype=np.float32)
    W = sfft.rfftn(white, workers=2)
    del white
    fr = [sfft.fftfreq(nz), sfft.fftfreq(ny), sfft.rfftfreq(nx)]
    H = None
    for s in noise_sigmas:  # Gaussian filters, sigma s 9um voxels, equalised variance (separable)
        sh = s * F
        g = [np.exp(-2 * np.pi ** 2 * sh ** 2 * f ** 2).astype(np.float32) for f in fr]
        term = (sh ** 1.5) * g[0][:, None, None] * g[1][None, :, None] * g[2][None, None, :]
        H = term if H is None else H + term
    W *= H
    del H
    noise = sfft.irfftn(W, s=(nz, ny, nx), workers=2).astype(np.float32)
    del W
    noise /= noise.std()
    qz = (lo_xyz[2] + np.arange(nz, dtype=np.float32))[:, None, None]
    qy = (lo_xyz[1] + np.arange(ny, dtype=np.float32))[None, :, None]
    qx = (lo_xyz[0] + np.arange(nx, dtype=np.float32))[None, None, :]
    S = sheet_spacing * F
    ph = rng.uniform(0, 2 * np.pi, 2)
    phi = (qy + 1.2 * S * np.sin(2 * np.pi * qx / (7.0 * S) + ph[0])
           + 0.6 * S * np.sin(2 * np.pi * qz / (5.0 * S) + ph[1])) / S
    d = phi - np.round(phi)
    sheets = np.exp(-0.5 * (d * sheet_spacing / sheet_width) ** 2).astype(np.float32)
    del phi, d
    sheets -= sheets.mean()
    sheets /= sheets.std()
    return sheets + noise_amp * noise


def box_mean_at(vol, centres_zyx, F):
    """Exact mean of piecewise-constant ``vol`` over axis-aligned cubes of side F
    centred at ``centres_zyx`` (..., 3) in voxel-centre coordinates."""
    S = np.zeros(tuple(n + 1 for n in vol.shape), np.float64)
    S[1:, 1:, 1:] = vol
    for ax in range(3):
        np.cumsum(S, axis=ax, out=S)
    c = np.asarray(centres_zyx, float).reshape(-1, 3)
    lo = c - F / 2.0 + 0.5
    hi = c + F / 2.0 + 0.5
    total = np.zeros(len(c))
    for bits in itertools.product((0, 1), repeat=3):
        coords = np.stack([hi[:, a] if bits[a] else lo[:, a] for a in range(3)])
        sign = (-1) ** (3 - sum(bits))
        total += sign * ndi.map_coordinates(S, coords, order=1, prefilter=False, mode="nearest")
    return (total / F ** 3).reshape(np.asarray(centres_zyx).shape[:-1])


def make_pair(shape9=(40, 104, 104), F=3.8976, z0=4.0, b=(7.3, -4.6, 2.2),
              tilt_deg=(0.26, 0.12, 0.0), Pm=None, flip_signs=(1, -1, 1),
              sheet_spacing=8.0, psf9_sigma=0.5, noise9=0.15, noiser=0.3,
              gain9=0.8, offset9=0.3, seed=0):
    """Returns dict(vol9, volr (raw, flipped), rescan_can, truth, sheet_spacing).

    shape9 is (z, y, x); b, Pm, flip_signs are (x, y, z); M = R(tilt) - I so
    that p + t(p) = R (p - Pm) + Pm + b.  Pm defaults to the volume centre.
    """
    rng = np.random.default_rng(seed)
    shape9 = np.asarray(shape9, int)
    M = rotation_xyz(*tilt_deg) - np.eye(3)
    b = np.asarray(b, float)
    Pm = (shape9[::-1] - 1) / 2.0 if Pm is None else np.asarray(Pm, float)
    ez = np.array([0.0, 0.0, 1.0])

    def q_of(p):
        return F * (p + (p - Pm) @ M.T + b - z0 * ez)

    corners = np.array(list(itertools.product(*[(-0.5, n - 0.5) for n in shape9[::-1]])))
    qc = q_of(corners)
    lo_w = np.minimum(np.floor(qc.min(0) - F / 2) - 3, 0).astype(int)  # xyz
    hi_w = (np.ceil(qc.max(0) + F / 2) + 3).astype(int)
    wshape = tuple((hi_w - lo_w)[::-1])
    world = world_texture(lo_w, wshape, F, sheet_spacing=sheet_spacing, rng=rng)

    grid = np.stack(np.meshgrid(*[np.arange(n, dtype=float) for n in shape9], indexing="ij"), -1)
    p_xyz = grid[..., ::-1].reshape(-1, 3)
    cw = (q_of(p_xyz) - lo_w)[:, ::-1]
    vol9 = box_mean_at(world, cw, F).reshape(tuple(shape9)).astype(np.float32)
    if psf9_sigma:
        vol9 = ndi.gaussian_filter(vol9, psf9_sigma)
    s9 = vol9.std()
    vol9 = gain9 * vol9 + offset9 + noise9 * s9 * rng.standard_normal(vol9.shape).astype(np.float32)

    o = (-lo_w)[::-1]
    can = world[o[0]:, o[1]:, o[2]:].copy()
    del world
    can += noiser * can.std() * rng.standard_normal(can.shape).astype(np.float32)
    raw = can
    for k, s in enumerate(flip_signs):  # k indexes x, y, z
        if s < 0:
            raw = np.flip(raw, 2 - k)
    raw = np.ascontiguousarray(raw)
    flip_zyx = tuple(bool(flip_signs[2 - i] < 0) for i in range(3))
    truth = {"F": F, "z0": z0, "M": M, "b": b, "Pm": Pm,
             "flip_signs_xyz": list(flip_signs), "flip_zyx": flip_zyx,
             "rescan_shape_zyx": raw.shape}
    return {"vol9": vol9.astype(np.float32), "volr": raw, "rescan_can": can,
            "truth": truth, "sheet_spacing": sheet_spacing}


def truth_fit(truth):
    """Fit-like dict of the true transform (for map_* and evaluate_patches)."""
    return {"F": truth["F"], "z0": truth["z0"], "M": np.asarray(truth["M"]).tolist(),
            "b": list(truth["b"]), "Pm": list(truth["Pm"]),
            "orientation": {"perm_zyx": [0, 1, 2], "flip_zyx": list(truth["flip_zyx"]),
                            "rescan_shape_zyx": list(truth["rescan_shape_zyx"])}}
