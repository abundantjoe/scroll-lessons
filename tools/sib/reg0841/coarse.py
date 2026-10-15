# Provenance: Project HERCULES | owner the owner | [id removed]
"""Steps 1 and 3 on coarse levels (CT only, numbers only).

Conventions: arrays [z, y, x]; points (x, y, z) in level-0 voxels; level-L index i has
level-0 centre i*2^L + (2^L - 1)/2 (exact mean pyramid, pyr_check.json).
Mesh affine (mesh_fit.json joint): q2 = A p9 + c.

Step 1 (flips / remounts): candidate orientations G applied about the rescan volume centre
C2, q' = G (A p + c - C2) + C2, G in {I, Rz90, Rz180, Rz270, flipX, flipY, flipZ, Rx180}.
For each G and each of 9 rescan L5 slices spread over the rescan z range, the slice pixels
(masked > 0, every 4th pixel) are mapped to the 9 um frame and 9 um L4 is sampled for every
z offset dz (full 9 um z range, step 32 vox) -> NCC(dz). At the 3 best dz a 2-D phase
correlation of the sampled slice against the rescan slice gives an in-plane shift, and the
NCC is re-scored after that shift. Score = best NCC per slice, and the spread of the implied
dz across slices.

Step 3 (z band, whole-slice NCC): for G = I, 25 rescan L4 slices (every ~39 L4 slices, every 4th px) are
mapped as above and the 9 um L3 band (z 11264-16383... cached z 11264-18431) is sampled at
dz in [-400, 400] step 2 vox, then refined at step 0.5 in +-8. Reports dz_peak(z2), NCC
peak, peak-to-sidelobe ratio (max NCC with |dz - dz_peak| > 40 vox), and the 9 um z of the
first and last rescan slice under the mesh affine corrected by dz_peak.
"""
import json, os, sys
import numpy as np
from scipy.ndimage import map_coordinates

C = "/work/reg/cache"
REPO = "/home/user/dominion"
mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]
A = np.array(mf["A"]); c = np.array(mf["c"])
S9 = (19400, 7703, 7703); S2 = (15121, 30469, 30469)
C2 = np.array([(S2[2] - 1) / 2, (S2[1] - 1) / 2, (S2[0] - 1) / 2])


def ctr(L):
    return (2 ** L - 1) / 2


def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def G_mats():
    I = np.eye(3)
    Rz = lambda k: np.array([[np.cos(k), -np.sin(k), 0], [np.sin(k), np.cos(k), 0], [0, 0, 1]]).round(12)
    return {"I": I, "Rz90": Rz(np.pi / 2), "Rz180": Rz(np.pi), "Rz270": Rz(3 * np.pi / 2),
            "flipX": np.diag([-1., 1, 1]), "flipY": np.diag([1., -1, 1]), "flipZ": np.diag([1., 1, -1]),
            "Rx180": np.diag([1., -1, -1])}


def map_slice(G, L2, k, shape2, sub):
    """Rescan level-L2 slice k pixels (sub-sampled) -> 9 um level-0 points p (x, y, z)."""
    s = 2 ** L2
    yy, xx = np.mgrid[0:shape2[1]:sub, 0:shape2[2]:sub]
    q = np.stack([xx.ravel() * s + ctr(L2), yy.ravel() * s + ctr(L2), np.full(xx.size, k * s + ctr(L2))], 1)
    # invert q = G (A p + c - C2) + C2  ->  A p + c = G^T (q - C2) + C2
    qq = (q - C2) @ G + C2
    p = np.linalg.solve(A, (qq - c).T).T
    return p, yy.ravel(), xx.ravel()


def sample9(vol, L, z0L, p, dz):
    s = 2 ** L
    coords = np.stack([(p[:, 2] + dz - ctr(L)) / s - z0L, (p[:, 1] - ctr(L)) / s, (p[:, 0] - ctr(L)) / s])
    return map_coordinates(vol, coords, order=1, mode="constant", cval=0.0)


