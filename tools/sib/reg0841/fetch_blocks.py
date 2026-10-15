# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch level-0 blocks for every planned patch (resumable; skips finished patches).
9 um: the 48 x 256 x 256 block. Rescan: bounding box of the block grown by G9 = 12 (9 um vox)
mapped through the mesh affine, grown by 10 rescan vox. Writes /work/reg/blocks/<id>_{v9,v2}.npy
and <id>.json (origins, hashes). Usage: fetch_blocks.py [fit|heldout|all]"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import zio
REPO = "/home/user/dominion"; OUT = "/work/reg/blocks"; os.makedirs(OUT, exist_ok=True)
plan = json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))
mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]
A = np.array(mf["A"]); c = np.array(mf["c"])
G9, G2 = 12, 10
roles = {"all": ("fit", "heldout")}.get(sys.argv[1], (sys.argv[1],))
for p in plan["patches"]:
    if p["role"] not in roles or os.path.exists(f"{OUT}/{p['id']}.json"):
        continue
    x, y, z = [int(v) for v in p["centre_xyz"]]
    hz, hy, hx = [s // 2 for s in plan["block_zyx"]]
    o9 = [z - hz, y - hy, x - hx]
    b9, i9 = zio.read("v9", 0, o9[0], o9[0] + 2 * hz, o9[1], o9[1] + 2 * hy, o9[2], o9[2] + 2 * hx, tag=p["id"])
    lo = np.array([x - hx - G9, y - hy - G9, z - hz - G9], float); hi = np.array([x + hx + G9, y + hy + G9, z + hz + G9], float)
    cr = np.array([[a, b, d] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for d in (lo[2], hi[2])]) @ A.T + c
    qlo = np.floor(cr.min(0)).astype(int) - G2; qhi = np.ceil(cr.max(0)).astype(int) + G2
    o2 = [int(qlo[2]), int(qlo[1]), int(qlo[0])]
    b2, i2 = zio.read("v2", 0, o2[0], int(qhi[2]), o2[1], int(qhi[1]), o2[2], int(qhi[0]), tag=p["id"])
    np.save(f"{OUT}/{p['id']}_v9.npy", b9); np.save(f"{OUT}/{p['id']}_v2.npy", b2)
    rec = dict(id=p["id"], role=p["role"], origin9_zyx=o9, shape9=list(b9.shape), origin2_zyx=o2, shape2=list(b2.shape),
               v9=i9, v2=i2, zero_frac9=float((b9 == 0).mean()), zero_frac2=float((b2 == 0).mean()))
    json.dump(rec, open(f"{OUT}/{p['id']}.json", "w"), indent=1)
    print(json.dumps(rec), flush=True)
