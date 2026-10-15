# Provenance: Project HERCULES | owner the owner | [id removed]
"""Census step 4: seed plan per volume (geometry and CT mask only; no tracing,
no ink model).

Design (fixed before any placement was computed):
  * 20 z-levels evenly spaced over [z_lo + 1150, z_hi - 1150], where [z_lo, z_hi]
    is the scroll's z extent (level-4 slices whose filled-mask area is >= 0.25 x
    the median non-empty area);
  * 3 angles per level, 120 deg apart, the triplet rotated by (k mod 3) x 40 deg
    so that seeds of adjacent levels are never stacked at the same angle;
  * wrap fraction f = 0.35 + 0.35 * frac(0.5 + n * 0.6180339887), n = 3k + a
    (golden-ratio sequence: seeds sharing an angle every 3rd level get radii
    far apart), measured on the ray from the centre to the CT-mask boundary;
  * planned point must lie in the CT mask eroded by 48 level-0 vox (3 px at
    level 4) and >= 320 vox from every other seed; otherwise f, then the angle,
    is nudged by the smallest step that satisfies both (recorded);
  * the seed is the m7 voxel with value 255 nearest the planned point (level 0,
    Euclidean), searched in a +-64 then +-160 vox box.
Duplicates: for every seed pair whose trace neighbourhoods could overlap
(surface distance <= 2 x reach, reach = generations x step 20 vox), a radial
sheet-following walk on the level-0 m7 prediction from seed i to seed j
decides whether they sit on the same sheet within 3 vox.
Numbers only: no image is written or displayed.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import OrderedDict

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
from centre import centroid_curve, load_shape, scroll_z_extent, umbilicus_curve  # noqa: E402

BUCKET = "vesuvius-challenge-open-data"
M7 = "surface-20260413222639-surface-m7-L0-th0.2"
N_LEVELS, N_ANG = 20, 3
F_LO, F_HI = 0.35, 0.70
MIN_SEP = 320.0
ERODE_L0 = 48
Z_MARGIN = 1150
PHI = 0.6180339887498949
STEP_VOX = 20.0  # tracer step (archive meta: scale 0.05 -> 20 vox per grid step)
DUP_TOL = 3.0
WALK_STEP, WALK_SHIFT = 4.0, 3.0  # walker v2 settings (validated in validate_walker.py)


def s3client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16,
                                            retries={"max_attempts": 8, "mode": "adaptive"}))


class M7Volume:
    """Level-0 m7 prediction with an LRU chunk cache (blosc/zstd 192^3 chunks)."""

    def __init__(self, scroll, vid, max_chunks=220):
        import numcodecs

        self.s3 = s3client()
        self.pre = f"{scroll}/representations/predictions/surfaces/{vid}-{M7}.zarr/0"
        za = json.loads(self.s3.get_object(Bucket=BUCKET, Key=self.pre + "/.zarray")["Body"].read())
        self.shape = za["shape"]
        self.ch = za["chunks"]
        self.codec = numcodecs.get_codec(za["compressor"])
        self.sep = za.get("dimension_separator", ".")
        self.cache: OrderedDict = OrderedDict()
        self.max_chunks = max_chunks
        self.fetched = 0
        self.fetched_bytes = 0

    def chunk(self, iz, iy, ix):
        k = (iz, iy, ix)
        if k in self.cache:
            self.cache.move_to_end(k)
            return self.cache[k]
        try:
            raw = self.s3.get_object(Bucket=BUCKET, Key=self.pre + "/" + self.sep.join(map(str, k)))["Body"].read()
            a = np.frombuffer(self.codec.decode(raw), np.uint8).reshape(self.ch)
            self.fetched_bytes += len(raw)
        except self.s3.exceptions.NoSuchKey:
            a = None
        self.fetched += 1
        self.cache[k] = a
        if len(self.cache) > self.max_chunks:
            self.cache.popitem(last=False)
        return a

    def prefetch(self, keys, workers=16):
        """Fetch missing chunks in parallel (keys = (iz, iy, ix))."""
        from concurrent.futures import ThreadPoolExecutor

        Z, Y, X = self.shape
        cz, cy, cx = self.ch
        todo = [k for k in dict.fromkeys(keys) if k not in self.cache and 0 <= k[0] <= (Z - 1) // cz
                and 0 <= k[1] <= (Y - 1) // cy and 0 <= k[2] <= (X - 1) // cx][: self.max_chunks - 8]

        def get(k):
            try:
                raw = self.s3.get_object(Bucket=BUCKET, Key=self.pre + "/" + self.sep.join(map(str, k)))["Body"].read()
                return k, raw
            except self.s3.exceptions.NoSuchKey:
                return k, None

        with ThreadPoolExecutor(workers) as ex:
            for k, raw in ex.map(get, todo):
                a = None if raw is None else np.frombuffer(self.codec.decode(raw), np.uint8).reshape(self.ch)
                self.fetched += 1
                self.fetched_bytes += len(raw) if raw else 0
                self.cache[k] = a
                if len(self.cache) > self.max_chunks:
                    self.cache.popitem(last=False)

    def keys_for_points(self, pts):
        cz, cy, cx = self.ch
        pts = np.asarray(np.rint(pts), int)
        return [tuple(r) for r in np.unique(np.c_[pts[:, 2] // cz, pts[:, 1] // cy, pts[:, 0] // cx], axis=0).tolist()]

    def box(self, z0, z1, y0, y1, x0, x1):
        """uint8 box [z0,z1) x [y0,y1) x [x0,x1), clipped to the volume (zeros outside)."""
        Z, Y, X = self.shape
        out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
        cz, cy, cx = self.ch
        for iz in range(max(0, z0) // cz, (min(Z, z1) - 1) // cz + 1):
            for iy in range(max(0, y0) // cy, (min(Y, y1) - 1) // cy + 1):
                for ix in range(max(0, x0) // cx, (min(X, x1) - 1) // cx + 1):
                    a = self.chunk(iz, iy, ix)
                    if a is None:
                        continue
                    gz0, gy0, gx0 = iz * cz, iy * cy, ix * cx
                    sz0, sz1 = max(z0, gz0), min(z1, gz0 + cz)
                    sy0, sy1 = max(y0, gy0), min(y1, gy0 + cy)
                    sx0, sx1 = max(x0, gx0), min(x1, gx0 + cx)
                    out[sz0 - z0:sz1 - z0, sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = \
                        a[sz0 - gz0:sz1 - gz0, sy0 - gy0:sy1 - gy0, sx0 - gx0:sx1 - gx0]
        return out

    def points(self, pts):
        """Values at integer level-0 points (N, 3) given as (x, y, z)."""
        pts = np.asarray(np.rint(pts), int)
        Z, Y, X = self.shape
        cz, cy, cx = self.ch
        v = np.zeros(len(pts), np.uint8)
        ok = (pts[:, 0] >= 0) & (pts[:, 0] < X) & (pts[:, 1] >= 0) & (pts[:, 1] < Y) & (pts[:, 2] >= 0) & (pts[:, 2] < Z)
        idx = np.nonzero(ok)[0]
        keys = np.c_[pts[idx, 2] // cz, pts[idx, 1] // cy, pts[idx, 0] // cx]
        for k in {tuple(r) for r in keys.tolist()}:
            a = self.chunk(*k)
            if a is None:
                continue
            s = idx[(keys == k).all(1)]
            v[s] = a[pts[s, 2] - k[0] * cz, pts[s, 1] - k[1] * cy, pts[s, 0] - k[2] * cx]
        return v


class Mask:
    def __init__(self, npz):
        d = np.load(npz)
        self.P = d["packed"]
        self.Z, self.Y, self.X = [int(v) for v in d["shape"]]
        self.f = 2 ** int(d["level"])
        self._c: dict = {}

    def slice(self, z_l0, eroded=False):
        i = int(np.clip(round((z_l0 - (self.f - 1) / 2) / self.f), 0, self.Z - 1))
        key = (i, eroded)
        if key not in self._c:
            m = np.unpackbits(self.P[i])[: self.Y * self.X].reshape(self.Y, self.X).astype(bool)
            if eroded:
                m = ndimage.binary_erosion(m, iterations=int(round(ERODE_L0 / self.f)))
            self._c[key] = m
        return self._c[key]

    def inside(self, x, y, z, eroded=True):
        m = self.slice(z, eroded)
        ix = int(round((x - (self.f - 1) / 2) / self.f))
        iy = int(round((y - (self.f - 1) / 2) / self.f))
        return 0 <= ix < self.X and 0 <= iy < self.Y and bool(m[iy, ix])

    def ray_radius(self, cx, cy, z, theta, rmax=12000.0):
        """Distance (level-0 vox) from (cx, cy) along theta to the last mask exit of the
        first mask run met on the ray (filled mask, not eroded)."""
        m = self.slice(z, False)
        r = np.arange(0.0, rmax, self.f / 4.0)
        xs = cx + r * math.cos(theta)
        ys = cy + r * math.sin(theta)
        ix = np.rint((xs - (self.f - 1) / 2) / self.f).astype(int)
        iy = np.rint((ys - (self.f - 1) / 2) / self.f).astype(int)
        ok = (ix >= 0) & (ix < self.X) & (iy >= 0) & (iy < self.Y)
        inside = np.zeros(r.size, bool)
        inside[ok] = m[iy[ok], ix[ok]]
        if not inside.any():
            return float("nan"), False
        first = int(np.argmax(inside))
        after = inside[first:]
        exit_ = first + (int(np.argmin(after)) if (~after).any() else after.size)
        return float(r[exit_ - 1]), first == 0


def centre_at(curve, z):
    zc, xc, yc = curve
    return float(np.interp(z, zc, xc)), float(np.interp(z, zc, yc))


def snap_to_m7(m7: M7Volume, p, mask: Mask, ok=None):
    """Nearest m7==255 voxel to p=(x,y,z) inside the eroded mask and satisfying ok(q)
    (z margin, spacing); returns (q, dist, searched)."""
    for h in (64, 160):
        x, y, z = [int(round(v)) for v in p]
        cz, cy, cx = m7.ch
        m7.prefetch([(iz, iy, ix) for iz in range((z - h) // cz, (z + h) // cz + 1)
                     for iy in range((y - h) // cy, (y + h) // cy + 1) for ix in range((x - h) // cx, (x + h) // cx + 1)])
        b = m7.box(z - h, z + h + 1, y - h, y + h + 1, x - h, x + h + 1)
        zz, yy, xx = np.nonzero(b == 255)
        if zz.size == 0:
            continue
        d2 = (zz - h) ** 2 + (yy - h) ** 2 + (xx - h) ** 2
        order = np.argsort(d2)
        for o in order[:5000]:
            q = (x + int(xx[o]) - h, y + int(yy[o]) - h, z + int(zz[o]) - h)
            if mask.inside(*q, eroded=True) and (ok is None or ok(q)):
                return q, float(math.sqrt(d2[o])), h
    return None, float("nan"), 160


def radial_run(m7, cx, cy, z, theta, r0, half=8):
    """Centre radius of the m7==255 run on the radial line nearest r0 (None if none)."""
    rr = r0 + np.arange(-half, half + 1, 1.0)
    pts = np.c_[cx + rr * math.cos(theta), cy + rr * math.sin(theta), np.full(rr.size, z)]
    v = m7.points(pts) == 255
    if not v.any():
        return None, 0
    lab, n = ndimage.label(v)
    best, bd, bw = None, 1e9, 0
    for k in range(1, n + 1):
        s = rr[lab == k]
        c = 0.5 * (s[0] + s[-1])
        d = 0.0 if s[0] <= r0 <= s[-1] else min(abs(s[0] - r0), abs(s[-1] - r0))
        if d < bd:
            best, bd, bw = c, d, len(s)
    return best, bw


def sheet_walk(m7, curve, si, sj, step=4.0, max_gap=48.0, track_half=4):
    """Follow the m7 sheet radially from seed i to seed j along the straight path in
    (theta, z) about the centre curve. Returns dict(verdict in {same, different,
    undetermined}, dr, gap_max)."""
    def cyl(s):
        cx, cy = centre_at(curve, s[2])
        return math.atan2(s[1] - cy, s[0] - cx), math.hypot(s[0] - cx, s[1] - cy)

    ti, ri = cyl(si)
    tj, rj = cyl(sj)
    dth = (tj - ti + math.pi) % (2 * math.pi) - math.pi
    L = math.hypot(0.5 * (ri + rj) * dth, sj[2] - si[2])
    n = max(2, int(math.ceil(L / step)))
    pp = []
    for t in np.linspace(0, 1, min(n, 200) + 1):
        z = si[2] + t * (sj[2] - si[2])
        c0, c1 = centre_at(curve, z)
        th = ti + t * dth
        for dr in (-60.0, 0.0, 60.0):
            rr = ri + t * (rj - ri) + dr
            pp.append((c0 + rr * math.cos(th), c1 + rr * math.sin(th), z))
    m7.prefetch(m7.keys_for_points(np.array(pp)))
    cx, cy = centre_at(curve, si[2])
    r, _ = radial_run(m7, cx, cy, si[2], ti, ri)
    if r is None:
        return dict(verdict="undetermined", reason="no sheet at seed i", dr=None, gap_max=None, path_vox=L)
    gap = gmax = 0.0
    for k in range(1, n + 1):
        t = k / n
        th = ti + t * dth
        z = si[2] + t * (sj[2] - si[2])
        cx, cy = centre_at(curve, z)
        rn, _ = radial_run(m7, cx, cy, z, th, r, half=track_half)
        if rn is None:
            gap += L / n
            gmax = max(gmax, gap)
            if gap > max_gap:
                return dict(verdict="undetermined", reason="sheet lost", dr=None, gap_max=gmax, path_vox=L,
                            lost_at=round(t, 3))
            continue
        gap = 0.0
        r = rn
    cx, cy = centre_at(curve, sj[2])
    rjc, _ = radial_run(m7, cx, cy, sj[2], tj, rj)
    if rjc is None:
        return dict(verdict="undetermined", reason="no sheet at seed j", dr=None, gap_max=gmax, path_vox=L)
    dr = r - rjc
    return dict(verdict="same" if abs(dr) <= DUP_TOL else "different", dr=round(dr, 2), gap_max=gmax, path_vox=L)


def surface_distance(curve, si, sj):
    def cyl(s):
        cx, cy = centre_at(curve, s[2])
        return math.atan2(s[1] - cy, s[0] - cx), math.hypot(s[0] - cx, s[1] - cy)

    ti, ri = cyl(si)
    tj, rj = cyl(sj)
    dth = abs((tj - ti + math.pi) % (2 * math.pi) - math.pi)
    return math.hypot(0.5 * (ri + rj) * dth, sj[2] - si[2])


def plan_volume(v, mask_dir, umb_path, out_dir, gens=(45, 75)):
    scroll, vid = v["scroll"], v["volume_id"]
    Z0, Y0, X0 = v["levels"]["0"]["shape"]
    sh = load_shape(mask_dir, scroll)
    mask = Mask(os.path.join(mask_dir, f"{scroll}_mask_L4.npz"))
    z_lo, z_hi, thr = scroll_z_extent(sh)
    if umb_path:
        uz, ux, uy, uvol = umbilicus_curve(umb_path)
        assert vid in uvol, (vid, uvol)
        curve = (uz, ux, uy)
        centre_src = "official umbilicus " + os.path.basename(umb_path)
    else:
        zc, xc, yc, _ = centroid_curve(sh)
        curve = (zc, xc, yc)
        centre_src = "CT-mask centroid L4 (running median 65 slices + Gaussian sigma 256 vox)"
    za, zb = z_lo + Z_MARGIN, z_hi - Z_MARGIN
    zs = np.linspace(za, zb, N_LEVELS)
    seeds = []
    for k, z in enumerate(zs):
        z = float(round(z))
        cx, cy = centre_at(curve, z)
        for a in range(N_ANG):
            n = N_ANG * k + a
            f0 = F_LO + (F_HI - F_LO) * ((0.5 + n * PHI) % 1.0)
            th0 = math.radians((k % 3) * 40.0 + a * 120.0)
            placed = None
            # nudge order: fraction first (+-0.01 steps within bounds), then angle (+-2 deg steps up to 30)
            for dth in [0] + [s * d for d in range(2, 32, 2) for s in (1, -1)]:
                th = th0 + math.radians(dth)
                R, centre_in = mask.ray_radius(cx, cy, z, th)
                if not np.isfinite(R):
                    continue
                for df in [0] + [s * d / 100 for d in range(1, 36) for s in (1, -1)]:
                    f = f0 + df
                    if not (F_LO <= f <= F_HI):
                        continue
                    p = (cx + f * R * math.cos(th), cy + f * R * math.sin(th), z)
                    if not mask.inside(*p, eroded=True):
                        continue
                    if any(math.dist(p, s["planned_xyz"]) < MIN_SEP for s in seeds if "planned_xyz" in s):
                        continue
                    placed = dict(id=f"{scroll}-s{n:02d}", level=k, angle_idx=a, n=n, theta_deg=round(math.degrees(th) % 360, 2),
                                  theta_nudge_deg=dth, f_planned=round(f0, 4), f=round(f, 4), f_nudge=round(df, 2),
                                  ray_radius_vox=round(R, 1), centre_inside_mask=centre_in,
                                  centre_xy=[round(cx, 1), round(cy, 1)], planned_xyz=[round(p[0], 1), round(p[1], 1), z])
                    break
                if placed:
                    break
            if placed is None:
                placed = dict(id=f"{scroll}-s{n:02d}", level=k, angle_idx=a, n=n, failed="no admissible planned point")
            seeds.append(placed)
    # snap to m7
    m7 = M7Volume(scroll, vid)
    t0 = time.time()
    for s in seeds:
        if "planned_xyz" not in s:
            continue
        done = [o["seed_xyz"] for o in seeds if o.get("seed_xyz")]
        adm = lambda q, done=done: (za <= q[2] <= zb) and all(math.dist(q, o) >= MIN_SEP for o in done)
        q, d, h = snap_to_m7(m7, s["planned_xyz"], mask, adm)
        s["seed_xyz"] = list(q) if q else None
        s["snap_dist_vox"] = round(d, 2) if q else None
        s["snap_search_half"] = h
    snap_s = time.time() - t0
    print(f"{scroll}: snapped {sum(1 for s in seeds if s.get('seed_xyz'))}/{len(seeds)} in {snap_s:.0f}s", flush=True)
    ok = [s for s in seeds if s.get("seed_xyz")]
    # post-snap checks
    for s in ok:
        x, y, z = s["seed_xyz"]
        others = [math.dist(s["seed_xyz"], o["seed_xyz"]) for o in ok if o is not s]
        s["min_sep_vox"] = round(min(others), 1) if others else None
        s["checks"] = dict(in_eroded_mask=mask.inside(x, y, z, True), z_margin=bool(z_lo + Z_MARGIN <= z <= z_hi - Z_MARGIN),
                           sep_ok=bool(min(others) >= MIN_SEP) if others else True,
                           m7_value_255=bool(m7.points(np.array([[x, y, z]]))[0] == 255))
        cx, cy = centre_at(curve, z)
        R, _ = mask.ray_radius(cx, cy, z, math.atan2(y - cy, x - cx))
        s["f_seed"] = round(math.hypot(x - cx, y - cy) / R, 4) if np.isfinite(R) and R > 0 else None
    # duplicates
    dups = {}
    t1 = time.time()
    for g in gens:
        reach = g * STEP_VOX
        pairs = []
        for i in range(len(ok)):
            for j in range(i + 1, len(ok)):
                sd = surface_distance(curve, ok[i]["seed_xyz"], ok[j]["seed_xyz"])
                if sd <= 2 * reach:
                    pairs.append((i, j, sd))
        res = []
        print(f"{scroll} g{g}: {len(pairs)} pairs in reach", flush=True)
        for pi, (i, j, sd) in enumerate(pairs):
            if pi % 20 == 0:
                print(f"  pair {pi}/{len(pairs)} {time.time() - t1:.0f}s chunks {m7.fetched}", flush=True)
            w = sheet_walk_v2(m7, ok[i]["seed_xyz"], ok[j]["seed_xyz"], step=WALK_STEP, max_shift=WALK_SHIFT)
            w.update(i=ok[i]["id"], j=ok[j]["id"], surface_dist=round(sd, 1))
            res.append(w)
        npairs = len(ok) * (len(ok) - 1) // 2
        cnt = {k: sum(1 for r in res if r["verdict"] == k) for k in ("same", "different", "undetermined")}
        dups[str(g)] = dict(reach_vox=reach, all_pairs=npairs, pairs_in_reach=len(pairs), **cnt,
                            share_same_of_all_pairs=cnt["same"] / npairs if npairs else None,
                            share_same_upper_of_all_pairs=(cnt["same"] + cnt["undetermined"]) / npairs if npairs else None,
                            share_same_of_determined_in_reach=cnt["same"] / (cnt["same"] + cnt["different"]) if (cnt["same"] + cnt["different"]) else None,
                            pairs=res)
    dup_s = time.time() - t1
    out = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
               scroll=scroll, volume_id=vid, volume_zarr_s3=v["volume_zarr_s3"],
               m7_zarr=f"s3://{BUCKET}/{scroll}/representations/predictions/surfaces/{vid}-{M7}.zarr",
               coords="level-0 voxels, seed_xyz = [x, y, z] (vc_grow_seg_from_seed meta seed order)",
               voxel_um_from_metadata=v["key_fields"]["samplePixelSize_mm"] * 1000.0,
               centre_source=centre_src, scroll_z_extent=[z_lo, z_hi], area_threshold_px_L4=thr,
               design=dict(levels=N_LEVELS, angles=N_ANG, wrap_fraction=[F_LO, F_HI], min_sep_vox=MIN_SEP,
                           erosion_l0_vox=ERODE_L0, z_margin_vox=Z_MARGIN, angle_rotation="(k mod 3) x 40 deg",
                           fraction_sequence="0.35 + 0.35 * frac(0.5 + n * 0.618034)", snap="nearest m7==255 in eroded mask",
                           dup_tol_vox=DUP_TOL, step_vox=STEP_VOX),
               z_levels=[float(round(z)) for z in zs], seeds=seeds,
               n_placed=len(ok), duplicates={g: {k: v for k, v in d.items() if k != "pairs"} for g, d in dups.items()},
               m7_chunks_fetched=m7.fetched, m7_bytes_fetched=m7.fetched_bytes, seconds=dict(snap=round(snap_s, 1), dup=round(dup_s, 1)))
    json.dump(out, open(os.path.join(out_dir, f"{scroll}_seeds.json"), "w"), indent=1)
    json.dump({g: d["pairs"] for g, d in dups.items()}, open(os.path.join(out_dir, f"{scroll}_dup_pairs.json"), "w"), indent=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="data/catalogue/eligible_products.json")
    ap.add_argument("--mask", required=True)
    ap.add_argument("--umb", required=True, help="dir with official umbilicus JSONs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vols", nargs="+", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cat = json.load(open(a.catalogue))
    for vol in a.vols:
        v = next(v for v in cat["volumes"] if v["scroll"] == "PHerc" + vol)
        if "0841" in v["scroll"]:
            raise PermissionError("PHerc0841 is not a census volume")
        if os.path.exists(os.path.join(a.out, f"{v['scroll']}_seeds.json")):
            continue
        umb = [os.path.join(a.umb, f) for f in os.listdir(a.umb) if f.startswith(v["volume_id"] + "-umbilicus")]
        o = plan_volume(v, a.mask, umb[0] if umb else None, a.out)
        print(json.dumps(dict(scroll=o["scroll"], placed=o["n_placed"], duplicates=o["duplicates"], seconds=o["seconds"],
                              chunks=o["m7_chunks_fetched"])), flush=True)
    return 0



# ---------------------------------------------------------------------------
# walker v2: follows the local m7 sheet normal (structure tensor) instead of a
# radial line about the centre curve (v1 failed validation on official sheets)
# ---------------------------------------------------------------------------

def local_normal(m7, p, rad=6, sigma=1.5):
    x, y, z = [int(round(v)) for v in p]
    b = m7.box(z - rad, z + rad + 1, y - rad, y + rad + 1, x - rad, x + rad + 1).astype(np.float32)
    if b.max() == 0:
        return None
    g = ndimage.gaussian_filter(b, sigma)
    gz, gy, gx = np.gradient(g)
    w = np.exp(-0.5 * ((np.indices(b.shape) - rad) ** 2).sum(0) / (rad / 2.0) ** 2)
    G = np.stack([gx, gy, gz], -1).reshape(-1, 3) * np.sqrt(w.reshape(-1, 1))
    J = G.T @ G
    ev, evec = np.linalg.eigh(J)
    if ev[2] <= 0:
        return None
    return evec[:, 2], float((ev[2] - ev[1]) / (ev[2] + 1e-9))  # normal (x, y, z), linearity


def normal_run(m7, p, n, half=6):
    """Offset along n of the centre of the m7==255 run nearest p (None if none within +-half)."""
    s = np.arange(-half, half + 1, 1.0)
    pts = np.asarray(p)[None] + s[:, None] * np.asarray(n)[None]
    v = m7.points(pts) == 255
    if not v.any():
        return None
    lab, k = ndimage.label(v)
    best, bd = None, 1e9
    for i in range(1, k + 1):
        ss = s[lab == i]
        c = 0.5 * (ss[0] + ss[-1])
        d = 0.0 if ss[0] <= 0 <= ss[-1] else min(abs(ss[0]), abs(ss[-1]))
        if d < bd:
            best, bd = c, d
    return best


def sheet_walk_v2(m7, si, sj, step=4.0, max_gap=48.0, max_shift=3.0, half=6):
    p = np.asarray(si, float)
    q = np.asarray(sj, float)
    L0 = float(np.linalg.norm(q - p))
    m7.prefetch(m7.keys_for_points(p[None] + np.linspace(0, 1, 120)[:, None] * (q - p)[None]))
    gap = gmax = 0.0
    n_prev = None
    for it in range(int(3 * L0 / step) + 10):
        ln = local_normal(m7, p)
        if ln is None:
            n = n_prev
        else:
            n = ln[0]
            if n_prev is not None and np.dot(n, n_prev) < 0:
                n = -n
        if n is None:
            return dict(verdict="undetermined", reason="no normal", dr=None, gap_max=gmax, path_vox=L0)
        n_prev = n
        d = q - p
        dt = d - np.dot(d, n) * n
        if np.linalg.norm(dt) <= step:
            p = p + dt
            break
        p = p + step * dt / np.linalg.norm(dt)
        o = normal_run(m7, p, n, half)
        if o is None:
            gap += step
            gmax = max(gmax, gap)
            if gap > max_gap:
                return dict(verdict="undetermined", reason="sheet lost", dr=None, gap_max=gmax, path_vox=L0,
                            lost_at=round(1 - float(np.linalg.norm(q - p)) / max(L0, 1), 3))
            continue
        gap = 0.0
        p = p + float(np.clip(o, -max_shift, max_shift)) * n
    else:
        return dict(verdict="undetermined", reason="no convergence", dr=None, gap_max=gmax, path_vox=L0)
    n = n_prev
    oq = normal_run(m7, q, n, half)
    op = normal_run(m7, p, n, half)
    if oq is None or op is None:
        return dict(verdict="undetermined", reason="no sheet at end", dr=None, gap_max=gmax, path_vox=L0)
    dr = float(np.dot((p + op * n) - (q + oq * n), n))
    return dict(verdict="same" if abs(dr) <= DUP_TOL else "different", dr=round(dr, 2), gap_max=gmax, path_vox=L0)


if __name__ == "__main__":
    sys.exit(main())
