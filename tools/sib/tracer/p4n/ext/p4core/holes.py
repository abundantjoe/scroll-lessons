# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-24: mesh holes and mesh edges of 20260701183124-w010-027 (2.4 um
tifxyz), per strip-a tile r0-r8 x c0-c19 (tile frame as mesh_audit.py).
Numbers only: CT is streamed as byte ranges into 1-D profiles / single
voxels and discarded.

Fixed before any number of this entry exists (this file's first commit):
 (a) invalid vertex fraction of the tile grid (x == -1 or non-finite);
     interior holes = 8-connected invalid components of the WHOLE grid that
     do not touch the grid border; each hole's area = n_cells x (20 vox x
     2.4 um)^2 = n x 0.002304 mm^2, listed for every hole meeting the tile.
 (b) 400 random valid vertices per tile (rng [20260928, r, c]); the L0 voxel
     nearest each vertex is read (1-byte range). Fraction whose value is 0,
     fraction whose zarr chunk is absent (HTTP 403/404), and their union.
     Vertices stand in for canvas pixels (pixels interpolate the vertices).
     Volume: the 2.4 um volume 20260411134726 (the mesh's own frame).
 (c) official flattening = the tifxyz grid (FLAT-2): flat triangle area
     200 vox^2 (step 20); ratio 2-D/3-D = 200 / A3. Fraction of triangles
     (FLAT-1 triangulation) with ratio > 2 or < 0.5.
 (d) 40 random valid vertices (rng [20260927, r, c], same as mesh_audit):
     L0 profile along the vertex normal over +-60 um (+-25 vox), Gaussian
     sigma 1 vox. Sheet peak = a local maximum (scipy find_peaks) with
     prominence >= P_MIN, where P_MIN = 0.25 x the median, over all c0-c8
     reference vertices, of the per-vertex largest prominence (computed
     from the reference tiles before any flag). All-zero profile = no peak.
 (e) boundary tiles (r0, r8, and any tile meeting an interior hole):
     40 rays per tile. r0/r8: 40 evenly spaced tile columns with a valid
     vertex; from the outermost valid vertex of that column (smallest row
     for r0 = top z, largest row for r8), direction = the unit tangent
     along the column fitted over the last 10 valid vertices, pointing out
     of the mesh. Holes: rim vertices (valid, 8-adjacent to the hole),
     direction = in-surface step toward the hole's centroid (grid Jacobian).
     At 0.5, 1, 2 and 5 mm along the ray: the +-60 um profile along the
     edge vertex's normal, peak rule as (d). For holes, points already past
     the far rim (valid mesh again) are not sampled.
 HOLE-FLAG (c9-c19 tiles): any of (a) invalid frac, (a) n holes,
 (b) union frac, (c) frac, (d) no-peak frac above the c0-c8 max; or (e)
 sheet at >= 2 mm on >= 25 % of rays (both 2 mm and 5 mm are reported).
usage: holes.py <mesh_dir> <out_rows.jsonl> <tiles spec: title|ref|rest>
"""

from __future__ import annotations

import json
import math
import sys
import time
import concurrent.futures as cf
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_count as cc  # noqa: E402
from mesh_audit import normals, profile, T  # noqa: E402

VOXMM = 2.4e-3
CELL_MM2 = (20 * VOXMM) ** 2
NR, NC = 9, 20
DISTS_MM = (0.5, 1.0, 2.0, 5.0)


def tiles(spec):
    title = [(r, c) for r in (0, 1) for c in range(11, 18)]
    ref = [(r, c) for r in range(NR) for c in range(0, 9)]
    if spec == "title":
        return title
    if spec == "ref":
        return ref
    return [(r, c) for r in range(NR) for c in range(NC) if (r, c) not in title and (r, c) not in ref]


def bounds(r, c, H, W):
    return (r * T) // 20, min(H, ((r + 1) * T) // 20), (c * T) // 20, min(W, ((c + 1) * T) // 20)


def voxel(xyz):
    x, y, z = (int(round(v)) for v in xyz)
    cz, cy, cx = z // 128, y // 128, x // 128
    off = ((z % 128) * 128 + (y % 128)) * 128 + (x % 128)
    b = cc._fetch(f"{cc.VOL}/{cz}/{cy}/{cx}", off, off)
    return None if b is None else b[0]


def best_prom(v):
    if not np.any(v > 0):
        return 0.0, None
    vs = ndimage.gaussian_filter1d(v.astype(float), 1.0)
    pk, pr = signal.find_peaks(vs, prominence=0)
    if pk.size == 0:
        return 0.0, None
    i = int(np.argmax(pr["prominences"]))
    return float(pr["prominences"][i]), int(pk[i])


def hole_labels(valid):
    inv = ~valid
    lab, n = ndimage.label(inv, structure=np.ones((3, 3)))
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]).tolist()) - {0}
    sizes = ndimage.sum(inv, lab, index=np.arange(1, n + 1))
    interior = [k for k in range(1, n + 1) if k not in border]
    return lab, {k: int(sizes[k - 1]) for k in interior}


def tile_row(P, V, lab, holes, r, c, pool):
    H, W = V.shape
    g0, g1, h0, h1 = bounds(r, c, H, W)
    v = V[g0:g1, h0:h1]
    out = {"r": r, "c": c, "grid_rows": [g0, g1], "grid_cols": [h0, h1], "n_vertices": int(v.size),
           "invalid_frac": float(1 - v.mean())}
    hl = [int(k) for k in np.unique(lab[g0:g1, h0:h1]) if int(k) in holes]
    out["holes"] = [{"label": k, "area_mm2": holes[k] * CELL_MM2} for k in hl]
    out["n_holes"] = len(hl)
    if v.sum() < 500:
        out["skip"] = "fewer than 500 valid vertices"
        return out
    Pt = P[g0:g1, h0:h1]
    # (c) official flattening area ratio
    A = Pt
    p00, p01, p10, p11 = A[:-1, :-1], A[:-1, 1:], A[1:, :-1], A[1:, 1:]
    q = v[:-1, :-1] & v[:-1, 1:] & v[1:, :-1] & v[1:, 1:]
    a1 = 0.5 * np.linalg.norm(np.cross(p00[q] - p10[q], p01[q] - p10[q]), axis=1)
    a2 = 0.5 * np.linalg.norm(np.cross(p01[q] - p10[q], p11[q] - p10[q]), axis=1)
    ratio = 200.0 / np.maximum(np.r_[a1, a2], 1e-9)
    out["flat_ratio_bad_frac"] = float(np.mean((ratio > 2) | (ratio < 0.5)))
    out["flat_ratio_p1_p50_p99"] = [float(np.percentile(ratio, k)) for k in (1, 50, 99)]
    ids = np.argwhere(v)
    # (b) zero / missing at 400 vertices
    rb = np.random.default_rng([20260928, r, c])
    pb = ids[rb.choice(len(ids), min(400, len(ids)), replace=False)]
    vals = list(pool.map(lambda ij: voxel(Pt[ij[0], ij[1]]), [tuple(x) for x in pb]))
    miss = np.array([x is None for x in vals])
    zero = np.array([x == 0 for x in vals])
    out["b_n"] = int(len(vals))
    out["b_missing_chunk_frac"] = float(miss.mean())
    out["b_zero_frac"] = float(zero.mean())
    out["b_zero_or_missing_frac"] = float((miss | zero).mean())
    # (d) profiles at 40 vertices (same picks as mesh_audit)
    N = normals(np.where(v[..., None], Pt, np.nan))
    rd = np.random.default_rng([20260927, r, c])
    okn = v & np.all(np.isfinite(N), -1)
    idn = np.argwhere(okn)
    pd_ = idn[rd.choice(len(idn), min(40, len(idn)), replace=False)]
    profs = list(pool.map(lambda ij: profile(Pt[ij[0], ij[1]], N[ij[0], ij[1]])[1], [tuple(x) for x in pd_]))
    out["d_best_prom"] = [best_prom(p)[0] for p in profs]
    # (e) boundary rays
    is_boundary = r in (0, NR - 1) or len(hl) > 0
    out["boundary_tile"] = bool(is_boundary)
    if is_boundary:
        out["e_rays"] = edge_rays(Pt, v, N, lab[g0:g1, h0:h1], hl, r, pool)
    return out


def edge_rays(Pt, v, N, labt, hl, r, pool):
    rays = []
    Hh, Ww = v.shape
    if r in (0, NR - 1):
        cols = [j for j in range(Ww) if v[:, j].any()]
        for j in [cols[int(k)] for k in np.linspace(0, len(cols) - 1, min(40, len(cols)))]:
            rows = np.where(v[:, j])[0]
            if r == 0:
                i0 = rows[0]
                seq = rows[:10]
                sgn = -1
            else:
                i0 = rows[-1]
                seq = rows[-10:]
                sgn = 1
            if len(seq) < 3:
                continue
            pts = Pt[seq, j]
            d = np.polyfit(seq.astype(float), pts, 1)[0]      # d(xyz)/d(row)
            t = sgn * d / (np.linalg.norm(d) + 1e-12)
            fin = [i for i in seq if np.all(np.isfinite(N[i, j]))]
            if not fin:
                continue
            # edge vertices have NaN normals (invalid neighbours): use the nearest inward finite one
            rays.append((Pt[i0, j], t, N[fin[0] if r == 0 else fin[-1], j], None))
    for k in hl:
        m = labt == k
        rim = ndimage.binary_dilation(m, np.ones((3, 3))) & v & np.all(np.isfinite(N), -1)
        ri = np.argwhere(rim)
        if len(ri) == 0:
            continue
        cen = np.argwhere(m).mean(0)
        for (i, j) in ri[np.linspace(0, len(ri) - 1, min(40, len(ri))).astype(int)]:
            gi = (cen - [i, j])
            gi /= np.linalg.norm(gi) + 1e-12
            di = Pt[min(i + 1, Hh - 1), j] - Pt[max(i - 1, 0), j]
            dj = Pt[i, min(j + 1, Ww - 1)] - Pt[i, max(j - 1, 0)]
            if not (np.all(np.isfinite(di)) and np.all(np.isfinite(dj))):
                continue
            t = gi[0] * di + gi[1] * dj
            t /= np.linalg.norm(t) + 1e-12
            rays.append((Pt[i, j], t, N[i, j], (k, i, j, gi)))
    res = []

    def one(ray):
        p0, t, n, hole = ray
        if not (np.all(np.isfinite(p0)) and np.all(np.isfinite(t)) and np.all(np.isfinite(n))):
            return {"hole": None, "prom": None, "error": "non-finite ray"}
        row = {"hole": None if hole is None else int(hole[0]), "prom": {}}
        for dmm in DISTS_MM:
            if hole is not None:
                # stop once the straight step in grid space re-enters valid mesh
                k, i, j, gi = hole
                steps = dmm / (20 * VOXMM)
                ii, jj = int(round(i + gi[0] * steps)), int(round(j + gi[1] * steps))
                if not (0 <= ii < Hh and 0 <= jj < Ww) or labt[ii, jj] != k:
                    row["prom"][str(dmm)] = None
                    continue
            q = p0 + t * (dmm / VOXMM)
            row["prom"][str(dmm)] = best_prom(profile(q, n)[1])[0]
        return row

    return list(pool.map(one, rays))


def main(mesh_dir, out_rows, spec):
    d = Path(mesh_dir)
    X, Y, Z = (np.load(d / f"{c}.npy") for c in "xyz")
    V = (X != -1) & np.isfinite(X) & np.isfinite(Y) & np.isfinite(Z) & (Z > 0)
    P = np.stack([X, Y, Z], -1).astype(np.float64)
    del X, Y, Z
    lab, holes = hole_labels(V)
    print("interior holes in whole grid:", len(holes), flush=True)
    done = set()
    if Path(out_rows).exists():
        done = {(j["r"], j["c"]) for j in map(json.loads, open(out_rows))}
    with cf.ThreadPoolExecutor(24) as pool:
        for (r, c) in tiles(spec):
            if (r, c) in done:
                continue
            t0 = time.time()
            row = tile_row(P, V, lab, holes, r, c, pool)
            row["wall_s"] = time.time() - t0
            with open(out_rows, "a") as f:
                f.write(json.dumps(row) + "\n")
            print(r, c, row.get("invalid_frac"), row.get("n_holes"), round(row["wall_s"]), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
