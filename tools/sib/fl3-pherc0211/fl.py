# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters screen helpers for one scroll (numbers only; no image is ever viewed).
# Extra pass 3 (tools/fl/BRIEF_PASS.md): adapted from tools/sib/fl-pherc0211/fl.py (pass 1, commit f5876b5):
#   seeds take a radius band (inner third for pass 3), 'rank' orders organizer segments by area, manifests carry scroll + pass.
# Subcommands: list | rank | seeds | measure | tiles.  Python: /opt/hv/bin/python (numpy, cv2, tifffile, numcodecs, requests, boto3).
import hashlib, json, math, os, sys
import numpy as np

BUCKET = "vesuvius-challenge-open-data"
HTTP = f"https://{BUCKET}.s3.amazonaws.com"
VOX_UM = 9.362
TILE_MM = 20.0
OUT_PX = 1068


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED))


def cmd_list(scroll, out):
    """List the scroll folder anonymously; find organizer tifxyz segments (dirs holding x.tif + meta.json)."""
    c = s3(); pg = c.get_paginator("list_objects_v2")
    top = [p["Prefix"] for r in pg.paginate(Bucket=BUCKET, Prefix=f"{scroll}/", Delimiter="/") for p in r.get("CommonPrefixes", [])]
    segs = {}
    for pre in [p for p in top if "segment" in p.lower()]:
        for r in pg.paginate(Bucket=BUCKET, Prefix=pre):
            for o in r.get("Contents", []):
                k = o["Key"]; d, f = k.rsplit("/", 1)
                if f in ("x.tif", "y.tif", "z.tif", "meta.json"):
                    s = segs.setdefault(d, {"files": {}})
                    s["files"][f] = o["Size"]
    tifxyz = [{"prefix": d, "x_tif_bytes": v["files"]["x.tif"]} for d, v in segs.items()
              if {"x.tif", "y.tif", "z.tif", "meta.json"} <= set(v["files"])]
    tifxyz.sort(key=lambda s: -s["x_tif_bytes"])
    json.dump({"scroll": scroll, "top_prefixes": top, "tifxyz_segments": tifxyz}, open(out, "w"), indent=1)
    print(f"list: {len(top)} top prefixes, {len(tifxyz)} tifxyz segments")


