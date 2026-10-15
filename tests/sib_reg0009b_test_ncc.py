# Provenance: Project HERCULES | owner the owner | [id removed]
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'sib', 'reg0009b'))
from reg import tile_ncc, bandpass


def test_shift_sign_and_subpixel():
    rng = np.random.default_rng(0)
    import cv2
    base = cv2.GaussianBlur(rng.normal(size=(700, 700)).astype(np.float32), (0, 0), 2)
    d = (3.4, -2.25)  # A(x) = B(x - d)
    M = np.float32([[1, 0, -d[0]], [0, 1, -d[1]]])
    B = base
    A = cv2.warpAffine(base, np.float32([[1, 0, d[0]], [0, 1, d[1]]]), (700, 700), flags=cv2.INTER_CUBIC)
    v = np.ones_like(A, bool)
    dx, dy, pk, n0, interior = tile_ncc(bandpass(A, v), bandpass(B, v), 200, 200)
    assert interior and pk > 0.95
    assert abs(dx - d[0]) < 0.25 and abs(dy - d[1]) < 0.25, (dx, dy)
