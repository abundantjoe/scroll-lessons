"""Unit tests for P4-I (DECL-P4-8) on synthetic tiles only. Numbers only."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct_core as sc  # noqa: E402
import struct_rules as sr  # noqa: E402

N = 1068
PPM = sc.PX_PER_MM_DISPLAY


def noise_tile(rng, kind='white', sd=25.0, mean=100.0):
    x = rng.normal(0, 1, (N, N))
    if kind == 'pink':
        F = np.fft.fft2(x)
        fy = np.fft.fftfreq(N)[:, None]; fx = np.fft.fftfreq(N)[None, :]
        r = np.hypot(fx, fy); r[0, 0] = 1
        x = np.real(np.fft.ifft2(F / r))
        x = (x - x.mean()) / x.std()
    return np.clip(mean + sd * x, 1, 255).astype(np.uint8)


def row_tile(rng, pitch_mm, theta_deg, amp=30.0, noise_sd=25.0, textlike=False):
    """Rows of 'ink' at a pitch; theta = wavevector angle (image axes, y down)."""
    y, x = np.mgrid[0:N, 0:N].astype(float)
    th = np.deg2rad(theta_deg)
    u = (x * np.cos(th) + y * np.sin(th)) / PPM          # mm along the wavevector
    ph = rng.uniform(0, 1)
    band = (((u / pitch_mm + ph) % 1.0) < 0.45).astype(float)   # a text line ~45 % of the pitch
    if textlike:
        # letters and words at random positions along each line (no periodic word gating)
        v = (-x * np.sin(th) + y * np.cos(th)) / PPM
        line = np.floor(u / pitch_mm + ph).astype(int)
        vv = np.arange(-40.0, 40.0, 0.1)
        keep = {}
        for L in np.unique(line):
            on = np.zeros(vv.size, bool)
            pos = -40.0 + rng.uniform(0, 3)
            while pos < 40.0:
                wl = rng.uniform(3, 12)                      # a word, 3-12 mm
                i0, i1 = np.searchsorted(vv, [pos, pos + wl])
                on[i0:i1] = rng.uniform(0, 1, i1 - i0) > 0.0
                pos += wl + rng.uniform(1.0, 2.5)            # a gap
            lett = (np.sin(2 * np.pi * vv / 1.3 + rng.uniform(0, 6)) > -0.2)
            keep[L] = on & lett
        idx = np.clip(np.searchsorted(vv, v), 0, vv.size - 1)
        mask = np.zeros_like(band)
        for L, k in keep.items():
            sel = line == L
            mask[sel] = k[idx[sel]]
        band = band * mask
    base = rng.normal(0, 1, (N, N)) * noise_sd
    return np.clip(90 + amp * band + base, 1, 255).astype(np.uint8)


@pytest.fixture(scope='module')
def noise_null():
    rng = np.random.default_rng(1)
    tiles = [noise_tile(rng, 'white' if i % 2 else 'pink') for i in range(120)]
    S = [sc.tile_stat(t)['S_row'] for t in tiles]
    S90 = [sc.tile_stat(np.rot90(t))['S_row'] for t in tiles]
    return np.array(S), np.array(S90)


@pytest.mark.parametrize('pitch,theta', [(3.5, 90), (5.0, 90), (7.0, 0), (8.5, 30), (4.2, 136), (6.0, 64)])
def test_planted_rows_detected_at_theta(pitch, theta, noise_null):
    rng = np.random.default_rng(int(pitch * 100 + theta))
    t = row_tile(rng, pitch, theta)
    r = sc.tile_stat(t)
    assert sc.ang_diff(r['theta_star'], theta) <= 5.0, r   # declared window is +-10
    S, S90 = noise_null
    assert r['S_row'] > np.percentile(S90, 99), (r, np.percentile(S90, 99))
    # the band-peak period is within one spectral resolution cell (1/20 mm^-1) of the pitch
    assert abs(1 / r['period_mm_at_peak'] - 1 / pitch) <= 1 / 20.0 + 1e-9, r


def test_pure_noise_below_rot90_p99(noise_null):
    S, S90 = noise_null
    T = np.percentile(S90, 99)
    assert (S > T).mean() <= 0.02


def test_blank_tiles_not_positive():
    blank0 = np.zeros((N, N), np.uint8)
    blankc = np.full((N, N), 120, np.uint8)
    for t in (blank0, blankc):
        r = sc.tile_stat(t)
        assert r['S_row'] is None
    tiles = {('title', 0, 0): blank0, ('title', 0, 1): blankc}
    stats = {k: sc.tile_stat(v) for k, v in tiles.items()}
    for k, v in stats.items():
        v['M_ink'] = 0.0
        v['labelled_adjacent'] = False
    pos = sr.struct_positive(stats, T=0.0, theta_c=90.0, gate_pass=True)
    assert pos == []


def test_mask_edge_is_not_structure(noise_null):
    """A straight invalid (0) region along a tile half must not make noise look like rows."""
    rng = np.random.default_rng(7)
    S, S90 = noise_null
    T = np.percentile(S90, 99)
    hits = 0
    for i in range(40):
        t = noise_tile(rng, 'pink' if i % 2 else 'white')
        cut = rng.integers(300, 700)
        if i % 4 < 2:
            t[:cut, :] = 0
        else:
            t[:, :cut] = 0
        r = sc.tile_stat(t)
        if r['S_row'] is not None and r['S_row'] > T:
            hits += 1
    assert hits <= 2


def test_small_zero_blobs_stay_in_support():
    rng = np.random.default_rng(3)
    t = noise_tile(rng)
    t[t < np.percentile(t, 1)] = 0            # the 1 % stretch clip of the CT displays
    m = sc.support_mask(t)
    assert m.mean() > 0.999
    t[:, :400] = 0                            # a large invalid region
    m = sc.support_mask(t)
    assert abs(m.mean() - (N - 400) / N) < 0.002


def test_rot90_invariance_of_declared_statistic():
    """Fact recorded in REPORT/ASK: S_row (max over all theta) is invariant under rot-90."""
    rng = np.random.default_rng(11)
    for t in (row_tile(rng, 5.0, 90), noise_tile(rng, 'pink')):
        a, b = sc.tile_stat(t), sc.tile_stat(np.rot90(t))
        assert abs(a['S_row'] - b['S_row']) <= 1e-3 * a['S_row']      # float32 remap/blur
        assert sc.ang_diff(a['theta_star'] + 90.0, b['theta_star']) <= 1e-9
        assert sc.ang_diff(a['theta_star'], b['theta_star']) == 90.0


def test_circ_median_and_angles():
    assert sc.circ_median([178, 2, 0, 176, 4]) in (0.0, 179.5, 0.5)
    assert sc.ang_diff(179, 1) == 2
    assert sc.circ_median([88, 90, 92]) == 90.0


def test_auc_and_jaccard():
    assert sc.auc([2, 3], [0, 1]) == 1.0
    assert sc.auc([1], [1]) == 0.5
    assert sc.jaccard({1, 2}, {2, 3}) == pytest.approx(1 / 3)
    j, p = sc.jaccard_perm_p({1, 2, 3}, {1, 2, 3}, range(60), n_perm=2000)
    assert j == 1.0 and p < 0.01


def test_gate_and_positive_rules():
    rng = np.random.default_rng(5)
    ctrl = {('ctrl', 0, i): dict(S_row=10.0 + i, theta_star=90.0 + (i % 3) - 1, M_ink=0.1,
                                 insufficient=False, labelled_adjacent=False) for i in range(10)}
    g = sr.gate(ctrl, T=12.5)
    assert g['n_nonblank'] == 10 and g['n_pass'] == 7 and g['pass'] is True
    g2 = sr.gate(ctrl, T=100.0)
    assert g2['pass'] is False
    title = {('title', 0, 0): dict(S_row=50.0, theta_star=95.0, M_ink=0.0, insufficient=False, labelled_adjacent=False),
             ('title', 0, 1): dict(S_row=50.0, theta_star=120.0, M_ink=0.0, insufficient=False, labelled_adjacent=False),
             ('title', 0, 2): dict(S_row=50.0, theta_star=90.0, M_ink=0.0, insufficient=False, labelled_adjacent=True),
             ('title', 0, 3): dict(S_row=5.0, theta_star=90.0, M_ink=0.0, insufficient=False, labelled_adjacent=False),
             ('title', 0, 4): dict(S_row=50.0, theta_star=90.0, M_ink=0.0, insufficient=False, labelled_adjacent=None)}
    assert sr.struct_positive(title, T=12.5, theta_c=90.0, gate_pass=True) == [('title', 0, 0)]
    assert sr.struct_positive(title, T=12.5, theta_c=90.0, gate_pass=False) == []
    del rng


def test_proposed_anchored_variant_separates_rows_from_rot90():
    """ASK-1 proposal, synthetic only: rows at theta_c beat their own rot-90 copies."""
    rng = np.random.default_rng(21)
    txt = [row_tile(rng, rng.uniform(3.5, 8.5), 90 + rng.uniform(-4, 4), amp=40, textlike=True) for _ in range(16)]
    noi = [noise_tile(rng, 'pink' if i % 2 else 'white') for i in range(16)]
    theta_c = sc.circ_median([sc.tile_stat(t)['theta_star'] for t in txt])
    assert sc.ang_diff(theta_c, 90) <= 4
    s_t = [sc.s_anch(sc.tile_R(t), theta_c) for t in txt]
    null = [sc.s_anch(sc.tile_R(np.rot90(t)), theta_c) for t in txt + noi]
    T = np.percentile(null, 99)
    assert np.mean(np.array(s_t) > T) >= 0.30
    assert sc.auc(s_t, null[:16]) >= 0.9
    s_n = [sc.s_anch(sc.tile_R(t), theta_c) for t in noi]
    assert np.mean(np.array(s_n) > T) <= 0.07     # 1 of 16 allowed
