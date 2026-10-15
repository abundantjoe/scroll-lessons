# Provenance: Project HERCULES | owner the owner | [id removed]
"""Window pipeline (hercules.pipeline.window) on synthetic cylinders.

Renders are emulated with hercules.pipeline.canvas.emulate_gen (verified
against the official binary in test_pipeline_canvas.py) sampling an analytic
3-D texture, so organizer SVs and levelled renders come from the same
surface exactly as the official renderer would produce them.
"""

import json
import math

import numpy as np
import pytest

from hercules.geometry.level_mesh import CentreCurve, iso_z_tilt_deg
from hercules.geometry.render_synth import cylinder_grid
from hercules.geometry.tifxyz import TifxyzMesh, read_tifxyz, valid_mask
from hercules.pipeline import canvas as C
from hercules.pipeline import window as Wn

R, CX, CY = 600.0, 700.0, 700.0
CENTRE = CentreCurve.straight(CX, CY)


def cyl_mesh(angle=25.0, shape=(70, 90), ripple=0.0):
    p = cylinder_grid(R, (CX, CY), shape, 20.0, angle, s0=-900.0, z0=100.0).astype(np.float64)
    if ripple:
        # radial ripple so the sheet is not developable-trivial
        dx, dy = p[..., 0] - CX, p[..., 1] - CY
        r = np.hypot(dx, dy)
        f = 1 + ripple * np.sin(p[..., 2] / 90.0) / R
        p[..., 0] = CX + dx * f
        p[..., 1] = CY + dy * f
    return TifxyzMesh(p.astype(np.float32), (0.05, 0.05), "cyl")


WIN = Wn.Window(500, 700, 400, 400)


@pytest.fixture(scope="module")
def base():
    return Wn.run_window(cyl_mesh(), WIN, CENTRE, margin_px=64)


@pytest.fixture(scope="module", params=[(True, 1), (True, -1), (False, 1), (False, -1)],
                ids=["asc+1", "asc-1", "desc+1", "desc-1"])
def variant(request):
    zasc, sign = request.param
    return Wn.run_window(cyl_mesh(ripple=6.0), WIN, CENTRE, margin_px=64, z_ascending=zasc, convention_sign=sign)


# ---------------------------------------------------------------------------
# levelling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("angle", [25.0, -25.0, 40.0])
def test_rotated_mesh_levels_to_horizontal_iso_z(angle):
    res = Wn.run_window(cyl_mesh(angle), WIN, CENTRE, margin_px=64)
    # z = 20 (u sin a + v cos a): gradient direction 90 - a
    assert abs(res.stats["angle_deg"] - (90.0 - angle)) < 0.01
    assert res.stats["spread_deg"] < 0.01
    reg = res.points[Wn._region_rows_cols(res.maps.lev, res.maps.lev_window.grow(64), res.points.shape[:2])]
    assert iso_z_tilt_deg(reg) < 0.05
    z = np.where(valid_mask(reg), reg[..., 2], np.nan)
    row_sd = np.nanstd(z, axis=1)
    assert np.nanmax(row_sd) < 0.05  # every row is one iso-z line
    dz = np.nanmedian(np.diff(np.nanmedian(z, axis=1)))
    assert abs(dz - 20.0) < 0.05  # z ascending, 20 vox per levelled row
    assert res.stats["edge_frac_5pct"] > 0.99 and res.stats["edge_frac_10pct"] == 1.0
    assert res.stats["lev_window_render_valid_frac"] == 1.0


def test_cut_covers_rotated_window(base):
    st = base.stats
    x, y, w, h = st["render_crop_xywh"]
    assert (w, h) == (400 + 128, 400 + 128)
    assert st["pad"]["top"] == 0 and st["pad"]["left"] == 0
    # the cut is the circumscribed disc: larger than window + margin
    assert st["cut"]["shape"][0] > st["cut"]["region_shape"][0]


# ---------------------------------------------------------------------------
# maps
# ---------------------------------------------------------------------------

