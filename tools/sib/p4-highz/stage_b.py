"""p4-highz steps 2-3 (DECL-P4-6 items 2-3; PROTOCOL.md): level-0 sheet-slab maximum and hi counts for every
eligible control (C) and E1 tile; numeric screen per tile; P4-F PNG tiles for E1 (committed per row).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: PNG bytes are hashed and written, never opened. Usage: python stage_b.py <scratch> <repo>
"""
import concurrent.futures as cf
import hashlib
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

NPROC, NTHR = 6, 24
BR = "claude/gifted-bell-gavnl5-sib-p4-highz"
R0, R1 = 107, 214  # 2-4 mm at 53.4 px/mm
URL = TH = SL = None
RNG = None


def one(yx):
    yc, xc = yx
    b = C.get(f"{URL}/{yc}/{xc}", RNG)
    if b is None:
        return yc, xc, None, None
    a = np.frombuffer(b, np.uint8).reshape(-1, C.CH, C.CH)
    return yc, xc, a.max(0).tobytes(), (a > TH).sum(0).astype(np.uint8).tobytes()


def one_gap(yx):
    yc, xc = yx
    b = C.get(f"{URL}/{yc}/{xc}", RNG)
    if b is None:
        return yc, xc, None
    a = np.frombuffer(b, np.uint8).reshape(-1, C.CH, C.CH)  # slices gap_lo[0] .. gap_hi[1] - 1
    g0 = SL[1][0]
    s = lambda lo, hi: (a[lo - g0:hi - g0] > TH).sum(0).astype(np.uint8).tobytes()
    return yc, xc, (s(*SL[0]), s(*SL[1]), s(*SL[2]))


def work(args):
    global URL, TH, RNG, SL
    kind, URL, TH, RNG, SL, items = args
    fn = one if kind == "sheet" else one_gap
    with cf.ThreadPoolExecutor(NTHR) as ex:
        return list(ex.map(fn, items))


