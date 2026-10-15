# Provenance: Project HERCULES | owner the owner | [id removed]
"""TRIBUNAL planted-fault suite: one test per fault on synthetic tifxyz/zarr data, run
through the full on-disk pre-read gate (hashes consistent, so only content checks can
catch the fault), plus clean-pass and fail-closed tests.

Run: PYTHONPATH=src pytest -q tests/test_tribunal_*.py (collected by plain pytest)
"""

import json
import math

import numpy as np
import pytest

import zarr

from hercules.geometry.render_synth import cylinder_grid
from hercules.tribunal import faults as F
from hercules.tribunal import preread as P
from hercules.tribunal import runner as Rn
from hercules.tribunal import synth as S

N = 21
CROP = {"y0": 16, "x0": 24, "h": 64, "w": 112}


class W:
    pass


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("trib")
    w = W()
    w.dir = d
    w.world = S.make_volume(seed=7, voxel_um=9.366)
    S.write_volume_zarr(w.world.vol, d / "vol.zarr")
    w.vol = zarr.open(str(d / "vol.zarr"), mode="r")["0"]
    w.url = Rn._vol_url("v7")
    w.meta = S.write_metadata(d / "metadata.json", w.world.voxel_um)
    w.sheet, w.phi, w.z0 = 2, 0.3, 8.0
    w.pts = S.sheet_mesh(w.world, w.sheet, shape_hw=(24, 40), step=Rn.WIN_STEP, z0=w.z0, phi_ref=w.phi)
    w.mesh_dir = S.write_mesh(w.pts, d / "mesh", Rn.WIN_STEP, "synth-7", w.world.voxel_um)
    w.decoys = Rn._decoys(w.world, w.sheet, w.phi, np.random.default_rng(1), arc_w=(w.pts.shape[1] - 1) * Rn.WIN_STEP)
    w.clean = w.render()
    return w


def _render(self, origin=(CROP["y0"], CROP["x0"]), shift=0):
    return S.render_delivered(self.vol, self.pts, Rn.WIN_STEP, origin, (CROP["h"], CROP["w"]), N, slice_shift=shift)


W.render = _render


def gate(w, name, stack, *, voxel=None, training=None, meta_path=None, meta_source=None, patch=None):
    rec = Rn._record(w.dir, name, w.world, w.mesh_dir, stack, CROP, N, voxel if voxel is not None else w.world.voxel_um,
                     meta_path or w.meta, meta_source or (w.url + "/metadata.json"), w.url)
    if patch:
        patch(rec)
    return P.preread_gate(rec, volume=w.vol, training=w.decoys if training is None else training)


def failed(rep):
    return set(rep["failed"])


# ----------------------------------------------------------------------------- clean

def test_clean_record_passes_every_check(world):
    rep = gate(world, "clean", world.clean)
    assert rep["passed"], rep["failed"]
    json.dumps(rep, default=float)  # JSON-able


def test_clean_with_render_noise_passes(world):
    rng = np.random.default_rng(3)
    st = world.clean.astype(float) + rng.normal(0, 8, world.clean.shape)
    st = np.where(world.clean > 0, np.clip(np.rint(st), 1, 255), 0).astype(np.uint8)
    assert gate(world, "clean_noise", st)["passed"]


# ----------------------------------------------------------------------------- one test per planted fault

@pytest.mark.parametrize("d", F.OFFSET_DIRECTIONS)
def test_fault_offset_8px_caught(world, d):
    st = world.render(origin=(CROP["y0"] + d[0], CROP["x0"] + d[1]))
    rep = gate(world, f"off{d[0]}_{d[1]}", st)
    assert failed(rep) == {"window_offset"}
    det = next(c for c in rep["checks"] if c["name"] == "window_offset")["details"]
    assert det["shift_yx"] == [d[0], d[1]]


def test_fault_swapped_depth_order_caught(world):
    rep = gate(world, "swap", F.swap_depth(world.clean))
    assert failed(rep) == {"depth_order"}


