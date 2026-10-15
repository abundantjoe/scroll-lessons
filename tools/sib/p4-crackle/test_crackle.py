"""Unit tests for the P4-H crackle channel (RULES.md DECL-P4-9; sibling task p4-crackle item 3).

Provenance: Project HERCULES | owner the owner | [id removed]

Synthetic data only. Pixel = 2.258 um (surface-volume level 0). A stack has 17 slices (the channel's
+-18 um slab): the crack network is shared by all slices, the CT noise is independent per slice.

Run: python -m pytest -q tools/sib/p4-crackle/test_crackle.py
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crackle as C  # noqa: E402

PX_UM = 2.258
N = 160          # patch side (361 um)
NOISE = 6.0      # per-voxel CT noise (uint8 units)
BASE = 80.0


def crack_network(spacing_um, rng, width_px=1.2):
    """Voronoi crack network: seeds on a jittered grid of the given spacing; a crack where the
    distance to the nearest two seeds differs by < width_px."""
    sp = spacing_um / PX_UM
    g = np.arange(-sp, N + sp, sp)
    gy, gx = np.meshgrid(g, g, indexing="ij")
    seeds = np.stack([gy.ravel(), gx.ravel()], 1) + rng.uniform(-0.35, 0.35, (gy.size, 2)) * sp
    yy, xx = np.mgrid[0:N, 0:N]
    d, _ = cKDTree(seeds).query(np.stack([yy.ravel(), xx.ravel()], 1), k=2)
    return ((d[:, 1] - d[:, 0]) < width_px).reshape(N, N)


def smooth_field(rng, amp=10.0):
    """Low-frequency density variation (no crackle): white noise blurred at sigma 20 px, scaled."""
    import cv2
    f = cv2.GaussianBlur(rng.normal(0, 1, (N, N)).astype(np.float32), (0, 0), 20)
    return amp * f / (f.std() + 1e-9)


def stack(rng, cracks=None, contrast=12.0, n=17):
    base = BASE + smooth_field(rng)
    if cracks is not None:
        base = base - contrast * cracks
    return np.clip(base[None] + rng.normal(0, NOISE, (n, N, N)), 0, 255).astype(np.uint8)


def patch_energy(st):
    e = C.dog_energy(st)
    m = C.HALO
    return float(e[m:-m, m:-m].mean())


def test_dog_kernel_constants():
    assert (C.SIG1, C.SIG2) == (1.5, 6.0)
    assert (C.SL0, C.SL1) == (50, 67) and (C.SL1 - C.SL0) == 17
    assert C.HALF * PX_UM <= 20.0 < (C.HALF + 1) * PX_UM
    assert C.HALO >= 4 * C.SIG2


def test_crackle_vs_smooth_auc():
    rng = np.random.default_rng(1)
    ec, es = [], []
    for i in range(40):
        sp = rng.uniform(10, 40)
        ec.append(patch_energy(stack(rng, crack_network(sp, rng), contrast=12.0)))
        es.append(patch_energy(stack(rng)))
    auc = C.auc_float(np.array(ec), np.array(es))
    print("crackle vs smooth patch AUC", auc)
    assert auc > 0.9


def test_contrast_sensitivity_sweep():
    """Characterisation (reported, not a pass bar): patch AUC vs crack contrast / per-voxel noise.
    Asserts only that separation does not decrease with contrast and is > 0.9 at contrast >= noise."""
    rng = np.random.default_rng(2)
    res = {}
    for k in (0.25, 0.5, 1.0, 2.0):
        ec, es = [], []
        for i in range(40):
            sp = rng.uniform(10, 40)
            ec.append(patch_energy(stack(rng, crack_network(sp, rng), contrast=k * NOISE)))
            es.append(patch_energy(stack(rng)))
        res[k] = C.auc_float(np.array(ec), np.array(es))
    print("patch AUC by crack contrast / noise", {k: round(v, 3) for k, v in res.items()})
    v = [res[k] for k in sorted(res)]
    assert all(b >= a - 0.05 for a, b in zip(v, v[1:])), res
    assert res[1.0] > 0.9 and res[2.0] > 0.9, res


def test_dog_responds_to_10_40um_crack_spacing():
    """For every crack spacing 10-40 um, the crackle energy exceeds the smooth-patch energy by
    >= 50 % (contrast 12, noise 6). The smooth-field term's own energy over pure noise is reported."""
    rng = np.random.default_rng(3)
    smooth = np.mean([patch_energy(stack(rng)) for _ in range(6)])
    pure = np.mean([patch_energy(np.clip(BASE + rng.normal(0, NOISE, (17, N, N)), 0, 255).astype(np.uint8))
                    for _ in range(6)])
    print("smooth-patch / pure-noise energy", round(smooth / pure, 3))
    ratios = {}
    for sp in (10, 15, 20, 25, 30, 40):
        e = np.mean([patch_energy(stack(rng, crack_network(sp, rng), contrast=12.0)) for _ in range(4)])
        ratios[sp] = e / smooth
    print("energy ratio crackle/smooth by spacing (um)", {k: round(v, 3) for k, v in ratios.items()})
    assert all(v >= 1.5 for v in ratios.values()), ratios


