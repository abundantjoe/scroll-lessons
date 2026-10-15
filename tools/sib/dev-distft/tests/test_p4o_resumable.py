# Provenance: Project HERCULES | owner the owner | [id removed]
"""Within-tile resume: the patched card_tiling equals the original bitwise, uninterrupted and after crashes.
SYNTHETIC inputs and a stand-in model only. Run: /opt/hv-ink/bin/python -m pytest -q tools/sib/dev-distft/tests/test_p4o_resumable.py"""
import os
import sys
import types

import numpy as np
import pytest
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Fake:
    """Deterministic stand-in: (1,1,62,256,256) -> logits (1,1,64,64); raises after `die` calls if set."""

    def __init__(self, die=None):
        self.calls, self.die = 0, die
        g = torch.Generator().manual_seed(0)
        self.w = torch.randn(62, generator=g)

    def __call__(self, t):
        self.calls += 1
        if self.die is not None and self.calls > self.die:
            raise RuntimeError("simulated container reclaim")
        x = torch.nn.functional.avg_pool3d(t, (1, 4, 4))[0, 0]           # (62,64,64)
        return types.SimpleNamespace(logits=(x * self.w[:, None, None]).sum(0)[None, None] - 50.0)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("P4O_CKPT_DIR", str(tmp_path / "ck"))
    monkeypatch.setenv("P4O_CKPT_EVERY", "3")
    for m in ("p4o_resumable", "infer_1667"):
        sys.modules.pop(m, None)
    import infer_1667 as I
    orig = I.card_tiling
    import p4o_resumable as R
    rng = np.random.default_rng(1)
    H = W = 1024
    img = rng.integers(0, 255, (H, W, 62), dtype=np.uint8)
    fm = np.ones((H, W), np.uint8); fm[:200, :300] = 0; fm[900:, 700:] = 0
    return I, R, orig, img, fm, H, W, str(tmp_path / "ck")


def test_uninterrupted_equals_original(env):
    I, R, orig, img, fm, H, W, _ = env
    tf = lambda y, x: img[y:y + 256, x:x + 256]
    a = orig(Fake(), H, W, fm, tf, I.train_norm)
    b = R.resumable_card_tiling(Fake(), H, W, fm, tf, I.train_norm)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_crash_resume_bitwise(env):
    I, R, orig, img, fm, H, W, ck = env
    tf = lambda y, x: img[y:y + 256, x:x + 256]
    ref = orig(Fake(), H, W, fm, tf, I.train_norm)
    nwin = int(sum(1 for y in range(0, H - 255, 128) for x in range(0, W - 255, 128) if not np.any(fm[y:y + 256, x:x + 256] == 0)))
    for die in (4, 11):                                               # two crashes, not on a save boundary
        with pytest.raises(RuntimeError):
            R.resumable_card_tiling(Fake(die=die), H, W, fm, tf, I.train_norm)
        assert len(os.listdir(ck)) == 1
    m = Fake()
    out = R.resumable_card_tiling(m, H, W, fm, tf, I.train_norm)
    assert np.array_equal(ref[0], out[0]) and np.array_equal(ref[1], out[1])
    assert m.calls < nwin                                              # resumed, did not redo everything
    assert os.listdir(ck) == []                                        # save removed at the end
