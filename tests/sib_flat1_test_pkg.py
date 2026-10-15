# Provenance: Project HERCULES | owner the owner | [id removed]
"""flatpkg tests (FLAT-2 B). Run:
PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python -m pytest -q tests/sib_flat1_test_pkg.py
"""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
import tifffile

import flatpkg as P
from hercules.geometry.render_synth import cylinder_grid


def cyl(n=40):
    return cylinder_grid(300.0, (400.0, 400.0), (n, n), 20.0, 30.0, s0=-400.0, z0=100.0)


def docker_ok():
    return Path("/work/flat1/bin/abf_uv_dump").exists() and shutil.which("docker") and \
        subprocess.run(["docker", "info"], capture_output=True).returncode == 0


@pytest.mark.parametrize("method", ["slim", "arap"])
def test_flatten_cylinder(method):
    p = cyl()
    r = P.flatten(p, method)
    m = P.metrics(p, r.uv)
    assert m["pct_quads_within_1pct"] >= 99.9 and m["flipped_triangles"] == 0
    assert not P.collapse_flags(m, r.info)["collapsed"]


@pytest.mark.skipif(not docker_ok(), reason="official ABF++ driver / docker unavailable")
def test_vc_flatten_cylinder(tmp_path):
    p = cyl()
    r = P.flatten(p, "vc_flatten", workdir=tmp_path)
    m = P.metrics(p, r.uv)
    assert m["pct_quads_within_1pct"] >= 99.9
    f = P.collapse_flags(m, r.info)
    assert not f["collapsed"] and abs(f["abf_rescale_factor"] - 1) < 0.1


def test_collapse_detector():
    good = {"flipped_triangles": 0, "n_triangles_uv_undefined": 0}
    assert not P.collapse_flags(good, {"abf_rescale_factor": 1.2})["collapsed"]
    assert P.collapse_flags(good, {"abf_rescale_factor": 2.58})["collapsed"]
    assert P.collapse_flags(good, {"abf_rescale_factor": 0.6})["collapsed"]
    assert P.collapse_flags({"flipped_triangles": 3, "n_triangles_uv_undefined": 0})["collapsed"]
    assert P.collapse_flags({"flipped_triangles": 0, "n_triangles_uv_undefined": 1})["collapsed"]
    # a real fold is detected end to end
    p = cyl(20)
    r = P.flatten(p, "slim")
    uv = r.uv.copy()
    uv[10, 10] += np.array([60.0, 60.0])
    assert P.collapse_flags(P.metrics(p, uv))["flipped"]


def test_package_round_trip_and_verifier(tmp_path):
    p = cyl()
    r = P.flatten(p, "slim")
    rec = P.write_package(tmp_path / "pkg", p, r.uv, method="slim", voxel_um=9.362, info=r.info)
    pk = P.read_package(tmp_path / "pkg")
    assert np.array_equal(pk["points"], p.astype(np.float32))
    assert np.array_equal(pk["uv"], r.uv.astype(np.float32).astype(np.float64))
    assert rec["metrics"]["pct_quads_within_5pct"] == 100.0
    ok, rep = P.verify_package(tmp_path / "pkg")
    assert ok, rep
    # tamper with one UV value: sha and metrics both catch it
    u = tifffile.imread(tmp_path / "pkg" / "u.tif")
    u[5, 5] += 3.0
    tifffile.imwrite(str(tmp_path / "pkg" / "u.tif"), u, photometric="minisblack", metadata=None)
    ok, rep = P.verify_package(tmp_path / "pkg")
    assert not ok and "u.tif" in rep["sha_mismatch"] and not rep["metrics_equal"]


def test_verifier_catches_record_edit(tmp_path):
    p = cyl(20)
    r = P.flatten(p, "arap")
    P.write_package(tmp_path / "pkg", p, r.uv, method="arap")
    f = tmp_path / "pkg" / "flat_record.json"
    rec = json.loads(f.read_text())
    rec["metrics"]["pct_quads_within_5pct"] = 99.0
    f.write_text(json.dumps(rec))
    ok, rep = P.verify_package(tmp_path / "pkg")
    assert not ok and not rep["metrics_equal"] and rep["diff_keys"] == ["pct_quads_within_5pct"]


def test_package_undefined_uv(tmp_path):
    p = cyl(20)
    r = P.flatten(p, "slim")
    uv = r.uv.copy()
    uv[3, 3] = np.nan
    rec = P.write_package(tmp_path / "pkg", p, uv, method="slim")
    assert rec["collapse"]["undefined_uv"] and rec["collapse"]["collapsed"]
    assert P.verify_package(tmp_path / "pkg")[0]
