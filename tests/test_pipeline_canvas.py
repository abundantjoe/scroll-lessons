# Provenance: Project HERCULES | owner the owner | [id removed]
"""Renderer canvas convention (hercules.pipeline.canvas).

Pure tests of the formulas derived from the villa 41701aa source, plus
end-to-end checks against the built official vc_render_tifxyz on synthetic
ramp volumes (value = 100 * x, 100 * y or 1000 * z), which read the sampled
voxel coordinate back from every output pixel. The official-binary tests are
skipped when /work/bin/vc or docker is unavailable.
"""

import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest

from hercules.geometry.tifxyz import TifxyzMesh, vertex_normals, write_tifxyz
from hercules.pipeline import canvas as C

VC = "/work/bin/vc"


def test_pixel_to_grid_half_pixel():
    cv = C.canvas_for((320, 399), (0.05, 0.05))
    assert cv.shape == (6400, 7980)
    v, u = cv.pixel_to_grid(0.0, 0.0)
    assert abs(u - 0.025) < 1e-5 and abs(v - 0.025) < 1e-5  # (P + 0.5) / 20
    v, u = cv.pixel_to_grid(2047.0, 1151.0)
    assert abs(u - 1151.5 / 20) < 1e-4 and abs(v - 2047.5 / 20) < 1e-4


def test_pixel_grid_round_trip_and_origin():
    cv = C.canvas_for((57, 83), (0.05, 0.05)).with_origin(13, -7)
    r = np.random.default_rng(0)
    y, x = r.uniform(-50, 1200, 500), r.uniform(-50, 1700, 500)
    v, u = cv.pixel_to_grid(y, x)
    y2, x2 = cv.grid_to_pixel(v, u)
    assert np.abs(y2 - y).max() < 1e-9 and np.abs(x2 - x).max() < 1e-9
    v0, u0 = C.canvas_for((57, 83), (0.05, 0.05)).pixel_to_grid(y + 13, x - 7)
    assert np.allclose(v, v0) and np.allclose(u, u0)


def test_non_integer_canvas_and_render_scale():
    # scale 0.03 -> W / s not an integer; render_scale 0.5 halves the canvas
    cv = C.canvas_for((10, 11), (0.03, 0.03), render_scale=0.5)
    Hc, Wc = cv.shape
    assert Wc == C.c_lround(11 * 0.5 / C.f32(0.03)) and Hc == C.c_lround(10 * 0.5 / C.f32(0.03))
    v, u = cv.pixel_to_grid(0.0, np.arange(Wc, dtype=float))
    assert np.allclose(np.diff(u), C.f32(0.03) / 0.5)
    # mid-canvas samples grid W/2 (renderer _center = cols / 2 / s), not (W-1)/2
    assert abs(u[0] + u[-1] - 11.0) < 1e-4


def test_c_lround_half_away():
    assert C.c_lround(0.5) == 1 and C.c_lround(-0.5) == -1 and C.c_lround(2.5) == 3
    assert list(C.c_lround(np.array([0.49, 1.5, -1.5]))) == [0, 2, -2]


def test_auto_crop_float32_origin():
    p = np.zeros((10, 13, 3), np.float32) + 5
    p[:1] = -1
    p[:, :2] = -1
    p[:, -1] = -1
    x, y, w, h = C.auto_crop_rect(p, (0.05, 0.05))
    # floor(2 / f32(0.05)) = floor(39.9999994) = 39 (NOT 40); verified on the binary below
    assert (x, y, w, h) == (39, 19, 201, 181)


def test_slice_offsets():
    o31 = C.slice_offsets(31)
    assert o31[15] == 0 and o31[0] == -15 and o31[30] == 15
    o28 = C.slice_offsets(28)
    assert o28[13] == -0.5 and o28[14] == 0.5
    assert C.surface_slices(31) == [15] and C.surface_slices(28) == [13, 14]
    assert np.allclose(C.slice_offsets(5, 0.5), [-1, -0.5, 0, 0.5, 1])


