# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic validation of the geometry-only handedness rule
(tools/sib/handed/handed.py). Numbers only: every render is scored by
normalised cross-correlation against the glyph template and its mirror
images; nothing is displayed.

Run: PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/sib_handed_synthetic.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "sib" / "handed"))
sys.path.insert(0, str(ROOT / "src"))

import handed as H  # noqa: E402
import synth as S  # noqa: E402
from hercules.geometry import level_mesh as L  # noqa: E402
from hercules.geometry import render_synth as RS  # noqa: E402
from hercules.geometry import tifxyz as T  # noqa: E402

SHAPE = (110, 140, 140)
CENTRE = (70.0, 70.0)
PIX = 1.5
Z_C = 55.0
PHI_G = np.radians(35.0)
K_G = 1
MARGIN = 0.2


def spiral(w=1):
    return S.Spiral(centre=CENTRE, r_outer=62.0, pitch=9.0, turns=4.5, phi_start=np.radians(-20.0), w=w)


def _score(img, tpl):
    img = np.nan_to_num(np.asarray(img, np.float32))
    return float(cv2.matchTemplate(img, tpl.astype(np.float32), cv2.TM_CCOEFF_NORMED).max())


def mirror_scores(img, g):
    return dict(id=_score(img, g), lr=_score(img, np.fliplr(g)), ud=_score(img, np.flipud(g)),
                rot180=_score(img, np.rot90(g, 2)))


@pytest.fixture(scope="module", params=["R", "K"])
def scene(request):
    g = S.font_glyph(request.param)
    sc = S.spiral_glyph_volume(SHAPE, spiral(), g, k_glyph=K_G, phi_g=PHI_G, z_c=Z_C, pix=PIX)
    sc.glyph_char = request.param
    return sc


def source_grid(sc, angle_deg=30.0, n=44):
    step = PIX
    a = np.radians(angle_deg)
    uc = vc = (n - 1) / 2
    s0 = 0.0 - step * (uc * np.cos(a) - vc * np.sin(a))
    z0 = Z_C - step * (uc * np.sin(a) + vc * np.cos(a))
    return S.spiral_sheet_grid(sc.spiral, K_G, (n, n), step, angle_deg, s0=s0, z0=z0, phi_ref=PHI_G)


def centroid_curve(vol, sigma=8.0):
    planes = {float(z): vol[z] for z in range(0, vol.shape[0], 2)}
    return H.centroid_track(planes, level=0, thresh=0.01, sigma=sigma)


def rule_render(vol, src, props, *, override_sign=None, centre=None):
    fi = H.frame_info(S.ZATTRS_ZYX, props)
    sign = H.predicted_convention(fi) if override_sign is None else override_sign
    cc = centre if centre is not None else centroid_curve(vol).curve
    lv = L.level_mesh(src, step_vox=PIX)
    o = L.orient_for_reading(lv.points, fi.z_ascending_display, sign, outward=cc)
    assert o.chirality_after == sign
    stack = RS.render_along_normals(vol, o.points, T.vertex_normals(o.points), n=5)
    return stack.mean(0), o, fi


# ---------------------------------------------------------------------------

def test_glyphs_are_mirror_asymmetric():
    for ch in "RK":
        g = S.font_glyph(ch)
        pad = np.pad(g, 6)
        assert _score(pad, np.fliplr(g)) < 0.7, ch  # a mirror-symmetric glyph could not test anything
        assert _score(pad, g) > 0.999


def test_frame_info_parity():
    fi = H.frame_info(S.ZATTRS_ZYX, dict(left_handed_coordinates=False, z_direction_is_top_to_bottom=True))
    assert fi.parity == 1 and fi.z_ascending_display is True
    fi = H.frame_info(S.ZATTRS_ZYX, dict(left_handed_coordinates=True, z_direction_is_top_to_bottom=None))
    assert fi.parity == -1 and fi.z_ascending_display is None
    assert H.frame_info(S.ZATTRS_ZYX, {}).parity == 0
    bad = {"multiscales": [{"axes": [{"name": "c"}, {"name": "y"}, {"name": "x"}]}]}
    assert H.frame_info(bad, dict(left_handed_coordinates=False)).parity == 0
    np.testing.assert_array_equal(H.text_side_vector("-y"), [0, -1, 0])
    assert H.text_side_vector("up") is None