def tile_arrays(mat, r, c):
    T, H, W, valid, dv = mat["T"], mat["H"], mat["W"], mat["valid"], mat["div"]
    ys, xs = r * T + np.arange(T), c * T + np.arange(T)
    v = valid[np.minimum(ys // dv, valid.shape[0] - 1)][:, np.minimum(xs // dv, valid.shape[1] - 1)]
    v &= (ys < H)[:, None] & (xs < W)[None, :]
    return v


def place(dst, r, c, T, yc, xc, arr):
    y0, x0 = yc * C.CH - r * T, xc * C.CH - c * T
    a0, b0 = max(0, -y0), max(0, -x0)
    a1, b1 = min(C.CH, T - y0), min(C.CH, T - x0)
    dst[y0 + a0:y0 + a1, x0 + b0:x0 + b1] = arr[a0:a1, b0:b1]


def acf_stats(D, m):
    if m.sum() < 1000:
        return None
    mu = D[m].mean()
    f = np.where(m, D - mu, 0.0)
    var = float((f[m] ** 2).mean())
    if var <= 0:
        return {"var": 0.0, "radial_peak_2_4mm": None}
    n = D.shape[0]
    F = np.fft.rfft2(f, (2 * n, 2 * n))
    Mf = np.fft.rfft2(m.astype(np.float64), (2 * n, 2 * n))
    A = np.fft.irfft2(F * np.conj(F), (2 * n, 2 * n))
    O = np.fft.irfft2(Mf * np.conj(Mf), (2 * n, 2 * n))
    A, O = np.fft.fftshift(A), np.fft.fftshift(O)
    ok = O > 0.05 * m.sum()
    acf = np.where(ok, A / np.maximum(O, 1) / var, np.nan)
    yy, xx = np.indices(acf.shape) - n
    rr = np.rint(np.hypot(yy, xx)).astype(int)
    sel = ok & (rr >= R0) & (rr <= R1)
    prof = np.bincount(rr[sel], weights=acf[sel], minlength=R1 + 1)[R0:R1 + 1] / np.maximum(
        np.bincount(rr[sel], minlength=R1 + 1)[R0:R1 + 1], 1)
    def axis(sel_ax, coord):
        s = sel & sel_ax
        rad = np.abs(coord[s])
        pr = np.bincount(rad, weights=acf[s], minlength=R1 + 1)[R0:R1 + 1] / np.maximum(
            np.bincount(rad, minlength=R1 + 1)[R0:R1 + 1], 1)
        return float(np.max(pr)), int(R0 + np.argmax(pr))
    pr_r = axis(np.abs(xx) <= 2, yy)
    pr_c = axis(np.abs(yy) <= 2, xx)
    k = int(np.argmax(prof))
    return {"var": var, "radial_peak_2_4mm": float(prof[k]), "radial_peak_radius_mm": (R0 + k) / 53.4,
            "radial_mean_2_4mm": float(prof.mean()),
            "dir_rows_peak": pr_r[0], "dir_rows_peak_mm": pr_r[1] / 53.4,
            "dir_cols_peak": pr_c[0], "dir_cols_peak_mm": pr_c[1] / 53.4}


def stroke_stats(hi, hic, um):
    n = int(hi.sum())
    out = {"hi_px": n}
    if n == 0:
        return out
    dt = cv2.distanceTransform(hi, cv2.DIST_L2, 5)
    ridge = (hi > 0) & (dt >= cv2.dilate(dt, np.ones((3, 3), np.uint8)))
    w = (2 * dt[ridge] - 1) * um
    ncc, lab, st, _ = cv2.connectedComponentsWithStats(hi, connectivity=8)
    st = st[1:]
    ext = np.maximum(st[:, 2], st[:, 3]) * um / 1000.0
    area = st[:, 4]
    out.update({"width_um_p10": float(np.percentile(w, 10)), "width_um_median": float(np.median(w)),
                "width_um_p90": float(np.percentile(w, 90)), "ridge_px": int(ridge.sum()),
                "components": int(ncc - 1), "comp_area_px_median": float(np.median(area)),
                "comp_area_px_p99": float(np.percentile(area, 99)), "comp_area_px_max": int(area.max()),
                "comp_extent_mm_max": float(ext.max()),
                "components_letter_scale_0p5_5mm": int(((ext >= 0.5) & (ext <= 5)).sum()),
                "hi_px_in_letter_scale_components": int(area[(ext >= 0.5) & (ext <= 5)].sum()),
                "mean_hi_depth_um": float(hic[hi > 0].mean() * um)})
    return out


def sh(repo, *cmd):
    return subprocess.run(cmd, cwd=repo, capture_output=True, text=True)


def commit_push(repo, paths, msg):
    sh(repo, "git", "add", *paths)
    sh(repo, "git", "commit", "-q", "-m", msg + "\n\n" + C.PROV + "\n\n" + open(os.path.join(SCR, "..", "attr.txt")).read().strip())
    for i in range(5):
        if sh(repo, "git", "push", "-q", "origin", BR).returncode == 0:
            return True
        time.sleep(2 ** (i + 1))
    return False


def run(name, repo, pool, th):
    global URL, TH, RNG, SL
    mat = C.load_material(name, SCR)
    SL = (mat["sheet"], mat["gap_lo"], mat["gap_hi"])
    URL, TH, RNG = mat["url0"], th["T_hi"], (mat["sheet"][0] * C.PLANE, mat["sheet"][1] * C.PLANE - 1)
    T_mid, T_hi = th["T_mid"], th["T_hi"]
    outp = os.path.join(SCR, f"stage_b_{name}.jsonl")
    done = {(d["r"], d["c"]) for d in map(json.loads, open(outp))} if os.path.exists(outp) else set()
    f1 = os.path.join(repo, "logs/sib/p4-highz/f1")
    os.makedirs(os.path.join(f1, "tiles"), exist_ok=True)
    todo = [t for t in mat["tiles"] if (t["r"], t["c"]) not in done]
    T = mat["T"]

    def submit(t):
        ch = C.tile_chunks(mat, t["r"], t["c"])
        return pool.map_async(work, [("sheet", URL, TH, RNG, SL, ch[i::NPROC * 4]) for i in range(NPROC * 4)])

    fut = submit(todo[0]) if todo else None
    row_files = []
    for k, t in enumerate(todo):
        t0 = time.time()
        res = [x for part in fut.get() for x in part]
        if k + 1 < len(todo):
            fut = submit(todo[k + 1])
        r, c = t["r"], t["c"]
        mip = np.zeros((T, T), np.uint8)
        hic = np.zeros((T, T), np.uint8)
        absent = np.zeros((T, T), bool)
        n_abs = 0
        for yc, xc, mb, hb in res:
            if mb is None:
                n_abs += 1
                place(absent, r, c, T, yc, xc, np.ones((C.CH, C.CH), bool))
                continue
            place(mip, r, c, T, yc, xc, np.frombuffer(mb, np.uint8).reshape(C.CH, C.CH))
            place(hic, r, c, T, yc, xc, np.frombuffer(hb, np.uint8).reshape(C.CH, C.CH))
        v = tile_arrays(mat, r, c)
        vp = v & ~absent
        mv = mip[vp]
        hi = ((mip > T_hi) & vp).astype(np.uint8)
        hicv = np.where(vp, hic, 0)
        n_hi = int(hicv.sum(dtype=np.int64))
        # display-grid density for the autocorrelation
        vf_d = cv2.resize(vp.astype(np.float32), (C.OUT_SIDE, C.OUT_SIDE), interpolation=cv2.INTER_AREA)
        hd = cv2.resize(hicv.astype(np.float32), (C.OUT_SIDE, C.OUT_SIDE), interpolation=cv2.INTER_AREA)
        md = vf_d >= 0.5
        D = np.where(md, hd / np.maximum(vf_d, 1e-9), 0.0)
        a0 = acf_stats(D, md)
        a90 = acf_stats(np.rot90(D), np.rot90(md))
        ss = stroke_stats(hi, hic, mat["um"])
        rec = {"r": r, "c": c, "material": name, "valid_fraction": float(v.sum()) / (T * T),
               "valid_fraction_src": t["valid_fraction_src"], "frac_outside": t["frac_outside"],
               "chunks": len(res), "chunks_absent": n_abs, "frac_valid_in_absent_chunk": float(absent[v].mean()) if v.any() else None,
               "n_hi": n_hi, "valid_px_present": int(vp.sum()), "n_hi_per_1e6_voxels": n_hi / max(1, (mat["sheet"][1] - mat["sheet"][0]) * int(vp.sum())) * 1e6,
               "mip_mean": float(mv.mean()) if mv.size else None, "mip_std": float(mv.std()) if mv.size else None,
               "frac_mip_zero": float((mv == 0).mean()) if mv.size else None,
               "frac_mip_gt_T_hi": float((mv > T_hi).mean()) if mv.size else None,
               "frac_mip_255": float((mv == 255).mean()) if mv.size else None,
               "acf": a0, "acf_rot90": a90, "stroke": ss}
        if name == "E1":
            val = np.clip(255.0 * (mip.astype(np.float32) - T_mid) / (T_hi - T_mid), 0, 255)
            val[~v] = 0
            disp = np.rint(cv2.resize(val, (C.OUT_SIDE, C.OUT_SIDE), interpolation=cv2.INTER_AREA)).clip(0, 255).astype(np.uint8)
            sys.path.insert(0, os.path.join(repo, "src"))
            from hercules.display.builder import png_bytes
            b = png_bytes(disp)
            chunks_, i = [], 8
            while i < len(b):
                n = int.from_bytes(b[i:i + 4], "big")
                chunks_.append(b[i + 4:i + 8].decode("ascii"))
                i += 12 + n
            assert set(chunks_) <= {"IHDR", "IDAT", "IEND"} and disp.shape == (C.OUT_SIDE, C.OUT_SIDE)
            fn = f"{mat['seg']}_r{r}_c{c}.png"
            open(os.path.join(f1, "tiles", fn), "wb").write(b)
            rec.update({"file": f"tiles/{fn}", "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                        "disp_frac_255": float((disp[md] == 255).mean()), "disp_frac_0_valid": float((disp[md] == 0).mean())})
            row_files.append(os.path.join(f1, "tiles", fn))
        rec["canvas_rows"], rec["canvas_cols"] = [r * T, (r + 1) * T], [c * T, (c + 1) * T]
        rec["secs"] = round(time.time() - t0, 1)
        with open(outp, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps({"m": name, "r": r, "c": c, "secs": rec["secs"], "absent": n_abs}), flush=True)
        nxt = todo[k + 1]["r"] if k + 1 < len(todo) else None
        if name == "E1" and nxt != r:
            import shutil
            shutil.copy(outp, os.path.join(f1, "partial_records_E1.jsonl"))
            ok = commit_push(repo, row_files + [os.path.join(f1, "partial_records_E1.jsonl")],
                             f"p4-highz F1 (DECL-P4-6): P4-F tiles, E1 row {r} ({len(row_files)} tiles)")
            print(json.dumps({"commit_row": r, "pushed": ok}), flush=True)
            row_files = []


def run_gap(name, repo, pool, th, tiles):
    """Full-coverage in-sheet fraction (slices 5..111) for the listed (r, c) tiles."""
    global URL, TH, RNG, SL
    mat = C.load_material(name, SCR)
    SL = (mat["sheet"], mat["gap_lo"], mat["gap_hi"])
    URL, TH, RNG = mat["url0"], th["T_hi"], (mat["gap_lo"][0] * C.PLANE, mat["gap_hi"][1] * C.PLANE - 1)
    outp = os.path.join(SCR, f"stage_b_gap_{name}.jsonl")
    done = {(d["r"], d["c"]) for d in map(json.loads, open(outp))} if os.path.exists(outp) else set()
    T = mat["T"]
    for (r, c) in tiles:
        if (r, c) in done:
            continue
        t0 = time.time()
        ch = C.tile_chunks(mat, r, c)
        res = [x for part in pool.map(work, [("gap", URL, TH, RNG, SL, ch[i::NPROC * 4]) for i in range(NPROC * 4)]) for x in part]
        v = tile_arrays(mat, r, c)
        acc = [np.zeros((T, T), np.uint8) for _ in range(3)]
        for yc, xc, bs in res:
            if bs is None:
                continue
            for a, b in zip(acc, bs):
                place(a, r, c, T, yc, xc, np.frombuffer(b, np.uint8).reshape(C.CH, C.CH))
        n = [int(np.where(v, a, 0).sum(dtype=np.int64)) for a in acc]
        rec = {"r": r, "c": c, "n_sheet": n[0], "n_gap_lo": n[1], "n_gap_hi": n[2],
               "f_in_full": n[0] / max(1, sum(n)), "secs": round(time.time() - t0, 1)}
        with open(outp, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    SCR, repo = sys.argv[1], sys.argv[2]
    os.chdir(repo)
    mode = sys.argv[3] if len(sys.argv) > 3 else "tiles"
    names = (sys.argv[4:] or ["C", "E1"]) if mode == "tiles" else [sys.argv[4]]
    thf = {n: "logs/sib/p4-highz/" + ("thresholds.json" if n in ("C", "E1") else "thresholds_2p4.json") for n in names}
    sh(repo, "git", "fetch", "-q", "origin", BR)
    for f in set(thf.values()):
        # thresholds must be committed and pushed before any tile number exists
        assert sh(repo, "git", "diff", "--quiet", "HEAD", "--", f).returncode == 0, f
        assert sh(repo, "git", "cat-file", "-e", f"origin/{BR}:{f}").returncode == 0, f
    with mp.get_context("fork").Pool(NPROC) as pool:
        if mode == "tiles":
            for name in names:
                run(name, repo, pool, json.load(open(os.path.join(repo, thf[name]))))
        else:
            name = sys.argv[4]
            tiles = [tuple(map(int, x.split(","))) for x in sys.argv[5:]]
            run_gap(name, repo, pool, json.load(open(os.path.join(repo, thf[name]))), tiles)
