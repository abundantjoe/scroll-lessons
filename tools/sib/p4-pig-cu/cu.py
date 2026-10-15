"""p4-pig-cu: CU-family (Egyptian blue / Cu-relic) GRAIN-statistics detector (RULES.md DECL-P4-10 items 2-4).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: CT bytes are reduced to per-pixel grain-voxel counts, per-cell sums and cluster statistics; nothing is
displayed, rendered or printed as an image. All parameters are read from logs/sib/p4-pig-cu/params.json (frozen before
any title-strip number).

Pipeline per tile (identical code path for tiles, injection blocks and nulls):
 1. Read the sheet slab (mesh surface +-20 um) of every chunk of the tile (one HTTP range per chunk).
 2. Bright voxels: v > T_g (material threshold). 3-D 26-connected components per chunk; a component is a GRAIN (or thin
    grain layer) if it has >= min_voxels voxels and its z-extent is <= max_z_slices (thicker bodies are 3-D inclusions,
    not a pen-stroke pigment layer). Per px: number of grain voxels.
 3. Cells of ~0.1 mm: grain-voxel sum G and valid-px count NV; g = G * cell_area / NV at cells with NV >= 50 % of area.
 4. detect(): stroke-scale mean S (k x k cells, normalised convolution), local background B = median filter (bg x bg
    cells), residual R = S - B, per-cell sigma = max(1.4826 MAD(R), sqrt(max(B,1)/k^2)), z = R / sigma.
    Clusters: 8-connected cells with z > z_c; kept if n >= min_cells and bbox extent in [ext_min, ext_max] cells
    (0.5-5 mm, letter scale). Cluster score = sum of z over its cells. Tile score = max cluster score (0 if none).
 5. Nulls: rot-90 (np.rot90 of g and mask; isotropic detector, so equal by construction; computed as a check) and a
    cell-permutation null (g permuted among valid cells, seeded per tile).
Usage:
  python cu.py score <MAT> <rows e.g. 0-2> <out_dir>      # MAT in C1 E1 C2 E2
  python cu.py onsheet <MAT> <scores_dir> <thr> <out.jsonl>
"""
import concurrent.futures as cf
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
import zlib

import numpy as np
import requests
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hz_common as HZ  # noqa: E402  (p4-highz fetch helpers, copied verbatim)

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PARAMS_PATH = os.path.join(REPO, "logs/sib/p4-pig-cu/params.json")
BUCKET = HZ.BUCKET
CH = 128


def load_params():
    return json.load(open(PARAMS_PATH))


# ----------------------------------------------------------------------------------------------------- materials
def git_json(ref, path):
    import subprocess
    return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{ref}:{path}"]))


