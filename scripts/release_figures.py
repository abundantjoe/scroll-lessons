"""Release figures (docs/figures/). Every number drawn is read from a committed results file; nothing is typed in.

  release_figures.py            -> fig1_headline.png, fig4_null.png, fig5_training.png
  release_figures.py --reading  -> fig2_reading_median_worst.png, fig3_unread_e_vs_team.png, figS_all_crops.png (needs data/ on disk)

Palette: validated categorical slots (blue, orange, aqua; all-pairs CVD-safe), recessive ink, light surface.
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, ".")
from inkeval import trunc  # noqa: E402

OUT = "docs/figures"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#9a9993"
NAMES = {"e": "E  ensemble (v8 + GP-R1)", "v8": "v8  2-D U-Net, 15 crops", "gpr1": "GP-R1  Grand-Prize-style 3-D->2-D",
         "v6b": "v6b  U-Net, 8 crops, team-vetoed", "v6c": "v6c  U-Net, 8 crops", "v7": "v7  best hand-built physics",
         "v2": "v2  band-passed depth template", "v0.1b": "v0.1b  papyrus subtraction", "team": "team 2.4 um model (positive control)"}
GROUP = {"e": BLUE, "v8": BLUE, "gpr1": BLUE, "v6b": BLUE, "v6c": BLUE, "v7": ORANGE, "v2": ORANGE, "v0.1b": ORANGE, "team": AQUA}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "savefig.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})


def fig1():
    ev = json.load(open("results/stats_evaluation7.json"))
    c1 = json.load(open("results/stats_confirmation.json")) if os.path.exists("results/stats_confirmation.json") else None
    order = ["team", "e", "v8", "gpr1", "v6b", "v6c", "v7", "v2", "v0.1b"]
    order = [m for m in order if m in ev["summary"]]
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.2), sharey=True)
    for ax, k, bar, title in ((axs[0], "pixel", 0.80, "Pixel AUC"), (axs[1], "stroke", 0.90, "Stroke AUC (0.25 mm disks)")):
        ax.axvline(0.5, color=GRAY, lw=1, zorder=1)
        ax.text(0.505, -0.55, "chance 0.5", ha="left", va="center", color=INK2, fontsize=8.5)
        ax.axvline(bar, color=INK2, lw=1, ls=(0, (4, 3)), zorder=1)
        ax.text(bar + 0.004, -0.55, f"declared bar {bar:.2f}", color=INK2, fontsize=8.5, va="center")
        for i, m in enumerate(order):
            y = len(order) - 1 - i
            s = ev["summary"][m][k]
            if s and "mean" in s:
                lo, hi = s["ci95"]
                ax.plot([lo, hi], [y + 0.12, y + 0.12], color=GROUP[m], lw=2, solid_capstyle="round", zorder=2)
                ax.plot(s["mean"], y + 0.12, "o", ms=8, color=GROUP[m], mec=SURF, mew=1.5, zorder=3)
            if c1 and m in c1["summary"] and c1["summary"][m].get(k) and "mean" in c1["summary"][m][k]:
                s2 = c1["summary"][m][k]; lo, hi = s2["ci95"]
                ax.plot([lo, hi], [y - 0.16, y - 0.16], color=GROUP[m], lw=2, alpha=0.55, solid_capstyle="round", zorder=2)
                ax.plot(s2["mean"], y - 0.16, "D", ms=7, mfc=SURF, mec=GROUP[m], mew=2, zorder=3)
        ax.set_xlim(0.45, 1.0); ax.set_ylim(-0.9, len(order) - 0.1); ax.set_title(title, loc="left", color=INK, fontsize=11.5, pad=18)
        ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
        ax.set_xlabel("held-out mean, 95 % crop-level bootstrap CI")
    axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels([NAMES[m] for m in reversed(order)])
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=BLUE, marker="o", lw=2, label="learned, ours (v6b: team-vetoed negatives)"),
         Line2D([], [], color=ORANGE, marker="o", lw=2, label="hand-built physics, ours (v7: team-vetoed negatives)"),
         Line2D([], [], color=AQUA, marker="o", lw=2, label="team model - positive control"),
         Line2D([], [], color=INK2, marker="o", lw=0, label=f"filled: 7 evaluation crops")]
    if c1:
        h.append(Line2D([], [], color=INK2, marker="D", mfc=SURF, lw=0, label=f"hollow: {c1['effective_n']['crops']} untouched confirmation crops (C1)"))
    fig.legend(handles=h, loc="lower center", ncol=3 if not c1 else 3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Ink detection on held-out, papyrologically read text - Scroll 1 (PHerc. Paris. 4), 2 segments",
                 x=0.01, ha="left", fontsize=12.5, color=INK)
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(f"{OUT}/fig1_headline.png", dpi=150); plt.close(fig)


def fig4():
    ev = json.load(open("results/stats_evaluation7.json"))
    nulls = {t: v["values"] for t, v in ev["negative_control_label_swap"].items() if "values" in v}
    tags = ["e", "v8", "v7", "team"]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    rng = np.random.default_rng(0)
    for i, t in enumerate(tags):
        matched = [r["pixel"] for r in ev["per_crop"][t]]
        if nulls and t in nulls:
            v = np.array(nulls[t]); ax.scatter(i - 0.18 + rng.uniform(-0.07, 0.07, v.size), v, s=14, color=GRAY, alpha=0.7, lw=0, zorder=2)
        ax.scatter(i + 0.18 + rng.uniform(-0.04, 0.04, len(matched)), matched, s=40, color=GROUP[t], edgecolor=SURF, lw=1, zorder=3)
    ax.axhline(0.5, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.set_xticks(range(len(tags))); ax.set_xticklabels([NAMES[t].split("  ")[0] if "  " in NAMES[t] else "team" for t in tags])
    ax.set_ylabel("pixel AUC"); ax.set_ylim(0.2, 1.0); ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_title("Matched crops (colour) vs label-swap null: each crop scored against another crop's labels (grey, 42 pairs)",
                 loc="left", fontsize=10.5, color=INK)
    ax.text(len(tags) - 0.5, 0.23, "A single crop's AUC can reach ~0.7 from layout alone; only multi-crop means carry weight.",
            ha="right", fontsize=8.5, color=INK2)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig4_null.png", dpi=150); plt.close(fig)


def fig5():
    runs = [("v6c", "8 crops, BCE selection", ORANGE, "models/v6c_unet.pt.json"),
            ("v6b", "8 crops, team-vetoed negatives", AQUA, "models/v6b_unet.pt.json"),
            ("v8", "15 crops, AUC selection", BLUE, "models/v8_unet.pt.json")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.4))
    for tag, lab, col, p in runs:
        c = json.load(open(p))["val_curve"]
        st = np.array([r[0] for r in c]); v = np.array([r[2] for r in c])
        a1.plot(st, v, color=col, lw=2, label=f"{tag}  {lab}")
        if tag != "v8":
            i = int(np.argmin(v)); a1.plot(st[i], v[i], "o", ms=8, color=col, mec=SURF, mew=1.5, zorder=4)
            a1.annotate(f"{tag} chosen: step {int(st[i])}", (st[i], v[i]), xytext=(8, -12), textcoords="offset points", fontsize=8.5, color=INK2)
        else:
            a = np.array([r[3] if r[3] is not None else np.nan for r in c]); i = int(np.nanargmax(a))
            a2.plot(st, a, color=col, lw=2)
            a2.plot(st[i], a[i], "o", ms=8, color=col, mec=SURF, mew=1.5, zorder=4)
            a2.annotate(f"chosen: step {int(st[i])}, AUC {trunc(a[i], 4):.4f}", (st[i], a[i]), xytext=(-60, -28), textcoords="offset points", fontsize=8.5, color=INK2)
    a1.set_xlabel("training step"); a1.set_ylabel("validation BCE"); a1.legend(frameon=False, fontsize=8.5)
    a1.set_title("Validation loss: the 8-crop runs diverge within a few hundred steps;\nthe 15-crop run diverges more slowly", loc="left", fontsize=10.5, color=INK)
    a2.set_xlabel("training step"); a2.set_ylabel("validation pixel AUC (v8)")
    a2.set_title("v8 (15 crops): validation AUC plateaus by ~step 1500;\nthe chosen maximum sits inside the plateau's noise", loc="left", fontsize=10.5, color=INK)
    for ax in (a1, a2):
        ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    fig.text(0.01, 0.01, "Validation crop 20231012184424/held4 (a training segment, never an evaluation crop). v6b's validation labels "
             "carry the team-model veto, v6c's and v8's do not, so v6b's loss is not strictly comparable.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(f"{OUT}/fig5_training.png", dpi=150); plt.close(fig)


def reading():
    import subprocess
    from PIL import Image
    py = sys.executable
    def render(seg, crop, tag, out, title, label=True):
        args = [py, "scripts/render_reading.py", f"data/s1/{seg}/derived/{crop}", tag, out, title] + (["--label"] if label else [])
        subprocess.run(args, check=True)
    tmp = "/tmp/release_fig"; os.makedirs(tmp, exist_ok=True)
    rows = sorted((x["pixel"], x["crop"]) for x in json.load(open("results/stats_evaluation7.json"))["per_crop"]["e"])
    (med, cm), (low, cw) = rows[len(rows) // 2], rows[0]                       # 7 crops: the 4th value is the median
    tr = lambda x: f"{trunc(x, 3):.3f}"                                          # truncated, never rounded up
    render(*cm.split(":"), "e", f"{tmp}/a.png", f"median crop by E pixel AUC ({tr(med)}): seg {cm.replace(':', ' ')}")
    render(*cw.split(":"), "e", f"{tmp}/b.png", f"worst crop by E pixel AUC ({tr(low)}): seg {cw.replace(':', ' ')}")
    a, b = Image.open(f"{tmp}/a.png"), Image.open(f"{tmp}/b.png")
    w = max(a.width, b.width); canvas = Image.new("RGB", (w, a.height + b.height), (252, 252, 251))
    canvas.paste(a, (0, 0)); canvas.paste(b, (0, a.height))
    canvas.save(f"{OUT}/fig2_reading_median_worst.png", optimize=True)
    subprocess.run([py, "scripts/r1_team_view.py", "20231005123336", "unread1", f"{OUT}/fig3_unread_e_vs_team.png", "e"], check=True)
    contact_sheet()


def contact_sheet():
    """Every evaluation and confirmation crop: E's output beside the verified text, so no crop is hidden."""
    import json as _j
    sets = [("evaluation", [("20231005123336", c) for c in ("held1", "held2", "held3")] + [("20231210121321", c) for c in ("held1", "held2", "held3", "held4")])]
    conf = []
    for seg in ("20231005123336", "20231210121321"):
        p = f"data/s1/{seg}/confirm.json"
        if os.path.exists(p): conf += [(seg, c["name"]) for c in _j.load(open(p))["crops"]]
    if conf: sets.append(("confirmation C1", conf))
    rows = sum(len(v) for _, v in sets)
    fig, axs = plt.subplots(rows, 2, figsize=(7.2, 3.5 * rows))
    i = 0
    for set_name, crops in sets:
        for seg, crop in crops:
            d = f"data/s1/{seg}/derived/{crop}"
            m = (np.load(f"{d}/mask_top.npy") > 0) & (np.load(f"{d}/mask_bot.npy") > 0)
            e = np.load(f"{d}/s_bot_e.npy").astype(np.float32)[::8, ::8]; mm = m[::8, ::8]; lab = np.load(f"{d}/label.npy")[::8, ::8]
            v = e[mm]; lo, hi = np.percentile(v, 1), np.percentile(v, 99)
            img = np.where(mm, 1 - np.clip((e - lo) / max(hi - lo, 1e-6), 0, 1), np.nan)
            a = json.load(open(f"{d}/judge_e.json"))["bot"]["auc_px"]
            axs[i, 0].imshow(img, cmap="gray", vmin=0, vmax=1); axs[i, 1].imshow(np.where(mm, lab, np.nan), cmap="gray_r", vmin=0, vmax=1)
            axs[i, 0].set_title(f"{set_name}: {seg} {crop} - E pixel AUC {trunc(a, 3):.3f}", loc="left", fontsize=8, color=INK)
            axs[i, 1].set_title("verified text", loc="left", fontsize=8, color=INK2)
            for ax in axs[i]: ax.set_xticks([]); ax.set_yticks([])
            i += 1
    fig.tight_layout(); fig.savefig(f"{OUT}/figS_all_crops.png", dpi=90); plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "--reading" in sys.argv:
        reading()
    else:
        fig1(); fig4(); fig5()
    print("figures written to", OUT)
