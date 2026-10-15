# Provenance: Project HERCULES | owner the owner | [id removed]
"""Real organizer-mesh checks (task contam items 4 and 5).

Part 1 validates the committed results (logs/sib/contam/*.json) against the
archive-known re-traces; it needs no network or mesh files. Part 2 re-runs a
planted-fault certificate on the real meshes when they are present locally
(fetched by tools/sib/contam/fetch_meshes.py), else it is skipped.

Run: PYTHONPATH=src pytest -q tests/sib_contam_test_real.py
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "sib" / "contam"))
import contam3d as C  # noqa: E402

LOGS = REPO / "logs" / "sib" / "contam"
MESHES = Path("/work/sib_contam/meshes/PHerc0139")


def _units():
    p = LOGS / "units_0139.json"
    if not p.exists():
        pytest.skip("units_0139.json not produced yet")
    return json.loads(p.read_text())


def _pair(u, x, y):
    for p in u["pairs_tested"]:
        a, b = p["a"], p["b"]
        if (f"-{x}_" in a and f"-{y}_" in b) or (f"-{y}_" in a and f"-{x}_" in b):
            return p
    return None


def _frac(p, of):
    return p["a_in_b"]["frac_of_a"] if f"-{of}_" in p["a"] else p["b_in_a"]["frac_of_a"]


def test_manifest_hashes_every_mesh_and_voxel_size_from_metadata():
    man = json.loads((LOGS / "mesh_manifest_0139.json").read_text())
    assert man["volume_metadata"]["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"] == 0.009362
    ok = [s for s, r in man["segments"].items() if r["status"] == "ok"]
    assert len(ok) == 38
    for s in ok:
        assert set(man["segments"][s]["files"]) == {"x.tif", "y.tif", "z.tif", "meta.json"}
        assert all(len(f["sha256"]) == 64 for f in man["segments"][s]["files"].values())


def test_w046_retraces_w045_83_percent():
    p = _pair(_units(), "w045", "w046")
    assert p and p["same"]
    assert _frac(p, "w046") == pytest.approx(0.83, abs=0.03)
    assert _frac(p, "w045") == pytest.approx(0.83, abs=0.03)


def test_w025_retraces_a_strip_of_w024():
    p = _pair(_units(), "w024", "w025")
    assert p and p["same"]
    assert 0.0 < _frac(p, "w024") < 0.6  # a strip, not the whole sheet


def test_w048_touches_w047():
    p = _pair(_units(), "w047", "w048")
    assert p and p["same"]
    assert _frac(p, "w047") < 0.10


def test_w052_shares_a_strip_with_w053():
    p = _pair(_units(), "w052", "w053")
    assert p and p["same"]


def test_units_partition_is_consistent_with_pairs():
    u = _units()
    unit_of = {m: x["unit"] for x in u["units"] for m in x["members"]}
    assert sorted(unit_of) == sorted(u["segments"])
    for p in u["pairs_tested"]:
        if p["same"]:
            assert unit_of[p["a"]] == unit_of[p["b"]]
    # adjacent windings are tested and found NOT same somewhere
    assert any(not p["same"] and p["a_in_b"]["counts"][0] == 0 for p in u["pairs_tested"])


def test_planted_faults_all_caught():
    p = LOGS / "planted_faults_0139.json"
    if not p.exists():
        pytest.skip("planted_faults_0139.json not produced yet")
    r = json.loads(p.read_text())
    assert r["all_caught"]
    fails = [x for x in r["results"] if not x["expect_pass"]]
    assert len(fails) >= 8 and all(not x["passed"] and x["raw_min"] < 2.0 for x in fails)
    assert any(x["expect_pass"] and x["passed"] for x in r["results"])


@pytest.mark.skipif(not MESHES.exists(), reason="real meshes not fetched")
def test_live_planted_fault_w045_training_catches_w046_window(tmp_path):
    names = {p.name for p in MESHES.iterdir() if p.is_dir()}
    t = next(n for n in names if "-w045_" in n)
    e = next(n for n in names if "-w046_" in n)
    man = json.loads((LOGS / "mesh_manifest_0139.json").read_text())
    reg = {"checkpoint": "planted", "frame": {"scroll": "PHerc0139", "volume_id": man["canvas_volume"],
                                              "voxel_size_mm": 0.009362},
           "patches": [dict(id="w045", segment=t, mesh_dir=str(MESHES / t), rect_px=None, label_source="planted",
                            mesh_sha256={k: v["sha256"] for k, v in man["segments"][t]["files"].items()})]}
    (tmp_path / "r.json").write_text(json.dumps(reg))
    region = {"segment": e, "mesh_dir": str(MESHES / e), "rect_px": [2940, 1930, 5076, 4066],
              "volume_id": man["canvas_volume"],
              "mesh_sha256": {k: v["sha256"] for k, v in man["segments"][e]["files"].items()}}
    c = C.fl09_certificate(tmp_path / "r.json", region, workers=2, base_dir="/")
    assert not c["passed"]
    assert c["primary_halo_inplane"]["raw_min"] < 1.0
    assert c["primary_halo_inplane"]["offending"]
