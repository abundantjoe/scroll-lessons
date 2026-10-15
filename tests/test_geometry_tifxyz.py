# Provenance: Project HERCULES | owner the owner | [id removed]
"""tifxyz I/O and grid-geometry tests (synthetic data only)."""

import json

import numpy as np
import pytest
import tifffile

from hercules.geometry import tifxyz as T


def plane_grid(H=6, W=7, step=20.0, origin=(100.0, 200.0, 300.0)):
    vv, uu = np.mgrid[0:H, 0:W].astype(np.float64)
    x = origin[0] + uu * step
    y = origin[1] + vv * step
    z = np.full_like(x, origin[2])
    return np.stack([x, y, z], axis=-1).astype(np.float32)


def test_write_read_round_trip_preserves_sentinel(tmp_path):
    rng = np.random.default_rng(0)
    pts = (rng.random((9, 11, 3)) * 500 + 10).astype(np.float32)
    pts[2, 3] = -1.0
    pts[5:7, 0:4] = -1.0
    pts[8, 10] = np.nan  # non-finite -> written as the sentinel
    mesh = T.TifxyzMesh(points=pts, scale=(0.05, 0.05), uuid="seg_test", meta={"max_gen": 7})
    d = T.write_tifxyz(tmp_path / "seg_test", mesh)

    for name in ("x.tif", "y.tif", "z.tif", "meta.json"):
        assert (d / name).exists()
    with tifffile.TiffFile(d / "x.tif") as tf:
        assert len(tf.pages) == 1
        page = tf.pages[0]
        assert page.dtype == np.float32
        assert page.shape == (9, 11)  # (rows=v, cols=u)
        assert page.compression == 1  # none
        assert not page.is_tiled
        assert page.samplesperpixel == 1

    meta = json.loads((d / "meta.json").read_text())
    assert meta["format"] == "tifxyz" and meta["type"] == "seg" and meta["uuid"] == "seg_test"
    assert meta["scale"] == [0.05, 0.05]
    assert meta["max_gen"] == 7
    valid = T.valid_mask(T.canonicalize(pts))
    exp_lo = pts[valid].min(axis=0)
    exp_hi = pts[valid].max(axis=0)
    np.testing.assert_allclose(meta["bbox"][0], exp_lo, rtol=0, atol=1e-3)
    np.testing.assert_allclose(meta["bbox"][1], exp_hi, rtol=0, atol=1e-3)

    raw = np.stack([tifffile.imread(d / n) for n in T.COORD_FILES], axis=-1)
    assert np.all(raw[~valid] == -1.0)  # sentinel on disk in all three bands

    back = T.read_tifxyz(d)
    assert back.uuid == "seg_test" and back.scale == (0.05, 0.05)
    assert back.step_vox == pytest.approx((20.0, 20.0))
    assert back.meta == {"max_gen": 7}
    np.testing.assert_array_equal(back.valid, valid)
    np.testing.assert_array_equal(back.points[valid], pts[valid])
    assert np.all(back.points[~valid] == -1.0)


def test_loader_rules_z_nonpositive_and_mask(tmp_path):
    pts = plane_grid(8, 8)
    pts[1, 1, 2] = 0.0  # official loader invalidates z <= 0
    mesh = T.TifxyzMesh(points=pts, scale=(0.05, 0.05), uuid="m")
    d = T.write_tifxyz(tmp_path / "m", mesh, write_mask=True, voxel_size_um=7.91)
    with tifffile.TiffFile(d / "x.tif") as tf:
        xres = tf.pages[0].tags["XResolution"].value
        assert xres[0] / xres[1] == pytest.approx(25400.0 / 7.91, rel=1e-4)
    back = T.read_tifxyz(d)
    assert not back.valid[1, 1] and back.valid.sum() == 63

    # mask at 2x the grid resolution: one sub-pixel < 255 invalidates its vertex
    m = np.full((16, 16), 255, np.uint8)
    m[9, 12] = 0
    tifffile.imwrite(d / "mask.tif", m)
    back = T.read_tifxyz(d)
    assert not back.valid[4, 6] and back.valid.sum() == 62
    assert T.read_tifxyz(d, apply_mask=False).valid.sum() == 63