KINDS = ["ascending", "rot180x", "reflect_z", "reflect_x"]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("param_flip", ["none", "u", "v", "uv"])
def test_planted_glyph_unmirrored(scene, kind, param_flip):
    """The rule (convention = parity from metadata, up from the z flag,
    r_out from the CT-mask centroid) renders the glyph unmirrored and upright
    for ascending / descending z, proper and improper frames, and any input
    (u, v) handedness."""
    src = source_grid(scene)
    if "u" in param_flip:
        src = np.ascontiguousarray(src[:, ::-1])
    if "v" in param_flip:
        src = np.ascontiguousarray(src[::-1])
    vol, pts, props = S.transform_scene(scene.vol, src, kind)
    img, o, fi = rule_render(vol, pts, props)
    s = mirror_scores(img, scene.glyph)
    assert s["id"] > 0.8, s
    assert s["id"] > s["lr"] + MARGIN, s
    if scene.glyph_char == "R":  # K is nearly up-down symmetric, so only R also tests 'upright'
        assert s["id"] > s["ud"] + MARGIN, s
        assert s["id"] > s["rot180"] + MARGIN, s


@pytest.mark.parametrize("kind", ["reflect_z", "reflect_x"])
def test_ignoring_parity_mirrors(scene, kind):
    """If a reflected frame is treated as right-handed (sign +1), the glyph
    comes out mirrored: the metadata parity is necessary."""
    vol, pts, props = S.transform_scene(scene.vol, source_grid(scene), kind)
    img, _, _ = rule_render(vol, pts, props, override_sign=+1)
    s = mirror_scores(img, scene.glyph)
    assert s["lr"] > s["id"] + MARGIN, s  # orient mirrored u: a left-right mirror image


def test_descending_z_is_not_a_mirror_in_a_proper_frame(scene):
    """A scroll mounted upside down (rot180x: z descends, frame right-handed)
    needs the SAME sign as ascending z; using -1 because 'z descends' mirrors."""
    vol, pts, props = S.transform_scene(scene.vol, source_grid(scene), "rot180x")
    img_ok, _, _ = rule_render(vol, pts, props)
    img_bad, _, _ = rule_render(vol, pts, props, override_sign=-1)
    g = scene.glyph
    assert mirror_scores(img_ok, g)["id"] > 0.8
    sb = mirror_scores(img_bad, g)
    assert sb["lr"] > sb["id"] + MARGIN, sb


def test_geometric_centre_gives_same_state(scene):
    """r_out from the mesh itself (least-squares normal-line centre, no CT)
    reproduces the unmirrored state on a patch of one winding."""
    from hercules.pipeline.centre import geometric_centre_curve

    src = source_grid(scene, n=60)
    cc, info = geometric_centre_curve(src, z_bin_vox=1000.0, min_vertices=20, stride=1)
    img, _, _ = rule_render(scene.vol, src, dict(left_handed_coordinates=False, z_direction_is_top_to_bottom=True),
                            centre=cc)
    s = mirror_scores(img, scene.glyph)
    assert s["id"] > 0.8 and s["id"] > s["lr"] + MARGIN, s


