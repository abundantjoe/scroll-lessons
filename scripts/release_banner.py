"""README banner (docs/figures/banner.png): real data only, every number read from the committed results.

  release_banner.py            (needs the evaluation crop 20231005123336/held2 on disk: data/s1/.../derived/held2)

Background: the ensemble E's score map on held-out evaluation crop 20231005123336/held2, a 15 mm x 4.6 mm strip through one line of
text that papyrologists have already read; outlines: the Grand-Prize hand labels of that text (registered as for judging). Nothing is
drawn by hand and no letter is added; the caption says that this is read text, not new text.
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

sys.path.insert(0, ".")
from inkeval import trunc  # noqa: E402

SEG, CROP = "20231005123336", "held2"
D = f"data/s1/{SEG}/derived/{CROP}"
Y0, Y1 = 1950, 3850                       # canvas rows of the crop: one full line of read text (label density peaks at 2050-3750)
DS = 4                                    # display downsampling (2.4 um -> 9.6 um per display pixel)
OUT = "docs/figures/banner.png"
BG, INK, MUTED, LINE = "#0a0c11", "#f4f1ea", "#9aa0ab", "#62e6ff"
T = lambda x: f"{trunc(x, 3):.3f}"

ev = json.load(open("results/stats_evaluation7.json")); c1 = json.load(open("results/stats_confirmation.json"))
tk = json.load(open("results/toolkit_vs_records.json"))
e_ev, e_c1 = ev["summary"]["e"], c1["summary"]["e"]
crop_auc = [r["pixel"] for r in ev["per_crop"]["e"] if r["crop"] == f"{SEG}:{CROP}"][0]

e = np.load(f"{D}/s_bot_e.npy").astype(np.float32)[Y0:Y1:DS, ::DS]
m = ((np.load(f"{D}/mask_top.npy") > 0) & (np.load(f"{D}/mask_bot.npy") > 0))[Y0:Y1:DS, ::DS]
lab = np.load(f"{D}/label.npy")[Y0:Y1:DS, ::DS].astype(np.float32)

v = e[m]; lo, hi = np.percentile(v, 3), np.percentile(v, 99.7)
heat = np.clip((e - lo) / (hi - lo), 0, 1)
heat = np.where(m, heat, np.nan)          # outside the judge mask: background, never filled in
cmap = LinearSegmentedColormap.from_list("ink", ["#0a0c11", "#1d1235", "#4b1a5e", "#8f2a5c", "#d9534f", "#f6a04d", "#fde7a9"])
cmap.set_bad(BG)

H, W = heat.shape
FOOT = 0.075                                                                  # dark footer band for the caption (fraction of height)
fig = plt.figure(figsize=(18, 18 * H / W / (1 - FOOT)), dpi=110, facecolor=BG)
ax = fig.add_axes([0, FOOT, 1, 1 - FOOT]); ax.set_axis_off(); ax.set_facecolor(BG)
ax.imshow(heat, cmap=cmap, vmin=0, vmax=1, interpolation="bilinear", aspect="auto")
ax.contour(gaussian_filter(lab, 1.0), levels=[0.5], colors=[LINE], linewidths=1.1, alpha=0.85)

# title panel: opaque on the left third, then a smooth fade into the data
x = np.arange(W) / W
alpha = np.clip((0.50 - x) / (0.50 - 0.30), 0, 1) ** 1.3 * 0.94
grad = np.zeros((H, W, 4)); grad[..., :3] = matplotlib.colors.to_rgb(BG); grad[..., 3] = alpha[None, :]
ax.imshow(grad, aspect="auto", extent=(-0.5, W - 0.5, H - 0.5, -0.5), zorder=3)   # above the outlines (contours draw at zorder 2)
ax.set_xlim(-0.5, W - 0.5); ax.set_ylim(H - 0.5, -0.5)

bar = 5000 / 2.4 / DS                                                         # 5 mm in display pixels
ax.plot([W - 24 - bar, W - 24], [34, 34], color=INK, lw=2.2, solid_capstyle="butt", zorder=4)
ax.text(W - 24, 26, "5 mm", color=INK, fontsize=10, ha="right", va="bottom", zorder=4)

fig.text(0.035, 0.66, "inkeval", color=INK, fontsize=64, fontweight="bold", va="bottom")
fig.text(0.037, 0.585, "honest evaluation of ink detection in Herculaneum scroll CT", color=INK, fontsize=16.5, va="bottom")
chips = [f"ensemble E: pixel AUC {T(e_ev['pixel']['mean'])} on 7 held-out crops",
         f"{T(e_c1['pixel']['mean'])} on 6 untouched crops, pre-registered",
         f"{tk['comparisons'] - tk['failures']}/{tk['comparisons']} published records reproduced exactly"]
y = 0.465
for s_ in chips:
    fig.text(0.037, y, s_, color=INK, fontsize=13, va="center",
             bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.8", facecolor="#ffffff12", edgecolor="#ffffff42", linewidth=0.8))
    y -= 0.11
fig.text(0.985, FOOT / 2, f"Scroll 1 (PHerc. Paris. 4), held-out crop {SEG}/{CROP}: ensemble E's ink score (heat; pixel AUC "
         f"{T(crop_auc)} on this crop) and the papyrologists' verified letters (outline). Read text, not new text. "
         "Dark speckle: outside the judge mask. Data CC BY-NC 4.0, Vesuvius Challenge.", color=MUTED, fontsize=8.6, ha="right", va="center")
fig.savefig(OUT, dpi=110, facecolor=BG)

from PIL import Image                                                         # 256-colour palette: same look, a fraction of the bytes
Image.open(OUT).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(OUT, optimize=True)
print("written", OUT, f"{W}x{H} display px; E pixel AUC on this crop {crop_auc!r}; {os.path.getsize(OUT)} bytes")
