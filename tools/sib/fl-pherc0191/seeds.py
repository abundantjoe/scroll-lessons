# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters PHerc0191: GrowPatch seed candidates at mid radius (DECL-FL-1 item 1).

Numbers only. Reads the organizer surface prediction (surface-m7, OME-Zarr, blosc/zstd u8)
anonymously over HTTPS, one z slab at level 3 (8x), finds the surface-pixel centroid and
radial extent r_max (p98 of surface-pixel distances), then for N angles picks the surface
pixel nearest to (0.5 r_max, theta) inside the annulus 0.45..0.55 r_max, and refines it at
level 0 to the nearest voxel >= 128 (falls back to the nearest nonzero voxel).
Output: JSON list of {k, theta_deg, x, y, z, value_l0, r_frac} (x y z = L0 voxel indices,
the vc_grow_seg_from_seed --seed order).
"""
import json, math, sys, argparse
import numpy as np, requests, numcodecs

BASE = ("https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0191/representations/predictions/"
        "surfaces/20250821151635-surface-20260413222639-surface-m7-L0-th0.2.zarr")
S = requests.Session()


def meta(level):
    return S.get(f"{BASE}/{level}/.zarray", timeout=60).json()


def chunk(level, m, cz, cy, cx):
    r = S.get(f"{BASE}/{level}/{cz}/{cy}/{cx}", timeout=120)
    ch = m["chunks"]
    if r.status_code in (403, 404):
        return np.zeros(ch, np.uint8)
    r.raise_for_status()
    raw = numcodecs.get_codec(m["compressor"]).decode(r.content)
    return np.frombuffer(raw, np.uint8).reshape(ch)


def zslice(level, z):
    m = meta(level)
    Z, Y, X = m["shape"]; c = m["chunks"]
    out = np.zeros((Y, X), np.uint8)
    cz, oz = divmod(z, c[0])
    for cy in range(-(-Y // c[1])):
        for cx in range(-(-X // c[2])):
            a = chunk(level, m, cz, cy, cx)[oz]
            y0, x0 = cy * c[1], cx * c[2]
            h, w = min(c[1], Y - y0), min(c[2], X - x0)
            out[y0:y0 + h, x0:x0 + w] = a[:h, :w]
    return out, m


def refine_l0(x, y, z, rad=24):
    m = meta(0); c = m["chunks"]
    cz, cy, cx = z // c[0], y // c[1], x // c[2]
    a = chunk(0, m, cz, cy, cx)
    lz, ly, lx = z - cz * c[0], y - cy * c[1], x - cx * c[2]
    sl = [slice(max(0, v - rad), min(c[i], v + rad + 1)) for i, v in enumerate((lz, ly, lx))]
    sub = a[tuple(sl)]
    for thr in (128, 1):
        idx = np.argwhere(sub >= thr)
        if len(idx):
            d = np.linalg.norm(idx + [s.start for s in sl] - [lz, ly, lx], axis=1)
            p = idx[int(np.argmin(d))] + [s.start for s in sl]
            v = int(a[tuple(p)])
            return int(cx * c[2] + p[2]), int(cy * c[1] + p[1]), int(cz * c[0] + p[0]), v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zfrac", type=float, nargs="+", default=[0.5])
    ap.add_argument("--angles", type=float, nargs="+", default=[45, 135, 225, 315, 0, 90, 180, 270])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    L, f = 3, 8
    m3 = meta(L)
    seeds, k = [], 0
    for zf in a.zfrac:
        z3 = int(round(zf * (m3["shape"][0] - 1)))
        sl, _ = zslice(L, z3)
        yy, xx = np.nonzero(sl)
        if len(yy) < 100:
            continue
        cy, cx = yy.mean(), xx.mean()
        r = np.hypot(yy - cy, xx - cx)
        rmax = float(np.percentile(r, 98))
        th = np.degrees(np.arctan2(yy - cy, xx - cx)) % 360
        for ang in a.angles:
            ty, tx = cy + 0.5 * rmax * math.sin(math.radians(ang)), cx + 0.5 * rmax * math.cos(math.radians(ang))
            dth = np.abs((th - ang + 180) % 360 - 180)
            ok = (np.abs(r / rmax - 0.5) < 0.05) & (dth < 8)
            if not ok.any():
                continue
            order = np.argsort(np.hypot(yy[ok] - ty, xx[ok] - tx))
            for j in order[:20]:
                y3, x3 = int(yy[ok][j]), int(xx[ok][j])
                ref = refine_l0(x3 * f + f // 2, y3 * f + f // 2, z3 * f + f // 2)
                if ref:
                    x, y, z, v = ref
                    seeds.append(dict(k=k, theta_deg=ang, zfrac=zf, x=x, y=y, z=z, value_l0=v,
                                      r_frac=round(float(r[ok][j] / rmax), 4),
                                      centroid_l0=[round(cx * f, 1), round(cy * f, 1)], rmax_l0=round(rmax * f, 1)))
                    k += 1
                    break
    json.dump(dict(source=BASE, level_used=L, seeds=seeds), open(a.out, "w"), indent=1)
    print(json.dumps(dict(n=len(seeds))))
    return 0 if seeds else 1


if __name__ == "__main__":
    sys.exit(main())
