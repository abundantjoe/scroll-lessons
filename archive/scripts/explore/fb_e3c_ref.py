"""E3c: the existing methods' pixel AUC on exactly the full-resolution 4096x4096 TRAIN window used
by E3/E3b, so the fibre-frame numbers there have a like-for-like reference."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import auc, ROOT, cdir
import fb_e3_fullres as E3

d = cdir("20231005123336", "train")
out = {}
for t in ("v0.1b", "v1b", "v2", "v3", "team"):
    p = os.path.join(d, f"s_bot_{t}.npy")
    if not os.path.exists(p):
        continue
    s = E3.sub(np.load(p).astype(np.float32))
    out[t] = round(auc(s, E3.txt, E3.blk), 4)
    del s
    print(t, out[t], flush=True)
json.dump(out, open(os.path.join(ROOT, "stats/explore/fb_e3c_ref.json"), "w"), indent=1)
