# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests of tools/sib/p4-core/trace_metrics.py (DECL-P4-7 item 3 metrics) on
synthetic spirals and synthetic texture arrays only. Each metric must pass
on a clean synthetic case and detect its planted defect."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
P4 = ROOT / "tools" / "sib" / "p4-core"
sys.path.insert(0, str(P4))

import synth_spiral as ss  # noqa: E402
import trace_metrics as tm  # noqa: E402

PITCH = 60.0
FLAT_BLOB_SHA1 = "67f6785543a17b887f12cacbb82c1e608daad5df"
FLAT_SHA256 = "bc5056bf2f269153237942271473ede4def6beb4bca8792b9b8a83a6328d2d5b"
FLAT_REF = "origin/claude/gifted-bell-gavnl5-sib-flat1:tools/sib/flat1/flatlib.py"
MARKER = b"# ---- BEGIN VERBATIM FLAT-2 flatlib.py ----\n"


@pytest.fixture(scope="module")
def world():
    """Squashed spiral around a drifting, wobbling axis; w010 = turns
    10..11.3 (so some rays see w010 twice -> local spacing), w011 for the
    independent spacing of metric (c)."""
    umb = ss.make_umbilicus(500.0, 400.0, drift=(0.02, -0.01), wobble=5.0)
    sp = ss.Spiral(r0=40.0, pitch=PITCH, squash=(1.1, 0.9), umb=umb)
    rng = np.random.default_rng(7)
    w010 = ss.spiral_grid(sp, 10, 11.3, 0, 800, noise=0.3, rng=rng)["points"]
    w011 = ss.spiral_grid(sp, 11, 12.3, 0, 800, noise=0.3, rng=rng)["points"]
    g = ss.spiral_grid(sp, 9.05, 9.95, 0, 800, noise=0.3, rng=rng)
    return {"umb": umb, "sp": sp, "w010": w010, "w011": w011, "trace": g["points"], "g": g, "rng": rng}


# ---------------------------------------------------------------------------
# provenance of the FLAT-2 copy
# ---------------------------------------------------------------------------

def test_flatlib_copy_is_verbatim_blob():
    b = (P4 / "flatlib_flat2.py").read_bytes()
    body = b[b.index(MARKER) + len(MARKER):]
    assert hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest() == FLAT_BLOB_SHA1
    assert hashlib.sha256(body).hexdigest() == FLAT_SHA256
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", FLAT_REF], capture_output=True, check=True).stdout
    except Exception:
        pytest.skip("source branch not available in this clone; blob sha1 already verified")
    assert hashlib.sha256(src).hexdigest() == hashlib.sha256(body).hexdigest()


# ---------------------------------------------------------------------------
# (a) self-intersection
# ---------------------------------------------------------------------------

def _seg_tri(P, Q, T):
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    d, e1, e2 = Q - P, b - a, c - a
    pv = np.cross(d, e2)
    det = (e1 * pv).sum(1)
    tv = P - a
    u = (tv * pv).sum(1) / det
    qv = np.cross(tv, e1)
    v = (d * qv).sum(1) / det
    t = (e2 * qv).sum(1) / det
    return (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)


def test_tri_tri_matches_edge_crossing_reference():
    """Non-coplanar triangles intersect iff an edge of one crosses the other."""
    rng = np.random.default_rng(0)
    n = 50_000
    A = rng.uniform(0, 1, (n, 3, 3))
    B = rng.uniform(0, 1, (n, 3, 3)) + rng.uniform(-0.5, 0.5, (n, 1, 3))
    ref = np.zeros(n, bool)
    for X, Y in ((A, B), (B, A)):
        for i in range(3):
            ref |= _seg_tri(X[:, i], X[:, (i + 1) % 3], Y)
    got = tm.tri_tri_intersect(A, B)
    assert 0.05 < ref.mean() < 0.5
    assert np.array_equal(got, ref)


