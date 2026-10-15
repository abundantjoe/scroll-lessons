"""Provenance: Project HERCULES | owner the owner | [id removed]

Unit tests for the DEV-LOOP evaluator (tools/sib/devloop/devlib.py) on synthetic maps with known blur,
known registration shifts and known resampling. Run: PYTHONPATH=src pytest -q tests/sib_devloop_evaluator.py
"""
import os
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'sib', 'devloop'))
import devlib as D  # noqa: E402

VOX = 9.362
PPM = 1000.0 / VOX


def strokes(shape=(600, 600), n=160, seed=0, width=4):
    """Synthetic 'reference' with letter-scale strokes (line segments 20-60 px, width ~4 px), values 0-255."""
    rng = np.random.default_rng(seed)
    img = np.zeros(shape, np.float32)
    for _ in range(n):
        y, x = rng.integers(20, shape[0] - 20), rng.integers(20, shape[1] - 20)
        L = rng.integers(20, 60)
        a = rng.uniform(0, np.pi)
        cv2.line(img, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), 1.0, width)
    return cv2.GaussianBlur(img, (0, 0), 1.0) * 255.0


def model_from(ref, sigma_mm, noise=0.0, seed=1, squash=False):
    rng = np.random.default_rng(seed)
    m = ref.astype(np.float64) if sigma_mm == 0 else cv2.GaussianBlur(ref.astype(np.float64), (0, 0),
                                                                       sigma_mm * PPM, borderType=cv2.BORDER_REFLECT)
    if squash:  # monotone nonlinearity like a sigmoid probability map, then uint8 like the official output
        m = 255.0 / (1.0 + np.exp(-(m / max(m.max(), 1e-9) - 0.3) * 8.0))
    m = m + rng.normal(0, noise, m.shape)
    return np.clip(m, 0, 255).astype(np.uint8)


@pytest.mark.parametrize('true_mm', [0.0, 0.05, 0.15, 0.30, 0.45])
def test_sigma_eq_recovers_known_blur(true_mm):
    ref = strokes()
    m = model_from(ref, true_mm, noise=2.0)
    valid = np.ones(ref.shape, bool)
    r = D.sigma_eq_window(m, ref, valid, VOX)
    assert abs(r['sigma_eq_mm'] - true_mm) <= 0.025 + 1e-9, r['sigma_eq_mm']
    assert r['r_best'] > 0.9


def test_sigma_eq_robust_to_monotone_squash_and_noise():
    ref = strokes(seed=3)
    m = model_from(ref, 0.20, noise=8.0, squash=True)
    r = D.sigma_eq_window(m, ref, np.ones(ref.shape, bool), VOX)
    assert abs(r['sigma_eq_mm'] - 0.20) <= 0.05, r['sigma_eq_mm']


def test_sigma_eq_ignores_invalid_pixels():
    ref = strokes(seed=4)
    m = model_from(ref, 0.10, noise=1.0)
    valid = np.ones(ref.shape, bool)
    valid[:, :200] = False
    m = m.copy()
    m[:, :200] = 255  # garbage where invalid must not matter
    r = D.sigma_eq_window(m, ref, valid, VOX)
    assert abs(r['sigma_eq_mm'] - 0.10) <= 0.025


def test_null_map_has_no_signal():
    ref = strokes(seed=5)
    rng = np.random.default_rng(9)
    null = rng.integers(0, 256, ref.shape).astype(np.uint8)
    r = D.sigma_eq_window(null, ref, np.ones(ref.shape, bool), VOX)
    assert abs(r['r_best']) < 0.1


def test_sigma_eq_monotone_in_true_blur():
    ref = strokes(seed=6)
    est = [D.sigma_eq_window(model_from(ref, s, noise=2.0), ref, np.ones(ref.shape, bool), VOX)['sigma_eq_mm']
           for s in (0.05, 0.15, 0.25, 0.35, 0.50)]
    assert all(b >= a for a, b in zip(est, est[1:])), est


def test_pooled_sigma_eq_over_windows():
    items = []
    for k in range(3):
        ref = strokes(seed=10 + k, shape=(400, 400))
        items.append((model_from(ref, 0.25, noise=2.0, seed=k), ref, np.ones(ref.shape, bool)))
    r = D.sigma_eq_pooled(items, VOX)
    assert abs(r['sigma_eq_mm'] - 0.25) <= 0.025 and r['r_best'] > 0.9
    # a single window through the pooled path equals the declared per-window function
    one = D.sigma_eq_window(*items[0], VOX)
    p1 = D.sigma_eq_pooled(items[:1], VOX)
    assert p1['sigma_eq_mm'] == one['sigma_eq_mm'] and abs(p1['r_best'] - one['r_best']) < 1e-12


