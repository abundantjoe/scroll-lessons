"""p4-purple-de: ONE-TIME application of DUAL_FREEZE (METRIC-HASH-40) to the 137 keV overlap of w010-027 (APPLY.md).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python apply.py <scratch> [worker_index n_workers]   (resumable per block)  ;  python apply.py <scratch> summarise
Frozen parameters are read from fit.json and registration.json, whose sha256 are checked against DUAL_FREEZE.md.
The 137 keV fence is lifted ONLY here (direct chunk reads); frozen tool files are not modified. Numbers only.
"""
import hashlib
import json
import os
import re
import sys
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage as ndi
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

scr = sys.argv[1]
OUT = os.path.join(D.REPO, "logs/sib/p4-purple/de")
od = os.path.join(scr, "apply")
os.makedirs(od, exist_ok=True)
fz = open(os.path.join(OUT, "DUAL_FREEZE.md")).read()
assert hashlib.sha256(fz.encode()).hexdigest() == "93d04a4d0bbba551fe0d648b64904e3491ed15981047c36568472cdee48f9427"
for p, h in re.findall(r"^- ((?:tools|logs)/\S+): ([0-9a-f]{64})$", fz, re.M):
    assert D.sha(open(os.path.join(D.REPO, p), "rb").read()) == h, p
F = json.load(open(os.path.join(OUT, "fit.json")))
R = json.load(open(os.path.join(OUT, "registration.json")))
K, K0 = F["papyrus_line"]["k"], F["papyrus_line"]["k0"]
MED, MAD, T, ONT = F["Z_median"], F["Z_mad_scaled"], F["T_abs_z_p99"], F["onsheet_C78_min_cm-1"]
Wc = np.array(R["affine_correction_W_rows_xyz1_to_dxyz"])
M = D.ref_to_137()
WIN = {D.V78: (-0.04, 0.22), D.V137: (0.01, 0.16)}
PS, B, NS = 83, 498, 51
OFF = np.arange(NS) - 25
g = D.git_json("logs/sib/pairs0814b/e2/grid.json", "origin/claude/gifted-bell-gavnl5-sib-pairs0814b")
TT, NR, NC = g["T_canvas_px"], g["tile_grid"]["n_rows"], g["tile_grid"]["n_cols"]
FPR = 0.0215


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


