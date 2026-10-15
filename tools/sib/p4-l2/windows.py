"""DECL-P4-17 item 1: P4-W title-scale windows (4 x 4 cm, 2 cm stride) from the P4-L raw store, L2S display.

Provenance: Project HERCULES | owner the owner | [id removed]
Builder only; never views a pixel. A window with top-left strip-a tile (r, c) covers tiles (r..r+1, c..c+1), canvas
rows [r*T, (r+2)*T), cols [c*T, (c+2)*T). Its unstretched slab max and mesh-valid mask are assembled from the four
raw npz files (sha256-checked against l2s/manifest.json). Display = the L2S rule on the window: builder.linear_window_ct
over mesh-valid px with max > 0, 0 elsewhere; cv2.INTER_AREA 16686 -> 1068 (26.7 px/mm); uint8 PNG IHDR/IDAT/IEND.
Sets: w (title zone, c = 9..18) and wpc (known-text positive control, c = 0..7); r = 0..6; eligible iff window
mesh-valid fraction >= 0.5 (all four tiles are in the 160-tile eligible set). File and window ids are uuid4, drawn
at build time and independent of tile ids; r, c in the manifest = the top-left tile (score_p4 --cand-cmin=9).
Usage: windows.py <raw_dir> <l2s_manifest> <out_root> --set w|wpc --worker k --nworkers n
"""
import argparse
import hashlib
import json
import os
import sys
import time
import uuid

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402
from hercules.display import builder  # noqa: E402

COLS = {"w": range(9, 19), "wpc": range(0, 8)}
ROWS = range(0, 7)


def pct_linear_from_hist(h, q):
    """np.percentile(values, q) (method 'linear') computed exactly from the uint8 histogram h of the values."""
    n = int(h.sum())
    c = np.cumsum(h)
    idx = (n - 1) * (q / 100.0)
    i0 = int(np.floor(idx))
    i1 = min(i0 + 1, n - 1)
    a = float(np.searchsorted(c, i0 + 1))
    b = float(np.searchsorted(c, i1 + 1))
    t = idx - i0
    return float(np.lerp(a, b, t)) if hasattr(np, "lerp") else float(
        (b - (b - a) * (1 - t)) if t >= 0.5 else (a + (b - a) * t))


def lean_display(mx, sv):
    """Byte-identical to builder.linear_window_ct(mx, valid=sv) then disp[~sv] = 0, without float64 full arrays."""
    h = np.bincount(mx[sv], minlength=256)
    lo, hi = pct_linear_from_hist(h, builder.LINEAR_LO_PCT), pct_linear_from_hist(h, builder.LINEAR_HI_PCT)
    if hi <= lo:
        hi = lo + 1.0
    lut = np.rint(np.clip((np.arange(256, dtype=np.float64) - lo) / (hi - lo) * 255.0, 0, 255)).astype(np.uint8)
    disp = lut[mx]
    disp[~sv] = 0
    return disp, (lo, hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir")
    ap.add_argument("l2s_manifest")
    ap.add_argument("out_root")
    ap.add_argument("--set", required=True, choices=list(COLS))
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--nworkers", type=int, default=1)
    a = ap.parse_args()
    man = json.load(open(a.l2s_manifest))
    assert not man["partial"]
    tl = {(t["r"], t["c"]): t for t in man["tiles"]}
    out = os.path.join(a.out_root, a.set + "_l2s")
    os.makedirs(os.path.join(out, "tiles"), exist_ok=True)
    cen = os.path.join(out, "census_w%d.jsonl" % a.worker)
    done = {(d["r"], d["c"]) for d in map(json.loads, open(cen))} if os.path.exists(cen) else set()
    plan = [(r, c) for r in ROWS for c in COLS[a.set]][a.worker::a.nworkers]
    T = l2.T
    for r, c in plan:
        if (r, c) in done:
            continue
        t0 = time.time()
        quad = [(r + i, c + j) for i in (0, 1) for j in (0, 1)]
        if not all(q in tl for q in quad):
            rec = {"r": r, "c": c, "eligible": False, "reason": "tile not in eligible set"}
        else:
            mx = np.zeros((2 * T, 2 * T), np.uint8)
            m = np.zeros((2 * T, 2 * T), bool)
            for (rr, cc) in quad:
                t = tl[(rr, cc)]
                b = open(os.path.join(a.raw_dir, t["raw_npz"]), "rb").read()
                assert hashlib.sha256(b).hexdigest() == t["raw_npz_sha256"], t["raw_npz"]
                z = np.load(os.path.join(a.raw_dir, t["raw_npz"]))
                sl = (slice((rr - r) * T, (rr - r + 1) * T), slice((cc - c) * T, (cc - c + 1) * T))
                mx[sl], m[sl] = z["max"], z["valid"]
            vf = float(m.mean())
            rec = {"r": r, "c": c, "eligible": vf >= l2.ELIG, "valid_fraction": vf}
            if rec["eligible"]:
                sv = m & (mx > 0)
                disp, (lo, hi) = lean_display(mx, sv)
                del mx
                o = cv2.resize(disp, (l2.OUT_SIDE, l2.OUT_SIDE), interpolation=cv2.INTER_AREA)
                del disp
                pb = builder.png_bytes(o)
                ch = l2.png_chunks(pb)
                assert set(ch) <= {"IHDR", "IDAT", "IEND"} and pb[16:24] == l2.OUT_SIDE.to_bytes(4, "big") * 2
                wid = str(uuid.uuid4())
                fn = "tiles/%s.png" % wid
                with open(os.path.join(out, fn), "wb") as fh:
                    fh.write(pb)
                rec.update({"window_id": wid, "file": fn, "png_sha256": hashlib.sha256(pb).hexdigest(),
                            "png_bytes": len(pb), "png_chunks": sorted(set(ch)),
                            "canvas_rows": [r * T, (r + 2) * T], "canvas_cols": [c * T, (c + 2) * T],
                            "tiles_covered": [list(q) for q in quad],
                            "stats": {"stretch_px": int(sv.sum()), "stretch_p1": lo, "stretch_p99": hi,
                                      "frac_out_zero": float((o == 0).mean()), "out_mean": float(o.mean())}})
        rec["utc"] = l2.utc()
        rec["s"] = round(time.time() - t0, 1)
        with open(cen, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("%s r%d c%d %.0fs" % (a.set, r, c, rec["s"]), flush=True)
    print("WORKER_DONE", flush=True)


if __name__ == "__main__":
    main()
