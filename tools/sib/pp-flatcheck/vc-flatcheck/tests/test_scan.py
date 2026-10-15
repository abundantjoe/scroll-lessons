import json

import numpy as np

import flatcheck as fc
from flatcheck.cli import main
from synth import STEP, plane_grid


def bump_grid(n_r=40, n_c=80, centre=(20, 60), amp=150.0, sigma=6.0):
    """Plane with a Gaussian bump (curved) at ``centre``: the only non-developable region."""
    p = plane_grid(n_r, n_c)
    r, c = np.mgrid[0:n_r, 0:n_c].astype(float)
    p[..., 2] += amp * np.exp(-((r - centre[0]) ** 2 + (c - centre[1]) ** 2) / (2 * sigma ** 2))
    return p


def test_worst_window_finds_the_bump():
    p = bump_grid()
    w = fc.worst_windows(p, 16, 16, k=2)
    assert len(w) == 2
    top = w[0]
    assert top["r0"] <= 20 <= top["r0"] + 16 and top["c0"] <= 60 <= top["c0"] + 16
    assert w[0]["mean_abs_angle_defect_deg"] > w[1]["mean_abs_angle_defect_deg"]
    # windows do not overlap
    a, b = w
    assert a["r0"] + 16 <= b["r0"] or b["r0"] + 16 <= a["r0"] or a["c0"] + 16 <= b["c0"] or b["c0"] + 16 <= a["c0"]


def test_windows_skip_holes():
    p = plane_grid(20, 20)
    p[5, 5] = -1.0
    for x in fc.worst_windows(p, 8, 8, k=10):
        assert not (x["r0"] <= 5 <= x["r0"] + 8 and x["c0"] <= 5 <= x["c0"] + 8)
    assert fc.worst_windows(p, 30, 30) == []


def test_cli_scan(tmp_path):
    mesh = tmp_path / "b.tifxyz"
    fc.write_tifxyz(mesh, bump_grid(), step=STEP)
    out = tmp_path / "s.json"
    assert main(["scan", str(mesh), "--window", "16", "16", "-k", "2", "--json", str(out)]) == 0
    r = json.loads(out.read_text())
    top = r["windows"][0]["results"]
    assert top["slim"]["pct_quads_within_5pct"] >= top["grid"]["pct_quads_within_5pct"]
    assert top["slim"]["fold_overs"] == 0
