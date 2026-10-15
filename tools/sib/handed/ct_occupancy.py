# Provenance: Project HERCULES | owner the owner | [id removed]
"""Does an organizer mesh lie on the scroll in its declared volume frame?

For each mesh: fraction of valid vertices outside the volume bounds, and on
zero (masked-out) CT at pyramid level L (nearest level-L voxel), and the mean
CT value at the vertices; then the same metrics after shifting the mesh by
dz in [-dz_max, dz_max] (level-0 voxels), to test a frame offset. Only the
level-L chunks the (shifted) meshes touch are read, held in memory, and
discarded; no CT is written anywhere. Numbers only.

Usage: python ct_occupancy.py SCROLL VOLUME_PREFIX OUT_JSON [--level 4] [--dz-max 4000] [--dz-step 32]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

BUCKET = "vesuvius-challenge-open-data"
S3DIR = Path("/work/handed/s3")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scroll")
    ap.add_argument("prefix")
    ap.add_argument("out")
    ap.add_argument("--level", type=int, default=4)
    ap.add_argument("--dz-max", type=int, default=4000)
    ap.add_argument("--dz-step", type=int, default=32)
    ap.add_argument("--glob", default="*.tifxyz")
    ap.add_argument("--dilate", type=int, default=0, help="also report non-zero within +-k level-L voxels")
    a = ap.parse_args()
    if a.scroll == "PHerc0841":
        raise SystemExit("PHerc0841 CT sampling near meshes is not allowed here (J windows)")
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=20,
                                          retries={"max_attempts": 8, "mode": "standard"}))
    pre = a.prefix.rstrip("/")
    za = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{pre}/{a.level}/.zarray")["Body"].read())
    Z, Y, X = za["shape"]
    cz, cy, cx = za["chunks"]
    assert za.get("compressor") is None and za.get("order", "C") == "C"
    sep = za.get("dimension_separator", ".")
    f = 2 ** a.level
    vol_id = pre.split("/")[-1].split("-")[0]
    meshes = []
    for d in sorted(S3DIR.glob(f"{a.scroll}/segments/*/mesh/{a.glob}")):
        if f"-on-{vol_id}-" not in d.name:
            continue
        m = read_tifxyz(d)
        p = m.points.astype(np.float64)
        ok = valid_mask(p)
        meshes.append((d.parts[len(S3DIR.parts) + 2], p[ok][::4]))  # every 4th valid vertex
    shifts = np.arange(-a.dz_max, a.dz_max + 1, a.dz_step)
    # chunks needed over all shifts
    need = set()
    for _, P in meshes:
        ix = np.clip((P[:, 0] / f).astype(int), 0, X - 1) // cx
        iy = np.clip((P[:, 1] / f).astype(int), 0, Y - 1) // cy
        zmin, zmax = (P[:, 2].min() - a.dz_max) / f, (P[:, 2].max() + a.dz_max) / f
        for kz in range(max(0, int(zmin) // cz), min(Z - 1, int(zmax)) // cz + 1):
            for kyx in set(zip(iy.tolist(), ix.tolist())):
                need.add((kz, *kyx))
    t0 = time.time()

    def fetch(k):
        key = f"{pre}/{a.level}/" + sep.join(map(str, k))
        for i in range(5):
            try:
                b = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
                return k, np.frombuffer(b, np.uint8).reshape(cz, cy, cx)
            except s3.exceptions.NoSuchKey:
                return k, None
            except Exception:
                time.sleep(2 ** (i + 1))
        raise RuntimeError(key)

    cache = {}
    with ThreadPoolExecutor(16) as ex:
        for k, arr in ex.map(fetch, sorted(need)):
            cache[k] = arr

    def sample(P):
        i = np.floor(P / f).astype(np.int64)  # level-L voxel containing the point
        inside = (i[:, 0] >= 0) & (i[:, 0] < X) & (i[:, 1] >= 0) & (i[:, 1] < Y) & (i[:, 2] >= 0) & (i[:, 2] < Z)
        v = np.zeros(len(P), np.float64)
        ii = i[inside]
        vals = np.zeros(len(ii))
        keys = np.stack([ii[:, 2] // cz, ii[:, 1] // cy, ii[:, 0] // cx], 1)
        for k in {tuple(x) for x in keys.tolist()}:
            sel = np.all(keys == k, axis=1)
            arr = cache.get(k)
            if arr is None:
                continue  # absent chunk = fill value 0
            q = ii[sel]
            vals[sel] = arr[q[:, 2] % cz, q[:, 1] % cy, q[:, 0] % cx]
        v[inside] = vals
        return inside, v

    out = dict(scroll=a.scroll, volume=pre, level=a.level, shape_level=[Z, Y, X], n_chunks=len(need),
               seconds_fetch=round(time.time() - t0, 1), dz=shifts.tolist(), meshes=[])
    for name, P in meshes:
        inside0, v0 = sample(P)
        occ, meanv = [], []
        for dz in shifts:
            Q = P.copy()
            Q[:, 2] += dz
            ins, v = sample(Q)
            occ.append(float((v > 0).mean()))
            meanv.append(float(v.mean()))
        occ = np.array(occ)
        dil = None
        if a.dilate:
            hit = np.zeros(len(P), bool)
            k = a.dilate
            for ox in range(-k, k + 1):
                for oy in range(-k, k + 1):
                    for oz in range(-k, k + 1):
                        _, vv = sample(P + f * np.array([ox, oy, oz], float))
                        hit |= vv > 0
            dil = float(1 - hit.mean())
        meanv = np.array(meanv)
        j = int(np.argmax(meanv))
        out["meshes"].append(dict(segment=name, n_vertices_sampled=int(len(P)), z_range=[float(P[:, 2].min()), float(P[:, 2].max())],
                                  frac_outside=float(1 - inside0.mean()), frac_zero_ct=float((v0 == 0).mean()),
                                  frac_zero_ct_dilated=dil, dilate=a.dilate,
                                  frac_zero_ct_inside=float((v0[inside0] == 0).mean()) if inside0.any() else None,
                                  mean_ct=float(v0.mean()), best_dz_by_mean_ct=int(shifts[j]), mean_ct_at_best=float(meanv[j]),
                                  frac_nonzero_at_best=float(occ[j]), occupancy_curve=[round(x, 4) for x in occ],
                                  mean_ct_curve=[round(x, 2) for x in meanv]))
        r = out["meshes"][-1]
        print(name[:34], "outside %.3f zero %.3f mean %.1f | best dz %d mean %.1f nonzero %.3f" % (
            r["frac_outside"], r["frac_zero_ct"], r["mean_ct"], r["best_dz_by_mean_ct"], r["mean_ct_at_best"], r["frac_nonzero_at_best"]), flush=True)
    Path(a.out).write_text(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