def test_flip_parity():
    f = C.flip_normals_after_orient
    assert f(True, False, False) is True and f(True, True, False) is False
    assert f(True, False, True) is False and f(True, True, True) is True
    assert f(False, True, False) is True
    assert C.slice_normal_sign(True) == -1 and C.slice_normal_sign(False) == 1


def test_official_normals_match_central_difference():
    r = np.random.default_rng(1)
    vv, uu = np.mgrid[0:7, 0:9].astype(np.float64)
    p = np.stack([20 * uu + r.normal(0, 1, uu.shape), 20 * vv + r.normal(0, 1, uu.shape),
                  r.normal(0, 3, uu.shape)], -1).astype(np.float32)
    n_off = C.vertex_normals_official(p)
    n_ref = vertex_normals(p)
    assert np.isnan(n_off[0]).all() and np.isnan(n_off[:, -1]).all()
    assert np.allclose(n_off[1:-1, 1:-1], n_ref[1:-1, 1:-1], atol=1e-6)


# ---------------------------------------------------------------------------
# against the official binary
# ---------------------------------------------------------------------------

def _vc_available() -> bool:
    if not os.path.exists(VC) or shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


needs_vc = pytest.mark.skipif(not _vc_available(), reason="official renderer not available")


@pytest.fixture(scope="module")
def synth_dir():
    base = Path("/work/pipeline")
    base.mkdir(parents=True, exist_ok=True)
    d = Path(tempfile.mkdtemp(prefix="pytest_canvas_", dir=str(base)))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _volume(d: Path, name: str, values: np.ndarray) -> Path:
    import zarr

    root = zarr.open_group(str(d / f"{name}.zarr"), mode="w")
    root.attrs["multiscales"] = [{"axes": [{"name": a, "type": "space"} for a in "zyx"],
                                  "datasets": [{"coordinateTransformations": [{"scale": [1.0, 1.0, 1.0],
                                                                               "type": "scale"}], "path": "0"}],
                                  "version": "0.4"}]
    a = root.create_dataset("0", shape=values.shape, chunks=(64, 64, 64), dtype="u2", compressor=None,
                            dimension_separator="/")
    a[:] = values.astype(np.uint16)
    return d / f"{name}.zarr"


def _render(vol: Path, mesh: Path, out: Path, *extra: str) -> np.ndarray:
    import zarr

    cmd = [VC, "vc_render_tifxyz", "-v", str(vol), "--segmentation", str(mesh), "--scale", "1",
           "--group-idx", "0", "--cache-gb", "1", "--zarr-output", str(out), *extra]
    env = dict(os.environ, VC_CPUS="2", OMP_NUM_THREADS="2")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
    assert r.returncode == 0, r.stderr[-2000:]
    return zarr.open(str(out / "0"), mode="r")[:].astype(np.float64)


@pytest.fixture(scope="module")
def synth(synth_dir):
    Z, Y, X = 64, 320, 320
    zz, yy, xx = np.meshgrid(np.arange(Z), np.arange(Y), np.arange(X), indexing="ij")
    vols = {k: _volume(synth_dir, k, v) for k, v in (("vx", 100 * xx), ("vy", 100 * yy), ("vz", 1000 * zz))}
    H, W = 10, 13
    vv, uu = np.mgrid[0:H, 0:W].astype(np.float64)
    # curved, sheared, tilted grid (non-uniform spacing) so offsets, axes and
    # bilinear interpolation are all exercised
    pts = np.stack([30 + 20 * uu + 4 * np.sin(0.7 * vv) + 0.02 * uu * vv,
                    20 + 18 * vv + 1.5 * uu,
                    30 + 0.6 * uu + 0.3 * vv + 0.05 * uu * vv], -1).astype(np.float32)
    mesh = write_tifxyz(synth_dir / "curved.tifxyz", TifxyzMesh(pts, (0.05, 0.05), "curved"))
    p2 = pts.copy()
    p2[:1] = -1
    p2[:, :2] = -1
    p2[:, -1] = -1
    p2[5, 6] = -1  # interior hole
    mesh_ac = write_tifxyz(synth_dir / "curved_ac.tifxyz", TifxyzMesh(p2, (0.05, 0.05), "curved_ac"))
    return dict(vols=vols, mesh=mesh, mesh_ac=mesh_ac, pts=pts, pts_ac=p2, dir=synth_dir)