class Zarr:
    """Minimal anonymous HTTPS reader for one zarr v2 array (C order, '/' separator)."""
    def __init__(self, url):
        import requests, numcodecs
        self.url = url.rstrip("/"); self.rq = requests.Session()
        self.meta = self.rq.get(self.url + "/.zarray", timeout=60).json()
        self.codec = numcodecs.get_codec(self.meta["compressor"]) if self.meta["compressor"] else None
        self.cs = self.meta["chunks"]; self.shape = self.meta["shape"]; self.cache = {}

    def chunk(self, ci):
        if ci in self.cache: return self.cache[ci]
        for t in range(5):
            try:
                r = self.rq.get(self.url + "/" + "/".join(map(str, ci)), timeout=120)
                break
            except Exception:
                import time; time.sleep(2 ** t)
        if r.status_code in (403, 404):
            a = np.full(self.cs, self.meta["fill_value"] or 0, np.uint8)
        else:
            r.raise_for_status(); b = r.content
            if self.codec: b = self.codec.decode(b)
            a = np.frombuffer(b, np.uint8).reshape(self.cs)
        if len(self.cache) > 64: self.cache.clear()
        self.cache[ci] = a; return a

    def at(self, z, y, x):
        z, y, x = int(z), int(y), int(x)
        if not (0 <= z < self.shape[0] and 0 <= y < self.shape[1] and 0 <= x < self.shape[2]): return 0
        c = self.chunk((z // self.cs[0], y // self.cs[1], x // self.cs[2]))
        return int(c[z % self.cs[0], y % self.cs[1], x % self.cs[2]])


def umbilicus_xy(cps, z):
    zs = np.array([p["z"] for p in cps], float); o = np.argsort(zs)
    xs = np.array([p["x"] for p in cps], float)[o]; ys = np.array([p["y"] for p in cps], float)[o]
    return float(np.interp(z, zs[o], xs)), float(np.interp(z, zs[o], ys))


def cmd_rank(listing, out):
    """Rank organizer tifxyz segments by area: meta.json area_cm2 where present, else x.tif bytes (flagged)."""
    import requests
    L = json.load(open(listing)); rows = []
    for s in L["tifxyz_segments"]:
        a = None
        try: a = requests.get(f"{HTTP}/{s['prefix']}/meta.json", timeout=60).json().get("area_cm2")
        except Exception: pass
        rows.append({"prefix": s["prefix"], "meta_area_cm2": a, "x_tif_bytes": s["x_tif_bytes"]})
    rows.sort(key=lambda r: (r["meta_area_cm2"] is None, -(r["meta_area_cm2"] or 0), -r["x_tif_bytes"]))
    for i, r in enumerate(rows): r["rank"] = i + 1
    json.dump({"rank_key": "meta.json area_cm2 desc; segments without it after, by x.tif bytes", "segments": rows}, open(out, "w"), indent=1)
    print(f"rank: {len(rows)} segments")


def cmd_seeds(ct_url, surf_url, umb_url, nseeds, out, lo=0.35, hi=0.65, tgt=0.5):
    """Seeds spread over a radius band: z fractions x azimuths; R = outer CT-mask radius along the ray (level 3);
    seed = centre of the surface-prediction run (level 0, >= threshold) nearest tgt*R within lo..hi R.
    Pass 3 (inner third): lo=0.05 (off the umbilicus core), hi=1/3, tgt=0.19."""
    import requests
    cps = requests.get(umb_url, timeout=60).json()["control_points"]
    ct3 = Zarr(ct_url.rstrip("/") + "/3"); sf = Zarr(surf_url.rstrip("/") + "/0")
    Z0 = sf.shape[0]; zr = (min(p["z"] for p in cps), max(p["z"] for p in cps))
    plan = [(0.30, 0), (0.45, 90), (0.60, 180), (0.75, 270), (0.38, 45), (0.53, 135), (0.68, 225), (0.83, 315)]
    seeds = []; log = []
    for zf, az in plan:
        if len(seeds) >= nseeds: break
        z = zr[0] + zf * (zr[1] - zr[0]); cx, cy = umbilicus_xy(cps, z)
        th = math.radians(az); dx, dy = math.cos(th), math.sin(th)
        R = 0
        for r3 in range(0, 1200):
            x3, y3 = (cx + r3 * 8 * dx) / 8, (cy + r3 * 8 * dy) / 8
            if not (0 <= x3 < ct3.shape[2] and 0 <= y3 < ct3.shape[1]): break
            if ct3.at(z / 8, y3, x3) > 0: R = r3 * 8
        ent = {"z_frac": zf, "azimuth_deg": az, "z": round(z, 1), "umb_x": round(cx, 1), "umb_y": round(cy, 1),
               "outer_radius_vox": R, "center_ct_l3": ct3.at(z / 8, cy / 8, cx / 8)}
        if R < 200:
            ent["result"] = "outer radius too small"; log.append(ent); continue
        vals = []; best = None
        for r in range(int(lo * R), int(hi * R)):
            v = sf.at(z, cy + r * dy, cx + r * dx); vals.append(v)
        vmax = max(vals) if vals else 0
        thr = 128 if vmax >= 128 else (1 if vmax > 0 else None)
        if thr is not None:
            hits = [int(lo * R) + i for i, v in enumerate(vals) if v >= thr]
            # centre of the hit run nearest tgt R (sheet middle, not its edge)
            runs = []; 
            for h in hits:
                if runs and h == runs[-1][-1] + 1: runs[-1].append(h)
                else: runs.append([h])
            if runs:
                run = min(runs, key=lambda q: abs(np.mean(q) - tgt * R)); best = int(round(np.mean(run)))
        ent.update({"surface_max_on_ray": vmax, "threshold": thr, "n_hit_vox": sum(1 for v in vals if thr and v >= thr)})
        if best is None:
            ent["result"] = "no surface voxel on ray"; log.append(ent); continue
        sx, sy = cx + best * dx, cy + best * dy
        ent.update({"result": "seed", "r_vox": best, "r_over_R": round(best / R, 3),
                    "seed_xyz": [round(sx, 1), round(sy, 1), round(z, 1)], "surface_value": sf.at(z, sy, sx)})
        seeds.append(ent); log.append(ent)
        print("seed", ent["seed_xyz"], "r/R", ent["r_over_R"], flush=True)
    json.dump({"ct": ct_url, "surface": surf_url, "umbilicus": umb_url, "umbilicus_z_range": zr,
               "radius_band_over_R": [lo, hi], "target_over_R": tgt, "seeds": seeds, "attempts": log}, open(out, "w"), indent=1)
    print(f"seeds: {len(seeds)}")


def load_xyz(d):
    import tifffile
    P = np.stack([tifffile.imread(os.path.join(d, f"{a}.tif")).astype(np.float64) for a in "xyz"], -1)
    valid = (P[..., 0] != -1) & np.isfinite(P).all(-1) & (P[..., 2] > 0)
    return P, valid


def cmd_measure(segdir, out):
    """True mesh area (sum of the two triangle areas per fully valid quad, voxel -> cm^2) and grid stats."""
    P, V = load_xyz(segdir); m = json.load(open(os.path.join(segdir, "meta.json")))
    q = V[:-1, :-1] & V[1:, :-1] & V[:-1, 1:] & V[1:, 1:]
    a, b, c, d = P[:-1, :-1], P[:-1, 1:], P[1:, :-1], P[1:, 1:]
    t1 = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1); t2 = 0.5 * np.linalg.norm(np.cross(b - d, c - d), axis=-1)
    area_vox2 = float(np.where(q, t1 + t2, 0).sum())
    e_u = np.linalg.norm(b - a, axis=-1)[q]; step = 1.0 / float(m["scale"][0])
    r = {"segment_dir": segdir, "grid_rows": int(P.shape[0]), "grid_cols": int(P.shape[1]), "valid_vertices": int(V.sum()),
         "valid_quads": int(q.sum()), "area_cm2": area_vox2 * (VOX_UM ** 2) / 1e8, "nominal_step_vox": step,
         "edge_u_within_10pct": float(np.mean(np.abs(e_u - step) <= 0.1 * step)) if e_u.size else 0.0,
         "meta_scale": m["scale"], "meta_area_cm2": m.get("area_cm2"), "x_tif_sha256": sha256(os.path.join(segdir, "x.tif"))}
    json.dump(r, open(out, "w"), indent=1); print(f"measure: area {r['area_cm2']:.2f} cm2, {r['valid_quads']} quads")


def cmd_tiles(segname, segdir, pred_tif, direction, source, outdir, manifest, scroll, pas):
    """2 x 2 cm tiles from the u8 prediction on the full render canvas (scale 1 => 1 px = 1 voxel = 9.362 um).
    Valid = mesh vertex validity resampled (nearest) to the canvas. Keep valid >= 0.5; INTER_AREA to 1068 px."""
    import cv2, tifffile
    p = tifffile.imread(pred_tif)
    if p.ndim == 3: p = p[0] if p.shape[0] < p.shape[-1] else p[..., 0]
    if p.dtype != np.uint8:
        pf = p.astype(np.float32); p = np.clip(pf * (255.0 if pf.max() <= 1.0 else 1.0), 0, 255).round().astype(np.uint8)
    _, V = load_xyz(segdir)
    valid = cv2.resize(V.astype(np.uint8), (p.shape[1], p.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    T = int(round(TILE_MM * 1000 / VOX_UM)); ppm = OUT_PX / (T * VOX_UM / 1000.0)
    os.makedirs(outdir, exist_ok=True)
    man = json.load(open(manifest)) if os.path.exists(manifest) else {"tiles": []}
    man.update({"scroll": scroll, "pass": int(pas), "decl": "DECL-FL-1", "tile_src_px": T, "tile_out_px": OUT_PX, "px_per_mm": round(ppm, 4),
                "voxel_um": VOX_UM, "chain": "C2-NT: vc_render_tifxyz -n 31 --flip-normals, ink_9um step-075000, both directions, no TTA",
                "canvas_hw": list(p.shape), "note": "valid = mesh vertex validity resampled nearest to canvas; r,c = tile grid indices from canvas origin"})
    man["tiles"] = [t for t in man["tiles"] if t.get("direction") != direction]
    nk = 0; nt = 0
    for r in range(p.shape[0] // T):
        for c in range(p.shape[1] // T):
            nt += 1
            vm = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]; vf = float(vm.mean())
            if vf < 0.5: continue
            t = p[r * T:(r + 1) * T, c * T:(c + 1) * T].copy(); t[~vm] = 0
            t = cv2.resize(t, (OUT_PX, OUT_PX), interpolation=cv2.INTER_AREA)
            fn = os.path.join(outdir, f"{segname}_{direction}_r{r:02d}_c{c:02d}.png"); cv2.imwrite(fn, t)
            vv = cv2.resize(vm.astype(np.uint8), (OUT_PX, OUT_PX), interpolation=cv2.INTER_NEAREST) > 0
            man["tiles"].append({"segment": segname, "r": r, "c": c, "direction": direction, "file": os.path.basename(fn),
                                 "png_sha256": sha256(fn), "valid_fraction": round(vf, 4), "px_per_mm": round(ppm, 4),
                                 "source": source, "pass": int(pas), "ink_score_ge128": round(float((t[vv] >= 128).mean()) if vv.any() else 0.0, 5)})
            nk += 1
    json.dump(man, open(manifest, "w"), indent=1)
    print(f"tiles {segname} {direction}: kept {nk} of {nt} grid cells (T={T} px)")


if __name__ == "__main__":
    a = sys.argv[1:]
    {"list": lambda: cmd_list(a[1], a[2]),
     "rank": lambda: cmd_rank(a[1], a[2]),
     "seeds": lambda: cmd_seeds(a[1], a[2], a[3], int(a[4]), a[5], *map(float, a[6:9])),
     "measure": lambda: cmd_measure(a[1], a[2]),
     "tiles": lambda: cmd_tiles(*a[1:10])}[a[0]]()