@pytest.mark.parametrize("kind", ["flip_lr", "flip_ud"])
def test_fault_mirrored_render_caught(world, kind):
    st = world.clean[:, :, ::-1] if kind == "flip_lr" else world.clean[:, ::-1, :]
    rep = gate(world, f"mirror_{kind}", np.ascontiguousarray(st))
    assert failed(rep) == {"mirror"}
    det = next(c for c in rep["checks"] if c["name"] == "mirror")["details"]
    assert det["transform"] == kind


@pytest.mark.parametrize("shift", [-1, 1])
def test_fault_off_by_one_slice_caught(world, shift):
    rep = gate(world, f"obo{shift}", world.render(shift=shift))
    assert failed(rep) == {"slice_index"}
    det = next(c for c in rep["checks"] if c["name"] == "slice_index")["details"]
    assert det["lag"] == shift


def test_fault_retraced_by_training_segment_caught(world):
    rt, _ = F.retrace_of(world.world.radii[world.sheet], world.world.centre_xy, world.pts.shape[:2], Rn.WIN_STEP, 0.0,
                         world.z0, np.random.default_rng(5), step=Rn.TRAIN_STEP, phi_ref=world.phi)
    rep = gate(world, "retrace", world.clean, training={**world.decoys, "retrace_seg": rt})
    assert failed(rep) == {"retrace"}
    det = next(c for c in rep["checks"] if c["name"] == "retrace")["details"]
    assert det["same_as"] == ["retrace_seg"]


@pytest.mark.parametrize("wrong", [9.362, 7.91, 2.403, round(9.366 * (1 + 1e-4), 6)])
def test_fault_wrong_voxel_size_caught(world, wrong):
    rep = gate(world, f"vox{wrong}", world.clean, voxel=wrong)
    assert failed(rep) == {"voxel_size"}


def test_fault_voxel_from_foreign_metadata_caught(world):
    fm = S.write_metadata(world.dir / "metadata_other.json", 7.91)
    rep = gate(world, "vox_foreign", world.clean, voxel=7.91, meta_path=fm,
               meta_source=Rn._vol_url("other") + "/metadata.json")
    assert failed(rep) == {"voxel_size"}
    assert next(c for c in rep["checks"] if c["name"] == "voxel_size")["reason"] == "metadata_not_of_this_volume"


@pytest.mark.parametrize("where", ["render_command", "display"])
def test_fault_wrong_voxel_in_one_place_caught(world, where):
    def patch(rec):
        if where == "render_command":
            i = rec["render_command"].index("--voxel-size")
            rec["render_command"][i + 1] = "9.4"
        else:
            rec["display"]["px_per_mm_image"] = 1000.0 * 0.5 / 9.4
    rep = gate(world, f"vox_{where}", world.clean, patch=patch)
    assert failed(rep) == {"voxel_size"}


# ----------------------------------------------------------------------------- re-trace rule details

def _cyl(R, step=20.0, **kw):
    return cylinder_grid(R, (2000.0, 2000.0), (30, 30), step, kw.pop("angle", 0.0), **kw).astype(np.float64)


def test_retrace_rule_literal_vertex_form_undercalls_at_20vox():
    """Documents the defect that motivates the surface form: an exact re-trace whose grid
    is offset by half a densified cell is invisible to the nearest-vertex form."""
    win = _cyl(600.0, s0=0.0, z0=100.0)
    rt = _cyl(600.0, s0=10.0, z0=110.0)
    r = P.check_retrace(win, {"rt": rt})
    seg = r.details["per_segment"]["rt"]
    assert seg["vertex"]["same"] is False and seg["surface"]["same"] is True
    assert not r.passed


@pytest.mark.parametrize("gap", [2.5, 3.0, 6.0, 12.0, -3.0, -12.0])
def test_retrace_no_false_alarm_on_neighbouring_sheet(gap):
    win = _cyl(600.0, s0=0.0, z0=100.0)
    nb = _cyl(600.0 + gap, s0=5.0, z0=107.0)
    assert P.check_retrace(win, {"nb": nb}).passed


def test_retrace_no_false_alarm_same_sheet_elsewhere():
    win = _cyl(600.0, s0=0.0, z0=100.0)
    far = _cyl(600.0, s0=900.0, z0=100.0)
    assert P.check_retrace(win, {"far": far}).passed


