# Provenance: Project HERCULES | owner the owner | [id removed]
"""D2 training pairs for PHerc0139 (task pairs0139; RULES.md DECL-D2 pair definition). Numbers only: no image is
opened, displayed or described; pixel arrays are never printed.

Per segment (python build_pairs.py SEG [--max-tiles N]):
1. Render: official vc_render_tifxyz of the organizer 9.362 um mesh on volume 20250728140407 (streamed from S3),
   --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size <metadata.json> --voxel-unit micrometer
   --auto-crop --flip-normals. The output origin is the --auto-crop rectangle (hercules.pipeline.canvas.auto_crop_rect)
   and is asserted against the output shape.
2. Candidate tiles: 128 x 128 on the 9.362 um canvas, stride 128 anchored at canvas (0, 0); >= 90 % render-valid
   (any of 31 slices > 0), >= 90 % 2.4-um-valid, no Rule-S pixel (exclude.py), segment not excluded.
3. Gates (logs/sib/pairs0139/gate_spec.json, fixed before any gate number): CT reference = organizer 2.399 um SV
   level 1, mean of slices 52..56, area-averaged onto the 9.362 um pixel through the fitted affine M (meshfit.py);
   ours = render slice 15. NCC0 >= 0.80 at zero shift, and >= 7 of 9 windows (64 px, offsets {0,32,64}^2) with a
   best shift (+-4 px search, parabolic refinement) of Euclidean length <= 1.0 px, not on the search border.
4. Labels: organizer ink map 20260417190342 area-averaged the same way: ink >= 150 (1), blank <= 100 (0), else 255
   (ignored); 255 also where the pixel is not render-valid or not 2.4-um-valid. Where the official 2.399 um human
   label set 20260918 exists, 'human' holds 1 / 0 / 255 (all 16 sub-samples supervised; ink if >= half are ink).
5. Output: kept tiles -> /work/p139/out/shards/<seg>_sNN.npz (images uint8 (N,21,128,128) = render slices 5..25,
   label uint8 (N,128,128), inkmap uint8 (N,128,128) = rounded area-averaged map value, human uint8 (N,128,128)),
   registry rows (JSON lines) for every candidate, kept or not, with gate numbers and 3-D coordinates.
"""
import argparse, hashlib, json, math, os, subprocess, sys, time, datetime
import numpy as np
import zarr, tifffile
from scipy import ndimage as ndi
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
from hercules.pipeline.canvas import canvas_for, auto_crop_rect
from sv24 import SV24
from meshfit import load_T
from fetch import get, listing

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
S3 = "/work/p139/s3"
SEGS = f"{S3}/PHerc0139/segments"
VOL = "s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/"
META9 = f"{S3}/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/metadata.json"
META24 = f"{S3}/PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/metadata.json"
OUT = os.environ.get("P139_OUT", "/work/p139/out")
RENDER = "/work/p139/render"
VC = "/work/bin/vc"
T = 128
Z0, Z1 = 5, 26                     # stored slices 5..25 (21, surface = stored index 10)
ZS = 15                            # surface slice of -n 31
L1_Z0, L1_Z1 = 52, 57              # 2.399 um SV slices 52..56 (surface 54 of 109)
SUB = 4                            # 4 x 4 sub-samples per 9.362 um pixel
NCC_MIN, WIN, WOFF, SMAX, ALIGN_PX, NWIN_MIN = 0.80, 64, (0, 32, 64), 4, 1.0, 7
LAB_INK, LAB_BLANK = 150, 100
SHARD_TILES = 200
# READ-CAL / PROBE / D1-canary windows on 0139 (organizer 9.362 um canvas, 2136 px) -- tagged, not excluded
TAG_WINDOWS = {"w030": [(2816, 3072)], "w035": [(1792, 768)], "w039": [(2816, 3840)], "w043": [(3072, 4608)],
               "w040": [(2048, 2048), (2560, 4096), (256, 512), (3072, 4352)],
               "w044": [(2816, 2816), (3328, 2816), (4096, 1024)]}
