"""GOLD injection-recovery on real CT (RULES.md DECL-P4-10 item 3). Numbers only; nothing is displayed.

Provenance: Project HERCULES | owner the owner | [id removed]

For each location (a chunk-aligned patch of ~6.6 mm of a material's surface volume, sheet slab only) one Greek
capital (polyline glyph, height 2-4 mm, stroke 0.3-0.6 mm) is planted as a gold layer of Au-equivalent thickness t
at a planar depth near the mesh surface. The grey increment follows MEMO.md section 3:
  dG(z, y, x) = dG_pap * (mu_Au / mu_pap(rho)) * Mf(y, x) * lf(z)
  - lf: exact fractional occupancy of the layer on the reconstruction depth grid (1.129 um for E1/C1, 2.4 um for
    E2/C2), filtered by the Paganin-mismatch x unsharp transfer
      H(k) = (1 + a g_Au k^2) / (1 + a g_rec k^2) * (1 + c (1 - exp(-2 pi^2 s^2 k^2))),  a = pi lambda z_det
    (DC gain 1, so the depth integral is conserved);
  - Mf: glyph coverage (4x supersampled) on the level grid, filtered in-plane by the same H (separable approximation).
  - E1/C1: the increment is added on the 1.129 um sub-slices (each L1 slice split in 2 equal sub-slices), clipped to
    [0, 255] and rounded per sub-slice, then pair-averaged and rounded (models clip-then-mean of the L1 build).
  - E2/C2: added at level 1 (4.8 um in-plane), clipped and rounded.
Detection uses gold.column_stats / block sums / disc mean exactly as the tile scorer, with params.json tau.
Recovered iff new hot area (hot after injection and not hot before) inside the glyph mask dilated by 0.15 mm is
>= 0.5 x glyph area AND > A_p99 of the material's control tiles.
False positives: the same criterion on the uninjected patch (virtual glyph) and on its 90-degree rotation.
Usage: python inject.py <params.json> <scratch> <out.jsonl> <MAT> <n_locations> [--procs 4]
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold as G  # noqa: E402

LAM = 12.39842 / 78.0 * 1e-10  # m

# Greek capitals as polylines in a unit box (x right, y down), height 1, width ~0.8
_O = [(0.4 + 0.4 * math.cos(t), 0.5 + 0.5 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 33)]
GLYPHS = {
    "ALPHA": [[(0, 1), (0.4, 0), (0.8, 1)], [(0.15, 0.62), (0.65, 0.62)]],
    "GAMMA": [[(0.1, 1), (0.1, 0), (0.75, 0)]],
    "DELTA": [[(0, 1), (0.4, 0), (0.8, 1), (0, 1)]],
    "EPSILON": [[(0.75, 0), (0.1, 0), (0.1, 1), (0.75, 1)], [(0.1, 0.5), (0.6, 0.5)]],
    "ETA": [[(0.1, 0), (0.1, 1)], [(0.7, 0), (0.7, 1)], [(0.1, 0.5), (0.7, 0.5)]],
    "KAPPA": [[(0.1, 0), (0.1, 1)], [(0.75, 0), (0.1, 0.55)], [(0.3, 0.4), (0.75, 1)]],
    "LAMBDA": [[(0, 1), (0.4, 0), (0.8, 1)]],
    "MU": [[(0.02, 1), (0.1, 0), (0.4, 0.7), (0.7, 0), (0.78, 1)]],
    "NU": [[(0.1, 1), (0.1, 0), (0.7, 1), (0.7, 0)]],
    "PI": [[(0.1, 1), (0.1, 0), (0.7, 0), (0.7, 1)]],
    "SIGMA": [[(0.75, 0), (0.05, 0), (0.45, 0.5), (0.05, 1), (0.75, 1)]],
    "TAU": [[(0.05, 0), (0.75, 0)], [(0.4, 0), (0.4, 1)]],
    "OMICRON": [_O],
    "THETA": [_O, [(0.2, 0.5), (0.6, 0.5)]],
    "OMEGA": [[(0.05, 1), (0.28, 1), (0.1, 0.65)] + [(0.4 + 0.33 * math.cos(t), 0.4 + 0.4 * math.sin(t))
                                                        for t in np.linspace(math.radians(135), math.radians(405), 20)]
              + [(0.7, 0.65), (0.52, 1), (0.75, 1)]],
}


def transfer(k, p):
    """k in cycles/m (array). Paganin-mismatch x unsharp transfer."""
    a = math.pi * LAM * p["z_det_m"]
    s = p["unsharp_sigma_m"]
    return (1 + a * p["g_au"] * k ** 2) / (1 + a * p["g_rec"] * k ** 2) * (1 + p["unsharp_c"] * (1 - np.exp(-2 * math.pi ** 2 * s ** 2 * k ** 2)))


def depth_profile(t_um, z_top_um, dz_um, n, p):
    """Filtered occupancy on n depth bins of size dz_um starting at depth 0 (bin i covers [i dz, (i+1) dz))."""
    fine = 16
    m = n * fine
    edges = np.arange(m + 1) * dz_um / fine
    occ = np.clip(np.minimum(edges[1:], z_top_um + t_um) - np.maximum(edges[:-1], z_top_um), 0, None) / (dz_um / fine)
    pad = 4 * m
    buf = np.zeros(m + 2 * pad)
    buf[pad:pad + m] = occ
    k = np.fft.rfftfreq(buf.size, d=dz_um / fine * 1e-6)
    f = np.fft.irfft(np.fft.rfft(buf) * transfer(k, p), n=buf.size)[pad:pad + m]
    return f.reshape(n, fine).mean(1)  # mean occupancy per bin (fraction of bin filled with Au)


def glyph_mask(shape, px_mm, rng, name):
    h_mm = rng.uniform(2.0, 4.0)
    w_mm = rng.uniform(0.3, 0.6)
    ang = math.radians(rng.uniform(-10, 10))
    ss = 4
    H, W = shape
    img = np.zeros((H * ss, W * ss), np.uint8)
    cy, cx = H * ss / 2, W * ss / 2
    sc = h_mm / px_mm * ss
    for pl in GLYPHS[name]:
        pts = []
        for x, y in pl:
            X_, Y_ = (x - 0.4) * sc, (y - 0.5) * sc
            pts.append((cx + X_ * math.cos(ang) - Y_ * math.sin(ang), cy + X_ * math.sin(ang) + Y_ * math.cos(ang)))
        cv2.polylines(img, [np.round(np.array(pts) * 16).astype(np.int32)], False, 255,
                      thickness=max(1, int(round(w_mm / px_mm * ss))), lineType=cv2.LINE_AA, shift=4)
    cov = img.reshape(H, ss, W, ss).astype(np.float32).mean((1, 3)) / 255.0
    return cov, {"glyph": name, "height_mm": h_mm, "stroke_mm": w_mm, "angle_deg": math.degrees(ang)}


def filt2d(a, px_m, p):
    ky = np.fft.fftfreq(a.shape[0], d=px_m)
    kx = np.fft.rfftfreq(a.shape[1], d=px_m)
    k = np.sqrt(ky[:, None] ** 2 + kx[None, :] ** 2)
    return np.fft.irfft2(np.fft.rfft2(a) * transfer(k, p), s=a.shape).astype(np.float32)


def features(V, sat, ok_mesh, B, px_mm, radius_mm):
    P, S, ok = G.column_stats(V, sat)
    ok = ok & ok_mesh
    okf = ok.astype(np.float32)
    maps = {"P": G.block_sum(P * okf, B), "S": G.block_sum(S * okf, B), "n": G.block_sum(okf, B)}
    Z, Zs, _ = G.score_maps(maps, px_mm, radius_mm, tau=None)
    return Z


def fetch_patch(mat, yc0, xc0, nch, z0, z1, threads=48):
    import concurrent.futures as cf
    n = z1 - z0 + 1
    V = np.zeros((n, nch * G.CH, nch * G.CH), np.uint8)
    jobs = [(i, j) for i in range(nch) for j in range(nch)]

    def w(ij):
        i, j = ij
        return ij, G.fetch_chunk(mat, yc0 + i, xc0 + j, z0, z1)
    absent = 0
    with cf.ThreadPoolExecutor(threads) as ex:
        for (i, j), a in ex.map(w, jobs):
            if a is None:
                absent += 1
                continue
            V[:, i * G.CH:(i + 1) * G.CH, j * G.CH:(j + 1) * G.CH] = a
    return V, absent


_ST = {}


def init(mat, params, name):
    _ST.update(mat=mat, P=params, name=name)


def run_location(job):
    mat, P, name = _ST["mat"], _ST["P"], _ST["name"]
    m = mat["m"]
    mp_ = P["materials"][name]
    rng = np.random.default_rng(job["seed"])
    B, px_mm = m["B"], m["px_um"] * m["B"] / 1000.0
    nch = mp_["patch_chunks"]
    z0, z1 = G.slab(name, P["core"]["half_um"])
    V, absent = fetch_patch(mat, job["yc0"], job["xc0"], nch, z0 - G.FLANK, z1 + G.FLANK)
    ys = job["yc0"] * G.CH + np.arange(nch * G.CH)
    xs = job["xc0"] * G.CH + np.arange(nch * G.CH)
    okm = G.level_valid(mat, ys, xs)
    usable = float(((V.min(0) > 0) & okm).mean())
    rec = {"mat": name, "loc": job["i"], "yc0": job["yc0"], "xc0": job["xc0"], "tile": job["tile"],
           "absent_chunks": absent, "usable_frac": usable}
    if usable < 0.9:
        rec["skipped"] = "usable < 0.9"
        return rec
    tau, a99 = P["materials"][name]["tau"], P["materials"][name]["A_p99_mm2"]
    radius = P["core"]["radius_mm"]
    sat = P["core"]["sat"]
    Z0 = features(V, sat, okm, B, px_mm, radius)
    Zr = features(np.ascontiguousarray(np.rot90(V, 1, axes=(1, 2))), sat, np.rot90(okm), B, px_mm, radius)
    gname = job["glyph"]
    cov, ginfo = glyph_mask(V.shape[1:], m["px_um"] / 1000.0, rng, gname)
    rec.update(ginfo)
    # evaluation region on the work grid
    covw = G.block_sum(cov, B) / (B * B)
    gl = covw >= 0.5
    rpx = int(round(radius / px_mm))
    reg = cv2.dilate(gl.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rpx + 1, 2 * rpx + 1))) > 0
    A_gl = float(gl.sum() * px_mm ** 2)
    rec["glyph_area_mm2"] = A_gl

    def crit(Z, Zb):
        hot = np.isfinite(Z) & (Z > tau)
        hotb = np.isfinite(Zb) & (Zb > tau)
        new = hot & ~hotb & reg
        a_new = float(new.sum() * px_mm ** 2)
        return a_new, bool(a_new >= 0.5 * A_gl and a_new > a99)

    def crit_null(Z):
        hot = np.isfinite(Z) & (Z > tau) & reg
        a = float(hot.sum() * px_mm ** 2)
        return a, bool(a >= 0.5 * A_gl and a > a99)
    rec["null_unrotated"] = crit_null(Z0)
    rec["null_rot90"] = crit_null(Zr)
    rec["base_hot_in_region_mm2"] = rec["null_unrotated"][0]
    # depth of the planted layer: top face at centre-slice start + offset
    dz_rec = mp_["recon_dz_um"]
    sub = mp_["subslices"]
    n = V.shape[0]
    off_um = rng.uniform(-4, 4) * m["dz_um"]
    z_top = (n // 2) * m["dz_um"] + m["dz_um"] / 2 + off_um
    rec["layer_top_offset_um"] = off_um
    Mf = filt2d(cov, m["px_um"] * 1e-6, mp_["tf"])
    res = {}
    for rho in P["rho_pap"]:
        amp = mp_["dG_pap"] * P["mu_ratio_78keV"][str(rho)]
        for t in P["thicknesses_um"]:
            lf = depth_profile(t, z_top, dz_rec, n * sub, mp_["tf"])
            Vn = np.empty_like(V)
            for r0 in range(0, V.shape[1], 256):
                vb = V[:, r0:r0 + 256].astype(np.float32)
                base = np.repeat(vb, sub, axis=0) if sub > 1 else vb
                add = amp * lf[:, None, None] * Mf[None, r0:r0 + 256, :]
                Vs = np.clip(np.rint(base + add), 0, 255)
                if sub > 1:
                    Vs = np.rint(Vs.reshape(n, sub, *Vs.shape[1:]).mean(1))
                Vn[:, r0:r0 + 256] = Vs.astype(np.uint8)
            Vn[V == 0] = 0  # keep out-of-scan zeros as zeros
            Z1 = features(Vn, sat, okm, B, px_mm, radius)
            a_new, ok = crit(Z1, Z0)
            # conserved depth integral (grey x level slices) at full glyph coverage, before clipping
            integ = float(amp * lf.sum() / sub * float(Mf[cov > 0.99].mean())) if (cov > 0.99).any() else None
            res[f"rho{rho}|t{t}"] = {"new_hot_mm2": a_new, "recovered": ok, "depth_integral_grey_slices": integ,
                                     "Zmax_in_region": float(np.nanmax(np.where(reg, Z1, np.nan)))}
    rec["results"] = res
    return rec


def choose_locations(mat, name, nloc, P, seed):
    rng = np.random.default_rng(seed)
    nch = P["materials"][name]["patch_chunks"]
    f = 2 ** mat["m"]["level"]
    T = mat["T"]
    tiles = mat["tiles"]
    jobs = []
    glyphs = sorted(GLYPHS)
    tries = 0
    while len(jobs) < nloc and tries < 50 * nloc:
        tries += 1
        t = tiles[rng.integers(len(tiles))]
        y0, x0 = t["r"] * T // f, t["c"] * T // f
        side = T // f
        yc0 = (y0 + rng.integers(0, max(1, side - nch * G.CH))) // G.CH
        xc0 = (x0 + rng.integers(0, max(1, side - nch * G.CH))) // G.CH
        ys = yc0 * G.CH + np.arange(0, nch * G.CH, 16)
        xs = xc0 * G.CH + np.arange(0, nch * G.CH, 16)
        if G.level_valid(mat, ys, xs).mean() < 0.95:
            continue
        jobs.append({"i": len(jobs), "yc0": int(yc0), "xc0": int(xc0), "tile": [t["r"], t["c"]],
                     "glyph": glyphs[len(jobs) % len(glyphs)], "seed": int(rng.integers(2 ** 31))})
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("params")
    ap.add_argument("scratch")
    ap.add_argument("out")
    ap.add_argument("mat")
    ap.add_argument("nloc", type=int)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--extra", type=int, default=6, help="spare locations for skipped (usable < 0.9) patches")
    a = ap.parse_args()
    P = json.load(open(a.params))
    mat = G.load_material(a.mat, a.scratch)
    jobs = choose_locations(mat, a.mat, a.nloc + a.extra, P, P["injection_seed"] + sum(map(ord, a.mat)))
    ctx = mp.get_context("fork")
    n_ok = 0
    with ctx.Pool(a.procs, initializer=init, initargs=(mat, P, a.mat)) as pool, open(a.out, "a") as fo:
        for rec in pool.imap(run_location, jobs):
            if "skipped" not in rec:
                n_ok += 1
                rec["counted"] = n_ok <= a.nloc
            fo.write(json.dumps(rec) + "\n")
            fo.flush()
            print(a.mat, rec["loc"], rec.get("skipped", ""), rec.get("counted"), flush=True)


if __name__ == "__main__":
    main()
