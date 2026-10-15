"""DECL-FL-1 First Letters screen, PHerc0800: segments -> C2-NT render -> ink_9um (both directions, no TTA, CPU)
-> 2 x 2 cm tiles (u8, INTER_AREA to 1068 px, PNG, valid >= 50 %). Idempotent: each unit writes a .done marker.

Provenance: Project HERCULES | owner the owner | [id removed]
Builder only: never opens, views or describes a pixel; writes numbers, hashes and PNG bytes.
Steps per segment: fetch mesh -> render (vc_render_tifxyz -n 31 --flip-normals, full canvas, --scale 1) ->
infer (vesuvius.ink_detection.inference.infer, step-075000, --direction both, no TTA) -> tiles + manifest.json.
The caller (pipeline.sh) commits and pushes after each unit.
Usage: /opt/hv/bin/python fl_driver.py <unit>  where unit = select | seg:<id> | tiles:<id>
"""
import glob, hashlib, json, os, subprocess, sys, time, urllib.request
import numpy as np

PROV = "Project HERCULES | owner the owner | [id removed]"
SCROLL = "PHerc0800"
VOL_ID = "20250521135224"
VOX_UM = 8.64
BASE = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
VOL = f"{BASE}/{SCROLL}/volumes/{VOL_ID}-8.640um-1.2m-116keV-masked.zarr/"
CKPT = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
CKPT_SHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
WK = "/work/fl-pherc0800"
REPO = subprocess.check_output(["git", "-C", os.path.dirname(os.path.abspath(__file__)), "rev-parse", "--show-toplevel"], text=True).strip()
OUT = f"{REPO}/logs/sib/fl-pherc0800"
VC = "/work/bin/vc"
N_SEG = 3
TILE_MM, OUT_SIDE, ELIG = 20.0, 1068, 0.5
sys.path.insert(0, f"{REPO}/src")


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def get(url, dst):
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(dst + ".tmp", "wb") as f:
                f.write(r.read())
            os.replace(dst + ".tmp", dst)
            return
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(url)


def list_segments():
    import re
    t = urllib.request.urlopen(f"{BASE}/?list-type=2&prefix={SCROLL}/segments/&delimiter=/").read().decode()
    return [p.split("/")[2] for p in re.findall(r"<Prefix>([^<]+)</Prefix>", t) if p.count("/") == 3]


def mesh_dir(seg):
    sid = seg.split("-")[0]
    return f"{SCROLL}/segments/{seg}/mesh/{sid}-on-{VOL_ID}-{VOX_UM:g}um.tifxyz"


def fetch_mesh(seg):
    import tifffile
    d = f"{WK}/{seg}/mesh.tifxyz"
    os.makedirs(d, exist_ok=True)
    rec = {}
    for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
        p = f"{d}/{f}"
        if not os.path.exists(p):
            get(f"{BASE}/{mesh_dir(seg)}/{f}", p)
        rec[f] = sha(p)
    P = np.stack([tifffile.imread(f"{d}/{a}.tif").astype(np.float64) for a in "xyz"], -1)
    valid = (P != -1).all(-1) & np.isfinite(P).all(-1)
    return d, P, valid, rec


def grid_stats(P, valid):
    e1 = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[valid[:, 1:] & valid[:, :-1]]
    e2 = np.linalg.norm(P[1:] - P[:-1], axis=-1)[valid[1:] & valid[:-1]]
    med = float(np.median(np.r_[e1, e2]))
    area_cm2 = float(valid.sum() * (med * VOX_UM / 1e4) ** 2)
    return med, area_cm2


def select():
    """Unit 'select': the N_SEG largest organizer tifxyz segments by mesh-valid area."""
    os.makedirs(OUT, exist_ok=True)
    segs = []
    for s in list_segments():
        try:
            _, P, v, rec = fetch_mesh(s)
        except Exception as e:
            segs.append({"segment": s, "error": str(e)})
            continue
        med, a = grid_stats(P, v)
        segs.append({"segment": s, "grid_shape": list(v.shape), "valid_fraction": float(v.mean()),
                     "median_edge_vox": med, "area_cm2": round(a, 3), "mesh_sha256": rec})
    ok = sorted([x for x in segs if "area_cm2" in x], key=lambda x: -x["area_cm2"])
    chosen = [x["segment"] for x in ok[:N_SEG]]
    json.dump({"provenance": PROV, "declaration": "RULES.md DECL-FL-1 item 1", "scroll": SCROLL, "volume": VOL,
               "rule": f"{N_SEG} largest organizer tifxyz segments by mesh-valid area (grid valid count x median edge^2)",
               "segments": segs, "chosen": chosen, "utc": utc()}, open(f"{OUT}/segments.json", "w"), indent=1)
    print("chosen", chosen)


def run_logged(cmd, log, env=None):
    with open(log, "a") as lf:
        lf.write(f"\n[{utc()}] $ {' '.join(cmd)}\n")
        lf.flush()
        return subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env).returncode


