"""Evidence sheet: a zoomed window where strokes are resolvable, each score map with the verified-text outline over it."""
import sys, os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation, uniform_filter

d, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
tags = [t for t in sys.argv[4:]]
lab = np.load(os.path.join(d, "label.npy"))
mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
W = 4200                                                      # 10 mm at 2.4 um: several letters
dens = uniform_filter((lab & mask).astype(np.float32), 801)    # pick the densest well-covered text patch
cov = uniform_filter(mask.astype(np.float32), 801)
h = W // 2
h0 = W // 2
thr = 0.5 * float(cov[h0:-h0, h0:-h0].max())            # adaptive: segment 2 is a far finer lace (mask ~33 %)
dens = np.where(cov > thr, dens, 0); dens[:h, :] = 0; dens[-h:, :] = 0; dens[:, :h] = 0; dens[:, -h:] = 0
cy, cx = np.unravel_index(np.argmax(dens), dens.shape)
sl = (slice(cy - W // 2, cy + W // 2), slice(cx - W // 2, cx + W // 2))
l = lab[sl]; m = mask[sl]
edge = binary_dilation(l, iterations=2) & ~l                   # stroke outline

avail = [("label", None)] + [(t, None) for t in tags if os.path.exists(os.path.join(d, f"s_bot_{t}.npy"))]
if os.path.exists(os.path.join(d, "s_top_team.npy")): avail.append(("team", None))
cols = min(4, len(avail)); rows = (len(avail) + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(5.2 * cols, 5.4 * rows)); axs = np.array(axs).ravel()
for ax, (t, _) in zip(axs, avail):
    ax.set_xticks([]); ax.set_yticks([])
    if t == "label":
        ax.imshow(np.where(m, l.astype(float), 0.5), cmap="gray", vmin=0, vmax=1); ax.set_title("verified text (GP label)")
    else:
        f = "s_top_team.npy" if t == "team" else f"s_bot_{t}.npy"
        x = np.load(os.path.join(d, f)).astype(np.float32)[sl]
        v = x[m]
        lo, hi = (np.percentile(v, 2), np.percentile(v, 98)) if v.size else (0, 1)
        ax.imshow(np.where(m, x, np.nan), cmap="magma" if t == "team" else "RdBu_r", vmin=lo, vmax=hi)
        ov = np.zeros(l.shape + (4,)); ov[edge] = (0, 1, 0, 0.9); ax.imshow(ov)
        j = os.path.join(d, f"judge_{t}.json")
        a = json.load(open(j))["bot"]["auc_px"] if os.path.exists(j) else None
        ax.set_title(f"{t}" + (f"  (pixel AUC {a:.3f})" if a else "") + "\ngreen = verified stroke outline")
    bar = 2000 / 2.4; ax.plot([60, 60 + bar], [W - 120] * 2, "w-", lw=3); ax.text(60, W - 180, "2 mm", color="w", fontsize=11)
for ax in axs[len(avail):]: ax.axis("off")
fig.suptitle(f"{title} — densest text window, {W*2.4/1000:.1f} mm across", fontsize=15, y=1.002)
fig.tight_layout(); fig.savefig(out, dpi=85); print(out, "window at", cy, cx)
