#!/usr/bin/env python
"""make_figures.py -- build the README figures from committed inputs only (no network, no data root).

  docs/figures/fig1_known_text_read.png   the quick-start contact sheet: CT | forward | reverse | per-unit margin, on
                                          the committed w040 known-text window (runs read_chart.py; maps as stored)
  docs/figures/fig2_flag_rates.png        flagged-unit rate with exact 95 % intervals: known text on a training-set
                                          sheet and on a held-out scroll vs the eligible-scroll populations
                                          (from records/release/release_stats.json)
  docs/figures/fig3_truncated_map.png     what a one-quadrant reverse map does to the margins if it is not refused
Maps are shown exactly as stored (uint8 = p x 255, grey, no contrast change). Nothing is enhanced.
usage: make_figures.py [--out docs/figures]
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
import numpy as np, tifffile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "examples"))
import rule55  # noqa: E402
import extract_w040_window as X  # noqa: E402

UM = 9.362


def fig1(out, tmp):
    X.main([tmp, "--truncate"])
    rd = os.path.join(tmp, "read")
    subprocess.run([sys.executable, os.path.join(HERE, "read_chart.py"), os.path.join(tmp, "ct_mid.tif"),
                    os.path.join(tmp, "forward.tif"), os.path.join(tmp, "reverse.tif"), "--maps-only", "--um", str(UM),
                    "--out", rd, "--key", "PHerc0139|w040_window|0|ink9um_seed42+plain|both",
                    "--ledger", os.path.join(tmp, "LEDGER.md"), "--max-panel-px", "800"], check=True, stdout=subprocess.DEVNULL)
    shutil.copy(os.path.join(rd, "contact_sheet.png"), os.path.join(out, "fig1_known_text_read.png"))


def fig2(out):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    s = json.load(open(os.path.join(ROOT, "records", "release", "release_stats.json")))
    rows = [("known text, TRAINING-SET sheet\n(w040, PHerc0139; R-CTRL55)", s["control"]),
            ("known text, HELD-OUT scroll\n(PHerc0841, 3 segments; R-HELDOUT)", s["heldout_reference"])]
    names = {"R-DEFICIT": "eligible corpus, screening reads\n(30 surfaces, R-DEFICIT)",
             "R-CREST-POWER phase 1, 11 of 12": "PHerc1203 + PHerc1447 team surfaces\n(11 surfaces, 150.67 cm², R-CREST-POWER)"}
    rows += [(names[c["name"]], c) for c in s["comparisons"] if c["name"] in names]
    fig, ax = plt.subplots(figsize=(8.8, 3.6), dpi=150)
    for i, (lab, r) in enumerate(rows):
        y = len(rows) - 1 - i
        lo, hi = r["cp95"]
        ax.plot([lo * 100, hi * 100], [y, y], color="black", lw=2)
        ax.plot([r["rate"] * 100], [y], "o", color=("#c0392b", "#d68910")[i] if i < 2 else "#2c3e50", ms=8)
        ax.text(hi * 100 + 0.6, y, "%d / %d flagged" % (r["k"], r["n"]), va="center", fontsize=9)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8.5)
    ax.set_xlim(-0.5, 26); ax.set_xlabel("flagged 0.5 cm² units, % of valid units (dot = observed; bar = exact 95 % CI)")
    ax.set_title("Frozen rule 5.5 flag rate: the eligible scrolls' rates are not significantly below the held-out known-text rate\n(exploratory one-sided Fisher tests, computed after the result: p ≥ 0.24)", fontsize=9)
    ax.grid(axis="x", alpha=0.3); fig.tight_layout()
    fig.savefig(os.path.join(out, "fig2_flag_rates.png")); plt.close(fig)


def fig3(out, tmp):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    f = tifffile.imread(os.path.join(tmp, "forward.tif")); r = tifffile.imread(os.path.join(tmp, "reverse.tif"))
    t = tifffile.imread(os.path.join(tmp, "reverse_truncated.tif")); m = tifffile.imread(os.path.join(tmp, "ct_mid.tif")) > 0
    true_u = rule55.evaluate(f, r, m, UM, unit_origin="auto")[0]["units"]["0.5cm2"]["valid_units"]
    bad_u = rule55.evaluate(f, t, m, UM, unit_origin="auto")[0]["units"]["0.5cm2"]["valid_units"]
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), dpi=130, gridspec_kw=dict(width_ratios=[1, 1, 1.25]))
    for ax, img, title in ((axs[0], r, "reverse map as written (complete)"), (axs[1], t, "reverse map, one quadrant written")):
        ax.imshow(img, cmap="gray", vmin=0, vmax=255, interpolation="nearest"); ax.set_title(title, fontsize=9); ax.axis("off")
    x = np.arange(len(true_u)); w = 0.38
    axs[2].bar(x - w / 2, [u["margin"] for u in true_u], w, label="complete maps (true)", color="#2c3e50")
    axs[2].bar(x + w / 2, [u["margin"] for u in bad_u], w, label="truncated reverse (not refused)", color="#c0392b")
    axs[2].axhline(rule55.MARGIN_MIN, color="gray", ls="--", lw=1)
    axs[2].text(len(true_u) - 0.5, rule55.MARGIN_MIN + 0.005, "flag bar %+.2f" % rule55.MARGIN_MIN, ha="right", fontsize=8, color="gray")
    axs[2].set_xticks(x); axs[2].set_xticklabels(["unit (%d,%d)" % (u["row"], u["col"]) for u in true_u], fontsize=8)
    axs[2].set_ylabel("forward − reverse margin"); axs[2].legend(fontsize=8, loc="upper left")
    axs[2].set_title("same forward map, same pixels", fontsize=9)
    fig.suptitle("A truncated reverse map inflates every margin it touches; read_chart.py and map_integrity.py refuse it", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(out, "fig3_truncated_map.png")); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "figures"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        fig1(a.out, tmp); fig2(a.out); fig3(a.out, tmp)
    for n in sorted(os.listdir(a.out)):
        print("wrote", os.path.join(a.out, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
