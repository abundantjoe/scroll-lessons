# Provenance: Project HERCULES | owner the owner | [id removed]
"""Which downsampling does the pyramid use? Compare level 1 with 2x2x2 mean pooling and with
strided picks of level 0 on an interior 256^3 block (per volume). Numbers only."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import zio
res = {}
for vol, (z, y, x) in {"v9": (14080, 3840, 1280), "v2": (7424, 15360, 5120)}.items():
    a0, _ = zio.read(vol, 0, z, z + 256, y, y + 256, x, x + 256, tag="pyr_check")
    a1, _ = zio.read(vol, 1, z // 2, z // 2 + 128, y // 2, y // 2 + 128, x // 2, x // 2 + 128, tag="pyr_check")
    a0 = a0.astype(np.float64); a1 = a1.astype(np.float64)
    mp = a0.reshape(128, 2, 128, 2, 128, 2).mean((1, 3, 5))
    r = {"nonzero0": float((a0 > 0).mean())}
    def cc(u, v): u = u - u.mean(); v = v - v.mean(); return float((u * v).sum() / np.sqrt((u * u).sum() * (v * v).sum()))
    r["corr_meanpool"] = cc(a1, mp); r["maxabs_meanpool"] = float(np.abs(a1 - mp).max())
    r["mae_meanpool"] = float(np.abs(a1 - mp).mean()); r["mae_meanpool_rounded"] = float(np.abs(a1 - np.round(mp)).mean())
    for o in [0, 1]:
        s = a0[o::2, o::2, o::2]; r[f"corr_stride{o}"] = cc(a1, s); r[f"mae_stride{o}"] = float(np.abs(a1 - s).mean())
    res[vol] = r
print(json.dumps(res, indent=1))
json.dump(res, open("/home/user/dominion/logs/sib/reg0841/pyr_check.json", "w"), indent=1)
