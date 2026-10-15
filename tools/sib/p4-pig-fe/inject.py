"""p4-pig-fe step 3: injection-recovery of FE-attenuation Greek-capital strokes planted into real CT (numbers only).

Provenance: Project HERCULES | owner the owner | [id removed]

Per location (a 9 x 9 mm patch; the letter at its centre):
  1. fetch the patch at the material's level (fetch slices F), reduce to block maps -> baseline MF response;
  2. for each regime (R = contrast ratio to papyrus) and thickness t: plant the letter as a paint layer on the
     recto side from the mesh plane outward, v' = v + blur(o (V_paint - v)), V_paint = v_air + R (v_pap - v_air),
     o = lateral letter mask x layer occupancy per slice; 3-D Gaussian blur sigma_psf (voxels); only nonzero voxels;
     clip 0..255, round to uint8; reduce and filter as in the strip run;
  3. z = max MF response over bar centres within the letter bounding box dilated by 0.5 mm, / sigma0 (control).
  Detected iff z > theta (the frozen hotspot threshold) [and, reported separately, f_in >= 0.8].
Usage: python inject.py <material> <scratch> <n_locations> <seed> <out.json> <theta> <sigma0>
"""
import concurrent.futures as cf
import json
import os
import sys
import time

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(__file__))
import fe  # noqa: E402
import strip  # noqa: E402

# Greek capitals as polylines in a unit box (x right 0..w, y down 0..1).
GREEK = {
    "A": [[(0, 1), (0.35, 0), (0.7, 1)], [(0.15, 0.6), (0.55, 0.6)]],
    "Delta": [[(0, 1), (0.35, 0), (0.7, 1), (0, 1)]],
    "E": [[(0.6, 0), (0, 0), (0, 1), (0.6, 1)], [(0, 0.5), (0.45, 0.5)]],
    "H": [[(0, 0), (0, 1)], [(0.65, 0), (0.65, 1)], [(0, 0.5), (0.65, 0.5)]],
    "K": [[(0, 0), (0, 1)], [(0.6, 0), (0, 0.55)], [(0.2, 0.4), (0.65, 1)]],
    "Lambda": [[(0, 1), (0.35, 0), (0.7, 1)]],
    "M": [[(0, 1), (0.1, 0), (0.4, 0.7), (0.7, 0), (0.8, 1)]],
    "N": [[(0, 1), (0, 0), (0.65, 1), (0.65, 0)]],
    "Pi": [[(0, 1), (0, 0), (0.65, 0), (0.65, 1)]],
    "Sigma": [[(0.65, 0), (0, 0), (0.35, 0.5), (0, 1), (0.65, 1)]],
    "T": [[(0, 0), (0.7, 0)], [(0.35, 0), (0.35, 1)]],
    "Gamma": [[(0.6, 0), (0, 0), (0, 1)]],
    "Omega": [[(0, 1), (0.25, 1), (0.1, 0.7), (0.1, 0.3), (0.4, 0), (0.7, 0.3), (0.7, 0.7), (0.55, 1), (0.8, 1)]],
    "Xi": [[(0, 0), (0.65, 0)], [(0.1, 0.5), (0.55, 0.5)], [(0, 1), (0.65, 1)]],
    "Z": [[(0, 0), (0.65, 0), (0, 1), (0.65, 1)]],
}


def letter_mask(shape, um_px, letter, h_mm, w_mm, rot_deg, ss=4):
    """Anti-aliased lateral coverage (0..1) of a letter centred in an array of `shape` at um_px per px."""
    H, W = shape
    Hs, Ws = H * ss, W * ss
    img = np.zeros((Hs, Ws), np.uint8)
    hpx = h_mm * 1000 / um_px * ss
    wpx = max(1, int(round(w_mm * 1000 / um_px * ss)))
    th = np.deg2rad(rot_deg)
    Rm = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    pts_all = [np.array(pl, float) for pl in GREEK[letter]]
    allp = np.concatenate(pts_all)
    cxy = (allp.min(0) + allp.max(0)) / 2
    for pl in pts_all:
        p = ((pl - cxy) * hpx) @ Rm.T + np.array([Ws / 2, Hs / 2])
        cv2.polylines(img, [np.round(p).astype(np.int32)], False, 255, thickness=wpx, lineType=cv2.LINE_8)
    return cv2.resize(img.astype(np.float32) / 255.0, (W, H), interpolation=cv2.INTER_AREA)


def occupancy(t_um, um_z, n_slices_side):
    """Layer from the mesh plane (lower face of slice `centre` minus half a voxel) outward: per-slice fraction."""
    o = np.zeros(n_slices_side, np.float32)
    rem = t_um / um_z
    for k in range(n_slices_side):
        o[k] = min(1.0, max(0.0, rem - k))
    return o


