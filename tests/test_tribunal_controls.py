# Provenance: Project HERCULES | owner the owner | [id removed]
"""Numerical tests of the TRIBUNAL batch-control builders (no image is ever viewed)."""


import cv2
import numpy as np
import pytest

from hercules.metrics.pixel import sigma_eq
from hercules.records.cf_scan import scan_bytes
from hercules.tribunal import controls as K

PX_PER_MM = 1000.0 / 9.366


def _synthetic_text(h=400, w=400, seed=0):
    """Stroke-like synthetic 'known text' map (0-255), not real material."""
    rng = np.random.default_rng(seed)
    img = np.full((h, w), 40.0)
    for _ in range(25):
        y, x = rng.integers(20, h - 20), rng.integers(20, w - 20)
        cv2.line(img, (int(x), int(y)), (int(x + rng.integers(-30, 30)), int(y + rng.integers(-30, 30))), 230.0, 4)
    return img


# ----------------------------------------------------------------------------- blur

def test_blur_sigma_zero_is_identity():
    a = _synthetic_text()
    np.testing.assert_array_equal(K.gaussian_blur_mm(a, 0.0, PX_PER_MM), a)


@pytest.mark.parametrize("sigma_mm", [0.05, 0.1, 0.2])
def test_blur_impulse_second_moment_equals_declared_sigma(sigma_mm):
    a = np.zeros((301, 301))
    a[150, 150] = 1.0
    b = K.gaussian_blur_mm(a, sigma_mm, PX_PER_MM)
    y, x = np.mgrid[0:301, 0:301] - 150.0
    var_x = float((b * x * x).sum() / b.sum())
    var_y = float((b * y * y).sum() / b.sum())
    s_px = sigma_mm * PX_PER_MM
    assert abs(np.sqrt(var_x) - s_px) / s_px < 0.02 and abs(np.sqrt(var_y) - s_px) / s_px < 0.02
    assert abs(b.sum() - 1.0) < 1e-6


def test_blur_matches_sigma_eq_measurement():
    """A canary blurred by declared sigma is measured back at that sigma by the project's
    own sigma_eq (same kernel, same border)."""
    ref = _synthetic_text(seed=3)
    for s in (0.1, 0.2, 0.3):
        best, r, _ = sigma_eq(K.gaussian_blur_mm(ref, s, PX_PER_MM), ref, PX_PER_MM)
        assert abs(best - s) < 1e-9 and r > 0.999


def test_positive_canary_key_and_display():
    ref = _synthetic_text()
    img, key = K.build_positive_canary(ref, sigma_mm=0.2, px_per_mm=PX_PER_MM, canary_id="c1",
                                       source={"fold": "K"})
    assert img.dtype == np.uint8 and img.shape == (200, 200)
    assert key["sigma_px"] == pytest.approx(0.2 * PX_PER_MM)
    assert key["window"] == "raw" and key["interp"] == "INTER_AREA" and key["display_scale"] == 0.5
    expect = cv2.resize(np.rint(np.clip(K.gaussian_blur_mm(ref, 0.2, PX_PER_MM), 0, 255)).astype(np.uint8),
                        (200, 200), interpolation=cv2.INTER_AREA)
    np.testing.assert_array_equal(img, expect)


# ----------------------------------------------------------------------------- display rule

def test_raw_window_is_identity_for_u8_and_scales_probabilities():
    a = (np.arange(256, dtype=np.uint8)[None, :].repeat(4, 0))
    np.testing.assert_array_equal(K.to_display_u8(a, "raw")[0], a)
    p = np.linspace(0, 1, 11)[None, :]
    np.testing.assert_array_equal(K.to_display_u8(p, "raw")[0], np.rint(p * 255).astype(np.uint8))


def test_p1p99_window_is_linear():
    rng = np.random.default_rng(1)
    a = rng.normal(100, 20, (200, 200))
    u8, meta = K.to_display_u8(a, "p1p99")
    lo, hi = np.percentile(a, [1, 99])
    assert meta["lo"] == pytest.approx(lo) and meta["hi"] == pytest.approx(hi)
    inner = (a > lo) & (a < hi)
    expect = (a[inner] - lo) / (hi - lo) * 255
    assert np.max(np.abs(u8[inner] - expect)) <= 0.5 + 1e-9
    assert u8[a <= lo].max() == 0 and u8[a >= hi].min() == 255


