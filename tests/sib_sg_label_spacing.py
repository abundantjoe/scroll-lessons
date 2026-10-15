# Provenance: Project HERCULES | owner the owner | [id removed]
"""Known-answer tests of tools/sib/sg/label_spacing.py (synthetic masks only)."""

import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "sib" / "sg"))
import label_spacing as LS  # noqa: E402

PX_MM = 1000.0 / 9.362


def fake_text(pitch_mm, h_mm, angle_deg, size_mm=20.0, seed=0, jitter_mm=0.0):
    """Binary mask of letter-like rings on rows at ``pitch_mm``, rotated by ``angle_deg``."""
    rng = np.random.default_rng(seed)
    n = int(size_mm * PX_MM)
    big = np.zeros((2 * n, 2 * n), np.uint8)
    h = h_mm * PX_MM
    y = 0.3 * n
    while y < 1.7 * n:
        x = 0.3 * n + rng.uniform(0, h)  # rows are not column-aligned (real text)
        yy = y + rng.uniform(-jitter_mm, jitter_mm) * PX_MM
        while x < 1.7 * n:
            w = h * rng.uniform(0.25, 0.45)
            c = (int(x), int(yy))
            cv2.ellipse(big, c, (int(w), int(h / 2)), 0, 0, 360, 1, thickness=max(2, int(0.12 * h)))
            x += 2 * w + h * rng.uniform(0.15, 0.5)
        y += pitch_mm * PX_MM
    m = cv2.getRotationMatrix2D((n - 0.5, n - 0.5), angle_deg, 1.0)
    rot = cv2.warpAffine(big, m, (2 * n, 2 * n), flags=cv2.INTER_NEAREST)
    return rot[n // 2:n // 2 + n, n // 2:n // 2 + n]


@pytest.mark.parametrize("pitch,h,angle", [(4.5, 2.8, 0.0), (5.0, 3.0, 7.0), (4.0, 2.2, 95.0), (6.0, 3.5, 160.0)])
def test_recovers_pitch_height_angle(pitch, h, angle):
    r = LS.measure_tile(fake_text(pitch, h, angle, size_mm=30.0), PX_MM)
    # row_angle_deg is reported in the cv2.getRotationMatrix2D convention of the generator
    d = abs(((r["row_angle_deg"] - angle) + 90) % 180 - 90)
    assert d <= 1.0, (r["row_angle_deg"], angle)
    assert r["pitch_mm"] == pytest.approx(pitch, rel=0.03)
    outer = h + max(2, int(0.12 * h * PX_MM)) / PX_MM  # ring height + stroke thickness
    assert r["component_height_mm_median"] == pytest.approx(outer, rel=0.05)
    assert r["band_fwhm_mm_median"] == pytest.approx(0.9 * outer, rel=0.1)  # 5-95 % mass extent
    assert r["pitch_cv"] is not None and r["pitch_cv"] < 0.05


def test_pitch_cv_sees_irregular_rows():
    r = LS.measure_tile(fake_text(5.0, 2.5, 0.0, size_mm=30.0, jitter_mm=1.0, seed=3), PX_MM)
    assert r["pitch_cv"] > 0.05


def test_decode_shard_roundtrip():
    import numcodecs
    rng = np.random.default_rng(0)
    shape, inner = (700, 1100), (512, 512)
    a = (rng.random(shape) > 0.97).astype(np.uint8) * 255
    gy, gx = math.ceil(shape[0] / 512), math.ceil(shape[1] / 512)
    pad = np.zeros((gy * 512, gx * 512), np.uint8)
    pad[: shape[0], : shape[1]] = a
    blosc = numcodecs.Blosc(cname="zstd", clevel=3, shuffle=numcodecs.Blosc.BITSHUFFLE)
    body, index = b"", []
    for i in range(gy):
        for j in range(gx):
            if i == 1 and j == 2:
                index.append((2 ** 64 - 1, 2 ** 64 - 1))  # empty inner chunk -> fill value
                pad[512:, 1024:] = 0
                continue
            c = blosc.encode(np.ascontiguousarray(pad[i * 512:(i + 1) * 512, j * 512:(j + 1) * 512]).tobytes())
            index.append((len(body), len(c)))
            body += c
    buf = body + np.asarray(index, dtype="<u8").tobytes() + b"\0\0\0\0"
    out = LS.decode_shard(buf, shape, inner)
    np.testing.assert_array_equal(out, pad[: shape[0], : shape[1]])


def test_aperiodic_tile_never_gives_negative_or_wrapped_pitch():
    # random blobs, and a single blob: no row period -> flagged, never a negative pitch
    rng = np.random.default_rng(5)
    n = int(20 * PX_MM)
    m = np.zeros((n, n), np.uint8)
    for _ in range(30):
        cv2.circle(m, (int(rng.uniform(0, n)), int(rng.uniform(0, n))), int(rng.uniform(5, 60)), 1, -1)
    for mask in (m, np.pad(np.ones((50, 50), np.uint8), ((900, n - 950), (900, n - 950)))):
        r = LS.measure_tile(mask, PX_MM)
        assert r["pitch_mm"] is None or r["pitch_mm"] > 0
        if r["pitch_mm"] is None:
            assert r["peak_at_lag_edge"] is True and r["n_rows"] == 0
