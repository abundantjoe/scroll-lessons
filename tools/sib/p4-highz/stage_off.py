"""p4-highz DECL-P4-6-A3: the unchanged P4-F screen at depth offsets (PROTOCOL_dstar.md). One level-0 range read per
chunk covers every requested offset's sheet slab. Numbers only; no PNG is written.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage:
  python stage_off.py <scratch> <repo> tiles <material> <o_um,o_um,...>       per-tile screen at each offset
  python stage_off.py <scratch> <repo> fin   <material> <o_um,...>            6 % sample f_in at each offset
  python stage_off.py <scratch> <repo> gap   <material> <o_um> r,c [r,c ...]  full-coverage f_in at one offset

Optional env: HZ_COLS=a-b restricts 'tiles' to tile columns a..b inclusive; HZ_MAXTILES=n caps the tile count (tests).

Exact E2 sweep command (DECL-P4-6-A3/-A4), run from the repo root on a checkout of this branch:
  pip install numpy requests opencv-python-headless tifffile scipy pillow
  git fetch origin claude/gifted-bell-gavnl5-sib-pairs0814b claude/gifted-bell-gavnl5-sib-p4-tiles-b
  mkdir -p /tmp/hz
  HZ_COLS=9-13 python3 tools/sib/p4-highz/stage_off.py /tmp/hz "$PWD" tiles E2 -60,-45,-30,-15,0,15,30,45,60   # hzw1
  HZ_COLS=14-19 python3 tools/sib/p4-highz/stage_off.py /tmp/hz "$PWD" tiles E2 -60,-45,-30,-15,0,15,30,45,60  # hzw2
Output: /tmp/hz/off_E2_-60_-45_-30_-15_0_15_30_45_60.jsonl (one JSON line per tile; resumes by (r, c) if restarted).
Frozen thresholds read by this tool: logs/sib/p4-highz/thresholds_2p4.json (E2, C2: T_hi 203; commit 39a2e1d) and
logs/sib/p4-highz/thresholds.json (E1, C: T_hi 233; commit a9eead1). The grid, eligibility and mesh come from
pairs0814b e2/grid.json + manifest.json (git) and the official tifxyz (downloaded, ~0.25 GB).
"""
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402
import stage_b as SB  # noqa: E402  (acf_stats, stroke_stats, tile_arrays, place: unchanged definitions)

NPROC, NTHR = 6, 24
W = {}


def one_tiles(yx):
    yc, xc = yx
    b = C.get(f"{W['url']}/{yc}/{xc}", W["rng"])
    if b is None:
        return yc, xc, None
    a = np.frombuffer(b, np.uint8).reshape(-1, C.CH, C.CH)
    out = []
    for s0, s1 in W["sheets"]:
        sl = a[s0 - W["r0"]:s1 - W["r0"]]
        out.append((np.packbits(sl.max(0) > W["th"]).tobytes(), (sl > W["th"]).sum(0).astype(np.uint8).tobytes()))
    return yc, xc, out


def one_whole(yx):
    yc, xc = yx
    b = C.get(f"{W['url']}/{yc}/{xc}")
    if b is None:
        return yc, xc, None
    a = np.frombuffer(b, np.uint8).reshape(-1, C.CH, C.CH) > W["th"]
    res = []
    for sh, lo, hi, _ in W["slabs"]:
        res.append(tuple(a[s0:s1].sum(0).astype(np.uint8) if s1 > s0 else np.zeros((C.CH, C.CH), np.uint8)
                         for s0, s1 in (sh, lo, hi)))
    if W.get("mat") is None:
        return yc, xc, [tuple(x.tobytes() for x in r) for r in res]
    v, ti = C.chunk_masks(W["mat"], W["tid"], yc, xc)
    out = {}
    for t in np.unique(ti[ti >= 0]):
        sel = ti == t
        out[int(t)] = [[int(x[sel].sum()) for x in r] for r in res]
    return yc, xc, out


def work(args):
    W.update(args[0])
    fn = one_tiles if W["kind"] == "tiles" else one_whole
    with cf.ThreadPoolExecutor(NTHR) as ex:
        return list(ex.map(fn, args[1]))