TAG_PX = 2136


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def voxel_um(meta=META9):
    d = json.load(open(meta))
    return float(d["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000.0


F_PLAIN = voxel_um(META9) / voxel_um(META24)       # reported plain-scaling control only


def short(seg):
    return seg.split("-")[1].split("_")[0]


# ----------------------------------------------------------------------------------------------------------- render
def render(seg, log):
    ts = seg.split("-")[0]
    mesh = f"{SEGS}/{seg}/mesh/{ts}-on-20250728140407-9.362um.tifxyz"
    out = f"{RENDER}/{short(seg)}.zarr"
    done = out + ".done.json"
    if os.path.exists(done):
        return out, json.load(open(done))
    os.makedirs(RENDER, exist_ok=True)
    subprocess.run(["rm", "-rf", out])
    vs = voxel_um()
    cmd = ["vc_render_tifxyz", "-v", VOL, "--remote-url", VOL, "--segmentation", mesh, "--scale", "1",
           "--group-idx", "0", "--num-slices", "31", "--slice-step", "1", "--voxel-size", f"{vs:g}",
           "--voxel-unit", "micrometer", "--auto-crop", "--flip-normals", "--cache-gb", "4", "--zarr-output", out]
    start = utc(); t0 = time.time()
    env = dict(os.environ, VC_CPUS=os.environ.get("VC_CPUS", "3"), OMP_NUM_THREADS=os.environ.get("VC_CPUS", "3"))
    with open(out + ".log", "w") as lf:
        rc = subprocess.run([VC, *cmd], stdout=lf, stderr=subprocess.STDOUT, env=env).returncode
    rec = dict(command=f"VC_CPUS={env['VC_CPUS']} {VC} " + " ".join(cmd), start=start, end=utc(), exit=rc,
               seconds=round(time.time() - t0, 1), voxel_size_um=vs)
    log(dict(event="render", segment=seg, **rec))
    if rc != 0:
        raise SystemExit(f"render failed rc={rc} {seg}")
    json.dump(rec, open(done, "w"))
    return out, rec


# ------------------------------------------------------------------------------------------------------------ utils
def ncc(a, b, m):
    n = int(m.sum())
    if n < 100:
        return float("nan")
    x = a[m] - a[m].mean(); y = b[m] - b[m].mean()
    d = math.sqrt(float(x @ x) * float(y @ y))
    return float(x @ y / d) if d > 0 else float("nan")


def ncc_grid(a, ma, ref, vr, y0, x0, h, w):
    """masked zero-mean NCC of a (h, w) vs ref[y0+dy : y0+dy+h, x0+dx : x0+dx+w] for every dy, dx in [-SMAX, SMAX];
    same value as ncc() (masked moments, float64); NaN when < 100 valid pixels or zero variance."""
    from numpy.lib.stride_tricks import sliding_window_view as swv
    n = 2 * SMAX + 1
    Rw = swv(ref[y0 - SMAX:y0 + SMAX + h, x0 - SMAX:x0 + SMAX + w], (h, w))[:n, :n]      # (n, n, h, w)
    Mw = swv(vr[y0 - SMAX:y0 + SMAX + h, x0 - SMAX:x0 + SMAX + w], (h, w))[:n, :n]
    M = (Mw & ma[None, None]).astype(np.float64)
    A = np.where(ma, a, 0.0)
    N = M.sum((2, 3))
    sa = np.einsum("ijkl,kl->ij", M, A); saa = np.einsum("ijkl,kl->ij", M, A * A)
    Rm = Rw * M
    sb = Rm.sum((2, 3)); sbb = (Rm * Rw).sum((2, 3)); sab = np.einsum("ijkl,kl->ij", Rm, A)
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sab - sa * sb / N; va = saa - sa * sa / N; vb = sbb - sb * sb / N
        G = cov / np.sqrt(va * vb)
    G[(N < 100) | ~(va * vb > 0)] = np.nan
    return G


def best_shift(ours, ref, vo, vr, y, x):
    """ours window at (y, x) (size WIN) vs ref (which has a SMAX margin); -> (dy, dx, ncc_best, on_border)."""
    a = ours[y:y + WIN, x:x + WIN].astype(np.float64); ma = vo[y:y + WIN, x:x + WIN]
    G = ncc_grid(a, ma, ref, vr, SMAX + y, SMAX + x, WIN, WIN)
    if not np.isfinite(G).any():
        return float("nan"), float("nan"), float("nan"), True
    i, j = np.unravel_index(np.nanargmax(G), G.shape)
    border = i in (0, 2 * SMAX) or j in (0, 2 * SMAX)
    fy = fx = 0.0
    if not border:
        c, u, d = G[i, j], G[i - 1, j], G[i + 1, j]
        den = u - 2 * c + d
        fy = 0.5 * (u - d) / den if np.isfinite(den) and den < 0 else 0.0
        c, l, r = G[i, j], G[i, j - 1], G[i, j + 1]
        den = l - 2 * c + r
        fx = 0.5 * (l - r) / den if np.isfinite(den) and den < 0 else 0.0
    return float(i - SMAX + fy), float(j - SMAX + fx), float(G[i, j]), bool(border)


def bilinear_xyz(points, cv, rows, cols):
    v, u = cv.pixel_to_grid(rows, cols)
    H, W = points.shape[:2]
    v = np.clip(v, 0, H - 1.000001); u = np.clip(u, 0, W - 1.000001)
    r = np.floor(v).astype(int); c = np.floor(u).astype(int); t = (v - r)[..., None]; s = (u - c)[..., None]
    p = points.astype(np.float64); vm = valid_mask(points)
    ok = vm[r, c] & vm[r, c + 1] & vm[r + 1, c] & vm[r + 1, c + 1]
    x = (1 - t) * ((1 - s) * p[r, c] + s * p[r, c + 1]) + t * ((1 - s) * p[r + 1, c] + s * p[r + 1, c + 1])
    x[~ok] = np.nan
    return x


class Seg:
    def __init__(self, seg, aff, excl):
        self.seg = seg
        ts = seg.split("-")[0]
        self.m9 = read_tifxyz(f"{SEGS}/{seg}/mesh/{ts}-on-20250728140407-9.362um.tifxyz")
        self.m2 = read_tifxyz(f"{SEGS}/{seg}/mesh/{ts}-on-20260102150214-2.399um.tifxyz")
        self.c9 = canvas_for(self.m9.points, self.m9.scale); self.c2 = canvas_for(self.m2.points, self.m2.scale)
        a = aff["segments"][seg]
        self.M = np.array(a["M_pix9_to_pix2"])
        assert list(self.c9.shape) == a["canvas9"] and list(self.c2.shape) == a["canvas2"]
        self.T = load_T()
        vm2 = valid_mask(self.m2.points)
        self.vm2 = vm2
        near = f"/work/p139/nearE2/{seg}.npz"      # CORR-RETRACE-RULE: point-to-surface Rule S, union with v1
        if os.path.exists(near):
            z = np.load(near); sh = tuple(z["shape"])
            self.nearE = np.unpackbits(z["packed"])[:sh[0] * sh[1]].reshape(sh).astype(bool)
            assert sh == tuple(self.c9.shape)
        else:
            self.nearE = None
        self.rule_s_px = 0 if self.nearE is None else int(self.nearE.sum())

    def map9(self, rows, cols):
        M = self.M
        return M[0, 0] * rows + M[0, 1] * cols + M[0, 2], M[1, 0] * rows + M[1, 1] * cols + M[1, 2]

    def sub_coords(self, Y0, X0, h, w):
        """2.399 um canvas coords (L0) of the 4x4 sub-samples of canvas9 pixels [Y0, Y0+h) x [X0, X0+w):
        arrays (h, w, SUB*SUB)."""
        o = (np.arange(SUB) + 0.5) / SUB - 0.5
        oy, ox = np.meshgrid(o, o, indexing="ij")
        yy = (np.arange(Y0, Y0 + h)[:, None, None] + oy.ravel()[None, None, :]) + 0 * ox.ravel()[None, None, :]
        xx = (np.arange(X0, X0 + w)[None, :, None] + ox.ravel()[None, None, :]) + 0 * yy
        yy = np.broadcast_to(yy, (h, w, SUB * SUB)); xx = np.broadcast_to(xx, (h, w, SUB * SUB))
        return self.map9(yy, xx)

    def valid2(self, y2, x2):
        """2.399 um mesh-valid at L0 canvas coords (nearest grid vertex, renderer convention)."""
        H, W = self.vm2.shape
        r = np.clip(np.floor((np.round(y2) + 10.5) / 20).astype(int), 0, H - 1)
        c = np.clip(np.floor((np.round(x2) + 10.5) / 20).astype(int), 0, W - 1)
        inside = (y2 > -0.5) & (x2 > -0.5) & (y2 < self.c2.shape[0] - 0.5) & (x2 < self.c2.shape[1] - 0.5)
        return self.vm2[r, c] & inside


def area_sample(arr, off, y, x, order=1):
    """bilinear sample of arr (whose [0,0] is at coords off) at (y, x) arrays; outside -> nan."""
    c = np.stack([np.asarray(y, np.float64).ravel() - off[0], np.asarray(x, np.float64).ravel() - off[1]])
    v = ndi.map_coordinates(arr.astype(np.float32), c, order=order, mode="constant", cval=np.nan)
    return v.reshape(np.shape(y))


# ------------------------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seg"); ap.add_argument("--max-tiles", type=int, default=0)
    ap.add_argument("--keep-render", action="store_true")
    a = ap.parse_args()
    seg = a.seg; sh = short(seg)
    os.makedirs(f"{OUT}/shards", exist_ok=True); os.makedirs(f"{OUT}/registry", exist_ok=True)
    logf = open(f"{OUT}/events.jsonl", "a")

    def log(d):
        d = dict(utc=utc(), **d); logf.write(json.dumps(d) + "\n"); logf.flush(); print(json.dumps(d), flush=True)

    excl = json.load(open(os.environ.get("P139_EXCL", "/work/p139/exclusion_v2.json")))
    if sh in excl["E"]:
        raise SystemExit(f"{seg} is excluded ({sh} in E)")
    aff = json.load(open("/work/p139/affines.json"))
    S = Seg(seg, aff, excl)
    t0 = time.time()
    # ---- inputs: ink map, human labels, SV reader
    objs, _ = listing(f"PHerc0139/segments/{seg}/ink-detection/", "/")
    ik = [o for o, _ in objs if "-2.399um-" in o and "20260417190342" in o and o.endswith(".tif")]
    assert len(ik) == 1
    ink_path, ink_sha = get(ik[0])
    INK = tifffile.imread(ink_path)
    assert INK.dtype == np.uint8 and INK.shape == tuple(S.c2.shape), (INK.shape, S.c2.shape)
    L = f"PHerc0139/segments/{seg}/ink-labels/2.399um-volume-20260102150214/20260918"
    lobjs, _ = listing(L + "/")
    HUM = None
    if lobjs:
        for k, _ in lobjs:
            if "/0/" in k or k.endswith(".zarr/zarr.json"):
                get(k)
        HL = np.asarray(zarr.open(f"{S3}/{L}/inklabels.zarr", mode="r")["0"][:]) > 0
        HS = np.asarray(zarr.open(f"{S3}/{L}/supervision.zarr", mode="r")["0"][:]) > 0
        assert HL.shape == INK.shape
        HUM = (HL & HS).astype(np.uint8) + 2 * HS.astype(np.uint8)   # 0 unsup, 2 blank, 3 ink
        del HL, HS
    sv = SV24(seg, level=1)
    assert sv.shape[0] == 109 and abs(sv.shape[1] - S.c2.shape[0] / 2) <= 1 and abs(sv.shape[2] - S.c2.shape[1] / 2) <= 1
    sv0 = SV24(seg, level=0, workers=2)
    assert sv0.shape[1:] == tuple(S.c2.shape), (sv0.shape, S.c2.shape)
    # ---- render
    rpath, rrec = render(seg, log)
    R = zarr.open(rpath, mode="r")
    R = R["0"] if hasattr(R, "keys") and "0" in R.keys() else R
    x0c, y0c, wc, hc = auto_crop_rect(S.m9.points, S.m9.scale)
    assert tuple(R.shape) == (31, hc, wc), (R.shape, hc, wc)
    log(dict(event="inputs", segment=seg, inkmap_key=ik[0], inkmap_sha256=ink_sha, human=HUM is not None,
             render=rpath, render_shape=list(R.shape), render_origin_yx=[y0c, x0c], canvas9=list(S.c9.shape),
             sv24_l1_shape=list(sv.shape), rule_s_px=S.rule_s_px))
    # ---- tiles
    Hc, Wc = S.c9.shape
    ty = range((y0c + T - 1) // T * T, y0c + hc - T + 1, T)
    tx = list(range((x0c + T - 1) // T * T, x0c + wc - T + 1, T))
    regf = open(f"{OUT}/registry/{sh}.jsonl", "w")
    buf = dict(images=[], label=[], inkmap=[], human=[]); rows_buf = []; shard_i = 0; n_kept = 0; n_cand = 0
    stats = dict(tiles_grid=0, fail_render_valid=0, fail_rule_s=0, fail_valid24=0, candidates=0, pass_ncc=0,
                 pass_win=0, kept=0)

    def flush():
        nonlocal shard_i
        if not rows_buf:
            return
        name = f"{sh}_s{shard_i:02d}.npz"
        p = f"{OUT}/shards/{name}"
        np.savez_compressed(p, images=np.stack(buf["images"]), label=np.stack(buf["label"]),
                            inkmap=np.stack(buf["inkmap"]), human=np.stack(buf["human"]),
                            tile_id=np.array([r["tile_id"] for r in rows_buf]))
        sz = os.path.getsize(p); assert sz < 90 * 1024 * 1024, sz
        h = sha_file(p)
        for i, r in enumerate(rows_buf):
            r["shard"] = name; r["shard_index"] = i; r["shard_sha256"] = h
            regf.write(json.dumps(r) + "\n")
        regf.flush()
        log(dict(event="shard", segment=seg, shard=name, n=len(rows_buf), bytes=sz, sha256=h))
        for k in buf:
            buf[k].clear()
        rows_buf.clear(); shard_i += 1

    prev_ref = None
    for Y in ty:
        band = np.asarray(R[:, Y - y0c:Y - y0c + T, :])            # (31, T, wc)
        bvalid = (band > 0).any(0)
        cands = []
        for X in tx:
            stats["tiles_grid"] += 1
            v = bvalid[:, X - x0c:X - x0c + T]
            if v.mean() < 0.9:
                stats["fail_render_valid"] += 1; continue
            if S.nearE is not None and S.nearE[Y:Y + T, X:X + T].any():
                stats["fail_rule_s"] += 1; continue
            yy, xx = np.meshgrid(np.arange(Y, Y + T), np.arange(X, X + T), indexing="ij")
            y2, x2 = S.map9(yy, xx)
            if S.valid2(y2, x2).mean() < 0.9:
                stats["fail_valid24"] += 1; continue
            cands.append(X)
        if not cands:
            continue
        # SV level-1 band covering all candidate tiles of this row (+ SMAX margin)
        Ym, Xa, Xb = Y - SMAX, min(cands) - SMAX, max(cands) + T + SMAX
        y2a, x2a = S.sub_coords(Ym, Xa, T + 2 * SMAX, Xb - Xa)
        y1 = (y2a + 0.5) / 2 - 0.5; x1 = (x2a + 0.5) / 2 - 0.5
        ly0, ly1 = int(np.floor(y1.min())) - 1, int(np.ceil(y1.max())) + 2
        lx0, lx1 = int(np.floor(x1.min())) - 1, int(np.ceil(x1.max())) + 2
        blk = sv.read(L1_Z0, L1_Z1, ly0, ly1, lx0, lx1)
        bval = (blk > 0).all(0).astype(np.float32)
        bmean = blk.astype(np.float32).mean(0)
        del y2a, x2a
        for X in cands:
            stats["candidates"] += 1
            n_cand += 1
            # reference CT on tile + margin
            y2, x2 = S.sub_coords(Ym, X - SMAX, T + 2 * SMAX, T + 2 * SMAX)
            y1 = (y2 + 0.5) / 2 - 0.5; x1 = (x2 + 0.5) / 2 - 0.5
            ref = area_sample(bmean, (ly0, lx0), y1, x1).mean(-1)
            rv = area_sample(bval, (ly0, lx0), y1, x1)
            vref = np.isfinite(ref) & (np.nan_to_num(rv, nan=0).min(-1) >= 0.999)
            ref = np.where(vref, ref, np.nan)
            ours = band[ZS, :, X - x0c:X - x0c + T].astype(np.float64)
            vo = ours > 0
            vr = vref
            m0 = vo & vr[SMAX:SMAX + T, SMAX:SMAX + T]
            n0 = ncc(ours, np.nan_to_num(ref[SMAX:SMAX + T, SMAX:SMAX + T]), m0)
            wins = []
            for wy in WOFF:
                for wx in WOFF:
                    dy, dx, nb, border = best_shift(ours, np.nan_to_num(ref), vo, vr, wy, wx)
                    ok = (not border) and np.isfinite(dy) and math.hypot(dy, dx) <= ALIGN_PX
                    wins.append(dict(y=wy, x=wx, dy=round(dy, 3) if np.isfinite(dy) else None,
                                     dx=round(dx, 3) if np.isfinite(dx) else None,
                                     ncc=round(nb, 4) if np.isfinite(nb) else None, border=border, aligned=bool(ok)))
            n_al = sum(w["aligned"] for w in wins)
            # reported only (never deciding): tile-level integer shift maximising NCC within +-SMAX
            tg = ncc_grid(ours, vo, np.nan_to_num(ref), vr, SMAX, SMAX, T, T)
            ti, tj = np.unravel_index(np.nanargmax(tg), tg.shape) if np.isfinite(tg).any() else (SMAX, SMAX)
            # reported negative controls on every 10th candidate (never deciding):
            #  mismatch = ours vs the previous candidate's reference; plain = reference mapped by plain voxel-ratio scaling
            ctl = None
            if n_cand % 10 == 1:
                ctl = {}
                if prev_ref is not None:
                    pr_, pv_ = prev_ref
                    ctl["mismatch_ncc0"] = round(ncc(ours, np.nan_to_num(pr_[SMAX:SMAX + T, SMAX:SMAX + T]),
                                                     vo & pv_[SMAX:SMAX + T, SMAX:SMAX + T]), 4)
                    ctl["mismatch_n_aligned"] = int(sum((not b_) and np.isfinite(d1) and math.hypot(d1, d2) <= ALIGN_PX
                                                        for d1, d2, _, b_ in (best_shift(ours, np.nan_to_num(pr_), vo, pv_, wy, wx)
                                                                              for wy in WOFF for wx in WOFF)))
                o = (np.arange(SUB) + 0.5) / SUB - 0.5
                py_ = (np.arange(Y - SMAX, Y + T + SMAX)[:, None, None, None] + o[None, None, :, None] + 0.5) * F_PLAIN - 0.5
                px_ = (np.arange(X - SMAX, X + T + SMAX)[None, :, None, None] + o[None, None, None, :] + 0.5) * F_PLAIN - 0.5
                py_, px_ = np.broadcast_arrays(py_, px_)
                py_ = py_.reshape(T + 2 * SMAX, T + 2 * SMAX, -1); px_ = px_.reshape(T + 2 * SMAX, T + 2 * SMAX, -1)
                q1y = (py_ + 0.5) / 2 - 0.5; q1x = (px_ + 0.5) / 2 - 0.5
                qa, qb = int(np.floor(q1y.min())) - 1, int(np.ceil(q1y.max())) + 2
                qc_, qd = int(np.floor(q1x.min())) - 1, int(np.ceil(q1x.max())) + 2
                pb = sv.read(L1_Z0, L1_Z1, qa, qb, qc_, qd)
                pref = area_sample(pb.astype(np.float32).mean(0), (qa, qc_), q1y, q1x).mean(-1)
                prv = area_sample((pb > 0).all(0).astype(np.float32), (qa, qc_), q1y, q1x)
                pvr = np.isfinite(pref) & (np.nan_to_num(prv, nan=0).min(-1) >= 0.999)
                ctl["plain_ncc0"] = round(ncc(ours, np.nan_to_num(pref[SMAX:SMAX + T, SMAX:SMAX + T]),
                                             vo & pvr[SMAX:SMAX + T, SMAX:SMAX + T]), 4)
                ctl["plain_n_aligned"] = int(sum((not b_) and np.isfinite(d1) and math.hypot(d1, d2) <= ALIGN_PX
                                                 for d1, d2, _, b_ in (best_shift(ours, np.nan_to_num(pref), vo, pvr, wy, wx)
                                                                       for wy in WOFF for wx in WOFF)))
            prev_ref = (ref, vr)
            p_ncc = bool(np.isfinite(n0) and n0 >= NCC_MIN); p_win = n_al >= NWIN_MIN
            stats["pass_ncc"] += p_ncc; stats["pass_win"] += p_win
            keep = p_ncc and p_win
            # labels (ink map, area-averaged) on the tile
            ty2 = y2[SMAX:SMAX + T, SMAX:SMAX + T]; tx2 = x2[SMAX:SMAX + T, SMAX:SMAX + T]
            ra, rb = int(np.floor(ty2.min())) - 1, int(np.ceil(ty2.max())) + 2
            ca, cb = int(np.floor(tx2.min())) - 1, int(np.ceil(tx2.max())) + 2
            ra_, ca_ = max(ra, 0), max(ca, 0)
            sub = INK[ra_:rb, ca_:cb]
            imap = area_sample(sub, (ra_, ca_), ty2, tx2).mean(-1)
            v24 = S.valid2(ty2, tx2).all(-1) & vr[SMAX:SMAX + T, SMAX:SMAX + T] & np.isfinite(imap)
            lv = v24 & vo
            lab = np.full((T, T), 255, np.uint8)
            lab[lv & (imap >= LAB_INK)] = 1; lab[lv & (imap <= LAB_BLANK)] = 0
            hum = np.full((T, T), 255, np.uint8)
            if HUM is not None:
                hs = HUM[ra_:rb, ca_:cb]
                sup = area_sample((hs >= 2).astype(np.float32), (ra_, ca_), ty2, tx2, order=0)
                hin = area_sample((hs == 3).astype(np.float32), (ra_, ca_), ty2, tx2, order=0)
                full = np.nan_to_num(sup, nan=0).min(-1) >= 1
                hm = lv & full
                hum[hm] = (np.nan_to_num(hin, nan=0).mean(-1)[hm] >= 0.5).astype(np.uint8)
            # 3-D coordinates (9.362 um volume voxels, x y z) of centre and corners; 3-D map error on a 5 x 5 grid
            pr = np.array([Y + (T - 1) / 2, Y, Y, Y + T - 1, Y + T - 1], float)
            pc = np.array([X + (T - 1) / 2, X, X + T - 1, X, X + T - 1], float)
            xyz = bilinear_xyz(S.m9.points, S.c9, pr, pc)
            g = np.linspace(0, T - 1, 5)
            gr, gc = np.meshgrid(Y + g, X + g, indexing="ij"); gr = gr.ravel(); gc = gc.ravel()
            X9 = bilinear_xyz(S.m9.points, S.c9, gr, gc)
            r2, c2 = S.map9(gr, gc)
            X2 = bilinear_xyz(S.m2.points, S.c2, r2, c2) @ S.T[:, :3].T + S.T[:, 3]
            err = np.linalg.norm(X9 - X2, axis=1)
            tid = f"{sh}_y{Y}_x{X}"
            row = dict(tile_id=tid, segment=seg, canvas9_y0=int(Y), canvas9_x0=int(X), size=T,
                       render_y0=int(Y - y0c), render_x0=int(X - x0c),
                       xyz_centre=[round(float(v), 2) for v in xyz[0]],
                       xyz_corners=[[round(float(v), 2) for v in c] for c in xyz[1:]],
                       canvas24_bbox=[int(np.floor(ty2.min())), int(np.floor(tx2.min())), int(np.ceil(ty2.max())), int(np.ceil(tx2.max()))],
                       map3d_err_vox=dict(median=round(float(np.nanmedian(err)), 3), max=round(float(np.nanmax(err)), 3)),
                       ncc0=round(n0, 4) if np.isfinite(n0) else None, n_valid_ncc=int(m0.sum()),
                       windows=wins, n_aligned=int(n_al),
                       reported_controls=ctl,
                       reported_tile_best_int_shift=[int(ti - SMAX), int(tj - SMAX)],
                       reported_tile_ncc_at_best_int_shift=round(float(tg[ti, tj]), 4) if np.isfinite(tg[ti, tj]) else None, pass_ncc=p_ncc, pass_windows=bool(p_win), kept=bool(keep),
                       render_valid_frac=round(float(vo.mean()), 4), valid24_frac=round(float(v24.mean()), 4),
                       label_source="organizer ink map 20260417190342 (2.399 um canvas), affine-mapped, area average; "
                                    "ink >= 150, blank <= 100",
                       inkmap_sha256=ink_sha,
                       ink_px=int((lab == 1).sum()), blank_px=int((lab == 0).sum()), ignored_px=int((lab == 255).sum()),
                       human_ink_px=int((hum == 1).sum()), human_blank_px=int((hum == 0).sum()),
                       tags=[f"{sh}_y{wy}_x{wx}" for (wy, wx) in TAG_WINDOWS.get(sh, [])
                             if Y < wy + TAG_PX and Y + T > wy and X < wx + TAG_PX and X + T > wx])
            if keep:
                img = band[Z0:Z1, :, X - x0c:X - x0c + T].copy()
                row["image_sha256"] = sha(img.tobytes()); row["label_sha256"] = sha(lab.tobytes())
                row["inkmap_u8_sha256"] = sha(np.clip(np.round(np.nan_to_num(imap)), 0, 255).astype(np.uint8).tobytes())
                buf["images"].append(img); buf["label"].append(lab)
                buf["inkmap"].append(np.clip(np.round(np.nan_to_num(imap)), 0, 255).astype(np.uint8))
                buf["human"].append(hum)
                rows_buf.append(row); n_kept += 1; stats["kept"] += 1
                if len(rows_buf) >= SHARD_TILES:
                    flush()
            else:
                regf.write(json.dumps(row) + "\n")
            if a.max_tiles and n_cand >= a.max_tiles:
                break
        log(dict(event="row", segment=seg, Y=int(Y), **stats, seconds=round(time.time() - t0, 1),
                 sv_bytes=sv.bytes, sv_requests=sv.requests))
        if a.max_tiles and n_cand >= a.max_tiles:
            break
    flush()
    regf.close()
    summ = dict(event="segment_done", segment=seg, **stats, seconds=round(time.time() - t0, 1), shards=shard_i,
                render=rrec, sv_bytes=sv.bytes, sv_requests=sv.requests, max_tiles=a.max_tiles)
    json.dump(summ, open(f"{OUT}/registry/{sh}.summary.json", "w"), indent=1)
    log(summ)
    if not a.keep_render and not a.max_tiles:
        subprocess.run(["rm", "-rf", rpath])


if __name__ == "__main__":
    main()
