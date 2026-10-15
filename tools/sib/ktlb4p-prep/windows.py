# Provenance: Project HERCULES | owner the owner | [id removed]
"""Candidate 2 x 2 cm windows on the 9.362 um organizer canvases of PHerc0500P2 (numbers only).

Canvas convention (as D1/D3): canvas pixel c <-> grid g = (c + 0.5) * scale (scale 0.05).
Samples every STRIDE canvas px. For each sample: 3-D point p9 (bilinear over the 9 um grid;
valid iff its 4 grid corners are valid); q0 = model(p9) in the 2.215 um volume (model_final.json);
nearest vertex of the SAME segment's 2.215 um mesh densified 5 x 5 (4-vox spacing; KD-tree); mapped iff the 3-D distance
<= MAP_TOL level-0 2.215 um vox; the organizer reference value is the ink map pixel at that
vertex's 2.215 canvas position, refined by the in-grid offset of the projection.

Window (2136 x 2136 px = 2 x 2 cm at 9.362 um) on a 128-px lattice is a CANDIDATE iff
mesh-valid >= 0.90 and reference-mapped >= 0.90 of its samples (feasibility only; the
reference VALUE is never used to select). Reported per window: coverage fractions, reference
ink fraction (>= 150; used only to flag BLANK candidates < 1 %, as the brief asks), and the
window-level zero-CT fraction on the 9 um volume (level 2, nearest voxel).
Usage: windows.py OUT_JSON
"""
import json, os, sys, time
import numpy as np
import tifffile
from scipy.spatial import cKDTree

REPO = "/home/user/dominion"
sys.path.insert(0, f"{REPO}/src")
from hercules.geometry.tifxyz import read_tifxyz, valid_mask, sample_grid, densify  # noqa: E402

S3 = "/work/handed/s3/PHerc0500P2/segments"
WIN = 2136
LAT = 128
STRIDE = 8
MAP_TOL = 8.0  # level-0 2.215 um vox (= 1.9 vox at 9 um) to the 5x5-densified 2.215 um mesh (4-vox spacing)
DENS = 5
model = json.load(open(f"{REPO}/logs/sib/ktlb4p-prep/reg/model_final.json"))
A = np.array(model["A"]); c = np.array(model["c"])
W = np.array(model["W"]) if model["kind"] == "affine+Q" else None


def fmap(P):
    if W is None:
        return P @ A.T + c
    x, y, z = (P / 1000.0).T
    F = np.c_[x, y, z, np.ones(len(x)), x * x, x * y, y * y]
    return (P + F @ W) @ A.T + c


