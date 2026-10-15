#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""PASS 2 seeds for PHerc0813 (tools/fl/BRIEF_PASS.md: auto-grow up to 4 segments seeded in the OUTER third of the
scroll radius). Numbers only; no image is viewed.

Method (fixed before any growth):
- Read the organizer surface-m7 L0 prediction (level 4 = 16x) from the open bucket, anonymously.
- For every level-4 z slice with surface voxels (>= 128), the centre is the centroid of the surface voxels and the
  radius R is the 99th percentile of their distance to it; centre and R are median-filtered over 9 slices.
  The bucket has no umbilicus for PHerc0813, so the surface-voxel centroid is the centre.
- Usable z: slices whose surface-voxel count is >= 50 % of the median. It is split into 4 equal bins; bin k gets
  azimuth target 45 + 90 k degrees and radius-fraction target 5/6 (middle of the outer third).
- In each bin, the level-4 surface voxel with r/R in [0.70, 0.95] nearest (in (r/R, angle) space) to the target
  is taken. It is refined at level 0 to the nearest voxel >= 128 in its 192^3 chunk. The seed must still have
  r/R >= 2/3 at level 0.
Usage: seeds.py OUT_JSON
"""
import json, sys
import numpy as np
import s3fs, zarr
from scipy.ndimage import median_filter

B = "vesuvius-challenge-open-data/PHerc0813"
SURF = f"{B}/representations/predictions/surfaces/20250821151723-surface-20260413222639-surface-m7-L0-th0.2.zarr"
VOLM = f"{B}/volumes/20250821151723-9.362um-1.2m-113keV-masked.zarr/metadata.json"
fs = s3fs.S3FileSystem(anon=True)


def find(o, k):
    if isinstance(o, dict):
        if k in o:
            return o[k]
        for v in o.values():
            x = find(v, k)
            if x is not None:
                return x
    return None


def main():
    vox_um = float(find(json.loads(fs.cat(VOLM)), "samplePixelSize")) * 1000.0
    g = zarr.open_group(zarr.storage.FSStore(SURF, fs=fs), mode="r")
    a4 = g["4"][:] >= 128                         # (z, y, x), level 4
    s4 = 16
    n = a4.reshape(a4.shape[0], -1).sum(1)
    zs = np.nonzero(n > 0)[0]
    cx = np.full(a4.shape[0], np.nan); cy = cx.copy(); R = cx.copy()
    for z in zs:
        yy, xx = np.nonzero(a4[z])
        cx[z], cy[z] = xx.mean(), yy.mean()
        R[z] = np.percentile(np.hypot(xx - cx[z], yy - cy[z]), 99)
    for arr in (cx, cy, R):
        ok = np.isfinite(arr)
        arr[ok] = median_filter(arr[ok], 9, mode="nearest")
    med = np.median(n[zs])
    use = np.nonzero(n >= 0.5 * med)[0]
    z0, z1 = int(use.min()), int(use.max())
    edges = np.linspace(z0, z1 + 1, 5)
    seeds = []
    for k in range(4):
        tgt_a = np.radians(45 + 90 * k); tgt_r = 5 / 6
        best = None
        for z in range(int(edges[k]), int(edges[k + 1])):
            if not np.isfinite(R[z]) or n[z] < 0.5 * med:
                continue
            yy, xx = np.nonzero(a4[z])
            r = np.hypot(xx - cx[z], yy - cy[z]) / R[z]
            ang = np.arctan2(yy - cy[z], xx - cx[z])
            m = (r >= 0.70) & (r <= 0.95)
            if not m.any():
                continue
            d = np.abs(r[m] - tgt_r) + np.abs(np.angle(np.exp(1j * (ang[m] - tgt_a)))) / np.pi
            dz = abs(z - (edges[k] + edges[k + 1]) / 2) / (edges[k + 1] - edges[k])
            i = int(np.argmin(d)); score = float(d[i] + dz)
            if best is None or score < best[0]:
                best = (score, z, int(xx[m][i]), int(yy[m][i]))
        _, z, x, y = best
        # refine at level 0 inside the 192^3 chunk that holds the level-4 voxel centre
        p0 = np.array([x, y, z]) * s4 + s4 // 2
        a0 = g["0"]
        c = [(int(p0[2]) // 192) * 192, (int(p0[1]) // 192) * 192, (int(p0[0]) // 192) * 192]
        blk = a0[c[0]:c[0] + 192, c[1]:c[1] + 192, c[2]:c[2] + 192]
        zz, yy, xx = np.nonzero(blk >= 128)
        if zz.size == 0:
            seeds.append(dict(k=k, ok=False, reason="no level-0 voxel >= 128 in chunk")); continue
        q = np.stack([xx + c[2], yy + c[1], zz + c[0]], 1)
        j = int(np.argmin(np.linalg.norm(q - p0, axis=1)))
        sx, sy, sz = (int(v) for v in q[j])
        z4 = min(max(sz // s4, 0), len(R) - 1)
        rf = float(np.hypot(sx / s4 - cx[z4], sy / s4 - cy[z4]) / R[z4])
        seeds.append(dict(k=k, ok=bool(rf >= 2 / 3), x=sx, y=sy, z=sz, value=int(blk[zz[j], yy[j], xx[j]]),
                          r_frac=round(rf, 4), angle_deg=round(float(np.degrees(np.arctan2(sy / s4 - cy[z4], sx / s4 - cx[z4]))), 1),
                          z_frac=round((sz / s4 - z0) / max(z1 - z0, 1), 4), R_vox_level0=round(float(R[z4] * s4), 1),
                          centre_level0=[round(float(cx[z4] * s4), 1), round(float(cy[z4] * s4), 1)],
                          refine_dist_vox=round(float(np.linalg.norm(q[j] - p0)), 1)))
    out = dict(rule=__doc__, voxel_um_metadata_json=vox_um, surface=SURF, level4_shape=list(a4.shape),
               usable_z_level0=[z0 * s4, (z1 + 1) * s4], seeds=seeds)
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rule"}))


if __name__ == "__main__":
    main()
