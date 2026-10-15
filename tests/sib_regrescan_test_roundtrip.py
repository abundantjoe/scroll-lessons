# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task regrescan: unit tests of the 9 -> 2.4 -> 9 um round trip, pyramid level
conversions and the coarse NCC search. No network; the fitted affines are read
from logs/sib/regrescan/<scroll>/final_affine.json when present."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools" / "sib" / "regrescan"))

import regrescan as R  # noqa: E402
from hercules.registration import c6  # noqa: E402

F = 9.362 / 2.403
SCROLLS = ["PHerc1203", "PHerc0846A"]


def _synthetic_tr(seed=0, ori=c6.Orientation()):
    rng = np.random.default_rng(seed)
    return c6.C6Transform(F, 7936.0, rng.normal(0, 0.004, (3, 3)), rng.normal(0, 20, 3),
                          np.array([3400.0, 3400.0, 9800.0]), ori, (15137, 26493, 26493))


@pytest.mark.parametrize("k9,kr", [(4, 5), (1, 2), (0, 0), (2, 3)])
def test_level_transform_consistent(k9, kr):
    tr = _synthetic_tr()
    tk = R.level_transform(tr, k9, kr)
    rng = np.random.default_rng(1)
    p0 = rng.uniform(1000, 5000, (50, 3)) + np.array([0, 0, 7000.0])
    q0 = c6.map_9_to_r(p0, R.tr_json(tr), frame="canonical")
    s9, sr = 2 ** k9, 2 ** kr
    qk = c6.map_9_to_r((p0 - (s9 - 1) / 2) / s9, R.tr_json(tk), frame="canonical")
    assert np.abs(qk * sr + (sr - 1) / 2 - q0).max() < 1e-8
    back = R.level0_transform(tk, F, k9, kr, tr.raw_shape)
    assert np.allclose(back.b, tr.b) and np.allclose(back.Pm, tr.Pm) and back.z0 == tr.z0


@pytest.mark.parametrize("flip", [(False, False, False), (True, False, True)])
def test_roundtrip_synthetic_quantised(flip):
    """9 um -> rescan voxel (rounded to the nearest stored voxel) -> 9 um < 0.5 vox."""
    tr = _synthetic_tr(2, c6.Orientation((0, 1, 2), flip))
    rng = np.random.default_rng(3)
    p = rng.uniform(500, 6000, (2000, 3)) + np.array([0, 0, 7936.0])
    q = c6.map_9_to_r(p, R.tr_json(tr), frame="raw")
    assert np.abs(c6.map_r_to_9(q, R.tr_json(tr), frame="raw") - p).max() < 1e-6
    err = np.linalg.norm(c6.map_r_to_9(np.round(q), R.tr_json(tr), frame="raw") - p, axis=1)
    assert err.max() < 0.5


def test_ncc_map_matches_bruteforce():
    rng = np.random.default_rng(4)
    A = rng.normal(size=(12, 14, 13))
    T = A[3:8, 4:10, 2:9] + 0.1 * rng.normal(size=(5, 6, 7))
    m = R._ncc_map(A, T)
    assert m.shape == (8, 9, 7)
    for idx in [(0, 0, 0), (3, 4, 2), (7, 8, 6), (5, 1, 3)]:
        blk = A[idx[0]:idx[0] + 5, idx[1]:idx[1] + 6, idx[2]:idx[2] + 7]
        assert abs(m[idx] - c6.ncc(blk, T)) < 1e-9
    assert np.unravel_index(np.argmax(m), m.shape) == (3, 4, 2)


def test_search_recovers_placement_outside_volume():
    rng = np.random.default_rng(5)
    A = np.zeros((20, 30, 30), np.float32)
    A[4:16, 5:25, 5:25] = rng.normal(size=(12, 20, 20))
    T = R._crop(A, [5, -3, 2], (10, 26, 26))  # template partly outside A (zeros = air)
    T = T + 0.01 * rng.normal(size=T.shape).astype(np.float32)
    v, pos, _ = R._search(A, T, [-3, -8, -8], [10, 8, 8])
    assert tuple(pos) == (5, -3, 2) and v > 0.99


def test_local_pitch_on_sheets():
    z, y, x = np.meshgrid(np.arange(48), np.arange(64), np.arange(64), indexing="ij")
    d = 0.8 * x + 0.6 * y  # sheets normal to (0.8, 0.6, 0), period 12 vox
    A = np.cos(2 * np.pi * d / 12.0)
    rng = np.random.default_rng(7)
    A = A + 0.3 * rng.normal(size=A.shape)
    pitch, k, info = R.local_pitch(A)
    assert info["method"] == "autocorrelation_first_max"
    assert abs(pitch - 12.0) < 1.0
    assert abs(abs(k @ np.array([0.8, 0.6, 0.0])) - 1) < 0.05


def _final(scroll):
    f = REPO / "logs" / "sib" / "regrescan" / scroll / "final_affine.json"
    if not f.exists():
        pytest.skip(f"{f} not produced yet")
    return json.loads(f.read_text())


@pytest.mark.parametrize("scroll", SCROLLS)
def test_roundtrip_fitted_affine(scroll):
    """Fitted affine: 9 um -> 2.4 um (exact and rounded to a stored voxel) -> 9 um."""
    fit = _final(scroll)
    tr = fit["transform"]
    band = fit["band"]
    rng = np.random.default_rng(6)
    z0, z1 = band["z9_common_all_columns"]
    c = np.array(band["rescan_centre_xy9"])
    rad = band["rescan_disc_radius_9um_vox"] * 0.95
    r = rad * np.sqrt(rng.uniform(0, 1, 5000))
    a = rng.uniform(0, 2 * np.pi, 5000)
    p = np.c_[c[0] + r * np.cos(a), c[1] + r * np.sin(a), rng.uniform(z0, z1, 5000)]
    q = c6.map_9_to_r(p, tr, frame="raw")
    raw = np.array(tr["orientation"]["rescan_shape_zyx"])[::-1]
    assert np.all(q > -1) and np.all(q < raw), "band points must map inside the rescan"
    assert np.abs(c6.map_r_to_9(q, tr, frame="raw") - p).max() < 1e-6
    err = np.linalg.norm(c6.map_r_to_9(np.round(q), tr, frame="raw") - p, axis=1)
    assert err.max() < 0.5
    # scale sanity: F from metadata, not assumed
    assert abs(tr["F"] - fit["F_from_metadata"]) < 1e-12
