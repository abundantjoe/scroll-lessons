"""Frozen-rule grain threshold for the 2.4 um materials (E2/C2) at level 1, from the CONTROL only (DECL-P4-6 item 2 rule:
p99.9 of in-sheet voxels > 0 of the known-text control). Sample: 600 random level-1 chunk positions of the control 2.4 um
surface volume (default_rng(20260926)); chunks with >= 90 % nonzero sheet voxels; sheet slab slices 46..62 (54 +- 8).
Provenance: Project HERCULES | owner the owner | [id removed]
"""
import concurrent.futures as cf, json, sys
import numpy as np, requests
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import hz_common as C
SV = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/segments/20260623142658-w028-037/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr/1"
za = requests.get(SV + "/.zarray").json(); H, W = za["shape"][1:]
rng = np.random.default_rng(20260926); ys = rng.integers(0, -(-H // 128), 600); xs = rng.integers(0, -(-W // 128), 600)
P = 128 * 128; rg = (46 * P, 63 * P - 1)
h = np.zeros(256, np.int64); used = 0
with cf.ThreadPoolExecutor(32) as ex:
    for b in ex.map(lambda yx: C.get(f"{SV}/0/{yx[0]}/{yx[1]}", rg), zip(ys, xs)):
        if b is None: continue
        a = np.frombuffer(b, np.uint8)
        if (a > 0).mean() < 0.9: continue
        used += 1; h += np.bincount(a, minlength=256)
h[0] = 0; c = np.cumsum(h) / h.sum()
out = {"provenance": C.PROV, "material": "C2 control 2.4 um level 1 sheet slab 46..62", "chunks_used": used,
       "p50": int(np.searchsorted(c, .5)), "p99": int(np.searchsorted(c, .99)), "p99.9": int(np.searchsorted(c, .999)),
       "p99.99": int(np.searchsorted(c, .9999)), "frac_255": float(h[255] / h.sum()), "hist": [int(x) for x in h]}
json.dump(out, open(sys.argv[1], "w"), indent=1); print({k: v for k, v in out.items() if k != "hist"})
