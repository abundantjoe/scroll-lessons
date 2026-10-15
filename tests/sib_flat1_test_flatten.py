# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-1 unit tests (synthetic geometry only).

Run: PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python -m pytest -q tests/sib_flat1_test_flatten.py
"""

import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

import flatlib as FL
from hercules.geometry.render_synth import cylinder_grid

STEP = 20.0
REPO = Path(__file__).resolve().parents[1]


def plane_grid(n_r: int, n_c: int, step: float = STEP) -> np.ndarray:
    r, c = np.mgrid[0:n_r, 0:n_c].astype(float)
    # tilted plane in 3-D, isometric grid
    e1 = np.array([1.0, 0.0, 1.0]) / math.sqrt(2)
    e2 = np.array([0.0, 1.0, 0.0])
    return 500.0 + step * (c[..., None] * e1 + r[..., None] * e2)


def sphere_grid(R: float, n: int, step: float = STEP) -> np.ndarray:
    """Grid on a sphere of radius R: u = arc along the equator direction,
    v = latitude arc. Doubly curved, K = 1/R^2."""
    r, c = np.mgrid[0:n, 0:n].astype(float)
    a = (c - (n - 1) / 2) * step / R
    b = (r - (n - 1) / 2) * step / R
    p = np.stack([np.sin(a) * np.cos(b), np.sin(b), np.cos(a) * np.cos(b)], -1) * R
    return p + 2000.0


def flatten(p, method, init="grid"):
    m = FL.grid_to_mesh(p)
    UV0 = FL.grid_init_uv(m, STEP) if init == "grid" else FL.tutte_init_uv(m)
    if method == "slim":
        UV, _ = FL.flatten_slim(m.V, m.F, UV0)
    elif method == "arap":
        UV, _ = FL.flatten_arap(m.V, m.F, UV0)
    else:
        UV = UV0
    return FL.uv_to_grid(m, UV, p.shape[:2]), m


# --------------------------------------------------------------------------
# metric sanity
# --------------------------------------------------------------------------

def test_metric_identity_scale_and_stretch():
    p = plane_grid(20, 30)
    m = FL.grid_to_mesh(p)
    uv = FL.uv_to_grid(m, FL.grid_init_uv(m, STEP), p.shape[:2])
    e = FL.evaluate(p, uv, m.quads)
    assert e["pct_quads_within_5pct"] == 100.0 and e["pct_quads_within_1pct"] == 100.0
    assert e["flipped_triangles"] == 0
    assert e["angle_abs_err_deg"]["max"] < 1e-6
    # a pure global scale of 1.06 fails raw, passes after area normalisation
    e = FL.evaluate(p, uv * 1.06, m.quads)
    assert e["pct_quads_within_5pct_raw"] == 0.0
    assert e["pct_quads_within_5pct_norm"] == 100.0
    assert e["area_scale_factor"] == pytest.approx(1 / 1.06, rel=1e-9)
    # anisotropic 6 % stretch is real distortion: fails whatever the scale
    uv2 = uv.copy()
    uv2[..., 0] *= 1.12
    e = FL.evaluate(p, uv2, m.quads)
    assert e["pct_quads_within_5pct"] == 0.0
    assert e["area_ratio"]["p50"] == pytest.approx(1.0, abs=1e-9)


def test_metric_counts_undefined_uv_as_failing_and_flips():
    p = plane_grid(10, 10)
    m = FL.grid_to_mesh(p)
    uv = FL.uv_to_grid(m, FL.grid_init_uv(m, STEP), p.shape[:2])
    uv[4, 4] = np.nan  # 4 quads touch vertex (4, 4)
    e = FL.evaluate(p, uv, m.quads)
    assert e["pct_quads_within_5pct"] == pytest.approx(100.0 * (81 - 4) / 81)
    uv = FL.uv_to_grid(m, FL.grid_init_uv(m, STEP), p.shape[:2])
    uv[4, 4] = uv[4, 4] + np.array([30.0, 30.0])  # fold the vertex over its neighbours
    e = FL.evaluate(p, uv, m.quads)
    assert e["flipped_triangles"] > 0


# --------------------------------------------------------------------------
# required: developable cylinder >= 99.9 % of quads within +-1 %
# --------------------------------------------------------------------------

@pytest.mark.parametrize("angle", [0.0, 30.0])
@pytest.mark.parametrize("method", ["slim", "arap"])
def test_cylinder_developable(method, angle):
    # radius 300 vox (2.8 mm at 9.362 um: a tight inner winding), 60 x 60 quads,
    # grid rotated by `angle` relative to the generators (non-planar quads at 30 deg)
    p = cylinder_grid(300.0, (400.0, 400.0), (60, 60), STEP, angle, s0=-600.0, z0=100.0)
    for init in ("grid", "tutte"):
        uv, m = flatten(p, method, init)
        e = FL.evaluate(p, uv, m.quads)
        assert e["pct_quads_within_1pct"] >= 99.9, (method, angle, init, e["pct_quads_within_1pct"])
        assert e["flipped_triangles"] == 0
        assert e["area_scale_factor"] == pytest.approx(1.0, abs=2e-3)


# --------------------------------------------------------------------------
# required: doubly curved patch shows the expected distortion
# --------------------------------------------------------------------------

def test_sphere_gauss_bonnet():
    """Angle defects sum to integral K dA = A / R^2 (the intrinsic reason no
    flattening can be isometric)."""
    import flat1_run as RUN

    for R in (1000.0, 3000.0):
        p = sphere_grid(R, 60)
        g = RUN.geometry_diagnostics(p)
        # interior vertices only: compare with the area of the interior region
        # (one quad ring less); tolerance covers the boundary ring and chord effects
        assert g["sum_angle_defect_rad"] == pytest.approx(g["area_vox2"] / R**2, rel=0.08)
    pc = cylinder_grid(300.0, (400.0, 400.0), (60, 60), STEP, 30.0, s0=-600.0, z0=100.0)
    gc = RUN.geometry_diagnostics(pc)
    assert abs(gc["sum_angle_defect_rad"]) < 1e-3 * gc["area_vox2"] / 1000.0**2


@pytest.mark.parametrize("method", ["slim", "arap"])
def test_sphere_expected_distortion(method):
    n = 60
    L = (n - 1) * STEP
    prev = None
    for R in (6000.0, 3000.0, 1000.0):
        p = sphere_grid(R, n)
        uv, m = flatten(p, method)
        e = FL.evaluate(p, uv, m.quads)
        er = e["edge_ratio_pctl"]
        spread = max(er["99.5"] - 1.0, 1.0 - er["0.5"])
        # scale of the unavoidable metric error of a flat map of a geodesic square of
        # half-side a = L/2: the latitude grid's own strain is 1 - cos(a/R) ~ a^2/(2R^2);
        # a distortion-minimising map spreads it over +- and so stays below it, but it
        # cannot vanish (Theorema egregium): expected within [1/8, 1] of that strain.
        s_grid = 1.0 - math.cos(L / 2 / R)
        assert s_grid / 8 <= spread <= s_grid, (R, spread, s_grid)
        assert e["flipped_triangles"] == 0
        # distortion measure is monotone in curvature
        if prev is not None:
            assert e["pct_quads_within_1pct"] <= prev + 1e-9
        prev = e["pct_quads_within_1pct"]
    # the strongly curved patch cannot meet the developable bar
    assert prev < 50.0


def test_sphere_slim_beats_grid():
    p = sphere_grid(1000.0, 60)
    uv_s, m = flatten(p, "slim")
    uv_g, _ = flatten(p, "grid")
    es, eg = FL.evaluate(p, uv_s, m.quads), FL.evaluate(p, uv_g, m.quads)
    assert es["sym_dirichlet_area_weighted"] < eg["sym_dirichlet_area_weighted"]
    assert es["edge_abs_log_ratio_mean"] < eg["edge_abs_log_ratio_mean"]


# --------------------------------------------------------------------------
# rectangle rule
# --------------------------------------------------------------------------

def test_rectangle_rule_deterministic_and_valid():
    vox = 9.362
    p = cylinder_grid(2000.0, (0.0, 0.0), (220, 300), STEP, 0.0, s0=0.0, z0=100.0)
    p[40:60, 100:180] = -1.0  # hole
    r1 = FL.choose_rectangle(p, vox, STEP, np.random.default_rng([1, 2]))
    r2 = FL.choose_rectangle(p, vox, STEP, np.random.default_rng([1, 2]))
    assert r1 == r2
    assert abs(r1["area_cm2"] - 4.0) <= 0.04
    assert 1.0 <= r1["aspect"] <= 2.0
    q = FL.quad_mask(p)[r1["r0"]:r1["r0"] + r1["h_quads"], r1["c0"]:r1["c0"] + r1["w_quads"]]
    assert q.all() and q.shape == (r1["h_quads"], r1["w_quads"])
    # a mesh that is too small has no rectangle
    assert FL.choose_rectangle(p[:50, :50], vox, STEP, np.random.default_rng(0)) is None


# --------------------------------------------------------------------------
# official ABF++ (needs docker + the built driver; skipped otherwise)
# --------------------------------------------------------------------------

ABF_BIN = Path("/work/flat1/bin/abf_uv_dump")


@pytest.mark.skipif(not (ABF_BIN.exists() and shutil.which("docker")), reason="official ABF++ driver not built")
def test_abf_cylinder_developable(tmp_path):
    import tifffile

    from hercules.geometry import tifxyz as T

    p = cylinder_grid(300.0, (400.0, 400.0), (60, 60), STEP, 30.0, s0=-600.0, z0=100.0)
    d = Path("/work/flat1/test_tmp") / "cyl"
    T.write_tifxyz(d, T.TifxyzMesh(points=p.astype(np.float32), scale=(0.05, 0.05), uuid="cyl"), overwrite=True)
    out = d.parent / "cyl_uv"
    r = subprocess.run([str(REPO / "tools/sib/flat1/run_abf.sh"), str(d), str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]
    uv = np.stack([tifffile.imread(out / "u.tif"), tifffile.imread(out / "v.tif")], -1).astype(np.float64)
    m = FL.grid_to_mesh(p)
    e = FL.evaluate(p, uv, m.quads)
    assert e["pct_quads_within_1pct"] >= 99.9
    assert e["flipped_triangles"] == 0


# --------------------------------------------------------------------------
# fallback trimming rule: never trims inside R, reports before/after
# --------------------------------------------------------------------------

def test_fallback_never_trims_R():
    import flat1_run as RUN

    lev = sphere_grid(1500.0, 80)
    rect = {"r0": 20, "c0": 20, "h_quads": 40, "w_quads": 40}
    fb = RUN.fallback(lev, rect, 9.362, float("nan"))
    assert fb["margin_quads"] == math.ceil(2000.0 / (20 * 9.362))
    for rd in fb["rounds"]:
        assert rd["metrics_R"]["n_quads"] == 40 * 40  # R intact in every round
    assert fb["rounds"][0]["n_margin_quads"] > 0
    assert fb["before_pct"] == fb["rounds"][0]["pct_R_within_5pct"]
    assert fb["after_pct"] == fb["rounds"][-1]["pct_R_within_5pct"]
