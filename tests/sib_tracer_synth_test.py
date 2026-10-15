# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for the rejection-gated tracer (build c, tools/sib/tracer/gate_c_41701aa.patch).

Tracer tests run the built official binaries inside the official deps image and are skipped when
docker or the builds are unavailable. The family is chosen by HRC_TRACER_FAMILY:
  "L" (default): task P + official villa-main parameter space_line_weight 0.1 (proposal);
  "S": the task P exactly. Measured result: S fails the full-area and continue tests on synthetic
       sheets (logs/sib/tracer/synth/verdicts.json); those cases are marked xfail for S only.
Criteria are fixed in tools/sib/tracer/synth_suite.py.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1] / "tools" / "sib" / "tracer"
sys.path.insert(0, str(HERE))

FAMILY = os.environ.get("HRC_TRACER_FAMILY", "L")
PRESETS = [f"{FAMILY}15", f"{FAMILY}20", f"{FAMILY}25"]


def _tracer_available() -> bool:
    try:
        from synth import BIN_GATED, BIN_VANILLA
    except Exception:
        return False
    if shutil.which("docker") is None:
        return False
    if subprocess.call(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        return False
    return Path(BIN_GATED, "vc_grow_seg_from_seed").exists() and Path(BIN_VANILLA, "vc_gen_normalgrids").exists()


needs_tracer = pytest.mark.skipif(not _tracer_available(), reason="docker / VC3D builds not available")
xfail_S = pytest.mark.xfail(FAMILY == "S", reason="measured: bare task P fails this synthetic test", strict=False)


@needs_tracer
@pytest.mark.parametrize("cfg", PRESETS)
@pytest.mark.parametrize("scene", ["B", "B_switch"])
def test_two_sheets_8vox_never_bridged(scene, cfg):
    from synth_suite import run_one
    r = run_one(scene, cfg, rep=90)
    assert "error" not in r, r.get("error")
    assert r["n_vertices_by_sheet"][1] == 0, r["n_vertices_by_sheet"]
    assert r["n_bridge_edges"] == 0


@needs_tracer
@xfail_S
@pytest.mark.parametrize("cfg", PRESETS)
def test_growth_continues_past_forced_rejection(cfg):
    from synth_suite import run_one
    r = run_one("C", cfg, rep=90)
    assert "error" not in r, r.get("error")
    assert r["n_rej_dist_in_hole"] >= 1
    assert r["far_core_frac"] >= 0.90


@needs_tracer
@xfail_S
@pytest.mark.parametrize("cfg", PRESETS)
def test_single_clean_sheet_full_area(cfg):
    from synth_suite import run_one
    r = run_one("A", cfg, rep=90)
    assert "error" not in r, r.get("error")
    c = r["coverage_seed_sheet"]
    assert c["covered_core_frac"] >= 0.95
    assert c["traced_outside_truth_frac"] <= 0.01
    assert r["max_abs_r_resid"] <= 2.5


# ---- pure-python glue (always runs)
def test_quad_top_vertex_and_v2_cutoff():
    from surfmetrics import crossing_pairs, quad_top_vertex
    from hercules.geometry.truncation import v2_truncation
    g = np.arange(36).reshape(6, 6) % 7 + 1
    rep = {"census": [{"transverse_contacts": [{"quad1": [0, 0], "quad2": [3, 3]}]},
                      {"transverse_contacts": [{"quad1": [3, 3], "quad2": [0, 0]},
                                               {"quad1": [1, 2], "quad2": [4, 0]}]}]}
    pairs = crossing_pairs(rep)
    assert len(pairs) == 2  # duplicate over triangulations counted once
    contacts = []
    for q1, q2 in pairs:
        a, b = quad_top_vertex(g, q1), quad_top_vertex(g, q2)
        assert g[a] == max(g[q1[0]:q1[0] + 2, q1[1]:q1[1] + 2].ravel())
        contacts.append((np.ravel_multi_index(a, g.shape), np.ravel_multi_index(b, g.shape)))
    exp = min(max(g[v:v + 2, u:u + 2].max(), g[v2:v2 + 2, u2:u2 + 2].max()) for (v, u), (v2, u2) in pairs)
    assert v2_truncation(g, contacts).cutoff == exp


def test_densified_distance_bound():
    from surfmetrics import distance_to_surface
    u, v = np.meshgrid(np.arange(10) * 20.0, np.arange(10) * 20.0)
    plane = np.stack([u, v, np.full_like(u, 50.0)], -1)
    q = np.array([[33.3, 71.1, 50.0], [100.0, 100.0, 53.0], [10.0, 10.0, 60.0]])
    d = distance_to_surface(q, plane, 20.0)
    exact = np.array([0.0, 3.0, 10.0])
    assert np.all(d >= exact - 1e-9) and np.all(d - exact <= 0.71)