def fetch_mesh_valid(seg_mesh_key, scratch, tag):
    """Mesh-valid vertex mask (x, y, z != -1 and finite); tifs fetched, hashed, reduced, deleted."""
    import tifffile
    vpath = os.path.join(scratch, f"valid_{tag}.npy")
    if os.path.exists(vpath):
        return np.load(vpath), json.load(open(vpath + ".json"))
    arrs, inputs = [], []
    for a in "xyz":
        key = f"{seg_mesh_key}/{a}.tif"
        b = HZ.get(f"{BUCKET}/{key}")
        inputs.append({"key": key, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
        p = os.path.join(scratch, f"mesh_{tag}_{a}.tif")
        open(p, "wb").write(b)
        del b
        x = tifffile.imread(p)
        arrs.append((x != -1) & np.isfinite(x))
        del x
        os.remove(p)
    valid = arrs[0] & arrs[1] & arrs[2]
    np.save(vpath, valid)
    json.dump(inputs, open(vpath + ".json", "w"))
    return valid, inputs


def load_material(name, scratch, P=None):
    P = P or load_params()
    m = dict(P["materials"][name])
    m["name"] = name
    f = 2 ** m["level"]
    m["f"] = f
    m["url"] = f"{BUCKET}/{m['sv_key']}/{m['level']}/0"
    za = requests.get(f"{BUCKET}/{m['sv_key']}/{m['level']}/.zarray", timeout=60).json()
    assert za["chunks"] == [m["nz"], CH, CH] and za["dtype"] == "|u1" and za["compressor"] is None, za
    m["LH"], m["LW"] = za["shape"][1:]
    valid, inputs = fetch_mesh_valid(m["mesh_key"], scratch, name)
    m["valid"], m["mesh_inputs"] = valid, inputs
    g = m["grid"]
    if g.get("ref"):
        grid = git_json(g["ref"], g["grid"])
        man = git_json(g["ref"], g["manifest"])
        T = int(grid.get("T_px") or grid.get("T_canvas_px"))
        tiles = []
        for t in man["tiles"]:
            vf = t["valid_fraction"]
            if vf < 0.5:
                continue
            if g.get("coverage"):
                fo = (t.get("stats") or {}).get("frac_mesh_points_outside_1129_volume", t.get("frac_outside"))
                if fo is None or fo >= 0.5:
                    continue
            tiles.append((int(t["r"]), int(t["c"])))
        m["grid_sha"] = {"grid": hashlib.sha256(json.dumps(grid, sort_keys=True).encode()).hexdigest(),
                         "manifest": hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest()}
    else:  # grid built here (C2): T from origin (0,0), eligible >= 50 % mesh-valid
        T = int(g["T"])
        H0, W0 = m["LH"] * f, m["LW"] * f
        nr, nc = -(-H0 // T), -(-W0 // T)
        tiles = []
        for r in range(nr):
            for c in range(nc):
                vm = canvas_valid(m, r * T, min((r + 1) * T, H0), c * T, min((c + 1) * T, W0))
                if vm.sum() / float(T * T) >= 0.5:
                    tiles.append((r, c))
    m["T"] = T
    m["tiles"] = sorted(tiles)
    return m


def canvas_valid(m, y0, y1, x0, x1, step=1):
    """Mesh-valid mask for canvas px rows [y0,y1), cols [x0,x1) (every `step` px): px -> vertex (px // mesh_div)."""
    v = m["valid"]
    ys = np.arange(y0, y1, step)
    xs = np.arange(x0, x1, step)
    gy = ys // m["mesh_div"]
    gx = xs // m["mesh_div"]
    iy = (gy >= 0) & (gy < v.shape[0])
    ix = (gx >= 0) & (gx < v.shape[1])
    out = v[np.clip(gy, 0, v.shape[0] - 1)][:, np.clip(gx, 0, v.shape[1] - 1)]
    return out & iy[:, None] & ix[None, :]


def level_px_range(m, a0, a1):
    """Level-L px indices whose canvas px (f*i) lies in [a0, a1)."""
    f = m["f"]
    return -(-a0 // f), -(-a1 // f)


# ----------------------------------------------------------------------------------------------------- grains
_STRUCT = np.ones((3, 3, 3), bool)


def grain_map(a, Tg, min_vox, max_z, max_vox=None):
    """a: (nz, h, w) uint8 slab. Returns per-px uint8 maps: grain voxels, bright voxels, grain count (component
    centroids, 1 per grain) and the data mask (bool). Grain = 26-connected component of voxels > Tg with
    min_vox <= size (<= max_vox if given) and z-extent <= max_z."""
    data = (a > 0).any(0)
    br = a > Tg
    nb = br.sum(0).astype(np.uint8)
    z2 = np.zeros(a.shape[1:], np.uint8)
    if not br.any():
        return z2, nb, z2.copy(), data
    lab, n = ndi.label(br, structure=_STRUCT)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    objs = ndi.find_objects(lab)
    zext = np.array([0] + [s[0].stop - s[0].start for s in objs])
    keep = (sizes >= min_vox) & (zext <= max_z)
    if max_vox:
        keep &= sizes <= max_vox
    keep[0] = False
    gv = keep[lab].sum(0).astype(np.uint8)
    ids = np.nonzero(keep)[0]
    nc = z2.copy()
    if ids.size:
        cy = np.array([(objs[i - 1][1].start + objs[i - 1][1].stop - 1) // 2 for i in ids])
        cx = np.array([(objs[i - 1][2].start + objs[i - 1][2].stop - 1) // 2 for i in ids])
        np.add.at(nc, (cy, cx), 1)
    return gv, nb, nc, data


# worker globals
_W = {}


def _winit(url, rng, nz, Tg, min_vox, max_z, max_vox=None):
    _W.update(url=url, rng=rng, nz=nz, Tg=Tg, min_vox=min_vox, max_z=max_z, max_vox=max_vox)


def _one(yx):
    yc, xc = yx
    b = HZ.get(f"{_W['url']}/{yc}/{xc}", _W["rng"])
    if b is None:
        return yc, xc, None
    a = np.frombuffer(b, np.uint8).reshape(-1, CH, CH)
    gv, nb, nc, data = grain_map(a, _W["Tg"], _W["min_vox"], _W["max_z"], _W.get("max_vox"))
    return yc, xc, (gv.tobytes(), nb.tobytes(), nc.tobytes(), np.packbits(data).tobytes())


def _work(items):
    with cf.ThreadPoolExecutor(12) as ex:
        return list(ex.map(_one, items))


def slab_range(lo, hi):
    return (lo * CH * CH, hi * CH * CH - 1)


# ----------------------------------------------------------------------------------------------------- cells
def region_arrays(m, pool, ly0, ly1, lx0, lx1, slab, nproc):
    """Per-px maps for level-L px rows [ly0,ly1), cols [lx0,lx1) using slab (lo, hi): dict gv, nb, nc (uint8) and
    valid (data present AND mesh-valid), plus chunk counts."""
    h, w = ly1 - ly0, lx1 - lx0
    A = {k: np.zeros((h, w), np.uint8) for k in ("gv", "nb", "nc")}
    ok = np.zeros((h, w), bool)
    chunks = [(yc, xc) for yc in range(max(ly0, 0) // CH, (min(ly1, m["LH"]) - 1) // CH + 1)
              for xc in range(max(lx0, 0) // CH, (min(lx1, m["LW"]) - 1) // CH + 1)]
    parts = [chunks[i::nproc * 4] for i in range(nproc * 4)]
    res = [x for part in pool.map(_work, parts) for x in part]
    n_abs = 0
    for yc, xc, d in res:
        if d is None:
            n_abs += 1
            continue
        y0, x0 = yc * CH - ly0, xc * CH - lx0
        a0, b0 = max(0, -y0), max(0, -x0)
        a1, b1 = min(CH, h - y0), min(CH, w - x0)
        for k, bts in zip(("gv", "nb", "nc"), d[:3]):
            A[k][y0 + a0:y0 + a1, x0 + b0:x0 + b1] = np.frombuffer(bts, np.uint8).reshape(CH, CH)[a0:a1, b0:b1]
        o_ = np.unpackbits(np.frombuffer(d[3], np.uint8))[:CH * CH].reshape(CH, CH).astype(bool)
        ok[y0 + a0:y0 + a1, x0 + b0:x0 + b1] = o_[a0:a1, b0:b1]
    f = m["f"]
    mv = canvas_valid(m, ly0 * f, ly1 * f, lx0 * f, lx1 * f, step=f)
    A["valid"] = ok & mv
    return A, len(chunks), n_abs


def px_to_cells(A, cell):
    """Cell sums: G grain voxels, FP grain-footprint px, NC grain count, NB bright voxels, NV valid px."""
    v = A["valid"]
    G, NV = to_cells(A["gv"], v, cell)
    FP, _ = to_cells((A["gv"] > 0).astype(np.uint8), v, cell)
    NC, _ = to_cells(A["nc"], v, cell)
    NB, _ = to_cells(A["nb"], v, cell)
    return {"G": G, "FP": FP, "NC": NC, "NB": NB, "NV": NV}


def stat_cells(Cd, cell, D):
    """The frozen per-cell statistic (D['statistic'] names the cell array) normalised to full-cell area."""
    if D["statistic"] == "OCC":
        g, m = cell_density(Cd["NC"], Cd["NV"], cell)
        return (Cd["NC"] > 0).astype(np.float64) * m, m
    return cell_density(Cd[D["statistic"]], Cd["NV"], cell)


def to_cells(arr, valid, cell):
    h, w = arr.shape
    H, W = -(-h // cell) * cell, -(-w // cell) * cell
    a = np.zeros((H, W), np.int64)
    v = np.zeros((H, W), np.int64)
    a[:h, :w] = np.where(valid, arr, 0)
    v[:h, :w] = valid
    sh = (H // cell, cell, W // cell, cell)
    return a.reshape(sh).sum((1, 3)), v.reshape(sh).sum((1, 3))


def cell_density(G, NV, cell, frac=0.5):
    m = NV >= frac * cell * cell
    g = np.where(m, G * (cell * cell) / np.maximum(NV, 1), 0.0)
    return g, m


# ----------------------------------------------------------------------------------------------------- detector
def detect(g, m, D, return_maps=False):
    k, bg, zc = D["smooth_cells"], D["bg_cells"], D["z_c"]
    gf = np.where(m, g, 0.0).astype(np.float64)
    mf = m.astype(np.float64)
    num = ndi.uniform_filter(gf, k, mode="constant") * k * k
    den = ndi.uniform_filter(mf, k, mode="constant") * k * k
    sv = m & (den >= 0.5 * k * k)
    out = {"valid_cells": int(m.sum()), "scored_cells": int(sv.sum()), "score": 0.0, "n_clusters": 0, "clusters": []}
    if sv.sum() < D["min_scored_cells"]:
        out["note"] = "too few scored cells"
        return (out, None) if return_maps else out
    S = np.where(sv, num / np.maximum(den, 1e-9), 0.0)
    fill = float(np.median(S[sv]))
    B = ndi.median_filter(np.where(sv, S, fill), size=bg, mode="reflect")
    R = S - B
    r = R[sv]
    mad = 1.4826 * float(np.median(np.abs(r - np.median(r))))
    sig = np.maximum(mad, np.sqrt(np.maximum(B, D.get("sigma_floor_min", 1.0)) / (k * k)))
    z = np.where(sv, R / sig, 0.0)
    hot = z > zc
    lab, n = ndi.label(hot, structure=np.ones((3, 3), bool))
    out.update({"S_median": fill, "R_mad_sigma": mad, "g_mean": float(g[m].mean()), "z_max": float(z[sv].max())})
    cl = []
    if n:
        objs = ndi.find_objects(lab)
        idx = np.arange(1, n + 1)
        ncell = ndi.sum(np.ones_like(z), lab, idx)
        zsum = ndi.sum(z, lab, idx)
        exc = ndi.sum(R, lab, idx)
        for i, s in enumerate(objs):
            ext = max(s[0].stop - s[0].start, s[1].stop - s[1].start)
            if ncell[i] >= D["min_cells"] and D["ext_min_cells"] <= ext <= D["ext_max_cells"]:
                cl.append({"id": int(i + 1), "n_cells": int(ncell[i]), "zsum": float(zsum[i]), "excess_grain_vox": float(exc[i]),
                           "bbox": [int(s[0].start), int(s[0].stop), int(s[1].start), int(s[1].stop)], "extent_cells": int(ext)})
    cl.sort(key=lambda c: -c["zsum"])
    out["n_clusters"] = len(cl)
    out["clusters"] = cl[:5]
    out["score"] = cl[0]["zsum"] if cl else 0.0
    if return_maps:
        return out, {"lab": lab, "z": z, "R": R, "sv": sv, "B": B}
    return out


def tile_seed(name, r, c):
    return int(hashlib.sha256(f"{name}:{r}:{c}".encode()).hexdigest()[:8], 16)


def score_cells(g, m, D, name, r, c):
    s0 = detect(g, m, D)
    s90 = detect(np.rot90(g), np.rot90(m), D)
    gp = g.copy()
    rng = np.random.default_rng(tile_seed(name, r, c))
    vals = gp[m]
    gp[m] = vals[rng.permutation(vals.size)]
    sp = detect(gp, m, D)
    return {"det": s0, "rot90": {"score": s90["score"], "n_clusters": s90["n_clusters"]},
            "perm": {"score": sp["score"], "n_clusters": sp["n_clusters"]}}


# ----------------------------------------------------------------------------------------------------- score run
def cmd_score(name, rows, out_dir, scratch):
    P = load_params()
    m = load_material(name, scratch, P)
    G = P["grain"]
    D = P["detector"]
    lo, hi = m["sheet"]
    nproc = P["run"]["nproc"]
    os.makedirs(out_dir, exist_ok=True)
    r0, r1 = [int(x) for x in rows.split("-")]
    tiles = [t for t in m["tiles"] if r0 <= t[0] <= r1]
    outp = os.path.join(out_dir, f"scores_{name}.jsonl")
    done = {(d["r"], d["c"]) for d in map(json.loads, open(outp))} if os.path.exists(outp) else set()
    json.dump({"provenance": PROV, "material": name, "tiles_eligible": m["tiles"], "mesh_inputs": m["mesh_inputs"],
               "grid_sha": m.get("grid_sha"), "LH_LW": [m["LH"], m["LW"]], "T": m["T"],
               "params_sha256": HZ.sha_file(PARAMS_PATH)}, open(os.path.join(out_dir, f"material_{name}.json"), "w"), indent=1)
    ctx = mp.get_context("fork")
    pool = ctx.Pool(nproc, initializer=_winit,
                    initargs=(m["url"], slab_range(lo, hi), m["nz"], m["T_g"], G["min_voxels"], G["max_z_slices"],
                              G.get("max_voxels")))
    T, f, cell = m["T"], m["f"], m["cell"]
    H0, W0 = m["LH"] * f, m["LW"] * f
    for (r, c) in tiles:
        if (r, c) in done:
            continue
        t0 = time.time()
        ly0, ly1 = level_px_range(m, r * T, min((r + 1) * T, H0))
        lx0, lx1 = level_px_range(m, c * T, min((c + 1) * T, W0))
        A, nch, nabs = region_arrays(m, pool, ly0, ly1, lx0, lx1, (lo, hi), nproc)
        Cd = px_to_cells(A, cell)
        g, cm = stat_cells(Cd, cell, D)
        sc = score_cells(g, cm, D, name, r, c)
        rec = {"material": name, "r": r, "c": c, "level_px_rows": [ly0, ly1], "level_px_cols": [lx0, lx1],
               "chunks": nch, "chunks_absent": nabs, "valid_px": int(Cd["NV"].sum()),
               "bright_vox": int(Cd["NB"].sum()), "grain_vox": int(Cd["G"].sum()), "grain_fp_px": int(Cd["FP"].sum()),
               "grains": int(Cd["NC"].sum()), "valid_cells": int(cm.sum()), **sc, "secs": round(time.time() - t0, 1)}
        np.savez_compressed(os.path.join(out_dir, f"cells_{name}_r{r}_c{c}.npz"),
                            **{k: v.astype(np.int32) for k, v in Cd.items()})
        with open(outp, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(json.dumps({"m": name, "r": r, "c": c, "score": round(rec["det"]["score"], 1),
                          "perm": round(rec["perm"]["score"], 1), "secs": rec["secs"], "abs": nabs}), flush=True)
    pool.close()


# ----------------------------------------------------------------------------------------------------- on-sheet
def cmd_onsheet(name, scores_dir, thr, outp, scratch):
    """In-sheet fraction of the top cluster of every tile with score > thr: sheet vs gap slabs over the cluster
    footprint, background = median over a ring of ring_mm around the cluster bbox (same slab)."""
    P = load_params()
    m = load_material(name, scratch, P)
    G, D, O = P["grain"], P["detector"], P["onsheet"]
    nproc = P["run"]["nproc"]
    cell = m["cell"]
    recs = [json.loads(l) for l in open(os.path.join(scores_dir, f"scores_{name}.jsonl"))]
    done = {(d["r"], d["c"]) for d in map(json.loads, open(outp))} if os.path.exists(outp) else set()
    ring = int(round(O["ring_mm"] / m["cell_mm"]))
    for rec in recs:
        if rec["det"]["score"] <= thr or (rec["r"], rec["c"]) in done:
            continue
        cl = rec["det"]["clusters"][0]
        by0, by1, bx0, bx1 = cl["bbox"]
        cy0, cy1, cx0, cx1 = by0 - ring, by1 + ring, bx0 - ring, bx1 + ring
        ly0, lx0 = rec["level_px_rows"][0] + cy0 * cell, rec["level_px_cols"][0] + cx0 * cell
        ly1, lx1 = rec["level_px_rows"][0] + cy1 * cell, rec["level_px_cols"][0] + cx1 * cell
        # cluster footprint from the stored cells (recomputed detector on the tile cells)
        z = dict(np.load(os.path.join(scores_dir, f"cells_{name}_r{rec['r']}_c{rec['c']}.npz")))
        g, cm = stat_cells(z, cell, D)
        det, maps = detect(g, cm, D, return_maps=True)
        foot = maps["lab"] == det["clusters"][0]["id"]
        fr = np.zeros((cy1 - cy0, cx1 - cx0), bool)
        ys, xs = np.nonzero(foot)
        ok = (ys >= cy0) & (ys < cy1) & (xs >= cx0) & (xs < cx1)
        fr[ys[ok] - cy0, xs[ok] - cx0] = True
        res = {}
        for sname, (lo, hi) in (("sheet", m["sheet"]), ("gap_lo", m["gaps"][0]), ("gap_hi", m["gaps"][1])):
            pool = mp.get_context("fork").Pool(nproc, initializer=_winit, initargs=(
                m["url"], slab_range(lo, hi), m["nz"], m["T_g"], G["min_voxels"], G["max_z_slices"], G.get("max_voxels")))
            A, nch, nabs = region_arrays(m, pool, ly0, ly1, lx0, lx1, (lo, hi), nproc)
            pool.close()
            gs, ms = stat_cells(px_to_cells(A, cell), cell, D)
            gs, ms = gs[:fr.shape[0], :fr.shape[1]], ms[:fr.shape[0], :fr.shape[1]]
            ringm = ms & ~ndi.binary_dilation(fr, iterations=2)
            bgv = float(np.median(gs[ringm])) if ringm.any() else 0.0
            ex = float((gs[fr & ms] - bgv).sum())
            res[sname] = {"slices": [lo, hi], "bg_per_cell": bgv, "excess": ex, "foot_cells": int((fr & ms).sum()),
                          "chunks": nch, "absent": nabs}
        e = {k: max(0.0, v["excess"]) for k, v in res.items()}
        tot = sum(e.values())
        out = {"material": name, "r": rec["r"], "c": rec["c"], "score": rec["det"]["score"], "cluster": cl,
               "slabs": res, "f_in": (e["sheet"] / tot) if tot > 0 else None,
               "f_in_uniform_baseline": (m["sheet"][1] - m["sheet"][0]) / float(sum(h - l for l, h in [m["sheet"]] + m["gaps"]))}
        with open(outp, "a") as fh:
            fh.write(json.dumps(out) + "\n")
        print(json.dumps({"r": rec["r"], "c": rec["c"], "f_in": out["f_in"]}), flush=True)


if __name__ == "__main__":
    scratch = os.environ.get("CU_SCRATCH", "/tmp/cu_scratch")
    os.makedirs(scratch, exist_ok=True)
    if sys.argv[1] == "score":
        cmd_score(sys.argv[2], sys.argv[3], sys.argv[4], scratch)
    elif sys.argv[1] == "onsheet":
        cmd_onsheet(sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5], scratch)
