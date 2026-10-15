"""edgeshape step 2a: cache per-crop feature matrices (all groups, 4 scales) on sampled label pixels.

Rows: up to 20000 text + 20000 blank labelled pixels per crop (seed 0).
Columns: every feature of every group at sigma in {0,4,8,16}, standardised by the crop's own
mask mean/std (unsupervised, identical operation on every crop).
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import es_lib as E

CACHE = "/home/user/megara/stats/explore/cache"
SIGS = [0, 4, 8, 16]
NPC = 20000
GROUPS = ["LVL", "CH22", "D1", "D2", "SHAPE", "EDGE"]


def build_crop(seg, crop, force=False):
    p = os.path.join(CACHE, f"es_M_{seg}_{crop}.npz")
    if os.path.exists(p) and not force:
        return p
    x, m, t, b = E.load_crop(seg, crop)
    rng = np.random.default_rng(0)
    ti = np.flatnonzero(t.ravel()); bi = np.flatnonzero(b.ravel())
    if ti.size > NPC:
        ti = rng.choice(ti, NPC, replace=False)
    if bi.size > NPC:
        bi = rng.choice(bi, NPC, replace=False)
    idx = np.concatenate([ti, bi])
    y = np.concatenate([np.ones(ti.size, bool), np.zeros(bi.size, bool)])
    cols, names, gidx = [], [], {}
    for sg in SIGS:
        g = E.build_groups(x, m, sg)
        for gn in GROUPS:
            F, nm = g[gn]
            s = len(names)
            for i, n in enumerate(nm):
                f = F[i].ravel()
                mu = float(f[m.ravel()].mean()); sd = float(f[m.ravel()].std()) + 1e-9
                cols.append(((f[idx] - mu) / sd).astype(np.float32))
                names.append(f"{gn}:{n}@{sg}")
            gidx.setdefault(gn, []).extend(range(s, len(names)))
        del g
    M = np.stack(cols, axis=1)
    np.savez_compressed(p, M=M, y=y, names=np.array(names),
                        gidx=json.dumps({k: v for k, v in gidx.items()}))
    return p


if __name__ == "__main__":
    t0 = time.time()
    which = E.TRAIN if len(sys.argv) < 2 else [tuple(a.split("/")) for a in sys.argv[1].split(",")]
    for seg, crop in which:
        p = build_crop(seg, crop)
        print(f"{seg}/{crop} -> {p}  {time.time()-t0:.0f}s", flush=True)
