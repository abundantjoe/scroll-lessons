import numpy as np
import pytest

from stripqc.fill import reflect_fill, fill_zarr


def synth(D=5, H=40, W=30, top=10, bottom=10, seed=0):
    rng = np.random.default_rng(seed)
    A = np.zeros((D, H, W), np.uint8)
    A[:, top:H - bottom] = rng.integers(1, 256, size=(D, H - top - bottom, W), dtype=np.uint8)
    return A


def test_valid_pixels_unchanged_and_no_blank_left():
    A = synth()
    out, st = reflect_fill(A)
    valid = (A > 0).any(0)
    assert np.array_equal(out[:, valid], A[:, valid])
    assert st['still_blank_px'] == 0 and st['valid_px'] == int(valid.sum())
    assert st['reflected_px'] == 20 * 30


def test_reflection_about_edge_rows():
    A = synth(top=10, bottom=10)
    out, _ = reflect_fill(A)
    for k in range(1, 10):
        assert np.array_equal(out[:, 10 - k], A[:, 10 + k])        # top: row t0 - k <- row t0 + k
        assert np.array_equal(out[:, 29 + k], A[:, 29 - k])        # bottom: row t1 + k <- row t1 - k


def test_reflection_clamped_to_valid_run_and_empty_column_nearest():
    A = synth(H=40, top=30, bottom=5)   # valid run of 5 rows: reflection must clamp, not read blank rows
    A[:, :, 7] = 0                       # an empty column -> nearest valid pixel
    out, st = reflect_fill(A)
    assert st['still_blank_px'] == 0
    assert (out > 0).any(0).all()
    assert np.array_equal(out[:, :, 7], out[:, :, 6]) or np.array_equal(out[:, :, 7], out[:, :, 8])


def test_rejects_wrong_shape():
    with pytest.raises(ValueError):
        reflect_fill(np.zeros((4, 4)))


def test_zarr_roundtrip(tmp_path):
    zarr = pytest.importorskip('zarr')
    A = synth()
    src = tmp_path / 'render.zarr'
    z = zarr.open(str(src / '0'), mode='w', shape=A.shape, chunks=(5, 16, 16), dtype=A.dtype, fill_value=0,
                  dimension_separator='/')
    z[:] = A
    st = fill_zarr(str(src), str(tmp_path / 'fill.zarr'))
    B = zarr.open(str(tmp_path / 'fill.zarr' / '0'), mode='r')[:]
    ref, _ = reflect_fill(A)
    assert np.array_equal(B, ref) and st['still_blank_px'] == 0


def test_zarr_refuses_to_overwrite_its_source(tmp_path):
    zarr = pytest.importorskip('zarr')
    A = synth()
    src = tmp_path / 'render.zarr'
    z = zarr.open(str(src / '0'), mode='w', shape=A.shape, chunks=(5, 16, 16), dtype=A.dtype, fill_value=0,
                  dimension_separator='/')
    z[:] = A
    with pytest.raises(ValueError):
        fill_zarr(str(src), str(src))
    assert np.array_equal(zarr.open(str(src / '0'), mode='r')[:], A)   # original render untouched
