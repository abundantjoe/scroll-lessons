# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for method C6 (9 um -> ~2.4 um rescan registration). Synthetic data only."""
import itertools
import json

import numpy as np
import pytest
from scipy import ndimage as ndi

from hercules.registration import c6
from hercules.registration import synthetic as S

F_TRUE = 9.366 / 2.403  # 3.8976, from metadata
Z0 = 4.0
B_TRUE = (7.3, -4.6, 2.2)
TILT = (0.26, 0.12, 0.0)  # deg about x, y, z
FLIP = (1, -1, 1)  # y flipped by the remount
BLOCK = (16, 40, 40)  # small test blocks; production default is (48, 256, 256)
COARSE = (24, 80, 80)
P_FIT = [(x, y, z) for x in (32, 72) for y in (32, 72) for z in (14, 27)]
P_CHECK = [(52, 52, 20), (24, 82, 17), (82, 24, 25), (40, 60, 28), (70, 44, 13), (60, 80, 24)]


@pytest.fixture(scope="module")
def pair():
    return S.make_pair(shape9=(40, 104, 104), F=F_TRUE, z0=Z0, b=B_TRUE, tilt_deg=TILT,
                       Pm=np.mean(P_FIT, axis=0), flip_signs=FLIP, seed=0)


@pytest.fixture(scope="module")
def readers(pair):
    return c6.ArrayReader(pair["vol9"]), c6.ArrayReader(pair["volr"])


@pytest.fixture(scope="module")
def fit(readers):
    r9, rr = readers
    F = c6.scale_factor(9.366, 2.403)
    return c6.register(r9, rr, F, Z0, P_FIT, P_CHECK, block=BLOCK, coarse_block=COARSE)


# ---------------------------------------------------------------- (a) recovery
def test_register_recovers_flip_translation_and_passes_check(fit, pair):
    json.dumps(fit)  # JSON-serialisable
    truth = pair["truth"]
    assert fit["flips"] == list(FLIP)
    assert fit["orientation"]["perm_xyz"] == [0, 1, 2]
    assert fit["coarse"]["ncc_margin"] > 0.3
    assert fit["F"] == pytest.approx(3.8976, abs=1e-4)
    np.testing.assert_allclose(fit["Pm"], np.mean(P_FIT, axis=0))
    assert np.max(np.abs(np.array(fit["b"]) - B_TRUE)) <= 0.3
    assert np.max(np.abs(np.array(fit["M"]) - truth["M"])) <= 3e-3  # tilts ~4.5e-3 rad
    assert fit["fit"]["residual_rms"] <= 0.5
    assert fit["check"]["n_ok"] == len(P_CHECK)
    assert fit["median_r"] >= 0.85
    assert fit["rms"] <= 0.5
    assert fit["bars"]["pass"]
    assert len(fit["check"]["patches"]) == len(P_CHECK)
    assert all(len(p["residual"]) == 3 for p in fit["check"]["patches"])


def test_register_absorbs_z0_error_into_bz(readers, fit):
    r9, rr = readers
    alt = c6.register(r9, rr, fit["F"], Z0 + 3.0, P_FIT, P_CHECK, block=BLOCK,
                      coarse_block=COARSE)
    assert alt["flips"] == list(FLIP)
    assert alt["b"][2] - alt["z0"] == pytest.approx(B_TRUE[2] - Z0, abs=0.3)
    p = np.array(P_CHECK, float)
    assert np.max(np.abs(c6.map_9_to_r(p, alt) - c6.map_9_to_r(p, fit))) < 0.3 * fit["F"]
    assert alt["median_r"] >= 0.85


# ---------------------------------------------------------------- (b) control
def test_half_sheet_spacing_control_has_much_lower_ncc(readers, fit, pair):
    r9, rr = readers
    half = pair["sheet_spacing"] / 2.0  # sheets are stacked along y
    ctrl = c6.evaluate_patches(r9, rr, fit, P_CHECK, block=BLOCK, offset=(0.0, half, 0.0))
    base = c6.evaluate_patches(r9, rr, fit, P_CHECK, block=BLOCK)
    assert base["median_r"] == pytest.approx(fit["median_r"], abs=1e-6)
    assert ctrl["median_r"] < 0.3
    assert ctrl["median_r"] < base["median_r"] - 0.5
    assert ctrl["rms"] > 3.0  # phase correlation sees the displacement


# ---------------------------------------------------------------- (c) round trip
def test_round_trip_fitted(fit, pair):
    rng = np.random.default_rng(5)
    p = rng.uniform([0, 0, 0], [103, 103, 39], (500, 3))
    q = c6.map_9_to_r(p, fit)
    back = c6.map_r_to_9(q, fit)
    assert np.max(np.abs(back - p)) < 0.05
    # raw frame really is the stored (y-flipped) rescan
    qc = c6.map_9_to_r(p, fit, frame="canonical")
    ny = pair["volr"].shape[1]
    np.testing.assert_allclose(q[:, 1], ny - 1 - qc[:, 1])
    np.testing.assert_allclose(q[:, [0, 2]], qc[:, [0, 2]])


