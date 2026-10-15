# Provenance: Project HERCULES | owner the owner | [id removed]
"""Handedness, outward-normal sign and slice-index tests on synthetic
volumes (render_synth is a test helper only)."""

import cv2
import numpy as np
import pytest

from hercules.geometry import level_mesh as L
from hercules.geometry import render_synth as RS
from hercules.geometry import tifxyz as T

# small synthetic scroll: cylinder radius 60 vox, glyph 'F' 20x14 px at 2 vox/px
SHAPE = (100, 150, 150)  # (Z, Y, X)
CENTRE = (75.0, 75.0)
RAD = 60.0
PIX = 2.0
MARGIN = 0.2  # required correlation margin, unmirrored over mirrored


@pytest.fixture(scope="module")
def glyph():
    return RS.glyph_F()


@pytest.fixture(scope="module")
def scene(glyph):
    """Volume with the glyph readable from OUTSIDE with its top at LOW z, and
    a source mesh whose (u, v) is rotated 30 deg relative to iso-z."""
    vol = RS.cylinder_glyph_volume(SHAPE, CENTRE, RAD, glyph, phi0=0.0, z0=30.0, pix_vox=PIX)
    H = W = 14
    step, a = 10.0, np.radians(30.0)
    uc = vc = (H - 1) / 2
    s_c, z_c = -14.0, 50.0  # glyph centre (arc, z) in the grid's unrolled coords
    s0 = s_c - step * (uc * np.cos(a) - vc * np.sin(a))
    z0 = z_c - step * (uc * np.sin(a) + vc * np.cos(a))
    src = RS.cylinder_grid(RAD, CENTRE, (H, W), step, 30.0, s0=s0, z0=z0)
    return vol, src


def _score(img, tpl):
    img = np.nan_to_num(img).astype(np.float32)
    return float(cv2.matchTemplate(img, tpl.astype(np.float32), cv2.TM_CCOEFF_NORMED).max())


