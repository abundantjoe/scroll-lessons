# Provenance: Project HERCULES | owner the owner | [id removed]
"""Surface metrics for traced tifxyz surfaces (numbers only; no image is written or read).

Definitions (fixed before any dev result was computed):
* crossings: distinct unordered quad pairs reported TRANSVERSE by the official vc_tifxyz_selfcross
  (villa 41701aa, default --exclude 1 --maxedge 60) under either quad triangulation.
  crossings_per_cm2 = crossings / raw area (cm^2).
* v2 truncation: quad generation = max of its 4 corner generations (generations.tif);
  cutoff = min over crossings of max(g(quad1), g(quad2)); keep vertices with g < cutoff
  (all vertices if there is no crossing). Implemented by hercules.geometry.truncation on vertex
  pairs (the corner of each quad with the largest generation), which gives the same cutoff.
* area: two triangles per fully valid quad, voxel size from the volume's metadata.json.
* edges: % of valid grid edges with length within +-10 % of the nominal step (1/scale).
* distance to team surface: Euclidean distance from each kept vertex to the team mesh densified
  to <= 1 vox spacing (bilinear); overestimates the exact point-to-surface distance by at most
  0.71 vox near the surface. frac_within_3 = fraction of kept vertices with distance <= 3 vox.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path("/home/user/dominion")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hercules.geometry.tifxyz import (TifxyzMesh, area_cm2, edge_fraction_within, edge_lengths,  # noqa: E402
                                      read_tifxyz, valid_mask, write_tifxyz)
from hercules.geometry.truncation import truncate_mesh_points  # noqa: E402


def selfcross(seg: Path, out_json: Path, runs_jsonl: Path, label: str) -> dict:
    from synth import BIN_VANILLA, run_logged, vc_cmd
    cmd = vc_cmd(BIN_VANILLA, "vc_tifxyz_selfcross", ["--surface", str(seg), "-o", str(out_json), "--threads", "2"],
                 cpus=2, threads=2)
    rc = run_logged(label, cmd, out_json.with_suffix(".log"), runs_jsonl)
    if rc != 0:
        raise RuntimeError(f"selfcross failed rc={rc} for {seg}")
    return json.loads(out_json.read_text())


def crossing_pairs(report: dict) -> set[tuple[tuple[int, int], tuple[int, int]]]:
    pairs = set()
    for d in report["census"]:
        for c in d["transverse_contacts"]:
            a, b = tuple(c["quad1"]), tuple(c["quad2"])
            pairs.add((min(a, b), max(a, b)))
    return pairs


def quad_top_vertex(g: np.ndarray, quad: tuple[int, int]) -> tuple[int, int]:
    """(row, col) of the quad corner with the largest generation."""
    v, u = quad
    cs = [(v, u), (v, u + 1), (v + 1, u), (v + 1, u + 1)]
    return max(cs, key=lambda rc: g[rc])


def edge_stats(points: np.ndarray, step: float) -> dict:
    lu, lv = edge_lengths(points)
    L = np.concatenate([lu[np.isfinite(lu)], lv[np.isfinite(lv)]])
    if L.size == 0:
        return {"n_edges": 0}
    q = np.percentile(L, [1, 5, 25, 50, 75, 95, 99])
    return {"n_edges": int(L.size), "frac_within_10pct": float(np.mean(np.abs(L - step) <= 0.1 * step)),
            "pct": dict(zip(["p1", "p5", "p25", "p50", "p75", "p95", "p99"], [float(x) for x in q]))}


def densify_grid(points: np.ndarray, k: int) -> np.ndarray:
    """Bilinear densification of every fully valid quad into k x k sub-samples (points only)."""
    p = np.asarray(points, dtype=np.float64)
    v = valid_mask(p)
    qv = v[:-1, :-1] & v[:-1, 1:] & v[1:, :-1] & v[1:, 1:]
    js, is_ = np.nonzero(qv)
    t = (np.arange(k) + 0.5) / k
    A, Bm = np.meshgrid(t, t, indexing="ij")
    a, b = A.ravel()[None, :, None], Bm.ravel()[None, :, None]
    p00, p01, p10, p11 = p[js, is_][:, None], p[js, is_ + 1][:, None], p[js + 1, is_][:, None], p[js + 1, is_ + 1][:, None]
    out = (1 - a) * (1 - b) * p00 + (1 - a) * b * p01 + a * (1 - b) * p10 + a * b * p11
    return np.concatenate([out.reshape(-1, 3), p[v]], axis=0)


def distance_to_surface(query: np.ndarray, ref_points: np.ndarray, ref_step: float) -> np.ndarray:
    from scipy.spatial import cKDTree
    k = max(1, int(math.ceil(ref_step / 1.0)))
    cloud = densify_grid(ref_points, k)
    tree = cKDTree(cloud)
    d, _ = tree.query(query, k=1, workers=4)
    return d


def analyse(seg: Path, work: Path, runs_jsonl: Path, voxel_um: float, team: Path | None = None,
            label: str = "") -> dict:
    work.mkdir(parents=True, exist_ok=True)
    m = read_tifxyz(seg)
    import tifffile
    g = tifffile.imread(seg / "generations.tif").astype(np.int64)
    step = 1.0 / float(m.scale[0])
    raw_area = area_cm2(m.points, voxel_um)
    rep = selfcross(seg, work / "selfcross_raw.json", runs_jsonl, f"selfcross_raw_{label}")
    pairs = crossing_pairs(rep)
    contacts = []
    for q1, q2 in pairs:
        a, b = quad_top_vertex(g, q1), quad_top_vertex(g, q2)
        contacts.append((np.ravel_multi_index(a, g.shape), np.ravel_multi_index(b, g.shape)))
    tp, tr = truncate_mesh_points(m.points, g, contacts)
    out = {
        "segment": str(seg), "grid_shape": list(g.shape), "step_vox": step, "voxel_um": voxel_um,
        "max_generation": int(g[valid_mask(m.points)].max()) if valid_mask(m.points).any() else 0,
        "raw": {"area_cm2": raw_area, "n_valid": int(valid_mask(m.points).sum()), "crossings": len(pairs),
                "crossings_per_cm2": (len(pairs) / raw_area) if raw_area > 0 else None,
                "edges": edge_stats(m.points, step)},
        "v2": {"cutoff_generation": tr.cutoff, "n_removed": tr.n_removed,
               "area_cm2": area_cm2(tp, voxel_um), "n_valid": int(valid_mask(tp).sum()),
               "edges": edge_stats(tp, step)},
    }
    # verify truncation leaves no crossing
    tdir = work / "v2_surface"
    write_tifxyz(tdir, TifxyzMesh(points=tp, scale=m.scale, uuid=(m.uuid or "seg") + "_v2", meta={}), overwrite=True, voxel_size_um=voxel_um)
    rep2 = selfcross(tdir, work / "selfcross_v2.json", runs_jsonl, f"selfcross_v2_{label}")
    out["v2"]["crossings_after"] = len(crossing_pairs(rep2))
    if team is not None:
        tm = read_tifxyz(team)
        q = tp[valid_mask(tp)].astype(np.float64)
        if q.size:
            d = distance_to_surface(q, tm.points, 1.0 / float(tm.scale[0]))
            out["team"] = {"team_segment": str(team), "n_query": int(q.shape[0]),
                           "frac_within_3": float(np.mean(d <= 3.0)), "median_dist": float(np.median(d)),
                           "p90_dist": float(np.percentile(d, 90))}
    return out
