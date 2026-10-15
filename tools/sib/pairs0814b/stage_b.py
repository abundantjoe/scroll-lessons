# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task pairs0814 stage B (DECL-D2 pairs, PHerc0814): render, gate, label and store 9 um / 2.4 um training pairs.
Numbers only: no image is written for viewing and none is opened.

Per organizer segment (stage A outputs: val9, cov9, ref9 on the 9.362 um canvas and the fitted canvas affine):
1. Patches: 384 x 384 px on the 9.362 um canvas, stride 384 from the canvas origin; a patch is a CANDIDATE if
   >= 90 % of its pixels are valid on both canvases (val9 and full 2.4 um footprint coverage).
2. Render: official vc_render_tifxyz of the organizer 9.362 um mesh on volume 20250804134230, -n 31, slice step 1,
   --flip-normals, voxel size from the volume's metadata.json (9.362 um), in 1536 px blocks (4 x 4 patches) with an
   8 px margin (crop intersected with the canvas; a manual crop inside the canvas is the output origin).
3. 2.4 um CT: the organizer 2.399 um surface volume of the same segment, level 0, slices 53-55 (surface slice 54 of
   109 = offset 0; 53/55 = +-1 slice) read by HTTP range requests of the uncompressed C-order chunks, then
   area-averaged onto the 9.362 um canvas with the stage-A affine (exact integral-image average over the pixel
   footprint, which the fitted affine keeps axis-aligned). A 2.4 um value of 0 is invalid (outside the surface).
4. Gate (DECL-D2): (i) NCC over the patch at zero shift between our render slice 15 (surface) and the 2.4 um surface
   slice 54 on the 9 um canvas, both-valid pixels only, must be >= 0.8; (ii) the patch is split into 3 x 3 windows of
   128 px; per window the NCC is evaluated at integer shifts within +-3 px, the best shift refined by a 1-D parabola
   per axis; a window ALIGNS if its refined shift has Euclidean norm <= 1.0 px and it has >= 50 % both-valid pixels;
   >= 7 of 9 windows must align. PASS = (i) and (ii). Control (reported, not gating): patch NCC at +-5 px shifts.
5. Labels (DECL-D2): ref9 (official 2.399 um ink map, area-averaged onto the 9 um canvas) >= 150 -> ink (1),
   <= 100 -> blank (0), otherwise or invalid -> ignored (255).
6. Output: every candidate gets a registry row (logs/sib/pairs0814/registry/<seg>.jsonl) with gate numbers, label
   counts and 3-D coordinates; every PASS patch is staged per block (/work/sib/blockpairs, written before the block's
   done marker) and packed by stage C into npz shards (images uint8 (N, 21, 384, 384) = render
   slices 5..25 of the -n 31 stack, the stored window of the D3 pools (the base model reads 17 slices 7..23 with
   +-2 jitter); the full stack is reproducible from the registry crop and the logged command), ref9 uint8, labels uint8, valid bool, xyz float32 (N, 17, 17, 3) = 9.362 um volume voxels of the
   mesh at every 24th patch pixel), each shard < 90 MB.