def test_fragment_text_side_rule():
    """Fragment: flat sheet in the x-z plane, ink on the -y face. The rule
    n_out = -text_side (= +y) with convention = parity renders unmirrored."""
    g = S.font_glyph("R")
    Z, Y, X = 70, 40, 70
    zz, yy, xx = np.meshgrid(np.arange(Z, dtype=float), np.arange(Y, dtype=float), np.arange(X, dtype=float),
                             indexing="ij")
    y0 = 20.0
    # a viewer on the -y side looking toward +y, top = low z, sees +x on the left. Compute: into-screen = +y,
    # up = -z, right = into x up = (+y) x (-z) = -x. So glyph column increases toward -x.
    col = (35.0 - xx) / PIX + (g.shape[1] - 1) / 2
    row = (zz - 35.0) / PIX + (g.shape[0] - 1) / 2
    ink = cv2.remap(g, col[:, 0, :].astype(np.float32), row[:, 0, :].astype(np.float32), cv2.INTER_LINEAR)
    vol = 0.3 * np.exp(-0.5 * ((yy - y0) / 1.0) ** 2) + ink[:, None, :] * np.exp(-0.5 * ((yy - (y0 - 1.2)) / 0.9) ** 2)
    vol = vol.astype(np.float32)
    vv, uu = np.mgrid[0:40, 0:40].astype(float)
    src = np.stack([5 + PIX * uu, np.full_like(uu, y0), 5 + PIX * vv], -1).astype(np.float32)
    n_out = -H.text_side_vector("-y")
    fi = H.frame_info(S.ZATTRS_ZYX, dict(left_handed_coordinates=False, z_direction_is_top_to_bottom=True))
    for s in (src, np.ascontiguousarray(src[:, ::-1])):
        lv = L.level_mesh(s, step_vox=PIX)
        o = L.orient_for_reading(lv.points, True, H.predicted_convention(fi), outward=n_out)
        img = RS.render_along_normals(vol, o.points, T.vertex_normals(o.points), n=5).mean(0)
        sc = mirror_scores(img, g)
        assert sc["id"] > 0.8 and sc["id"] > sc["lr"] + MARGIN, sc


# ---------------------------------------------------------------------------
# normal-sign tests at several angles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("phi_deg", list(range(0, 360, 30)))
def test_normal_sign_spiral_centroid(phi_deg):
    sp = spiral()
    sc = S.spiral_glyph_volume(SHAPE, sp, S.font_glyph("R"), k_glyph=K_G, phi_g=PHI_G, z_c=Z_C, pix=PIX)
    cc = centroid_curve(sc.vol).curve
    p = S.spiral_sheet_grid(sp, 2, (12, 12), 2.0, 20.0, s0=-12.0, z0=30.0, phi_ref=np.radians(phi_deg))
    n = T.vertex_normals(p)
    rep = L.normal_sign_report(p, n, cc)
    assert rep.sign == 1 and not rep.ambiguous, (phi_deg, rep.frac_clear, rep.frac_positive)
    assert L.normal_sign_report(p, -n, cc).sign == -1
    st = H.chirality_stats(p, cc)
    assert st["sign"] == 1 and st["agreement"] == 1.0
    assert H.chirality_stats(np.ascontiguousarray(p[:, ::-1]), cc)["sign"] == -1


@pytest.mark.parametrize("phi_deg", [0, 45, 90, 135, 180, 270])
def test_normal_sign_crushed_scroll_flags(phi_deg):
    """Crushed (oval, axis ratio 0.3) cross-section: where the sheet normal is
    near-perpendicular to the centroid direction (ends of the major axis) the
    report is flagged ambiguous; where it is clear, the sign is right."""
    sp = spiral()
    p = S.spiral_sheet_grid(sp, 2, (12, 12), 2.0, 0.0, s0=-12.0, z0=30.0, phi_ref=np.radians(phi_deg)).astype(np.float64)
    p[..., 1] = CENTRE[1] + 0.3 * (p[..., 1] - CENTRE[1])
    cc = L.CentreCurve.straight(*CENTRE)
    rep = L.normal_sign_report(p, T.vertex_normals(p), cc)
    if rep.ambiguous:
        assert phi_deg in (0, 180) or rep.frac_clear < 0.8
    else:
        assert rep.sign == 1


def test_undetermined_rout_is_flagged():
    """Radial sheet (normal perpendicular to r_out everywhere): chirality 0 and
    the mesh prediction is FLAG."""
    vv, uu = np.mgrid[0:10, 0:10].astype(np.float64)
    p = np.stack([450.0 + 20 * uu, np.full_like(uu, 400.0), 100 + 20 * vv], axis=-1).astype(np.float32)
    cc = L.CentreCurve.straight(400.0, 400.0)
    fi = H.frame_info(S.ZATTRS_ZYX, dict(left_handed_coordinates=False, z_direction_is_top_to_bottom=True))
    pred = H.predict_mesh("radial", p, cc, fi, r_out_source="test")
    assert pred.native_chirality["sign"] == 0
    assert H.confidence(pred, []) == "FLAG"
    assert any("undetermined" in f for f in pred.flags)


