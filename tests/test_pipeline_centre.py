# Provenance: Project HERCULES | owner the owner | [id removed]
"""Centre curves (hercules.pipeline.centre): mask centroid on a fake S3 zarr,
geometry-only fallbacks, umbilicus JSON."""

import io
import json

import numpy as np
import pytest

from hercules.geometry.render_synth import cylinder_grid
from hercules.pipeline import centre as Ce

PREFIX = "PHercTEST/volumes/test.zarr"
URL = f"s3://vesuvius-challenge-open-data/{PREFIX}/"


class FakeS3:
    class exceptions:  # noqa: N801 - mimics boto3 client.exceptions
        class NoSuchKey(Exception):
            pass

    def __init__(self, objects):
        self.objects = objects
        self.calls = 0

    def get_object(self, Bucket, Key, Range=None):
        self.calls += 1
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey(Key)
        b = self.objects[Key]
        if Range:
            a, c = (int(t) for t in Range.split("=")[1].split("-"))
            b = b[a:c + 1]
        return {"Body": io.BytesIO(b)}

    def list_objects_v2(self, Bucket, Prefix):
        return {"Contents": [{"Key": k} for k in sorted(self.objects) if k.startswith(Prefix)]}


def disk_volume(Z=40, Y=50, X=60):
    zz, yy, xx = np.mgrid[0:Z, 0:Y, 0:X]
    cx = 25 + 0.2 * zz
    cy = 20 + 0.1 * zz
    v = ((xx - cx) ** 2 + (yy - cy) ** 2 < 12 ** 2).astype(np.uint8) * 90
    v[20:23] = 0  # empty slices (below min area) are dropped
    return v


def fake_store(vol, level=4, chunks=(16, 32, 32), compressor=None, drop_empty=True):
    Z, Y, X = vol.shape
    cz, cy, cx = chunks
    za = dict(zarr_format=2, shape=[Z, Y, X], chunks=list(chunks), dtype="|u1", fill_value=0, order="C",
              filters=None, dimension_separator="/", compressor=compressor)
    objs = {f"{PREFIX}/{level}/.zarray": json.dumps(za).encode(),
            f"{PREFIX}/0/.zarray": json.dumps(dict(za, shape=[Z * 16, Y * 16, X * 16])).encode()}
    for iz in range(-(-Z // cz)):
        for iy in range(-(-Y // cy)):
            for ix in range(-(-X // cx)):
                c = np.zeros(chunks, np.uint8)
                part = vol[iz * cz:(iz + 1) * cz, iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx]
                c[:part.shape[0], :part.shape[1], :part.shape[2]] = part
                if drop_empty and not c.any():
                    continue  # missing chunk = fill value
                b = c.tobytes()
                if compressor is not None:
                    import numcodecs

                    b = numcodecs.get_codec(compressor).encode(b)
                objs[f"{PREFIX}/{level}/{iz}/{iy}/{ix}"] = bytes(b)
    return FakeS3(objs)


def expected(vol, z):
    m = vol[z] > 0
    yy, xx = np.mgrid[0:vol.shape[1], 0:vol.shape[2]]
    return xx[m].mean() * 16 + 7.5, yy[m].mean() * 16 + 7.5


@pytest.mark.parametrize("compressor", [None, {"id": "zlib", "level": 1}])
def test_mask_centroid_exact(compressor):
    vol = disk_volume()
    s3 = fake_store(vol, compressor=compressor)
    mc = Ce.mask_centroid_curve(URL, 4, smooth_sigma_vox=0, client=s3, workers=2)
    assert mc.level == 4 and len(mc.z_full) == vol.shape[0]
    assert np.allclose(mc.z_full, np.arange(vol.shape[0]) * 16 + 7.5)
    for z in (0, 7, 19, 33, 39):
        ex, ey = expected(vol, z)
        assert abs(mc.x_raw[z] - ex) < 1e-9 and abs(mc.y_raw[z] - ey) < 1e-9
        cx, cy = mc.curve(np.array([z * 16 + 7.5]))
        assert abs(cx[0] - ex) < 1e-9 and abs(cy[0] - ey) < 1e-9
    assert np.isnan(mc.x_raw[20:23]).all()  # empty slices dropped, then interpolated over
    cx, cy = mc.curve(np.array([21 * 16 + 7.5]))
    assert abs(cx[0] - (25 + 0.2 * 21) * 16 - 7.5) < 16


def test_mask_centroid_stride_range_and_smoothing():
    vol = disk_volume()
    s3 = fake_store(vol)
    mc = Ce.mask_centroid_curve(URL, 4, z_range=(100, 500), z_stride=4, smooth_sigma_vox=64, client=s3)
    zi = np.round((mc.z_full - 7.5) / 16).astype(int)
    assert zi[0] == 5 and zi[-1] == 31  # slices whose extent overlaps the range and np.all(np.diff(zi)[:-1] == 4)
    # a linear trend survives Gaussian smoothing to well under a voxel in the interior
    z = 16 * 12 + 7.5
    cx, _ = mc.curve(np.array([z]))
    assert abs(cx[0] - expected(vol, 12)[0]) < 3


def test_sealed_scroll_guard():
    with pytest.raises(PermissionError):
        Ce.mask_centroid_curve("s3://vesuvius-challenge-open-data/PHerc0841/volumes/v.zarr/", 4, client=FakeS3({}))


def test_geometric_centre_recovers_cylinder_axis():
    p = cylinder_grid(600.0, (700.0, 650.0), (60, 80), 20.0, 25.0, s0=-900.0, z0=100.0)
    curve, info = Ce.geometric_centre_curve(p)
    cx, cy = curve(np.array([500.0, 900.0]))
    assert np.abs(cx - 700).max() < 0.5 and np.abs(cy - 650).max() < 0.5


def test_volume_axis_centre():
    s3 = fake_store(disk_volume())
    c, info = Ce.volume_axis_centre(URL, client=s3)
    assert info["shape"] == [640, 800, 960]
    cx, cy = c(np.array([0.0]))
    assert cx[0] == (960 - 1) / 2 and cy[0] == (800 - 1) / 2


def test_umbilicus_json_and_lookup():
    d = {"control_points": [{"x": 10, "y": 20, "z": 300, "score": 1}, {"x": 12, "y": 18, "z": 100, "score": 1}],
         "metadata": {"volume": "20260102150214-2.399um-0.2m-78keV-masked.zarr"}}
    c = Ce.umbilicus_from_json(d, expect_volume="20260102150214")
    x, y = c(np.array([200.0]))
    assert x[0] == 11 and y[0] == 19
    with pytest.raises(ValueError):
        Ce.umbilicus_from_json(d, expect_volume="20250728140407")
    s3 = FakeS3({"PHerc0139/representations/umbilicus/20260102150214-umbilicus-20260826112529.json": b"{}"})
    assert Ce.find_official_umbilicus("PHerc0139", "20250728140407", client=s3) is None
    assert Ce.find_official_umbilicus("PHerc0139", "20260102150214", client=s3).endswith("112529.json")