def test_round_trip_permuted_and_tilted():
    ori = c6.Orientation((0, 2, 1), (True, False, True))
    M = S.rotation_xyz(1.5, -0.8, 2.0) * 1.01 - np.eye(3)
    tr = c6.C6Transform(9.362 / 2.399, 11.0, M, (-3.1, 5.5, 0.7), (60.0, 40.0, 30.0), ori,
                        (900, 700, 800))
    rng = np.random.default_rng(6)
    p = rng.uniform(-20, 200, (300, 3))
    back = c6.map_r_to_9(c6.map_9_to_r(p, tr), tr)
    assert np.max(np.abs(back - p)) < 0.05


# ---------------------------------------------------------------- (d) phase correlation
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_phase_correlation_subvoxel(seed):
    rng = np.random.default_rng(seed)
    big = ndi.gaussian_filter(rng.standard_normal((64, 112, 112)), 1.2)
    d = rng.uniform(-3.5, 3.5, 3)
    moved = ndi.shift(big, d, order=5, mode="wrap")
    sl = (slice(16, 48), slice(24, 88), slice(24, 88))
    a = big[sl] + 0.1 * rng.standard_normal(big[sl].shape)
    b = moved[sl] + 0.1 * rng.standard_normal(big[sl].shape)
    s, peak = c6.phase_correlate_3d(a, b, upsample=10)
    assert np.max(np.abs(s - d)) <= 0.15
    assert peak > 0.2
    s2, _ = c6.phase_correlate_3d(b, a)  # antisymmetric
    assert np.max(np.abs(s2 + d)) <= 0.15


def test_phase_correlation_integer_and_zero():
    rng = np.random.default_rng(9)
    a = ndi.gaussian_filter(rng.standard_normal((24, 48, 48)), 1.0)
    s, peak = c6.phase_correlate_3d(a, a)
    assert np.max(np.abs(s)) < 1e-6 and peak > 0.9
    b = np.roll(a, (2, -3, 5), axis=(0, 1, 2))
    s, _ = c6.phase_correlate_3d(a, b)
    np.testing.assert_allclose(s, (2, -3, 5), atol=0.05)


# ---------------------------------------------------------------- building blocks
def test_scale_factor_from_metadata():
    assert c6.scale_factor(9.366, 2.403) == pytest.approx(3.8976, abs=1e-4)
    assert c6.scale_factor(9.362, 2.403) == pytest.approx(3.89596, abs=1e-5)
    assert c6.scale_factor(9.362, 2.399) == pytest.approx(3.90246, abs=1e-5)
    with pytest.raises(ValueError):
        c6.scale_factor(2.403, 9.366)


def _brute_weights(n_in, F, o, n_out):
    W = np.zeros((n_out, n_in))
    for i in range(n_out):
        a, b = o + F * i - F / 2, o + F * i + F / 2
        for k in range(n_in):
            W[i, k] = max(0.0, min(k + 0.5, b) - max(k - 0.5, a)) / F
    return W


