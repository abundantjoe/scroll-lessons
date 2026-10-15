# Provenance: Project HERCULES | owner the owner | [id removed]
"""Diagnostic (reported, not deciding): where does the systematic window shift come from?
For the tiles of a registry (default: smoke run), per 9 window: best shift and NCC of
  A  ours (render slice 15)             vs organizer 9.362 um SV (mean of surface slices 13, 14 of 28), same canvas
  B  organizer 9.362 um SV (13, 14)     vs 2.399 um reference through M (same reference as the gate)
  C  ours                               vs 2.399 um reference (= the gate's numbers, recomputed)
A ~ 0 shift validates our render/canvas path; B ~ C means the shift is between the two scans, not in our render.
Numbers only. Usage: diag_conv.py SEG REGISTRY.jsonl OUT.json"""
import json, sys, math
import numpy as np, zarr
import build_pairs as B
from sv24 import SV24

seg, reg, outp = sys.argv[1:4]
aff = json.load(open("/work/p139/affines.json"))
S = B.Seg(seg, aff, None)
rows = [json.loads(l) for l in open(reg)]
sv = SV24(seg, level=1)


class SV9(SV24):
    def __init__(self, seg):
        self.prefix = f"PHerc0139/segments/{seg}/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr/0"
        za = json.loads(__import__("sv24")._s3().get_object(Bucket=__import__("sv24").B, Key=self.prefix + "/.zarray")["Body"].read())
        self.shape = tuple(za["shape"]); self.chunks = tuple(za["chunks"])
        from concurrent.futures import ThreadPoolExecutor
        self.ex = ThreadPoolExecutor(16); self.bytes = 0; self.requests = 0


sv9 = SV9(seg)
assert sv9.shape[1:] == tuple(S.c9.shape), (sv9.shape, S.c9.shape)
R = zarr.open(f"/work/p139/render/{B.short(seg)}.zarr", mode="r")
R = R["0"] if hasattr(R, "keys") and "0" in R.keys() else R
res = []
for r in rows:
    Y, X = r["canvas9_y0"], r["canvas9_x0"]; ry, rx = r["render_y0"], r["render_x0"]
    ours = np.asarray(R[B.ZS, ry:ry + B.T, rx:rx + B.T]).astype(np.float64)
    o9 = sv9.read(13, 15, Y - B.SMAX, Y + B.T + B.SMAX, X - B.SMAX, X + B.T + B.SMAX).astype(np.float64)
    v9 = (o9 > 0).all(0); o9 = o9.mean(0)
    y2, x2 = S.sub_coords(Y - B.SMAX, X - B.SMAX, B.T + 2 * B.SMAX, B.T + 2 * B.SMAX)
    y1 = (y2 + 0.5) / 2 - 0.5; x1 = (x2 + 0.5) / 2 - 0.5
    ly0, lx0 = int(np.floor(y1.min())) - 1, int(np.floor(x1.min())) - 1
    blk = sv.read(B.L1_Z0, B.L1_Z1, ly0, int(np.ceil(y1.max())) + 2, lx0, int(np.ceil(x1.max())) + 2)
    ref = B.area_sample(blk.astype(np.float32).mean(0), (ly0, lx0), y1, x1).mean(-1)
    rv = B.area_sample((blk > 0).all(0).astype(np.float32), (ly0, lx0), y1, x1)
    vr = np.isfinite(ref) & (np.nan_to_num(rv, nan=0).min(-1) >= 0.999)
    vo = ours > 0
    o9c = o9[B.SMAX:B.SMAX + B.T, B.SMAX:B.SMAX + B.T]; v9c = v9[B.SMAX:B.SMAX + B.T, B.SMAX:B.SMAX + B.T]
    out = dict(tile=r["tile_id"])
    for name, (a, va, b, vb) in {"A_ours_vs_org9": (ours, vo, o9, v9), "B_org9_vs_ref24": (o9c, v9c, np.nan_to_num(ref), vr),
                                  "C_ours_vs_ref24": (ours, vo, np.nan_to_num(ref), vr)}.items():
        w = [B.best_shift(a, b, va, vb, wy, wx) for wy in B.WOFF for wx in B.WOFF]
        m0 = va & vb[B.SMAX:B.SMAX + B.T, B.SMAX:B.SMAX + B.T]
        out[name] = dict(ncc0=B.ncc(a, b[B.SMAX:B.SMAX + B.T, B.SMAX:B.SMAX + B.T], m0),
                         dy=[x[0] for x in w], dx=[x[1] for x in w], ncc=[x[2] for x in w], border=[x[3] for x in w])
    res.append(out)
summ = {}
for name in ("A_ours_vs_org9", "B_org9_vs_ref24", "C_ours_vs_ref24"):
    dy = np.array([v for o in res for v, b in zip(o[name]["dy"], o[name]["border"]) if not b and np.isfinite(v)])
    dx = np.array([v for o in res for v, b in zip(o[name]["dx"], o[name]["border"]) if not b and np.isfinite(v)])
    n0 = np.array([o[name]["ncc0"] for o in res], float)
    summ[name] = dict(n_tiles=len(res), ncc0_median=float(np.nanmedian(n0)), ncc0_p90=float(np.nanpercentile(n0, 90)),
                      dy_median=float(np.median(dy)), dx_median=float(np.median(dx)),
                      shift_len_median=float(np.median(np.hypot(dy, dx))),
                      border_frac=float(np.mean([b for o in res for b in o[name]["border"]])))
print(json.dumps(summ, indent=1))
json.dump(dict(provenance=B.PROV, segment=seg, registry=reg, summary=summ, tiles=res), open(outp, "w"))