def seg_unit(seg):
    """Render + infer for one segment (the long unit)."""
    d = f"{WK}/{seg}"
    os.makedirs(d, exist_ok=True)
    mdir, P, v, rec = fetch_mesh(seg)
    render = f"{d}/render.zarr"
    if not os.path.exists(f"{render}.done"):
        subprocess.run(["rm", "-rf", render])
        env = dict(os.environ, VC_CPUS="3", OMP_NUM_THREADS="3")
        rc = run_logged([VC, "vc_render_tifxyz", "-v", VOL, "--remote-url", VOL, "--segmentation", mdir, "--scale", "1",
                         "--group-idx", "0", "--num-slices", "31", "--slice-step", "1", "--voxel-size", str(VOX_UM),
                         "--voxel-unit", "micrometer", "--flip-normals", "--cache-gb", "2", "--zarr-output", render],
                        f"{d}/render.log", env)
        if rc != 0:
            raise SystemExit(f"render rc={rc}")
        open(f"{render}.done", "w").write(utc())
    pred = f"{d}/pred.tif"
    if not os.path.exists(f"{pred}.done"):
        assert sha(CKPT) == CKPT_SHA
        env = dict(os.environ, OMP_NUM_THREADS="3")
        rc = run_logged(["/opt/hv-ink/bin/python", "-m", "vesuvius.ink_detection.inference.infer", render, CKPT, pred,
                         "--direction", "both", "--batch-size", "4", "--num-workers", "1", "--no-compile"],
                        f"{d}/infer.log", env)
        if rc != 0 or not os.path.exists(pred):
            raise SystemExit(f"infer rc={rc}")
        open(f"{pred}.done", "w").write(json.dumps({"utc": utc(), "sha256": sha(pred)}))


def tiles_unit(seg):
    import tifffile, cv2
    from hercules.display import builder
    d = f"{WK}/{seg}"
    mdir, P, valid, rec = fetch_mesh(seg)
    pred = tifffile.imread(f"{d}/pred.tif")
    pred = np.asarray(pred)
    if pred.ndim == 3:
        pred = pred[0] if pred.shape[0] == 1 else pred[..., 0]
    gh, gw = valid.shape
    H, W = pred.shape
    s = H / gh
    assert abs(s - W / gw) < 1e-6, (pred.shape, valid.shape)
    med, area = grid_stats(P, valid)
    px_mm = s / (med * VOX_UM / 1000)
    T = int(round(TILE_MM * px_mm))
    od = f"{OUT}/{seg}/tiles"
    os.makedirs(od, exist_ok=True)
    tiles = []
    for r in range(-(-H // T)):
        for c in range(-(-W // T)):
            y0, y1, x0, x1 = r * T, min((r + 1) * T, H), c * T, min((c + 1) * T, W)
            ys, xs = np.arange(r * T, (r + 1) * T), np.arange(c * T, (c + 1) * T)
            inb = (ys < H)[:, None] & (xs < W)[None, :]
            m = valid[np.ix_(np.minimum(ys, H - 1) * gh // H, np.minimum(xs, W - 1) * gw // W)] & inb
            vf = float(m.mean())
            if vf < ELIG:
                continue
            crop = np.zeros((T, T), pred.dtype)
            crop[: y1 - y0, : x1 - x0] = pred[y0:y1, x0:x1]
            u8 = builder.model_map_u8(crop)
            raw = u8[m]
            u8[~m] = 0
            disp = cv2.resize(u8, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
            b = builder.png_bytes(disp)
            fn = f"{seg}_r{r}_c{c}.png"
            open(f"{od}/{fn}", "wb").write(b)
            tiles.append({"segment": seg, "r": r, "c": c, "file": f"tiles/{fn}", "png_sha256": hashlib.sha256(b).hexdigest(),
                          "valid_fraction": round(vf, 4), "px_per_mm": px_mm,
                          "ink_score_raw_frac_ge_128": round(float((raw >= 128).mean()), 5),
                          "source": {"prediction": f"{WK}/{seg}/pred.tif", "prediction_sha256": json.load(open(f"{d}/pred.tif.done"))["sha256"],
                                     "render": "vc_render_tifxyz -n 31 --flip-normals --scale 1 (C2-NT)",
                                     "model": f"ink_9um hybrid_3d2d-seed42 step-075000 sha256 {CKPT_SHA}, --direction both, no TTA, CPU",
                                     "mesh": rec, "volume": VOL}})
    json.dump({"provenance": PROV, "declaration": "RULES.md DECL-FL-1 item 1", "scroll": SCROLL, "segment": seg,
               "canvas_shape": [H, W], "grid_shape": [gh, gw], "px_per_mm": px_mm, "T_canvas_px": T,
               "tile_rule": "2 x 2 cm from canvas (0,0); u8 = hercules builder.model_map_u8; 0 outside mesh-valid; cv2 INTER_AREA to 1068 px; valid >= 0.5",
               "n_tiles": len(tiles), "tiles": tiles, "utc": utc()}, open(f"{OUT}/{seg}/manifest.json", "w"), indent=1)
    open(f"{d}/tiles.done", "w").write(utc())
    print("tiles", seg, len(tiles))


if __name__ == "__main__":
    u = sys.argv[1]
    if u == "select":
        select()
    elif u.startswith("seg:"):
        seg_unit(u[4:])
    elif u.startswith("tiles:"):
        tiles_unit(u[6:])
