# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for tools/sib/contam/contam3d.py on synthetic sheets.

Run: PYTHONPATH=src pytest -q tests/sib_contam_test_core.py
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "sib" / "contam"))
import contam3d as C  # noqa: E402

from hercules.geometry import tifxyz as T  # noqa: E402
from hercules.geometry.render_synth import cylinder_grid  # noqa: E402

R = 300.0
CEN = (400.0, 400.0)
SC = (0.05, 0.05)  # 20 vox grid step, as the official 9.362 um meshes


def sheet(radius=R, shape=(12, 12), s0=0.0, z0=100.0, angle=0.0, step=20.0, centre=CEN):
    return cylinder_grid(radius, centre, shape, step, angle, s0=s0, z0=z0)


def ds(g, k=5, rect=None, name=""):
    return C.dense_surface(g, SC, k, rect_px=rect, name=name)


# ---------------------------------------------------------------------------
# sampling bound and densification
# ---------------------------------------------------------------------------

def test_quad_sampling_bound_is_rigorous_on_twisted_quads():
    rng = np.random.default_rng(0)
    for _ in range(50):
        g = rng.normal(0, 10, (2, 2, 3))
        g[0, 1] += (20, 0, 0)
        g[1, 0] += (0, 20, 0)
        g[1, 1] += (20, 20, 0)
        h = C.quad_sampling_bound(g)
        st = rng.random((4000, 2))
        pts = T.sample_grid(g, st[:, 0], st[:, 1])
        corners = g.reshape(-1, 3).astype(np.float64)
        d = np.min(np.linalg.norm(pts[:, None, :] - corners[None], axis=-1), axis=1)
        assert d.max() <= h + 1e-9


def test_dense_surface_covers_the_bilinear_surface_within_h():
    g = sheet(shape=(8, 9), angle=17.0)
    D = ds(g, 5)
    assert D.k == 5 and D.n == (7 * 5 + 1) * (8 * 5 + 1)
    # spacing ~4 vox -> half-diagonal ~2.83; h must be at least that and small
    assert 2.8 <= D.h <= 3.2
    rng = np.random.default_rng(1)
    rows, cols = rng.random(20000) * 7, rng.random(20000) * 8
    true = T.sample_grid(g, rows, cols)
    d, _ = cKDTree(D.points).query(true)
    assert d.max() <= D.h + 1e-6
    # canvas mapping: canvas px = grid index / scale
    i = np.argmin(np.linalg.norm(D.points - g[3, 4].astype(np.float64), axis=1))
    assert np.allclose(D.canvas[i], [4 / 0.05, 3 / 0.05])
    # area weights integrate to the mesh area
    assert D.area.sum() == pytest.approx(T.area_vox2(g), rel=0.03)


def test_rect_selection_is_a_superset_of_the_rect_surface():
    g = sheet(shape=(15, 15))
    rect = [55, 75, 190, 161]  # canvas px, deliberately off-grid
    D = ds(g, 5, rect=rect)
    rng = np.random.default_rng(2)
    xs = rng.uniform(rect[0], rect[2] - 1, 5000)
    ys = rng.uniform(rect[1], rect[3] - 1, 5000)
    true = T.sample_grid(g, ys * SC[1], xs * SC[0])
    d, _ = cKDTree(D.points).query(true)
    assert d.max() <= D.h + 1e-6
    # and it is not the whole sheet
    assert D.n < ds(g, 5).n / 4


# ---------------------------------------------------------------------------
# same-papyrus rule (normal distance)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def base():
    return ds(sheet(), 5, name="base")


def test_retrace_on_other_grid_is_same(base):
    a = sheet(shape=(12, 12), s0=70.0, z0=104.3, angle=12.0)
    A = ds(a, 5)
    A.points = A.points + np.random.default_rng(7).normal(0, 0.3, A.points.shape)
    r = C.same_papyrus_nd(A, base)
    assert r.same and r.n_within_2 >= 1000 and r.counts[0] >= 2 * r.counts[2]
    assert r.nd_median < 0.6
    assert 0.3 < r.frac_of_a < 0.9


@pytest.mark.parametrize("dr", [8.0, 25.0])
def test_parallel_sheet_or_adjacent_winding_is_not_same(base, dr):
    r = C.same_papyrus_nd(ds(sheet(radius=R + dr), 5), base)
    assert not r.same and r.counts == (0, 0, 0)


def test_parallel_sheet_2p5_vox_fails_the_ratio(base):
    r = C.same_papyrus_nd(ds(sheet(radius=R + 2.5), 5), base)
    assert r.counts[0] == 0 and r.counts[2] > 1000 and not r.same


