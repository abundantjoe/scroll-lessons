"""P4-L4 (RULES.md DECL-P4-18): surface-following thin slabs L4- / L4+ from the 2.4 um surface volumes, level 1.

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only; never views a pixel. Rules frozen in logs/sib/p4-l2/l4/params_l4.json (pushed before any L4 number).
Usage (control cells): l4.py ctl <ctl_mesh_dir> <out_dir> --worker k --nworkers n
"""
import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import os
import sys
import time

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402

LEVEL, NZ, CH, C = 1, 109, 128, 54
T_MID = 93
WIN = 25                      # +-60 um
LO_M, HI_M = -8, 2            # L4-: [s_minus - 8, s_minus + 2]
LO_P, HI_P = -2, 8            # L4+: [s_plus - 2, s_plus + 8]
_g = np.exp(-0.5 * np.arange(-4, 5) ** 2)
GK = (_g / _g.sum()).astype(np.float32)


def smooth_z(v):
    """Gaussian sigma 1 slice along axis 0 (radius 4, edge replicate). v: (NZ, N) -> float32."""
    p = np.concatenate([np.repeat(v[:1], 4, 0), v, np.repeat(v[-1:], 4, 0)]).astype(np.float32)
    out = np.zeros(v.shape, np.float32)
    for k, w in enumerate(GK):
        out += w * p[k:k + v.shape[0]]
    return out


def faces(v):
    """v: (NZ, N) uint8 raw profiles -> (s_minus, s_plus, valid) per column, per DECL-P4-18 item 1."""
    nz, n = v.shape
    above = smooth_z(v) > T_MID
    idx = np.arange(nz)[:, None]
    dist = np.where(above, np.abs(idx - C), 10 ** 6)
    # nearest above-slice to C; ties -> lower slice (argmin over dist*2 + (idx > C))
    key = dist * 2 + (idx > C)
    s0 = key.argmin(0)
    valid = dist.min(0) <= WIN
    lo = np.where(~above & (idx < s0[None]), idx, -1).max(0) + 1
    hi = np.where(~above & (idx > s0[None]), idx, nz).min(0) - 1
    return lo, hi, valid


def face_max(v, s, a, b):
    offs = np.arange(a, b + 1)[:, None]
    ii = np.clip(s[None] + offs, 0, v.shape[0] - 1)
    return np.take_along_axis(v, ii, 0).max(0)


def l4_block(v):
    """v: (NZ, h, w) uint8 -> dict of (h, w) arrays: m (L4-), p (L4+), sm, sp (offsets vs slice 54), ok."""
    nz, h, w = v.shape
    f = v.reshape(nz, -1)
    sm, sp, ok = faces(f)
    return {"m": face_max(f, sm, LO_M, HI_M).reshape(h, w), "p": face_max(f, sp, LO_P, HI_P).reshape(h, w),
            "sm": (sm - C).astype(np.int8).reshape(h, w), "sp": (sp - C).astype(np.int8).reshape(h, w),
            "ok": ok.reshape(h, w)}


_s = requests.Session()
_s.mount("https://", requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=3))


def get_full(seg, cy, cx):
    key = f"{l2.sv_key(seg)}/{LEVEL}/0/{cy}/{cx}"
    for i in range(7):
        try:
            r = _s.get(f"{l2.HTTP}/{key}", timeout=90)
            if r.status_code == 404:
                return None, {"k": key.split(".zarr/")[1], "status": 404}
            if r.status_code == 200 and len(r.content) == NZ * CH * CH:
                return np.frombuffer(r.content, np.uint8).reshape(NZ, CH, CH), {
                    "k": key.split(".zarr/")[1], "status": 200, "sha256": hashlib.sha256(r.content).hexdigest()}
        except requests.RequestException:
            pass
        time.sleep(min(2 ** i, 30))
    raise RuntimeError(key)


