# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests of logs/sib/readcal2/p4ms/p4ms.py on a synthetic canvas (no P4 data, no image viewed)."""
import os
import sys

import cv2
import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'logs', 'sib', 'readcal2', 'p4ms'))
sys.path.insert(0, os.path.join(REPO, 'src'))
import p4ms as P  # noqa: E402
from hercules.display import builder as B  # noqa: E402
from hercules.scorer.display import DisplayMap  # noqa: E402

T = 2200  # small synthetic tile (real: 8343); still >= 2 x 1068 so every scale downsamples
GRID = P.Grid(T=T, px_per_mm=T / 20.0, canvas_hw=(3 * T, 3 * T), n_rows=3, n_cols=3)


def canvas():
    rng = np.random.default_rng(0)
    v = rng.integers(20, 230, (3 * T, 3 * T)).astype(np.uint8)
    ok = np.ones_like(v, bool)
    ok[:, : T // 3] = False  # column 0 mostly invalid (-> tiles still eligible at >= 50 %)
    ok[2 * T:, 2 * T:] = False  # tile (2, 2) fully invalid
    return v, ok


V, OK = canvas()


def source(y0, y1, x0, x1):
    v = np.zeros((y1 - y0, x1 - x0), np.uint8)
    o = np.zeros_like(v, bool)
    ya, yb, xa, xb = max(0, y0), min(V.shape[0], y1), max(0, x0), min(V.shape[1], x1)
    v[ya - y0:yb - y0, xa - x0:xb - x0] = V[ya:yb, xa:xb]
    o[ya - y0:yb - y0, xa - x0:xb - x0] = OK[ya:yb, xa:xb]
    return v, o


TILES = [{'r': r, 'c': c} for r in range(3) for c in range(3)]


def test_windows_geometry_and_px_per_mm():
    ws = P.windows(GRID, TILES)
    s2 = [w for w in ws if w.scale == 'S2']
    s1 = [w for w in ws if w.scale == 'S1']
    s4 = [w for w in ws if w.scale == 'S4']
    assert len(s2) == 9 and len(s1) == 36 and len(s4) == 4
    for w in s2:
        assert (w.h, w.w) == (T, T) and w.px_per_mm(GRID) == pytest.approx(53.4)
    for w in s4:
        assert (w.h, w.w) == (2 * T, 2 * T) and w.px_per_mm(GRID) == pytest.approx(26.7)
    # the 4 zooms tile their tile exactly, without gaps or overlap
    for r in range(3):
        for c in range(3):
            m = np.zeros((T, T), int)
            for w in [z for z in s1 if (z.r, z.c) == (r, c)]:
                m[w.y0 - r * T:w.y1 - r * T, w.x0 - c * T:w.x1 - c * T] += 1
                assert w.px_per_mm(GRID) == pytest.approx(106.8, rel=1e-3)
            assert (m == 1).all()
    # the real grid gives the declared px/mm
    real = P.Grid(8343, 417.1314650253318, (69760, 170000), 9, 21)
    w = P.windows(real, [{'r': 0, 'c': 0}, {'r': 0, 'c': 1}, {'r': 1, 'c': 0}, {'r': 1, 'c': 1}])
    pm = {x.scale: round(x.px_per_mm(real), 2) for x in w if x.part in ('block', 'tile', 'TL')}
    assert pm == {'S4': 26.7, 'S2': 53.4, 'S1': 106.81}  # TL = T // 2 = 4171 px; BR 4172 px -> 106.79


def test_s4_requires_all_four_tiles():
    ws = P.windows(GRID, [t for t in TILES if (t['r'], t['c']) != (1, 1)])
    assert not any(w.scale == 'S4' for w in ws)


def test_global_mapping_matches_p4l2_rule_and_s2_is_plain_area_downscale():
    v, o = source(0, T, T, 2 * T)
    img, par = P.render(v, o, 'global', t_mid=93, t_hi=203)
    f = np.clip((v.astype(np.float32) - np.float32(93)) * np.float32(255.0 / 110), 0, 255)
    ref = np.rint(f).astype(np.uint8)
    ref[~o] = 0
    assert np.array_equal(img, cv2.resize(ref, (1068, 1068), interpolation=cv2.INTER_AREA))
    assert par['mode'] == 'global'


def test_window_mapping_matches_display_builder_ct_window():
    v, o = source(0, T, T, 2 * T)
    img, par = P.render(v, o, 'window')
    u8, _ = B.linear_window_ct(v.astype(np.float64), o)
    exp = cv2.resize(np.where(o, u8, 0).astype(np.uint8), (1068, 1068), interpolation=cv2.INTER_AREA)
    assert np.array_equal(img, exp)
    img2, par2 = P.render(v, o, 'window', positive_only=True)
    assert par2['positive_only'] and par2['n'] <= par['n']


def test_downscale_only():
    v = np.zeros((1000, 1000), np.uint8)
    with pytest.raises(ValueError):
        P.render(v, np.ones_like(v, bool), 'window')


def test_build_deterministic_eligibility_keys_and_verify(tmp_path):
    b1 = P.build(GRID, TILES, source, 'global', str(tmp_path / 'a'), 20260926, t_mid=93, t_hi=203)
    b2 = P.build(GRID, TILES, source, 'global', str(tmp_path / 'b'), 20260926, t_mid=93, t_hi=203)
    assert b1['manifest'] == b2['manifest'] and b1['key'] == b2['key']
    sk = {(s['scale'], s['r'], s['c'], s['part']) for s in b1['skipped']}
    assert ('S2', 2, 2, 'tile') in sk and all(s['valid_fraction'] < 0.5 for s in b1['skipped'])
    for u in b1['manifest']:
        data = open(tmp_path / 'a' / (u + '.png'), 'rb').read()
        assert P.sha(data) == b1['manifest'][u] and b'tEXt' not in data
    # S2 of the builder equals an independently computed tile PNG (the verify path used on real manifests)
    tiles_ref = []
    for t in TILES:
        v, o = source(*GRID.tile_rect(t['r'], t['c']))
        if o.mean() < 0.5:
            continue
        img, _ = P.render(v, o, 'global', t_mid=93, t_hi=203)
        tiles_ref.append(dict(t, png_sha256=P.sha(B.png_bytes(img))))
    chk = P.verify_s2_against_manifest(b1, tiles_ref)
    assert chk['all_equal'] and chk['n_s2'] == 8


def test_key_maps_to_canvas_like_scorer_displaymap():
    b = P.build(GRID, TILES[:4] + [{'r': 1, 'c': 0}, {'r': 1, 'c': 1}], source, 'window', '/tmp/p4ms_test_keys', 7,
                scales=('S4', 'S1'))
    for u, k in b['key'].items():
        dm = DisplayMap('r', 'i', 'w', k['scale_canvas_px_per_image_px'], k['y0'], k['x0'], ('text', 'nontext'))
        for (x, y) in ((0, 0), (500.5, 1000), (1067, 1067)):
            assert P.image_to_canvas(x, y, k) == pytest.approx(dm.to_canvas(x, y))
        X, Y = P.image_to_canvas(1067.5, 1067.5, k)  # image edge -> window edge
        assert X == pytest.approx(k['x0'] + k['w'] - 0.5) and Y == pytest.approx(k['y0'] + k['h'] - 0.5)