def test_self_intersection_clean_vs_fold(world):
    sp = world["sp"]
    r = tm.self_intersection(world["trace"])
    assert r["n_intersecting_pairs"] == 0 and r["pass"] is True
    assert r["n_candidate_pairs_nonadjacent"] > 0  # broadphase actually tested something
    W = world["trace"].shape[1]
    c0, K = 60, 16
    ds, dr = ss.fold_offsets(W, c0, K=K, a=2.5, b=12.0)
    fold = ss.spiral_grid(sp, 9.05, 9.95, 0, 800, ds=ds, dr=dr, noise=0.3, rng=np.random.default_rng(1))["points"]
    f = tm.self_intersection(fold)
    assert f["pass"] is False
    H = fold.shape[0]
    assert f["n_intersecting_pairs"] >= H - 1  # at least one crossing per row of quads
    assert f["pairs_per_cm2"] > 0
    cols = np.array([[p[0][1], p[1][1]] for p in f["example_pairs_quad_rc"]])
    assert cols.min() >= c0 - 1 and cols.max() <= c0 + K
    # a gentle fold (a < 1) does not cross itself
    ds2, dr2 = ss.fold_offsets(W, c0, K=K, a=0.8, b=12.0)
    g = ss.spiral_grid(sp, 9.05, 9.95, 0, 800, ds=ds2, dr=dr2)["points"]
    assert tm.self_intersection(g)["n_intersecting_pairs"] == 0


def test_self_intersection_timing_2e5():
    sp = ss.Spiral(r0=40.0, pitch=PITCH, umb=ss.make_umbilicus(0, 0, drift=(0.01, 0.0)))
    g = ss.spiral_grid(sp, 10, 11.6, 0, 6400, noise=0.5, rng=np.random.default_rng(2))["points"]
    t0 = time.perf_counter()
    r = tm.self_intersection(g)
    dt = time.perf_counter() - t0
    print(f"\nself_intersection: {r['n_triangles']} triangles in {dt:.2f} s")
    assert r["n_triangles"] >= 200_000
    assert r["n_intersecting_pairs"] == 0
    assert dt < 60.0


# ---------------------------------------------------------------------------
# (b) winding
# ---------------------------------------------------------------------------

def test_winding_coordinate_unwraps_consistently(world):
    g = world["g"]
    wc = tm.winding_coordinate(world["trace"], world["umb"], seed=(20, 100))
    assert wc["n_components"] == 1
    d = wc["w"] - g["theta"] / (2 * np.pi)
    # constant integer offset over the mesh, up to the squash (1.1 / 0.9)
    # which moves the geometric angle off the parametric one by <= 0.1 rad
    assert np.nanmax(d) - np.nanmin(d) < 0.04
    assert abs(np.nanmedian(d) - np.rint(np.nanmedian(d))) < 0.02
    assert np.nanmax(wc["w"]) - np.nanmin(wc["w"]) == pytest.approx(0.9, abs=0.02)


def test_winding_clean_trace(world):
    r = tm.winding_continuity(world["trace"], world["w010"], world["umb"], expected_offset=-1)
    json.dumps(r)
    assert r["pass"] is True
    assert r["offset_mode"] == -1 and r["offset_mode_frac"] >= 0.98
    assert r["n_jumps"] == 0 and r["frac_continuous_pairs"] == 1.0
    assert r["frac_inside_w010"] == 1.0 and r["frac_rays_hit_w010"] > 0.95
    assert r["phase_mode_frac"] == 1.0 and r["phase_max_abs_residual"] < 1e-6
    assert r["spacing_median_vox"] == pytest.approx(PITCH, rel=0.15)


def test_winding_planted_offset_two(world):
    t2 = ss.spiral_grid(world["sp"], 8.05, 8.95, 0, 800, noise=0.3, rng=np.random.default_rng(3))["points"]
    r = tm.winding_continuity(t2, world["w010"], world["umb"], expected_offset=-2)
    assert r["offset_mode"] == -2 and r["offset_mode_frac"] >= 0.98
    assert r["offset_count_only_mode"] == -1  # no trace sheet between: the radial term finds the skipped winding
    assert r["n_jumps"] == 0 and r["pass"] is True
    assert tm.winding_continuity(t2, world["w010"], world["umb"], expected_offset=-1)["pass"] is False


def test_winding_multi_turn_trace_is_continuous(world):
    tm3 = ss.spiral_grid(world["sp"], 7.1, 9.95, 0, 800)["points"]
    r = tm.winding_continuity(tm3, world["w010"], world["umb"])
    assert r["n_jumps"] == 0 and r["pass"] is True
    h = r["offset_hist"]
    for k in ("-1", "-2", "-3"):
        assert h.get(k, 0) > 0.2 * r["n_rays_hit_w010"]
    assert r["phase_mode_frac"] == 1.0


