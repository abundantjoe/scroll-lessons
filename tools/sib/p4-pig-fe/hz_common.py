"""p4-highz shared geometry and fetch helpers (RULES.md DECL-P4-6; protocol logs/sib/p4-highz/PROTOCOL.md).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: CT bytes are reduced to histograms, counts and maxima; nothing is displayed or printed.
"""
import hashlib
import json
import os
import subprocess
import threading
import time

import numpy as np
import requests

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SRC_REF = "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b"
SV_NAME = "surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr"
N_SLICES, CENTRE = 116, 58
SHEET = (52, 65)      # slices 52..64, +-13.5 um
GAP_LO = (5, 32)      # slices 5..31, offsets 27..53 (60.96..119.67 um)
GAP_HI = (85, 112)    # slices 85..111
CH = 128
PLANE = CH * CH
UM = 2.258
OUT_SIDE = 1068
MATERIALS = {
    "E1": {"seg": "20260623141924-w010-027", "grid": "logs/sib/p4-tiles-b/e1/grid.json",
           "manifest": "logs/sib/p4-tiles-b/e1/manifest.json"},
    "C": {"seg": "20260623142658-w028-037", "grid": "logs/sib/p4-tiles-b/m2b/grid.json",
          "manifest": "logs/sib/p4-tiles-b/m2b/manifest.json"},
}

_tl = threading.local()


def session():
    s = getattr(_tl, "s", None)
    if s is None:
        s = _tl.s = requests.Session()
    return s


def get(url, rng=None, tries=7):
    h = {"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {}
    for i in range(tries):
        try:
            r = session().get(url, headers=h, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(30, 2 ** (i + 1)))


def git_json(path):
    return json.loads(subprocess.check_output(["git", "show", f"{SRC_REF}:{path}"]))


def sv_prefix(seg):
    return f"{BUCKET}/PHercParis4/segments/{seg}/{SV_NAME}"


def mesh_key(seg):
    return f"PHercParis4/segments/{seg}/mesh/{seg.split('-')[0]}-on-20260608103018-1.129um.tifxyz"


def load_material(name, scratch):
    """Grid, eligible tiles and mesh-valid vertex mask for a material. Mesh tifs are fetched, hashed, reduced, deleted."""
    import tifffile
    m = MATERIALS[name]
    g, man = git_json(m["grid"]), git_json(m["manifest"])
    seg = m["seg"]
    T = int(g["T_px"])
    H, W = (g.get("canvas_shape_L0_surface_volume") or g.get("canvas_shape"))
    tiles = []
    for t in man["tiles"]:
        fo = (t.get("stats") or {}).get("frac_mesh_points_outside_1129_volume", t.get("frac_outside"))
        if t["valid_fraction"] >= 0.5 and fo is not None and fo < 0.5:
            tiles.append({"r": t["r"], "c": t["c"], "valid_fraction_src": t["valid_fraction"], "frac_outside": fo})
    vpath = os.path.join(scratch, f"valid_{name}.npy")
    inputs = []
    if os.path.exists(vpath):
        valid = np.load(vpath)
        inputs = json.load(open(vpath + ".json"))
    else:
        arrs = []
        for a in "xyz":
            key = f"{mesh_key(seg)}/{a}.tif"
            b = get(f"{BUCKET}/{key}")
            inputs.append({"key": key, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
            p = os.path.join(scratch, f"mesh_{name}_{a}.tif")
            open(p, "wb").write(b)
            del b
            x = tifffile.imread(p)
            arrs.append((x != -1) & np.isfinite(x))
            del x
            os.remove(p)
        valid = arrs[0] & arrs[1] & arrs[2]
        np.save(vpath, valid)
        json.dump(inputs, open(vpath + ".json", "w"))
    return {"name": name, "seg": seg, "T": T, "H": int(H), "W": int(W), "grid": g, "tiles": tiles,
            "valid": valid, "mesh_inputs": inputs, "url0": sv_prefix(seg) + "/0/0"}


def tile_index_map(mat):
    nr, nc = mat["grid"]["tile_grid_rows_cols"]
    tid = -np.ones((nr, nc), np.int32)
    for i, t in enumerate(mat["tiles"]):
        tid[t["r"], t["c"]] = i
    return tid


def chunk_masks(mat, tid, yc, xc):
    """Per px of chunk (yc, xc): mesh-valid mask and eligible tile index (-1 = none); px beyond canvas invalid."""
    T, H, W, valid = mat["T"], mat["H"], mat["W"], mat["valid"]
    ys = yc * CH + np.arange(CH)
    xs = xc * CH + np.arange(CH)
    iny, inx = ys < H, xs < W
    gy = np.minimum(ys // 10, valid.shape[0] - 1)
    gx = np.minimum(xs // 10, valid.shape[1] - 1)
    v = valid[gy][:, gx] & iny[:, None] & inx[None, :]
    ti = tid[np.minimum(ys // T, tid.shape[0] - 1)][:, np.minimum(xs // T, tid.shape[1] - 1)]
    ti = np.where(v, ti, -1)
    return v, ti


def tile_chunks(mat, r, c):
    T, H, W = mat["T"], mat["H"], mat["W"]
    y1, x1 = min((r + 1) * T, H), min((c + 1) * T, W)
    return [(yc, xc) for yc in range(r * T // CH, (y1 - 1) // CH + 1) for xc in range(c * T // CH, (x1 - 1) // CH + 1)]


def hist_pct(h, q):
    """Smallest v with CDF(v) >= q for a 256-bin histogram."""
    c = np.cumsum(h, dtype=np.float64)
    if c[-1] == 0:
        return None
    return int(np.searchsorted(c, q * c[-1], side="left"))


def pct_block(h):
    hz = h.copy()
    hz[0] = 0
    n, nz = int(h.sum()), int(hz.sum())
    return {"n_voxels": n, "n_nonzero": nz, "frac_zero": h[0] / n if n else None,
            "frac_at_255_saturated": h[255] / n if n else None,
            "excl_zero": {k: hist_pct(hz, q) for k, q in (("p50", .5), ("p99", .99), ("p99.9", .999), ("p99.99", .9999))},
            "incl_zero": {k: hist_pct(h, q) for k, q in (("p50", .5), ("p99", .99), ("p99.9", .999), ("p99.99", .9999))},
            "mean_excl_zero": float((np.arange(256) * hz).sum() / nz) if nz else None}


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
