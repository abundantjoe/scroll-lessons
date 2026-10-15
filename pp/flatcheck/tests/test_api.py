import json
import subprocess
import sys

import numpy as np
import pytest
import tifffile

import flatcheck as P
from flatcheck import report, tifxyz
from conftest import abf, cylinder_grid


def cyl(n=40):
    return cylinder_grid(300.0, (400.0, 400.0), (n, n), 20.0, 30.0, s0=-400.0, z0=100.0)


@pytest.mark.parametrize("method", ["slim", "arap"])
def test_flatten_cylinder(method):
    p = cyl()
    r = P.flatten(p, method)
    m = P.metrics(p, r.uv)
    assert m["pct_quads_within_1pct"] >= 99.9 and not P.collapse_flags(m, r.info)["collapsed"]


@abf
def test_vc_flatten_cylinder():
    p = cyl()
    r = P.flatten(p, "vc_flatten")
    m = P.metrics(p, r.uv)
    assert m["pct_quads_within_1pct"] >= 99.9 and not P.collapse_flags(m, r.info)["collapsed"]


def test_collapse_detector():
    good = {"flipped_triangles": 0, "n_triangles_uv_undefined": 0}
    assert not P.collapse_flags(good, {"abf_rescale_factor": 1.2})["collapsed"]
    assert P.collapse_flags(good, {"abf_rescale_factor": 2.58})["collapsed"]
    assert P.collapse_flags(good, {"abf_rescale_factor": 0.6})["collapsed"]
    assert P.collapse_flags({"flipped_triangles": 3, "n_triangles_uv_undefined": 0})["collapsed"]
    assert P.collapse_flags({"flipped_triangles": 0, "n_triangles_uv_undefined": 1})["collapsed"]


def test_package_round_trip_and_tamper(tmp_path):
    p = cyl()
    r = P.flatten(p, "slim")
    rec = P.write_package(tmp_path / "pkg", p, r.uv, method="slim", info=r.info)
    pk = P.read_package(tmp_path / "pkg")
    assert np.array_equal(pk["points"], p.astype(np.float32))
    assert rec["metrics"]["pct_quads_within_5pct"] == 100.0
    assert P.verify_package(tmp_path / "pkg")[0]
    u = tifffile.imread(tmp_path / "pkg" / "u.tif")
    u[5, 5] += 3.0
    tifffile.imwrite(str(tmp_path / "pkg" / "u.tif"), u, photometric="minisblack", metadata=None)
    ok, rep = P.verify_package(tmp_path / "pkg")
    assert not ok and "u.tif" in rep["sha_mismatch"] and not rep["metrics_equal"]


def test_record_edit_caught(tmp_path):
    p = cyl(20)
    r = P.flatten(p, "arap")
    P.write_package(tmp_path / "pkg", p, r.uv, method="arap")
    f = tmp_path / "pkg" / "flat_record.json"
    rec = json.loads(f.read_text())
    rec["metrics"]["pct_quads_within_5pct"] = 99.0
    f.write_text(json.dumps(rec))
    ok, rep = P.verify_package(tmp_path / "pkg")
    assert not ok and rep["diff_keys"] == ["pct_quads_within_5pct"]


def test_tifxyz_round_trip(tmp_path):
    p = cyl(30).astype(np.float32)
    p[3:5, 3:5] = -1
    for comp in (None, "zlib"):
        d = tifxyz.write(tmp_path / f"t_{comp}", tifxyz.Tifxyz(p, (0.05, 0.05), "t"), compression=comp)
        t = tifxyz.read(d)
        assert np.array_equal(t.points, p) and t.step_vox == (20.0, 20.0)
        assert json.loads((d / "meta.json").read_text())["format"] == "tifxyz"


def test_grid_report():
    p = cyl(60)
    r = report.grid_report(p, 20.0, tile=20)
    assert r["pct_quads_within_tol_raw"] == 100.0 and r["fold_triangles"] == 0 and r["tiles_summary"]["n_tiles"] == 9
    q = p.copy()
    q[30, 30, 0] += 300.0  # a spike: folds + failing quads
    r2 = report.grid_report(q, 20.0)
    assert r2["fold_triangles"] > 0 and r2["pct_quads_within_tol_raw"] < 100.0
    q = p * np.array([1.08, 1.0, 1.0]) + np.array([0, 0, 0])  # anisotropic stretch fails
    assert report.grid_report(p * 1.2, 20.0)["pct_quads_within_tol_raw"] == 0.0
    assert report.grid_report(p * 1.2, 20.0)["pct_quads_within_tol_norm"] == 100.0


def test_cli(tmp_path):
    p = cyl(50).astype(np.float32)
    d = tifxyz.write(tmp_path / "m.tifxyz", tifxyz.Tifxyz(p, (0.05, 0.05), "m"))
    r = subprocess.run([sys.executable, "-m", "flatcheck.cli", "report", str(d), "--json", str(tmp_path / "r.json")],
                       capture_output=True, text=True)
    assert r.returncode == 0 and json.loads((tmp_path / "r.json").read_text())["pct_quads_within_tol_raw"] == 100.0
    r = subprocess.run([sys.executable, "-m", "flatcheck.cli", "flatten", str(d), "--out", str(tmp_path / "o"),
                        "--rect", "5", "5", "30", "30"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    res = json.loads((tmp_path / "o" / "flatcheck_result.json").read_text())
    assert all(v["package_verified"] for v in res["methods"].values())
    r = subprocess.run([sys.executable, "-m", "flatcheck.cli", "verify", str(tmp_path / "o" / "slim")],
                       capture_output=True, text=True)
    assert r.returncode == 0
