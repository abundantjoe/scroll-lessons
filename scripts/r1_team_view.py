"""R1 corroboration (RULES.md): render the team model's published prediction on the identical R1 windows.

The team map is an INDEPENDENT second opinion, not ground truth, and is used for nothing but this side-by-side view.
  r1_team_view.py <seg> <window-name> <out.png> [tag]      (tag defaults to v8; the release figure uses e)
"""
import sys, os, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from scipy.ndimage import zoom
Image.MAX_IMAGE_PIXELS = None

seg, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
tag = sys.argv[4] if len(sys.argv) > 4 else "v8"
d = f"data/s1/{seg}/derived/{name}"
c = [x for x in json.load(open(f"data/s1/{seg}/unread.json"))["crops"] if x["name"] == name][0]
y0, x0, side = c["y0"], c["x0"], c["side"]

ink = np.asarray(Image.open(f"data/s1/{seg}/overview/ink_ds8.jpg").convert("L")).astype(np.float32) / 255.0
sub = ink[y0 // 8:(y0 + side) // 8 + 1, x0 // 8:(x0 + side) // 8 + 1]
team = zoom(sub, 8, order=1)[:side, :side]

sc = np.load(os.path.join(d, f"s_bot_{tag}.npy")).astype(np.float32)
mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
ds = max(1, side // 1600)
sc, m, team = sc[::ds, ::ds], mask[::ds, ::ds], team[::ds, ::ds]
v = sc[m]
lo, hi = (np.percentile(v, 1), np.percentile(v, 99)) if v.size else (0, 1)
ours = np.where(m, 1.0 - np.clip((sc - lo) / max(hi - lo, 1e-6), 0, 1), np.nan)

fig, axs = plt.subplots(1, 2, figsize=(19, 9.8))
NAME = {"e": "E (ensemble of v8 and GP-R1)"}.get(tag, tag)
for ax, (t, im) in zip(axs, [(f"ours: {NAME}", ours), ("independent: team 2.4 um model (not ground truth)", 1.0 - team)]):
    ax.imshow(im, cmap="gray", vmin=0, vmax=1, interpolation="bilinear")
    ax.set_title(t, fontsize=13); ax.set_xticks([]); ax.set_yticks([])
    bar = 5000 / 2.4 / ds
    ax.plot([40, 40 + bar], [im.shape[0] - 60] * 2, "k-", lw=3)
    ax.text(40, im.shape[0] - 90, "5 mm", fontsize=11, bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
fig.suptitle(f"R1 {seg} {name} ({c['dist_to_label_mm']} mm from the nearest read text) - UNREAD papyrus", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(out, dpi=105, facecolor="white")
print(out, "team map: mean %.3f  p99 %.3f  frac>0.5 %.4f" % (team.mean(), np.percentile(team, 99), (team > 0.5).mean()))
