"""p4-pig-cu injection-recovery (RULES.md DECL-P4-10 item 3): Egyptian-blue-like grain-field Greek capitals planted into
real CT sheet slabs at control (C1, C2) and title-strip (E1, E2) locations; the unchanged cu.py detector is run on each
block with and without the plant.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: blocks are held as arrays and reduced to detector numbers; nothing is displayed or saved as an image.
Parameters come from params.json["injection"] (frozen). Usage: python inject.py <MAT> <out.jsonl> [site_from site_to]
"""
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time

import cv2
import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cu  # noqa: E402
import hz_common as HZ  # noqa: E402

CH = 128
LETTERS = {
    "A": [[(0, 1), (0.4, 0), (0.8, 1)], [(0.16, 0.6), (0.64, 0.6)]],
    "Gamma": [[(0, 1), (0, 0), (0.7, 0)]],
    "Delta": [[(0, 1), (0.4, 0), (0.8, 1), (0, 1)]],
    "E": [[(0.7, 0), (0, 0), (0, 1), (0.7, 1)], [(0, 0.5), (0.55, 0.5)]],
    "H": [[(0, 0), (0, 1)], [(0.7, 0), (0.7, 1)], [(0, 0.5), (0.7, 0.5)]],
    "K": [[(0, 0), (0, 1)], [(0.7, 0), (0, 0.55)], [(0.2, 0.4), (0.7, 1)]],
    "Lambda": [[(0, 1), (0.4, 0), (0.8, 1)]],
    "M": [[(0, 1), (0, 0), (0.4, 0.6), (0.8, 0), (0.8, 1)]],
    "N": [[(0, 1), (0, 0), (0.7, 1), (0.7, 0)]],
    "Pi": [[(0, 1), (0, 0), (0.7, 0), (0.7, 1)]],
    "Sigma": [[(0.7, 0), (0, 0), (0.35, 0.5), (0, 1), (0.7, 1)]],
    "T": [[(0, 0), (0.8, 0)], [(0.4, 0), (0.4, 1)]],
}


def letter_mask(name, h_px, w_px, stroke_px, shape, cy, cx):
    """uint8 mask (shape) with the letter of height h_px centred at (cy, cx); stroke thickness stroke_px."""
    m = np.zeros(shape, np.uint8)
    wid = max(x for pl in LETTERS[name] for x, _ in pl)
    s = 16  # sub-pixel shift for cv2
    for pl in LETTERS[name]:
        pts = np.array([[(cx + (x - wid / 2) * h_px) * s, (cy + (y - 0.5) * h_px) * s] for x, y in pl], np.int64)
        cv2.polylines(m, [pts.astype(np.int32)], False, 1, thickness=max(1, int(round(stroke_px))), lineType=cv2.LINE_8, shift=4)
    return m.astype(bool)


def sample_diams(rng, n, med, sl, lo, hi):
    d = np.exp(rng.normal(np.log(med), sl, n))
    return np.clip(d, lo, hi)


def pick_sites(m, n, seed, block_lpx):
    rng = np.random.default_rng(seed)
    T, f = m["T"], m["f"]
    H0, W0 = m["LH"] * f, m["LW"] * f
    sites = []
    tries = 0
    while len(sites) < n and tries < 200 * n:
        tries += 1
        r, c = m["tiles"][rng.integers(len(m["tiles"]))]
        ly0, ly1 = cu.level_px_range(m, r * T, min((r + 1) * T, H0))
        lx0, lx1 = cu.level_px_range(m, c * T, min((c + 1) * T, W0))
        if ly1 - ly0 < block_lpx or lx1 - lx0 < block_lpx:
            continue
        by = int(rng.integers(ly0, ly1 - block_lpx + 1))
        bx = int(rng.integers(lx0, lx1 - block_lpx + 1))
        vm = cu.canvas_valid(m, by * f, (by + block_lpx) * f, bx * f, (bx + block_lpx) * f, step=8 * f)
        if vm.mean() >= 0.9:
            sites.append({"tile": [int(r), int(c)], "by": by, "bx": bx, "valid_frac_step8": float(vm.mean())})
    return sites