if len(sys.argv) > 2 and sys.argv[2] == "summarise":
    recs = []
    for f in sorted(os.listdir(od)):
        if f.startswith("b_") and f.endswith(".json"):
            recs += json.load(open(os.path.join(od, f)))["patches"]
    blocks_all = json.load(open(os.path.join(od, "blocks.json")))
    done = len([f for f in os.listdir(od) if f.startswith("b_")])
    tiles = {}
    for p in recs:
        tiles.setdefault(p["tile"], []).append(p)
    out = {"provenance": D.PROV, "serves": "METRIC-HASH-40 one-time application (APPLY.md)",
           "frozen": {"k": K, "k0": K0, "z_median": MED, "z_mad": MAD, "T": T, "onsheet_C78_min": ONT,
                      "registration": "published composed affine + frozen control affine correction W, not refitted",
                      "control_FPR": FPR},
           "blocks_total": len(blocks_all), "blocks_done": done, "tiles": {}}
    for t, ps in sorted(tiles.items(), key=lambda kv: (int(kv[0].split("_c")[0][1:]), int(kv[0].split("_c")[1]))):
        used = [p for p in ps if p["fv"] >= 0.5]
        on = [p for p in used if p["C78"] >= ONT]
        hot = [p for p in on if abs(p["z"]) > T]
        neg = sum(p["z"] < -T for p in hot)
        pos = sum(p["z"] > T for p in hot)
        hs = {(p["pi"], p["pj"]) for p in hot}
        best = 0
        seen = set()
        for c in hs:
            if c in seen:
                continue
            st, n = [c], 0
            seen.add(c)
            while st:
                a = st.pop()
                n += 1
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    b = (a[0] + d[0], a[1] + d[1])
                    if b in hs and b not in seen:
                        seen.add(b)
                        st.append(b)
            best = max(best, n)
        nh = len(hot)
        out["tiles"][t] = {"patches_used": len(used), "patches_onsheet": len(on), "hot_z_lt_-T": int(neg),
                           "hot_z_gt_+T": int(pos), "largest_4conn_cluster": best,
                           "hot_rate_over_used": nh / len(used) if used else None,
                           "binom_p_ge_vs_control_FPR": float(stats.binom.sf(nh - 1, len(used), FPR)) if used else None,
                           "z_p1_p50_p99": [float(np.percentile([p["z"] for p in used], q)) for q in (1, 50, 99)] if used else None,
                           "title_zone_c10_c17": 10 <= int(t.split("_c")[1]) <= 17}
    allu = [p for p in recs if p["fv"] >= 0.5]
    allh = [p for p in allu if p["C78"] >= ONT and abs(p["z"]) > T]
    out["all_tiles"] = {"patches_used": len(allu), "hotspots": len(allh), "rate": len(allh) / max(1, len(allu)),
                        "binom_p": float(stats.binom.sf(len(allh) - 1, len(allu), FPR)) if allu else None}
    out["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(out, open(os.path.join(OUT, "title_zone.json"), "w"), indent=1)
    print(json.dumps(out["all_tiles"]), json.dumps({k: v for k, v in out["tiles"].items() if v["title_zone_c10_c17"]}))
    sys.exit(0)

wi, nw = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
xyz, _ = D.load_mesh(D.SEG_E2, scr)
H, W = xyz.shape[:2]
bpath = os.path.join(od, "blocks.json")
if os.path.exists(bpath):
    blocks = [tuple(b) for b in json.load(open(bpath))]
else:
    bs = set()
    for i0 in range(0, H, 128):
        blk = np.asarray(xyz[i0:i0 + 128])
        gi, gj = np.nonzero(np.isfinite(blk[..., 0]))
        Q = D.map_pts(M, blk[gi, gj].astype(np.float64))
        ins = D.inside_extent(Q)
        for a, b in zip((gi[ins] + i0) * 20 // B, gj[ins] * 20 // B):
            bs.add((int(a), int(b)))
    blocks = sorted(bs)
    json.dump(blocks, open(bpath, "w"))
log("blocks", len(blocks))
mine = blocks[wi * len(blocks) // nw:(wi + 1) * len(blocks) // nw]   # contiguous ranges (cache locality)
cache = OrderedDict()
CMAX = 700
pool = ThreadPoolExecutor(16)


def getc(v, k):
    key = (v, k)
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    Z, Y, X = D.SHAPE[v]
    c = None
    if 0 <= k[0] * 128 < Z and 0 <= k[1] * 128 < Y and 0 <= k[2] * 128 < X:
        b = D.get(f"{D.BUCKET}/PHercParis4/volumes/{v}.zarr/0/{k[0]}/{k[1]}/{k[2]}")
        c = None if b is None else np.frombuffer(b, np.uint8).reshape(128, 128, 128)
    cache[key] = c
    while len(cache) > CMAX:
        cache.popitem(last=False)
    return c


def sample(v, Q):
    ok = np.isfinite(Q).all(1)
    out = np.zeros(len(Q), np.float32)
    if not ok.any():
        return out
    Qo = Q[ok]
    bse = np.floor(Qo).astype(np.int64)
    enc = lambda k: (k[:, 0] + 64) * (1 << 40) + (k[:, 1] + 64) * (1 << 20) + (k[:, 2] + 64)
    parts = [np.unique(enc(np.c_[bse[:, 2] // 128, bse[:, 1] // 128, bse[:, 0] // 128]))]
    be = bse[((bse % 128) == 127).any(1)]
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                parts.append(np.unique(enc(np.c_[(be[:, 2] + dz) // 128, (be[:, 1] + dy) // 128, (be[:, 0] + dx) // 128])))
    u = np.unique(np.concatenate(parts))
    keys = {(int(c >> 40) - 64, int((c >> 20) & ((1 << 20) - 1)) - 64, int(c & ((1 << 20) - 1)) - 64) for c in u}
    kz = np.array(sorted(keys))
    lo, hi = kz.min(0), kz.max(0) + 1
    box = np.zeros(tuple((hi - lo) * 128), np.uint8)
    need = [k for k in keys if (v, k) not in cache]
    list(pool.map(lambda k: getc(v, k), need))
    for k in keys:
        c = getc(v, k)
        if c is not None:
            o = (np.array(k) - lo) * 128
            box[o[0]:o[0] + 128, o[1]:o[1] + 128, o[2]:o[2] + 128] = c
    q = Qo - lo[::-1] * 128
    out[ok] = ndi.map_coordinates(box, [q[:, 2], q[:, 1], q[:, 0]], order=1, mode="constant", cval=0)
    return out


t0 = time.time()
for n, (br, bc) in enumerate(mine):
    fn = os.path.join(od, f"b_{br}_{bc}.json")
    if os.path.exists(fn):
        continue
    r0, c0 = br * B, bc * B
    g0i, g0j = max(0, r0 // 20 - 2), max(0, c0 // 20 - 2)
    win = np.asarray(xyz[g0i:min(H, (r0 + B) // 20 + 3), g0j:min(W, (c0 + B) // 20 + 3)], np.float64)
    di, dj = np.gradient(win, axis=0), np.gradient(win, axis=1)
    nrm = np.cross(dj, di)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    rr, cc = np.meshgrid((r0 + np.arange(B)) / 20.0 - g0i, (c0 + np.arange(B)) / 20.0 - g0j, indexing="ij")
    it = lambda A: np.stack([ndi.map_coordinates(A[..., k], [rr, cc], order=1, mode="constant", cval=np.nan)
                             for k in range(3)], -1)
    p, nn = it(win), it(nrm)
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    P = (p[:, :, None, :] + OFF[None, None, :, None] * nn[:, :, None, :]).reshape(-1, 3)
    Q = D.map_pts(M, P + np.c_[P, np.ones(len(P))] @ Wc)
    f78 = sample(D.V78, P).reshape(B, B, NS)
    f137 = sample(D.V137, Q).reshape(B, B, NS)
    valid = (f78.min(2) > 0.5) & (f137.min(2) > 0.5)
    pats = []
    for i in range(6):
        for j in range(6):
            sl = (slice(i * PS, (i + 1) * PS), slice(j * PS, (j + 1) * PS))
            v = valid[sl]
            fv = float(v.mean())
            if fv == 0:
                continue
            a = WIN[D.V78][0] + f78[sl][v].mean() * (WIN[D.V78][1] - WIN[D.V78][0]) / 255.0
            b = WIN[D.V137][0] + f137[sl][v].mean() * (WIN[D.V137][1] - WIN[D.V137][0]) / 255.0
            z = ((b - (K * a + K0)) - MED) / MAD
            ci, cj = r0 + i * PS + PS // 2, c0 + j * PS + PS // 2
            pats.append({"pi": br * 6 + i, "pj": bc * 6 + j, "tile": f"r{ci // TT}_c{cj // TT}", "fv": fv,
                         "C78": float(a), "C137": float(b), "z": float(z)})
    json.dump({"block": [br, bc], "patches": pats}, open(fn + ".tmp", "w"))
    os.replace(fn + ".tmp", fn)
    if n % 5 == 0:
        log(wi, n, len(mine), round(time.time() - t0), len(cache))
log("worker done", wi)
