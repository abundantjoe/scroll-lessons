"""Render a detector's score map as a reading image: white papyrus, dark ink, at a scale where letters are legible.

  render_reading.py <crop_dir> <tag> <out.png> <title> [--label] [--window y x size]

--label adds the verified-text panel beside it (only meaningful where labels exist).
Without --window the whole crop is rendered, downsampled to keep the file manageable.
"""
import sys, os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d, tag, out, title = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
want_label = "--label" in sys.argv
win = None
if "--window" in sys.argv:
    i = sys.argv.index("--window"); win = tuple(int(v) for v in sys.argv[i + 1:i + 4])

sc = np.load(os.path.join(d, f"s_bot_{tag}.npy")).astype(np.float32)
mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
lab = None
if want_label and os.path.exists(os.path.join(d, "label.npy")):
    lab = np.load(os.path.join(d, "label.npy"))

if win:
    y, x, s = win; sl = (slice(y, y + s), slice(x, x + s)); ds = max(1, s // 1600)
else:
    sl = (slice(None), slice(None)); ds = max(1, sc.shape[0] // 1600)
sc = sc[sl][::ds, ::ds]; m = mask[sl][::ds, ::ds]
if lab is not None: lab = lab[sl][::ds, ::ds]

v = sc[m]
lo, hi = (np.percentile(v, 1), np.percentile(v, 99)) if v.size else (0, 1)
img = np.clip((sc - lo) / max(hi - lo, 1e-6), 0, 1)
img = np.where(m, 1.0 - img, np.nan)              # ink dark on light papyrus

panels = [("detector " + {"e": "E (ensemble of v8 and GP-R1)"}.get(tag, tag) + " - dark = ink; white = outside the judge mask", img, "gray")]
if lab is not None: panels.append(("verified text (where read)", np.where(m, lab.astype(float), np.nan), "gray_r"))
fig, axs = plt.subplots(1, len(panels), figsize=(9.5 * len(panels), 9.8))
axs = np.atleast_1d(axs)
for ax, (t, im, cm) in zip(axs, panels):
    ax.imshow(im, cmap=cm, vmin=0, vmax=1, interpolation="bilinear")
    ax.set_title(t, fontsize=13); ax.set_xticks([]); ax.set_yticks([])
    bar = 5000 / 2.4 / ds
    ax.plot([40, 40 + bar], [im.shape[0] - 60] * 2, "k-", lw=3)
    ax.text(40, im.shape[0] - 90, "5 mm", fontsize=11, bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
fig.suptitle(title, fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(out, dpi=110, facecolor="white")
print(out, "rendered", img.shape, "downsample", ds)