def read_block(m, by, bx, n, slab):
    rng = cu.slab_range(*slab)
    keys = [(yc, xc) for yc in range(by // CH, (by + n - 1) // CH + 1) for xc in range(bx // CH, (bx + n - 1) // CH + 1)]

    def one(k):
        b = HZ.get(f"{m['url']}/{k[0]}/{k[1]}", rng)
        return k, (None if b is None else np.frombuffer(b, np.uint8).reshape(-1, CH, CH).copy())
    with cf.ThreadPoolExecutor(48) as ex:
        return dict(ex.map(one, keys))


def block_cells(m, chunks, gcache, by, bx, n, P, valid):
    """Same per-px maps and cell statistic as cu.cmd_score, for an n x n level-L block."""
    G = P["grain"]
    A = {k: np.zeros((n, n), np.uint8) for k in ("gv", "nb", "nc")}
    ok = np.zeros((n, n), bool)
    for (yc, xc), a in chunks.items():
        if a is None:
            continue
        if (yc, xc) not in gcache:
            gcache[(yc, xc)] = cu.grain_map(a, m["T_g"], G["min_voxels"], G["max_z_slices"], G.get("max_voxels"))
        maps = gcache[(yc, xc)]
        y0, x0 = yc * CH - by, xc * CH - bx
        a0, b0, a1, b1 = max(0, -y0), max(0, -x0), min(CH, n - y0), min(CH, n - x0)
        for k, arr in zip(("gv", "nb", "nc"), maps[:3]):
            A[k][y0 + a0:y0 + a1, x0 + b0:x0 + b1] = arr[a0:a1, b0:b1]
        ok[y0 + a0:y0 + a1, x0 + b0:x0 + b1] = maps[3][a0:a1, b0:b1]
    A["valid"] = ok & valid
    return cu.stat_cells(cu.px_to_cells(A, m["cell"]), m["cell"], P["detector"])


def plant(m, chunks, by, bx, n, mask_l0, grains, V, P):
    """Return a modified copy of the affected chunks. mask_l0 region coords are native level-0 px of the block
    (level-0 px = level-L px * f). grains: (N, 4) array y_um, x_um, z_um (rel. mesh surface), d_um."""
    I = P["injection"]
    f = m["f"]
    um = m["um_per_slice"]  # native voxel edge (isotropic native grid)
    lo, hi = m["sheet"]
    nzs = hi - lo
    zc = m["centre"] - lo
    ys, xs = np.nonzero(mask_l0)
    pad = 12
    ry0, ry1 = max(0, ys.min() - pad), min(n * f, ys.max() + pad + 1)
    rx0, rx1 = max(0, xs.min() - pad), min(n * f, xs.max() + pad + 1)
    ry0, rx0 = ry0 - ry0 % f, rx0 - rx0 % f
    ry1, rx1 = ry1 + (-ry1) % f, rx1 + (-rx1) % f
    hy, hx = ry1 - ry0, rx1 - rx0
    occ = np.zeros(nzs * hy * hx, np.float64)
    K = 64
    rng = np.random.default_rng(12345)
    u = rng.normal(size=(K, 3))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    u *= rng.random((K, 1)) ** (1 / 3)
    vv = um ** 3
    for s in range(0, len(grains), 20000):
        g = grains[s:s + 20000]
        r = g[:, 3] / 2
        vol = np.pi / 6 * g[:, 3] ** 3
        py = (g[:, 0][:, None] + r[:, None] * u[None, :, 0]) / um - ry0
        px = (g[:, 1][:, None] + r[:, None] * u[None, :, 1]) / um - rx0
        pz = (g[:, 2][:, None] + r[:, None] * u[None, :, 2]) / um + zc + 0.5
        iy, ix, iz = np.floor(py).astype(np.int64), np.floor(px).astype(np.int64), np.floor(pz).astype(np.int64)
        ok = (iy >= 0) & (iy < hy) & (ix >= 0) & (ix < hx) & (iz >= 0) & (iz < nzs)
        w = np.broadcast_to((vol / K / vv)[:, None], iy.shape)
        occ += np.bincount(((iz * hy + iy) * hx + ix)[ok], weights=w[ok], minlength=occ.size)
    occ = np.minimum(occ.reshape(nzs, hy, hx), 1.0)
    occ = ndi.gaussian_filter(occ, I["psf_sigma_vox"] if "psf_sigma_vox" in I else 0.7)
    new = {}
    ly0, lx0 = ry0 // f, rx0 // f
    ly1, lx1 = ry1 // f, rx1 // f
    for (yc, xc), a in chunks.items():
        if a is None:
            continue
        y0, x0 = yc * CH - by, xc * CH - bx
        a0, b0, a1, b1 = max(ly0, y0), max(lx0, x0), min(ly1, y0 + CH), min(lx1, x0 + CH)
        if a0 >= a1 or b0 >= b1:
            continue
        b = a.copy()
        bg = b[:, a0 - y0:a1 - y0, b0 - x0:b1 - x0].astype(np.float64)
        o = occ[:, (a0 - ly0) * f:(a1 - ly0) * f, (b0 - lx0) * f:(b1 - lx0) * f]
        bgu = np.repeat(np.repeat(bg, f, 1), f, 2) if f > 1 else bg
        v = np.clip(bgu + o * (V - bgu), 0, 255)
        if f > 1:
            v = v.reshape(nzs, a1 - a0, f, b1 - b0, f).mean((2, 4))
        v = np.where(bg > 0, np.rint(v), 0)  # no-data voxels stay 0
        b[:, a0 - y0:a1 - y0, b0 - x0:b1 - x0] = v.astype(np.uint8)
        new[(yc, xc)] = b
    return new


def letter_eval(det, maps, lmask_cells):
    best = 0.0
    lab = maps["lab"] if maps is not None else None
    for c in det["clusters"] if lab is not None else []:
        if (lab == c["id"])[lmask_cells].any():
            best = max(best, c["zsum"])
    # clusters beyond the top-5 are not listed; recompute over all labels overlapping the letter
    if lab is not None:
        ids = np.unique(lab[lmask_cells & (lab > 0)])
        D = cu.load_params()["detector"]
        for i in ids:
            cm = lab == i
            ys, xs = np.nonzero(cm)
            ext = max(ys.max() - ys.min() + 1, xs.max() - xs.min() + 1)
            if cm.sum() >= D["min_cells"] and D["ext_min_cells"] <= ext <= D["ext_max_cells"]:
                best = max(best, float(maps["z"][cm].sum()))
    return best


def main():
    name, outp = sys.argv[1], sys.argv[2]
    P = cu.load_params()
    I, D = P["injection"], P["detector"]
    scratch = os.environ.get("CU_SCRATCH", "/tmp/cu_scratch")
    os.makedirs(scratch, exist_ok=True)
    m = cu.load_material(name, scratch, P)
    f, cell = m["f"], m["cell"]
    nb_cells = int(round(I["block_mm"] / m["cell_mm"]))
    n = nb_cells * cell  # level-L px
    seed = I["seed"] + int(hashlib.sha256(name.encode()).hexdigest()[:6], 16)
    sites = pick_sites(m, I["sites_per_material"], seed, n)
    s_from, s_to = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, len(sites))
    done = {d["site"] for d in map(json.loads, open(outp))} if os.path.exists(outp) else set()
    um_l = m["um_per_slice"] * f  # level-L in-plane px (um)
    for si in range(s_from, s_to):
        if si in done or si >= len(sites):
            continue
        t0 = time.time()
        st = sites[si]
        rng = np.random.default_rng(seed * 100 + si)
        by, bx = st["by"], st["bx"]
        chunks = read_block(m, by, bx, n, m["sheet"])
        valid = cu.canvas_valid(m, by * f, (by + n) * f, bx * f, (bx + n) * f, step=f)
        gcache = {}
        g0, cm0 = block_cells(m, chunks, gcache, by, bx, n, P, valid)
        det0, maps0 = cu.detect(g0, cm0, D, return_maps=True)
        letter = I["letters"][int(rng.integers(len(I["letters"])))]
        h_mm = float(rng.uniform(*I["height_mm"]))
        w_mm = float(rng.uniform(*I["stroke_mm"]))
        n0 = n * f  # native level-0 px of the block
        um0 = m["um_per_slice"]
        lm0 = letter_mask(letter, h_mm * 1000 / um0, None, w_mm * 1000 / um0, (n0, n0), n0 / 2, n0 / 2)
        lmL = lm0.reshape(n, f, n, f).any((1, 3)) if f > 1 else lm0
        lmc = cu.to_cells(lmL.astype(np.uint8), np.ones_like(lmL), cell)[0] > 0
        lmc_d = ndi.binary_dilation(lmc, iterations=2)
        area_um2 = float(lm0.sum()) * um0 * um0
        rec = {"material": name, "site": si, **st, "letter": letter, "height_mm": h_mm, "stroke_mm": w_mm,
               "letter_area_mm2": area_um2 / 1e6, "block_px": n, "block_cells": nb_cells,
               "blank": {"score": det0["score"], "n_clusters": det0["n_clusters"],
                         "letter_zone_score": letter_eval(det0, maps0, lmc_d), "g_mean": det0.get("g_mean"),
                         "R_mad_sigma": det0.get("R_mad_sigma")}, "variants": {}}
        ys, xs = np.nonzero(lm0)
        for dk, dv in I["densities"].items():
            t_um = dv["layer_um"]
            target = dv["vol_frac"] * area_um2 * t_um
            gd = I["grain_diam_um"]
            ds = []
            tot = 0.0
            while tot < target:
                d = sample_diams(rng, 20000, dv.get("grain_median_um", gd["median"]), gd["sigma_ln"], gd["clip"][0], t_um)
                cv = np.cumsum(np.pi / 6 * d ** 3) + tot
                k = int(np.searchsorted(cv, target)) + 1
                ds.append(d[:k])
                tot = cv[min(k, len(cv)) - 1]
            d = np.concatenate(ds)
            pick = rng.integers(len(ys), size=len(d))
            gy = (ys[pick] + rng.random(len(d))) * um0
            gx = (xs[pick] + rng.random(len(d))) * um0
            half = np.maximum(t_um / 2 - d / 2, 0)
            gz = rng.uniform(-1, 1, len(d)) * half
            grains = np.stack([gy, gx, gz, d], 1)
            for ck, cvv in I["contrast"].items():
                new = plant(m, chunks, by, bx, n, lm0, grains, cvv["V"], P)
                ch2 = dict(chunks)
                ch2.update(new)
                gc2 = {k: v for k, v in gcache.items() if k not in new}
                g1, cm1 = block_cells(m, ch2, gc2, by, bx, n, P, valid)
                det1, maps1 = cu.detect(g1, cm1, D, return_maps=True)
                rec["variants"][f"{dk}_{ck}"] = {"n_grains": int(len(d)), "grain_d_median_um": float(np.median(d)),
                                                 "score": det1["score"], "letter_score": letter_eval(det1, maps1, lmc_d),
                                                 "n_clusters": det1["n_clusters"],
                                                 "stat_added": float((g1[cm1].sum() - g0[cm0].sum()))}
        rec["secs"] = round(time.time() - t0, 1)
        with open(outp, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(json.dumps({"site": si, "letter": letter, "blank": round(rec["blank"]["score"], 1),
                          "v": {k: round(v["letter_score"], 1) for k, v in rec["variants"].items()}, "secs": rec["secs"]}), flush=True)


if __name__ == "__main__":
    main()