def test_winding_jump_detected_at_the_right_place(world):
    H, W = world["trace"].shape[:2]
    cj = W // 2
    jt = ss.spiral_grid(world["sp"], 9.05, 9.95, 0, 800, dr=ss.jump_offsets(H, W, cj, PITCH))["points"]
    r = tm.winding_continuity(jt, world["w010"], world["umb"], expected_offset=-1, max_report=10_000)
    assert r["pass"] is False
    assert r["n_jumps"] >= H - 2  # one per row (edge rows may miss w010 in z)
    locs = np.array(r["jump_pairs_rc"])
    assert np.all(locs[:, 1] == cj - 1) and np.all(locs[:, 3] == cj) and np.all(locs[:, 0] == locs[:, 2])
    assert r["offset_hist"].get("-1", 0) > 0.3 * r["n_rays_hit_w010"]
    assert r["offset_hist"].get("-2", 0) > 0.3 * r["n_rays_hit_w010"]


def test_winding_trace_outside_w010_fails(world):
    out = ss.spiral_grid(world["sp"], 11.4, 11.9, 0, 800)["points"]
    r = tm.winding_continuity(out, world["w010"], world["umb"])
    assert r["frac_inside_w010"] < 0.5 and r["pass"] is False


# ---------------------------------------------------------------------------
# (c) neighbour distance
# ---------------------------------------------------------------------------

def test_point_triangle_distance_vs_dense_sampling():
    rng = np.random.default_rng(4)
    A, B, C = rng.normal(size=(3, 3))
    P = rng.normal(size=(200, 3)) * 2
    d = tm.point_triangle_distance(P, *(np.broadcast_to(x, P.shape) for x in (A, B, C)))
    u, v = np.meshgrid(np.linspace(0, 1, 301), np.linspace(0, 1, 301))
    m = (u + v) <= 1
    S = A + u[m, None] * (B - A) + v[m, None] * (C - A)
    ref = np.min(np.linalg.norm(P[:, None] - S[None], axis=2), axis=1)
    assert np.all(d <= ref + 1e-9)
    assert np.max(ref - d) < 0.02


def test_neighbour_ratio_clean_vs_too_close(world):
    umb = world["umb"]
    pair = (world["w010"], world["w011"])
    c = tm.neighbour_distance_ratio(world["trace"], world["w010"], None, umb=umb, spacing_pair=pair)
    assert c["spacing_median_vox"] == pytest.approx(PITCH, rel=0.05)
    assert c["pass"] is True and c["frac_ratio_ge_threshold"] == 1.0
    assert 0.85 <= c["ratio_p5"] and 0.9 <= c["ratio_p50"] <= 1.1  # squash 1.1 / 0.9
    close = ss.spiral_grid(world["sp"], 9.05, 9.95, 0, 800, dr=0.7 * PITCH, noise=0.3,
                           rng=np.random.default_rng(5))["points"]
    d = tm.neighbour_distance_ratio(close, world["w010"], None, umb=umb, spacing_pair=pair)
    assert d["pass"] is False and d["frac_ratio_ge_threshold"] == 0.0
    assert 0.2 <= d["ratio_p50"] <= 0.4
    # unsquashed clean spiral: ratio ~ 1.0 with the true pitch
    sp0 = ss.Spiral(r0=40.0, pitch=PITCH, umb=umb)
    n0 = ss.spiral_grid(sp0, 10, 11, 0, 800)["points"]
    t0 = ss.spiral_grid(sp0, 9.1, 9.9, 0, 800)["points"]
    e = tm.neighbour_distance_ratio(t0, n0, PITCH)
    assert e["ratio_p50"] == pytest.approx(1.0, abs=0.02) and e["ratio_p1"] > 0.97
    with pytest.raises(ValueError):
        tm.neighbour_distance_ratio(t0, n0, None)  # no circular spacing from the trace itself


# ---------------------------------------------------------------------------
# (d) flattening distortion
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def patches():
    sp0 = ss.Spiral(r0=40.0, pitch=PITCH, umb=ss.make_umbilicus(0, 0, drift=(0.01, 0.0)))
    cyl = ss.spiral_grid(sp0, 10, 10.4, 0, 800)["points"]
    bump = ss.spiral_grid(sp0, 10, 10.4, 0, 800, dr=ss.bump_offsets(150.0, 120.0))["points"]
    return cyl, bump


