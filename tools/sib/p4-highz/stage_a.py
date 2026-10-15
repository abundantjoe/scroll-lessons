"""p4-highz step 1 (DECL-P4-6 item 2; PROTOCOL.md step 1): physics sanity histograms on a random 6 % of level-0
chunks of each material's eligible tiles, whole chunks. Writes per-tile histograms (npz) and physics.json.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only. Usage: python stage_a.py <scratch> <repo>
"""
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

FRAC, SEED, NPROC, NTHR = 0.06, 20260926, 6, 16
M = TID = None


def one(yc_xc):
    yc, xc = yc_xc
    b = C.get(f"{M['url0']}/{yc}/{xc}")
    if b is None:
        return yc, xc, None
    a = np.frombuffer(b, np.uint8).reshape(M["n_slices"], C.CH, C.CH)
    v, ti = C.chunk_masks(M, TID, yc, xc)
    out = {}
    for t in np.unique(ti[ti >= 0]):
        sel = ti == t
        cols = a[:, sel]  # (116, npx)
        hs = [np.bincount(cols[s0:s1].ravel(), minlength=256) for s0, s1 in (M["sheet"], M["gap_lo"], M["gap_hi"])]
        hm = np.bincount(cols[M["sheet"][0]:M["sheet"][1]].max(0), minlength=256)
        nz = cols > 0
        out[int(t)] = (np.stack(hs + [hm]).astype(np.int64), cols.sum(1, dtype=np.int64), nz.sum(1), 
                       np.where(nz, cols, 0).sum(1, dtype=np.int64), int(sel.sum()))
    return yc, xc, out


def work(items):
    with cf.ThreadPoolExecutor(NTHR) as ex:
        return list(ex.map(one, items))


def run(name, scratch):
    global M, TID
    M = C.load_material(name, scratch)
    TID = C.tile_index_map(M)
    allc = sorted({ch for t in M["tiles"] for ch in C.tile_chunks(M, t["r"], t["c"])})
    rng = np.random.default_rng(SEED)
    pick = sorted(rng.choice(len(allc), int(round(FRAC * len(allc))), replace=False))
    sample = [allc[i] for i in pick]
    nt = len(M["tiles"])
    H = np.zeros((nt, 4, 256), np.int64)
    prof = np.zeros((nt, M["n_slices"]), np.int64)
    profnz_n = np.zeros((nt, M["n_slices"]), np.int64)
    profnz_s = np.zeros((nt, M["n_slices"]), np.int64)
    npx = np.zeros(nt, np.int64)
    ntile_chunks = np.zeros(nt, np.int64)
    absent = []
    t0 = time.time()
    parts = [sample[i::NPROC * 8] for i in range(NPROC * 8)]
    with mp.get_context("fork").Pool(NPROC) as pool:
        for res in pool.imap_unordered(work, parts):
            for yc, xc, out in res:
                if out is None:
                    absent.append([yc, xc])
                    continue
                for t, (h, ps, pn, pnz, n) in out.items():
                    H[t] += h
                    prof[t] += ps
                    profnz_n[t] += pn
                    profnz_s[t] += pnz
                    npx[t] += n
                    ntile_chunks[t] += 1
    secs = time.time() - t0
    np.savez_compressed(os.path.join(scratch, f"stage_a_{name}.npz"), H=H, prof=prof, profnz_n=profnz_n,
                        profnz_s=profnz_s, npx=npx, ntile_chunks=ntile_chunks,
                        rc=np.array([[t["r"], t["c"]] for t in M["tiles"]]))
    info = {"material": name, "segment": M["seg"], "eligible_tiles": nt, "chunk_positions_in_eligible_tiles": len(allc),
            "sampled": len(sample), "sample_fraction": len(sample) / len(allc), "absent_404": len(absent),
            "present": len(sample) - len(absent), "secs": round(secs, 1), "mesh_inputs": M["mesh_inputs"],
            "mesh_valid_vertices": int(M["valid"].sum()), "grid_mesh_valid_vertices": M["grid"].get("mesh_valid_vertices")}
    json.dump(info, open(os.path.join(scratch, f"stage_a_{name}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in info.items() if k != "mesh_inputs"}), flush=True)


if __name__ == "__main__":
    scratch = sys.argv[1]
    os.chdir(sys.argv[2])
    for name in (sys.argv[3:] or ["C", "E1"]):
        if not os.path.exists(os.path.join(scratch, f"stage_a_{name}.npz")):
            run(name, scratch)
