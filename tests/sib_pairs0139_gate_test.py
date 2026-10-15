# Provenance: Project HERCULES | owner the owner | [id removed]
"""pairs0139 build_pairs gate helpers on synthetic smooth noise (no real data): ncc and best_shift."""
import sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, "tools/sib/pairs0139")
import build_pairs as B


def tex(seed, n=200):
    return ndi.gaussian_filter(np.random.default_rng(seed).standard_normal((n, n)), 2.0)


def test_ncc_identity_and_sign():
    a = tex(0)[:64, :64]; m = np.ones(a.shape, bool)
    assert abs(B.ncc(a, a, m) - 1) < 1e-12 and abs(B.ncc(a, -a, m) + 1) < 1e-12


def test_best_shift_recovers_known_shift():
    big = tex(1)
    for sy, sx in [(0.0, 0.0), (1.4, -0.6), (-2.3, 2.0)]:
        # ref sampled so that ours(y, x) = ref(y + sy, x + sx) (ref carries an SMAX margin)
        yy, xx = np.meshgrid(np.arange(128 + 2 * B.SMAX), np.arange(128 + 2 * B.SMAX), indexing="ij")
        ref = ndi.map_coordinates(big, [yy + 30.0, xx + 30.0], order=3)
        ours = ndi.map_coordinates(big, [yy[:128, :128] + 30.0 + B.SMAX + sy, xx[:128, :128] + 30.0 + B.SMAX + sx], order=3)
        vo = np.ones(ours.shape, bool); vr = np.ones(ref.shape, bool)
        dy, dx, n, border = B.best_shift(ours, ref, vo, vr, 32, 32)
        assert not border and abs(dy - sy) < 0.25 and abs(dx - sx) < 0.25, (sy, sx, dy, dx)


def test_border_shift_flagged():
    big = tex(2)
    yy, xx = np.meshgrid(np.arange(136), np.arange(136), indexing="ij")
    ref = ndi.map_coordinates(big, [yy + 30.0, xx + 30.0], order=1)
    ours = ndi.map_coordinates(big, [yy[:128, :128] + 30.0 + B.SMAX + 6, xx[:128, :128] + 30.0 + B.SMAX], order=1)
    dy, dx, n, border = B.best_shift(ours, ref, np.ones((128, 128), bool), np.ones((136, 136), bool), 32, 32)
    assert border


def test_ncc_grid_matches_loop():
    rng = np.random.default_rng(5)
    ref = tex(3, 136); ours = tex(4, 128) + 0.5 * ref[4:132, 4:132]
    vo = rng.random((128, 128)) > 0.05; vr = rng.random((136, 136)) > 0.05
    for (y, x, h, w) in [(4, 4, 128, 128), (36, 68, 64, 64)]:
        a = ours[y - 4:y - 4 + h, x - 4:x - 4 + w]; ma = vo[y - 4:y - 4 + h, x - 4:x - 4 + w]
        G = B.ncc_grid(a, ma, ref, vr, y, x, h, w)
        for dy in range(-B.SMAX, B.SMAX + 1):
            for dx in range(-B.SMAX, B.SMAX + 1):
                sl = (slice(y + dy, y + dy + h), slice(x + dx, x + dx + w))
                assert abs(G[dy + B.SMAX, dx + B.SMAX] - B.ncc(a, ref[sl], ma & vr[sl])) < 1e-9
