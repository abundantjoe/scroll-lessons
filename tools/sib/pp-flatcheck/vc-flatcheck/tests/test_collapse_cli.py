import json

import numpy as np

import flatcheck as fc
from flatcheck.cli import main
from synth import STEP, cylinder_grid, sphere_grid


def test_collapse_detector():
    good = {"flipped_triangles": 0, "n_triangles_uv_undefined": 0, "area_scale_factor": 1.0}
    assert not fc.collapse_flags(good, 1.2)["collapsed"]
    assert fc.collapse_flags(good, 2.58)["collapsed"]
    assert fc.collapse_flags(good, 0.6)["collapsed"]
    assert fc.collapse_flags(dict(good, flipped_triangles=3))["collapsed"]
    assert fc.collapse_flags(dict(good, n_triangles_uv_undefined=1))["collapsed"]
    # a shrunken, un-rescaled map is caught through the area factor
    p = cylinder_grid(300.0, (20, 20), STEP, 0.0)
    uv, _ = fc.flatten(p, "slim", step=STEP)
    assert fc.collapse_flags(fc.metrics(p, uv / 2.6))["rescale_out_of_range"]
    # a real fold is detected end to end
    uv[10, 10] += np.array([60.0, 60.0])
    assert fc.collapse_flags(fc.metrics(p, uv))["flipped"]


def test_tifxyz_roundtrip(tmp_path):
    p = sphere_grid(1500.0, 12)
    p[0, 0] = -1.0
    fc.write_tifxyz(tmp_path / "m.tifxyz", p, step=STEP)
    q, meta = fc.read_tifxyz(tmp_path / "m.tifxyz")
    assert meta["scale"] == [1 / STEP, 1 / STEP]
    assert np.allclose(q, p.astype(np.float32))
    uv = fc.grid_uv(q, STEP)
    fc.write_uv(tmp_path / "u.tif", tmp_path / "v.tif", uv)
    uv2 = fc.read_uv(tmp_path / "u.tif", tmp_path / "v.tif")
    assert np.isnan(uv2[0, 0]).all() and np.allclose(uv2[1:, 1:], uv[1:, 1:])


def test_cli_report_and_flatten(tmp_path, capsys):
    p = sphere_grid(1000.0, 40)
    mesh = tmp_path / "m.tifxyz"
    fc.write_tifxyz(mesh, p, step=STEP)
    out = tmp_path / "r.json"
    assert main(["report", str(mesh), "--compare", "--json", str(out)]) == 0
    r = json.loads(out.read_text())
    assert set(r["results"]) == {"grid", "slim", "arap"}
    assert r["results"]["slim"]["metrics"]["edge_abs_log_ratio_mean"] < \
        r["results"]["grid"]["metrics"]["edge_abs_log_ratio_mean"]
    assert "SLIM".lower() in capsys.readouterr().out
    assert main(["flatten", str(mesh), "--method", "arap", "--out", str(tmp_path / "flat")]) == 0
    assert main(["report", str(mesh), "--uv", str(tmp_path / "flat/u.tif"), str(tmp_path / "flat/v.tif"),
                 "--rows", "0:20", "--cols", "5:", "--bar", "101", "--strict"]) == 1
