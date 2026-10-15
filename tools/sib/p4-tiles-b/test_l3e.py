"""Unit tests for l3e_lib (DECL-P4-12-A4 task item 3). Synthetic data only.

Provenance: Project HERCULES | owner the owner | [id removed]
Run: python -m pytest tools/sib/p4-tiles-b/test_l3e.py -q

T_hi is derived in each test as p99.9 of the synthetic sheet slab (slices 52..64), the rule
p4-highz used for the frozen 233. Two tests document limits of the declared rule rather than
hide them: the false-PASS rate on a flat, layer-free profile, and that a pure sheet-density bump
(no ink) is indistinguishable from a layer at d* ~ 0.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l3e_lib import calibrate, slab_slices, slice_counts  # noqa: E402

N, C, STEP = 116, 58, 2.258


def stack(seed, sheet_amp, layer_slice=None, n_chunks=8, hw=96, profile="flat"):
    rng = np.random.default_rng(seed)
    k = np.arange(N)[:, None, None]
    base = 110 + sheet_amp * np.exp(-0.5 * ((k - C) / 20.0) ** 2)
    out = []
    for _ in range(n_chunks):
        v = base + rng.normal(0, 30, (N, hw, hw))
        if layer_slice is not None:
            if profile == "flat":  # flat-topped deposit, 7 slices (15.8 um)
                dens = np.where(np.abs(k - layer_slice) <= 3, 0.02, 0.0)
            else:  # peaked deposit, Gaussian in depth, sigma 2 slices (4.5 um; FWHM ~ 10.6 um)
                dens = 0.03 * np.exp(-0.5 * ((k - layer_slice) / 2.0) ** 2)
            lay = rng.random((N, hw, hw)) < dens
            v = np.where(lay, 250, v)
        out.append(np.clip(np.rint(v), 0, 255).astype(np.uint8))
    return out


def t_hi_from(chunks):
    return float(np.percentile(np.concatenate([c[52:65].ravel() for c in chunks]), 99.9))


def counts(chunks, thi):
    mask = np.ones(chunks[0].shape[1:], bool)
    mask[:8] = False
    h = np.zeros(N, np.int64)
    p = np.zeros(N, np.int64)
    for c in chunks:
        a, b, _ = slice_counts(c, mask, thi)
        h += a
        p += b
    return h, p


@pytest.mark.parametrize("ls", [20, 36, 58, 75, 96])
@pytest.mark.parametrize("sheet_amp", [0, 30])
def test_peaked_layer_recovered_within_5um(ls, sheet_amp):
    """Declared d* (argmax) recovers a peaked deposit within 5 um."""
    thi = t_hi_from(stack(100 + ls, sheet_amp))  # threshold frozen on the ink-free control
    h, p = counts(stack(ls, sheet_amp, layer_slice=ls, profile="gauss"), thi)
    r = calibrate(h, p, STEP, C)
    assert r["verdict"] == "PASS", r["reasons"]
    assert abs(r["d_star_um"] - (ls - C) * STEP) <= 5.0
    assert abs(r["halfmax_centroid_um"] - (ls - C) * STEP) <= 5.0


@pytest.mark.parametrize("ls", [20, 36, 58, 75, 96])
@pytest.mark.parametrize("sheet_amp", [0, 30])
def test_flat_layer_centroid_within_5um_argmax_within_half_thickness(ls, sheet_amp):
    """A flat-topped 15.8 um deposit: the declared argmax is only defined to within the half
    thickness (3 slices, 6.8 um); the half-max centroid diagnostic recovers it within 5 um."""
    thi = t_hi_from(stack(100 + ls, sheet_amp))
    h, p = counts(stack(ls, sheet_amp, layer_slice=ls, profile="flat"), thi)
    r = calibrate(h, p, STEP, C)
    assert r["verdict"] == "PASS", r["reasons"]
    assert abs(r["d_star_um"] - (ls - C) * STEP) <= 3 * STEP + 1e-9
    assert abs(r["halfmax_centroid_um"] - (ls - C) * STEP) <= 5.0


def test_no_bright_voxels_stops():
    h = np.zeros(N, np.int64)
    p = np.full(N, 10 ** 6, np.int64)
    r = calibrate(h, p, STEP, C)
    assert r["verdict"] == "STOP"


def test_flat_no_layer_false_pass_rate_measured():
    """Layer-free flat profile, iid binomial counts: the declared max-over-offsets rule has a
    false-PASS rate near 1 - Phi(3)^116 ~ 0.145 (one-sided) plus the +-100 um window restriction.
    The rate is measured and must stay below 0.25; it is reported, not tuned."""
    rng = np.random.default_rng(20260926)
    n_sim, n_pass = 2000, 0
    for _ in range(n_sim):
        p = np.full(N, 10 ** 6)
        h = rng.binomial(p, 1e-3)
        n_pass += calibrate(h, p, STEP, C)["verdict"] == "PASS"
    rate = n_pass / n_sim
    print("false_pass_rate_flat", rate)
    assert rate < 0.25


def test_layer_outside_window_stops():
    thi = t_hi_from(stack(7, 0))
    h, p = counts(stack(7, 0, layer_slice=110), thi)  # +117 um
    r = calibrate(h, p, STEP, C)
    assert r["verdict"] == "STOP"
    assert any("outside" in s for s in r["reasons"])


def test_sheet_bump_without_ink_documented_limitation():
    """Documents that a sheet-density bump alone (no ink) produces a PASS at d* ~ 0: the declared
    rule cannot tell sheet density from an ink layer at the mesh. A d* within a few um of 0 on real
    data must be reported with this caveat."""
    ch = stack(11, 30)
    h, p = counts(ch, t_hi_from(ch))
    r = calibrate(h, p, STEP, C)
    assert r["verdict"] == "PASS" and abs(r["d_star_um"]) <= 10.0


def test_both_sides_reported():
    thi = t_hi_from(stack(9, 0))
    h, p = counts(stack(9, 0, layer_slice=40), thi)
    r = calibrate(h, p, STEP, C)
    assert r["side_negative"]["offset_um"] < 0 and r["side_positive"]["offset_um"] > 0
    assert r["global_peak"]["offset_um"] == r["side_negative"]["offset_um"]


def test_rot90_invariance():
    rng = np.random.default_rng(3)
    v = rng.integers(0, 256, (N, 32, 32), dtype=np.uint8)
    m = rng.random((32, 32)) < 0.7
    a = slice_counts(v, m, 233)
    b = slice_counts(np.rot90(v, 1, axes=(1, 2)), np.rot90(m), 233)
    assert all((x == y).all() for x, y in zip(a, b))


def test_slab_slices():
    assert slab_slices(0.0, STEP, C, N) == list(range(C - 4, C + 5))
    s = slab_slices(-40.0, STEP, C, N)
    assert len(s) == 9 and all(abs((k - C) * STEP + 40.0) <= 10.0 for k in s)
