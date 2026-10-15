"""p4-purple-de B4(a): known-text labels for the control sites from the official 2.4 um prediction of w028-037
(ink >= strip p90, background <= strip p50, 50 um boundary exclusion; DECL-P4-9 recipe). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python labels.py <scratch>   (after sites.py; writes <scratch>/labels/<id>.npy and logs/.../labels.json)
"""
import json
import os
import sys

import numpy as np
import tifffile
import zlib
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

scr = sys.argv[1]
od = os.path.join(scr, "labels")
os.makedirs(od, exist_ok=True)
KEY = ("PHercParis4/segments/20260701183125-w028-037/ink-detection/PHercParis4-20260701183125-2.4um-0.22m-78keV-volume-"
       "20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif")
tp = os.path.join(scr, "pred.tif")
if not os.path.exists(tp):
    import hashlib
    h = hashlib.sha256()
    with D.session().get(f"{D.BUCKET}/{KEY}", stream=True, timeout=600) as r, open(tp, "wb") as f:
        r.raise_for_status()
        for b in r.iter_content(1 << 22):
            f.write(b)
            h.update(b)
    open(tp + ".sha256", "w").write(h.hexdigest())
sha = open(tp + ".sha256").read().strip()
tf = tifffile.TiffFile(tp)
pg = tf.pages[0]
assert pg.compression == 32946 and pg.predictor == 1 and pg.is_tiled and pg.dtype == np.uint8
Hc, Wc = pg.shape[:2]
TH, TW = pg.tilelength, pg.tilewidth
NTW = (Wc + TW - 1) // TW
fh = open(tp, "rb")


def tile(ti, tj):
    k = ti * NTW + tj
    fh.seek(pg.dataoffsets[k])
    return np.frombuffer(zlib.decompress(fh.read(pg.databytecounts[k])), np.uint8).reshape(TH, TW)


def window(r0, r1, c0, c1):
    out = np.zeros((r1 - r0, c1 - c0), np.uint8)
    for ti in range(r0 // TH, (r1 - 1) // TH + 1):
        for tj in range(c0 // TW, (c1 - 1) // TW + 1):
            t = tile(ti, tj)
            a0, a1 = max(r0, ti * TH), min(r1, (ti + 1) * TH)
            b0, b1 = max(c0, tj * TW), min(c1, (tj + 1) * TW)
            out[a0 - r0:a1 - r0, b0 - c0:b1 - c0] = t[a0 - ti * TH:a1 - ti * TH, b0 - tj * TW:b1 - tj * TW]
    return out


xyz, _ = D.load_mesh(D.SEG_C2, scr)
valid_grid = np.isfinite(np.asarray(xyz[..., 0]))

# strip percentiles over mesh-valid canvas px, every 8th row and column
vals = []
cols = np.arange(0, Wc, 8)
for ti in range((Hc + TH - 1) // TH):
    r0, r1 = ti * TH, min(Hc, (ti + 1) * TH)
    blk = np.concatenate([tile(ti, tj) for tj in range(NTW)], 1)[:r1 - r0:8][:, :Wc:8] if TH % 8 == 0 else None
    rows = np.arange(r0, r1, 8)
    m = valid_grid[np.minimum(rows // 20, valid_grid.shape[0] - 1)][:, np.minimum(cols // 20, valid_grid.shape[1] - 1)]
    vals.append(blk[m])
vals = np.concatenate(vals)
p50, p90 = float(np.percentile(vals, 50)), float(np.percentile(vals, 90))
sites = json.load(open(os.path.join(D.REPO, "logs/sib/p4-purple/de/sites.json")))["sites"]
out = {"provenance": D.PROV, "serves": "PROTOCOL.md B4 (a) labels", "prediction_key": KEY, "prediction_sha256": sha,
       "prediction_shape": [int(Hc), int(Wc)], "strip_sample_px": int(len(vals)), "p50": p50, "p90": p90,
       "exclusion_px": 21, "sites": {}}
for part in ("fit", "held"):
    for s in sites[part]:
        ci, cj = s["canvas_centre_ij"]
        w = window(ci - 249, ci + 249, cj - 249, cj + 249).astype(np.float32)
        ink, bg = w >= p90, w <= p50
        d_ink = ndi.distance_transform_edt(~ink)
        d_bg = ndi.distance_transform_edt(~bg)
        lab = np.zeros(w.shape, np.int8)       # 0 none, 1 ink, -1 background
        lab[ink & (d_bg > 21)] = 1
        lab[bg & (d_ink > 21)] = -1
        np.save(os.path.join(od, s["id"] + ".npy"), lab)
        out["sites"][s["id"]] = {"frac_ink": float((lab == 1).mean()), "frac_bg": float((lab == -1).mean())}
json.dump(out, open(os.path.join(D.REPO, "logs/sib/p4-purple/de/labels.json"), "w"), indent=1)
print(p50, p90, len(vals))
