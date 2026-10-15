# Provenance: Project HERCULES | owner the owner | [id removed]
"""Pick the dry-run window on PHerc0139 w035 (9.362 um mesh) by a coded, deterministic rule.

Two exclusion groups, 3-D, voxel units of volume 20250728140407; every mesh densified x5:
  G144 (>= 150 vox = the task's 144-vox 3-D clearance + 6 vox discretisation margin; run v6 at 144 chose a
        window at 145.0 vox, inside that margin): the sealed / session windows on 0139, i.e. SEAL-J-D1 blanks
        blank_w053_y256_x1536 and blank_w053_y256_x7168 and the D1 canary canary_w044_y2816_x2816
        (organizer 9.362 um canvas = mesh grid x 20; 2136 px squares + one grid cell border), and the whole
        title mesh (title region).
  G40  (>= 40 vox = 2 grid cells, i.e. not the same papyrus traced twice): the whole w024, w047, w053 and
        w044 meshes (never used).
PROBE window w035_y1792_x768 (read by PROBE-1/2 readers on reference maps; NOT sealed): it lies on w035 itself
and covers grid rows 88-199 of 291, so every 2 x 2 cm w035 window overlaps it (run pick_window_v5: 0 of 1108
candidates at >= 40 vox). It is therefore not a hard exclusion; the rule minimises the overlap instead
(fraction of the window's grid cells inside the probe square on the 9.362 um organizer canvas = grid x 20,
the canvas the D1 records use for organizer windows) and reports it.
Why not 144 vox from the whole meshes: w044 and w024 are adjacent windings; over all 1108 fully valid
candidates the best whole-mesh clearance is 92.6 vox (runs pick_window_v2..v4, all 0 candidates).
Candidates: 108 x 108-vertex sub-grids (107 cells = 2140 canvas px >= 2 cm) of the w035 grid, all vertices
valid, on a 4-vertex lattice. Method: one KD-tree distance per densified w035 vertex and group; a candidate's
clearance is the minimum over its block. Among candidates passing both groups choose the smallest
probe overlap, then the largest G144 clearance; ties by (r0, c0). Output: logs/sib/factory/window_pick.json (numbers only)."""
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
from hercules.geometry.tifxyz import densify, read_tifxyz, valid_mask  # noqa: E402

R = "/work/factory/s3/PHerc0139/segments/"
VOL = "20250728140407"
W035 = R + f"20260317000000-w035_2026031718/mesh/20260317000000-on-{VOL}-9.362um.tifxyz"
SEG = {"w024": "20260215000000-w024_2026021572", "w047": "20260206000001-w047_2026020613",
       "w053": "20260220000000-w053_2026022021", "w044": "20260115000000-w044_2026011522",
       "title": "20260422000000-title_2026042222_zmid_flatboi"}
SEALED = {"blank_w053_y256_x1536": ("w053", 256, 1536), "blank_w053_y256_x7168": ("w053", 256, 7168),
          "canary_w044_y2816_x2816": ("w044", 2816, 2816)}