def _rand_org(res, n=4000, extra=150, seed=0):
    r = np.random.default_rng(seed)
    w = res.maps.window
    return (r.uniform(w.y0 - extra, w.y0 + w.h + extra, n), r.uniform(w.x0 - extra, w.x0 + w.w + extra, n))


def test_round_trip(variant):
    m = variant.maps
    y, x = _rand_org(variant)
    ly, lx = m.org_to_lev(y, x)
    y2, x2 = m.lev_to_org(ly, lx)
    assert np.abs(y2 - y).max() < 0.05 and np.abs(x2 - x).max() < 0.05
    assert np.abs(y2 - y).max() < 1e-8  # exact in practice
    r = np.random.default_rng(1)
    ly, lx = r.uniform(-100, 500, 3000), r.uniform(-100, 500, 3000)
    y, x = m.lev_to_org(ly, lx)
    ly2, lx2 = m.org_to_lev(y, x)
    assert np.abs(ly2 - ly).max() < 0.05 and np.abs(lx2 - lx).max() < 0.05
    # canvas frame differs from window frame by the window origin only
    cy_, cx_ = m.org_to_lev(y, x, frame="canvas")
    assert np.allclose(cy_ - ly2, m.lev_window.y0) and np.allclose(cx_ - lx2, m.lev_window.x0)


def test_window_centre_maps_to_levelled_window_centre(variant):
    m = variant.maps
    yc, xc = m.window.centre
    ly, lx = m.org_to_lev(yc, xc)
    assert abs(ly - (m.lev_window.h - 1) / 2) <= 0.5 and abs(lx - (m.lev_window.w - 1) / 2) <= 0.5


def test_mirror_flags(variant):
    st = variant.stats
    zasc, sign = variant.orient.z_ascending, variant.orient.convention_sign
    assert st["chirality_after"] == sign
    # the cylinder grid has du x dv outward: chirality +1 before any flip
    assert st["chirality_before"] == 1
    assert st["flip_v"] == (not zasc)
    assert st["flip_u_mirror"] == ((1 if zasc else -1) != sign)
    assert st["map_mirrored"] == (st["flip_u_mirror"] != st["flip_v"])
    assert abs(abs(st["map_det"]) - 1.0) < 0.01
    # z trend of the output grid
    z = np.where(valid_mask(variant.points), variant.points[..., 2], np.nan)
    trend = np.nanmedian(np.diff(z, axis=0))
    assert (trend > 0) == zasc
    assert not st["ambiguous"] and st["sign_levelled"]["frac_clear"] == 1.0


def test_maps_agree_with_3d_surface(variant):
    """The same (u, v) seen through both canvases is the same 3-D point:
    emulated organizer render coords at org pixels vs emulated levelled render
    coords at the mapped pixels (differences are the second-order levelling
    resample error only)."""
    res = variant
    m = res.maps
    mesh = cyl_mesh(ripple=6.0)
    w = m.window
    org_cv = C.canvas_for(mesh.points, mesh.scale).with_origin(w.y0, w.x0)
    co_org, no_org = C.emulate_gen(mesh.points, org_cv, (w.h, w.w))
    # the organizer window is a rotated square in the levelled frame: emulate
    # the levelled render over the window + 100 px (inside the 64 px render
    # margin plus the rotation extra of the cut)
    E = 100
    lev_cv = m.lev.with_origin(m.lev_window.y0 - E, m.lev_window.x0 - E)
    co_lev, no_lev = C.emulate_gen(res.points, lev_cv, (m.lev_window.h + 2 * E, m.lev_window.w + 2 * E))
    r = np.random.default_rng(3)
    yi, xi = r.integers(0, w.h, 3000), r.integers(0, w.w, 3000)
    ly, lx = m.org_to_lev(yi + w.y0, xi + w.x0)
    got = np.stack([Wn.bilinear(co_lev[..., k], ly + E, lx + E) for k in range(3)], -1)
    ref = co_org[yi, xi]
    ok = np.isfinite(got).all(-1) & np.isfinite(ref).all(-1)
    assert ok.mean() == 1.0
    d = np.linalg.norm(got[ok] - ref[ok], axis=-1)
    assert np.percentile(d, 99) < 0.3 and d.max() < 0.5
    # normals agree in direction up to the parity of the flips
    nref = no_org[yi, xi][ok]
    ngot = np.stack([Wn.bilinear(no_lev[..., k], ly + E, lx + E) for k in range(3)], -1)[ok]
    dot = np.nansum(nref * ngot, axis=-1)
    parity = -1 if (m.flip_u != m.flip_v) else 1
    assert np.nanmedian(dot * parity) > 0.99