def test_retrace_densify_is_5x5():
    assert P.RETRACE_DENSIFY == 5 and P.RETRACE_MIN_WITHIN_2 == 1000 and P.RETRACE_RATIO == 2.0


def test_surface_distance_exact_on_plane():
    g = np.zeros((5, 5, 3))
    g[..., 0], g[..., 1] = np.meshgrid(np.arange(5) * 4.0, np.arange(5) * 4.0, indexing="xy")
    g[..., 2] = 10.0
    pts = np.array([[5.0, 7.0, 10.6], [9.3, 2.1, 12.2], [1.0, 1.0, 9.1]])
    d = P.surface_distances(pts, g, max_dist=3.0)
    np.testing.assert_allclose(d, [0.6, 2.2, 0.9], atol=1e-9)


# ----------------------------------------------------------------------------- fail-closed behaviour

def test_unverifiable_stack_fails_closed(world):
    other = S.make_volume(seed=99)
    st = S.render_delivered(other.vol, world.pts, Rn.WIN_STEP, (CROP["y0"], CROP["x0"]), (CROP["h"], CROP["w"]), N)
    rep = gate(world, "foreign_ct", st)
    assert {"window_offset", "mirror", "depth_order", "slice_index"} <= failed(rep)
    for c in rep["checks"]:
        if c["name"] in ("window_offset", "mirror", "depth_order", "slice_index"):
            assert c["reason"] in ("unverifiable", "ambiguous") or c["reason"].startswith(("transform", "lag", "offset", "reversed"))


def test_depth_symmetric_volume_is_ambiguous_not_pass(tmp_path):
    """A volume that does not vary along the sheet normal cannot show the depth order:
    the check must fail (ambiguous), never pass."""
    rng = np.random.default_rng(0)
    Z, Y, X = 112, 192, 192
    from scipy.ndimage import gaussian_filter, map_coordinates
    tex = gaussian_filter(rng.standard_normal((Z, 256)), 2.0)
    tex = (tex - tex.min()) / (tex.max() - tex.min()) * 200 + 20
    zz, yy, xx = np.mgrid[0:Z, 0:Y, 0:X]
    phi = (np.arctan2(yy - 96.0, xx - 96.0) + np.pi) / (2 * np.pi) * 255
    vol = map_coordinates(tex, [zz.ravel(), phi.ravel()], order=1, mode="wrap").reshape(Z, Y, X).astype(np.uint8)
    world = S.World(vol=vol, centre_xy=(96.0, 96.0), radii=(30, 42, 54, 66, 78), voxel_um=9.366, seed=0)
    pts = S.sheet_mesh(world, 2, shape_hw=(24, 40), step=4.0, z0=8.0)
    st = S.render_delivered(vol, pts, 4.0, (16, 24), (64, 112), N)
    reg = P.register(st, vol, pts, (0.25, 0.25), (16, 24), N, 1.0, True)
    assert not P.check_depth_order(reg).passed
    assert not P.check_slice_index(reg).passed


def test_provenance_hash_mismatch_fails(world):
    def patch(rec):
        rec["stack"]["sha256"] = "0" * 64
    rep = gate(world, "badhash", world.clean, patch=patch)
    assert "provenance" in failed(rep)


def test_missing_training_list_fails(world):
    rec = Rn._record(world.dir, "notrain", world.world, world.mesh_dir, world.clean, CROP, N, world.world.voxel_um,
                     world.meta, world.url + "/metadata.json", world.url)
    rep = P.preread_gate(rec, volume=world.vol, training=None)
    assert failed(rep) == {"retrace"}


def test_require_clean_raises(world):
    rep = gate(world, "swap2", F.swap_depth(world.clean))
    with pytest.raises(P.TribunalFault):
        P.require_clean(rep)
    P.require_clean(gate(world, "clean2", world.clean))


# ----------------------------------------------------------------------------- map order provenance

