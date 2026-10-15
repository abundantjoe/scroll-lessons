# Provenance: Project HERCULES | owner the owner | [id removed]
"""p4_package tests on synthetic tifxyz meshes (no Paris 4 data)."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

import p4_package as PK
from hercules.geometry import tifxyz as T
from hercules.geometry.render_synth import cylinder_grid


def docker_ok():
    return Path("/work/flat1/bin/abf_uv_dump").exists() and shutil.which("docker") and \
        subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def make_mesh(d: Path, hole=True):
    p = cylinder_grid(2000.0, (0.0, 0.0), (300, 400), 20.0, 10.0, s0=0.0, z0=100.0).astype(np.float32)
    if hole:
        p[120:125, 150:160] = -1.0
    T.write_tifxyz(d, T.TifxyzMesh(points=p, scale=(0.05, 0.05), uuid="syn"), overwrite=True)
    return p


def test_crop_indices_rule():
    c = PK.crop_indices(2000, 100.0, 1, 2, (300, 400))
    # tile rows canvas [2000, 4000) -> grid [100, 200); margin 1000 px = 50 grid
    assert (c["r0"], c["r1"], c["c0"], c["c1"]) == (50, 250, 150, 350)
    q = PK.tile_quad_mask(c, 2000, 1, 2, (c["r1"] - c["r0"], c["c1"] - c["c0"]))
    assert q.sum() == 100 * 100


@pytest.mark.parametrize("methods", [("slim",), ("vc_flatten", "slim")])
def test_package_synthetic(methods):
    if "vc_flatten" in methods and not docker_ok():
        pytest.skip("docker / ABF driver unavailable")
    base = Path("/work/flat1/test_tmp/p4pkg") / "_".join(methods)
    shutil.rmtree(base, ignore_errors=True)
    make_mesh(base / "mesh.tifxyz")
    rec = PK.package(base / "mesh.tifxyz", 2000, 100.0, 1, 1, base / "out", voxel_um=2.4, methods=methods)
    assert 9900 <= rec["n_quads_tile"] <= 10000
    for m in methods:
        v = rec["methods"][m]
        assert v["package_verified"]
        assert v["tile"]["pct_quads_within_1pct"] >= 99.9  # developable synthetic sheet
        assert v["passes_bar_tile"] and not v["collapse"]["collapsed"]
    assert json.loads((base / "out" / "p4_package_record.json").read_text())["tile"] == [1, 1]