def _blob_image(shape, centres, sigma=2.0, amps=None):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float64)
    img = np.zeros(shape)
    for i, (cy, cx) in enumerate(centres):
        a = 1.0 if amps is None else amps[i]
        img += a * np.exp(-0.5 * ((yy - cy) ** 2 + (xx - cx) ** 2) / sigma ** 2)
    return img


def test_painted_pattern_lands_at_predicted_position(variant):
    m = variant.maps
    w = m.window
    # the levelled window is a rotated square on the organizer canvas: paint
    # the organizer image over the window + 100 px so it covers it
    org_origin = (w.y0 - 100, w.x0 - 100)
    shape = (w.h + 200, w.w + 200)
    r = np.random.default_rng(7)
    # blob centres anywhere in the organizer window whose image lies >= 15 px
    # inside the levelled window
    cand = np.c_[r.uniform(w.y0, w.y0 + w.h, 200), r.uniform(w.x0, w.x0 + w.w, 200)]
    cy_, cx_ = m.org_to_lev(cand[:, 0], cand[:, 1])
    inside = (cy_ > 15) & (cy_ < w.h - 15) & (cx_ > 15) & (cx_ < w.w - 15)
    chosen = []
    for c in cand[inside]:  # keep blobs >= 25 px apart so centroids do not mix
        if all(math.hypot(*(c - d)) >= 25 for d in chosen):
            chosen.append(c)
    cen_org = np.array(chosen[:25])
    assert len(cen_org) >= 20
    img = _blob_image(shape, cen_org - np.array(org_origin))
    lev = Wn.resample_to_levelled(img, m, (w.h, w.w), org_origin=org_origin)
    assert np.isfinite(lev).mean() > 0.999
    py, px = m.org_to_lev(cen_org[:, 0], cen_org[:, 1])
    yy, xx = np.mgrid[0:w.h, 0:w.w]
    for (cy, cx) in zip(py, px):
        sel = (np.hypot(yy - cy, xx - cx) < 7) & np.isfinite(lev)
        wgt = lev[sel]
        my, mx = (yy[sel] * wgt).sum() / wgt.sum(), (xx[sel] * wgt).sum() / wgt.sum()
        assert math.hypot(my - cy, mx - cx) < 0.5


def test_asymmetric_pattern_mirrors_exactly_when_flipped(variant):
    """An 'L' of three blobs keeps or reverses its handedness according to
    map_mirrored."""
    m = variant.maps
    w = m.window
    yc, xc = w.centre
    pts = np.array([[yc, xc], [yc - 60, xc], [yc, xc + 30]])  # up and right arms
    img = _blob_image((w.h, w.w), pts - [w.y0, w.x0])
    lev = Wn.resample_to_levelled(img, m, (w.h, w.w), org_origin=(w.y0, w.x0))
    py, px = m.org_to_lev(pts[:, 0], pts[:, 1])
    a = np.array([py[1] - py[0], px[1] - px[0]])
    b = np.array([py[2] - py[0], px[2] - px[0]])
    cross = a[0] * b[1] - a[1] * b[0]
    # original handedness: up x right in (y, x) = (-60*30 - 0) < 0
    assert (np.sign(cross) == -1) == (not variant.stats["map_mirrored"])
    # and the image content is there
    for yy_, xx_ in zip(py, px):
        assert lev[int(round(yy_)), int(round(xx_))] > 0.9


# ---------------------------------------------------------------------------
# padding near the mesh edge
# ---------------------------------------------------------------------------

