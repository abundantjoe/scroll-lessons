# Provenance: Project HERCULES | [id removed]
# DECL-FL-4-A1 fleet copy of the DECL-FL-2 fl.py (p4v-03 PHerc0268 copy of fl-pherc0257 54b29c96), unchanged except: new
# subcommands seeds_inner (inner windings first, axis reused from the FL-2 seeds.json) and vgrid (vertex-grid block means for seam checks).
# Original subcommands: list | seeds | measure | tiles.  Python: /opt/hv/bin/python (numpy, cv2, tifffile, numcodecs, requests).
# Subcommands: list | seeds | measure | tiles.  Python: /opt/hv/bin/python (numpy, cv2, tifffile, numcodecs, requests, boto3).
import hashlib, json, math, os, sys
import numpy as np

BUCKET = "vesuvius-challenge-open-data"
HTTP = f"https://{BUCKET}.s3.amazonaws.com"
VOX_UM = float(os.environ.get("FL_VOX_UM", "9.362"))
TILE_MM = 20.0
OUT_PX = 1068
SCROLL = os.environ.get("FL_SCROLL", "PHerc0257")


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


def cmd_seeds(ct_url, surf_url, umb_url, nseeds, out):
    """Seeds spread over mid radius: z fractions x azimuths; mid radius = 0.5 * outer CT-mask radius along the ray
    (level 3); seed = surface-prediction voxel (level 0) >= threshold nearest to mid radius within 0.35..0.65 R."""
    import requests
    ct3 = Zarr(ct_url.rstrip("/") + "/3"); sf = Zarr(surf_url.rstrip("/") + "/0")
    Z0 = sf.shape[0]
    if umb_url != "none":
        cps = requests.get(umb_url, timeout=60).json()["control_points"]
    else:  # no organizer umbilicus: axis proxy = centroid of the CT mask (nonzero) in level-4 slices, x16 to level 0
        ct4 = Zarr(ct_url.rstrip("/") + "/4"); cps = []
        for zf in np.linspace(0.05, 0.95, 19):
            z4 = int(zf * ct4.shape[0]); cz = z4 // ct4.cs[0]; ny, nx = ct4.shape[1], ct4.shape[2]
            sl = np.zeros((ny, nx), np.uint8)
            for yi in range(0, ny, ct4.cs[1]):
                for xi in range(0, nx, ct4.cs[2]):
                    c = ct4.chunk((cz, yi // ct4.cs[1], xi // ct4.cs[2]))[z4 % ct4.cs[0]]
                    sl[yi:yi + ct4.cs[1], xi:xi + ct4.cs[2]] = c[:min(ct4.cs[1], ny - yi), :min(ct4.cs[2], nx - xi)]
            yy, xx = np.nonzero(sl)
            if yy.size < 500: continue
            cps.append({"z": z4 * 16.0, "x": float(xx.mean() * 16 + 8), "y": float(yy.mean() * 16 + 8), "n_mask_l4": int(yy.size)})
        print("axis proxy (CT-mask centroid, level 4):", [(p["z"], round(p["x"]), round(p["y"])) for p in cps], flush=True)
        if len(cps) < 2: raise SystemExit("seeds: CT mask empty; no axis proxy")
    zr = (min(p["z"] for p in cps), max(p["z"] for p in cps))
    plan = [(0.30, 0), (0.45, 90), (0.60, 180), (0.75, 270), (0.38, 45), (0.53, 135), (0.68, 225), (0.83, 315)]
    # DECL-FL-2: 48 candidates, the pilot's extension verbatim (fl-pherc0257 fl2/fl.py): first 8 = DECL-FL-1 plan,
    # then a 6 z-fraction x 8 azimuth grid offset by 22.5 deg
    plan += [(zf, 22.5 + 45 * k) for zf in (0.22, 0.34, 0.46, 0.58, 0.70, 0.82) for k in range(8)]
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
        for r in range(int(0.35 * R), int(0.65 * R)):
            v = sf.at(z, cy + r * dy, cx + r * dx); vals.append(v)
        vmax = max(vals) if vals else 0
        thr = 128 if vmax >= 128 else (1 if vmax > 0 else None)
        if thr is not None:
            hits = [int(0.35 * R) + i for i, v in enumerate(vals) if v >= thr]
            # centre of the hit run nearest 0.5 R (sheet middle, not its edge)
            runs = []; 
            for h in hits:
                if runs and h == runs[-1][-1] + 1: runs[-1].append(h)
                else: runs.append([h])
            if runs:
                run = min(runs, key=lambda q: abs(np.mean(q) - 0.5 * R)); best = int(round(np.mean(run)))
        ent.update({"surface_max_on_ray": vmax, "threshold": thr, "n_hit_vox": sum(1 for v in vals if thr and v >= thr)})
        if best is None:
            ent["result"] = "no surface voxel on ray"; log.append(ent); continue
        sx, sy = cx + best * dx, cy + best * dy
        ent.update({"result": "seed", "r_vox": best, "r_over_R": round(best / R, 3),
                    "seed_xyz": [round(sx, 1), round(sy, 1), round(z, 1)], "surface_value": sf.at(z, sy, sx)})
        seeds.append(ent); log.append(ent)
        print("seed", ent["seed_xyz"], "r/R", ent["r_over_R"], flush=True)
    json.dump({"ct": ct_url, "surface": surf_url, "umbilicus": umb_url, "axis_points": cps, "umbilicus_z_range": zr,
               "seeds": seeds, "attempts": log}, open(out, "w"), indent=1)
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


def cmd_tiles(segname, segdir, pred_tif, direction, source, outdir, manifest):
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
    man.update({"scroll": SCROLL, "decl": os.environ.get("FL_DECL", "DECL-FL-1"), "volume": os.environ.get("FL_VOLUME"),
                "model": os.environ.get("FL_MODEL"), "model_sha256": os.environ.get("FL_MODEL_SHA"), "tile_src_px": T, "tile_out_px": OUT_PX, "px_per_mm": round(ppm, 4),
                "voxel_um": VOX_UM, "chain": os.environ.get("FL_CHAIN", "C2-NT: vc_render_tifxyz -n 31 --flip-normals, ink_9um step-075000, both directions, no TTA"),
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
                                 "source": source, "scroll": SCROLL, "volume": os.environ.get("FL_VOLUME"),
                                 "model": os.environ.get("FL_MODEL"), "model_sha256": os.environ.get("FL_MODEL_SHA"),
                                 "segment_area_cm2": float(os.environ["FL_AREA_CM2"]) if os.environ.get("FL_AREA_CM2") else None,
                                 "ink_score_ge128": round(float((t[vv] >= 128).mean()) if vv.any() else 0.0, 5)})
            nk += 1
    json.dump(man, open(manifest, "w"), indent=1)
    print(f"tiles {segname} {direction}: kept {nk} of {nt} grid cells (T={T} px)")


def cmd_seeds_inner(ct_url, surf_url, axis_json, out):
    """DECL-FL-4-A1 item 3: inner windings first. Axis = the FL-2 CT-mask-centroid axis points (axis_json = FL-2 seeds.json).
    Outer radius R per (z fraction, azimuth) ray exactly as cmd_seeds (level 3). Radial targets t = 0.15, 0.20, 0.25, 0.30, 0.35
    (ascending = innermost first) x z fractions 0.30, 0.50, 0.70 x 8 azimuths (offset 22.5 deg on odd bands); seed = centre of the
    surface-prediction hit run (level 0, >= 128, else >= 1) nearest t*R within t*R +- 0.025 R."""
    ct3 = Zarr(ct_url.rstrip("/") + "/3"); sf = Zarr(surf_url.rstrip("/") + "/0")
    cps = json.load(open(axis_json))["axis_points"]; zr = (min(p["z"] for p in cps), max(p["z"] for p in cps))
    Rc = {}; seeds = []; log = []
    for bi, t in enumerate((0.15, 0.20, 0.25, 0.30, 0.35)):
        for zf in (0.30, 0.50, 0.70):
            for k in range(8):
                az = 45 * k + (22.5 if bi % 2 else 0.0)
                z = zr[0] + zf * (zr[1] - zr[0]); cx, cy = umbilicus_xy(cps, z)
                th = math.radians(az); dx, dy = math.cos(th), math.sin(th)
                if (zf, az) not in Rc:
                    R = 0
                    for r3 in range(0, 1200):
                        x3, y3 = (cx + r3 * 8 * dx) / 8, (cy + r3 * 8 * dy) / 8
                        if not (0 <= x3 < ct3.shape[2] and 0 <= y3 < ct3.shape[1]): break
                        if ct3.at(z / 8, y3, x3) > 0: R = r3 * 8
                    Rc[(zf, az)] = R
                R = Rc[(zf, az)]
                ent = {"band_t": t, "z_frac": zf, "azimuth_deg": az, "z": round(z, 1), "umb_x": round(cx, 1), "umb_y": round(cy, 1), "outer_radius_vox": R}
                if R < 200: ent["result"] = "outer radius too small"; log.append(ent); continue
                lo, hi = int((t - 0.025) * R), int((t + 0.025) * R)
                vals = [sf.at(z, cy + r * dy, cx + r * dx) for r in range(lo, hi)]
                vmax = max(vals) if vals else 0; thr = 128 if vmax >= 128 else (1 if vmax > 0 else None)
                best = None
                if thr is not None:
                    runs = []
                    for h in [lo + i for i, v in enumerate(vals) if v >= thr]:
                        if runs and h == runs[-1][-1] + 1: runs[-1].append(h)
                        else: runs.append([h])
                    if runs: best = int(round(np.mean(min(runs, key=lambda q: abs(np.mean(q) - t * R)))))
                ent.update({"surface_max_on_ray": vmax, "threshold": thr})
                if best is None: ent["result"] = "no surface voxel in band"; log.append(ent); continue
                sx, sy = cx + best * dx, cy + best * dy
                ent.update({"result": "seed", "r_vox": best, "r_over_R": round(best / R, 3), "seed_xyz": [round(sx, 1), round(sy, 1), round(z, 1)]})
                seeds.append(ent); log.append(ent); print("seed", ent["seed_xyz"], "r/R", ent["r_over_R"], flush=True)
    json.dump({"decl": "DECL-FL-4-A1", "ct": ct_url, "surface": surf_url, "axis_points": cps, "umbilicus_z_range": zr,
               "seeds": seeds, "attempts": log}, open(out, "w"), indent=1)
    print(f"seeds_inner: {len(seeds)}")


def cmd_vgrid(segdir, pred_tif, out_tif, axis_json):
    """Seam-check support (DECL-FL-4-A1 item 5): prediction block means on the tifxyz vertex grid (INTER_AREA), uint8, plus
    per-segment radial stats (mean r/R needs R, so record mean radial distance in voxels from the axis) printed as JSON."""
    import cv2, tifffile
    P, V = load_xyz(segdir); p = tifffile.imread(pred_tif)
    g = cv2.resize(p, (P.shape[1], P.shape[0]), interpolation=cv2.INTER_AREA); g[~V] = 0
    tifffile.imwrite(out_tif, g.astype(np.uint8), compression="zlib", metadata=None, software=False)  # tag-free: pre-commit cf_scan
    cps = json.load(open(axis_json))["axis_points"]; q = P[V]
    zs = np.array([p_["z"] for p_ in cps]); o = np.argsort(zs)
    ax = np.interp(q[:, 2], zs[o], np.array([p_["x"] for p_ in cps])[o]); ay = np.interp(q[:, 2], zs[o], np.array([p_["y"] for p_ in cps])[o])
    rad = np.hypot(q[:, 0] - ax, q[:, 1] - ay)
    print(json.dumps({"vgrid": out_tif, "grid": list(g.shape), "radial_vox_median": round(float(np.median(rad)), 1),
                      "radial_vox_p10": round(float(np.percentile(rad, 10)), 1), "radial_vox_p90": round(float(np.percentile(rad, 90)), 1)}))


def cmd_cover(segname, segdir, pred_tif, direction, source, outdir, manifest):
    """DECL-FL-4-A2: cover tiling for FL-4 segments (canvas ~3.46 cm square, so the FL-2 grid keeps only 1 of 2 x 2 cm).
    Cells: T = 2 cm at offsets {0, W-T} x {0, H-T} (they overlap where the canvas is < 4 cm), valid >= 0.5, INTER_AREA to
    1068 px (53.4 px/mm), masked outside the mesh, exactly as cmd_tiles. Window: the WHOLE canvas at 26.7 px/mm (INTER_AREA),
    masked, placed top-left in a 1068 x 1068 zero frame (the DECL-FL-3 window format), one per segment and direction."""
    import cv2, tifffile
    p = tifffile.imread(pred_tif)
    if p.ndim == 3: p = p[0] if p.shape[0] < p.shape[-1] else p[..., 0]
    _, V = load_xyz(segdir)
    valid = cv2.resize(V.astype(np.uint8), (p.shape[1], p.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    H, W = p.shape; T = int(round(TILE_MM * 1000 / VOX_UM)); ppm = OUT_PX / (T * VOX_UM / 1000.0)
    os.makedirs(outdir, exist_ok=True)
    man = json.load(open(manifest)) if os.path.exists(manifest) else {"tiles": [], "windows": []}
    man.update({"scroll": SCROLL, "decl": "DECL-FL-4-A2 cover tiling", "volume": os.environ.get("FL_VOLUME"), "model": os.environ.get("FL_MODEL"),
                "model_sha256": os.environ.get("FL_MODEL_SHA"), "tile_src_px": T, "tile_out_px": OUT_PX, "px_per_mm": round(ppm, 4),
                "window_px_per_mm": round(ppm / 2, 4), "voxel_um": VOX_UM, "chain": os.environ.get("FL_CHAIN"), "canvas_hw": [H, W]})
    man["tiles"] = [t for t in man.get("tiles", []) if t.get("direction") != direction]
    man["windows"] = [t for t in man.get("windows", []) if t.get("direction") != direction]
    ys = sorted({0, max(0, H - T)}) if H >= T else []; xs = sorted({0, max(0, W - T)}) if W >= T else []
    common = {"segment": segname, "direction": direction, "source": source, "scroll": SCROLL, "volume": os.environ.get("FL_VOLUME"),
              "model": os.environ.get("FL_MODEL"), "model_sha256": os.environ.get("FL_MODEL_SHA"),
              "segment_area_cm2": float(os.environ["FL_AREA_CM2"]) if os.environ.get("FL_AREA_CM2") else None}
    for r, y0 in enumerate(ys):
        for c, x0 in enumerate(xs):
            vm = valid[y0:y0 + T, x0:x0 + T]; vf = float(vm.mean())
            if vf < 0.5: continue
            t = p[y0:y0 + T, x0:x0 + T].copy(); t[~vm] = 0
            t = cv2.resize(t, (OUT_PX, OUT_PX), interpolation=cv2.INTER_AREA)
            fn = os.path.join(outdir, f"{segname}_{direction}_r{r:02d}_c{c:02d}.png"); cv2.imwrite(fn, t)
            vv = cv2.resize(vm.astype(np.uint8), (OUT_PX, OUT_PX), interpolation=cv2.INTER_NEAREST) > 0
            man["tiles"].append(dict(common, r=r, c=c, y0_px=y0, x0_px=x0, file=os.path.basename(fn), png_sha256=sha256(fn),
                                     valid_fraction=round(vf, 4), px_per_mm=round(ppm, 4),
                                     ink_score_ge128=round(float((t[vv] >= 128).mean()) if vv.any() else 0.0, 5)))
    f = (ppm / 2) / (1000.0 / VOX_UM); hw = (max(1, int(round(H * f))), max(1, int(round(W * f))))
    if hw[0] <= OUT_PX and hw[1] <= OUT_PX and valid.any():
        q = p.copy(); q[~valid] = 0
        w = cv2.resize(q, (hw[1], hw[0]), interpolation=cv2.INTER_AREA)
        wv = cv2.resize(valid.astype(np.uint8), (hw[1], hw[0]), interpolation=cv2.INTER_NEAREST) > 0
        fr = np.zeros((OUT_PX, OUT_PX), np.uint8); fr[:hw[0], :hw[1]] = w
        fn = os.path.join(outdir, f"{segname}_{direction}_window.png"); cv2.imwrite(fn, fr)
        man["windows"].append(dict(common, file=os.path.basename(fn), png_sha256=sha256(fn), content_hw_px=list(hw),
                                   px_per_mm=round(ppm / 2, 4), valid_fraction_of_content=round(float(wv.mean()), 4),
                                   ink_score_ge128=round(float((w[wv] >= 128).mean()) if wv.any() else 0.0, 5)))
    json.dump(man, open(manifest, "w"), indent=1)
    print(f"cover {segname} {direction}: {len([t for t in man['tiles'] if t['direction'] == direction])} cells, "
          f"{len([t for t in man['windows'] if t['direction'] == direction])} window (canvas {H}x{W}, T={T})")


if __name__ == "__main__":
    a = sys.argv[1:]
    {"list": lambda: cmd_list(a[1], a[2]),
     "seeds": lambda: cmd_seeds(a[1], a[2], a[3], int(a[4]), a[5]),
     "measure": lambda: cmd_measure(a[1], a[2]),
     "tiles": lambda: cmd_tiles(*a[1:8]),
     "seeds_inner": lambda: cmd_seeds_inner(a[1], a[2], a[3], a[4]),
     "vgrid": lambda: cmd_vgrid(a[1], a[2], a[3], a[4]),
     "cover": lambda: cmd_cover(*a[1:8])}[a[0]]()