def test_downsample_area_is_exact_box_mean():
    rng = np.random.default_rng(2)
    F = 3.8976
    x = rng.random((30, 44, 50)).astype(np.float32)
    o, shp = (1.6, 2.3, 1.9), (6, 10, 11)
    d = c6.downsample_area(x, F, o, shp)
    Ws = [_brute_weights(n, F, oo, m) for n, oo, m in zip(x.shape, o, shp)]
    ref = np.einsum("az,by,cx,zyx->abc", *Ws, x.astype(float))
    np.testing.assert_allclose(d, ref, atol=1e-5)
    # independent summed-area-table implementation (used by the synthetic generator)
    idx = np.stack(np.meshgrid(*[np.arange(m) for m in shp], indexing="ij"), -1)
    sat = S.box_mean_at(x, np.asarray(o) + F * idx, F)
    np.testing.assert_allclose(d, sat, atol=1e-5)
    # constants preserved, uint16 accepted, default grid
    np.testing.assert_allclose(c6.downsample_area(np.full((40, 40, 40), 7.0), F), 7.0)
    u = (x * 1000).astype(np.uint16)
    np.testing.assert_allclose(c6.downsample_area(u, F, o, shp),
                               c6.downsample_area(u.astype(np.float32), F, o, shp), rtol=1e-5)
    assert c6.downsample_area(x, F).shape == tuple(int(n // F) for n in x.shape)


def test_downsample_area_nan_and_out_of_block():
    F = 3.9
    x = np.ones((20, 20, 20), np.float32)
    x[10, 10, 10] = np.nan
    d = c6.downsample_area(x, F, (0.0, 0.0, 0.0), (5, 5, 5))
    assert np.isnan(d[0]).all() and np.isnan(d[:, 0]).all()  # footprint leaves the block
    k = int(round(10 / F))
    assert np.isnan(d[k, k, k])  # touches the NaN
    n_touch = sum(abs(i * F - 10) < F / 2 + 0.5 for i in range(1, 5))  # footprints per axis
    assert np.isnan(d[1:, 1:, 1:]).sum() == n_touch ** 3
    np.testing.assert_allclose(d[1:, 1:, 1:][np.isfinite(d[1:, 1:, 1:])], 1.0, atol=1e-6)


def test_ncc_valid_voxels():
    rng = np.random.default_rng(3)
    a = rng.standard_normal((8, 9, 10))
    assert c6.ncc(a, 2 * a + 1) == pytest.approx(1.0)
    assert c6.ncc(a, -a) == pytest.approx(-1.0)
    b = a.copy()
    b[0] = np.nan
    b[1] = 1e6  # excluded by mask
    m = np.ones(a.shape, bool)
    m[1] = False
    assert c6.ncc(a, b, mask=m) == pytest.approx(1.0)
    assert np.isnan(c6.ncc(a, np.full(a.shape, np.nan)))


def test_fit_affine_exact_and_rms():
    rng = np.random.default_rng(4)
    P = rng.uniform(0, 200, (12, 3))
    M = np.array([[1e-3, 4e-3, -2e-3], [-4e-3, -5e-4, 3e-3], [2e-3, -3e-3, 2e-4]])
    Pm = P.mean(0)
    T = (P - Pm) @ M.T + np.array([7.3, -4.6, 2.2])
    out = c6.fit_affine(P, T)
    np.testing.assert_allclose(out["M"], M, atol=1e-8)
    np.testing.assert_allclose(out["b"], [7.3, -4.6, 2.2], atol=1e-8)
    assert out["rms"] < 1e-6
    noise = rng.normal(0, 0.2, T.shape)
    out = c6.fit_affine(P, T + noise)
    assert 0.05 < out["rms"] < 0.4
    # coplanar layout (all z equal) stays finite; fewer than 4 -> translation only
    P2 = P.copy()
    P2[:, 2] = 30.0
    assert np.isfinite(c6.fit_affine(P2, T)["M"]).all()
    t3 = c6.fit_affine(P[:3], T[:3])
    np.testing.assert_allclose(t3["M"], 0.0)


def test_oriented_reader_all_48_orientations():
    rng = np.random.default_rng(7)
    raw = rng.random((12, 15, 18)).astype(np.float32)
    rr = c6.ArrayReader(raw)
    assert len(c6.candidate_orientations("flips")) == 8
    assert len(c6.candidate_orientations("all")) == 48
    for ori in c6.candidate_orientations("all"):
        R = c6.OrientedReader(rr, raw.shape, ori)
        can = ori.orient_block(raw)
        assert R.shape == can.shape
        lo = np.array([1, 2, 3])
        hi = np.array(can.shape) - 1
        np.testing.assert_array_equal(R(lo, hi), can[1:hi[0], 2:hi[1], 3:hi[2]])
        # point maps agree with the array reorientation
        q = np.array([[2, 3, 4], [5, 1, 7]])
        r = ori.can_to_raw(q, raw.shape).astype(int)
        np.testing.assert_array_equal(raw[tuple(r.T)], can[tuple(q.T)])
        np.testing.assert_allclose(ori.raw_to_can(r, raw.shape), q)
        G = ori.G_xyz()
        assert sorted(np.abs(G).sum(0)) == [1, 1, 1] and abs(round(np.linalg.det(G))) == 1


def test_array_reader_pads_with_nan():
    x = np.arange(4 * 5 * 6, dtype=np.uint16).reshape(4, 5, 6)
    r = c6.ArrayReader(x)
    inside = r((0, 1, 2), (3, 4, 5))
    np.testing.assert_array_equal(inside, x[0:3, 1:4, 2:5])
    out = r((-1, 3, 4), (2, 7, 8))
    assert out.dtype == np.float32 and out.shape == (3, 4, 4)
    assert np.isnan(out[0]).all() and np.isnan(out[:, 2:]).all()
    np.testing.assert_array_equal(out[1:, :2, :2], x[0:2, 3:5, 4:6])


def test_sampler_matches_generator_at_truth(readers, pair):
    """Rescan resampled under the true transform reproduces the 9 um volume."""
    r9, rr = readers
    truth = pair["truth"]
    tf = S.truth_fit(truth)
    tr = c6.C6Transform.from_fit(tf)
    rc = c6.OrientedReader(rr, rr.shape, tr.orientation)
    for c in P_CHECK[:3]:
        row = c6._measure_patch(r9, rc, tr, c, BLOCK, 10, True)
        assert row["r"] > 0.95
        assert np.max(np.abs(row["delta"])) < 0.15


def test_coarse_test_with_xy_permutations_picks_true_orientation(readers):
    r9, rr = readers
    rows = c6._coarse_orientation(r9, rr, rr.shape, F_TRUE, Z0,
                                  c6.candidate_orientations("flips+xy"), COARSE, 2, None, 10)
    assert len(rows) == 16
    best = max(rows, key=lambda r: r["ncc"])
    assert best["orientation"].perm_xyz() == [0, 1, 2]
    assert best["orientation"].flip_signs_xyz() == list(FLIP)
    others = sorted(r["ncc"] for r in rows if r is not best)
    assert best["ncc"] - others[-1] > 0.3
    np.testing.assert_allclose(best["b0"], B_TRUE, atol=1.0)
