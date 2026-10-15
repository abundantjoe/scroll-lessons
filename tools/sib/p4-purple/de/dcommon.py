"""p4-purple-de shared helpers: fetch, mesh load, composed affine, and the HARD FENCE on every 137 keV read.

Provenance: Project HERCULES | owner the owner | [id removed]
Protocol: logs/sib/p4-purple/de/PROTOCOL.md. Numbers only: CT bytes are reduced to statistics; nothing is displayed.
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
V137 = "20260323153942-2.400um-0.2m-137keV-masked"
V78 = "20260411134726-2.400um-0.2m-78keV-masked"
SHAPE = {V137: (6625, 8431, 8431), V78: (75784, 32693, 32693)}
CH = 128
SEG_E2 = "20260701183124-w010-027"
SEG_C2 = "20260701183125-w028-037"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
SCANS_REF = "origin/claude/gifted-bell-gavnl5-sib-p4-highz"
FENCE_MARGIN_VOX = 833  # 2 mm at 2.4 um

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


def git_json(path, ref):
    return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{ref}:{path}"]))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def A4(M):
    return np.vstack([np.asarray(M, float), [0, 0, 0, 1]])


def ref_to_137():
    """4x4 matrix mapping V78 level-0 xyz (REF, mesh frame) to V137 level-0 xyz (published composed affine)."""
    sc = git_json("logs/sib/p4-highz/scans.json", SCANS_REF)
    to_ref = np.linalg.inv(A4(sc["volumes"][V78]["registration"]["matrix_moving_to_fixed_xyz"])) @ A4(
        sc["volumes"][V137]["registration"]["matrix_moving_to_fixed_xyz"])
    return np.linalg.inv(to_ref)


def load_mesh(seg, scratch, frame="20260411134726-2.4um"):
    """Returns (xyz float32 array HxWx3 with NaN for invalid, inputs list). Fetched tifs are hashed and deleted."""
    import tifffile
    key = f"PHercParis4/segments/{seg}/mesh/{seg.split('-')[0]}-on-{frame}.tifxyz"
    cache = os.path.join(scratch, f"mesh_{seg}.npy")
    if os.path.exists(cache):
        return np.load(cache, mmap_mode="r"), json.load(open(cache + ".json"))
    arrs, inputs = [], []
    for a in "xyz":
        b = get(f"{BUCKET}/{key}/{a}.tif")
        inputs.append({"key": f"{key}/{a}.tif", "bytes": len(b), "sha256": sha(b)})
        p = os.path.join(scratch, f"m_{a}.tif")
        open(p, "wb").write(b)
        del b
        arrs.append(tifffile.imread(p).astype(np.float32))
        os.remove(p)
    ok = np.isfinite(arrs[0]) & np.isfinite(arrs[1]) & np.isfinite(arrs[2]) & (arrs[0] != -1) & (arrs[1] != -1) & (arrs[2] != -1)
    xyz = np.stack(arrs, -1)
    del arrs
    xyz[~ok] = np.nan
    np.save(cache, xyz)
    json.dump(inputs, open(cache + ".json", "w"))
    return xyz, inputs


def map_pts(M, P):
    return (M[:3, :3] @ np.asarray(P, np.float64).T).T + M[:3, 3]


def inside_extent(Q, shape_zyx=SHAPE[V137]):
    Z, Y, X = shape_zyx
    return (Q[:, 0] >= 0) & (Q[:, 0] < X) & (Q[:, 1] >= 0) & (Q[:, 1] < Y) & (Q[:, 2] >= 0) & (Q[:, 2] < Z)


def inside_cyl(Q, c=4215.0, R=4215.0):
    return (Q[:, 0] - c) ** 2 + (Q[:, 1] - c) ** 2 <= R * R


# ---------------------------------------------------------------- HARD FENCE (PROTOCOL amendment A-1)
class FenceError(Exception):
    pass


D_F = 146  # voxels, 0.35 mm
_FENCE = {}


def fence(scratch):
    """KD-tree of every valid w010-027 2.4 um mesh vertex (all rows and columns) mapped into the 137 keV frame and within
    2 mm of its extent. Geometry only."""
    if _FENCE:
        return _FENCE
    from scipy.spatial import cKDTree
    cache = os.path.join(scratch, "fence_F.npy")
    if os.path.exists(cache):
        F = np.load(cache)
    else:
        xyz, _ = load_mesh(SEG_E2, scratch)
        M = ref_to_137()
        parts = []
        g = FENCE_MARGIN_VOX
        for i0 in range(0, xyz.shape[0], 256):
            P = np.asarray(xyz[i0:i0 + 256]).reshape(-1, 3)
            P = P[np.isfinite(P[:, 0])]
            Q = map_pts(M, P)
            m = ((Q[:, 0] > -g) & (Q[:, 0] < 8431 + g) & (Q[:, 1] > -g) & (Q[:, 1] < 8431 + g) & (Q[:, 2] > -g)
                 & (Q[:, 2] < 6625 + g))
            parts.append(Q[m])
        F = np.concatenate(parts).astype(np.float64)
        np.save(cache, F)
    _FENCE.update({"F": F, "tree": cKDTree(F), "sha256_F_float64": sha(F.tobytes()), "n_F": len(F)})
    path = os.path.join(REPO, "logs/sib/p4-purple/de/fence.json")
    if not os.path.exists(path):
        json.dump({"provenance": PROV, "rule": "PROTOCOL amendment A-1", "D_f_vox": D_F, "n_F": len(F),
                   "sha256_F_float64": _FENCE["sha256_F_float64"], "segment": SEG_E2,
                   "F_bbox_xyz": [F.min(0).tolist(), F.max(0).tolist()]}, open(path, "w"), indent=1)
    return _FENCE


def fence_dist(x0, x1, y0, y1, z0, z1, scratch):
    """Min distance (voxels) from the fenced set F to the box [x0,x1) x [y0,y1) x [z0,z1) (inf if > search radius)."""
    f = fence(scratch)
    c = np.array([(x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2, (z0 + z1 - 1) / 2])
    h = np.array([(x1 - 1 - x0) / 2, (y1 - 1 - y0) / 2, (z1 - 1 - z0) / 2])
    idx = f["tree"].query_ball_point(c, float(np.linalg.norm(h) + D_F))
    if not idx:
        return np.inf
    d = np.maximum(np.abs(f["F"][idx] - c) - h, 0)
    return float(np.sqrt((d ** 2).sum(1)).min())


def fence_ok_chunks(x0, x1, y0, y1, z0, z1, scratch):
    """True if the chunk-aligned cover of the box (what read_box actually fetches) passes the fence."""
    a = lambda v: (max(0, v) // CH) * CH
    b = lambda v: ((v - 1) // CH + 1) * CH
    return fence_dist(a(x0), b(x1), a(y0), b(y1), a(z0), b(z1), scratch) >= D_F


def fence_check(x0, x1, y0, y1, z0, z1, scratch):
    """Raise FenceError if any point of the V137 level-0 box is closer than D_F voxels to a w010-027 vertex."""
    if fence_dist(x0, x1, y0, y1, z0, z1, scratch) < D_F:
        raise FenceError((x0, x1, y0, y1, z0, z1))


def read_byte_137(xi, yi, zi, scratch):
    fence_check(xi, xi + 1, yi, yi + 1, zi, zi + 1, scratch)
    return _read_byte(V137, xi, yi, zi)


def read_byte_78(xi, yi, zi):
    return _read_byte(V78, xi, yi, zi)


def _read_byte(v, xi, yi, zi):
    Z, Y, X = SHAPE[v]
    if not (0 <= xi < X and 0 <= yi < Y and 0 <= zi < Z):
        return None
    url = f"{BUCKET}/PHercParis4/volumes/{v}.zarr/0/{zi // CH}/{yi // CH}/{xi // CH}"
    off = ((zi % CH) * CH + (yi % CH)) * CH + (xi % CH)
    b = get(url, (off, off))
    return 0 if b is None else b[0]


def read_chunk(v, zc, yc, xc, scratch):
    if v == V137:
        fence_check(xc * CH, (xc + 1) * CH, yc * CH, (yc + 1) * CH, zc * CH, (zc + 1) * CH, scratch)
    b = get(f"{BUCKET}/PHercParis4/volumes/{v}.zarr/0/{zc}/{yc}/{xc}")
    if b is None:
        return None
    return np.frombuffer(b, np.uint8).reshape(CH, CH, CH)


def read_box(v, x0, y0, z0, n, scratch, cache=None):
    """Level-0 box [z0,z0+n) x [y0,y0+n) x [x0,x0+n) as uint8 (zyx); missing chunks and out-of-volume are 0."""
    Z, Y, X = SHAPE[v]
    if v == V137:
        fence_check(x0, x0 + n, y0, y0 + n, z0, z0 + n, scratch)
    out = np.zeros((n, n, n), np.uint8)
    for zc in range(max(0, z0) // CH, (min(Z, z0 + n) - 1) // CH + 1):
        for yc in range(max(0, y0) // CH, (min(Y, y0 + n) - 1) // CH + 1):
            for xc in range(max(0, x0) // CH, (min(X, x0 + n) - 1) // CH + 1):
                key = (v, zc, yc, xc)
                c = cache.get(key) if cache is not None else None
                if c is None:
                    c = read_chunk(v, zc, yc, xc, scratch)
                    if c is None:
                        c = np.zeros((CH, CH, CH), np.uint8)
                    if cache is not None:
                        cache[key] = c
                zs, ys, xs = zc * CH, yc * CH, xc * CH
                a0 = (max(z0, zs), max(y0, ys), max(x0, xs))
                a1 = (min(z0 + n, zs + CH), min(y0 + n, ys + CH), min(x0 + n, xs + CH))
                if min(a1[i] - a0[i] for i in range(3)) <= 0:
                    continue
                out[a0[0] - z0:a1[0] - z0, a0[1] - y0:a1[1] - y0, a0[2] - x0:a1[2] - x0] = \
                    c[a0[0] - zs:a1[0] - zs, a0[1] - ys:a1[1] - ys, a0[2] - xs:a1[2] - xs]
    return out