def test_map_order_provenance(tmp_path):
    a, b = tmp_path / "fwd.tif", tmp_path / "rev.tif"
    a.write_bytes(b"forward-map-bytes")
    b.write_bytes(b"reverse-map-bytes")
    log = [{"output_sha256": P.file_sha256(a), "direction": "forward", "input_stack_sha256": "S"},
           {"output_sha256": P.file_sha256(b), "direction": "reverse", "input_stack_sha256": "S"}]
    good = {"t": {"path": a, "order": "text", "stack_sha256": "S"}, "n": {"path": b, "order": "nontext", "stack_sha256": "S"}}
    assert P.check_map_order(good, "forward", log).passed
    swapped = {"t": {"path": b, "order": "text", "stack_sha256": "S"}, "n": {"path": a, "order": "nontext", "stack_sha256": "S"}}
    r = P.check_map_order(swapped, "forward", log)
    assert not r.passed and set(r.details["bad"]) == {"t", "n"}
    assert P.check_map_order(swapped, "reverse", log).passed
    wrong_stack = {"t": {"path": a, "order": "text", "stack_sha256": "OTHER"}}
    assert not P.check_map_order(wrong_stack, "forward", log).passed
    c = tmp_path / "unlogged.tif"
    c.write_bytes(b"x")
    assert not P.check_map_order({"t": {"path": c, "order": "text", "stack_sha256": "S"}}, "forward", log).passed


def test_reference_render_matches_official_canvas_convention(world):
    """Pixel P of the reference samples grid (P + 0.5) s: the delivered (independent) render
    and the reference agree to NCC > 0.99 on every slice of a clean stack."""
    offs = P.slice_offsets_ext(N, 1.0, 0)
    ref = P.reference_stack(world.vol, world.pts, (0.25, 0.25), (CROP["y0"], CROP["x0"]), (CROP["h"], CROP["w"]),
                            offs, True)
    for k in range(N):
        d = np.where(world.clean[k] == 0, np.nan, world.clean[k].astype(float))
        assert P.ncc(d, ref[k])[0] > 0.99
    assert math.isclose(offs[N // 2], 0.0)


# ----------------------------------------------------------------------------- REAL-TRIB-2 (i): no short-circuit, injectable, unrounded

def test_every_reason_reported_together(world):
    """Mirrored AND offset: the mirror check reports its transform and the offset check its shift; each
    check lists all of its own failing conditions (no early return)."""
    st = world.render(origin=(CROP["y0"], CROP["x0"] + 8))[:, :, ::-1]
    reg = P.register(np.ascontiguousarray(st), world.vol, world.pts, (0.25, 0.25), (CROP["y0"], CROP["x0"]), N, 1.0, True)
    m = P.check_mirror(reg)
    assert not m.passed and m.details["reasons"][0].startswith("transform:")
    strict = P.check_mirror(reg, {"MIN_REF_NCC": 1.01, "MIRROR_MARGIN": 5.0})
    assert strict.details["reasons"] == ["unverifiable", strict.details["reasons"][1], "ambiguous"]


def test_thresholds_injectable_and_unrounded(world):
    reg = P.register(world.clean, world.vol, world.pts, (0.25, 0.25), (CROP["y0"], CROP["x0"]), N, 1.0, True)
    s = P.check_slice_index(reg).details["margin"]
    assert P.check_slice_index(reg, {"SLICE_MARGIN": s - 1e-12}).passed
    assert not P.check_slice_index(reg, {"SLICE_MARGIN": s + 1e-12}).passed  # no rounding anywhere
    ncc = reg.best_ncc
    assert P.check_window_offset(reg, {"MIN_REF_NCC": ncc}).passed
    assert P.check_window_offset(reg, {"MIN_REF_NCC": ncc + 1e-12}).details["reasons"] == ["unverifiable"]
    with pytest.raises(ValueError):
        P.check_mirror(reg, {"MIRROR_MARGN": 0.1})


def test_gate_reports_thresholds_in_force(world):
    rec = Rn._record(world.dir, "thr", world.world, world.mesh_dir, world.clean, CROP, N, world.world.voxel_um,
                     world.meta, world.url + "/metadata.json", world.url)
    rep = P.preread_gate(rec, volume=world.vol, training=world.decoys, thresholds={"SLICE_MARGIN": 0.042})
    assert rep["thresholds"]["SLICE_MARGIN"] == 0.042 and rep["thresholds"]["MIRROR_MARGIN"] == 0.05
