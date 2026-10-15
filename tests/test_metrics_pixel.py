"""Provenance: Project HERCULES | owner the owner | [id removed]"""
import cv2
import numpy as np

from hercules.metrics import pixel as P


def test_auc_known_values():
    assert P.auc([1, 2, 3, 4], [0, 0, 1, 1]) == 1.0
    assert P.auc([4, 3, 2, 1], [0, 0, 1, 1]) == 0.0
    assert P.auc([1, 1, 1, 1], [0, 1, 0, 1]) == 0.5
    assert P.auc([1, 2, 3, 9], [0, 0, 1, 2]) == 1.0  # label 2 ignored


def test_auc_random_near_half():
    rng = np.random.default_rng(0)
    a = P.auc(rng.random(20000), rng.integers(0, 2, 20000))
    assert abs(a - 0.5) < 0.02


def test_sigma_eq_recovers_blur():
    rng = np.random.default_rng(1)
    ref = np.zeros((400, 400))
    ref[rng.integers(0, 400, 300), rng.integers(0, 400, 300)] = 1.0
    ref = cv2.GaussianBlur(ref, (0, 0), 2.0)
    ppm = 106.77
    true_mm = 0.15
    model = cv2.GaussianBlur(ref, (0, 0), true_mm * ppm) + rng.normal(0, 1e-4, ref.shape)
    s, r, _ = P.sigma_eq(model, ref, ppm)
    assert abs(s - true_mm) <= 0.025 and r > 0.95


def test_blob_f180():
    m = np.zeros((100, 100), np.uint8)
    m[10:20, 10:20] = 200  # 100 px
    m[50:55, 50:55] = 200  # 25 px
    m[80, 80] = 200        # 1 px
    # area 4.717 cm2 -> K = 10: all three blobs
    assert P.blob_f180(m, 4.717) == 126 / 10000
    # area tiny -> K = 1: largest only
    assert P.blob_f180(m, 0.1) == 100 / 10000
    assert P.blob_f180(np.zeros((5, 5), np.uint8), 1.0) == 0.0


def test_pearson():
    x = np.arange(100.0)
    assert abs(P.pearson(x, 2 * x + 1) - 1) < 1e-12
    assert abs(P.pearson(x, -x) + 1) < 1e-12
