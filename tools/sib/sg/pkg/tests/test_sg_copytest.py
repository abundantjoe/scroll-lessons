# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for the DECL-SG 7 copy test (hercules.sg.copytest), with rulings B6 (|NCC|)
and B7 (n_eff >= 30 floor, copy-test null).  Synthetic arrays only."""

import time

import cv2
import numpy as np
import pytest

from hercules.sg import constants as C
from hercules.sg import copytest as T


def smooth(rng, shape, sigma=1.5):
    a = rng.random(shape)
    return cv2.GaussianBlur(a, (0, 0), sigma)


def test_rotation_steps_are_24_of_15_degrees():
    assert C.SG7_ROTATIONS_DEG == tuple(range(0, 360, 15)) and len(C.SG7_ROTATIONS_DEG) == 24


@pytest.mark.parametrize("angle", [0, 15, 90, 225, 345])
def test_fft_ncc_equals_bruteforce(angle):
    rng = np.random.default_rng(angle)
    patches = rng.random((2, 37, 41))
    crop = rng.random((19, 23))
    tmpl, mask, ss = T.templates_for(crop, 19, (angle,))
    fast = T.masked_ncc_maps(patches, tmpl, mask, ss)
    for i in range(2):
        np.testing.assert_allclose(fast[i, 0], T.ncc_bruteforce(patches[i], tmpl[0], mask), atol=1e-10)


def test_exact_copy_at_zero_degrees_is_ncc_one():
    rng = np.random.default_rng(1)
    patch = smooth(rng, (120, 120))
    crop = patch[40:81, 30:71].copy()
    r = T.copy_test([crop], [smooth(rng, (120, 120)), patch])
    assert r["status"] == "FAIL" and r["reason"] == "copy_found"
    p = r["per_letter"][0]
    assert p["max_abs_ncc"] == pytest.approx(1.0, abs=1e-9) and p["signed_ncc_at_max"] == pytest.approx(1.0, abs=1e-9)
    assert p["patch"] == 1 and p["angle_deg"] == 0 and p["yx"] == [40, 30] and p["n_eff"] >= C.SG7_NEFF_MIN


@pytest.mark.parametrize("k", [1, 3, 7, 12, 23])
def test_rotated_copy_found_at_every_step(k):
    rng = np.random.default_rng(10 + k)
    patch = smooth(rng, (150, 150))
    crop = T.rotate_crop(patch[45:106, 45:106], -15 * k)  # the letter was a rotated label patch
    r = T.copy_test([crop], [patch])
    p = r["per_letter"][0]
    assert r["status"] == "FAIL" and p["max_abs_ncc"] >= 0.9 and p["angle_deg"] == 15 * k


def test_unrelated_patches_pass():
    rng = np.random.default_rng(2)
    crops = [smooth(rng, (41, 35)) for _ in range(3)]
    patches = [smooth(rng, (64, 64)) for _ in range(40)]
    r = T.copy_test(crops, patches)
    assert r["status"] == "PASS" and r["max_abs_ncc"] < C.SG7_NCC_MAX and r["n_rotations"] == 24
    assert r["n_eff_min"] >= C.SG7_NEFF_MIN and r["neff_floor_enforced"] is True


def test_copy_flag_matches_threshold_inclusive():
    rng = np.random.default_rng(3)
    patch = smooth(rng, (60, 60))
    crop = patch[10:51, 10:51].copy()
    p = T.copy_test([crop], [patch])["per_letter"][0]
    assert p["copy"] is True and (p["max_abs_ncc"] >= C.SG7_NCC_MAX) == p["copy"]


def test_B6_inverted_copy_is_a_copy():
    # ruling B6: |NCC| >= 0.8; an intensity-inverted copy (NCC -1) is still a copy
    rng = np.random.default_rng(4)
    patch = smooth(rng, (80, 80))
    crop = 1.0 - patch[20:61, 20:61]
    r = T.copy_test([crop], [patch])
    p = r["per_letter"][0]
    assert r["status"] == "FAIL" and r["reason"] == "copy_found"
    assert p["signed_ncc_at_max"] == pytest.approx(-1.0, abs=1e-9) and r["min_signed_ncc"] == pytest.approx(-1.0, abs=1e-9)
    assert r["max_signed_ncc"] < 0.8  # the signed maximum alone would have missed it


def test_patch_smaller_than_crop_uses_centre_square():
    rng = np.random.default_rng(5)
    big = smooth(rng, (90, 90))
    crop = big[10:81, 10:81].copy()  # 71 x 71 letter crop
    patch = big[25:66, 25:66].copy()  # 41 x 41 label patch = the crop's centre
    r = T.copy_test([crop], [patch])
    p = r["per_letter"][0]
    assert p["d"] == 41 and p["max_abs_ncc"] == pytest.approx(1.0, abs=1e-9) and r["status"] == "FAIL"


def test_flat_crop_is_not_evaluable_and_fails():
    r = T.copy_test([np.ones((30, 30))], [np.random.default_rng(0).random((50, 50))])
    assert r["status"] == "FAIL" and r["reason"] == "not_evaluable"


def test_B7_crop_below_neff_floor_fails_closed():
    # sigma 4 smoothing on a 41 px crop: n_eff well below 30 -> not evaluable -> FAIL, even
    # though the patches are unrelated
    rng = np.random.default_rng(12)
    crop = smooth(rng, (41, 41), 4.0)
    r = T.copy_test([crop], [smooth(rng, (64, 64), 4.0) for _ in range(3)])
    assert r["status"] == "FAIL" and r["reason"] == "not_evaluable" and r["copies"] == []
    ne = r["per_letter"][0]["not_evaluable"][0]
    assert ne["reason"] == "n_eff_below_floor" and ne["n_eff"] < C.SG7_NEFF_MIN
    # the synthetic null may bypass the floor to measure the statistic itself
    assert T.copy_test([crop], [smooth(rng, (64, 64), 4.0)], enforce_neff=False)["not_evaluable"] == []


def test_B7_floor_applies_per_patch_size_group():
    # a large patch group gives a large disc (n_eff ok); a small group gives a small disc
    rng = np.random.default_rng(13)
    crop = smooth(rng, (81, 81), 1.5)
    big = [smooth(rng, (100, 100), 1.5)]
    small = [smooth(rng, (20, 20), 1.5)]
    assert T.copy_test([crop], big)["status"] == "PASS"
    r = T.copy_test([crop], big + small)
    assert r["status"] == "FAIL" and r["per_letter"][0]["not_evaluable"][0]["patch_shape"] == [20, 20]


def test_B7_copy_test_null_check():
    rng = np.random.default_rng(14)
    patches = [smooth(rng, (64, 64)) for _ in range(5)]
    null = {f"t{i:02d}": [smooth(rng, (41, 41)) for _ in range(2)] for i in range(40)}
    r = T.copy_test_null_check(null, patches)
    assert r["status"] == "INFORMATIVE" and r["false_flags"] == 0 and r["n_null_tiles"] == 40
    null["t00"] = [patches[2][10:51, 10:51].copy()]  # a null crop that happens to copy a label
    r = T.copy_test_null_check(null, patches)
    assert r["status"] == "UNINFORMATIVE" and r["false_flags"] == 1
    few = {k: v for k, v in list(null.items())[1:]}
    assert T.copy_test_null_check(few, patches)["status"] == "UNINFORMATIVE"  # 39 tiles


def test_flat_patch_regions_give_zero_not_spurious():
    rng = np.random.default_rng(6)
    patch = np.zeros((80, 80))
    patch[:, 60:] = smooth(rng, (80, 20))
    r = T.copy_test([smooth(rng, (31, 31), 1.0)], [patch])
    assert r["max_abs_ncc"] < 0.8 and np.isfinite(r["max_abs_ncc"])


def test_binary_label_patch_against_probability_crop():
    rng = np.random.default_rng(7)
    label = (smooth(rng, (140, 140), 1.5) > 0.5).astype(float)
    crop = cv2.GaussianBlur(label[30:101, 30:101], (0, 0), 0.7) * 0.6 + 0.2  # ink map of the same strokes
    r = T.copy_test([crop], [label])
    assert r["status"] == "FAIL" and r["reason"] == "copy_found" and r["max_abs_ncc"] >= 0.8


def test_empty_inputs_fail():
    assert T.copy_test([], [np.zeros((10, 10))])["status"] == "FAIL"
    assert T.copy_test([np.zeros((10, 10))], [])["status"] == "FAIL"
    with pytest.raises(ValueError):
        T.copy_test([np.full((20, 20), np.nan)], [np.zeros((30, 30))])


def test_crop_boxes():
    img = np.arange(100.0).reshape(10, 10)
    c = T.crop_boxes(img, [[2, 3, 5, 7]])[0]
    assert c.shape == (4, 3) and c[0, 0] == 32
    assert T.crop_boxes(img, [[0, 0, 2, 2]], margin_px=5)[0].shape == (7, 7)


def test_efficiency_budget():
    # 21 letters x 24 rotations against 300 label patches of 64 x 64 on CPU
    rng = np.random.default_rng(9)
    crops = [smooth(rng, (48, 40), 1.0) for _ in range(21)]
    patches = [smooth(rng, (64, 64), 1.0) for _ in range(300)]
    t = time.perf_counter()
    r = T.copy_test(crops, patches)
    dt = time.perf_counter() - t
    assert r["n_letters"] == 21 and r["n_rotations"] == 24 and np.isfinite(r["max_abs_ncc"])
    assert (r["status"] == "PASS") == (r["max_abs_ncc"] < C.SG7_NCC_MAX)
    assert dt < 120.0, dt


def test_known_limitation_low_neff_fields_cross_bar_by_chance():
    # Recorded property (copytest_null.json): with strongly smoothed fields and a small disc
    # (n_eff well below 30), unrelated crops reach |NCC| >= 0.8 by chance.  This is why the
    # ruling-B7 floor exists; with the floor enforced these crops are not evaluable.
    rng = np.random.default_rng(8)
    crops = [smooth(rng, (48, 40), 3.0) for _ in range(21)]
    patches = [smooth(rng, (64, 64), 3.0) for _ in range(300)]
    r = T.copy_test(crops, patches, enforce_neff=False)
    assert r["max_abs_ncc"] >= C.SG7_NCC_MAX
    assert r["n_eff_min"] < C.SG7_NEFF_MIN


@pytest.mark.parametrize("sigma", [1.0, 2.0])
def test_coherence_area_matches_gaussian_theory(sigma):
    # smoothed white noise: autocorrelation exp(-r^2 / (4 sigma^2)) -> half-max area 4 ln2 pi sigma^2
    rng = np.random.default_rng(int(sigma))
    a = cv2.GaussianBlur(rng.standard_normal((256, 256)), (0, 0), sigma)
    assert T.coherence_area_px(a) == pytest.approx(4 * np.log(2) * np.pi * sigma ** 2, rel=0.15)
