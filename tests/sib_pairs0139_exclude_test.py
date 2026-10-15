# Provenance: Project HERCULES | owner the owner | [id removed]
"""pairs0139 exclude.py: sub-quad bound and exact Rule-N count vs brute force on synthetic meshes."""
import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "tools/sib/pairs0139")
import exclude as E


def fake(offset_z, n=8, wobble=0.0, seed=0):
    rng = np.random.default_rng(seed)
    v, u = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    p = np.stack([u * 20.0, v * 20.0, np.full(u.shape, offset_z) + wobble * rng.standard_normal(u.shape)], -1)
    m = E.M.__new__(E.M)
    m.p = p; H, W = u.shape; m.canvas = (H * E.K, W * E.K)
    qr, qc = np.nonzero(np.ones((H - 1, W - 1), bool)); nn = E.K // E.KS
    m.sq_r = np.repeat(qr, nn * nn); m.sq_c = np.repeat(qc, nn * nn)
    ij = np.tile(np.arange(nn * nn), qr.size); m.sq_i = ij // nn; m.sq_j = ij % nn
    C = m.corners(np.arange(m.sq_r.size)); m.cent = C.mean(1); m.h = np.linalg.norm(C - m.cent[:, None], axis=-1).max(1)
    m.n_dense = qr.size * E.K ** 2; m.big = np.nonzero(m.h > E.HC)[0]
    m.spts = m.cent[m.h <= E.HC]; m.sown = np.nonzero(m.h <= E.HC)[0]
    if m.big.size:
        P, _ = m.samples(m.big); m.spts = np.concatenate([m.spts, P.reshape(-1, 3)])
        m.sown = np.concatenate([m.sown, np.repeat(m.big, E.KS ** 2)])
    m.tree = cKDTree(m.spts)
    return m


def test_bound_and_exact():
    a = fake(0.0, wobble=3.0, seed=1); b = fake(1.8, wobble=3.0, seed=2)
    Pa, RCa = a.samples(np.arange(a.sq_r.size)); Pb, _ = b.samples(np.arange(b.sq_r.size))
    # every sample within h of its sub-quad centre
    assert (np.linalg.norm(Pa - a.cent[:, None], axis=-1) <= a.h[:, None] + 1e-9).all()
    d, _ = cKDTree(Pb.reshape(-1, 3)).query(Pa.reshape(-1, 3))
    brute = set(map(tuple, RCa.reshape(-1, 2)[d <= E.D_N]))
    rc, _ = E.near_pixels(a, [b], E.D_N, exact=True)
    assert set(map(tuple, rc)) == brute and len(brute) > 0
    rcs, _ = E.near_pixels(a, [b], 16.0, exact=False)
    brute16 = set(map(tuple, RCa.reshape(-1, 2)[d <= 16.0]))
    assert brute16 <= set(map(tuple, rcs))


def test_far_is_empty():
    a = fake(0.0); b = fake(40.0)
    rc, _ = E.near_pixels(a, [b], E.D_N, exact=True)
    assert len(rc) == 0