def test_window_near_edge_is_padded_and_exact():
    mesh = cyl_mesh(shape=(40, 50))
    res = Wn.run_window(mesh, Wn.Window(20, 30, 300, 300), CENTRE, margin_px=64)
    st = res.stats
    assert st["pad"]["top"] > 0 or st["pad"]["left"] > 0
    x, y, w, h = st["render_crop_xywh"]
    Hc, Wc = res.maps.lev.shape
    assert x >= 0 and y >= 0 and x + w <= Wc and y + h <= Hc
    yy, xx = _rand_org(res)
    ly, lx = res.maps.org_to_lev(yy, xx)
    y2, x2 = res.maps.lev_to_org(ly, lx)
    assert np.abs(y2 - yy).max() < 1e-8 and np.abs(x2 - xx).max() < 1e-8


# ---------------------------------------------------------------------------
# writing and render command
# ---------------------------------------------------------------------------

def test_write_levelled_tifxyz(tmp_path, base):
    p = Wn.write_levelled_tifxyz(base, tmp_path / "lev.tifxyz", "lev_test", voxel_size_um=9.362, source="cyl")
    m = read_tifxyz(p)
    assert m.scale == (0.05, 0.05)
    assert np.array_equal(valid_mask(m.points), valid_mask(base.points))
    assert np.allclose(m.points[valid_mask(m.points)], base.points[valid_mask(base.points)])
    text = (p / "meta.json").read_text(encoding="utf-8")
    assert text.splitlines()[1].strip().startswith('"provenance": "Project HERCULES')
    meta = json.loads(text)
    assert meta["hercules_lev_window"] == [base.maps.lev_window.y0, base.maps.lev_window.x0, 400, 400]
    # the written grid has the canvas the maps assume
    assert C.canvas_for(m.points, m.scale).shape == base.maps.lev.shape


def test_render_command(base):
    url = Wn.volume_url("PHerc0139", "20250728140407-9.362um-1.2m-113keV-masked")
    assert url == "s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/"
    crop = base.maps.render_crop(64)
    flip = C.flip_normals_after_orient(True, base.maps.flip_u, base.maps.flip_v)
    cmd = Wn.render_command(url, "/work/x/lev.tifxyz", "/work/x/out.zarr", 9.362, crop_xywh=crop, flip_normals=flip)
    s = " ".join(cmd)
    for frag in ("--scale 1", "--group-idx 0", "--num-slices 31", "--slice-step 1", "--voxel-size 9.362",
                 "--voxel-unit micrometer", f"--crop-x {crop[0]}", f"--crop-width {crop[2]}", f"-v {url}",
                 f"--remote-url {url}"):
        assert frag in s
    assert "--auto-crop" not in cmd and ("--flip-normals" in cmd) == flip
    with pytest.raises(PermissionError):
        Wn.render_command("s3://vesuvius-challenge-open-data/PHerc0841/volumes/x.zarr/", "m", "o", 9.366)
    md = {"scan": {"tomo": {"acquisition": {"detector": {"samplePixelSize": 0.009362}}}}}
    assert Wn.voxel_size_from_metadata(md) == 9.362


def test_render_crop_refuses_to_leave_canvas(base):
    with pytest.raises(ValueError):
        base.maps.render_crop(10_000)


def test_j_windows_constants():
    assert Wn.J_WINDOWS_0841["J1"] == ("214732", 300, 2315)
    assert Wn.J_WINDOWS_0841["J5"] == ("022814", 1000, 2760)
    assert Wn.J_WINDOW_PX == 2136 and Wn.SEALED_CLEARANCE_PX == 256


# ---------------------------------------------------------------------------
# alignment gate on emulated renders
# ---------------------------------------------------------------------------

def texture(p):
    r = np.random.default_rng(11)
    k = r.normal(0, 1, (24, 3))
    k /= np.linalg.norm(k, axis=1, keepdims=True)
    lam = r.uniform(5, 16, 24)
    ph = r.uniform(0, 2 * np.pi, 24)
    x = np.asarray(p, float)
    out = np.zeros(x.shape[:-1])
    for i in range(24):
        out += np.sin(2 * np.pi * (x @ k[i]) / lam[i] + ph[i])
    return 128 + 12 * out


