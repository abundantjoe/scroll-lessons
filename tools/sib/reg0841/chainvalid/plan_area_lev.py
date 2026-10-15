# Provenance: Project HERCULES | owner the owner | [id removed]
"""Area and crops on the LEVELLED canvas (stricter default, ASK 1: the chain levels the mapped meshes; scoring maps
back to the organizer canvas). Levelled px renderable iff its 4 levelled nodes are valid. E_org = organizer-canvas
px that are renderable on the organizer grid (area_<seg>.npy) AND in supervision AND whose mapped levelled px
(nearest) is renderable. Crops (2048, step 1792, 128 px margin) on the levelled canvas; primary = crops whose core
holds mapped E px; secondary = 2 largest-core non-label crops per segment. Writes area_lev.json and
/work/cv/lev_E_<seg>.npz (E_org rows/cols, their levelled px, ink flags)."""
import json, sys
import numpy as np, tifffile, zarr
sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841/chainvalid"); from levelmap import org_px_to_lev_px
SEG = {"w00": "20260220213127-w00", "214732": "20260220214732-auto_grown_20260220144552896", "022814": "20260221022814-auto_grown_20260220174252405"}
out = {"crop": 2048, "step": 1792, "margin": 128, "segments": {}}
for k, s in SEG.items():
    T = json.load(open(f"/work/cv/mesh_lev/{k}/level_transform.json"))
    V = tifffile.imread(f"/work/cv/mesh_lev/{k}/x.tif") != -1
    H, W = V.shape[0] * 20, V.shape[1] * 20
    Wv = V[:-1, :-1] & V[1:, :-1] & V[:-1, 1:] & V[1:, 1:]
    gr = np.floor((np.arange(H) + 0.5) / 20).astype(int); gc = np.floor((np.arange(W) + 0.5) / 20).astype(int)
    okr = gr < Wv.shape[0]; okc = gc < Wv.shape[1]
    RL = np.zeros((H, W), bool); RL[np.ix_(okr, okc)] = Wv[np.ix_(gr[okr], gc[okc])]
    np.save(f"/work/cv/area_lev_{k}.npy", RL)
    Ro = np.load(f"/work/cv/area_{k}.npy")
    sup = zarr.open_array(f"/work/cv/org/{s}/supervision.zarr/0", mode="r")[:] > 0
    ink = zarr.open_array(f"/work/cv/org/{s}/inklabels.zarr/0", mode="r")[:] > 0
    er, ec = np.nonzero(Ro & sup)
    rp, cp = org_px_to_lev_px(T, er, ec)
    ri, ci = np.rint(rp).astype(int), np.rint(cp).astype(int)
    inside = (ri >= 0) & (ci >= 0) & (ri < H) & (ci < W)
    okE = np.zeros(len(er), bool); okE[inside] = RL[ri[inside], ci[inside]]
    np.savez_compressed(f"/work/cv/lev_E_{k}.npz", r=er[okE], c=ec[okE], rp=rp[okE], cp=cp[okE], ink=ink[er[okE], ec[okE]])
    crops = []
    for y in range(-128, H, 1792):
        for x in range(-128, W, 1792):
            y0, y1, x0, x1 = max(y + 128, 0), y + 1920, max(x + 128, 0), x + 1920
            n = int(RL[y0:y1, x0:x1].sum())
            if n:
                ne = int(((ri[okE] >= y0) & (ri[okE] < y1) & (ci[okE] >= x0) & (ci[okE] < x1)).sum())
                crops.append(dict(y=y, x=x, core_px=n, core_E_px=ne))
    out["segments"][k] = dict(canvas=[H, W], renderable_px=int(RL.sum()), E_org_px=int(len(er)), E_mapped_renderable=int(okE.sum()),
                              E_ink=int(ink[er[okE], ec[okE]].sum()), n_crops=len(crops), crops=crops)
    print(k, {kk: v for kk, v in out["segments"][k].items() if kk != "crops"}, [c for c in crops if c["core_E_px"]], flush=True)
json.dump(out, open("/home/user/dominion/logs/sib/reg0841/chainvalid/area_lev.json", "w"), indent=1)
