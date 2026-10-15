"""Compute GOLD work maps and per-tile summaries for a material (numbers only).

Provenance: Project HERCULES | owner the owner | [id removed]

Usage: python run_tiles.py <MAT> <scratch> <outdir> [--rows r0,r1,...] [--procs 4] [--threads 24]
Writes <outdir>/<MAT>/r{r}_c{c}.npz (Z, Zs float16 on the work grid; n usable counts uint8) and appends one JSON line
per tile to <outdir>/<MAT>/tiles.jsonl (Z histogram, summary). No image is written or displayed.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold as G  # noqa: E402

HIST_LO, HIST_HI, HIST_BIN = -100.0, 400.0, 0.25
NB = int((HIST_HI - HIST_LO) / HIST_BIN)
_MAT = None
_P = None


def init(mat, params):
    global _MAT, _P
    _MAT, _P = mat, params


def one(tile):
    mat, p = _MAT, _P
    r, c = tile["r"], tile["c"]
    t0 = time.time()
    win = {"sheet": G.slab(mat["name"], p["half_um"])}
    maps, meta = G.tile_work_maps(mat, r, c, win, p["sat"], threads=p["threads"])
    m = mat["m"]
    px_mm = m["px_um"] * m["B"] / 1000.0
    Z, Zs, res = G.score_maps(maps["sheet"], px_mm, p["radius_mm"], tau=None)
    good = np.isfinite(Z)
    h = np.histogram(np.clip(Z[good], HIST_LO, HIST_HI - 1e-3), bins=NB, range=(HIST_LO, HIST_HI))[0]
    out = os.path.join(p["outdir"], mat["name"])
    np.savez_compressed(os.path.join(out, f"r{r}_c{c}.npz"), Z=Z.astype(np.float16), Zs=Zs.astype(np.float16),
                        n=maps["sheet"]["n"].astype(np.uint8), P=maps["sheet"]["P"].astype(np.float32))
    rec = {"mat": mat["name"], "r": r, "c": c, "valid_fraction_src": tile["valid_fraction_src"], **meta, **res,
           "hist_nonzero": {int(i): int(h[i]) for i in np.nonzero(h)[0]}, "secs": round(time.time() - t0, 1),
           "window": win["sheet"]}
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mat")
    ap.add_argument("scratch")
    ap.add_argument("outdir")
    ap.add_argument("--rows", default=None)
    ap.add_argument("--tiles", default=None, help="r:c,r:c")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=24)
    a = ap.parse_args()
    params = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "detector_core.json")))
    params.update({"threads": a.threads, "outdir": a.outdir})
    mat = G.load_material(a.mat, a.scratch)
    tiles = mat["tiles"]
    if a.rows:
        rows = {int(x) for x in a.rows.split(",")}
        tiles = [t for t in tiles if t["r"] in rows]
    if a.tiles:
        want = {tuple(map(int, x.split(":"))) for x in a.tiles.split(",")}
        tiles = [t for t in tiles if (t["r"], t["c"]) in want]
    os.makedirs(os.path.join(a.outdir, a.mat), exist_ok=True)
    done = set()
    jl = os.path.join(a.outdir, a.mat, "tiles.jsonl")
    if os.path.exists(jl):
        done = {(d["r"], d["c"]) for d in map(json.loads, open(jl))}
    todo = [t for t in tiles if (t["r"], t["c"]) not in done]
    print(f"{a.mat}: {len(tiles)} tiles selected, {len(todo)} to do", flush=True)
    ctx = mp.get_context("fork")
    with ctx.Pool(a.procs, initializer=init, initargs=(mat, params)) as pool, open(jl, "a") as fo:
        for rec in pool.imap_unordered(one, todo):
            fo.write(json.dumps(rec) + "\n")
            fo.flush()
            print(f"{a.mat} r{rec['r']} c{rec['c']} chunks {rec['chunks']} absent {rec['absent']} "
                  f"secs {rec['secs']}", flush=True)
    json.dump({"mat": a.mat, "mesh_inputs": mat["mesh_inputs"], "T": mat["T"], "grid_rc": mat["grid_rc"],
               "shape": mat["shape"], "n_tiles_eligible": len(mat["tiles"]),
               "tiles_eligible": [(t["r"], t["c"]) for t in mat["tiles"]]},
              open(os.path.join(a.outdir, a.mat, "material.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