def test_crossing_sheet_is_not_same(base):
    # a plane crossing the base sheet at 30 deg along the vertical line s = 105
    phi = 105.0 / R
    p0 = np.array([CEN[0] + R * np.cos(phi), CEN[1] + R * np.sin(phi), 100.0])
    t = np.array([-np.sin(phi), np.cos(phi), 0.0])
    n = np.array([np.cos(phi), np.sin(phi), 0.0])
    e1 = np.cos(np.radians(30)) * t + np.sin(np.radians(30)) * n
    vv, uu = np.mgrid[0:12, -6:6].astype(np.float64)
    plane = p0 + 20.0 * uu[..., None] * e1 + 20.0 * vv[..., None] * np.array([0, 0, 1.0])
    cross = ds(plane.astype(np.float32), 5)
    r = C.same_papyrus_nd(cross, base)
    assert r.n_within_2 > 0  # it does touch
    assert not r.same


def test_small_overlap_below_1000_points_is_not_same(base):
    # a 2 x 2-quad re-trace: ~40 x 40 vox = ~121 samples < 1000
    r = C.same_papyrus_nd(ds(sheet(shape=(3, 3), s0=40.0, z0=140.0), 5), base)
    assert r.counts[0] > 50 and r.n_within_2 < 1000 and not r.same


def test_verdict_is_density_independent():
    a, b = sheet(shape=(10, 10), s0=50.0, z0=103.0, angle=8.0), sheet(shape=(10, 10))
    r5 = C.same_papyrus_nd(ds(a, 5), ds(b, 5))
    r20 = C.same_papyrus_nd(ds(a, 20), ds(b, 20))
    assert r5.same and r20.same
    assert r5.frac_of_a == pytest.approx(r20.frac_of_a, abs=0.03)
    assert r5.area_within_2_vox2 == pytest.approx(r20.area_within_2_vox2, rel=0.05)


def test_prefiltered_pair_equals_full_test(base):
    ga, gb = sheet(shape=(12, 12), s0=70.0, z0=104.3, angle=12.0), sheet()
    A, B = ds(ga, 5), ds(gb, 5)
    ra, rb = C.raw_vertices(ga), C.raw_vertices(gb)
    pr = C.pair_same_papyrus(A, B, ra, rb, C.quad_sampling_bound(ga), C.quad_sampling_bound(gb))
    full_ab, full_ba = C.same_papyrus_nd(A, B), C.same_papyrus_nd(B, A)
    assert pr.ab.counts == full_ab.counts and pr.ba.counts == full_ba.counts
    assert pr.ab.frac_of_a == pytest.approx(full_ab.frac_of_a)
    assert pr.same


# ---------------------------------------------------------------------------
# papyrus units: geometry only, never names
# ---------------------------------------------------------------------------

def _unit_fixture():
    g = {
        "s1": sheet(),
        "s1_retrace": sheet(s0=90.0, z0=97.0, angle=-9.0),
        "s2_next_winding": sheet(radius=R + 30.0),
        "s2_retrace": sheet(radius=R + 30.0, s0=-80.0, z0=120.0, angle=5.0),
        "s3_far": sheet(radius=R + 30.0, z0=100.0 + 400.0),
    }
    return g


def _units(grids):
    dense = {n: ds(v, 5, name=n) for n, v in grids.items()}
    raw = {n: C.raw_vertices(v) for n, v in grids.items()}
    hr = {n: C.quad_sampling_bound(v) for n, v in grids.items()}
    pairs = C.pairwise_same_papyrus(dense, raw, hr)
    return C.papyrus_units(list(grids), pairs), pairs


def test_papyrus_units_group_retraces_and_split_windings():
    units, pairs = _units(_unit_fixture())
    assert units == [["s1", "s1_retrace"], ["s2_next_winding", "s2_retrace"], ["s3_far"]]
    # the far sheet is screened out; adjacent windings are tested and NOT same
    tested = {(p.a, p.b) for p in pairs}
    assert ("s1", "s2_next_winding") in tested
    assert not any(p.same for p in pairs if {p.a, p.b} == {"s1", "s2_next_winding"})


def test_papyrus_units_ignore_names():
    g = _unit_fixture()
    rename = {"s1": "zz9", "s1_retrace": "aa1", "s2_next_winding": "mm5", "s2_retrace": "w045", "s3_far": "w046"}
    units, _ = _units({rename[k]: v for k, v in g.items()})
    back = {v: k for k, v in rename.items()}
    assert sorted(sorted(back[m] for m in u) for u in units) == \
        [["s1", "s1_retrace"], ["s2_next_winding", "s2_retrace"], ["s3_far"]]


