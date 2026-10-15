"""Provenance: Project HERCULES | owner the owner | [id removed]"""
import io
import random

import numpy as np
from PIL import Image

from hercules.display import builder as B


def test_linear_window_is_linear_and_monotone():
    rng = np.random.default_rng(0)
    img = rng.normal(100, 20, (200, 200))
    u8, (lo, hi) = B.linear_window_ct(img)
    inside = (img > lo) & (img < hi)
    expected = np.rint((img[inside] - lo) / (hi - lo) * 255)
    assert np.max(np.abs(u8[inside].astype(float) - expected)) <= 1
    assert (u8[img <= lo] == 0).all() and (u8[img >= hi] == 255).all()


def test_model_map_raw():
    p = np.linspace(0, 1, 256).reshape(16, 16)
    u8 = B.model_map_u8(p)
    assert u8.min() == 0 and u8.max() == 255
    assert B.model_map_u8(u8) is u8


def test_area_downscale_is_block_mean():
    a = np.arange(16, dtype=np.uint8).reshape(4, 4) * 10
    d = B.area_downscale(a, 0.5)
    exp = a.reshape(2, 2, 2, 2).mean(axis=(1, 3))
    assert np.max(np.abs(d.astype(float) - exp)) <= 0.5


def test_raw_slab_means_indices():
    stack = np.stack([np.full((3, 3), i, float) for i in range(31)])
    f, b = B.raw_slab_means(stack)
    assert f[0, 0] == np.mean([16, 17, 18, 19, 20]) and b[0, 0] == np.mean([10, 11, 12, 13, 14])


def test_png_has_no_text_chunks():
    data = B.png_bytes(np.zeros((8, 8), np.uint8))
    im = Image.open(io.BytesIO(data))
    assert im.info == {} or set(im.info) <= {"dpi"} and not im.text


def test_layouts_cover_window():
    ppc = B.px_per_cm(9.366)
    n = int(round(2 * ppc))
    for layout in ("D2", "D1Q", "D1S"):
        tiles = B.tile_origins(n, n, 9.366, layout)
        cov = np.zeros((n, n), bool)
        for y, x, h, w in tiles:
            cov[y:y + h, x:x + w] = True
        assert cov.all(), layout
    assert len(B.tile_origins(n, n, 9.366, "D1Q")) == 9


def test_items_key_and_randomisation():
    t = np.full((2136, 2136), 200, np.uint8)
    b = np.full((2136, 2136), 50, np.uint8)
    items = B.build_items(t, b, "W", 300, 2315, 9.366, "D2", rng=random.Random(1))
    assert len(items) == 1
    k = items[0]["key"]
    left = np.asarray(Image.open(io.BytesIO(items[0]["left_png"])))
    assert left.shape == (1068, 1068)
    assert (left.mean() > 100) == (k["side_order"]["left"] == "text")
    assert k["scale"] == 2.0 and abs(k["px_per_mm_image"] - 53.38) < 0.05
    sides = set()
    for s in range(20):
        sides.add(B.build_items(t, b, "W", 0, 0, 9.366, "D2", rng=random.Random(s))[0]["key"]["side_order"]["left"])
    assert sides == {"text", "nontext"}


def test_d1s_amended_and_size_cap():
    import pytest
    n = int(round(2 * B.px_per_cm(9.366)))
    tiles = B.tile_origins(n, n, 9.366, "D1S")
    assert len(tiles) == 15 and all(w <= 1068 and h <= 1068 for _, _, h, w in tiles)
    big = np.zeros((1200, 1200), np.uint8)
    with pytest.raises(ValueError):
        B.build_items(big, big, "W", 0, 0, 8.0, "D1Q", rng=random.Random(0))
