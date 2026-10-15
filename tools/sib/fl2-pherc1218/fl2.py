# Provenance: Project HERCULES | owner the owner | [id removed]
"""RULES.md DECL-FL-1 / OWNER-STANDING-ORDER-5, tools/fl/BRIEF_PASS.md (dcb6a6b): First Letters extra pass,
SCROLL PHerc1218, PASS 2. Numbers only: no image, tile or CT pixel is ever opened for viewing; PNG tiles are written
for the census and never looked at here.

Adapted from tools/sib/fl-pherc0175a/fl.py (tracer sibling, branch tracer f06d743); differences are marked PASS2.
Bucket listing 2026-09-30T04:1xZ: PHerc1218/ has photos/, representations/, volumes/ only (no organizer segments),
so PASS 2 auto-grows up to 4 segments seeded in the OUTER third of the scroll radius (BRIEF_PASS item 2).
Rules fixed in this file before any PHerc1218 prediction or CT value is read:

seeds   m7 L4 (138 um) prediction >= 170. Occupied z range = slices with any such voxel. Seed k (k = 0..3) at
        z = 30/45/55/70 % of that range; in that slice: centre = centroid of the mask, R = p95 of mask radii.
        PASS2: target = centre + (5/6) R (cos, sin)(k * 90 deg + 45 deg), the middle of the outer third; the seed
        is the mask voxel (z +- 2 slices) with radius >= (2/3) R nearest the target. L4 -> L1: x8 + 4.
        In the local L1 crop the seed snaps to the nearest voxel >= 170 within 32 vox.
crop    m7 level 1 (17.28 um), chunk copy, cube of +-H = 80 x 20 + 128 L1 vox around the seed (clipped).
grow    PASS2: the OFFICIAL vc_grow_seg_from_seed of villa 41701aa (BRIEF_PASS item 1), params = the tracer
        preset L15 file (step 20 L1 vox = 0.3456 mm; its gate-only keys are not read by the official build),
        80 generations, voxelsize 17.28, normal grids from the official vc_gen_normalgrids on the crop.
check   native frame = (local + origin) x 2 (L0, 8.64 um); official vc_tifxyz_selfcross; if transverse crossings
        > 0, the v2 truncation (hercules.geometry.truncation), re-checked to 0. Keep only 0 crossings and area
        >= 16 cm^2 (BRIEF_PASS item 2).
tiles   ink tifs (C2-NT render, ink_9um step-075000, BOTH directions, no TTA) -> 2 x 2 cm tiles on the render canvas
        (1 px per 8.64 um voxel = 115.74 px/mm) from (0, 0); valid = mesh-valid canvas fraction; keep valid >= 0.5;
        u8; cv2.INTER_AREA to 1068 x 1068 (53.4 px/mm); PNG. Manifest fields per BRIEF_PASS item 4 (+ direction,
        ink_score of DECL-FL-1 item 2).
The voxel size is read from the volume's metadata.json at run time and must equal 8.64 um (I9).
Note: the base model was trained at 9.362 um; 8.64 um is an out-of-protocol transfer (as HRV-1 recorded).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

REPO = Path("/home/user/dominion")
sys.path.insert(0, str(REPO / "src"))
W = Path("/work/fl2_1218")
OUT = REPO / "logs/sib/fl2-pherc1218"
B = "vesuvius-challenge-open-data"
M7 = "PHerc1218/representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr"
VOL_KEY = "PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr"
VOL_URL = f"https://vesuvius-challenge-open-data.s3.amazonaws.com/{VOL_KEY}"
BIN = "/work/villa/volume-cartographer/build/hrc-release-gcc/bin"
IMG = "ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f"
SCROLL = "PHerc1218"
PASS = 2
VOX_UM = 8.64
GENS = 80
H = GENS * 20 + 128
TH = 170
C = 192


def s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=32), region_name="us-east-1")


def vc_cmd(app: str, args: list, cpus: int = 2) -> list:
    """Official villa 41701aa app inside the official deps image (docker/env/vc_wrapper.sh conventions)."""
    import os
    proxy = os.environ.get("HTTPS_PROXY", "")
    return ["docker", "run", "--rm", "--network", "host", "--cpus", str(cpus), "-e", f"OMP_NUM_THREADS={cpus}",
            "-e", f"HTTPS_PROXY={proxy}", "-e", f"https_proxy={proxy}", "-e", "HOME=/work/vchome",
            "-e", "SSL_CERT_FILE=/root/.ccr/ca-bundle.crt", "-e", "CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt",
            "-v", "/root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro", "-v", "/home/user:/home/user",
            "-v", "/work:/work", IMG, f"{BIN}/{app}", *args]


def selfcross(seg: Path, out_json: Path) -> dict:
    """Official vc_tifxyz_selfcross (as tools/sib/tracer/surfmetrics.selfcross)."""
    import subprocess
    with open(out_json.with_suffix(".log"), "w") as lf:
        rc = subprocess.run(vc_cmd("vc_tifxyz_selfcross", ["--surface", str(seg), "-o", str(out_json), "--threads", "2"]),
                            stdout=lf, stderr=subprocess.STDOUT).returncode
    if rc != 0:
        raise RuntimeError(f"selfcross failed rc={rc} for {seg}")
    return json.loads(out_json.read_text())


def crossing_pairs(report: dict) -> set:
    """Distinct unordered quad pairs reported TRANSVERSE (tools/sib/tracer/surfmetrics.crossing_pairs)."""
    pairs = set()
    for d in report["census"]:
        for c in d["transverse_contacts"]:
            a, b = tuple(c["quad1"]), tuple(c["quad2"])
            pairs.add((min(a, b), max(a, b)))
    return pairs


def quad_top_vertex(g: np.ndarray, quad: tuple) -> tuple:
    """(row, col) of the quad corner with the largest generation (tools/sib/tracer/surfmetrics.quad_top_vertex)."""
    v, u = quad
    cs = [(v, u), (v, u + 1), (v + 1, u), (v + 1, u + 1)]
    return max(cs, key=lambda rc: g[rc])


def cmd_voxel():
    """I9: voxel size from the volume's metadata.json (key samplePixelSize, in mm); must be 8.64 um."""
    cl = s3()
    md = json.loads(cl.get_object(Bucket=B, Key=f"{VOL_KEY}/metadata.json")["Body"].read())
    found = []

    def walk(o, path):
        if isinstance(o, dict):
            for k2, v in o.items():
                walk(v, f"{path}.{k2}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
        elif path.endswith(".samplePixelSize"):
            found.append((path, o))
    walk(md, "")
    um = sorted({round(float(v) * 1000.0, 6) for _, v in found})
    out = {"volume": VOL_KEY, "key": "samplePixelSize (mm)", "found": found, "voxel_um": um, "expected_um": VOX_UM}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "voxel.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out))
    if um != [VOX_UM]:
        raise SystemExit(f"voxel size in metadata.json {um} um != {VOX_UM} um")


def read_level(level: int, lo, hi) -> np.ndarray:
    """Read [lo, hi) (zyx) of an m7 level into memory (blosc chunks via numcodecs)."""
    import numcodecs
    cl = s3()
    za = json.loads(cl.get_object(Bucket=B, Key=f"{M7}/{level}/.zarray")["Body"].read())
    sep = za.get("dimension_separator", ".")
    codec = numcodecs.get_codec(za["compressor"])
    ch = za["chunks"]
    out = np.zeros([h - l for l, h in zip(lo, hi)], np.uint8)
    idx = [(z, y, x) for z in range(lo[0] // ch[0], (hi[0] - 1) // ch[0] + 1)
           for y in range(lo[1] // ch[1], (hi[1] - 1) // ch[1] + 1)
           for x in range(lo[2] // ch[2], (hi[2] - 1) // ch[2] + 1)]

    def get(k):
        try:
            b = cl.get_object(Bucket=B, Key=f"{M7}/{level}/{k[0]}{sep}{k[1]}{sep}{k[2]}")["Body"].read()
        except cl.exceptions.NoSuchKey:
            return k, None
        return k, np.frombuffer(codec.decode(b), np.uint8).reshape(ch)
    with ThreadPoolExecutor(16) as ex:
        for k, a in ex.map(get, idx):
            if a is None:
                continue
            s = [k[i] * ch[i] for i in range(3)]
            src = tuple(slice(max(lo[i] - s[i], 0), min(hi[i] - s[i], ch[i])) for i in range(3))
            dst = tuple(slice(max(s[i] - lo[i], 0), max(s[i] - lo[i], 0) + (src[i].stop - src[i].start)) for i in range(3))
            out[dst] = a[src]
    return out


def cmd_seeds():
    cl = s3()
    za = json.loads(cl.get_object(Bucket=B, Key=f"{M7}/4/.zarray")["Body"].read())
    v = read_level(4, (0, 0, 0), za["shape"])
    m = v >= TH
    zs = np.flatnonzero(m.any((1, 2)))
    z0, z1 = int(zs.min()), int(zs.max())
    seeds = []
    for k, f in enumerate((0.30, 0.45, 0.55, 0.70)):
        zt = int(round(z0 + f * (z1 - z0)))
        yy, xx = np.nonzero(m[zt])
        cy, cx = yy.mean(), xx.mean()
        R = np.percentile(np.hypot(yy - cy, xx - cx), 95)
        ang = math.radians(90 * k + 45)                                  # PASS2
        ty, tx = cy + (5 / 6) * R * math.sin(ang), cx + (5 / 6) * R * math.cos(ang)
        zlo = max(zt - 2, 0)
        zz, yy2, xx2 = np.nonzero(m[zlo:zt + 3])
        rr = np.hypot(yy2 - cy, xx2 - cx)
        ok = rr >= (2 / 3) * R                                          # PASS2: outer third only
        if not ok.any():
            raise SystemExit(f"seed {k}: no mask voxel in the outer third at z {zt}")
        zz, yy2, xx2, rr = zz[ok], yy2[ok], xx2[ok], rr[ok]
        i = int(np.argmin((yy2 - ty) ** 2 + (xx2 - tx) ** 2 + (zz + zlo - zt) ** 2))
        s4 = (int(zz[i] + zlo), int(yy2[i]), int(xx2[i]))
        seeds.append({"k": k, "z_frac": f, "seed_L4_zyx": s4, "seed_L1_zyx": [c * 8 + 4 for c in s4],
                      "centre_L4_yx": [float(cy), float(cx)], "R_L4": float(R),
                      "seed_radius_fraction": float(rr[i] / R), "target_angle_deg": 90 * k + 45})
    W.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    info = {"m7": f"s3://{B}/{M7}", "L4_shape": za["shape"], "occupied_z_L4": [z0, z1], "seeds": seeds}
    (W / "seeds.json").write_text(json.dumps(info, indent=1))
    (OUT / "seeds.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info))


def cmd_crop(k: int):
    """Local L1 crop (chunk copy) + seed snap. Writes W/seg{k}/crop.zarr and crop.json."""
    import numcodecs
    cl = s3()
    sd = json.loads((W / "seeds.json").read_text())["seeds"][k]
    za = json.loads(cl.get_object(Bucket=B, Key=f"{M7}/1/.zarray")["Body"].read())
    sep = za.get("dimension_separator", ".")
    shp = za["shape"]
    s = sd["seed_L1_zyx"]
    c0 = [max(0, (s[i] - H) // C) for i in range(3)]
    c1 = [min(-(-shp[i] // C), (s[i] + H) // C + 1) for i in range(3)]
    org = [c0[i] * C for i in range(3)]
    shape = [min(shp[i], c1[i] * C) - org[i] for i in range(3)]
    d = W / f"seg{k}"
    zp = d / "crop.zarr"
    (zp / "0").mkdir(parents=True, exist_ok=True)
    loc = dict(za); loc["shape"] = shape; loc["dimension_separator"] = "."
    (zp / "0/.zarray").write_text(json.dumps(loc))
    (zp / ".zgroup").write_text(json.dumps({"zarr_format": 2}))
    (zp / ".zattrs").write_text(json.dumps({"multiscales": [{"version": "0.4", "name": "/",
        "axes": [{"name": a, "type": "space"} for a in "zyx"],
        "datasets": [{"path": "0", "coordinateTransformations": [{"type": "scale", "scale": [1.0, 1.0, 1.0]}]}]}]}))
    (zp / "meta.json").write_text(json.dumps({"type": "vol", "uuid": f"fl2_1218_seg{k}", "name": f"fl2_1218_seg{k}",
        "format": "zarr", "width": shape[2], "height": shape[1], "slices": shape[0], "voxelsize": 2 * VOX_UM,
        "min": 0.0, "max": 255.0}))
    jobs = [(z, y, x) for z in range(c0[0], c1[0]) for y in range(c0[1], c1[1]) for x in range(c0[2], c1[2])]

    def get(j):
        dst = zp / "0" / f"{j[0]-c0[0]}.{j[1]-c0[1]}.{j[2]-c0[2]}"
        if dst.exists():
            return None
        try:
            b = cl.get_object(Bucket=B, Key=f"{M7}/1/{j[0]}{sep}{j[1]}{sep}{j[2]}")["Body"].read()
        except cl.exceptions.NoSuchKey:
            return None
        dst.write_bytes(b)
        return len(b)
    with ThreadPoolExecutor(16) as ex:
        sizes = [x for x in ex.map(get, jobs) if x]
    # seed snap: nearest voxel >= TH within 32 vox of the seed (local frame)
    import zarr
    a = zarr.open(str(zp / "0"), mode="r")
    ls = [s[i] - org[i] for i in range(3)]
    lo = [max(0, ls[i] - 32) for i in range(3)]
    blk = np.asarray(a[lo[0]:ls[0] + 33, lo[1]:ls[1] + 33, lo[2]:ls[2] + 33])
    pts = np.argwhere(blk >= TH)
    if len(pts) == 0:
        raise SystemExit(f"seed {k}: no prediction >= {TH} within 32 L1 vox")
    p = pts[np.argmin(((pts + lo - ls) ** 2).sum(1))] + lo
    info = {"k": k, "origin_L1_zyx": org, "shape": shape, "n_chunks_copied": len(sizes),
            "seed_local_zyx": [int(x) for x in p], "seed_L1_zyx": [int(p[i] + org[i]) for i in range(3)]}
    (d / "crop.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


def cmd_post(k: int):
    """Native frame, self-crossing check (+ v2 truncation), area; writes W/seg{k}/native.tifxyz + post.json."""
    import tifffile
    from hercules.geometry.tifxyz import area_cm2
    from hercules.geometry.truncation import truncate_mesh_points
    d = W / f"seg{k}"
    cr = json.loads((d / "crop.json").read_text())
    segs = [p for p in (d / "trace").iterdir() if p.is_dir() and (p / "x.tif").exists()]
    post = {"k": k, "n_outputs": len(segs)}
    if len(segs) != 1:
        post["keep"] = False; post["why"] = "no single trace output"
        (d / "post.json").write_text(json.dumps(post, indent=1)); print(json.dumps(post)); return
    src = segs[0]
    P = np.stack([tifffile.imread(src / f"{a}.tif") for a in "xyz"], -1).astype(np.float64)
    g = tifffile.imread(src / "generations.tif") if (src / "generations.tif").exists() else None
    v = P[..., 0] != -1
    o = np.array(cr["origin_L1_zyx"][::-1], float)                          # xyz
    N = np.where(v[..., None], (P + o) * 2.0, -1.0)
    nd = d / "native.tifxyz"
    nd.mkdir(exist_ok=True)

    def write(pts, gens):
        for i, a in enumerate("xyz"):
            tifffile.imwrite(nd / f"{a}.tif", pts[..., i].astype(np.float32), metadata=None, software=False)
        if gens is not None:
            tifffile.imwrite(nd / "generations.tif", gens.astype(np.uint16), metadata=None, software=False)
        vv = pts[..., 0] != -1
        (nd / "meta.json").write_text(json.dumps({"format": "tifxyz", "type": "seg", "uuid": f"fl2_1218_seg{k}",
            "scale": [1 / 40, 1 / 40], "bbox": [pts[vv].min(0).tolist(), pts[vv].max(0).tolist()],
            "hrc_frame": "native 8.64 um voxels of 20250521120456 (PHerc1218); grid step 40 vox (0.3456 mm)"}, indent=1))
    write(N, g)
    rep = selfcross(nd, d / "selfcross.json")
    pairs = crossing_pairs(rep)
    post["crossings_raw"] = len(pairs)
    post["area_raw_cm2"] = float(area_cm2(N, VOX_UM))
    if pairs and g is not None:
        gi = g.astype(np.int64)
        contacts = [(np.ravel_multi_index(quad_top_vertex(gi, q1), gi.shape),
                     np.ravel_multi_index(quad_top_vertex(gi, q2), gi.shape)) for q1, q2 in pairs]
        N2, tr = truncate_mesh_points(N, gi, contacts)
        write(N2, np.where(N2[..., 0] != -1, g, 0))
        rep2 = selfcross(nd, d / "selfcross_v2.json")
        post["crossings_after_v2"] = len(crossing_pairs(rep2))
        post["v2"] = {"cutoff": tr.cutoff, "n_contacts": tr.n_contacts, "n_removed": tr.n_removed}
        N = N2
    post["crossings_final"] = post.get("crossings_after_v2", len(pairs))
    post["area_cm2"] = float(area_cm2(N, VOX_UM))
    post["keep"] = post["crossings_final"] == 0 and post["area_cm2"] >= 16.0
    (d / "post.json").write_text(json.dumps(post, indent=1))
    print(json.dumps(post))


def _u8(ink):
    if ink.ndim == 3:
        ink = ink[..., 0] if ink.shape[-1] < ink.shape[0] else ink[0]
    if ink.dtype == np.uint8:
        return ink
    f = ink.astype(np.float64)
    mx = float(np.nanmax(f)) if f.size else 0.0
    scale = 255.0 if mx <= 1.0 else (255.0 / 65535.0 if mx > 255 else 1.0)
    return np.clip(np.rint(np.nan_to_num(f) * scale), 0, 255).astype(np.uint8)


def cmd_tiles(k: int):
    """2 x 2 cm tiles of both ink directions of segment k (BRIEF_PASS item 4; DECL-FL-1 item 1). Never displayed."""
    import cv2
    import tifffile
    d = W / f"seg{k}"
    name = f"seg{k}"
    sid = f"{SCROLL}_fl{PASS}_seg{k}"
    X = tifffile.imread(d / "native.tifxyz/x.tif")
    gv = X != -1
    ppm = 1000.0 / VOX_UM                                   # canvas px per mm (1 px per 8.64 um voxel)
    T = int(round(20 * ppm))
    td = OUT / name / "tiles"
    td.mkdir(parents=True, exist_ok=True)
    man = {"scroll": SCROLL, "pass": PASS, "segment": sid, "source": "auto",
           "checkpoint_sha256": "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab",
           "chain": "C2-NT: official vc_render_tifxyz -n 31 --flip-normals (villa 41701aa); official infer, both "
                    "directions, no TTA, CPU",
           "canvas_px_per_mm": ppm, "tile_canvas_px": T, "tile_px": 1068, "px_per_mm": 1068 / 20.0, "tiles": []}
    for direction, f in (("forward", d / "ink.tif"), ("reverse", d / "ink_reverse.tif")):
        if not f.exists():
            raise SystemExit(f"missing {f}")
        ink = _u8(tifffile.imread(f))
        fy, fx = ink.shape[0] / gv.shape[0], ink.shape[1] / gv.shape[1]
        man.setdefault("grid_to_canvas", [fy, fx])
        for r in range(-(-ink.shape[0] // T)):
            for c in range(-(-ink.shape[1] // T)):
                y0, x0 = r * T, c * T
                yy = np.arange(y0, y0 + T); xx = np.arange(x0, x0 + T)
                inside = (yy[:, None] < ink.shape[0]) & (xx[None, :] < ink.shape[1])
                gy = np.minimum((yy / fy).astype(int), gv.shape[0] - 1)
                gx = np.minimum((xx / fx).astype(int), gv.shape[1] - 1)
                valid = gv[gy[:, None], gx[None, :]] & inside
                vf = float(valid.mean())
                if vf < 0.5:
                    continue
                t = np.zeros((T, T), np.uint8)
                sub = ink[y0:y0 + T, x0:x0 + T]
                t[:sub.shape[0], :sub.shape[1]] = sub
                t[~valid] = 0
                t = cv2.resize(t, (1068, 1068), interpolation=cv2.INTER_AREA)
                fn = td / f"{sid}_{direction}_r{r}_c{c}.png"
                cv2.imwrite(str(fn), t)
                vv = cv2.resize(valid.astype(np.uint8), (1068, 1068), interpolation=cv2.INTER_NEAREST).astype(bool)
                man["tiles"].append({"segment": sid, "r": r, "c": c, "direction": direction, "png": fn.name,
                                     "png_sha256": hashlib.sha256(fn.read_bytes()).hexdigest(), "valid_fraction": vf,
                                     "px_per_mm": 1068 / 20.0, "source": "auto", "pass": PASS,
                                     "ink_score": float(np.mean(t[vv] >= 128)) if vv.any() else 0.0})
    (OUT / name / "manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    print(json.dumps({"segment": sid, "n_tiles": len(man["tiles"])}))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "seeds":
        cmd_seeds()
    elif c == "voxel":
        cmd_voxel()
    else:
        {"crop": cmd_crop, "post": cmd_post, "tiles": cmd_tiles}[c](int(sys.argv[2]))
