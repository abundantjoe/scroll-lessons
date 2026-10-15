# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch coarse pyramid levels to /work/reg/cache (npy): 9 um L4 (whole), 9 um L3 (z band
chunks 11-17), rescan L5 (whole), rescan L4 (whole). Prints array hashes (json)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import zio
os.makedirs("/work/reg/cache", exist_ok=True)
out = {}
for vol, lev, zr in [("v9", 4, None), ("v2", 5, None), ("v9", 3, (11 * 128, 18 * 128)), ("v2", 4, None)]:
    shape, ch = zio.meta(vol, lev)
    z0, z1 = zr if zr else (0, shape[0])
    z1 = min(z1, shape[0])
    a, info = zio.read(vol, lev, z0, z1, 0, shape[1], 0, shape[2], tag=f"coarse_{vol}_L{lev}")
    np.save(f"/work/reg/cache/{vol}_L{lev}.npy", a)
    info.update(shape=list(a.shape), z0=z0, level_shape=list(shape), nonzero_frac=float((a > 0).mean()))
    out[f"{vol}_L{lev}"] = info
    print(vol, lev, info, flush=True)
json.dump(out, open("/home/user/dominion/logs/sib/reg0841/coarse_fetch.json", "w"), indent=1)