def emulate_stack(points, cv, shape, n, flip):
    co, no = C.emulate_gen(points, cv, shape)
    ok = C.render_valid(co, no)
    sgn = C.slice_normal_sign(flip)
    stack = np.zeros((n, *shape), np.float32)
    for k, off in enumerate(C.slice_offsets(n)):
        v = texture(co + off * sgn * no)
        v[~ok] = 0
        stack[k] = np.clip(v, 1, 255) * ok
    return stack


@pytest.fixture(scope="module")
def gate_case():
    mesh = cyl_mesh(shape=(45, 55), ripple=6.0)
    win = Wn.Window(260, 350, 256, 256)
    res = Wn.run_window(mesh, win, CENTRE, margin_px=32, convention_sign=-1)  # mirrored case
    org_cv = C.canvas_for(mesh.points, mesh.scale)
    Hc, Wc = org_cv.shape
    sv = np.zeros((28, Hc, Wc), np.float32)
    part = emulate_stack(mesh.points, org_cv.with_origin(win.y0, win.x0), (win.h, win.w), 28, True)
    sv[:, win.y0:win.y0 + win.h, win.x0:win.x0 + win.w] = part
    x, y, w, h = res.maps.render_crop(32)
    flip = C.flip_normals_after_orient(True, res.maps.flip_u, res.maps.flip_v)
    ours = emulate_stack(res.points, res.maps.lev.with_origin(y, x), (h, w), 31, flip)
    return res, sv, ours


def test_alignment_gate_passes_on_exact_chain(gate_case):
    res, sv, ours = gate_case
    g = Wn.alignment_gate(ours, sv, res.maps, render_margin_px=32)
    assert g["render_slice"] == 15 and g["render_slice_offset"] == 0.0
    assert g["sv_slices"] == [13, 14] and g["sv_slice_offsets"] == [-0.5, 0.5]
    assert g["passed"] and g["best_shift"] == [0, 0]
    assert g["ncc_zero_shift"] > 0.95
    assert g["control_ncc_max"] < g["ncc_zero_shift"] - 0.3


def test_alignment_gate_detects_misregistration(gate_case):
    res, sv, ours = gate_case
    x, y, _, _ = res.maps.render_crop(32)
    # claim the render starts 4 px further right: a 4 px misregistration
    g = Wn.alignment_gate(ours, sv, res.maps, render_origin=(y, x + 4))
    assert not g["passed"]
    assert 3.0 <= g["best_shift_norm"] <= 5.0


def test_slice_direction_matches_organizer_after_mirror(gate_case):
    """With flip_normals_after_orient, our slice 15 + d matches the organizer
    slice at the same signed offset (e.g. ours 17 (+2) vs organizer 15 (+1.5)
    better than vs organizer 12 (-1.5))."""
    res, sv, ours = gate_case
    m = res.maps
    x, y, _, _ = m.render_crop(32)
    w = m.window
    sv_full = sv.copy()
    org_cv = C.canvas_for(cyl_mesh(shape=(45, 55), ripple=6.0).points, (0.05, 0.05))
    sv_full[:, w.y0:w.y0 + w.h, w.x0:w.x0 + w.w] = emulate_stack(
        cyl_mesh(shape=(45, 55), ripple=6.0).points, org_cv.with_origin(w.y0, w.x0), (w.h, w.w), 28, True)
    a = Wn.resample_to_organizer(ours[17].astype(float), m, w, lev_origin=(y, x))
    same = Wn.ncc(a, sv_full[15, w.y0:w.y0 + w.h, w.x0:w.x0 + w.w])[0]
    opp = Wn.ncc(a, sv_full[12, w.y0:w.y0 + w.h, w.x0:w.x0 + w.w])[0]
    assert same > 0.8 and same > opp + 0.3