def test_coordinate_map_inverse_and_level():
    c = np.array([0.0, 10.0, 1234.5, 2135.0])
    assert np.allclose(D.c2_to_c9(D.c9_to_c2(c, 3.8912), 3.8912), c)
    # pixel-centre convention of a 2^L mean pyramid: 2 x 2 mean of level 0
    a = np.random.default_rng(0).random((64, 64)).astype(np.float32)
    l1 = a.reshape(32, 2, 32, 2).mean((1, 3))
    y = np.array([10.0])
    yl = D.level_coord(y, 1)[0]  # level-0 row 10 = level-1 row 4.75
    assert abs(yl - 4.75) < 1e-12
    # bilinear value at level-1 (4.75, 4.75) approximates level-0 at (10, 10) for a smooth ramp
    ramp = np.add.outer(np.arange(64.0), np.arange(64.0))
    r1 = ramp.reshape(32, 2, 32, 2).mean((1, 3))
    v = cv2.remap(r1.astype(np.float32), np.float32([[yl]]), np.float32([[yl]]), cv2.INTER_LINEAR)[0, 0]
    assert abs(v - ramp[10, 10]) < 1e-4
    assert l1.shape == (32, 32)


def _synthetic_pair(r=(3.9, 3.88), shape9=(300, 280), seed=0):
    """A 9 um-canvas pattern P9 and its 2.4 um canvas rendering by the inverse formula (piecewise-constant on
    9 um pixel footprints), so that area-averaging recovers P9 away from footprint boundaries."""
    rng = np.random.default_rng(seed)
    P9 = cv2.resize(rng.random((shape9[0] // 10, shape9[1] // 10)).astype(np.float32), shape9[::-1],
                    interpolation=cv2.INTER_NEAREST) * 255
    H2 = int(round(shape9[0] * r[0])) + 60
    W2 = int(round(shape9[1] * r[1])) + 60
    yy = np.floor(D.c2_to_c9(np.arange(H2), r[0]) + 0.5).astype(int)
    xx = np.floor(D.c2_to_c9(np.arange(W2), r[1]) + 0.5).astype(int)
    yy = np.clip(yy, 0, shape9[0] - 1)
    xx = np.clip(xx, 0, shape9[1] - 1)
    P2 = P9[np.ix_(yy, xx)]
    return P9, P2


def test_ref_on_9_area_average_recovers_blocks():
    r = (3.9, 3.88)
    P9, P2 = _synthetic_pair(r)
    out, inside = D.ref_on_9(P2, (0, 0, P9.shape[0], P9.shape[1]), r)
    # compare interiors of the 10 x 10 constant blocks (footprint edges blur by < 1 px)
    m = np.zeros(P9.shape, bool)
    for i in range(0, P9.shape[0], 10):
        for j in range(0, P9.shape[1], 10):
            m[i + 2:i + 8, j + 2:j + 8] = True
    m &= inside
    assert np.abs(out[m] - P9[m]).max() < 1e-3


def test_ref_on_9_crop_origin_and_shift():
    r = (3.9, 3.88)
    P9, P2 = _synthetic_pair(r, seed=2)
    full, _ = D.ref_on_9(P2, (100, 90, 60, 70), r)
    crop = P2[300:700, 250:700]
    part, ins = D.ref_on_9(crop, (100, 90, 60, 70), r, ref_origin_yx=(300, 250))
    assert ins.all() and np.allclose(full, part)
    # a shift of exactly one 9 um pixel (r 2.4 um px) equals sampling the neighbouring 9 um window
    sh, _ = D.ref_on_9(P2, (100, 90, 60, 70), r, shift2_yx=(r[0], r[1]))
    nb, _ = D.ref_on_9(P2, (101, 91, 60, 70), r)
    assert np.allclose(sh, nb, atol=1e-3)


def _texture(shape, seed=0):
    rng = np.random.default_rng(seed)
    return cv2.GaussianBlur(rng.normal(0, 1, shape).astype(np.float32), (0, 0), 2.0)


@pytest.mark.parametrize('shift', [(0.0, 0.0), (1.3, -0.7), (-2.4, 2.2)])
def test_ct_residual_shift_recovers_known_shift(shift):
    big = _texture((700, 700), seed=1)
    h = w = 600
    S = 4
    y0 = x0 = 50
    ours = big[y0:y0 + h, x0:x0 + w].copy()
    valid = np.ones_like(ours, bool)

    def ct(dy, dx, pad):
        ys = np.arange(-pad, h + pad, dtype=np.float32) + y0 + shift[0] + dy
        xs = np.arange(-pad, w + pad, dtype=np.float32) + x0 + shift[1] + dx
        my, mx = np.meshgrid(ys, xs, indexing='ij')
        img = cv2.remap(big, mx, my, cv2.INTER_CUBIC)
        return img + np.random.default_rng(3).normal(0, 0.05, img.shape).astype(np.float32), np.ones(img.shape, bool)

    res = D.ct_residual_shift(ours, valid, ct, sub_windows=3, max_shift=S)
    assert res['n_good'] == 9
    # ct(y) = big(y0 + shift + y), ours(y) = big(y0 + y) = ct(y - shift): the correction to ADD to the mapped
    # coordinate is -shift, and sampling the CT with it re-aligns it with ours
    assert abs(res['shift9'][0] + shift[0]) < 0.25 and abs(res['shift9'][1] + shift[1]) < 0.25, res['shift9']
    fixed, _ = ct(res['shift9'][0], res['shift9'][1], 0)
    raw, _ = ct(0.0, 0.0, 0)
    n_fixed, n_raw = D._ncc(ours, fixed, valid), D._ncc(ours, raw, valid)
    assert n_fixed > 0.9 and n_fixed >= n_raw - 1e-3, (n_fixed, n_raw)  # noise (0.05 vs texture std ~0.14) caps NCC


def test_ct_residual_shift_rejects_unrelated_ct():
    ours = _texture((300, 300), seed=5)

    def ct(dy, dx, pad):
        return _texture((300 + 2 * pad, 300 + 2 * pad), seed=6), np.ones((300 + 2 * pad, 300 + 2 * pad), bool)

    res = D.ct_residual_shift(ours, np.ones_like(ours, bool), ct, sub_windows=3, max_shift=4, min_ncc=0.35)
    assert res['n_good'] <= 1


def test_blob_constraint_and_finalist_rule():
    m = np.zeros((2136, 2136), np.uint8)
    v = np.ones_like(m, bool)
    assert D.blob_f180_window(m, v, VOX)['blob_f180'] == 0.0
    m[100:600, 100:600] = 200  # a big false blob: 250000 / 4.56e6 = 0.055 > 0.0272
    b = D.blob_f180_window(m, v, VOX)
    assert b['blob_f180'] > D.BLOB_BAR and abs(b['area_cm2'] - 3.998) < 0.01
    ok = D.finalist({'A': 0.30, 'B': 0.35, 'C': 0.349}, 0.30, blob_ok=True)
    assert ok['finalist'] and ok['n_pass'] == 3 and abs(ok['bar_mm'] - 0.35) < 1e-12
    assert not D.finalist({'A': 0.30, 'B': 0.35, 'C': 0.375}, 0.30, blob_ok=True)['finalist']
    assert not D.finalist({'A': 0.1, 'B': 0.1, 'C': 0.1}, 0.30, blob_ok=False)['finalist']
    assert not D.finalist({'A': 0.1, 'B': 0.1}, 0.30, blob_ok=True)['finalist']
    assert not D.finalist({'A': 0.1, 'B': 0.1, 'C': float('nan')}, 0.30, blob_ok=True)['finalist']


def test_text_order_choice_and_labels():
    assert D.text_order_choice(0.73, 0.54) == 'forward'
    assert D.text_order_choice(0.5, 0.6) == 'reverse'
    assert D.text_order_choice(0.5, 0.5) is None
    assert D.text_order_choice(float('nan'), 0.5) is None
    ref = np.array([[0, 100, 120, 150, 255]], np.float32)
    lab = D.ref_labels(ref, np.array([[1, 1, 1, 1, 0]], bool))
    assert lab.tolist() == [[0, 0, 255, 1, 255]]


def test_misregistration_inflates_sigma_eq():
    """Why registration matters: a 3 px (0.028 mm) shift of a sharp model map raises sigma_eq above 0."""
    ref = strokes(seed=8)
    m = model_from(ref, 0.0, noise=1.0)
    sh = np.roll(m, 3, axis=1)
    v = np.ones(ref.shape, bool)
    v[:, :10] = False
    s0 = D.sigma_eq_window(m, ref, v, VOX)['sigma_eq_mm']
    s3 = D.sigma_eq_window(sh, ref, v, VOX)['sigma_eq_mm']
    assert s0 == 0.0 and s3 >= 0.025


def test_vendored_surface_distance_catches_offset_retrace():
    """CORR-RETRACE-RULE: an exact re-trace offset by half a dense cell is SAME under the surface form (the vertex
    form under-calls it on 20-vox meshes)."""
    from hercules.geometry.tifxyz import densify
    import surfdist as SD
    u, v = np.meshgrid(np.arange(0, 400, 20.0), np.arange(0, 400, 20.0))
    B = np.stack([u, v, np.full_like(u, 100.0)], -1)
    A = np.stack([u + 2.0, v + 2.0, np.full_like(u, 100.5)], -1)  # same sheet, shifted half a dense cell, 0.5 vox off
    Ad, Bd = densify(A, 5), densify(B, 5)
    r = SD.same_papyrus_surface(Ad.reshape(-1, 3), Bd)
    assert r['same'] and r['counts'][0] >= 2 * r['counts'][2]  # c2 > 0 only where A overhangs B's border
    d = SD.surface_distances(np.array([[50.0, 50.0, 103.0]]), Bd, max_dist=5.0)
    assert abs(d[0] - 3.0) < 1e-9
    far = np.stack([u, v, np.full_like(u, 110.0)], -1)  # neighbouring sheet 10 vox away: NOT SAME
    assert not SD.same_papyrus_surface(densify(far, 5).reshape(-1, 3), Bd)['same']