def test_dog_transfer_function_band():
    """Sinusoid amplitude transfer of the DoG: peak period between 10 and 40 um (analytic and
    numeric agree), and the response at 40 um is >= 50 % of the peak."""
    s1, s2 = C.SIG1, C.SIG2
    f_star = np.sqrt(np.log(s2 ** 2 / s1 ** 2) / (2 * np.pi ** 2 * (s2 ** 2 - s1 ** 2)))
    period_um = PX_UM / f_star
    assert 10.0 <= period_um <= 40.0, period_um

    def H(f):
        return np.exp(-2 * np.pi ** 2 * s1 ** 2 * f ** 2) - np.exp(-2 * np.pi ** 2 * s2 ** 2 * f ** 2)

    peak = H(f_star)
    resp = {p: float(H(PX_UM / p) / peak) for p in (10, 15, 20, 30, 40)}
    print("DoG amplitude transfer relative to peak by period (um)", {k: round(v, 3) for k, v in resp.items()},
          "peak period um", round(period_um, 2))
    assert resp[40] >= 0.5
    # numeric check on a sinusoid of the peak period
    L = 512
    x = np.arange(L)
    img = (100 + 10 * np.sin(2 * np.pi * f_star * x))[None, :].repeat(L, 0)
    e = C.dog_energy(img[None].astype(np.float32))
    num_amp = np.sqrt(2 * e[64:-64, 64:-64].mean()) / 10.0
    assert abs(num_amp - peak) < 0.02, (num_amp, peak)


def test_auc_hist_matches_rank_auc():
    rng = np.random.default_rng(4)
    a = rng.integers(0, 256, 3000)
    b = rng.integers(0, 200, 5000)
    h1 = np.bincount(a, minlength=256)
    h2 = np.bincount(b, minlength=256)
    assert abs(C.auc_hist(h1, h2) - C.auc_float(a.astype(float), b.astype(float))) < 1e-9


def test_class_masks_boundary_exclusion():
    pred = np.zeros((100, 100), np.uint8)
    pred[:, 50:] = 200
    ink, bg = C.class_masks(pred, np.ones_like(pred, bool), 200, 0, px_um=18.727)
    # 50 um = 2.67 px: px-centre distance: ink col 52 is 3 px (56 um) from col 49, so kept; bg col 47 likewise
    cols_i = np.nonzero(ink.any(0))[0]
    cols_b = np.nonzero(bg.any(0))[0]
    assert cols_i.min() == 52 and cols_b.max() == 47
    assert not ink[:2].any() and ink[2].any() and not bg[-2:].any()  # tile edge counts as a boundary