def thr(name, repo):
    f = "thresholds.json" if name in ("C", "E1") else "thresholds_2p4.json"
    return json.load(open(os.path.join(repo, "logs/sib/p4-highz", f)))["T_hi"]


def o_slices(name, o_um):
    return int(round(o_um / C.MATERIALS[name]["um"]))


def run_tiles(scr, repo, name, offs, pool):
    mat = C.load_material(name, scr)
    T, um, th = mat["T"], mat["um"], thr(name, repo)
    oss = [o_slices(name, o) for o in offs]
    slabs = [C.slabs_at(name, o) for o in oss]
    r0, r1 = min(s[0][0] for s in slabs), max(s[0][1] for s in slabs)
    cfg = {"kind": "tiles", "url": mat["url0"], "th": th, "rng": (r0 * C.PLANE, r1 * C.PLANE - 1), "r0": r0,
           "sheets": [s[0] for s in slabs]}
    outp = os.path.join(scr, f"off_{name}_{'_'.join(str(o) for o in offs)}.jsonl")
    done = {(d["r"], d["c"]) for d in map(json.loads, open(outp))} if os.path.exists(outp) else set()
    cols = [int(x) for x in os.environ.get("HZ_COLS", "0-10000").split("-")]
    todo = [t for t in mat["tiles"] if (t["r"], t["c"]) not in done and cols[0] <= t["c"] <= cols[1]]
    todo = todo[:int(os.environ.get("HZ_MAXTILES", "100000"))]
    sub = lambda t: pool.map_async(work, [(cfg, C.tile_chunks(mat, t["r"], t["c"])[i::NPROC * 4]) for i in range(NPROC * 4)])
    fut = sub(todo[0]) if todo else None
    for k, t in enumerate(todo):
        t0 = time.time()
        res = [x for part in fut.get() for x in part]
        if k + 1 < len(todo):
            fut = sub(todo[k + 1])
        r, c = t["r"], t["c"]
        v = SB.tile_arrays(mat, r, c)
        absent = np.zeros((T, T), bool)
        for yc, xc, o in res:
            if o is None:
                SB.place(absent, r, c, T, yc, xc, np.ones((C.CH, C.CH), bool))
        vp = v & ~absent
        vf_d = cv2.resize(vp.astype(np.float32), (C.OUT_SIDE, C.OUT_SIDE), interpolation=cv2.INTER_AREA)
        md = vf_d >= 0.5
        rec = {"r": r, "c": c, "material": name, "valid_px_present": int(vp.sum()), "offsets": {}}
        for j, o in enumerate(offs):
            hi = np.zeros((T, T), np.uint8)
            hic = np.zeros((T, T), np.uint8)
            for yc, xc, oo in res:
                if oo is None:
                    continue
                SB.place(hi, r, c, T, yc, xc, np.unpackbits(np.frombuffer(oo[j][0], np.uint8))[:C.PLANE].reshape(C.CH, C.CH))
                SB.place(hic, r, c, T, yc, xc, np.frombuffer(oo[j][1], np.uint8).reshape(C.CH, C.CH))
            hi &= vp.astype(np.uint8)
            hicv = np.where(vp, hic, 0)
            hd = cv2.resize(hicv.astype(np.float32), (C.OUT_SIDE, C.OUT_SIDE), interpolation=cv2.INTER_AREA)
            D = np.where(md, hd / np.maximum(vf_d, 1e-9), 0.0)
            rec["offsets"][str(o)] = {"o_slices": oss[j], "sheet": list(slabs[j][0]), "n_hi": int(hicv.sum(dtype=np.int64)),
                                      "acf": SB.acf_stats(D, md), "acf_rot90": SB.acf_stats(np.rot90(D), np.rot90(md)),
                                      "stroke": SB.stroke_stats(hi, hic, um)}
        rec["secs"] = round(time.time() - t0, 1)
        with open(outp, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps({"m": name, "r": r, "c": c, "secs": rec["secs"]}), flush=True)