def region_l4(seg, y0, y1, x0, x1, shape, ex):
    """Level-1 rows [y0,y1), cols [x0,x1). Returns dict of arrays (0 / ok False outside the array or 404)."""
    H, W = shape
    h, w = y1 - y0, x1 - x0
    out = {"m": np.zeros((h, w), np.uint8), "p": np.zeros((h, w), np.uint8), "sm": np.zeros((h, w), np.int8),
           "sp": np.zeros((h, w), np.int8), "ok": np.zeros((h, w), bool)}
    jobs = [(cy, cx) for cy in range(max(y0, 0) // CH, (min(y1, H) - 1) // CH + 1)
            for cx in range(max(x0, 0) // CH, (min(x1, W) - 1) // CH + 1)]
    recs = []
    for (cy, cx), (d, rec) in zip(jobs, ex.map(lambda j: get_full(seg, *j), jobs)):
        recs.append(rec)
        if d is None:
            continue
        ya, yb = max(cy * CH, y0), min(cy * CH + CH, y1, H)
        xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W)
        b = l4_block(d[:, ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH])
        for k in out:
            out[k][ya - y0:yb - y0, xa - x0:xb - x0] = b[k]
    return out, recs


def l1_mask(valid, H0, W0, y0, y1, x0, x1):
    """Mesh-valid at level-1 px (canvas px (2i, 2j))."""
    gh, gw = valid.shape
    ys, xs = 2 * np.arange(y0, y1), 2 * np.arange(x0, x1)
    m = valid[np.ix_(np.clip(ys * gh // H0, 0, gh - 1), np.clip(xs * gw // W0, 0, gw - 1))]
    return m & (ys < H0)[:, None] & (xs < W0)[None, :]


def cells_of(a, m, ok):
    """4 x 4 cells: per face histogram of L4 values over (mesh-valid & L4-valid) px."""
    n = a["m"].shape[0]
    e = np.round(np.linspace(0, n, 5)).astype(int)
    cells = []
    for i in range(4):
        for j in range(4):
            sl = (slice(e[i], e[i + 1]), slice(e[j], e[j + 1]))
            s = m[sl] & ok[sl]
            cells.append({"i": i, "j": j, "n_px": int(m[sl].size), "n_valid": int(m[sl].sum()), "n_pos": int(s.sum()),
                          "hist_m": np.bincount(a["m"][sl][s], minlength=256).tolist(),
                          "hist_p": np.bincount(a["p"][sl][s], minlength=256).tolist()})
    return cells


def cmd_ctl(a):
    import block_ctl
    za0, _ = l2.zarray(l2.CTL)
    H0, W0 = za0["shape"][1:]
    j = requests.get(f"{l2.HTTP}/{l2.sv_key(l2.CTL)}/{LEVEL}/.zarray", timeout=60).json()
    H1, W1 = j["shape"][1:]
    assert j["chunks"] == [NZ, CH, CH] and j["compressor"] is None and (H1, W1) == (-(-H0 // 2), -(-W0 // 2))
    valid = l2.load_valid(a.mesh_dir)
    ic, tx = block_ctl.tile_plan(valid, H0, W0)
    plan = [(t, "intercol") for t in ic] + [(t, "text") for t in tx]
    os.makedirs(os.path.join(a.out, "arr"), exist_ok=True)
    fo = os.path.join(a.out, "ctl_l4_w%d.jsonl" % a.worker)
    done = {(d["r"], d["c"]) for d in map(json.loads, open(fo))} if os.path.exists(fo) else set()
    ex = cf.ThreadPoolExecutor(16)
    for (r, c), cls in plan[a.worker::a.nworkers]:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1 = (r * l2.T) // 2, ((r + 1) * l2.T - 1) // 2 + 1
        x0, x1 = (c * l2.T) // 2, ((c + 1) * l2.T - 1) // 2 + 1
        m = l1_mask(valid, H0, W0, y0, y1, x0, x1)
        arr, recs = region_l4(l2.CTL, y0, y1, x0, x1, (H1, W1), ex)
        ok = arr["ok"] & m
        buf = io.BytesIO()
        np.savez_compressed(buf, valid=m, **arr)
        open(os.path.join(a.out, "arr", f"ctl_r{r}_c{c}.npz"), "wb").write(buf.getvalue())
        sm, sp = arr["sm"][ok].astype(int), arr["sp"][ok].astype(int)
        rec = {"r": r, "c": c, "class": cls, "l1_rows": [y0, y1], "l1_cols": [x0, x1],
               "n_valid": int(m.sum()), "frac_l4_valid": float(ok.sum() / max(1, m.sum())),
               "offsets_um": {k: (np.percentile(v, [10, 50, 90]) * 2.4).tolist() if v.size else None
                              for k, v in (("s_minus", sm), ("s_plus", sp), ("thickness", sp - sm))},
               "cells": cells_of(arr, m, arr["ok"]), "npz_sha256": hashlib.sha256(buf.getvalue()).hexdigest(),
               "chunks": len(recs), "missing": sum(x["status"] == 404 for x in recs), "s": round(time.time() - t0, 1),
               "utc": l2.utc()}
        with open(fo, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("ctl-l4 r%d c%d %s %.0fs" % (r, c, cls, rec["s"]), flush=True)
    print("WORKER_DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp_ = ap.add_subparsers(dest="cmd", required=True)
    p = sp_.add_parser("ctl")
    p.add_argument("mesh_dir")
    p.add_argument("out")
    p.add_argument("--worker", type=int, default=0)
    p.add_argument("--nworkers", type=int, default=1)
    a = ap.parse_args()
    {"ctl": cmd_ctl}[a.cmd](a)
