# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests of the READCAL-2 builders (tools/sib/readcal2/rc2lib.py). Arrays and hashes only."""
import hashlib
import math
import os
import sys
import uuid

import cv2
import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'sib', 'readcal2'))
sys.path.insert(0, os.path.join(REPO, 'src'))
import rc2lib as R  # noqa: E402
from hercules.display import builder as B  # noqa: E402
from hercules.scorer.display import DisplayMap  # noqa: E402

VOX = 9.362
FONTS_OK = os.path.exists(R.FONT_SERIF) and os.path.exists(R.FONT_SANS)
needs_fonts = pytest.mark.skipif(not FONTS_OK, reason='DejaVu fonts not installed')


def _toy_noise(var=100.0, fc=0.05):
    f = np.linspace(0, 0.75, 200)
    shape = 1.0 / (1.0 + (f / fc) ** 2)
    m = R.NoiseModel(radial_f=f, radial_psd=shape, mean=60.0, var=var)
    g = m.psd_on_grid((512, 512)).copy()
    g[0, 0] = 0
    m.radial_psd = shape * var / g.mean()
    return m


@needs_fonts
def test_keysheet_is_byte_exact_regeneration_of_frozen_sheet():
    ks = R.keysheet()
    assert ks.shape == (1068, 1068) and ks.dtype == np.uint8
    assert R.sha256(R.png_bytes(ks)) == R.KEYSHEET_SHA256
    frozen = cv2.imread(os.path.join(REPO, 'configs/briefs/probe2_keysheet.png'), cv2.IMREAD_UNCHANGED)
    assert np.array_equal(frozen, ks)
    assert hashlib.sha256(open(os.path.join(REPO, 'configs/briefs/probe2_keysheet.png'), 'rb').read()).hexdigest() == R.KEYSHEET_SHA256


def test_png_bytes_matches_display_builder_encoder():
    a = (np.arange(64 * 48) % 251).astype(np.uint8).reshape(48, 64)
    assert R.png_bytes(a) == B.png_bytes(a)
    assert b'tEXt' not in R.png_bytes(a) and b'iTXt' not in R.png_bytes(a)


def test_uuid_stream_deterministic_distinct_uuid4():
    a = [R.UuidStream(7, 'x').next() for _ in range(1)]
    s1, s2 = R.UuidStream(7, 'x'), R.UuidStream(7, 'x')
    l1 = [s1.next() for _ in range(100)]
    l2 = [s2.next() for _ in range(100)]
    assert l1 == l2 and len(set(l1)) == 100 and a[0] == l1[0]
    assert all(uuid.UUID(u).version == 4 for u in l1)
    assert R.UuidStream(8, 'x').next() != l1[0] and R.UuidStream(7, 'y').next() != l1[0]


def test_voxel_guard():
    with pytest.raises(ValueError):
        R.px_per_mm_canvas(0.009362)  # mm passed by mistake
    assert abs(R.px_per_mm_canvas(9.362) - 106.8147) < 1e-3


@needs_fonts
def test_glyph_cap_height_matches_declared_mm():
    fpx, band, cw, cent = R.glyph_layout(VOX)
    cov = R.glyph_coverage('Η', fpx, (band, cw))
    rows = np.nonzero(cov.max(1) > 0.5)[0]
    cap_mm = (rows[-1] - rows[0] + 1) / R.px_per_mm_canvas(VOX)
    assert abs(cap_mm - R.CAP_HEIGHT_MM) < 0.02
    assert len(cent) == 24 and band == 400 and cw == 356


@needs_fonts
def test_placebo_blobs_match_ink_area_and_are_not_glyphs():
    covs, _ = R.glyph_covs(VOX)
    blobs, info = R.placebo_covs(covs, 20260925)
    blobs2, _ = R.placebo_covs(covs, 20260925)
    assert all(np.array_equal(a, b) for a, b in zip(blobs, blobs2))
    for d in info:
        assert abs(d['blob_area_px'] - d['glyph_area_px']) <= 0.01 * d['glyph_area_px']

    def cen(a):
        ys, xs = np.nonzero(a > 0.5)
        return ys.mean(), xs.mean()

    def iou(g, b):
        (gy, gx), (by, bx) = cen(g), cen(b)
        M = np.float32([[1, 0, gx - bx], [0, 1, gy - by]])
        s = cv2.warpAffine(b.astype(np.float32), M, (b.shape[1], b.shape[0])) > 0.5
        m = g > 0.5
        return (s & m).sum() / (s | m).sum()
    worst = max(iou(g, b) for b in blobs for g in covs)
    assert worst < 0.6, worst