def _check(render_x, render_y, pts, origin):
    cv = C.canvas_for(pts, (0.05, 0.05)).with_origin(*origin)
    co, no = C.emulate_gen(pts, cv, render_x.shape)
    val = C.render_valid(co, no)
    assert (val == (render_x > 0)).all()
    assert val.sum() > 1000
    # uint16 value = 100 * coordinate: quantisation 0.005 vox
    assert np.abs(co[..., 0][val] * 100 - render_x[val]).max() <= 1.0
    assert np.abs(co[..., 1][val] * 100 - render_y[val]).max() <= 1.0
    return co, no, val


@needs_vc
def test_official_full_canvas_convention(synth):
    s = synth
    rx = _render(s["vols"]["vx"], s["mesh"], s["dir"] / "rx.zarr", "-n", "1")[0]
    ry = _render(s["vols"]["vy"], s["mesh"], s["dir"] / "ry.zarr", "-n", "1")[0]
    assert rx.shape == C.canvas_for(s["pts"], (0.05, 0.05)).shape == (200, 260)
    co, no, val = _check(rx, ry, s["pts"], (0, 0))
    # the alternative "grid = P * s" (no half pixel) is off by ~0.5 vox = 50 value units
    alt = C.canvas_for(s["pts"], (0.05, 0.05)).with_origin(0, 0)
    v, u = alt.pixel_to_grid(100.0, 100.0)
    assert abs(u - 100.5 / 20) < 1e-5
    from hercules.geometry.tifxyz import sample_grid
    P = np.arange(rx.shape[1], dtype=float)
    Q = np.arange(rx.shape[0], dtype=float)
    naive = sample_grid(s["pts"], (Q * 0.05)[:, None], (P * 0.05)[None, :])
    assert np.median(np.abs(naive[..., 0][val] * 100 - rx[val])) > 40


@needs_vc
def test_official_manual_crop_origin(synth):
    s = synth
    crop = ["--crop-x", "37", "--crop-y", "11", "--crop-width", "100", "--crop-height", "80"]
    rx = _render(s["vols"]["vx"], s["mesh"], s["dir"] / "cx.zarr", "-n", "1", *crop)[0]
    ry = _render(s["vols"]["vy"], s["mesh"], s["dir"] / "cy.zarr", "-n", "1", *crop)[0]
    assert rx.shape == (80, 100)
    _check(rx, ry, s["pts"], (11, 37))


@needs_vc
def test_official_auto_crop_origin(synth):
    s = synth
    rx = _render(s["vols"]["vx"], s["mesh_ac"], s["dir"] / "ax.zarr", "-n", "1", "--auto-crop")[0]
    ry = _render(s["vols"]["vy"], s["mesh_ac"], s["dir"] / "ay.zarr", "-n", "1", "--auto-crop")[0]
    x, y, w, h = C.auto_crop_rect(s["pts_ac"], (0.05, 0.05))
    assert (x, y) == (39, 19) and rx.shape == (h, w)
    _check(rx, ry, s["pts_ac"], (y, x))


@needs_vc
@pytest.mark.parametrize("n,flip", [(5, False), (5, True), (4, False)])
def test_official_slices_and_flip(synth, n, flip):
    s = synth
    extra = ["-n", str(n)] + (["--flip-normals"] if flip else [])
    rz = _render(s["vols"]["vz"], s["mesh"], s["dir"] / f"z{n}{int(flip)}.zarr", *extra)
    cv = C.canvas_for(s["pts"], (0.05, 0.05))
    co, no = C.emulate_gen(s["pts"], cv, rz.shape[1:])
    val = C.render_valid(co, no)
    sign = C.slice_normal_sign(flip)
    for k, off in enumerate(C.slice_offsets(n)):
        pred = 1000 * (co[..., 2] + off * sign * no[..., 2])
        got = rz[k]
        assert (got > 0)[val].all()
        # trilinear on a linear ramp is exact up to uint16 quantisation
        assert np.abs(pred[val] - got[val]).max() <= 1.0, (k, off)