def ct_sampler():
    """Nearest level-2 voxel of the 9 um volume (chunks cached in memory)."""
    sys.path.insert(0, f"{REPO}/tools/sib/ktlb4p-prep/reg")
    import zio
    (shp, ch) = zio.meta("v9", 2)
    cache = {}

    def samp(P):
        i = np.floor(P / 4).astype(int)
        v = np.zeros(len(P))
        ok = (i >= 0).all(1) & (i[:, 0] < shp[2]) & (i[:, 1] < shp[1]) & (i[:, 2] < shp[0])
        keys = np.stack([i[:, 2] // ch[0], i[:, 1] // ch[1], i[:, 0] // ch[2]], 1)
        for k in {tuple(x) for x in keys[ok].tolist()}:
            if k not in cache:
                arr, _ = zio.read("v9", 2, k[0] * ch[0], (k[0] + 1) * ch[0], k[1] * ch[1], (k[1] + 1) * ch[1],
                                  k[2] * ch[2], (k[2] + 1) * ch[2], tag="windows_L2")
                cache[k] = arr
            sel = ok & np.all(keys == k, 1)
            q = i[sel]
            v[sel] = cache[k][q[:, 2] - k[0] * ch[0], q[:, 1] - k[1] * ch[1], q[:, 0] - k[2] * ch[2]]
        return v
    return samp


def main():
    samp = ct_sampler()
    out = dict(win_px=WIN, lattice_px=LAT, stride_px=STRIDE, map_tol_2um_vox=MAP_TOL, model_kind=model["kind"],
               segments={}, windows=[])
    for seg in sorted(os.listdir(S3)):
        d9 = [d for d in os.listdir(f"{S3}/{seg}/mesh") if d.endswith("9.362um.tifxyz")]
        d2 = [d for d in os.listdir(f"{S3}/{seg}/mesh") if d.endswith("2.215um.tifxyz")]
        ref = f"/work/k4p/ref/{seg}.tif"
        if not d9 or not d2 or not os.path.exists(ref):
            out["segments"][seg] = dict(skipped="missing 9 um mesh, 2.215 um mesh or reference map")
            continue
        t0 = time.time()
        m9 = read_tifxyz(f"{S3}/{seg}/mesh/{d9[0]}"); m2 = read_tifxyz(f"{S3}/{seg}/mesh/{d2[0]}")
        s9 = m9.scale[0]; s2 = m2.scale[0]
        H9, W9 = int(round(m9.points.shape[0] / s9)), int(round(m9.points.shape[1] / s9))
        cy, cx = np.mgrid[STRIDE // 2:H9:STRIDE, STRIDE // 2:W9:STRIDE]
        gy, gx = (cy + 0.5) * s9, (cx + 0.5) * s9
        P = sample_grid(m9.points.astype(np.float64), gy, gx)  # sentinel -1 where invalid
        val = valid_mask(P)
        # 2.215 um mesh vertices
        p2 = densify(m2.points.astype(np.float64), DENS).astype(np.float64); v2 = valid_mask(p2)
        iy2, ix2 = np.nonzero(v2)
        s2d = s2 * DENS  # dense grid index -> canvas: (i / (s2 * DENS)) - 0.5
        tree = cKDTree(p2[v2])
        Q = fmap(P[val])
        dist, idx = tree.query(Q, distance_upper_bound=MAP_TOL)
        mapped = np.zeros(val.shape, bool)
        refv = np.full(val.shape, -1, np.int16)
        okm = np.isfinite(dist)
        vy, vx = np.nonzero(val)
        mapped[vy[okm], vx[okm]] = True
        ink = tifffile.imread(ref)
        ry = np.clip(np.round(iy2[idx[okm]] / s2d - 0.5).astype(int), 0, ink.shape[0] - 1)
        rx = np.clip(np.round(ix2[idx[okm]] / s2d - 0.5).astype(int), 0, ink.shape[1] - 1)
        refv[vy[okm], vx[okm]] = ink[ry, rx]
        del ink
        # window-level CT: zero at the 3-D point (9 um level 2)
        zero = np.zeros(val.shape, bool)
        ct = samp(P[val])
        zero[vy, vx] = ct == 0
        # canvas-lattice windows via summed-area tables over the sample grid
        k = WIN // STRIDE

        def sat(a):
            return np.pad(a.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))

        Sv, Sm, Sz = sat(val), sat(mapped), sat(zero)
        Si = sat(refv >= 150)
        Sn = sat((refv >= 0) & (refv < 150))
        nwin = 0
        for y0 in range(0, H9 - WIN + 1, LAT):
            for x0 in range(0, W9 - WIN + 1, LAT):
                a, b = y0 // STRIDE, x0 // STRIDE
                box = lambda S: int(S[a + k, b + k] - S[a, b + k] - S[a + k, b] + S[a, b])  # noqa: E731
                n = k * k
                nv, nm = box(Sv), box(Sm)
                if nv < 0.9 * n or nm < 0.9 * n:
                    continue
                ni, nn, nz = box(Si), box(Sn), box(Sz)
                out["windows"].append(dict(segment=seg, y0=y0, x0=x0, h=WIN, w=WIN, mesh_valid=nv / n, ref_mapped=nm / n,
                                           ref_ink_frac=ni / max(ni + nn, 1), zero_ct_frac=nz / max(nv, 1),
                                           blank_candidate=bool(ni / max(ni + nn, 1) < 0.01)))
                nwin += 1
        out["segments"][seg] = dict(canvas_hw=[H9, W9], n_samples=int(val.size), frac_valid=float(val.mean()),
                                    frac_mapped_of_valid=float(mapped.sum() / max(val.sum(), 1)),
                                    map_dist_median_2um=float(np.median(dist[okm])) if okm.any() else None,
                                    n_candidate_windows=nwin, seconds=round(time.time() - t0, 1))
        print(seg[:34], out["segments"][seg], flush=True)
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print("windows", len(out["windows"]))


if __name__ == "__main__":
    main()
