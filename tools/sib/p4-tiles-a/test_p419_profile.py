"""Unit tests for p419_profile on synthetic line patterns of known pitch and indent.

Provenance: Project HERCULES | owner the owner | [id removed]

Run: python -m pytest tools/sib/p4-tiles-a/test_p419_profile.py  (or python this file)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import p419_profile as P  # noqa: E402

NB = P.NBINS


def synth(pitch_mm, height_mm, lefts_mm, width_mm=40.0, first_mm=6.0, noise=0.0, seed=0, fine=10):
    """Binned (0.5 mm) sums of a fine synthetic image: lines of Gaussian height profile."""
    n = NB * fine
    z = (np.arange(n) + 0.5) * P.BIN_MM / fine
    x = (np.arange(n) + 0.5) * P.BIN_MM / fine
    img = np.zeros((n, n))
    sig = height_mm / 2.3548
    k = 0
    c = first_mm
    while c < NB * P.BIN_MM - 2:
        L = lefts_mm[k % len(lefts_mm)]
        row = np.exp(-0.5 * ((z - c) / sig) ** 2)[:, None]
        col = ((x >= L) & (x < L + width_mm)).astype(float)[None, :]
        img += 100 * row * col
        c += pitch_mm
        k += 1
    img += np.random.default_rng(seed).normal(0, noise, img.shape) if noise else 0
    img = np.clip(img, 0, None)
    S = img.reshape(NB, fine, NB, fine).sum((1, 3))
    return S, k


def test_pitch_recovered():
    for p in (3.0, 4.5, 6.0, 9.0):
        S, _ = synth(p, 1.5, [5.0])
        g = P.analyse_group(S)
        assert abs(g["p_mm"] - p) < 0.25, (p, g["p_mm"])


def test_line_count():
    for p, h in ((5.0, 1.2), (4.0, 1.0), (8.0, 2.4)):
        S, k = synth(p, h, [5.0])
        g = P.analyse_group(S)
        assert g["n_lines"] == k, (p, h, g["n_lines"], k)


def test_dense_profile_finds_no_lines():
    """Declared rule (median + 2 robust SD): a near-sinusoidal profile (FWHM 2 mm at 5 mm
    pitch) has no outlier peaks, so no lines are found. Documented limitation, not a bug."""
    g = P.analyse_group(synth(5.0, 2.0, [5.0])[0])
    assert g["n_lines"] == 0 and g["s_mm"] is None


def test_fwhm_tracks_height():
    g1 = P.analyse_group(synth(8.0, 1.2, [5.0])[0])
    g2 = P.analyse_group(synth(8.0, 2.4, [5.0])[0])
    assert abs(g1["h_mm"] - 1.2) < 0.4, g1["h_mm"]
    assert abs(g2["h_mm"] - 2.4) < 0.4, g2["h_mm"]
    assert g2["h_mm"] / g1["h_mm"] > 1.6


def test_aligned_left_edge():
    g = P.analyse_group(synth(5.0, 1.2, [7.0])[0])
    assert g["s_mm"] < 0.3, g["s_mm"]
    assert all(abs(l["left_edge_mm"] - 7.25) <= 0.5 for l in g["lines"])


def test_indented_left_edge():
    lefts = [2.0, 12.0, 5.0, 9.0]
    g = P.analyse_group(synth(5.0, 1.2, lefts)[0])
    assert g["s_mm"] > 3.0, g["s_mm"]


def test_noise_robust():
    S, k = synth(5.0, 1.2, [5.0], noise=20.0, seed=3)
    g = P.analyse_group(S)
    assert abs(g["p_mm"] - 5.0) < 0.3 and abs(g["n_lines"] - k) <= 1


def test_decisions():
    body = P.analyse_group(synth(5.0, 1.2, [5.0])[0])
    body2 = P.analyse_group(synth(5.1, 1.2, [5.2])[0])
    big = P.analyse_group(synth(7.5, 2.4, [5.0])[0])
    indent = P.analyse_group(synth(5.0, 1.2, [2.0, 14.0, 6.0, 10.0])[0])
    assert P.decide(body2, body, body2)["verdict"] == "BODY-LIKE"
    assert P.decide(big, body, body2)["verdict"] == "TITLE-LIKE"
    assert P.decide(indent, body, body2)["verdict"] == "TITLE-LIKE"
    mid = P.analyse_group(synth(6.1, 1.2, [5.0])[0])  # r_p about 1.22: neither rule
    assert P.decide(mid, body, body2)["verdict"] == "INDETERMINATE"
    assert P.decide(body, body, big)["verdict"] == "INVALID"


def test_binned_sums_matches_direct():
    class R:
        def __init__(self, a):
            self.a = a

        def read(self, y0, y1, x0, x1):
            return self.a[y0:y1, x0:x1]
    a = np.random.default_rng(1).integers(0, 256, (1250, 1300)).astype(np.uint8)
    S, ze, xe = P.binned_sums(R(a), 10, 1210, 50, 1250, nz=12, nx=12, chunk_bins=5)
    for i in range(12):
        for j in range(12):
            assert S[i, j] == int(a[ze[i]:ze[i + 1], xe[j]:xe[j + 1]].astype(np.int64).sum())


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
            print("ok", name)
