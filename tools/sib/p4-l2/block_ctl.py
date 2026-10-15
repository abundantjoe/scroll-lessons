"""DECL-P4-17 item 2: per-cell histograms of the L2S-depth slab max on the CONTROL strip 20260701183125-w028-037.

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only. Same slab (48..60), level 0 and region code as L2 (tools/sib/p4-l2/l2.py). Cells: 4 x 4 per 2 cm tile
(edges round(linspace(0, 8343, 5)), ~5.0 mm). Per cell: mesh-valid px count, px with max > 0, and the uint8 histogram of
the slab max over mesh-valid px with max > 0. Tiles: all eligible tiles of the intercolumn columns c11, c15, c19 and a
seeded sample (default 40) of the text-column tiles (c0-c9, c12-c14, c16-c18). Resumable (append-only jsonl).
Usage: block_ctl.py <ctl_mesh_dir> <out_jsonl> --worker k --nworkers n
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402

INTERCOL = (11, 15, 19)
TEXTCOL = tuple(range(0, 10)) + (12, 13, 14, 16, 17, 18)
SEED, N_TEXT = 20260927, 40
EDGES = np.round(np.linspace(0, l2.T, 5)).astype(int)


def tile_plan(valid, H, W):
    nr, nc = -(-H // l2.T), -(-W // l2.T)
    el = [(r, c) for r in range(nr) for c in range(nc)
          if l2.canvas_mask(valid, H, W, r * l2.T, (r + 1) * l2.T, c * l2.T, (c + 1) * l2.T).mean() >= l2.ELIG]
    ic = [t for t in el if t[1] in INTERCOL]
    tx = [t for t in el if t[1] in TEXTCOL]
    idx = np.random.default_rng(SEED).choice(len(tx), min(N_TEXT, len(tx)), replace=False)
    return ic, [tx[i] for i in sorted(idx)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh_dir")
    ap.add_argument("out")
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--nworkers", type=int, default=1)
    a = ap.parse_args()
    za, _ = l2.zarray(l2.CTL)
    H, W = za["shape"][1:]
    valid = l2.load_valid(a.mesh_dir)
    ic, tx = tile_plan(valid, H, W)
    plan = [(t, "intercol") for t in ic] + [(t, "text") for t in tx]
    done = set()
    if os.path.exists(a.out):
        done = {(d["r"], d["c"]) for d in map(json.loads, open(a.out))}
    ex = cf.ThreadPoolExecutor(16)
    for (r, c), cls in plan[a.worker::a.nworkers]:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, x0 = r * l2.T, c * l2.T
        m = l2.canvas_mask(valid, H, W, y0, y0 + l2.T, x0, x0 + l2.T)
        mx, _, _, _ = l2.region(l2.CTL, y0, y0 + l2.T, x0, x0 + l2.T, (H, W), m, ex)
        cells = []
        for i in range(4):
            for j in range(4):
                sl = (slice(EDGES[i], EDGES[i + 1]), slice(EDGES[j], EDGES[j + 1]))
                mm, v = m[sl], mx[sl]
                s = mm & (v > 0)
                cells.append({"i": i, "j": j, "n_px": int(mm.size), "n_valid": int(mm.sum()), "n_pos": int(s.sum()),
                              "hist": np.bincount(v[s], minlength=256).tolist()})
        with open(a.out, "a") as fh:
            fh.write(json.dumps({"r": r, "c": c, "class": cls, "cells": cells, "utc": l2.utc(),
                                 "s": round(time.time() - t0, 1)}) + "\n")
        print("ctl-cells r%d c%d %s %.0fs" % (r, c, cls, time.time() - t0), flush=True)
    print("WORKER_DONE", a.worker, flush=True)


if __name__ == "__main__":
    main()