# ---------------------------------------------------------------------------
# clearance certificate (fold / shell)
# ---------------------------------------------------------------------------

def test_clearance_catches_a_window_retraced_by_a_training_segment():
    train = ds(sheet(shape=(6, 6), s0=0.0, z0=100.0), 5, name="train")
    # evaluation window on ANOTHER trace of the same papyrus (re-trace grid)
    region = ds(sheet(shape=(12, 12), s0=-30.0, z0=90.0, angle=7.0), 5, rect=[0, 0, 100, 100])
    cert = C.clearance(region, {"p0": train})
    assert not cert.passed
    assert cert.raw_min < 2.0
    assert cert.per_patch["p0"]["n_offending"] > 0
    assert cert.offending and cert.offending[0]["patch"] == "p0"
    assert set(cert.offending[0]) >= {"dist", "train_xyz", "region_xyz", "train_canvas_px", "region_canvas_px"}


def test_clearance_covers_all_windings():
    train = {"p": ds(sheet(), 5)}
    for dr, ok in ((30.0, False), (100.0, False), (140.0, True)):
        region = ds(sheet(radius=R + dr), 5)
        cert = C.clearance(region, train)
        assert cert.passed is ok, (dr, cert.raw_min, cert.certified_min)


def test_certified_min_is_a_true_lower_bound():
    rng = np.random.default_rng(5)
    for _ in range(5):
        dr = rng.uniform(128, 140)
        a = sheet(radius=R + dr, angle=rng.uniform(-20, 20), s0=rng.uniform(-50, 50))
        b = sheet(angle=rng.uniform(-20, 20))
        cert = C.clearance(ds(a, 5), {"b": ds(b, 5)})
        # analytic truth: coaxial sheets whose (phi, z) footprints overlap; the
        # bilinear quads are chords, inside their cylinder by <= diag^2 / (8 r),
        # so the true surface distance lies in [dr - sag_outer, dr + sag_inner]
        sag_outer = (20.0 * math.sqrt(2)) ** 2 / (8 * (R + dr))
        assert cert.certified_min <= dr - sag_outer
        assert cert.certified_min >= dr - cert.h_region - cert.h_train - 1.0  # and it is tight
        pp = cert.per_patch["b"]
        assert cert.raw_min - cert.certified_min <= cert.h_region + cert.h_train + 1e-9
        assert pp["raw_min_exact"]


def test_clearance_far_branch_is_fast_and_rigorous():
    a, b = ds(sheet(), 5), ds(sheet(z0=100.0 + 220.0 + 900.0), 5)  # ~900 vox apart
    cert = C.clearance(a, {"b": b})
    assert cert.passed and cert.per_patch["b"]["raw_min_exact"]
    assert cert.raw_min == pytest.approx(900.0, abs=0.01)
    assert cert.certified_min <= 900.0


def test_local_bounds_tighter_than_global_but_rigorous():
    g = sheet(shape=(10, 10)).astype(np.float64)
    g[:, 9] = g[:, 8] + (g[:, 9] - g[:, 8]) * 4.0  # one stretched column of quads
    D = ds(g.astype(np.float32), 5)
    assert D.h > 2 * np.median(D.hs)
    rng = np.random.default_rng(3)
    rows, cols = rng.random(20000) * 9, rng.random(20000) * 9
    true = T.sample_grid(g, rows, cols)
    d, j = cKDTree(D.points).query(true, k=8)
    # every true point is within the local bound of one of its nearby samples
    assert np.all(np.any(d <= D.hs[j] + 1e-6, axis=1))


def test_clearance_boundary():
    # zero-extent quads (h = 0) make the threshold exactly testable
    pt = lambda x: np.broadcast_to(np.float32([x, 0.0, 1.0]), (2, 2, 3)).copy()  # noqa: E731
    reg = C.dense_surface(pt(0.0), (1.0, 1.0), 1)
    assert reg.h == 0.0
    far = C.dense_surface(pt(128.0), (1.0, 1.0), 1)
    near = C.dense_surface(pt(127.75), (1.0, 1.0), 1)
    ok, bad = C.clearance(reg, {"f": far}), C.clearance(reg, {"n": near})
    assert ok.passed and ok.certified_min == 128.0
    assert not bad.passed
    assert bad.per_patch["n"]["n_offending"] == 4


