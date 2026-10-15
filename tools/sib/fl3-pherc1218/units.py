"""First Letters extra pass 3, PHerc1218 (tools/fl/BRIEF_PASS.md @ dcb6a6ba; RULES.md DECL-FL-1).
Idempotent units; each finished unit writes /work/fl3/state/<unit>.done and pushes to the worker branch.
Numbers, hashes and file lists only: no image, tile or CT pixel is ever opened for viewing.
Provenance: Project HERCULES | owner the owner | [id removed]
"""
import hashlib, json, os, subprocess, sys, time, urllib.request, glob
import numpy as np

REPO = "/home/user/dominion"; BR = "claude/gifted-bell-gavnl5-sib-p4-inner"
W = "/work/fl3"; ST = f"{W}/state"; LOG = f"{REPO}/logs/sib/fl3-pherc1218"
S3H = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc1218"
VOL = "volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr"
SURF = "representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr"
VOX_UM = 8.64; CKPT = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
CKPT_SHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
N_SEEDS = 4; MIN_AREA_CM2 = 16.0; OUT_SIDE = 1068
os.makedirs(ST, exist_ok=True); os.makedirs(LOG, exist_ok=True)

def done(u): return os.path.exists(f"{ST}/{u}.done")
def mark(u, info=None):
    json.dump(info or {}, open(f"{ST}/{u}.done", "w"))
def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line, flush=True); open(f"{LOG}/progress.log", "a").write(line + "\n")
def sh(cmd, logf, timeout=None):
    with open(logf, "a") as fh:
        fh.write(f"\n# {time.strftime('%FT%TZ', time.gmtime())} {cmd}\n"); fh.flush()
        return subprocess.run(cmd, shell=True, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout).returncode
def push(msg):
    subprocess.run(f"cd {REPO} && git add logs/sib/fl3-pherc1218 tools/sib/fl3-pherc1218", shell=True)
    if subprocess.run(f"cd {REPO} && git diff --cached --quiet", shell=True).returncode == 0: return
    subprocess.run(["git", "-C", REPO, "commit", "-q", "-m", f"fl3-pherc1218: {msg}\n\nProvenance: Project HERCULES | [id removed]\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01AXfmasnYmkW3pgGvTRpDwK"])
    for i in range(4):
        if subprocess.run(f"cd {REPO} && git push -q origin {BR}", shell=True).returncode == 0: return
        time.sleep(2 ** (i + 1))

