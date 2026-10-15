"""p4-pig-fe: full-coverage block maps and tile scores for one material (numbers only).

Provenance: Project HERCULES | owner the owner | [id removed]

  python strip.py maps  <material> <scratch> [rows]   -> <scratch>/maps_<material>.npz (block sums E, S, D, V)
  python strip.py score <material> <scratch> <out.json> [--sigma0 X]

Material geometry, eligibility and bands: logs/sib/p4-pig-fe/params.json (frozen before any title-strip number).
"""
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import fe  # noqa: E402

P = None
G = {}


def geometry(name, scr, P):
    """Canvas/level geometry, eligible tiles and the chunk list at the material's level."""
    m = fe.MAT[name]
    pm = P["materials"][name]
    za = json.loads(fe.get(fe.url_level(name) + "/.zarray"))
    _, H, W = za["shape"]
    g = {"name": name, "H": H, "W": W, "blk": m["blk"], "scale": 2 ** m["level"] if m["family"] == "24" else 1}
    if m["family"] == "1129":
        import hz_common as hz
        mat = hz.load_material(name, scr)
        g["T"] = mat["T"]
        g["tiles"] = [(t["r"], t["c"]) for t in mat["tiles"]]
        g["mesh"] = os.path.join(scr, f"valid_{name}.npy")
        g["mesh_inputs"] = mat["mesh_inputs"]
    else:
        g["T"] = pm["T_canvas_px"]
        g["mesh"] = None
        if pm.get("eligible_from"):
            man = json.loads(fe.git_show(pm["eligible_from"]["ref"], pm["eligible_from"]["path"]))
            g["tiles"] = [(t["r"], t["c"]) for t in man["tiles"]]
        else:
            nr, nc = -(-H * g["scale"] // g["T"]), -(-W * g["scale"] // g["T"])
            g["tiles"] = [(r, c) for r in range(nr) for c in range(nc)]   # eligibility decided from V afterwards
    s, T = g["scale"], g["T"]
    ch = set()
    for r, c in g["tiles"]:
        y0, y1 = r * T // s, min(-(-(r + 1) * T // s), H)
        x0, x1 = c * T // s, min(-(-(c + 1) * T // s), W)
        for yc in range(y0 // fe.CH, (y1 - 1) // fe.CH + 1):
            for xc in range(x0 // fe.CH, (x1 - 1) // fe.CH + 1):
                ch.add((yc, xc))
    g["chunks"] = sorted(ch)
    return g


def _one(yx):
    yc, xc = yx
    bd, lo, hi = G["bd"], G["bd"]["F"][0], G["bd"]["F"][1]
    b = fe.get(f"{G['url']}/{yc}/{xc}", (lo * fe.PLANE, hi * fe.PLANE - 1))
    if b is None:
        return yc, xc, None
    a = np.frombuffer(b, np.uint8).reshape(hi - lo, fe.CH, fe.CH)
    mesh = None
    if G["mesh"] is not None:
        ys = yc * fe.CH + np.arange(fe.CH)
        xs = xc * fe.CH + np.arange(fe.CH)
        v = G["mesh"]
        mesh = np.asarray(v[np.minimum(ys // 10, v.shape[0] - 1)][:, np.minimum(xs // 10, v.shape[1] - 1)])
        mesh = mesh & (ys < G["H"])[:, None] & (xs < G["W"])[None, :]
    return yc, xc, fe.reduce_chunk(a, G["B_lo"], G["B_hi"], bd, G["blk"], mesh)


def _init(name, meshp, B_lo, B_hi, bd, blk, H, W):
    G.update(url=fe.url_chunks(name), mesh=np.load(meshp, mmap_mode="r") if meshp else None, B_lo=B_lo, B_hi=B_hi,
             bd=bd, blk=blk, H=H, W=W)


def _batch(items):
    with cf.ThreadPoolExecutor(32) as ex:
        return [r for r in ex.map(_one, items)]


def maps(name, scr, rows=None):
    P = fe.load_params()
    g = geometry(name, scr, P)
    fam = P["families"][fe.MAT[name]["family"]]
    bd = {k: tuple(v) for k, v in fam["bands"].items()}
    chunks = g["chunks"]
    if rows is not None:
        T, s = g["T"], g["scale"]
        keep = set()
        for r, c in g["tiles"]:
            if r in rows:
                y0, y1 = r * T // s, min(-(-(r + 1) * T // s), g["H"])
                keep.update(range(y0 // fe.CH, (y1 - 1) // fe.CH + 1))
        chunks = [yx for yx in chunks if yx[0] in keep]
    nb = fe.CH // g["blk"]
    ny, nx = -(-g["H"] // fe.CH) * nb, -(-g["W"] // fe.CH) * nb
    E = np.zeros((ny, nx), np.float32); S = np.zeros_like(E); D = np.zeros_like(E); V = np.zeros_like(E)
    t0, n404, done = time.time(), 0, 0
    batches = [chunks[i:i + 512] for i in range(0, len(chunks), 512)]
    with mp.Pool(4, _init, (name, g["mesh"], fam["B_lo"], fam["B_hi"], bd, g["blk"], g["H"], g["W"])) as p:
        for res in p.imap_unordered(_batch, batches):
            for yc, xc, r in res:
                done += 1
                if r is None:
                    n404 += 1
                    continue
                sl = (slice(yc * nb, yc * nb + nb), slice(xc * nb, xc * nb + nb))
                E[sl], S[sl], D[sl], V[sl] = r
            if done % 20480 < 512:
                print(f"{name} {done}/{len(chunks)} 404={n404} {time.time() - t0:.0f}s", flush=True)
    meta = {"material": name, "chunks": len(chunks), "absent_404": n404, "secs": round(time.time() - t0, 1),
            "T": g["T"], "scale": g["scale"], "blk": g["blk"], "tiles": g["tiles"], "rows": rows,
            "B_lo": fam["B_lo"], "B_hi": fam["B_hi"], "bands": bd, "mesh_inputs": g.get("mesh_inputs")}
    tag = name if rows is None else f"{name}_r" + "-".join(map(str, rows))
    np.savez(os.path.join(scr, f"maps_{tag}.npz"), E=E, S=S, D=D, V=V, meta=json.dumps(meta))
    print(json.dumps(meta)[:400], flush=True)
    return meta


def tile_block_range(r, T, scale, blk_l0):
    """Block index range [a, b) whose centre (L0 canvas) lies in [r T, (r+1) T)."""
    a = int(np.ceil((r * T - blk_l0 / 2) / blk_l0))
    b = int(np.ceil(((r + 1) * T - blk_l0 / 2) / blk_l0))
    return max(a, 0), b


def score_tiles(M, meta, P, sigma0=None, only=None):
    """Per tile: max z of the matched filter (and rot-90), argmax, in-sheet fraction at argmax."""
    name = meta["material"]
    fam = P["families"][fe.MAT[name]["family"]]
    mfp = P["detector"]["matched_filter"]
    blk_um = fe.MAT[name]["um_xy"] * meta["blk"]
    ker = fe.bar_kernels(blk_um, mfp["bar_width_mm"], mfp["bar_length_mm"], mfp["flank_width_mm"])
    blk_l0 = meta["blk"] * meta["scale"]
    T = meta["T"]
    marg = int(np.ceil(mfp["margin_mm"] * 1000 / blk_um))
    E, S, D, V = M["E"], M["S"], M["D"], M["V"]
    out = []
    allr = []
    tiles = [tuple(t) for t in meta["tiles"]]
    for (r, c) in tiles:
        if only is not None and (r, c) not in only:
            continue
        a0, a1 = tile_block_range(r, T, 1, blk_l0)
        b0, b1 = tile_block_range(c, T, 1, blk_l0)
        a1, b1 = min(a1, E.shape[0]), min(b1, E.shape[1])
        y0, y1, x0, x1 = max(a0 - marg, 0), min(a1 + marg, E.shape[0]), max(b0 - marg, 0), min(b1 + marg, E.shape[1])
        sub = lambda A: A[y0:y1, x0:x1]
        e, v = sub(E), sub(V)
        inner = (slice(a0 - y0, a1 - y0), slice(b0 - x0, b1 - x0))
        nblk_px = meta["blk"] ** 2
        vfrac = float((V[a0:a1, b0:b1] >= 0.5 * nblk_px).mean()) if (a1 > a0 and b1 > b0) else 0.0
        rec = {"r": r, "c": c, "valid_block_frac": vfrac}
        if vfrac < P["eligibility"]["min_valid_block_frac"]:
            rec["eligible"] = False
            out.append(rec)
            continue
        rec["eligible"] = True
        resp, arg = fe.mf_response(e, v, ker)
        ri = resp[inner]
        fin = ri[np.isfinite(ri)]
        allr.append(fin)
        rot, _ = fe.mf_response(np.rot90(e).copy(), np.rot90(v).copy(), ker)
        rot_i = np.rot90(rot, -1)[inner]
        if fin.size == 0:
            rec["eligible"] = False
            out.append(rec)
            continue
        k = int(np.nanargmax(ri))
        iy, ix = np.unravel_index(k, ri.shape)
        rec.update({"r_max": float(ri[iy, ix]), "r_rot90_max": float(np.nanmax(rot_i)),
                    "argmax_block": [int(a0 + iy), int(b0 + ix)], "orientation_deg": int(ker[arg[inner][iy, ix]][0]),
                    "n_positions": int(fin.size)})
        # in-sheet fraction at argmax: bar footprint means of S and D excess
        ang, bar, fl = ker[arg[inner][iy, ix]]
        R = bar.shape[0] // 2
        cy, cx = a0 - y0 + iy, b0 - x0 + ix
        ys, xs = np.nonzero(bar)
        ys, xs = ys + cy - R, xs + cx - R
        okk = (ys >= 0) & (ys < e.shape[0]) & (xs >= 0) & (xs < e.shape[1])
        ys, xs = ys[okk], xs[okk]
        vv = sub(V)[ys, xs].sum()
        ms, md = sub(S)[ys, xs].sum() / max(vv, 1), sub(D)[ys, xs].sum() / max(vv, 1)
        rec["mean_S_excess_bar"], rec["mean_D_excess_bar"] = float(ms), float(md)
        rec["f_in"] = float(ms / (ms + md)) if (ms + md) > 0 else None
        out.append(rec)
    allr = np.concatenate(allr) if allr else np.zeros(0)
    return out, allr


def score(name, scr, outp, sigma0=None, mapsfile=None):
    P = fe.load_params()
    Z = np.load(mapsfile or os.path.join(scr, f"maps_{name}.npz"))
    meta = json.loads(str(Z["meta"]))
    M = {k: Z[k] for k in "ESDV"}
    recs, allr = score_tiles(M, meta, P)
    res = {"provenance": fe.PROV, "material": name, "maps_meta": meta, "n_positions": int(allr.size)}
    if sigma0 is None:
        med = float(np.median(allr))
        sigma0 = float(1.4826 * np.median(np.abs(allr - med)))
        res["r_median"] = med
        res["sigma0_rule"] = "1.4826 * MAD of r over all valid positions of eligible tiles of this (control) material"
    res["sigma0"] = sigma0
    for t in recs:
        if t.get("eligible") and "r_max" in t:
            t["z"] = t["r_max"] / sigma0
            t["z_rot90"] = t["r_rot90_max"] / sigma0
    res["tiles"] = recs
    json.dump(res, open(outp, "w"), indent=1)
    return res


if __name__ == "__main__":
    cmd, name, scr = sys.argv[1:4]
    if cmd == "maps":
        rows = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
        maps(name, scr, rows)
    elif cmd == "score":
        s0 = None
        if "--sigma0" in sys.argv:
            s0 = float(sys.argv[sys.argv.index("--sigma0") + 1])
        mf = None
        if "--maps" in sys.argv:
            mf = sys.argv[sys.argv.index("--maps") + 1]
        score(name, scr, sys.argv[4], s0, mf)