def test_retrace_expansion_finds_the_patch_papyrus_on_other_traces():
    train = {"p": ds(sheet(shape=(6, 6)), 5)}
    others = {"retrace": ds(sheet(shape=(12, 12), s0=-50.0, z0=80.0, angle=10.0), 5),
              "winding": ds(sheet(radius=R + 30.0), 5)}
    ex = C.retrace_expansion(train, others)
    assert set(ex) == {"p@retrace"}
    # the expansion lies on the patch's papyrus (tangent-plane test: it may
    # reach up to the search radius beyond the patch edge, never further)
    d = cKDTree(train["p"].points).query(ex["p@retrace"].points)[0]
    assert d.max() <= C.SP_RADIUS_VOX + 1e-9 and np.median(d) < train["p"].h


# ---------------------------------------------------------------------------
# FL-09 certificate end to end (tifxyz on disk + registry)
# ---------------------------------------------------------------------------

def _write(tmp, name, grid):
    d = tmp / name
    T.write_tifxyz(d, T.TifxyzMesh(points=grid.astype(np.float32), scale=SC, uuid=name))
    return d


@pytest.fixture()
def fl09_setup(tmp_path):
    long = sheet(shape=(8, 40), s0=0.0)          # 780 vox long strip, the training segment
    retr = sheet(shape=(8, 20), s0=-5.0, z0=103.0, angle=2.0)  # re-traces its first ~380 vox
    wind = sheet(radius=R + 30.0, shape=(8, 40))  # next winding
    for n, g in (("train_seg", long), ("retrace_seg", retr), ("wind_seg", wind)):
        _write(tmp_path, n, g)
    reg = {"checkpoint": "synthetic", "frame": {"scroll": "SYN", "volume_id": "v1", "voxel_size_mm": 0.009362},
           "patches": [{"id": "p0", "segment": "train_seg", "mesh_dir": "train_seg", "rect_px": [0, 0, 128, 128],
                        "label_source": "human:synthetic"}]}
    (tmp_path / "reg.json").write_text(json.dumps(reg))
    return tmp_path


def _cert(tmp, seg, rect, **kw):
    region = {"segment": seg, "mesh_dir": seg, "rect_px": rect, "volume_id": "v1"}
    return C.fl09_certificate(tmp / "reg.json", region, **kw)


def test_fl09_fails_on_retrace_of_training_patch(fl09_setup):
    c = _cert(fl09_setup, "retrace_seg", [100, 0, 228, 128])
    assert not c["passed"] and not c["passed_alt_scalar"]
    assert c["primary_halo_inplane"]["raw_min"] < 3.0
    assert c["primary_halo_inplane"]["offending"]


def test_fl09_fails_on_next_winding(fl09_setup):
    c = _cert(fl09_setup, "wind_seg", [0, 0, 140, 140])
    assert not c["passed"]
    assert 25.0 < c["primary_halo_inplane"]["raw_min"] < 35.0


def test_fl09_halo_and_pass_along_the_sheet(fl09_setup):
    # R starts 150 px after the patch ends: 150 >= 128 but 150 - 64 < 128 -> FAIL (halo)
    c = _cert(fl09_setup, "train_seg", [128 + 150, 0, 128 + 150 + 128, 128])
    assert not c["passed"] and c["primary_halo_inplane"]["raw_min"] < 128
    # R starts 300 px after the patch: arc 300 - 64 = 236 px -> chord ~ 231 vox -> PASS
    c = _cert(fl09_setup, "train_seg", [128 + 300, 0, 128 + 300 + 128, 128])
    assert c["passed"] and c["passed_alt_scalar"]
    assert c["primary_halo_inplane"]["certified_min"] >= 128.0
    assert c["registry_sha256"] == C.sha256_file(fl09_setup / "reg.json")
    assert set(c["training_mesh_sha256"]["train_seg"]) == {"x.tif", "y.tif", "z.tif", "meta.json"}


def test_fl09_retrace_expansion_and_hash_checks(fl09_setup):
    retr = {"retrace_seg": "retrace_seg", "wind_seg": "wind_seg"}
    c = _cert(fl09_setup, "train_seg", [128 + 300, 0, 128 + 300 + 128, 128], retrace_meshes=retr)
    assert c["n_training_surfaces"] >= 2 and "p0@retrace_seg" in c["primary_halo_inplane"]["per_patch"]
    region = {"segment": "train_seg", "mesh_dir": "train_seg", "rect_px": [400, 0, 500, 100], "volume_id": "v2"}
    with pytest.raises(ValueError, match="frame"):
        C.fl09_certificate(fl09_setup / "reg.json", region)
    region["volume_id"] = "v1"
    region["mesh_sha256"] = {"x.tif": "0" * 64}
    with pytest.raises(ValueError, match="hash mismatch"):
        C.fl09_certificate(fl09_setup / "reg.json", region)


