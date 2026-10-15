"""P4-L L2S (RULES.md DECL-P4-12-A2): per-tile 1-99 % stretch of the same thin-slab max channel.

Provenance: Project HERCULES | owner the owner | [id removed]

Builder only: never opens, views or prints image pixels. Numbers, hashes and PNG bytes only.
Per tile: recompute the slab max with l2.region (identical code and params as L2), then
  1. rebuild the L2 display and check its PNG sha256 equals the pushed L2 manifest (determinism check);
  2. store the unstretched max (uint8, 8343 x 8343, raw CT scale) as <raw_dir>/<segment>_r<r>_c<c>.npz (sha256 recorded);
  3. L2S display: hercules.display.builder.linear_window_ct over mesh-valid px with max > 0 (DECL-P4-5-A1 rule),
     0 outside mesh-valid and where max == 0; cv2.INTER_AREA 8343 -> 1068; uint8 PNG IHDR/IDAT/IEND.
Usage: l2s.py <mesh_dir> <l2s_dir> <raw_dir> <thresholds.json> <l2_manifest.json> --worker k --nworkers n
"""
import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402
from hercules.display import builder  # noqa: E402  (l2 put src on sys.path)


def main():
    ap = argparse.ArgumentParser()
    for n in ("mesh_dir", "out", "raw_dir", "thresholds", "l2_manifest"):
        ap.add_argument(n)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--nworkers", type=int, default=1)
    ap.add_argument("--threads", type=int, default=16)
    a = ap.parse_args()
    th = json.load(open(a.thresholds))
    t_mid, t_hi = int(th["T_mid"]), int(th["T_hi"])
    za, _ = l2.zarray(l2.SEG)
    H0, W0 = za["shape"][1:]
    assert (H0, W0) == (69760, 170000)
    valid = l2.load_valid(a.mesh_dir)
    man = json.load(open(a.l2_manifest))
    assert not man["partial"] and man["n_tiles"] == 160
    ref = {(t["r"], t["c"]): t for t in man["tiles"]}
    tiles = l2.order_tiles(list(ref))[a.worker::a.nworkers]
    tdir = os.path.join(a.out, "tiles")
    os.makedirs(tdir, exist_ok=True)
    os.makedirs(a.raw_dir, exist_ok=True)
    cen = os.path.join(a.out, "census_w%d.jsonl" % a.worker)
    done = {(d["r"], d["c"]) for d in map(json.loads, open(cen))} if os.path.exists(cen) else set()
    ex = cf.ThreadPoolExecutor(a.threads)
    for r, c in tiles:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1, x0, x1 = r * l2.T, (r + 1) * l2.T, c * l2.T, (c + 1) * l2.T
        m = l2.canvas_mask(valid, H0, W0, y0, y1, x0, x1)
        assert m.mean() == ref[(r, c)]["valid_fraction"]
        mx, hist, n_hi, recs = l2.region(l2.SEG, y0, y1, x0, x1, (H0, W0), m, ex, t_hi=t_hi)
        t1 = time.time()
        # 1. determinism check against pushed L2
        b2 = builder.png_bytes(cv2.resize(l2.display_from_max(mx, m, t_mid, t_hi), (l2.OUT_SIDE, l2.OUT_SIDE),
                                          interpolation=cv2.INTER_AREA))
        l2_ok = hashlib.sha256(b2).hexdigest() == ref[(r, c)]["png_sha256"]
        # 2. raw max
        fn = f"{l2.SEG}_r{r}_c{c}"
        buf = io.BytesIO()
        np.savez_compressed(buf, max=mx, valid=m)
        raw = buf.getvalue()
        with open(os.path.join(a.raw_dir, fn + ".npz"), "wb") as fh:
            fh.write(raw)
        # 3. L2S
        sv = m & (mx > 0)
        disp, (lo, hi) = builder.linear_window_ct(mx, valid=sv)
        disp[~sv] = 0
        out = cv2.resize(disp, (l2.OUT_SIDE, l2.OUT_SIDE), interpolation=cv2.INTER_AREA)
        assert out.shape == (l2.OUT_SIDE, l2.OUT_SIDE) and out.dtype == np.uint8
        b = builder.png_bytes(out)
        ch = l2.png_chunks(b)
        assert set(ch) <= {"IHDR", "IDAT", "IEND"} and ch[0] == "IHDR" and ch[-1] == "IEND", ch
        assert b[16:24] == l2.OUT_SIDE.to_bytes(4, "big") * 2 and b[24] == 8 and b[25] == 0
        with open(os.path.join(tdir, fn + ".png"), "wb") as fh:
            fh.write(b)
        vals = mx[m]
        vh = np.bincount(vals, minlength=256)
        rec = {"file": "tiles/" + fn + ".png", "r": r, "c": c, "png_sha256": hashlib.sha256(b).hexdigest(),
               "png_bytes": len(b), "png_chunks": sorted(set(ch)), "valid_fraction": float(m.mean()),
               "canvas_rows": [y0, y1], "canvas_cols": [x0, x1], "level": l2.LEVEL,
               "raw_npz": fn + ".npz", "raw_npz_sha256": hashlib.sha256(raw).hexdigest(), "raw_npz_bytes": len(raw),
               "raw_max_sha256": hashlib.sha256(np.ascontiguousarray(mx).tobytes()).hexdigest(),
               "l2_png_rebuilt_equal": l2_ok,
               "stats": {"domain": "slab max (slices 48..60, level 0) at mesh-valid canvas px",
                         "valid_px": int(vals.size), "stretch_px": int(sv.sum()),
                         "stretch_p1": lo, "stretch_p99": hi,
                         "max_mean": float(vals.mean()), "max_std": float(vals.std()),
                         **{"max_p%s" % q: l2.q_hist(vh, float(q) / 100) for q in ("1", "50", "99", "99.9")},
                         "frac_valid_max_zero": float((vals == 0).mean()),
                         "frac_out_zero": float((out == 0).mean()), "frac_out_255": float((out == 255).mean()),
                         "out_mean": float(out.mean())},
               "chunks_read": sum(x["status"] == 206 for x in recs),
               "chunks_missing": sum(x["status"] == 404 for x in recs),
               "read_s": round(t1 - t0, 1), "compute_s": round(time.time() - t1, 1), "utc": l2.utc()}
        with open(cen, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("l2s r%d c%d l2_equal=%s %.1fs" % (r, c, l2_ok, time.time() - t0), flush=True)
        del mx, disp, out
    ex.shutdown()
    print("WORKER_DONE", a.worker, l2.utc(), flush=True)


if __name__ == "__main__":
    main()
