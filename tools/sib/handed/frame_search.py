# Provenance: Project HERCULES | owner the owner | [id removed]
"""Joint 3-D translation search: is there ONE offset (dx, dy, dz) that puts a
group of organizer meshes on non-zero (masked-in) CT of their declared
volume? Level-4 chunks are read into memory only (never written); metric =
fraction of sampled vertices on non-zero CT, per mesh; objective = the
minimum over meshes. Numbers only.

Usage: python frame_search.py SCROLL VOLUME_PREFIX OUT_JSON SEGMENT_PREFIX [SEGMENT_PREFIX ...]
"""
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

B = "vesuvius-challenge-open-data"
S3DIR = Path("/work/handed/s3")
scroll, pre, out, *segs = sys.argv[1:]
assert scroll != "PHerc0841"
LEVEL = 4
f = 2 ** LEVEL
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=20))
za = json.loads(s3.get_object(Bucket=B, Key=f"{pre}/{LEVEL}/.zarray")["Body"].read())
Z, Y, X = za["shape"]
c = za["chunks"][0]
t0 = time.time()
vol = np.zeros((Z, Y, X), np.uint8)
keys = [(i, j, k) for i in range(-(-Z // c)) for j in range(-(-Y // c)) for k in range(-(-X // c))]


def fetch(kk):
    try:
        b = s3.get_object(Bucket=B, Key=f"{pre}/{LEVEL}/" + "/".join(map(str, kk)))["Body"].read()
        return kk, np.frombuffer(b, np.uint8).reshape(c, c, c)
    except s3.exceptions.NoSuchKey:
        return kk, None


with ThreadPoolExecutor(16) as ex:
    for (i, j, k), a in ex.map(fetch, keys):
        if a is not None:
            zz, yy, xx = min(c, Z - i * c), min(c, Y - j * c), min(c, X - k * c)
            vol[i * c:i * c + zz, j * c:j * c + yy, k * c:k * c + xx] = a[:zz, :yy, :xx]
nz = vol > 0
del vol
pts = []
names = []
for d in sorted(S3DIR.glob(f"{scroll}/segments/*/mesh/*.tifxyz")):
    name = d.parts[len(S3DIR.parts) + 2]
    if any(name.startswith(s) for s in segs):
        p = read_tifxyz(d).points.astype(np.float64)
        pts.append(p[valid_mask(p)][::8] / f)
        names.append(name)


def occ(P, dx, dy, dz):
    i = np.floor(P + np.array([dx, dy, dz]) / f).astype(np.int64)
    ok = (i[:, 0] >= 0) & (i[:, 0] < X) & (i[:, 1] >= 0) & (i[:, 1] < Y) & (i[:, 2] >= 0) & (i[:, 2] < Z)
    v = np.zeros(len(P), bool)
    q = i[ok]
    v[ok] = nz[q[:, 2], q[:, 1], q[:, 0]]
    return v.mean()


grid_xy = np.arange(-1536, 1537, 128)
grid_z = np.arange(-4096, 4097, 128)
best = (-1, None)
for dz in grid_z:
    for dy in grid_xy:
        for dx in grid_xy:
            m = min(occ(P, dx, dy, dz) for P in pts)
            if m > best[0]:
                best = (m, (int(dx), int(dy), int(dz)))
# refine
bx, by, bz = best[1]
for dz in range(bz - 128, bz + 129, 16):
    for dy in range(by - 128, by + 129, 16):
        for dx in range(bx - 128, bx + 129, 16):
            m = min(occ(P, dx, dy, dz) for P in pts)
            if m > best[0]:
                best = (m, (dx, dy, dz))
res = dict(scroll=scroll, volume=pre, level=LEVEL, segments=names, seconds=round(time.time() - t0, 1),
           occupancy_at_zero=[round(occ(P, 0, 0, 0), 4) for P in pts], best_min_occupancy=round(best[0], 4),
           best_offset_xyz_level0=best[1], occupancy_at_best=[round(occ(P, *best[1]), 4) for P in pts],
           search=dict(xy=[int(grid_xy[0]), int(grid_xy[-1]), 128], z=[int(grid_z[0]), int(grid_z[-1]), 128], refine_step=16))
Path(out).write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != "segments"}))