def _render_read(vol, src, centre, z_ascending, sign, n=5):
    lv = L.level_mesh(src, step_vox=PIX)
    o = L.orient_for_reading(lv.points, z_ascending, sign, outward=centre)
    assert o.chirality_after == sign
    stack = RS.render_along_normals(vol, o.points, T.vertex_normals(o.points), n=n)
    return stack[n // 2]


def _mirror_scores(img, glyph):
    return _score(img, glyph), _score(img, np.fliplr(glyph))


def _transform(scene, kind):
    vol, src = scene
    Z, Y, _ = SHAPE
    src = src.copy()
    if kind == "ascending":
        return vol, src, L.CentreCurve.straight(*CENTRE)
    if kind == "descending_reflected":  # flip z of volume and mesh (a mirror)
        src[..., 2] = (Z - 1) - src[..., 2]
        return np.ascontiguousarray(vol[::-1]), src, L.CentreCurve.straight(*CENTRE)
    if kind == "descending_rotated":  # scroll upside down: 180 deg about x (proper rotation)
        src[..., 2] = (Z - 1) - src[..., 2]
        src[..., 1] = (Y - 1) - src[..., 1]
        return np.ascontiguousarray(vol[::-1, ::-1]), src, L.CentreCurve.straight(CENTRE[0], (Y - 1) - CENTRE[1])
    raise ValueError(kind)


# (case, z_ascending, matching convention sign). -1 = legible from the
# outward side. A reflection (z flip) swaps the legible face -> sign flips;
# a rigid rotation keeps it.
CASES = [
    ("ascending", True, -1),
    ("descending_reflected", False, +1),
    ("descending_rotated", False, -1),
]


@pytest.mark.parametrize("kind,z_asc,sign", CASES)
@pytest.mark.parametrize("mirror_source", [False, True])
def test_glyph_unmirrored_with_matching_convention(scene, glyph, kind, z_asc, sign, mirror_source):
    vol, src, centre = _transform(scene, kind)
    if mirror_source:  # the input parameterisation's handedness must not matter
        src = np.ascontiguousarray(src[:, ::-1])
    img = _render_read(vol, src, centre, z_asc, sign)
    s_id, s_lr = _mirror_scores(img, glyph)
    assert s_id > 0.8
    assert s_id > s_lr + MARGIN
    assert s_id > _score(img, np.flipud(glyph)) + MARGIN  # also not upside down


@pytest.mark.parametrize("kind,z_asc,sign", CASES)
def test_glyph_mirrored_with_wrong_convention(scene, glyph, kind, z_asc, sign):
    vol, src, centre = _transform(scene, kind)
    img = _render_read(vol, src, centre, z_asc, -sign)
    s_id, s_lr = _mirror_scores(img, glyph)
    assert s_lr > s_id + MARGIN


def test_orient_flags_and_apply():
    src = RS.cylinder_grid(300.0, (400.0, 400.0), (12, 12), 20.0, 0.0, z0=50.0)
    cc = L.CentreCurve.straight(400.0, 400.0)
    assert L.chirality(src, cc) == 1  # du ~ +phi, dv ~ +z, n_out = r: det = +1
    o = L.orient_for_reading(src, True, -1, outward=cc)
    assert o.flip_u and not o.flip_v and o.levelled_ok and o.z_trend > 0
    np.testing.assert_array_equal(o.apply(src), o.points)
    o2 = L.orient_for_reading(src, False, -1, outward=cc)
    assert o2.flip_v and not o2.flip_u and o2.z_trend < 0  # v flip alone reverses chirality
    with pytest.raises(ValueError):
        L.orient_for_reading(src, True, 0, outward=cc)


@pytest.mark.parametrize("angle_deg", [0, 90, 180, 270])
def test_normal_sign_around_cylinder(angle_deg):
    cc = L.CentreCurve.straight(400.0, 400.0)
    p = RS.cylinder_grid(300.0, (400.0, 400.0), (12, 12), 20.0, 30.0,
                         s0=-110.0, z0=100.0, phi_ref=np.radians(angle_deg))
    n = T.vertex_normals(p)
    rep = L.normal_sign_report(p, n, cc)
    assert rep.sign == 1 and not rep.ambiguous and rep.frac_clear == 1.0
    assert np.nanmin(rep.cos) > 0.99
    # inward-facing normals are detected and fixed by a global flip
    rep_in = L.normal_sign_report(p, -n, cc)
    assert rep_in.sign == -1 and not rep_in.ambiguous
    fixed, rep0 = L.orient_normals_outward(p, -n, cc)
    assert rep0.sign == -1
    assert L.normal_sign_report(p, fixed, cc).sign == 1
    # a u-mirrored parameterisation yields inward normals
    assert L.normal_sign_report(p[:, ::-1], T.vertex_normals(p[:, ::-1]), cc).sign == -1


def test_normal_sign_ambiguous_for_radial_sheet():
    cc = L.CentreCurve.straight(400.0, 400.0)
    vv, uu = np.mgrid[0:10, 0:10].astype(np.float64)
    p = np.stack([450.0 + 20 * uu, np.full_like(uu, 400.0), 100 + 20 * vv], axis=-1).astype(np.float32)
    rep = L.normal_sign_report(p, T.vertex_normals(p), cc)
    assert rep.ambiguous and rep.frac_clear == 0.0


def test_curved_centre_curve():
    # tilted umbilicus: c(z) = (400 + 0.1 z, 400)
    cc = L.CentreCurve(z=[0.0, 1000.0], x=[400.0, 500.0], y=[400.0, 400.0])
    p = np.array([[[700.0, 400.0, 0.0], [600.0, 400.0, 1000.0]]], dtype=np.float32)
    r = L.outward_directions(p, cc)
    np.testing.assert_allclose(r[0, 0], [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(r[0, 1], [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(cc(np.array([500.0]))[0], [450.0])


@pytest.mark.parametrize("normal_sign", [1, -1])
def test_slice_index_plane(normal_sign):
    n = 31
    x0 = 20.0
    vol = RS.plane_volume((40, 40, 48), [x0, x0 + 5.0], amplitudes=[1.0, 0.5])
    vv, uu = np.mgrid[0:6, 0:6].astype(np.float64)
    y = 8 + 4 * vv
    z = 8 + 4 * uu
    p = np.stack([np.full_like(y, x0), y, z], axis=-1).astype(np.float32)
    if normal_sign < 0:
        p = np.ascontiguousarray(p[:, ::-1])
    nrm = T.vertex_normals(p)  # du=+z, dv=+y -> du x dv = -x
    sx = int(np.sign(np.nanmean(nrm[..., 0])))
    stack = RS.render_along_normals(vol, p, nrm, n=n)
    assert stack.shape == (n, 6, 6)
    prof = np.nanmean(stack, axis=(1, 2))
    assert int(np.argmax(prof)) == n // 2
    assert prof[n // 2] > 0.99
    # the marker plane 5 vox along +x appears 5 slices along the normal
    k = n // 2 + 5 * sx
    assert prof[k] == pytest.approx(0.5, abs=0.02)
    assert prof[n // 2 - 5 * sx] < 0.01


def test_slice_index_oblique_plane():
    n = 31
    nhat = np.array([0.6, 0.48, 0.64])
    nhat /= np.linalg.norm(nhat)
    q0 = np.array([30.0, 30.0, 30.0])
    zz, yy, xx = np.meshgrid(*(np.arange(60.0),) * 3, indexing="ij")
    dist = (xx - q0[0]) * nhat[0] + (yy - q0[1]) * nhat[1] + (zz - q0[2]) * nhat[2]
    vol = np.exp(-0.5 * (dist / 0.8) ** 2).astype(np.float32)
    e1 = np.cross(nhat, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(nhat, e1)
    vv, uu = np.mgrid[-3:4, -3:4].astype(np.float64)
    p = (q0 + 3 * uu[..., None] * e1 + 3 * vv[..., None] * e2).astype(np.float32)
    stack = RS.render_along_normals(vol, p, T.vertex_normals(p), n=n)
    prof = np.nanmean(stack, axis=(1, 2))
    assert int(np.argmax(prof)) == n // 2