Resumable per block (done markers). Usage: stage_b.py SEG_ID|all [--max-blocks N]
"""
import concurrent.futures as cf
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time

import numpy as np
import requests
import zarr

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
from hercules.geometry.tifxyz import read_tifxyz, sample_grid  # noqa: E402

SC = "PHerc0814"
VOL9 = "s3://vesuvius-challenge-open-data/PHerc0814/volumes/20250804134230-9.362um-1.2m-113keV-masked.zarr/"
VOXEL_UM = 9.362  # checked against the volume metadata.json in main()
HTTP = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SV24 = "surface-volumes/2.399um-0.22m-78keV-volume-20260309142202.zarr/0"
WORK = "/work/sib"
SEGW = f"{WORK}/seg"
LOGD = f"{REPO}/logs/sib/pairs0814"
REGD = f"{LOGD}/registry"
SHARDD = f"{WORK}/shards"
P, BLK, MARGIN = 384, 1536, 8
NS, SURF = 31, 15
Z24 = (53, 56)  # 2.4 um SV slices 53, 54, 55 (surface = 54 of 109)
NCC_MIN, ALIGN_PX, ALIGN_MIN, SEARCH, WIN_VALID = 0.8, 1.0, 7, 3, 0.5
INK, BLANK = 150, 100
Z_STORE = (5, 26)  # stored render slices 5..25
MAX_PER_SHARD = 20  # 20 x (21 x 384 x 384 + 3 x 384 x 384 + xyz) < 75 MB even uncompressed
PROV = "Project HERCULES | owner the owner | [id removed]"

_sess = requests.Session()
_sess.mount("https://", requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=3))


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def log_run(cmd, start, end, rc, out_sha):
    with open(f"{LOGD}/runs.jsonl", "a") as f:
        f.write(json.dumps({"utc_start": start, "utc_end": end, "command": cmd, "exit_code": rc,
                            "output_sha256": out_sha}) + "\n")


def tree_sha(root):
    rows = []
    for d, _, fs in os.walk(root):
        for fn in fs:
            p = os.path.join(d, fn)
            rows.append(f"{sha256(p)}  ./{os.path.relpath(p, root)}\n")
    return hashlib.sha256("".join(sorted(rows, key=lambda r: r.split('  ', 1)[1])).encode()).hexdigest()


# ------------------------------------------------------------------ render
def render(seg_dir, x, y, w, h, out):
    cmd = ["vc_render_tifxyz", "-v", VOL9, "--remote-url", VOL9, "--segmentation", f"{seg_dir}/mesh9",
           "--scale", "1", "--group-idx", "0", "--num-slices", str(NS), "--slice-step", "1",
           "--voxel-size", f"{VOXEL_UM:g}", "--voxel-unit", "micrometer", "--flip-normals",
           "--crop-x", str(x), "--crop-y", str(y), "--crop-width", str(w), "--crop-height", str(h),
           "--cache-gb", "2", "--zarr-output", out]
    for attempt in range(2):
        shutil.rmtree(out, ignore_errors=True)
        start = utc()
        with open(f"{out}.log", "w") as lf:
            pr = subprocess.run(["/work/bin/vc", *cmd], stdout=lf, stderr=subprocess.STDOUT,
                                env=dict(os.environ, VC_CPUS="3", OMP_NUM_THREADS="3"))
        end = utc()
        ok = pr.returncode == 0 and os.path.exists(f"{out}/0")
        log_run(["VC_CPUS=3", "/work/bin/vc", *cmd], start, end, pr.returncode, tree_sha(out) if ok else "missing")
        if ok:
            a = np.asarray(zarr.open(f"{out}/0", mode="r")[:])
            assert a.shape == (NS, h, w) and a.dtype == np.uint8, (a.shape, a.dtype)
            return a
    return None


# ------------------------------------------------------------------ 2.4 um surface slabs
def fetch_region24(seg, y0, y1, x0, x1, shape24):
    """(3, y1-y0, x1-x0) uint8 of SV slices 53..55 over the 2.4 um canvas box (clipped; outside = 0)."""
    base = f"{HTTP}/{SC}/segments/{seg}/{SV24}"
    H, W = shape24
    out = np.zeros((Z24[1] - Z24[0], y1 - y0, x1 - x0), np.uint8)
    keys = [(cy, cx) for cy in range(max(0, y0) // 128, (min(H, y1) - 1) // 128 + 1)
            for cx in range(max(0, x0) // 128, (min(W, x1) - 1) // 128 + 1)]

    def get(k):
        cy, cx = k
        for i in range(5):
            try:
                r = _sess.get(f"{base}/0/{cy}/{cx}", timeout=60,
                              headers={"Range": f"bytes={Z24[0] * 16384}-{Z24[1] * 16384 - 1}"})
                if r.status_code == 404:
                    return k, None
                if r.status_code == 206:
                    return k, np.frombuffer(r.content, np.uint8).reshape(Z24[1] - Z24[0], 128, 128)
            except requests.RequestException:
                pass
            time.sleep(2 ** (i + 1))
        raise RuntimeError(f"chunk fetch failed {base}/0/{cy}/{cx}")

    with cf.ThreadPoolExecutor(32) as ex:
        for (cy, cx), a in ex.map(get, keys):
            if a is None:
                continue
            gy, gx = cy * 128, cx * 128
            ya, yb = max(y0, gy), min(y1, gy + 128)
            xa, xb = max(x0, gx), min(x1, gx + 128)
            if ya < yb and xa < xb:
                out[:, ya - y0:yb - y0, xa - x0:xb - x0] = a[:, ya - gy:yb - gy, xa - gx:xb - gx]
    return out, len(keys)


def area_avg_block(G, oy, ox, A, bx, by, bw, bh):
    """Average of G (2.4 um canvas box with origin (oy, ox)) over each 9 um pixel footprint of the block."""
    M, t = A[:, :2], A[:, 2]
    Mi = np.linalg.inv(M)
    ti = -Mi @ t
    hx = 0.5 * (abs(Mi[0, 0]) + abs(Mi[0, 1]))
    hy = 0.5 * (abs(Mi[1, 0]) + abs(Mi[1, 1]))
    X, Y = np.meshgrid(np.arange(bx, bx + bw, dtype=np.float64), np.arange(by, by + bh, dtype=np.float64))
    cx = Mi[0, 0] * X + Mi[0, 1] * Y + ti[0] - ox
    cy = Mi[1, 0] * X + Mi[1, 1] * Y + ti[1] - oy
    h2, w2 = G.shape
    I = np.zeros((h2 + 1, w2 + 1))
    I[1:, 1:] = np.asarray(G, np.float64).cumsum(0).cumsum(1)

    def Iv(xx, yy):
        u = np.clip(xx + 0.5, 0, w2); v = np.clip(yy + 0.5, 0, h2)
        u0 = np.floor(u).astype(np.int64); v0 = np.floor(v).astype(np.int64)
        u1 = np.minimum(u0 + 1, w2); v1 = np.minimum(v0 + 1, h2)
        fu = u - u0; fv = v - v0
        return (1 - fu) * (1 - fv) * I[v0, u0] + fu * (1 - fv) * I[v0, u1] + (1 - fu) * fv * I[v1, u0] + fu * fv * I[v1, u1]
    s = Iv(cx + hx, cy + hy) - Iv(cx - hx, cy + hy) - Iv(cx + hx, cy - hy) + Iv(cx - hx, cy - hy)
    return s / (4 * hx * hy)


# ------------------------------------------------------------------ gate
def ncc(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    n = int(ok.sum())
    if n < 100:
        return math.nan, n
    x = a[ok] - a[ok].mean(); y = b[ok] - b[ok].mean()
    den = math.sqrt(float((x * x).sum()) * float((y * y).sum()))
    return (float((x * y).sum()) / den if den > 0 else math.nan), n


def window_shift(ours, ref, y, x, n):
    """ours/ref: block arrays (NaN invalid). NCC of ours[y:y+n, x:x+n] vs ref shifted by (dy, dx) in +-SEARCH."""
    a = ours[y:y + n, x:x + n]
    S = SEARCH
    g = np.full((2 * S + 1, 2 * S + 1), np.nan)
    nv = 0
    for dy in range(-S, S + 1):
        for dx in range(-S, S + 1):
            yy, xx = y + dy, x + dx
            if yy < 0 or xx < 0 or yy + n > ref.shape[0] or xx + n > ref.shape[1]:
                continue
            v, k = ncc(a, ref[yy:yy + n, xx:xx + n])
            g[dy + S, dx + S] = v
            if dy == 0 and dx == 0:
                nv = k
    if not np.isfinite(g).any():
        return dict(dy=None, dx=None, ncc=None, n_valid=nv, aligned=False)
    iy, ix = np.unravel_index(np.nanargmax(g), g.shape)

    def refine(c, m, p):
        den = c - 2 * m + p if all(np.isfinite([c, m, p])) else 0.0
        return 0.0 if den >= 0 else 0.5 * (c - p) / den
    sy = iy - S + (refine(g[iy - 1, ix], g[iy, ix], g[iy + 1, ix]) if 0 < iy < 2 * S else 0.0)
    sx = ix - S + (refine(g[iy, ix - 1], g[iy, ix], g[iy, ix + 1]) if 0 < ix < 2 * S else 0.0)
    at_edge = iy in (0, 2 * S) or ix in (0, 2 * S)
    aligned = bool((not at_edge) and math.hypot(sy, sx) <= ALIGN_PX and nv >= WIN_VALID * n * n)
    return dict(dy=float(sy), dx=float(sx), ncc=float(g[iy, ix]), ncc0=float(g[S, S]), n_valid=nv,
                at_search_edge=bool(at_edge), aligned=aligned)


# ------------------------------------------------------------------ segment
def run_segment(seg, max_blocks=None):
    sid = seg.split("-", 1)[0]
    d = f"{SEGW}/{sid}"
    sa = json.load(open(f"{LOGD}/stage_a/{sid}.json"))
    A = np.array(sa["affine_c2_to_c9"], float)
    H9, W9 = sa["canvas9_hw"]
    H2, W2 = sa["canvas24_hw"]
    val9 = np.load(f"{d}/val9.npy")
    cov9 = np.load(f"{d}/cov9.npy")
    ref9 = np.load(f"{d}/ref9.npy")
    both = val9 & (cov9 == 255)
    mesh = read_tifxyz(f"{d}/mesh9")
    s9 = 1.0 / np.float32(mesh.scale[0])
    os.makedirs(REGD, exist_ok=True)
    os.makedirs(f"{WORK}/blocks/{sid}", exist_ok=True)
    regf = f"{REGD}/{sid}.jsonl"
    bdir = f"{WORK}/blockpairs/{sid}"
    os.makedirs(bdir, exist_ok=True)
    cand = [(py, px) for py in range(0, H9 - P + 1, P) for px in range(0, W9 - P + 1, P)
            if both[py:py + P, px:px + P].mean() >= 0.9]
    blocks = sorted({(py // BLK * BLK, px // BLK * BLK) for py, px in cand})
    print(f"{sid}: canvas {H9}x{W9}, candidates {len(cand)}, blocks {len(blocks)}", flush=True)
    todo = [b for b in blocks if not os.path.exists(f"{WORK}/blocks/{sid}/{b[0]}_{b[1]}.done.json")]
    if max_blocks is not None:
        todo = todo[:max_blocks]

    def geom(b):
        by, bx = b
        ry, rx = max(0, by - MARGIN), max(0, bx - MARGIN)
        return ry, rx, min(H9, by + BLK + MARGIN) - ry, min(W9, bx + BLK + MARGIN) - rx

    # renders run one at a time in a worker thread, one block ahead of the fetch + gate of the current block
    rex = cf.ThreadPoolExecutor(1)
    futs = {}

    def submit(i):
        if i < len(todo) and i not in futs:
            ry, rx, rh, rw = geom(todo[i])
            futs[i] = rex.submit(render, d, rx, ry, rw, rh, f"{WORK}/blocks/{sid}/r_{todo[i][0]}_{todo[i][1]}.zarr")
    submit(0)
    for bi, (by, bx) in enumerate(todo):
        done = f"{WORK}/blocks/{sid}/{by}_{bx}.done.json"
        t0 = time.time()
        ry, rx, rh, rw = geom((by, bx))
        out = f"{WORK}/blocks/{sid}/r_{by}_{bx}.zarr"
        R = futs.pop(bi).result()
        submit(bi + 1)
        rows = []
        items = []
        if R is None:
            for py, px in cand:
                if (py // BLK * BLK, px // BLK * BLK) == (by, bx):
                    rows.append(dict(segment=seg, patch_id=f"{sid}_{py}_{px}", y0=py, x0=px, size=P,
                                     status="RENDER_FAILED"))
        else:
            t1 = time.time()  # render wait (the render itself overlaps the previous block's gate)
            # 2.4 um box covering the block (+margin) footprint
            Mi = np.linalg.inv(A[:, :2]); ti = -Mi @ A[:, 2]
            corners = np.array([[rx - 1, ry - 1], [rx + rw + 1, ry - 1], [rx - 1, ry + rh + 1], [rx + rw + 1, ry + rh + 1]], float)
            c2 = corners @ Mi.T + ti
            oy, ox = int(np.floor(c2[:, 1].min())) - 4, int(np.floor(c2[:, 0].min())) - 4
            ey, ex = int(np.ceil(c2[:, 1].max())) + 5, int(np.ceil(c2[:, 0].max())) + 5
            G, nchunks = fetch_region24(seg, oy, ey, ox, ex, (H2, W2))
            t2 = time.time()
            sl = [area_avg_block(G[k], oy, ox, A, rx, ry, rw, rh) for k in range(G.shape[0])]
            cov = area_avg_block((G[1] > 0).astype(np.float64), oy, ox, A, rx, ry, rw, rh)
            ref24 = np.where(cov >= 0.999, sl[1], np.nan)
            ref24m = np.where(cov >= 0.999, (sl[0] + sl[1] + sl[2]) / 3.0, np.nan)
            ours = np.where(R[SURF] > 0, R[SURF].astype(np.float64), np.nan)
            for py, px in cand:
                if (py // BLK * BLK, px // BLK * BLK) != (by, bx):
                    continue
                ly, lx = py - ry, px - rx
                o = ours[ly:ly + P, lx:lx + P]
                n0, nv = ncc(o, ref24[ly:ly + P, lx:lx + P])
                n0m, _ = ncc(o, ref24m[ly:ly + P, lx:lx + P])
                ctrl = {}
                for cy_, cx_ in ((5, 0), (-5, 0), (0, 5), (0, -5)):
                    yy, xx = ly + cy_, lx + cx_
                    if 0 <= yy and 0 <= xx and yy + P <= ref24.shape[0] and xx + P <= ref24.shape[1]:
                        ctrl[f"{cy_},{cx_}"] = ncc(o, ref24[yy:yy + P, xx:xx + P])[0]
                wins = [window_shift(ours, ref24, ly + wy * 128, lx + wx * 128, 128) for wy in range(3) for wx in range(3)]
                n_al = sum(w["aligned"] for w in wins)
                passed = bool(np.isfinite(n0) and n0 >= NCC_MIN and n_al >= ALIGN_MIN)
                rp = ref9[py:py + P, px:px + P]
                vp = both[py:py + P, px:px + P] & (R[SURF, ly:ly + P, lx:lx + P] > 0)
                lab = np.full((P, P), 255, np.uint8)
                lab[vp & (rp >= INK)] = 1
                lab[vp & (rp <= BLANK)] = 0
                gy = (np.arange(0, P + 1, 24) + py + 0.5) / s9 * 1.0  # grid coords of pixel centres (P + 0.5) s
                gx = (np.arange(0, P + 1, 24) + px + 0.5) / s9 * 1.0
                xyz = sample_grid(mesh.points, gy[:, None], gx[None, :]).astype(np.float32)
                cxyz = sample_grid(mesh.points, np.array([(py + P / 2) / s9]), np.array([(px + P / 2) / s9]))[0]
                good = xyz[..., 0] != -1
                row = dict(segment=seg, patch_id=f"{sid}_{py}_{px}", y0=py, x0=px, size=P, status="GATED",
                           ncc0=n0, n_valid=nv, ncc0_slab53_55=n0m, control_ncc_shift5=ctrl, windows=wins, n_aligned=int(n_al), passed=passed,
                           valid_frac=float(vp.mean()), n_ink=int((lab == 1).sum()), n_blank=int((lab == 0).sum()),
                           n_ignore=int((lab == 255).sum()),
                           centre_xyz_vox9=[float(v) for v in cxyz],
                           bbox_xyz_vox9=[[float(v) for v in xyz[good].min(0)], [float(v) for v in xyz[good].max(0)]] if good.any() else None,
                           footprint24_xywh=[float(v) for v in (np.array([px - 0.5, py - 0.5]) @ Mi.T + ti)] +
                                            [float(P * abs(Mi[0, 0])), float(P * abs(Mi[1, 1]))])
                if passed:
                    items.append(dict(img=np.ascontiguousarray(R[Z_STORE[0]:Z_STORE[1], ly:ly + P, lx:lx + P]), ref9=rp.copy(),
                                      lab=lab, valid=vp, xyz=xyz, pid=row["patch_id"]))
                    row["staged"] = f"blockpairs/{sid}/{by}_{bx}.npz"
                rows.append(row)
            t3 = time.time()
            timing = dict(render_wait_s=round(t1 - t0, 1), fetch24_s=round(t2 - t1, 1), gate_s=round(t3 - t2, 1),
                          chunks24=nchunks)
        if items:  # staging file per block, written before the block's done marker (resume-safe)
            bp = f"{bdir}/{by}_{bx}.npz"
            np.savez_compressed(bp + ".tmp.npz", images=np.stack([b["img"] for b in items]),
                                ref9=np.stack([b["ref9"] for b in items]), labels=np.stack([b["lab"] for b in items]),
                                valid=np.stack([b["valid"] for b in items]), xyz=np.stack([b["xyz"] for b in items]),
                                patch_id=np.array([b["pid"] for b in items]))
            os.replace(bp + ".tmp.npz", bp)
            for r in rows:
                if r.get("staged"):
                    r["staged_sha256"] = sha256(bp)
        with open(regf, "a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        shutil.rmtree(out, ignore_errors=True)
        json.dump(dict(utc=utc(), n_rows=len(rows), n_pass=sum(bool(r.get("passed")) for r in rows),
                       timing=timing if R is not None else None), open(done, "w"))
        print(f"{sid} block {by},{bx}: {len(rows)} patches, pass {sum(bool(r.get('passed')) for r in rows)}, "
              f"{timing if R is not None else 'RENDER_FAILED'}", flush=True)
    rex.shutdown(wait=True)
    if all(os.path.exists(f"{WORK}/blocks/{sid}/{by}_{bx}.done.json") for by, bx in blocks):
        json.dump(dict(utc=utc(), candidates=len(cand), blocks=len(blocks)), open(f"{WORK}/blocks/{sid}/SEGMENT_DONE.json", "w"))


def main():
    md = json.load(open(f"{WORK}/meta/v0814_9.json"))
    vox = round(float(md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000, 6)
    assert abs(vox - VOXEL_UM) < 1e-9, vox
    segs = sorted(json.load(open(f"{LOGD}/segment_inventory.json"))["inventory"][SC]["segments"])
    if sys.argv[1] != "all":
        segs = [s for s in segs if s.startswith(sys.argv[1])]
    mb = int(sys.argv[sys.argv.index("--max-blocks") + 1]) if "--max-blocks" in sys.argv else None
    for s in segs:
        sid = s.split("-", 1)[0]
        if not os.path.exists(f"{LOGD}/stage_a/{sid}.json"):
            print("no stage A yet", sid, flush=True)
            continue
        if os.path.exists(f"{WORK}/blocks/{sid}/SEGMENT_DONE.json"):
            continue
        run_segment(s, mb)


if __name__ == "__main__":
    main()
