"""p4-purple-de B1: control sites (w028-037) and their flattened +-60 um profiles in both registered volumes.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python sites.py <scratch>
Writes <scratch>/sites/<id>.npz (grey profiles, float16; never displayed) and logs/sib/p4-purple/de/sites.json.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

scr = sys.argv[1]
od = os.path.join(scr, "sites")
os.makedirs(od, exist_ok=True)
M = D.ref_to_137()
reg = json.load(open(os.path.join(D.REPO, "logs/sib/p4-purple/de/registration.json")))
assert reg["primary_model"] == "A"
Wc = np.array(reg["affine_correction_W_rows_xyz1_to_dxyz"])
g = D.git_json("logs/sib/p4-tiles-b/grid.json", "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b")
T = g["T_px"]
xyz, _ = D.load_mesh(D.SEG_C2, scr)
H, W = xyz.shape[:2]
S, HS, NW, NS = 498, 249, 13, 51           # site px, half, grid half-window, samples
OFF = np.arange(NS) - 25                   # voxels (2.4 um) along the normal: -60..+60 um
MIS = 250 / 2.4                            # misregistration shift, voxels


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def to137(P):
    return D.map_pts(M, P + np.c_[P, np.ones(len(P))] @ Wc)


def site_geometry(gi, gj):
    win = np.asarray(xyz[gi - NW:gi + NW + 1, gj - NW:gj + NW + 1], np.float64)
    if not np.isfinite(win).all():
        return None
    di = np.gradient(win, axis=0)
    dj = np.gradient(win, axis=1)
    n = np.cross(dj, di)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    ti = di / np.linalg.norm(di, axis=-1, keepdims=True)
    r = (np.arange(S) - HS) / 20.0 + NW
    rr, cc = np.meshgrid(r, r, indexing="ij")
    it = lambda A: np.stack([ndi.map_coordinates(A[..., k], [rr, cc], order=1) for k in range(3)], -1)
    p, nn, tt = it(win), it(n), it(ti)
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    tt /= np.linalg.norm(tt, axis=-1, keepdims=True)
    return win, p, nn, tt


def chunks_of(Q):
    """Chunk keys (zc, yc, xc) touched by trilinear sampling at level-0 xyz points Q (exact)."""
    b = np.floor(Q).astype(np.int64)
    enc = lambda k: (k[:, 0] + 64) * (1 << 40) + (k[:, 1] + 64) * (1 << 20) + (k[:, 2] + 64)
    keys = [np.unique(enc(np.c_[b[:, 2] // 128, b[:, 1] // 128, b[:, 0] // 128]))]
    edge = ((b % 128) == 127).any(1)
    be = b[edge]
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                keys.append(np.unique(enc(np.c_[(be[:, 2] + dz) // 128, (be[:, 1] + dy) // 128, (be[:, 0] + dx) // 128])))
    u = np.unique(np.concatenate(keys))
    return {(int(c >> 40) - 64, int((c >> 20) & ((1 << 20) - 1)) - 64, int(c & ((1 << 20) - 1)) - 64) for c in u}


def sample(v, Q, keys, pool):
    kz = np.array(sorted(keys))
    lo = kz.min(0)
    hi = kz.max(0) + 1
    box = np.zeros(tuple((hi - lo) * 128), np.uint8)
    Z, Y, X = D.SHAPE[v]
    good = [k for k in keys if 0 <= k[0] * 128 < Z and 0 <= k[1] * 128 < Y and 0 <= k[2] * 128 < X]
    got = pool.map(lambda k: (k, D.read_chunk(v, k[0], k[1], k[2], scr)), good)
    for k, c in got:
        if c is not None:
            o = (np.array(k) - lo) * 128
            box[o[0]:o[0] + 128, o[1]:o[1] + 128, o[2]:o[2] + 128] = c
    base = lo[::-1] * 128  # xyz
    q = Q - base
    return ndi.map_coordinates(box, [q[:, 2], q[:, 1], q[:, 0]], order=1, mode="constant", cval=0).astype(np.float32)


_fc = {}


def fence_ok_keys(keys):
    for k in keys:
        if k not in _fc:
            _fc[k] = D.fence_ok_chunks(k[2] * 128, k[2] * 128 + 128, k[1] * 128, k[1] * 128 + 128, k[0] * 128,
                                       k[0] * 128 + 128, scr)
        if not _fc[k]:
            return False
    return True


# ---- candidates (grid step 5)
rng = np.random.default_rng(16)
cands = []
for gi in range(NW, H - NW, 5):
    row = np.asarray(xyz[gi])
    for gj in range(NW, W - NW, 5):
        if np.isfinite(row[gj, 0]):
            Q = D.map_pts(M, row[gj][None].astype(np.float64))
            if D.inside_extent(Q)[0] and D.inside_cyl(Q)[0]:
                cands.append((gi, gj))
cands = [cands[i] for i in rng.permutation(len(cands))]
log("candidate centres", len(cands))

chosen = {"fit": [], "held": []}
stats = {"tried": 0, "invalid_window": 0, "outside": 0, "fence": 0, "zero_centre": 0, "spacing": 0}
pool = ThreadPoolExecutor(16)
for gi, gj in cands:
    if len(chosen["fit"]) >= 40 and len(chosen["held"]) >= 40:
        break
    part = "fit" if (gj * 20 // T) % 2 == 0 else "held"
    if len(chosen[part]) >= 40:
        continue
    c0 = np.asarray(xyz[gi, gj], np.float64)
    allc = [s["centre_ref"] for s in chosen["fit"] + chosen["held"]]
    if allc and np.min(np.linalg.norm(np.array(allc) - c0, axis=1)) < 625:
        stats["spacing"] += 1
        continue
    stats["tried"] += 1
    geo = site_geometry(gi, gj)
    if geo is None:
        stats["invalid_window"] += 1
        continue
    win, p, nn, tt = geo
    Qw = D.map_pts(M, win.reshape(-1, 3))
    if not (D.inside_extent(Qw).all() and D.inside_cyl(Qw).all()):
        stats["outside"] += 1
        continue
    P = (p[:, :, None, :] + OFF[None, None, :, None] * nn[:, :, None, :]).reshape(-1, 3)
    Q = to137(P)
    Pm = P + MIS * np.repeat(tt[:, :, None, :], NS, 2).reshape(-1, 3)
    Qm = to137(Pm)
    k137, k137m = chunks_of(Q), chunks_of(Qm)
    if not fence_ok_keys(k137 | k137m):
        stats["fence"] += 1
        continue
    Qc, Pc = to137(c0[None])[0], c0
    if not D.read_byte_137(*map(int, np.rint(Qc)), scr) or not D.read_byte_78(*map(int, np.rint(Pc))):
        stats["zero_centre"] += 1
        continue
    t0 = time.time()
    g78 = sample(D.V78, P, chunks_of(P), pool).reshape(S, S, NS)
    g137 = sample(D.V137, Q, k137, pool).reshape(S, S, NS)
    g137m = sample(D.V137, Qm, k137m, pool).reshape(S, S, NS)
    sid = f"s{gi}_{gj}"
    np.savez(os.path.join(od, sid + ".npz"), g78=g78.astype(np.float16), g137=g137.astype(np.float16),
             g137m=g137m.astype(np.float16))
    valid = (g78.min(2) > 0.5) & (g137.min(2) > 0.5)
    rec = {"id": sid, "gi": gi, "gj": gj, "tile_r": gi * 20 // T, "tile_c": gj * 20 // T, "part": part,
           "centre_ref": c0.tolist(), "centre_137": Qc.tolist(), "canvas_centre_ij": [gi * 20, gj * 20],
           "frac_valid_px": float(valid.mean()), "frac_valid_px_misreg": float(((g78.min(2) > 0.5) & (g137m.min(2) > 0.5)).mean()),
           "n_chunks": [len(chunks_of(P)), len(k137), len(k137m)], "sec": round(time.time() - t0, 1)}
    chosen[part].append(rec)
    log(part, len(chosen[part]), rec)
    json.dump({"provenance": D.PROV, "serves": "PROTOCOL.md B1", "selection_stats": stats, "sites": chosen,
               "registration_model": "A (registration.json)", "offsets_vox": OFF.tolist(), "misreg_um": 250},
              open(os.path.join(D.REPO, "logs/sib/p4-purple/de/sites.json"), "w"), indent=1)
log("done", stats, len(chosen["fit"]), len(chosen["held"]))
