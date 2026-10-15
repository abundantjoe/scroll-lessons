#!/usr/bin/env python3
"""Contact sheet per chart: raw face render S | relief | s_top | s_bot | reference | mask. 1 cm bar on every panel. Script-generated only.
usage: contact_sheet.py <derived_dir> <pitch> <tag> <out.png> [--ref ref_crop.npy] [--ds 8]"""
import sys, os, argparse, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ap = argparse.ArgumentParser(); ap.add_argument("d"); ap.add_argument("pitch", type=float); ap.add_argument("tag"); ap.add_argument("out")
ap.add_argument("--ref", default=None); ap.add_argument("--ds", type=int, default=8); ap.add_argument("--title", default="")
a = ap.parse_args(); d = a.d; ds = a.ds
def ld(n): x = np.load(os.path.join(d, n), mmap_mode="r"); return np.asarray(x[::ds, ::ds]).astype(np.float32)
S = ld("S_top.npy"); Sb = ld("S_bot.npy"); r = ld("relief_top.npy"); st = ld(f"s_top_{a.tag}.npy"); sb = ld(f"s_bot_{a.tag}.npy"); m = ld("mask_top.npy"); ct = ld("ct_mid.npy")
panels = [(ct, "CT mid slice", "gray", (0, 255)), (S, "S_top (face intensity)", "gray", (np.percentile(S, 1), np.percentile(S, 99))),
          (r, "relief r_top (µm, proud +)", "RdBu_r", (-15, 15)), (st, f"s_top {a.tag}", "RdBu_r", (-2, 2)), (sb, f"s_bot {a.tag}", "RdBu_r", (-2, 2))]
if a.ref: ref = np.load(a.ref)[::ds, ::ds]; panels.append((ref, "reference (team 2.4 µm model)", "magma", (0, 255)))
else: panels.append((m.astype(float), "mask_top", "gray", (0, 1)))
fig, ax = plt.subplots(2, 3, figsize=(18, 12)); bar = 10000 / (a.pitch * ds)
for axx, (img, title, cmap, (lo, hi)) in zip(ax.ravel(), panels):
    axx.imshow(img, cmap=cmap, vmin=lo, vmax=hi); axx.set_title(title, fontsize=10); axx.set_xticks([]); axx.set_yticks([])
    axx.plot([10, 10 + bar], [img.shape[0] - 15] * 2, "k-", lw=5); axx.plot([10, 10 + bar], [img.shape[0] - 15] * 2, "w-", lw=3); axx.text(10, img.shape[0] - 25, "1 cm", color="w", fontsize=9, bbox=dict(facecolor="k", alpha=0.5, pad=1))
fig.suptitle(a.title or d); plt.tight_layout(); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); plt.savefig(a.out, dpi=100)