def phase_shift2d(a, b):
    """Shift (dy, dx) such that b(y, x) ~ a(y - dy, x - dx)."""
    w = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    Fa = np.fft.fft2((a - a.mean()) * w); Fb = np.fft.fft2((b - b.mean()) * w)
    R = Fb * np.conj(Fa); R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    i = np.unravel_index(np.argmax(r), r.shape)
    return [int(v if v <= n // 2 else v - n) for v, n in zip(i, r.shape)]


def step1(res):
    v9 = np.load(f"{C}/v9_L4.npy").astype(np.float32)
    v2 = np.load(f"{C}/v2_L5.npy").astype(np.float32)
    ks = np.linspace(40, v2.shape[0] - 41, 9).round().astype(int)
    out = {}
    for name, G in G_mats().items():
        rows = []
        for k in ks:
            sl = v2[k]
            p, yy, xx = map_slice(G, 5, k, v2.shape, 4)
            ref = sl[yy, xx]
            m = ref > 0
            if m.sum() < 1000:
                continue
            p = p[m]; ref = ref[m]; yy = yy[m]; xx = xx[m]
            dzs = np.arange(-20000, 20000, 32.0)
            base_z = p[:, 2].mean()
            dzs = dzs[(base_z + dzs > 0) & (base_z + dzs < S9[0])]
            nc = []
            for dz in dzs:
                smp = sample9(v9, 4, 0, p, dz)
                mm = smp > 0
                nc.append(ncc(ref[mm], smp[mm]) if mm.sum() > 0.3 * len(ref) else -1)
            nc = np.array(nc)
            best = {"ncc": -2}
            for i in np.argsort(nc)[::-1][:3]:
                # in-plane refinement on the full sampled slice grid (every 2nd px)
                grid = np.zeros((v2.shape[1] // 2 + 1, v2.shape[2] // 2 + 1), np.float32); gs = grid.copy()
                pf, yf, xf = map_slice(G, 5, k, v2.shape, 2)
                gs[yf // 2, xf // 2] = sample9(v9, 4, 0, pf, dzs[i]); grid[yf // 2, xf // 2] = sl[yf, xf]
                dy, dx = phase_shift2d(gs, grid)
                gs2 = np.roll(gs, (dy, dx), (0, 1))
                mm = (grid > 0) & (gs2 > 0)
                v = ncc(grid[mm], gs2[mm]) if mm.sum() > 1000 else -1
                if v > best["ncc"]:
                    best = {"ncc": v, "ncc_noshift": float(nc[i]), "dz": float(dzs[i]), "shift_px_L5": [dy, dx]}
            rows.append(dict(k_L5=int(k), **best))
        dz = np.array([r["dz"] for r in rows]); n = np.array([r["ncc"] for r in rows])
        out[name] = dict(slices=rows, median_ncc=float(np.median(n)), min_ncc=float(n.min()),
                         dz_median=float(np.median(dz)), dz_spread_iqr=float(np.subtract(*np.percentile(dz, [75, 25]))),
                         shift_nonzero=int(sum(r["shift_px_L5"] != [0, 0] for r in rows)))
        print(name, out[name]["median_ncc"], out[name]["dz_median"], out[name]["dz_spread_iqr"], flush=True)
    res["step1_orientation"] = out


def step3(res):
    v9 = np.load(f"{C}/v9_L3.npy").astype(np.float32); z0L = 1408  # cached L3 slices start (fetch_coarse.json)
    v2 = np.load(f"{C}/v2_L4.npy", mmap_mode="r")
    G = np.eye(3)
    ks = np.linspace(0, v2.shape[0] - 1, 25).round().astype(int)
    rows = []
    for k in ks:
        sl = np.asarray(v2[k], np.float32)
        p, yy, xx = map_slice(G, 4, k, v2.shape, 4)
        ref = sl[yy, xx]; m = ref > 0
        if m.sum() < 1000:
            rows.append(dict(k_L4=int(k), z2=float(k * 16 + ctr(4)), skipped="empty")); continue
        p = p[m]; ref = ref[m]
        def curve(dzs):
            o = []
            for dz in dzs:
                smp = sample9(v9, 3, z0L, p, dz); mm = smp > 0
                o.append(ncc(ref[mm], smp[mm]) if mm.sum() > 0.5 * len(ref) else np.nan)
            return np.array(o)
        dzs = np.arange(-400, 400.1, 2.0); nc = curve(dzs)
        i = np.nanargmax(nc)
        fine = np.arange(dzs[i] - 8, dzs[i] + 8.01, 0.5); nf = curve(fine); j = np.nanargmax(nf)
        side = np.nanmax(np.where(np.abs(dzs - fine[j]) > 40, nc, np.nan))
        pz = p[:, 2].mean()
        rows.append(dict(k_L4=int(k), z2=float(k * 16 + ctr(4)), z9_mesh_affine=float(pz), dz_peak=float(fine[j]),
                         ncc_peak=float(nf[j]), ncc_dz0=float(curve([0.0])[0]), sidelobe_max=float(side),
                         peak_to_sidelobe=float(nf[j] - side), n_px=int(m.sum())))
        print(rows[-1], flush=True)
    res["step3_zband"] = dict(rows=rows)
    ok = [r for r in rows if "dz_peak" in r]
    zz = np.array([[r["z2"], r["z9_mesh_affine"] + r["dz_peak"]] for r in ok])
    fitl = np.polyfit(zz[:, 0], zz[:, 1], 1)
    res["step3_zband"].update(
        z9_vs_z2_linear_fit=fitl.tolist(), implied_scale_z=float(1 / fitl[0]),
        z9_at_rescan_z0=float(np.polyval(fitl, 0)), z9_at_rescan_zmax=float(np.polyval(fitl, S2[0] - 1)),
        dz_peak_median=float(np.median([r["dz_peak"] for r in ok])),
        dz_peak_max_abs=float(max(abs(r["dz_peak"]) for r in ok)))


if __name__ == "__main__":
    res = {"mesh_affine": {"A": A.tolist(), "c": c.tolist()}}
    which = sys.argv[1]
    if which in ("1", "all"):
        step1(res)
    if which in ("3", "all"):
        step3(res)
    json.dump(res, open(f"{REPO}/logs/sib/reg0841/coarse_step{which}.json", "w"), indent=1)