PROBE = ("w035", 1792, 768)
WIN_PX = 2136
N, LATTICE, K = 108, 4, 5
G144, G40 = 150.0, 40.0  # 144 + 6: two x the densified half-diagonal (20/5 x sqrt2/2 = 2.83 vox) as discretisation margin
VOXEL_UM = round(float(json.load(open(f"/work/factory/s3/PHerc0139/volumes/{VOL}-9.362um-1.2m-113keV-masked.zarr/metadata.json"))
                       ["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000.0, 6)
OUT = os.path.join(REPO, "logs", "sib", "factory", "window_pick.json")


def mesh(short):
    seg = SEG[short] if short in SEG else "20260317000000-w035_2026031718"
    ts = seg.split("-")[0]
    return read_tifxyz(f"{R}{seg}/mesh/{ts}-on-{VOL}-9.362um.tifxyz").points


def pts(P):
    D = densify(P, K)
    return D[valid_mask(D)].reshape(-1, 3).astype(np.float64)


def window_pts(P, y0, x0, size_px, f=1.0):
    y0, x0, s = y0 * f / 20, x0 * f / 20, size_px * f / 20
    r0, r1 = max(int(np.floor(y0 - 1)), 0), int(np.ceil(y0 + s + 1)) + 1
    c0, c1 = max(int(np.floor(x0 - 1)), 0), int(np.ceil(x0 + s + 1)) + 1
    return pts(P[r0:r1, c0:c1]), [r0, r1], [c0, c1]


def main():
    P = mesh("w035")
    V = valid_mask(P)
    H, W = V.shape
    info, g144, g40 = {}, [], []
    for name, (short, y0, x0) in SEALED.items():
        q, rr, cc = window_pts(mesh(short), y0, x0, WIN_PX)
        g144.append(q)
        info[name] = dict(group="G144", grid_rows=rr, grid_cols=cc, n_points=len(q))
    q = pts(mesh("title"))
    g144.append(q)
    info["title_mesh"] = dict(group="G144", n_points=len(q))
    for short in ("w024", "w047", "w053", "w044"):
        q = pts(mesh(short))
        g40.append(q)
        info[f"{short}_mesh"] = dict(group="G40", n_points=len(q))
    py0, px0, ps = PROBE[1] / 20, PROBE[2] / 20, WIN_PX / 20
    info["probe_9362_canvas"] = dict(group="overlap minimised (not sealed)", grid_rows=[py0, py0 + ps],
                                     grid_cols=[px0, px0 + ps])
    D = densify(P, K)
    dv = valid_mask(D)
    Q = D[dv].reshape(-1, 3).astype(np.float64)
    fields = []
    for g in (g144, g40):
        f = np.full(dv.shape, -1.0)
        f[dv] = cKDTree(np.concatenate(g)).query(Q, k=1, workers=3)[0]
        fields.append(f)
    k = (D.shape[0] - 1) // (H - 1)
    best, n_cand, n_ok, c144, c40 = None, 0, 0, [], []
    for r0 in range(0, H - N + 1, LATTICE):
        for c0 in range(0, W - N + 1, LATTICE):
            if not V[r0:r0 + N, c0:c0 + N].all():
                continue
            n_cand += 1
            blk = (slice(k * r0, k * (r0 + N - 1) + 1), slice(k * c0, k * (c0 + N - 1) + 1))
            d1, d2 = float(fields[0][blk].min()), float(fields[1][blk].min())
            c144.append(d1)
            c40.append(d2)
            ov = (max(0.0, min(r0 + N - 1, py0 + ps) - max(r0, py0)) * max(0.0, min(c0 + N - 1, px0 + ps) - max(c0, px0))
                  / float((N - 1) ** 2))
            if d1 >= G144 and d2 >= G40:
                n_ok += 1
                key = (round(ov, 6), -d1, r0, c0)
                if best is None or key < best[0]:
                    best = (key, d1, r0, c0, ov)
    qd = lambda a: {str(x): round(float(np.quantile(a, x)), 2) for x in (0.0, 0.5, 0.9, 1.0)} if a else {}
    res = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
               mesh=W035.replace("/work/factory/s3/", "s3://vesuvius-challenge-open-data/"), grid_shape=[H, W],
               voxel_size_um=VOXEL_UM,
               rule=dict(n_vertices=N, lattice=LATTICE, densify=K, g144_min_vox=G144, g40_min_vox=G40),
               exclusions=info, n_fully_valid_candidates=n_cand, n_passing_candidates=n_ok,
               g144_clearance_quantiles_vox=qd(c144), g40_clearance_quantiles_vox=qd(c40))
    if best:
        _, d1, r0, c0, ov = best
        q = pts(P[r0:r0 + N, c0:c0 + N])
        per = {}
        for name, (short, y0, x0) in SEALED.items():
            per[name] = window_pts(mesh(short), y0, x0, WIN_PX)[0]
        per["title_mesh"] = pts(mesh("title"))
        for short in ("w024", "w047", "w053", "w044"):
            per[f"{short}_mesh"] = pts(mesh(short))
        per["probe_9362_canvas (report only)"] = window_pts(P, PROBE[1], PROBE[2], WIN_PX)[0]
        res["chosen"] = dict(grid_rows=[r0, r0 + N], grid_cols=[c0, c0 + N], canvas_y0=r0 * 20, canvas_x0=c0 * 20,
                             probe_window_overlap_fraction=round(ov, 4),
                             g144_clearance_vox=round(d1, 2), g144_clearance_mm=round(d1 * VOXEL_UM / 1000.0, 3),
                             clearance_per_exclusion_vox={n: round(float(cKDTree(e).query(q, k=1, workers=3)[0].min()), 2)
                                                          for n, e in per.items()})
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