def test_synth_noise_reproduces_spectrum_and_variance():
    m = _toy_noise()
    rng = np.random.default_rng(1)
    x = R.synth_noise(m, (1024, 1024), rng)
    assert abs(x.mean()) < 0.5
    assert abs(x.var() / m.var - 1) < 0.08
    p2 = R.periodogram_tiles(x, None, tile=256, step=128)
    f, pr = R.radial_average(p2, 64)
    target = np.interp(f, m.radial_f, m.radial_psd)
    sel = (f > 0.01) & (f < 0.45)
    rel = np.abs(pr[sel] / target[sel] - 1)
    assert np.median(rel) < 0.08 and rel.max() < 0.35


def test_periodogram_mean_equals_variance_for_white_noise():
    x = np.random.default_rng(2).normal(0, 3, (1024, 1024))
    p2 = R.periodogram_tiles(x, None)
    assert abs(p2.mean() / 9.0 - 1) < 0.03


@needs_fonts
def test_exemplar_and_placebo_share_noise_and_labels():
    covs, _ = R.glyph_covs(VOX)
    blobs, _ = R.placebo_covs(covs, 3)
    m = _toy_noise()
    ex, _ = R.render_sheet(covs, 0.30, m, VOX, seed=11)
    pl, _ = R.render_sheet(blobs, 0.30, m, VOX, seed=11)
    zero, _ = R.render_sheet([np.zeros_like(c) for c in covs], 0.30, m, VOX, seed=11)
    ex2, _ = R.render_sheet(covs, 0.30, m, VOX, seed=11)
    assert np.array_equal(ex, ex2) and ex.shape == (1068, 1068)
    # label strips identical
    for r in range(4):
        sl = slice(r * 267 + 200, (r + 1) * 267)
        assert np.array_equal(ex[sl], pl[sl]) and np.array_equal(ex[sl], zero[sl])
    # away from ink, EX, placebo and an empty sheet carry the same noise field (the shape contribution
    # there is < 1e-3 of the ink contrast, so the uint8 pixels differ by at most 1 rounding step)
    f = R.glyph_field(covs, VOX) + R.glyph_field(blobs, VOX)
    far = R.area_downscale((R.gaussian_blur_canvas(f, 0.30, VOX, cv2.BORDER_CONSTANT) < 1e-3).astype(np.uint8) * 255, 0.5) == 255
    band = np.zeros((1068, 1068), bool)
    for r in range(4):
        band[r * 267:r * 267 + 200] = far[r * 200:(r + 1) * 200]
    assert band.sum() > 2000
    for a in (ex, pl):
        d = np.abs(a[band].astype(int) - zero[band].astype(int))
        assert d.max() <= 1 and (d == 0).mean() > 0.9
    assert not np.array_equal(ex, pl)
    # a different seed changes the noise
    ex3, _ = R.render_sheet(covs, 0.30, m, VOX, seed=12)
    assert not np.array_equal(ex, ex3)


def test_blur_operator_width_in_mm():
    img = np.zeros((801, 801))
    img[400, 400] = 1.0
    for s in (0.15, 0.30, 0.45):
        b = R.gaussian_blur_canvas(img, s, VOX)
        yy, xx = np.mgrid[0:801, 0:801]
        sd = math.sqrt((b * (xx - 400) ** 2).sum() / b.sum())
        assert abs(sd / (s * R.px_per_mm_canvas(VOX)) - 1) < 0.02


def test_blur_valid_normalised_and_masked():
    rng = np.random.default_rng(0)
    ref = np.full((300, 300), 120.0)
    valid = np.ones((300, 300), bool)
    valid[:, :80] = False
    ref[~valid] = np.nan
    out = R.blur_valid(ref, valid, 0.30, VOX)
    assert np.allclose(out[valid], 120.0, atol=1e-6) and np.all(out[~valid] == 0)
    r2 = rng.uniform(0, 255, (300, 300))
    assert np.array_equal(R.blur_valid(r2, valid, 0.0, VOX)[valid], r2[valid])