def test_registry_validation(tmp_path):
    bad = {"checkpoint": "c", "frame": {"scroll": "s", "volume_id": "v"}, "patches": []}
    (tmp_path / "r.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="voxel_size_mm"):
        C.load_registry(tmp_path / "r.json")
    dup = {"checkpoint": "c", "frame": {"scroll": "s", "volume_id": "v", "voxel_size_mm": 0.01},
           "patches": [dict(id="a", segment="s", mesh_dir="m", rect_px=None, label_source="h")] * 2}
    (tmp_path / "r.json").write_text(json.dumps(dup))
    with pytest.raises(ValueError, match="duplicate"):
        C.load_registry(tmp_path / "r.json")


def test_fl09_slab_margin_raises_the_surface_threshold(fl09_setup):
    rect = [128 + 300, 0, 128 + 300 + 128, 128]  # passes at slab 0 (certified ~ 225 vox)
    c0 = _cert(fl09_setup, "train_seg", rect)
    c1 = _cert(fl09_setup, "train_seg", rect, slab_region_vox=60.0, slab_train_vox=60.0)
    assert c0["passed"] and c0["surface_threshold_vox"] == 128.0
    assert c1["surface_threshold_vox"] == 248.0 and not c1["passed"]


# ---------------------------------------------------------------------------
# CORR-RETRACE-RULE: vertex form OR surface form (fail closed)
# ---------------------------------------------------------------------------

def test_half_cell_offset_exact_retrace_missed_by_vertex_form_caught_by_rule():
    # exact re-trace of the same sheet, grid shifted by half a dense cell (2 vox
    # at 5 x 5 on a 20 vox grid) along both grid axes: nearest dense vertex is
    # sqrt(8) = 2.83 vox away everywhere, the surface is 0 vox away
    b = sheet(shape=(12, 12))
    a = sheet(shape=(12, 12), s0=2.0, z0=102.0)
    r = C.corrected_pair(a, b, 5)
    for side in ("a_in_b", "b_in_a"):
        assert not r[side]["vertex"]["same"]           # the literal rule under-calls
        assert r[side]["vertex"]["counts"][0] == 0
        assert r[side]["surface"]["same"]               # form (b) catches it
        assert r[side]["same"]
    # the normal-distance form agrees with the surface form
    assert C.same_papyrus_nd(ds(a, 5), ds(b, 5)).same


def test_corrected_rule_negatives_and_positive_grid_retrace():
    b = sheet()
    for g, want in ((sheet(radius=R + 8.0), False),          # parallel 8 vox
                    (sheet(radius=R + 25.0), False),         # adjacent winding
                    (sheet(radius=R + 2.5), False),          # 2.5 vox: fails the ratio
                    (sheet(s0=70.0, z0=104.3, angle=12.0), True)):  # rotated re-trace
        r = C.corrected_pair(g, b, 5)
        same = bool(r and (r["a_in_b"]["same"] or r["b_in_a"]["same"]))
        assert same is want


def test_corrected_pair_prefilter_equals_full_grids():
    a, b = sheet(s0=70.0, z0=104.3, angle=12.0), sheet()
    r = C.corrected_pair(a, b, 5)
    full = C.corrected_direction(T.densify(a, 5).astype(np.float64), T.densify(b, 5).astype(np.float64))
    assert r["a_in_b"]["vertex"]["counts"] == full["vertex"]["counts"]
    assert r["a_in_b"]["surface"]["counts"] == full["surface"]["counts"]


def test_vendored_surface_code_matches_reference_source():
    import hashlib
    import subprocess
    ref = "95de3ba320a4718cedaea47085b39dbc52329713:src/hercules/tribunal/preread.py"
    try:
        src = subprocess.run(["git", "-C", str(Path(__file__).resolve().parents[1]), "show", ref],
                             capture_output=True, check=True).stdout
    except Exception:
        pytest.skip("reference commit not reachable")
    assert hashlib.sha256(src).hexdigest() == "58196006944a74106c4fe5f3d85742f2415aeaf1794eeffa3a2d87b9b406777a"
    txt = src.decode()
    body = txt[txt.index("def _closest_on_triangles"):txt.index("def check_retrace")]
    mine = (Path(__file__).resolve().parents[1] / "tools/sib/contam/ref_surface.py").read_text()
    assert body in mine