def get(url):
    for i in range(5):
        try: return urllib.request.urlopen(url, timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
        except Exception: pass
        time.sleep(2 ** i)
    raise RuntimeError(url)

def unit_env():
    if done("env"): return
    rc = sh(f"bash {REPO}/docker/env/setup_env.sh", "/work/logs/fl3_env.log")
    assert rc == 0, "setup_env failed"
    h = hashlib.sha256(open(CKPT, "rb").read()).hexdigest(); assert h == CKPT_SHA, h
    mark("env", {"ckpt_sha256": h}); log("env ok")

def read_raw_level(level):
    za = json.loads(get(f"{S3H}/{VOL}/{level}/.zarray")); shp = za["shape"]; C = za["chunks"][0]
    a = np.zeros(shp, np.uint8)
    for cz in range(-(-shp[0] // C)):
        for cy in range(-(-shp[1] // C)):
            for cx in range(-(-shp[2] // C)):
                b = get(f"{S3H}/{VOL}/{level}/{cz}/{cy}/{cx}")
                if b is None: continue
                blk = np.frombuffer(b, np.uint8).reshape(C, C, C)
                sl = tuple(slice(i * C, min((i + 1) * C, n)) for i, n in zip((cz, cy, cx), shp))
                a[sl] = blk[:sl[0].stop - sl[0].start, :sl[1].stop - sl[1].start, :sl[2].stop - sl[2].start]
    return a

def unit_seeds():
    if done("seeds"): return
    L = 5; f = 2 ** L; A = read_raw_level(L) > 0
    area = A.sum((1, 2)); zs = np.where(area > 50)[0]; z0, z1 = int(zs.min()), int(zs.max())
    sza = json.loads(get(f"{S3H}/{SURF}/1/.zarray")); SC = sza["chunks"][0]
    import numcodecs
    comp = numcodecs.get_codec(sza["compressor"])
    def surf_chunk(cz, cy, cx):
        b = get(f"{S3H}/{SURF}/1/{cz}/{cy}/{cx}")
        return None if b is None else np.frombuffer(comp.decode(b), np.uint8).reshape(SC, SC, SC)
    seeds = []
    for k, (zf, ang) in enumerate(zip((0.30, 0.45, 0.60, 0.75), (45, 135, 225, 315))):
        zl = int(round(z0 + zf * (z1 - z0))); m = A[zl]; yy, xx = np.nonzero(m)
        cy, cx = yy.mean(), xx.mean(); R = float(np.sqrt(m.sum() / np.pi))
        rr = R / 6.0; th = np.radians(ang)
        p1 = np.array([zl * f + f / 2, (cy + rr * np.sin(th)) * f + f / 2, (cx + rr * np.cos(th)) * f + f / 2]) / 2.0  # level-1 zyx
        c = (p1 // SC).astype(int); blk = surf_chunk(*c); best = None
        if blk is not None:
            idx = np.argwhere(blk >= 128)
            if len(idx):
                g = idx + c * SC; ctr_l1 = np.array([zl * f + f / 2, cy * f + f / 2, cx * f + f / 2]) / 2.0
                r_ok = np.hypot(g[:, 1] - ctr_l1[1], g[:, 2] - ctr_l1[2]) <= (R * f / 3.0) / 2.0  # level-1 vox; inner third
                g = g[r_ok] if r_ok.any() else g[:0]
                if len(g): best = g[np.argmin(np.linalg.norm(g - p1, axis=1))]
        rec = {"k": k, "z_frac": zf, "angle_deg": ang, "centre_L0_zyx": [zl * f + f / 2, cy * f + f / 2, cx * f + f / 2], "R_eq_L0_vox": R * f,
               "target_r_L0_vox": rr * f, "inner_third_limit_L0_vox": R * f / 3.0}
        if best is not None:
            z, y, x = (best * 2 + 1).tolist(); rec.update({"seed_xyz_L0": [x, y, z], "seed_r_L0_vox": float(np.hypot(y - rec["centre_L0_zyx"][1], x - rec["centre_L0_zyx"][2]))})
        seeds.append(rec)
    out = {"scroll": "PHerc1218", "rule": "PASS 3: no organizer segments -> auto-grow up to 4 seeded in the INNER third of the radius",
           "centre_radius_method": f"level-{L} masked volume (>0) per z: centroid and equivalent radius sqrt(area/pi)", "z_extent_L0": [z0 * f, z1 * f + f - 1],
           "seed_snap": "nearest level-1 surface-m7 voxel >= 128 within the seed's 192^3 level-1 chunk and inside the inner third", "seeds": seeds}
    json.dump(out, open(f"{LOG}/seeds.json", "w"), indent=1)
    mark("seeds", {"n_valid": sum("seed_xyz_L0" in s for s in seeds)}); log(f"seeds: {sum('seed_xyz_L0' in s for s in seeds)} valid"); push("seeds")

def unit_grow(k):
    u = f"grow{k}"
    if done(u): return
    s = json.load(open(f"{LOG}/seeds.json"))["seeds"][k]
    if "seed_xyz_L0" not in s:
        mark(u, {"skipped": "no surface voxel near seed"}); log(f"{u} skipped"); return
    d = f"{W}/grow/s{k}"; os.makedirs(d, exist_ok=True); os.makedirs(f"{W}/cache", exist_ok=True)
    params = {"use_cuda": False, "step_size": 20, "min_area_cm": 0.3, "generations": 400, "thread_limit": 3,
              "cache_root": f"{W}/cache", "voxelsize": VOX_UM, "cache_size": 4e9}
    json.dump(params, open(f"{d}/params.json", "w"), indent=1)
    x, y, z = s["seed_xyz_L0"]
    name = f"fl3_pherc1218_s{k}"
    rc = sh(f"/work/bin/vc vc_grow_seg_from_seed -v {S3H}/{SURF}/ -t {d}/{name} -p {d}/params.json -s {x} {y} {z} --segment-name {name} --skip-overlap-check",
            f"{W}/grow/s{k}.log", timeout=8 * 3600)
    meta = glob.glob(f"{d}/**/meta.json", recursive=True)
    info = {"rc": rc, "params": params, "seed_xyz": [x, y, z], "meta": meta}
    mark(u, info); log(f"{u} rc={rc} meta={len(meta)}")

def seg_dir(k):
    m = glob.glob(f"{W}/grow/s{k}/**/meta.json", recursive=True)
    return os.path.dirname(m[0]) if m else None

def unit_filter(k):
    u = f"filter{k}"
    if done(u): return
    d = seg_dir(k); rec = {"k": k, "segment_dir": d}
    if d:
        meta = json.load(open(f"{d}/meta.json")); area = float(meta.get("area_vx2", 0)) * (VOX_UM * 1e-4) ** 2
        rep = f"{W}/grow/s{k}_selfcross.json"
        rc = sh(f"/work/bin/vc vc_tifxyz_selfcross {d} -o {rep}", f"{W}/grow/s{k}.log")
        txt = open(rep).read() if os.path.exists(rep) else ""
        try: nx = int(json.loads(txt).get("transverse_total", -1))
        except Exception: nx = -1
        rec.update({"area_cm2": round(area, 2), "selfcross_rc": rc, "self_intersections": nx,
                    "keep": bool(nx == 0 and area >= MIN_AREA_CM2)})
    else:
        rec["keep"] = False; rec["reason"] = "no segment grown"
    json.dump(rec, open(f"{LOG}/filter_s{k}.json", "w"), indent=1)
    mark(u, rec); log(f"{u} {rec}"); push(f"filter s{k} keep={rec['keep']}")

def unit_render_infer(k):
    u = f"infer{k}"
    if done(u) or not json.load(open(f"{ST}/filter{k}.done")).get("keep"): return
    d = seg_dir(k); out = f"{W}/render/s{k}.zarr"; os.makedirs(f"{W}/render", exist_ok=True)
    if not done(f"render{k}"):
        rc = sh(f"/work/bin/vc vc_render_tifxyz -v s3://vesuvius-challenge-open-data/PHerc1218/{VOL}/ --remote-url s3://vesuvius-challenge-open-data/PHerc1218/{VOL}/ "
                f"--segmentation {d} --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size {VOX_UM} --voxel-unit micrometer --flip-normals --cache-gb 4 --zarr-output {out}",
                f"{W}/render/s{k}.log", timeout=12 * 3600)
        assert rc == 0, f"render s{k} rc={rc}"; mark(f"render{k}"); log(f"render{k} ok")
    os.makedirs(f"{W}/infer/s{k}", exist_ok=True)
    rc = sh(f"OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer {out} {CKPT} {W}/infer/s{k}/s{k}.tif --direction both --batch-size 4 --num-workers 1 --no-compile",
            f"{W}/infer/s{k}.log", timeout=24 * 3600)
    assert rc == 0, f"infer s{k} rc={rc}"; mark(u); log(f"{u} ok")

def unit_tiles(k):
    u = f"tiles{k}"
    if done(u) or not json.load(open(f"{ST}/filter{k}.done")).get("keep"): return
    sys.path.insert(0, f"{REPO}/src"); from hercules.display import builder
    import tifffile
    d = seg_dir(k); seg = f"fl3_pherc1218_s{k}"
    P = np.stack([tifffile.imread(f"{d}/{c}.tif").astype(np.float32) for c in "xyz"], -1)
    valid = ~(P == -1).any(-1) & np.isfinite(P).all(-1); gh, gw = valid.shape
    pred = tifffile.imread(f"{W}/infer/s{k}/s{k}.tif"); assert pred.dtype == np.uint8, pred.dtype
    H, W_ = pred.shape[-2:]; pred = pred.reshape(H, W_)
    e = np.concatenate([np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[valid[:, 1:] & valid[:, :-1]],
                        np.linalg.norm(P[1:] - P[:-1], axis=-1)[valid[1:] & valid[:-1]]])
    px_per_mm = float(np.sqrt((H / gh) * (W_ / gw)) / (np.median(e) * VOX_UM / 1000)); T = int(round(20 * px_per_mm))
    od = f"{LOG}/{seg}/tiles"; os.makedirs(od, exist_ok=True); tiles = []
    for r in range(-(-H // T)):
        for c in range(-(-W_ // T)):
            y0, x0 = r * T, c * T; ys = np.arange(y0, y0 + T); xs = np.arange(x0, x0 + T)
            m = valid[np.ix_(np.clip(ys * gh // H, 0, gh - 1), np.clip(xs * gw // W_, 0, gw - 1))] & (ys < H)[:, None] & (xs < W_)[None, :]
            vf = float(m.mean())
            if vf < 0.5: continue
            crop = np.zeros((T, T), np.uint8); hh, ww = min(T, H - y0), min(T, W_ - x0); crop[:hh, :ww] = pred[y0:y0 + hh, x0:x0 + ww]
            crop[~m] = 0; b = builder.png_bytes(builder.area_downscale(crop, OUT_SIDE / T))
            fn = f"{seg}_r{r}_c{c}.png"; open(f"{od}/{fn}", "wb").write(b)
            tiles.append({"segment": seg, "r": r, "c": c, "file": f"tiles/{fn}", "png_sha256": hashlib.sha256(b).hexdigest(), "valid_fraction": vf,
                          "px_per_mm": px_per_mm, "source": "auto", "pass": 3})
    man = {"provenance": "Project HERCULES | [id removed]", "brief": "tools/fl/BRIEF_PASS.md @ dcb6a6ba", "scroll": "PHerc1218", "pass": 3, "segment": seg,
           "source": "auto", "volume": VOL, "surface_prediction": SURF, "ink_model": {"path": "HF scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth", "sha256": CKPT_SHA},
           "chain": "vc_render_tifxyz -n 31 --flip-normals; official infer --direction both, no TTA, CPU; tiles from the forward-order prediction",
           "px_per_mm": px_per_mm, "T_canvas_px": T, "display": "u8 prediction, 0 outside mesh-valid, INTER_AREA to 1068 px, PNG", "filter": json.load(open(f"{LOG}/filter_s{k}.json")),
           "tiles": tiles}
    json.dump(man, open(f"{LOG}/{seg}/manifest.json", "w"), indent=1)
    mark(u, {"n": len(tiles)}); log(f"{u} n={len(tiles)}"); push(f"tiles s{k} n={len(tiles)}")

def main():
    unit_env(); unit_seeds()
    for k in range(N_SEEDS):
        unit_grow(k); unit_filter(k)
    for k in range(N_SEEDS):
        unit_render_infer(k); unit_tiles(k)
    n = sum(json.load(open(f"{ST}/tiles{k}.done")).get("n", 0) for k in range(N_SEEDS) if done(f"tiles{k}"))
    if not done("final"):
        kept = sum(json.load(open(f"{ST}/filter{k}.done")).get("keep", False) for k in range(N_SEEDS))
        line = f"DONE {n} tiles" + ("" if kept else " (no auto-grown segment passed the filter: 0 self-intersections and >= 16 cm^2)")
        open(f"{LOG}/STATUS.md", "a").write(line + "\n"); mark("final", {"n": n}); log(line); push("DONE")
    print("ALL_DONE", flush=True)

if __name__ == "__main__":
    main()