def test_ref_ladder_sigma0_equals_display_builder_path():
    rng = np.random.default_rng(3)
    ref = rng.uniform(0, 255, (2136, 2136))
    valid = np.ones_like(ref, bool)
    valid[:10] = False
    lad = R.ref_ladder_images(ref, valid, VOX, sigmas=(0.0, 0.30))
    exp = B.area_downscale(B.model_map_u8(np.where(valid, ref, 0.0)), 0.5)
    assert np.array_equal(lad[0.0], exp)
    assert lad[0.30].shape == (1068, 1068) and lad[0.30].std() < lad[0.0].std()
    with pytest.raises(ValueError):
        R.ref_ladder_images(ref[:100, :100], valid[:100, :100], VOX)


def test_ms_images_geometry_and_scorer_frame():
    w = (np.arange(2136 * 2136) % 253).astype(np.uint8).reshape(2136, 2136)
    parts = R.ms_images(w)
    assert [p[0] for p in parts] == ['OV', 'TL', 'TR', 'BL', 'BR']
    assert all(p[1].shape == (1068, 1068) for p in parts)
    assert np.array_equal(parts[0][1], B.area_downscale(w, 0.5))
    for name, img, scale, y0, x0 in parts[1:]:
        assert scale == 1.0 and np.array_equal(img, w[y0:y0 + 1068, x0:x0 + 1068])
    # canvas mapping identical to the scorer's DisplayMap convention
    for name, img, scale, y0, x0 in parts:
        dm = DisplayMap('r', 'i', 'w', scale, y0, x0, ('text', 'nontext'))
        for (x, y) in ((0, 0), (533.5, 12), (1067, 1067)):
            assert R.image_to_canvas(x, y, scale, x0, y0) == dm.to_canvas(x, y)


def test_ms_merge_dedupes_same_identity_only():
    n = [{'ch': 'Α', 'x': 100, 'y': 100, 'conf': 'tentative', 'part': 'OV'},
         {'ch': 'Α', 'x': 130, 'y': 110, 'conf': 'firm', 'part': 'TL'},
         {'ch': 'Ο', 'x': 105, 'y': 100, 'conf': 'tentative', 'part': 'OV'},
         {'ch': 'Α', 'x': 400, 'y': 100, 'conf': 'tentative', 'part': 'OV'}]
    m = R.ms_merge(n)
    assert len(m) == 3
    a = [x for x in m if x['ch'] == 'Α' and x['x'] < 200]
    assert len(a) == 1 and a[0]['part'] == 'TL' and a[0]['conf'] == 'firm'
    n[1]['conf'] = 'tentative'
    n[0]['conf'] = 'firm'
    assert [x for x in R.ms_merge(n) if x['ch'] == 'Α' and x['x'] < 200][0]['conf'] == 'firm'


def test_row_residuals():
    rows = [{'y': 100.0, 'angle_deg': 0.0}, {'y': 300.0, 'angle_deg': 45.0}]
    letters = [{'x': 50, 'y': 80, 'box': [40, 60, 60, 102], 'row': 0},
               {'x': 100, 'y': 380, 'box': [90, 360, 110, 395], 'row': 1},
               {'x': 5, 'y': 5, 'box': [0, 0, 10, 10]}]
    r = R.row_letter_residuals(rows, letters)
    assert r[0] == pytest.approx(2.0) and r[1] == pytest.approx(395 - 400) and r[2] is None


def test_masked_periodogram_agrees_with_tiles_on_red_noise_with_holes():
    m = _toy_noise(var=400.0, fc=0.01)
    x = R.synth_noise(m, (2136, 2136), np.random.default_rng(4)) + 77.0
    valid = np.ones((2136, 2136), bool)
    valid[:, :600] = False
    valid[1500:, 1500:] = False
    pm = R.periodogram_masked(x, valid)
    pt = R.periodogram_tiles(x, valid)
    fm, prm = R.radial_average(pm, 256)
    ft, prt = R.radial_average(pt, 64)
    sel = (ft >= 0.02) & (ft <= 0.45)
    ratio = np.interp(ft[sel], fm, prm) / prt[sel]
    assert 0.85 < np.median(ratio) < 1.15
    target = np.interp(fm, m.radial_f, m.radial_psd)
    s2 = (fm > 0.003) & (fm < 0.3)
    assert np.median(np.abs(prm[s2] / target[s2] - 1)) < 0.15