def fetch_patch(name, y0, x0, ny, nx, lo, hi):
    """Level-L voxels [lo:hi, y0:y0+ny, x0:x0+nx] (chunk-aligned origin), missing chunks as 0."""
    out = np.zeros((hi - lo, ny, nx), np.uint8)
    url = fe.url_chunks(name)
    jobs = [(yc, xc) for yc in range(y0 // fe.CH, (y0 + ny - 1) // fe.CH + 1)
            for xc in range(x0 // fe.CH, (x0 + nx - 1) // fe.CH + 1)]

    def one(yx):
        b = fe.get(f"{url}/{yx[0]}/{yx[1]}", (lo * fe.PLANE, hi * fe.PLANE - 1))
        return yx, b

    with cf.ThreadPoolExecutor(48) as ex:
        for (yc, xc), b in ex.map(one, jobs):
            if b is None:
                continue
            a = np.frombuffer(b, np.uint8).reshape(hi - lo, fe.CH, fe.CH)
            ys, xs = yc * fe.CH - y0, xc * fe.CH - x0
            out[:, ys:ys + fe.CH, xs:xs + fe.CH] = a
    return out


def reduce_patch(vol, mesh, B_lo, B_hi, bd, blk, base=None, region=None):
    """Block maps of a patch. With base=(E, S, D, V) and region=(y0, y1, x0, x1), only chunks overlapping the
    region are recomputed (the rest is copied from base)."""
    nF, ny, nx = vol.shape
    if base is None:
        E = np.zeros((ny // blk, nx // blk), np.float32); S = np.zeros_like(E); D = np.zeros_like(E); V = np.zeros_like(E)
        ycs, xcs = range(ny // fe.CH), range(nx // fe.CH)
    else:
        E, S, D, V = (b.copy() for b in base)
        y0, y1, x0, x1 = region
        ycs, xcs = range(y0 // fe.CH, (y1 - 1) // fe.CH + 1), range(x0 // fe.CH, (x1 - 1) // fe.CH + 1)
    for yc in ycs:
        for xc in xcs:
            sl = (slice(yc * fe.CH, yc * fe.CH + fe.CH), slice(xc * fe.CH, xc * fe.CH + fe.CH))
            m = mesh[sl] if mesh is not None else None
            r = fe.reduce_chunk(vol[:, sl[0], sl[1]], B_lo, B_hi, bd, blk, m)
            nb = fe.CH // blk
            bs = (slice(yc * nb, yc * nb + nb), slice(xc * nb, xc * nb + nb))
            E[bs], S[bs], D[bs], V[bs] = r
    return E, S, D, V


def window_stats(E, S, D, V, ker, win, sigma0):
    resp, arg = fe.mf_response(E, V, ker)
    w = resp[win]
    if not np.isfinite(w).any():
        return None
    k = int(np.nanargmax(w))
    iy, ix = np.unravel_index(k, w.shape)
    cy, cx = win[0].start + iy, win[1].start + ix
    ang, bar, fl = ker[arg[cy, cx]]
    R = bar.shape[0] // 2
    ys, xs = np.nonzero(bar)
    ys, xs = ys + cy - R, xs + cx - R
    ok = (ys >= 0) & (ys < E.shape[0]) & (xs >= 0) & (xs < E.shape[1])
    ys, xs = ys[ok], xs[ok]
    vv = max(V[ys, xs].sum(), 1)
    ms, md = S[ys, xs].sum() / vv, D[ys, xs].sum() / vv
    return {"z": float(w[iy, ix] / sigma0), "f_in": float(ms / (ms + md)) if ms + md > 0 else None}


def main(name, scr, nloc, seed, outp, theta, sigma0):
    P = fe.load_params()
    m = fe.MAT[name]
    fam = P["families"][m["family"]]
    bd = {k: tuple(v) for k, v in fam["bands"].items()}
    lo, hi = bd["F"]
    c = m["centre"]
    inj = P["injection"]
    mfp = P["detector"]["matched_filter"]
    blk = m["blk"]
    blk_um = m["um_xy"] * blk
    ker = fe.bar_kernels(blk_um, mfp["bar_width_mm"], mfp["bar_length_mm"], mfp["flank_width_mm"])
    g = strip.geometry(name, scr, P)
    mesh_full = np.load(g["mesh"], mmap_mode="r") if g["mesh"] else None
    side_um = inj["patch_mm"] * 1000
    npx = int(np.ceil(side_um / m["um_xy"] / fe.CH)) * fe.CH
    rng = np.random.default_rng(seed)
    T, s = g["T"], g["scale"]
    tiles = list(g["tiles"])
    res = {"provenance": fe.PROV, "material": name, "seed": seed, "theta": theta, "sigma0": sigma0, "locations": []}
    tried = 0
    while len(res["locations"]) < nloc and tried < 50 * nloc:
        tried += 1
        r, cc = tiles[rng.integers(len(tiles))]
        # chunk-aligned patch origin inside the tile (level-L px)
        ty0, tx0 = r * T // s, cc * T // s
        span = T // s - npx
        y0 = (ty0 + int(rng.integers(0, max(span, 1)))) // fe.CH * fe.CH
        x0 = (tx0 + int(rng.integers(0, max(span, 1)))) // fe.CH * fe.CH
        letter = list(GREEK)[rng.integers(len(GREEK))]
        h_mm = float(rng.uniform(*inj["height_mm"]))
        w_mm = float(rng.uniform(*inj["stroke_mm"]))
        rot = float(rng.choice([0, 90, 180, 270]) + rng.uniform(-10, 10))
        # mesh-valid check from the mask only (no CT): >= 90 % of the patch
        if mesh_full is not None:
            ys = y0 + np.arange(npx)
            xs = x0 + np.arange(npx)
            mesh = np.asarray(mesh_full[np.minimum(ys // 10, mesh_full.shape[0] - 1)][:, np.minimum(xs // 10, mesh_full.shape[1] - 1)])
            mesh &= (ys < g["H"])[:, None] & (xs < g["W"])[None, :]
            if mesh.mean() < 0.9:
                continue
        else:
            mesh = None
        vol = fetch_patch(name, y0, x0, npx, npx, lo, hi)
        nzf = float((vol > 0).all(0).mean())
        if nzf < 0.9:      # E2/C2 validity (surface volume masked to the mesh); also scan coverage for E1/C
            continue
        lm = letter_mask((npx, npx), m["um_xy"], letter, h_mm, w_mm, rot)
        yy, xx = np.nonzero(lm > 0.01)
        dil = int(np.ceil(500 / blk_um))
        win = (slice(max(yy.min() // blk - dil, 0), min(yy.max() // blk + dil + 1, npx // blk)),
               slice(max(xx.min() // blk - dil, 0), min(xx.max() // blk + dil + 1, npx // blk)))
        base_maps = reduce_patch(vol, mesh, fam["B_lo"], fam["B_hi"], bd, blk)
        base = window_stats(*base_maps, ker, win, sigma0)
        rot90 = None
        loc = {"tile": [int(r), int(cc)], "origin_level_px": [int(y0), int(x0)], "patch_px": npx, "letter": letter,
               "height_mm": h_mm, "stroke_mm": w_mm, "rot_deg": rot, "valid_nonzero_frac": nzf, "baseline": base,
               "planted": []}
        # region to modify: letter bbox + 4 sigma margin
        mg = 12
        py0, py1 = max(yy.min() - mg, 0), min(yy.max() + mg + 1, npx)
        px0, px1 = max(xx.min() - mg, 0), min(xx.max() + mg + 1, npx)
        sub = vol[:, py0:py1, px0:px1].astype(np.float32)
        lat = lm[py0:py1, px0:px1]
        nz = sub > 0
        for reg in inj["regimes"]:
            Vp = fam["v_air"] + reg["R"] * (fam["v_pap"] - fam["v_air"])
            for t_um in inj["thickness_um"]:
                occ = np.zeros(hi - lo, np.float32)
                o = occupancy(t_um, m["um_z"], hi - c)
                occ[c - lo:] = o
                O = occ[:, None, None] * lat[None]
                dlt = O * (Vp - sub)
                sp = inj["psf_sigma_vox"]
                dlt = gaussian_filter(dlt, sigma=(sp, sp * m["um_z"] / m["um_xy"], sp * m["um_z"] / m["um_xy"]))
                new = np.where(nz, np.clip(np.rint(sub + dlt), 1, 255), 0).astype(np.uint8)
                cy0, cx0 = py0 // fe.CH * fe.CH, px0 // fe.CH * fe.CH
                cy1, cx1 = -(-py1 // fe.CH) * fe.CH, -(-px1 // fe.CH) * fe.CH
                v2 = vol[:, cy0:cy1, cx0:cx1].copy()
                v2[:, py0 - cy0:py1 - cy0, px0 - cx0:px1 - cx0] = new
                mp_ = None if mesh is None else mesh[cy0:cy1, cx0:cx1]
                loc_maps = reduce_patch(v2, mp_, fam["B_lo"], fam["B_hi"], bd, blk)
                nb = blk
                E2_, S2_, D2_, V2_ = (b.copy() for b in base_maps)
                bsl = (slice(cy0 // nb, cy1 // nb), slice(cx0 // nb, cx1 // nb))
                for dst, src in zip((E2_, S2_, D2_, V2_), loc_maps):
                    dst[bsl] = src
                st = window_stats(E2_, S2_, D2_, V2_, ker, win, sigma0)
                st.update({"regime": reg["name"], "R": reg["R"], "t_um": t_um,
                           "detected": bool(st["z"] > theta),
                           "detected_and_in_sheet": bool(st["z"] > theta and (st["f_in"] or 0) >= 0.8)})
                loc["planted"].append(st)
                del v2
        res["locations"].append(loc)
        print(name, len(res["locations"]), letter, round(h_mm, 2), round(w_mm, 2), "base z",
              None if base is None else round(base["z"], 2),
              [(p["regime"][:3], p["t_um"], round(p["z"], 1)) for p in loc["planted"]], flush=True)
        json.dump(res, open(outp, "w"), indent=1)
    res["tried"] = tried
    json.dump(res, open(outp, "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], int(a[3]), int(a[4]), a[5], float(a[6]), float(a[7]))