def test_write_refuses_overwrite_and_requires_uuid(tmp_path):
    mesh = T.TifxyzMesh(points=plane_grid(), scale=(0.05, 0.05), uuid="a")
    T.write_tifxyz(tmp_path / "a", mesh)
    with pytest.raises(FileExistsError):
        T.write_tifxyz(tmp_path / "a", mesh)
    g = np.arange(42, dtype=np.uint16).reshape(6, 7)
    tifffile.imwrite(tmp_path / "a" / "generations.tif", g)
    T.write_tifxyz(tmp_path / "a", mesh, overwrite=True)  # extra channel carried forward
    np.testing.assert_array_equal(tifffile.imread(tmp_path / "a" / "generations.tif"), g)
    T.write_tifxyz(tmp_path / "a", mesh, overwrite=True, preserve_aux=False)
    assert not (tmp_path / "a" / "generations.tif").exists()
    with pytest.raises(ValueError):
        T.write_tifxyz(tmp_path / "b", T.TifxyzMesh(points=plane_grid(), uuid=""))


def test_densify_bilinear_and_invalid_propagation():
    p = plane_grid(4, 5, step=20.0)
    p[0, 0] = -1.0  # kills quad (0, 0) only
    d = T.densify(p, k=5)
    assert d.shape == (16, 21, 3)
    ok = T.valid_mask(d)
    assert not ok[1, 1]  # interior of the dead quad
    assert ok[5, 5] and ok[0, 5] and ok[5, 0]  # corners/edges shared with valid quads
    assert not ok[0, 0]
    # plane is linear in (u, v) -> bilinear subdivision is exact: 4 vox spacing
    vv, uu = np.nonzero(ok)
    np.testing.assert_allclose(d[vv, uu, 0], 100 + uu * 4.0, atol=1e-4)
    np.testing.assert_allclose(d[vv, uu, 1], 200 + vv * 4.0, atol=1e-4)
    assert T.edge_fraction_within(d, 4.0, 0.1) == 1.0


def test_normals_area_and_edge_fraction():
    p = plane_grid(11, 11, step=20.0)
    n = T.vertex_normals(p)
    np.testing.assert_allclose(n[T.valid_mask(p)], np.tile([0, 0, 1.0], (121, 1)), atol=1e-6)
    assert T.area_vox2(p) == pytest.approx(200.0 * 200.0)
    # 7.91 um voxels: 40000 vox^2 * 62.5681 um^2 = 2.502724e6 um^2 = 0.02502724 cm^2
    assert T.area_cm2(p, 7.91) == pytest.approx(40000 * 7.91**2 * 1e-8)
    with pytest.raises(ValueError):
        T.area_cm2(p, None)
    q = p.copy()
    q[5, 5, 0] += 3.0  # two u-edges become 23 / 17 vox (+-15 %); v-edges 20.22 (+1.1 %)
    lu, lv = T.edge_lengths(q)
    total = np.isfinite(lu).sum() + np.isfinite(lv).sum()
    assert T.edge_fraction_within(q, 20.0, 2.0) == pytest.approx((total - 2) / total)
    assert T.edge_fraction_within(q, 20.0, 0.5) == pytest.approx((total - 4) / total)


def test_sample_grid_propagates_invalid():
    p = plane_grid(3, 3)
    p[2, 2] = -1.0
    s = T.sample_grid(p, np.array([0.5, 1.5, 1.0, 5.0]), np.array([0.5, 1.5, 0.25, 0.0]))
    np.testing.assert_allclose(s[0], [110, 210, 300], atol=1e-5)
    assert np.all(s[1] == -1.0)  # quad (1,1) touches the invalid corner
    np.testing.assert_allclose(s[2], [105, 220, 300], atol=1e-5)
    assert np.all(s[3] == -1.0)  # outside
