# Provenance: Project HERCULES | owner the owner | [id removed]
"""Re-check recorded clearances with the corrected (CORR-RETRACE-RULE) point-to-surface
distance. Mesh geometry only: no CT, no render, no ink map, no seal, no image.

Part J (PHerc0841, D3-FEAS / DECL-D3-A2): every PRIMARY-grid tile position (128 px,
stride 64) on the 3 organizer segments with >= 90 % mesh-valid pixels and no pixel inside
its own segment's J window. For every mesh-valid pixel of such a tile: point-to-point
distance to the nearest J canvas point (the recorded method) and, where that is below
146 vox, the exact point-to-surface distance to the triangulated J canvas-point surface
(1-vox spacing). A tile's clearance is the minimum over its pixels. The recorded 306
PRIMARY text tiles and the 288 pool tiles are subsets of the tiles checked here (their
text status needs the reference ink map, which this check does not open), so any tile
whose surface clearance falls below 128 / 144 vox while its point clearance does not is
listed by origin for cross-reference with fa_tiles.json.

Part B (PHerc0139, RCBANK-1 and the SEAL-J-D1 blanks): each clean bank segment (w024,
w047, w053) and each blank window vs every base-training trace, densified 5 x 5, with the
corrected same-papyrus rule (vertex OR surface form) and the area within 1 / 2 / 3 vox.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from hercules.geometry.contamination import same_papyrus  # noqa: E402
from hercules.geometry.tifxyz import densify, read_tifxyz, sample_grid, valid_mask  # noqa: E402
from hercules.pipeline.window import J_WINDOW_PX, J_WINDOWS_0841, SEGMENTS_0841  # noqa: E402
from hercules.tribunal.preread import surface_distances  # noqa: E402

W = 3
TILE, STRIDE, MINVALID = 128, 64, 0.9
T_EXCL, T_POOL = 128.0, 144.0
PRE = 146.0  # point distances below this get the exact surface distance (spacing <= 1 vox)
BASE_0139 = ["w028", "w029", "w030", "w035", "w039", "w040", "w041", "w043", "w044", "w045", "w046"]  # w028: devloop R3 (ink_9um label list)
BANK_0139 = ["w024", "w047", "w053"]
BLANKS = {"blank_w053_y256_x1536": ("w053", 256, 1536), "blank_w053_y256_x7168": ("w053", 256, 7168)}


def mesh_path(root: Path, scroll: str, sid: str, vol: str) -> Path:
    ts = sid.split("-")[0]
    return root / scroll / "segments" / sid / "mesh" / f"{ts}-on-{vol}.tifxyz"


def canvas_pts(points, r0, r1, c0, c1):
    rows = (np.arange(r0, r1, dtype=np.float64) + 0.5) / 20.0
    cols = (np.arange(c0, c1, dtype=np.float64) + 0.5) / 20.0
    R, C = np.meshgrid(rows, cols, indexing="ij")
    g = sample_grid(points, R, C)
    return g, valid_mask(g)


def part_j(root: Path) -> dict:
    vol = "20250821151531-9.366um"
    meshes = {k: read_tifxyz(mesh_path(root, "PHerc0841", sid, vol)).points.astype(np.float64)
              for k, sid in SEGMENTS_0841.items()}
    jgrids, jpts = {}, []
    for j, (seg, y0, x0) in sorted(J_WINDOWS_0841.items()):
        g, v = canvas_pts(meshes[seg], y0, y0 + J_WINDOW_PX, x0, x0 + J_WINDOW_PX)
        jgrids[j] = g
        jpts.append(g[v])
    jpts = np.concatenate(jpts)
    tree = cKDTree(jpts)
    out = {"J_points": int(len(jpts)), "segments": {}}
    for seg, pts in meshes.items():
        H, Wd = pts.shape[:2]
        Hc, Wc = H * 20, Wd * 20
        own = [(y0, x0) for s, y0, x0 in J_WINDOWS_0841.values() if s == seg]
        dpt = np.full((Hc, Wc), np.inf)
        dsf = np.full((Hc, Wc), np.inf)
        valid = np.zeros((Hc, Wc), bool)
        injw = np.zeros((Hc, Wc), bool)
        for y0, x0 in own:
            injw[y0:y0 + J_WINDOW_PX, x0:x0 + J_WINDOW_PX] = True
        for r0 in range(0, Hc, 256):
            r1 = min(Hc, r0 + 256)
            g, v = canvas_pts(pts, r0, r1, 0, Wc)
            valid[r0:r1] = v
            q = g[v]
            d, _ = tree.query(q, k=1, distance_upper_bound=PRE, workers=W)
            blk = np.full(v.shape, np.inf)
            blk[v] = d
            dpt[r0:r1] = blk
        # exact surface distance where 127 <= point distance < PRE (surface <= point, and every
        # pixel with point distance < 128 is already excluded, so its surface value only needs
        # to stay below 128: it is set to the point distance)
        low = np.isfinite(dpt) & valid & (dpt < 127.0)
        dsf[low] = dpt[low]
        near = np.isfinite(dpt) & valid & ~injw & (dpt >= 127.0)
        rr, cc = np.nonzero(near)
        if rr.size:
            q = sample_grid(pts, (rr + 0.5) / 20.0, (cc + 0.5) / 20.0)
            best = np.full(rr.size, np.inf)
            for j, g in jgrids.items():
                best = np.minimum(best, surface_distances(q, g, max_dist=PRE + 1.0, workers=W))
            dsf[rr, cc] = best
        # tiles
        tiles = []
        for ty in range(0, Hc - TILE + 1, STRIDE):
            for tx in range(0, Wc - TILE + 1, STRIDE):
                v = valid[ty:ty + TILE, tx:tx + TILE]
                if v.mean() < MINVALID or injw[ty:ty + TILE, tx:tx + TILE].any():
                    continue
                mp = float(dpt[ty:ty + TILE, tx:tx + TILE][v].min())
                ms = float(dsf[ty:ty + TILE, tx:tx + TILE][v].min())
                tiles.append((ty, tx, mp, ms))
        keep = valid & ~injw & (dpt >= T_EXCL)
        flag128 = [t for t in tiles if t[2] >= T_EXCL and t[3] < T_EXCL]
        flag144 = [t for t in tiles if t[2] >= T_POOL and t[3] < T_POOL]
        elig = [t for t in tiles if t[2] >= T_EXCL]
        out["segments"][seg] = {
            "canvas": [Hc, Wc], "mesh_valid_px": int(valid.sum()),
            "tiles_ge90valid_outside_own_J": len(tiles),
            "tiles_point_clearance_ge128": len(elig),
            "tiles_point_ge144": sum(t[2] >= T_POOL for t in tiles),
            "tiles_surface_ge144": sum(t[3] >= T_POOL for t in tiles),
            "min_point_dist_retained_px": float(dpt[keep].min()) if keep.any() else None,
            "min_surface_dist_retained_px": float(dsf[keep].min()) if keep.any() else None,
            "retained_px_point": int(keep.sum()),
            "retained_px_surface_lt128": int((keep & (dsf < T_EXCL)).sum()),
            "max_point_minus_surface_vox": float(np.max((dpt - dsf)[np.isfinite(dsf) & np.isfinite(dpt)]))
            if np.isfinite(dsf).any() else None,
            "flag_eligible_but_surface_lt128": [{"y0": t[0], "x0": t[1], "point": t[2], "surface": t[3]} for t in flag128],
            "flag_point_ge144_but_surface_lt144": [{"y0": t[0], "x0": t[1], "point": t[2], "surface": t[3]} for t in flag144],
        }
    return out


def part_b(root: Path, fetched: dict) -> dict:
    vol = "20250728140407-9.362um"
    ids = {k.split("/")[1]: v["mesh"] for k, v in fetched["segments"].items()
           if k.startswith("PHerc0139/") and "mesh" in v}

    def find(tag):
        return sorted(sid for sid in ids if f"-{tag}_" in sid)

    base = {sid: read_tifxyz(ids[sid]).points.astype(np.float64) for t in BASE_0139 for sid in find(t)}
    missing = [t for t in BASE_0139 if not find(t)]
    area_per_dense = (20.0 / 5) ** 2  # vox^2 per densified vertex
    vox_cm2 = (9.362e-4) ** 2
    res = {"base_training_traces": sorted(base), "missing_9um_mesh": missing, "bank": {}, "blanks": {}}
    for t in BANK_0139 + ["blanks"]:
        items = []
        if t == "blanks":
            for name, (tag, y0, x0) in BLANKS.items():
                p = read_tifxyz(ids[find(tag)[0]]).points.astype(np.float64)
                g, v = canvas_pts(p, y0, y0 + 2136, x0, x0 + 2136)
                g[~v] = -1.0
                items.append((name, g[::4, ::4], 1.0 * 16))  # 4-vox sampling of the canvas points
        else:
            sid = find(t)[0]
            p = read_tifxyz(ids[sid]).points.astype(np.float64)
            items.append((sid, densify(p, 5), area_per_dense))
        for name, A, apd in items:
            per = {}
            for bid, B in base.items():
                Bd = densify(B, 5)
                lit = same_papyrus(A, Bd, workers=W)
                d = surface_distances(A, Bd, max_dist=3.0, workers=W)
                c = [int(np.sum(d < 1)), int(np.sum((d >= 1) & (d < 2))), int(np.sum((d >= 2) & (d < 3)))]
                sf_same = (c[0] + c[1]) >= 1000 and c[0] >= 2.0 * c[2]
                dv = cKDTree(Bd[valid_mask(Bd)]).query(A[valid_mask(A)] if A.ndim == 3 else A, k=1, workers=W)[0]
                per[bid] = {"vertex_counts": list(lit.counts), "vertex_same": bool(lit.same),
                            "surface_counts": c, "surface_same": bool(sf_same),
                            "same_corrected": bool(lit.same or sf_same),
                            "area_lt1_cm2": float(c[0] * apd * vox_cm2),
                            "area_lt2_cm2": float((c[0] + c[1]) * apd * vox_cm2),
                            "min_surface_dist_vox": float(np.min(d)) if np.isfinite(d).any() else None,
                            "min_vertex_dist_vox": float(dv.min())}
            key = "blanks" if t == "blanks" else "bank"
            res[key][name] = {"vs_base": per,
                              "same_as": sorted(b for b, v in per.items() if v["same_corrected"]),
                              "min_vertex_dist_to_any_base_vox": min(v["min_vertex_dist_vox"] for v in per.values()),
                              "area_lt2_any_base_cm2_sum": sum(v["area_lt2_cm2"] for v in per.values())}
    return res


def main_part_b_only():
    """--part-b-only MESH_ROOT FETCHED OUT: recompute part B (e.g. after a base-list correction) and keep
    the previous part B under part_b_superseded."""
    root, fetched, out_path = Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()), Path(sys.argv[4])
    res = json.loads(out_path.read_text())
    res.setdefault("part_b_superseded", []).append({"reason": "base-training list lacked w028", "part_b": res["part_b"]})
    res["part_b"] = part_b(root, fetched)
    out_path.write_text(json.dumps(res, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8")
    print("part B recomputed")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--part-b-only":
        return main_part_b_only()
    root = Path(sys.argv[1])
    fetched = json.loads(Path(sys.argv[2]).read_text())
    out_path = Path(sys.argv[3])
    t0 = time.time()
    res = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "rule": "CORR-RETRACE-RULE point-to-surface distance", "inputs": "meshes_fetched.json (sha256 per file)",
           "not_used": "no CT, render, ink map, seal or image", "part_j": part_j(root)}
    res["part_b"] = part_b(root, fetched)
    res["seconds"] = round(time.time() - t0, 1)
    out_path.write_text(json.dumps(res, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8")
    print("done", res["seconds"])


if __name__ == "__main__":
    main()
