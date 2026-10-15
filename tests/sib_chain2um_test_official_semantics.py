# Provenance: Project HERCULES | owner the owner | [id removed]
"""chain2um: pin the official optimized_inference semantics the CPU driver relies on.
Run: /opt/hv-ink/bin/python -m pytest -q tests/sib_chain2um_test_official_semantics.py (needs /work/villa at 41701aa)."""
import sys
import numpy as np
import pytest

OI = '/work/villa/ink-detection/optimized_inference'
torch = pytest.importorskip('torch')


@pytest.fixture(scope='module')
def oi():
    sys.path.insert(0, OI)
    import inference
    return inference


def _dataset(oi, arr, reverse, start, end):
    oi.CFG.in_chans = end - start
    oi.CFG.tile_size = oi.CFG.size = 4
    oi.CFG.max_clip_value = 200
    src = oi.LayersSource(arr, start_z=start, end_z=end)
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    tf = A.Compose([A.ToFloat(max_value=200), ToTensorV2()])
    return oi.SlidingWindowDataset(src, np.array([[0, 0, 4, 4]]), reverse, tf)


def test_reverse_is_channel_flip_after_layer_slice(oi):
    arr = np.tile(np.arange(63, dtype=np.uint8)[None, None, :] + 1, (4, 4, 1))  # layer k has value k+1
    fwd = _dataset(oi, arr, False, 0, 62)[0][0].numpy()[0, :, 0, 0]
    rev = _dataset(oi, arr, True, 0, 62)[0][0].numpy()[0, :, 0, 0]
    assert np.allclose(fwd * 200, np.arange(1, 63))           # forward = layers 0..61 ascending
    assert np.allclose(rev * 200, np.arange(62, 0, -1))       # reverse = layers 61..0
    assert np.allclose(rev, fwd[::-1])


def test_clip_200_and_scale(oi):
    arr = np.full((4, 4, 62), 255, np.uint8)
    x = _dataset(oi, arr, False, 0, 62)[0][0].numpy()
    assert np.allclose(x, 1.0)                                # clip 0..200 then /200


def test_nested_autocast_off_is_fp32():
    conv = torch.nn.Conv3d(1, 2, 3)
    x = torch.randn(1, 1, 4, 8, 8)
    with torch.inference_mode(), torch.autocast(device_type='cpu', enabled=True):
        y_bf = conv(x)
        with torch.autocast(device_type='cpu', enabled=False):
            y_fp = conv(x.float())
    assert y_bf.dtype == torch.bfloat16
    assert y_fp.dtype == torch.float32
    assert torch.allclose(y_fp, conv(x), atol=0, rtol=0)