# ---------------------------------------------------------------------------
# cylinder round trip
# ---------------------------------------------------------------------------

def test_cylinder_round_trip():
    R, C = 300.0, (400.0, 400.0)
    p = RS.cylinder_grid(R, C, (40, 40), 20.0, 30.0, s0=-400.0, z0=100.0)
    lv = L.level_mesh(p, step_vox=10.0)
    back = lv.map_back(p.shape[:2])
    ok = T.valid_mask(back) & T.valid_mask(p)
    assert ok.mean() > 0.8
    err = np.linalg.norm(back[ok] - p[ok], axis=-1)
    # two bilinear resamplings (level, map back); each has chord error <= sagitta of a cell
    # diagonal d: d^2 / (8 R) with d = 10 sqrt(2) vox -> 0.083 vox; bound = 2 x that
    bound = 2 * (2 * 10.0 ** 2) / (8 * R)
    assert err.max() < bound, (err.max(), bound)
    cc = L.CentreCurve.straight(*C)
    assert L.chirality(p, cc) == 1 and L.chirality(lv.points, cc) == 1  # level_mesh is a proper rotation
    for zasc in (True, False):
        for sign in (1, -1):
            o = L.orient_for_reading(lv.points, zasc, sign, outward=cc)
            assert o.chirality_after == sign
            np.testing.assert_array_equal(o.apply(o.apply(lv.points)), lv.points)  # flips are involutions
    # chirality: reversed by a u- or v-mirror, kept by a 180 deg grid rotation
    assert L.chirality(p[:, ::-1], cc) == -1 and L.chirality(p[::-1], cc) == -1
    assert L.chirality(p[::-1, ::-1], cc) == 1
    # the predicted state for this mesh: native grid (u ~ +phi, v ~ +z) is legible
    fi = H.frame_info(S.ZATTRS_ZYX, dict(left_handed_coordinates=False, z_direction_is_top_to_bottom=True))
    pr = H.predict_mesh("cyl", p, cc, fi, r_out_source="exact")
    assert pr.native_legible is True and pr.mirror_u_needed is False and pr.flip_v_needed is False
    assert H.confidence(pr, [1.0]) == "HIGH"


# ---------------------------------------------------------------------------
# winding sense and the (weaker) up-direction consistency check
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("w", [1, -1])
def test_winding_sense_measured(w):
    sp = spiral(w)
    g = S.spiral_row_grid(sp, 400, 6, 10.0, 5.0, theta0=0.3, dtheta=2.5 * 2 * np.pi / 400)
    cc = L.CentreCurve.straight(*CENTRE)
    ws = H.winding_sense(g, cc)
    assert ws["w"] == w and ws["agreement"] == 1.0
    assert ws["dr_per_turn_median"] == pytest.approx(-9.0 * w, abs=0.5)  # one pitch per turn
    short = H.winding_sense(g[:, :100], cc)  # < 1 turn: undetermined
    assert short["w"] == 0


@pytest.mark.parametrize("kind", KINDS)
def test_winding_predicts_up_for_a_physical_roll(kind):
    """A physical roll (text read inward, top at low z in the ascending build,
    w = +1): w * parity = +1 iff text top at low z, in every frame."""
    sp = spiral(1)
    g = S.spiral_row_grid(sp, 400, 6, 10.0, 5.0, theta0=0.3, dtheta=2.5 * 2 * np.pi / 400)
    vol = np.zeros(SHAPE, np.float32)
    vol2, g2, props = S.transform_scene(vol, g, kind)
    Z, Y, X = SHAPE
    c = np.array([CENTRE[0], CENTRE[1]])
    if kind == "rot180x":
        c[1] = (Y - 1) - c[1]
    if kind == "reflect_x":
        c[0] = (X - 1) - c[0]
    ws = H.winding_sense(g2, L.CentreCurve.straight(*c))
    fi = H.frame_info(S.ZATTRS_ZYX, props)
    assert (ws["w"] * fi.parity == 1) == props["z_direction_is_top_to_bottom"]
