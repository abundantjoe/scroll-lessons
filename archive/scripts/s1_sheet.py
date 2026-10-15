"""Scroll-1 review sheet: CT mid, S_top, label, and the score maps for the given tags, plus the team comparator."""
import sys, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, pitch, out, title = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]; tags = sys.argv[5:]
ds = 4
def L(n):
    p = os.path.join(d, n); return np.asarray(np.load(p, mmap_mode="r")[::ds, ::ds]).astype(np.float32) if os.path.exists(p) else None
panels = [("ct_mid.npy", "CT mid slice", "gray", None), ("S_bot.npy", "S_bot (writing face)", "gray", None), ("label.npy", "GP label (verified text)", "gray", (0, 1))]
for t in tags: panels.append((f"s_bot_{t}.npy", f"s_bot {t}", "RdBu_r", (-3, 3)))
panels.append(("s_top_team.npy", "team 2.4 µm model (ds8)", "magma", (0, 1)))
n = len(panels); cols = 3; rows = (n + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows)); axs = np.array(axs).ravel()
for ax, (f, t, cm, cl) in zip(axs, panels):
    x = L(f); ax.set_title(t); ax.set_xticks([]); ax.set_yticks([])
    if x is None: continue
    if cl is None: cl = (np.percentile(x[x > 0], 1) if (x > 0).any() else 0, np.percentile(x[x > 0], 99) if (x > 0).any() else 1)
    ax.imshow(x, cmap=cm, vmin=cl[0], vmax=cl[1]); bar = 5000 / pitch / ds; ax.plot([20, 20 + bar], [x.shape[0] - 30] * 2, "w-", lw=3); ax.text(20, x.shape[0] - 45, "5 mm", color="w")
for ax in axs[n:]: ax.axis("off")
fig.suptitle(title); fig.tight_layout(); fig.savefig(out, dpi=80); print(out)