def test_area_downscale_is_block_mean():
    a = np.random.default_rng(2).integers(0, 256, (64, 64)).astype(np.uint8)
    img, _ = K._finish(a, "raw", 0.5)
    blocks = a.reshape(32, 2, 32, 2).astype(float).mean(axis=(1, 3))
    assert np.max(np.abs(img.astype(float) - blocks)) <= 0.5 + 1e-9


# ----------------------------------------------------------------------------- baits

def test_bait_pixel_shuffle_keeps_histogram_exactly():
    a = _synthetic_text()
    b = K.blank_like(a, "pixel_shuffle", np.random.default_rng(0))
    np.testing.assert_array_equal(np.sort(a.ravel()), np.sort(b.ravel()))
    assert abs(np.corrcoef(a.ravel(), b.ravel())[0, 1]) < 0.05


def test_bait_phase_scramble_keeps_amplitude_spectrum():
    a = _synthetic_text()
    b = K.blank_like(a, "phase_scramble", np.random.default_rng(0))
    Fa = np.abs(np.fft.fft2(a - a.mean()))
    Fb = np.abs(np.fft.fft2(b - b.mean()))
    assert np.max(np.abs(Fa - Fb)) / Fa.max() < 1e-9
    assert abs(b.mean() - a.mean()) < 1e-9
    assert abs(np.corrcoef(a.ravel(), b.ravel())[0, 1]) < 0.1


def test_bait_constant_blank():
    b = K.blank_like(_synthetic_text(), "constant", np.random.default_rng(0))
    assert b.std() == 0


@pytest.mark.parametrize("kind", K.BAIT_KINDS)
def test_bait_builders_follow_display_rule(kind):
    m = _synthetic_text()
    img, key = K.build_bait(kind, m, bait_id="b", blank_mode="phase_scramble" if kind == "blank" else None,
                            rng=np.random.default_rng(0))
    assert key["type"] == "bait" and key["kind"] == kind and img.shape == (200, 200)
    if kind != "blank":  # wrong-order and NULL-arm maps are shown exactly like any map
        expect = cv2.resize(np.rint(m).astype(np.uint8), (200, 200), interpolation=cv2.INTER_AREA)
        np.testing.assert_array_equal(img, expect)


def test_bait_rejects_unknown_kind():
    with pytest.raises(ValueError):
        K.build_bait("inverted", _synthetic_text(), bait_id="b")


# ----------------------------------------------------------------------------- mirror canaries

def test_mirror_canaries_complete_and_exact_mirrors():
    items = K.build_mirror_canaries(px_per_mm=PX_PER_MM, canvas_hw=(512, 512), letter_height_mm=2.5,
                                    rng=np.random.default_rng(0))
    assert len(items) == 14
    by = {(k["glyph"], k["mirrored"]): img for img, k in items}
    assert {g for g, _ in by} == set("EKRCGBN")
    for g in "EKRCGBN":
        np.testing.assert_array_equal(by[(g, True)], by[(g, False)][:, ::-1])
        assert K.asymmetry(by[(g, False)]) > 0.05  # every glyph is left-right asymmetric
    keys = [k for _, k in items]
    assert all(k["font_sha256"] == K.font_sha256() for k in keys)
    assert all(k["glyph_asymmetry"] > 0.1 for k in keys)


def test_mirror_glyph_height_close_to_declared():
    m = K.glyph_mask("E", height_px=270, canvas_hw=(512, 512))
    rows = np.flatnonzero(m.max(axis=1) > 0.5)
    assert abs((rows[-1] - rows[0] + 1) - 270) / 270 < 0.05


# ----------------------------------------------------------------------------- files

def test_written_png_has_no_metadata_and_uuid_name(tmp_path):
    img, key = K.build_positive_canary(_synthetic_text(), sigma_mm=0.1, px_per_mm=PX_PER_MM, canary_id="c")
    keys = K.write_controls([(img, key)], tmp_path)
    f = tmp_path / keys[0]["image"]["name"]
    data = f.read_bytes()
    assert set(K.png_chunks(data)) <= K.ALLOWED_PNG_CHUNKS
    assert scan_bytes(str(f), data) == []
    assert len(f.stem) == 36 and f.stem.count("-") == 4
    assert "canary_id" not in f.name and keys[0]["canary_id"] == "c"


def test_encode_rejects_oversize():
    with pytest.raises(ValueError):
        K.encode_png(np.zeros((1069, 10), dtype=np.uint8))
