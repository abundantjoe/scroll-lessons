# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch blocks for planned patches of a ROLE (resumable). 9 um: 48 x 256 x 256 level-0 block.
2.215 um: LEVEL 1 bounding box of the block grown by G9 = 12 (9 um vox) mapped through the
organizer affine, grown by G1 = 6 level-1 vox. Writes /work/k4p/blocks/<id>_{v9,v2}.npy + <id>.json
(origins, chunk hashes). Usage: fetch_blocks.py fit|heldout"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import zio
REPO = "/home/user/dominion"; OUT = "/work/k4p/blocks"; os.makedirs(OUT, exist_ok=True)
plan = json.load(open(f"{REPO}/logs/sib/ktlb4p-prep/reg/patch_plan.json"))
if sys.argv[1] == "heldout":
    assert os.path.exists(f"{REPO}/logs/sib/ktlb4p-prep/reg/model_final.json"), "model must be frozen before held-out reads"
M = np.array(plan["organizer_affine"]); A, c = M[:, :3], M[:, 3]
G9, G1 = 12, 6
for p in plan["patches"]:
    if p["role"] != sys.argv[1] or os.path.exists(f"{OUT}/{p['id']}.json"):
        continue
    x, y, z = [int(v) for v in p["centre_xyz"]]
    hz, hy, hx = [s // 2 for s in plan["block_zyx"]]
    o9 = [z - hz, y - hy, x - hx]
    b9, i9 = zio.read("v9", 0, o9[0], o9[0] + 2 * hz, o9[1], o9[1] + 2 * hy, o9[2], o9[2] + 2 * hx, tag=p["id"])
    lo = np.array([x - hx - G9, y - hy - G9, z - hz - G9], float); hi = np.array([x + hx + G9, y + hy + G9, z + hz + G9], float)
    cr = np.array([[a, b, e] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for e in (lo[2], hi[2])]) @ A.T + c
    q1lo = np.floor((cr.min(0) - 0.5) / 2).astype(int) - G1; q1hi = np.ceil((cr.max(0) - 0.5) / 2).astype(int) + G1
    o2 = [int(q1lo[2]), int(q1lo[1]), int(q1lo[0])]
    b2, i2 = zio.read("v2", 1, o2[0], int(q1hi[2]), o2[1], int(q1hi[1]), o2[2], int(q1hi[0]), tag=p["id"])
    np.save(f"{OUT}/{p['id']}_v9.npy", b9); np.save(f"{OUT}/{p['id']}_v2.npy", b2)
    rec = dict(id=p["id"], role=p["role"], origin9_zyx=o9, shape9=list(b9.shape), origin2_zyx_level1=o2, shape2=list(b2.shape),
               v9=i9, v2=i2, zero_frac9=float((b9 == 0).mean()), zero_frac2=float((b2 == 0).mean()))
    json.dump(rec, open(f"{OUT}/{p['id']}.json", "w"), indent=1)
    print(p["id"], b9.shape, b2.shape, round(rec["zero_frac9"], 3), round(rec["zero_frac2"], 3), flush=True)
