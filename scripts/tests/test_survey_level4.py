import os, sys, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import survey_level4 as S


def disk(n=400, r=150):
    yy, xx = np.mgrid[:n, :n]
    return np.hypot(yy - n / 2, xx - n / 2) <= r


def test_mask_erosion():
    d = disk()
    sl = (d * 100).astype(np.uint8)
    m = S.scroll_mask(sl)
    assert m.sum() < d.sum() and not m[~d].any()
    assert S.scroll_mask(sl, erode=0).sum() == d.sum()
    # erosion by 3 px removes at most the 3-px rim
    rim = disk(r=147)
    assert m[rim].all()


def test_rings_high_uniform_low():
    n = 400; d = disk(n)
    yy, xx = np.mgrid[:n, :n]; rr = np.hypot(yy - n / 2, xx - n / 2)
    rings = np.where(d, np.where((rr // 4) % 2 == 0, 220, 20), 0).astype(np.uint8)
    uniform = (d * 120).astype(np.uint8)
    lc_r = S.layer_contrast(rings, S.scroll_mask(rings))
    lc_u = S.layer_contrast(uniform, S.scroll_mask(uniform))
    assert lc_r > 0.5 and lc_u < 1e-6
    assert S.air_gap_fraction(uniform, S.scroll_mask(uniform)) == 0.0
    ag = S.air_gap_fraction(rings, S.scroll_mask(rings))
    assert 0.3 < ag < 0.7


def test_area_and_bar():
    m = np.ones((10, 10), bool)
    # 100 px at 16*9.362 um = 149.79 um per px -> 100*(0.014979 cm)^2
    assert abs(S.area_cm2(m, 9.362) - 100 * (16 * 9.362 / 1e4) ** 2) < 1e-12
    assert round(10000 / (16 * 9.362)) == 67 and round(10000 / (16 * 8.64)) == 72


def test_check_zarray():
    good = {"zarr_format": 2, "dtype": "|u1", "compressor": None, "chunks": [128, 128, 128],
            "dimension_separator": "/", "order": "C", "filters": None}
    S.check_zarray(good)
    import pytest
    for k, v in [("dtype", "<u2"), ("compressor", {"id": "blosc"}), ("chunks", [192, 192, 192])]:
        with pytest.raises(SystemExit):
            S.check_zarray({**good, k: v})


def test_eligible_list():
    assert len(S.ELIGIBLE) == 23 and set(S.SECTION6) == {s for s, _ in S.ELIGIBLE}
    assert sum(p == 8.64 for p in S.PROMPT_PITCH.values()) == 12