@pytest.mark.parametrize("method", ["slim", "arap"])
def test_flattening_developable_vs_bump(patches, method):
    if not tm._have_igl():
        pytest.skip("libigl absent: FLAT-2 flatteners unavailable (fallback tested separately)")
    cyl, bump = patches
    a = tm.flattening_distortion(cyl, method=method)
    b = tm.flattening_distortion(bump, method=method)
    json.dumps(a)
    assert "flatlib_flat2" in a["flattener"]
    # developable (axis drift = sheared generalised cylinder): residual is
    # only the solver's stopping tolerance
    assert a["area_error_weighted_mean_abs_log"] < 1e-3 and a["angle_error_mean_deg"] < 0.05
    assert a["pct_quads_within_5pct"] == 100.0 and a["flipped_triangles"] == 0
    assert b["area_error_weighted_mean_abs_log"] > 0.01 and b["angle_error_mean_deg"] > 0.5
    assert b["pct_quads_within_5pct"] < 90.0
    assert a["pass"] is None  # report only: DECL-P4-7 gives no threshold
    thr = {"area_abs_log_max": 0.005, "angle_mean_deg_max": 0.5}
    assert tm.flattening_distortion(cyl, method=method, thresholds=thr)["pass"] is True
    assert tm.flattening_distortion(bump, method=method, thresholds=thr)["pass"] is False


def test_flattening_scipy_fallback_discriminates(patches, monkeypatch):
    monkeypatch.setattr(tm, "_have_igl", lambda: False)
    cyl, bump = patches
    a = tm.flattening_distortion(cyl)
    b = tm.flattening_distortion(bump)
    assert a["flattener"].startswith("FALLBACK")
    assert a["area_error_weighted_mean_abs_log"] < 1e-3 and a["angle_error_mean_deg"] < 0.05
    assert b["area_error_weighted_mean_abs_log"] > 0.01 and b["angle_error_mean_deg"] > 0.5


# ---------------------------------------------------------------------------
# (e) fibre coherence (synthetic arrays only)
# ---------------------------------------------------------------------------

def test_fibre_coherence_hv_vs_isotropic():
    rng = np.random.default_rng(6)
    ref = ss.hv_fibre_texture((512, 512), rng, noise=0.6)  # stands in for the w010 strip
    hv = ss.hv_fibre_texture((512, 512), rng, noise=0.1)
    hv_only_h = ss.hv_fibre_texture((512, 512), rng, w_v=0.0, noise=0.1)
    iso = ss.isotropic_texture((512, 512), rng)
    diag = ss.diagonal_fibre_texture((512, 512), rng, noise=0.1)
    r_hv = tm.fibre_coherence(hv, ref)
    json.dumps(r_hv)
    assert r_hv["pass"] is True and r_hv["hv4_median"] > 0.6
    assert tm.fibre_coherence(hv_only_h, ref)["pass"] is True
    r_iso = tm.fibre_coherence(iso, ref)
    assert r_iso["pass"] is False and abs(r_iso["hv4_median"]) < 0.15
    r_d = tm.fibre_coherence(diag, ref)
    assert r_d["pass"] is False and r_d["hv4_median"] < -0.5
    # reference given as a number, and NaN (masked) regions are tolerated
    hvn = hv.copy()
    hvn[:40, :] = np.nan
    r2 = tm.fibre_coherence(hvn, reference_median=r_hv["reference_hv4_median"])
    assert r2["pass"] is True and r2["n_windows"] == 56


# ---------------------------------------------------------------------------
# bundle
# ---------------------------------------------------------------------------

def test_run_all_clean_and_defect(world):
    rng = np.random.default_rng(8)
    ref = ss.hv_fibre_texture((256, 256), rng, noise=0.6)
    tex = ss.hv_fibre_texture((256, 256), rng, noise=0.1)
    kw = dict(spacing_pair=(world["w010"], world["w011"]), expected_offset=-1,
              reference_texture=ref)
    r = tm.run_all(world["trace"], world["w010"], world["umb"], trace_texture=tex, **kw)
    json.dumps(r)
    assert set(r["passed"]) == {"a", "b", "c", "e"} and r["failed"] == [] and r["report_only"] == ["d"]
    close = ss.spiral_grid(world["sp"], 9.05, 9.95, 0, 800, dr=0.7 * PITCH)["points"]
    r2 = tm.run_all(close, world["w010"], world["umb"], trace_texture=ss.isotropic_texture((256, 256), rng), **kw)
    assert "c" in r2["failed"] and "e" in r2["failed"] and r2["all_pass"] is False
