# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for tools/sib/devloop-r1/lc_pool.py on synthetic planar meshes (no scroll data)."""
import importlib.util
import os

import numpy as np

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "sib", "devloop-r1", "lc_pool.py")
_s = importlib.util.spec_from_file_location("lc_pool", _p)
P = importlib.util.module_from_spec(_s)
_s.loader.exec_module(P)
from hercules.geometry.tifxyz import TifxyzMesh  # noqa: E402


def plane(z, H=200, W=200, s=0.05):
    """Grid vertex (v, u) at (x, y) = (u / s, v / s), constant z; canvas pixel P maps to grid (P + 0.5) s, i.e.
    x = P + 0.5 in voxels."""
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    pts = np.stack([u / s, v / s, np.full_like(u, z)], -1).astype(np.float32)
    return TifxyzMesh(points=pts, scale=(s, s))


MESHES = {"DEV": plane(100.0), "NEAR": plane(110.0), "FAR": plane(130.0), "HOLE": plane(200.0)}
MESHES["HOLE"].points[:, :] = -1  # entirely invalid


def row(tid, seg, y0=512, x0=512, centre=None, kept=True):
    c = centre if centre is not None else [x0 + 64.0, y0 + 64.0, float(MESHES[seg].points[0, 0, 2])]
    return dict(tile_id=tid, segment=seg, canvas9_y0=y0, canvas9_x0=x0, size=128, shard="s.npz" if kept else None,
                kept=kept, xyz_centre=c)


def run(rows, excluded=(), dev_segments=("DEV",)):
    return P.build(rows, [("DEV", 0, 0, 2136, 2136)], set(dev_segments), set(excluded), MESHES.__getitem__)


def test_canvas_mapping_matches_renderer_convention():
    c = P.centre_point(MESHES["FAR"], 512, 512)
    assert np.allclose(c, [512 + 63.5 + 0.5, 512 + 63.5 + 0.5, 130.0], atol=1e-3)


def test_clearance_fail_closed():
    allow, rep = run([row("near", "NEAR"), row("far", "FAR")])
    assert allow == ["far"]
    assert rep["rejected"] == {"dev_clearance": 1}
    assert abs(rep["clearance_vox_quantiles"][0.0] - 10.0) < 1e-3


def test_threshold_is_16_vox():
    MESHES["EDGE15"], MESHES["EDGE17"] = plane(115.0), plane(117.0)
    allow, _ = run([row("a", "EDGE15"), row("b", "EDGE17")])
    assert allow == ["b"]


def test_centre_mismatch_and_invalid_and_segment_rules():
    rows = [row("bad_centre", "FAR", centre=[0.0, 0.0, 0.0]), row("hole", "HOLE", centre=[576.0, 576.0, -1.0]),
            row("dev", "DEV"), row("excl", "FAR"), row("unkept", "FAR", kept=False)]
    rows[3]["segment"] = "EXCL"
    MESHES["EXCL"] = plane(130.0)
    allow, rep = run(rows, excluded={"EXCL"})
    assert allow == []
    assert rep["rejected"] == {"centre_mismatch": 2, "dev_segment": 1, "excluded_segment": 1, "not_kept": 1}
