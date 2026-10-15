#!/usr/bin/env python3
"""Overview figure for w028: CT mid slice at pyramid level 4 beside the team prediction,
with 1 cm bars, plus fill/histogram assertions on the level-4 stack. Nothing hand-edited."""
import zarr, numpy as np, tifffile, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, json, os
PITCH = 2.399  # µm, from the store's .zattrs coordinateTransformations (level 0)
L4 = 16
g = zarr.open("data/w028/stack.zarr", mode="r")["4"]
vol = g[:]                     # (109, 2339, 1897)
print("level4 shape", vol.shape, "dtype", vol.dtype)
mid = vol.shape[0] // 2
fill = (vol > 0).mean(); print("nonzero fraction", fill)
hist = np.bincount(vol[mid].ravel(), minlength=256)
print("mid slice: mean", vol[mid].mean(), "p1/p50/p99", np.percentile(vol[mid][vol[mid] > 0], [1, 50, 99]))
assert 0.2 < fill < 1.0, "fill assertion failed"
onsheet4 = (vol[mid] > 0)
np.save("data/w028/overview/onsheet_l4.npy", onsheet4)
tifffile.imwrite("data/w028/overview/ct_mid_l4.tif", vol[mid])
pred = np.load("data/w028/overview/pred_ds20.npy")
fig, ax = plt.subplots(1, 2, figsize=(16, 10))
ax[0].imshow(vol[mid], cmap="gray", vmin=0, vmax=255); ax[0].set_title(f"w028 CT mid slice (k={mid}), level 4 ({PITCH*L4:.1f} µm/px)")
bar = 10000 / (PITCH * L4); ax[0].plot([50, 50 + bar], [vol.shape[1] - 60] * 2, "w-", lw=4); ax[0].text(50, vol.shape[1] - 80, "1 cm", color="w")
ax[1].imshow(pred, cmap="magma", vmin=0, vmax=255); ax[1].set_title("team ink prediction (2.4 µm model), 20x block mean")
bar2 = 10000 / (PITCH * 20); ax[1].plot([50, 50 + bar2], [pred.shape[0] - 60] * 2, "w-", lw=4); ax[1].text(50, pred.shape[0] - 80, "1 cm", color="w")
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig("data/w028/overview/overview.png", dpi=110)
json.dump({"level4_shape": list(vol.shape), "nonzero_fraction": float(fill), "mid_slice": int(mid)}, open("data/w028/overview/overview.json", "w"), indent=1)
