# Provenance: Project HERCULES | owner the owner | [id removed]
"""CHAIN VALID prep: exact evaluation area and render/inference crop list (numbers only).
Pixel (row, col) of the 2.4 um canvas is renderable iff its 4 surrounding mapped-mesh nodes are kept
(g = (c + 0.5)/20). Crops: 2048 x 2048 px, grid step 1792 (128 px context margin on every side); a crop is
listed iff its inner 1792 x 1792 core holds >= 1 renderable px. Counts: renderable px, organizer-map px,
supervision px and ink px inside the renderable area. Writes logs/sib/reg0841/chainvalid/area.json."""
import json, sys
import numpy as np, tifffile, zarr
REPO = "/home/user/dominion"
SEG = {"w00": "20260220213127-w00", "214732": "20260220214732-auto_grown_20260220144552896", "022814": "20260221022814-auto_grown_20260220174252405"}
out = {"crop": 2048, "step": 1792, "margin": 128, "segments": {}}
for k, s in SEG.items():
    X = tifffile.imread(f"/work/cv/mesh/{k}/x.tif"); V = X != -1
    H, W = V.shape[0] * 20, V.shape[1] * 20
    Wv = V[:-1, :-1] & V[1:, :-1] & V[:-1, 1:] & V[1:, 1:]
    gr = np.floor((np.arange(H) + 0.5) / 20).astype(int); gc = np.floor((np.arange(W) + 0.5) / 20).astype(int)
    okr = gr < Wv.shape[0]; okc = gc < Wv.shape[1]
    R = np.zeros((H, W), bool); R[np.ix_(okr, okc)] = Wv[np.ix_(gr[okr], gc[okc])]
    ink = zarr.open_array(f"/work/cv/org/{s}/inklabels.zarr/0", mode="r")[:] > 0
    sup = zarr.open_array(f"/work/cv/org/{s}/supervision.zarr/0", mode="r")[:] > 0
    org = tifffile.imread(f"/work/cv/org/{s}/inkmap.tif")
    assert org.shape == ink.shape == R.shape, (org.shape, ink.shape, R.shape)
    E = R & sup
    crops = []
    for y in range(-128, H, 1792):
        for x in range(-128, W, 1792):
            core = R[max(y + 128, 0):max(y + 1920, 0), max(x + 128, 0):max(x + 1920, 0)]
            n = int(core.sum())
            if n:
                crops.append(dict(y=y, x=x, core_px=n, core_sup_px=int(E[max(y + 128, 0):y + 1920, max(x + 128, 0):x + 1920].sum())))
    np.save(f"/work/cv/area_{k}.npy", R)
    px = (2.403e-4) ** 2
    out["segments"][k] = dict(segment=s, canvas=[H, W], renderable_px=int(R.sum()), renderable_cm2=float(R.sum() * px),
                              org_map_nonzero_in_R=int((org[R] > 0).sum()), sup_in_R=int(E.sum()), ink_in_R=int((E & ink).sum()),
                              blank_in_R=int((E & ~ink).sum()), sup_in_R_cm2=float(E.sum() * px), n_crops=len(crops), crops=crops,
                              renderable_sha256=__import__("hashlib").sha256(np.packbits(R).tobytes()).hexdigest())
    print(k, {kk: v for kk, v in out["segments"][k].items() if kk != "crops"}, flush=True)
json.dump(out, open(f"{REPO}/logs/sib/reg0841/chainvalid/area.json", "w"), indent=1)