def run_fin(scr, repo, name, offs):
    mat = C.load_material(name, scr)
    tid = C.tile_index_map(mat)
    allc = sorted({ch for t in mat["tiles"] for ch in C.tile_chunks(mat, t["r"], t["c"])})
    rng = np.random.default_rng(20260926)  # the step-1 sample positions (PROTOCOL.md)
    sample = [allc[i] for i in sorted(rng.choice(len(allc), int(round(0.06 * len(allc))), replace=False))]
    slabs = [C.slabs_at(name, o_slices(name, o)) for o in offs]
    cfg = {"kind": "whole", "url": mat["url0"], "th": thr(name, repo), "slabs": slabs, "mat": mat, "tid": tid}
    W.update(cfg)
    acc = np.zeros((len(mat["tiles"]), len(offs), 3), np.int64)
    with mp.get_context("fork").Pool(NPROC) as pool:
        for part in pool.imap_unordered(work, [({}, sample[i::NPROC * 8]) for i in range(NPROC * 8)]):
            for yc, xc, out in part:
                if out:
                    for t, lst in out.items():
                        acc[t] += np.array(lst)
    res = {}
    for i, t in enumerate(mat["tiles"]):
        for j, o in enumerate(offs):
            sh, lo, hi, dg = slabs[j]
            ns, nl, nh = (int(x) for x in acc[i, j])
            av = (lo[1] - lo[0]) + (hi[1] - hi[0])
            ng = (nl + nh) * (2 * dg) / max(1, av)
            res.setdefault(f"r{t['r']}_c{t['c']}", {})[str(o)] = {
                "n_sheet": ns, "n_gap_lo": nl, "n_gap_hi": nh, "gap_slices_available": [lo[1] - lo[0], hi[1] - hi[0]],
                "gap_slices_declared_per_side": dg, "f_in_sample": ns / max(1e-9, ns + ng)}
    json.dump(res, open(os.path.join(scr, f"fin_{name}_{'_'.join(str(o) for o in offs)}.json"), "w"))
    print(json.dumps({"fin": name, "tiles": len(res)}), flush=True)


def run_gap(scr, repo, name, o, tiles, pool):
    mat = C.load_material(name, scr)
    T = mat["T"]
    sl = C.slabs_at(name, o_slices(name, o))
    cfg = {"kind": "whole", "url": mat["url0"], "th": thr(name, repo), "slabs": [sl], "mat": None}
    for r, c in tiles:
        ch = C.tile_chunks(mat, r, c)
        res = [x for part in pool.map(work, [(cfg, ch[i::NPROC * 4]) for i in range(NPROC * 4)]) for x in part]
        v = SB.tile_arrays(mat, r, c)
        acc = [np.zeros((T, T), np.uint8) for _ in range(3)]
        for yc, xc, bs in res:
            if bs:
                for a, b in zip(acc, bs[0]):
                    SB.place(a, r, c, T, yc, xc, np.frombuffer(b, np.uint8).reshape(C.CH, C.CH))
        ns, nl, nh = (int(np.where(v, a, 0).sum(dtype=np.int64)) for a in acc)
        av = (sl[1][1] - sl[1][0]) + (sl[2][1] - sl[2][0])
        ng = (nl + nh) * (2 * sl[3]) / max(1, av)
        rec = {"r": r, "c": c, "o_um": o, "n_sheet": ns, "n_gap_lo": nl, "n_gap_hi": nh,
               "gap_slices_available": [sl[1][1] - sl[1][0], sl[2][1] - sl[2][0]], "f_in_full": ns / max(1e-9, ns + ng)}
        with open(os.path.join(scr, f"offgap_{name}.jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    scr, repo, mode, name = sys.argv[1:5]
    os.chdir(repo)
    offs = [int(x) for x in sys.argv[5].split(",")]
    if mode == "fin":
        run_fin(scr, repo, name, offs)
    else:
        with mp.get_context("fork").Pool(NPROC) as pool:
            if mode == "tiles":
                run_tiles(scr, repo, name, offs, pool)
            else:
                run_gap(scr, repo, name, offs[0], [tuple(map(int, x.split(","))) for x in sys.argv[6:]], pool)
