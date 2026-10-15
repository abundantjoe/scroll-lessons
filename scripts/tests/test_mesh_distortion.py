"""RULES G-GP: the mesh parameterisation metric, and the matched-baseline mode that part 2 turned on."""
import importlib.util, json, os, sys
import numpy as np, pytest, tifffile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location(
    "mesh_distortion", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mesh_distortion.py"))
md = importlib.util.module_from_spec(spec); spec.loader.exec_module(md)

UM = 9.362


def write_grid(d, P, scale=0.05):
    os.makedirs(d, exist_ok=True)
    for i, n in enumerate("xyz"):
        tifffile.imwrite(os.path.join(d, n + ".tif"), P[..., i].astype(np.float32))
    json.dump({"scale": [scale, scale], "format": "tifxyz"}, open(os.path.join(d, "meta.json"), "w"))
    return d


def plane(rows, cols, step, x0=1000.0):
    """A flat, uniformly spaced grid at node spacing `step` voxels (all coordinates > 0 so valid_mask passes)."""
    u, v = np.meshgrid(np.arange(cols) * step, np.arange(rows) * step)
    return np.stack([x0 + u, x0 + v, np.full_like(u, 500.0)], -1)


def test_flat_uniform_grid_is_isometric_conformal_and_flat(tmp_path):
    r = md.measure(write_grid(str(tmp_path / "flat"), plane(40, 40, 20.0)), UM)
    assert r["stretch_median"] == pytest.approx(1.0, abs=1e-6)
    assert r["anisotropy_median"] == pytest.approx(1.0, abs=1e-6)
    assert r["shear_median"] == pytest.approx(0.0, abs=1e-6)
    assert r["sag_um_median"] == pytest.approx(0.0, abs=1e-6)


def test_a_grid_stretched_along_u_reports_the_stretch_and_the_anisotropy(tmp_path):
    P = plane(40, 40, 20.0)
    P[..., 0] = 1000.0 + (P[..., 0] - 1000.0) * 2.0        # double the spacing along u only
    r = md.measure(write_grid(str(tmp_path / "stretched"), P), UM)
    assert r["anisotropy_median"] == pytest.approx(2.0, rel=1e-6)
    assert r["stretch_p90"] == pytest.approx(2.0, rel=1e-6)


def test_sag_is_reported_in_micrometres(tmp_path):
    """A +-2 voxel checkerboard in z: every node sits 4 voxels off its four neighbours' plane, so sag = 4 * um.

    A single bumped node would not show in a percentile -- five nodes of 1521 -- which is the metric behaving
    correctly, not a defect: sag is a distribution over the grid, never a worst-case detector.
    """
    P = plane(41, 41, 20.0)
    i, j = np.indices(P.shape[:2])
    P[..., 2] += 2.0 * np.where((i + j) % 2 == 0, 1.0, -1.0)
    r = md.measure(write_grid(str(tmp_path / "checker"), P), UM)
    assert r["sag_um_median"] == pytest.approx(4.0 * UM, rel=1e-3)   # the report rounds to 2 dp
    assert r["sag_um_p90"] == pytest.approx(4.0 * UM, rel=1e-3)


def test_a_single_bumped_node_does_not_move_the_percentiles(tmp_path):
    P = plane(41, 41, 20.0)
    P[20, 20, 2] += 4.0
    r = md.measure(write_grid(str(tmp_path / "bump"), P), UM)
    assert r["sag_um_p90"] == pytest.approx(0.0, abs=1e-9)


def test_matched_baseline_makes_two_densities_of_the_same_surface_agree(tmp_path):
    """The confound G-GP part 2 turned on: raw sag shrinks with node spacing, matched-baseline sag does not.

    Same smooth cylinder sampled at a 20-voxel spacing and at a 5-voxel spacing. Raw p90 sag must differ a lot
    (roughly as the square of the spacing); at a matched physical baseline the two must agree closely.
    """
    def cyl(rows, cols, step, R=800.0):
        v, u = np.meshgrid(np.arange(cols) * step, np.arange(rows) * step, indexing="xy")
        th = u / R
        return np.stack([2000.0 + R * np.cos(th), 2000.0 + R * np.sin(th), 500.0 + v], -1)

    coarse = write_grid(str(tmp_path / "c"), cyl(60, 60, 20.0))
    fine = write_grid(str(tmp_path / "f"), cyl(240, 240, 5.0))
    rc, rf = md.measure(coarse, UM), md.measure(fine, UM)
    assert rf["sag_um_p90"] < rc["sag_um_p90"] / 4          # raw sag: the denser grid looks far better
    bc = md.measure(coarse, UM, baseline_um=20.0 * UM)
    bf = md.measure(fine, UM, baseline_um=20.0 * UM)
    assert bf["stride_nodes"] == 4 and bc["stride_nodes"] == 1
    assert bf["sag_um_p90"] == pytest.approx(bc["sag_um_p90"], rel=0.10)


def test_a_grid_too_small_for_the_stride_returns_none(tmp_path):
    assert md.measure(write_grid(str(tmp_path / "tiny"), plane(2, 2, 20.0)), UM) is None
    small = write_grid(str(tmp_path / "small"), plane(9, 9, 20.0))
    assert md.measure(small, UM, baseline_um=20.0 * 9.362 * 8) is None   # stride 8 needs 17 rows
