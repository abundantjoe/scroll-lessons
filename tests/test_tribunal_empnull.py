# Provenance: Project HERCULES | owner the owner | [id removed]
"""TRIBUNAL empirical null tile builder (plan section 8.2) on synthetic data."""


import numpy as np
import pytest
from scipy.spatial import cKDTree

from hercules.geometry.level_mesh import CentreCurve
from hercules.geometry.render_synth import cylinder_grid
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
from hercules.tribunal import empnull as E

C = (1000.0, 1000.0)
CENTRE = CentreCurve.straight(*C)


class ShellM7:
    """Lazy binary m7-like volume: sheets are shells |r - r_k| <= half (volume vox),
    stored at ``scale`` volume voxels per m7 voxel."""

    def __init__(self, radii, half=1.5, scale=1.0, shape_zyx=(1200, 2000, 2000)):
        self.radii, self.half, self.scale = np.asarray(radii, float), half, float(scale)
        self.shape = tuple(int(s // scale) for s in shape_zyx)

    def __getitem__(self, sl):
        zs, ys, xs = sl
        y = (np.arange(ys.start, ys.stop) + 0.0) * self.scale
        x = (np.arange(xs.start, xs.stop) + 0.0) * self.scale
        r = np.hypot(x[None, :] - C[0], y[:, None] - C[1])
        m = (np.abs(r[..., None] - self.radii[None, None, :]) <= self.half).any(-1)
        return np.broadcast_to(m[None], (zs.stop - zs.start, *m.shape)).astype(np.uint8)


def _mesh(R, shape=(30, 30), s0=0.0, z0=200.0, step=20.0):
    return cylinder_grid(R, C, shape, step, 0.0, s0=s0, z0=z0).astype(np.float64)


@pytest.mark.parametrize("R,pitch", [(300.0, 12.0), (600.0, 18.0)])
def test_pitch_constant_spacing(R, pitch):
    m7 = ShellM7([R - 2 * pitch, R - pitch, R, R + pitch, R + 2 * pitch])
    res = E.local_pitch(_mesh(R), m7)
    assert res["status"] == "OK" and abs(res["pitch_vox"] - pitch) <= 0.5
    assert res["own_sheet_confirmed"] == res["n_vertices"]


def test_pitch_takes_nearest_neighbour():
    m7 = ShellM7([300.0 - 9.0, 300.0, 300.0 + 15.0])
    res = E.local_pitch(_mesh(300.0), m7)
    assert abs(res["pitch_vox"] - 9.0) <= 0.5


def test_pitch_with_downsampled_m7():
    m7 = ShellM7([276.0, 288.0, 300.0, 312.0, 324.0], half=2.0, scale=2.0)
    res = E.local_pitch(_mesh(300.0), m7, m7_scale=2.0)
    assert abs(res["pitch_vox"] - 12.0) <= 1.0


def test_pitch_mesh_off_m7_sheet_is_insufficient():
    m7 = ShellM7([280.0, 320.0])
    res = E.local_pitch(_mesh(300.0), m7)
    assert res["status"] == "INSUFFICIENT" and res["own_sheet_confirmed"] == 0


def test_offsheet_meshes_at_half_pitch(tmp_path):
    p = _mesh(300.0)
    out = E.offsheet_meshes(p, (0.05, 0.05), 12.0, tmp_path, "cand", 9.366, centre=CENTRE)
    assert {o["side"] for o in out} == {"outward", "inward"}
    for o in out:
        q = read_tifxyz(o["mesh_path"]).points
        assert q.shape == p.shape
        v = valid_mask(q)
        r = np.hypot(q[v][:, 0] - C[0], q[v][:, 1] - C[1])
        expect = 306.0 if o["side"] == "outward" else 294.0
        assert np.max(np.abs(r - expect)) < 0.05


RB = 600.0  # band tests: R on a radius-600 sheet (circumference ~3770 vox)


def _candidates(volume_id="V"):
    """Segments in the band (560, 600, 620) and outside it (480, 720), in two z blocks;
    200 px tiles every 300 px so tiles of one segment are separated."""
    cands = []
    for i, R in enumerate([480.0, 560.0, 600.0, 620.0, 720.0]):
        for j, z0 in enumerate((100.0, 1000.0)):
            pts = _mesh(R, shape=(40, 180), s0=0.0, z0=z0)
            cands += E.grid_tiles(f"seg{i}_{j}", volume_id, pts, (0.05, 0.05), (200, 200), stride_px=300)
    return cands


def _R_points():
    return _mesh(RB, shape=(40, 180), s0=0.0, z0=100.0)


def test_band_selection_rules():
    R_pts = _R_points()
    R_cloud, vf = E.tile_cloud(R_pts, (0.05, 0.05), {"y0": 200, "x0": 400, "h": 200, "w": 200})
    assert vf == 1.0
    cands = _candidates() + [dict(c, volume_id="OTHER") for c in _candidates()[:5]]
    excl = E.tile_cloud(_mesh(620.0, shape=(40, 180), s0=0.0, z0=1000.0), (0.05, 0.05),
                        {"y0": 400, "x0": 1400, "h": 200, "w": 200})[0]
    sel = E.select_band_tiles(R_cloud, "V", cands, CENTRE, 25, exclusions={"J": excl}, seed=3)
    assert sel["rejected"]["other_volume"] == 5 and sel["rejected"]["out_of_band"] > 0
    assert sel["rejected"]["near_R"] > 0 and sel["rejected"]["near_exclusion"] > 0
    rR = sel["radius_R_vox"]
    by_key = {(c["segment_id"], tuple(c["window"].values())): c for c in cands}
    tR, tE = cKDTree(R_cloud), cKDTree(excl)
    clouds = []
    for c in sel["chosen"]:
        assert abs(c["radius_vox"] - rR) <= 0.1 * rR
        cl = by_key[(c["segment_id"], tuple(c["window"].values()))]["cloud"]
        assert tR.query(cl)[0].min() >= E.SEP_FROM_R_VOX
        assert tE.query(cl)[0].min() >= E.EXCLUSION_VOX
        for o in clouds:
            assert cKDTree(o).query(cl)[0].min() >= E.MUTUAL_SEP_VOX
        clouds.append(cl)
    again = E.select_band_tiles(R_cloud, "V", cands, CENTRE, 25, exclusions={"J": excl}, seed=3)
    assert again["chosen"] == sel["chosen"]


def test_build_null_set_complete(tmp_path):
    R_pts = _R_points()
    m7 = ShellM7([576.0, 588.0, 600.0, 612.0, 624.0])
    R = {"candidate_id": "cand1", "volume_id": "V", "segment_id": "seg2_0",
         "window": {"y0": 200, "x0": 400, "h": 200, "w": 200}, "text_direction": "forward"}
    ns = E.build_null_set(R, R_points=R_pts, scale=(0.05, 0.05), voxel_um=9.366, m7=m7, centre=CENTRE,
                          band_candidates=_candidates(), out_dir=tmp_path, seed=1)
    kinds = [t["kind"] for t in ns["tiles"]]
    assert ns["status"] == "OK" and ns["n_tiles"] >= 40 and ns["n_band"] >= 20
    assert kinds.count("R_nontext_order") == 1 and kinds.count("R_null_arm") == 1
    assert kinds.count("R_offsheet_half_pitch") == 2
    assert all(t["order"] == "nontext" and t["direction"] == "reverse" for t in ns["tiles"]
               if t["kind"] in ("band_nontext_order", "R_nontext_order"))
    assert abs(ns["pitch"]["pitch_vox"] - 12.0) <= 0.5
    assert len({t["null_id"] for t in ns["tiles"]}) == len(ns["tiles"])
    assert all(t["match"]["tile_hw"] == [200, 200] for t in ns["tiles"])


def test_build_null_set_insufficient_is_reported(tmp_path):
    R_pts = _R_points()
    m7 = ShellM7([588.0, 600.0, 612.0])
    R = {"candidate_id": "cand2", "volume_id": "V", "segment_id": "seg2_0",
         "window": {"y0": 200, "x0": 400, "h": 200, "w": 200}, "text_direction": "reverse"}
    ns = E.build_null_set(R, R_points=R_pts, scale=(0.05, 0.05), voxel_um=9.366, m7=m7, centre=CENTRE,
                          band_candidates=_candidates()[:10], out_dir=tmp_path, seed=1)
    assert ns["status"] == "INSUFFICIENT" and ns["n_band"] < 20


# ----------------------------------------------------------------------------- REAL-TRIB-2 (ii) additions

def test_chunk_point_sampler_matches_direct_indexing():
    import zarr
    rng = np.random.default_rng(0)
    a = rng.integers(0, 255, (40, 50, 60)).astype(np.uint8)
    z = zarr.array(a, chunks=(16, 16, 16))
    q = np.stack([rng.integers(-5, 45, 3000), rng.integers(-5, 55, 3000), rng.integers(-5, 65, 3000)], 1)
    got = E.ChunkPointSampler(z).sample(q)
    ok = np.all((q >= 0) & (q < a.shape), axis=1)
    np.testing.assert_array_equal(got[ok], a[q[ok, 0], q[ok, 1], q[ok, 2]])
    assert np.all(got[~ok] == 0)


def test_local_pitch_chunk_path_equals_block_path(monkeypatch):
    import zarr
    radii = [276.0, 288.0, 300.0, 312.0, 324.0]
    sh = ShellM7(radii, shape_zyx=(400, 1400, 1400))
    z0 = zarr.array(np.asarray(sh[slice(150, 400), slice(600, 1400), slice(600, 1400)]), chunks=(64, 64, 64))

    class Offset:  # expose the sub-block at its global coordinates
        shape = sh.shape
        chunks = (64, 64, 64)

        def __getitem__(self, sl):
            zz, yy, xx = sl
            return z0[zz.start - 150:zz.stop - 150, yy.start - 600:yy.stop - 600, xx.start - 600:xx.stop - 600]

    pts = cylinder_grid(300.0, C, (8, 10), 20.0, 0.0, s0=0.0, z0=220.0, phi_ref=0.3).astype(np.float64)
    a = E.local_pitch(pts, Offset(), min_points=10)
    monkeypatch.setattr(np, "prod", lambda x: 10 ** 12)  # force the chunk path
    b = E.local_pitch(pts, Offset(), min_points=10)
    assert a["pitch_vox"] == b["pitch_vox"] and a["n_used"] == b["n_used"]
    assert abs(a["pitch_vox"] - 12.0) <= 0.5


@pytest.mark.parametrize("tilt", [0.0, 0.05])
def test_centre_from_normals_recovers_axis(tilt):
    meshes = []
    for R, phi in ((300.0, 0.0), (340.0, 2.0), (380.0, 4.0)):
        p = cylinder_grid(R, C, (60, 80), 20.0, 0.0, s0=0.0, z0=0.0, phi_ref=phi).astype(np.float64)
        p[..., 0] += tilt * p[..., 2]  # a slanted axis: centre x = 1000 + tilt z
        meshes.append(p)
    curve, diag = E.centre_from_normals(meshes, z_band=200.0, stride=1)
    zq = np.array([300.0, 700.0, 1000.0])
    cx, cy = curve(zq)
    np.testing.assert_allclose(cy, C[1], atol=0.5)
    np.testing.assert_allclose(cx, C[0] + tilt * zq, atol=0.5 + tilt * 100)
    with pytest.raises(ValueError):
        E.centre_from_normals([meshes[0][:3, :3]], z_band=200.0)
