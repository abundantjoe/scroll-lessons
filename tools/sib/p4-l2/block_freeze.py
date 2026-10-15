"""DECL-P4-17 item 2: freeze T_d and the cell rule on the CONTROL strip; validate on held-out control cells.

Provenance: Project HERCULES | owner the owner | [id removed]
Rules (fixed in this code before its first run):
- cell (5 x 5 mm, 16 per tile) used iff n_valid >= 0.5 n_px and n_pos (valid & max > 0) >= 0.5 n_px;
- statistic f_T(cell) = fraction of the cell's n_pos px with slab max > T;
- split by TILE: numpy default_rng(20260928).permutation within each class; the first half (ceil) = train, rest = held-out;
- for each T in 140..254: F(T) = inverted-CDF 0.95 quantile of f_T over TRAIN intercolumn cells; a cell is flagged iff
  f_T > F(T); T_d = argmax of train text recall (ties -> lowest T);
- validation (held-out): text recall >= 0.90 AND intercolumn FPR <= 0.05 -> PASS, else FAIL;
- title-zone rule (applied later, only after the orchestrator's METRIC-HASH): flagged iff f_Td > P99, P99 = inverted-CDF
  0.99 quantile of f_Td over ALL control intercolumn cells; a block candidate is a 4-connected cluster of >= 4 flagged
  cells on the strip-wide cell lattice.
Usage: block_freeze.py <ctl_cells_jsonl...> --out <json>
"""
import argparse
import json
import math

import numpy as np

SEED = 20260928
TS = range(140, 255)


def qinv(v, q):
    v = np.sort(np.asarray(v))
    return float(v[max(0, math.ceil(q * len(v)) - 1)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tiles = {}
    for p in a.inputs:
        for l in open(p):
            x = json.loads(l)
            tiles[(x["r"], x["c"])] = x
    rng = np.random.default_rng(SEED)
    split = {}
    for cls in ("text", "intercol"):
        ks = sorted(k for k, x in tiles.items() if x["class"] == cls)
        perm = rng.permutation(len(ks))
        ntr = math.ceil(len(ks) / 2)
        for n, i in enumerate(perm):
            split[ks[i]] = "train" if n < ntr else "held"
    cells = []  # (cls, split, cum-above array)
    for k, x in sorted(tiles.items()):
        for c in x["cells"]:
            if c["n_valid"] >= 0.5 * c["n_px"] and c["n_pos"] >= 0.5 * c["n_px"]:
                h = np.array(c["hist"], np.int64)
                above = h[::-1].cumsum()[::-1]  # above[t] = count >= t
                frac = np.array([above[t + 1] / c["n_pos"] for t in range(255)])  # frac > t
                cells.append((x["class"], split[k], frac))
    sel = lambda cls, sp: np.array([f for c, s, f in cells if c == cls and (sp is None or s == sp)])  # noqa: E731
    trt, tri, hot, hoi, ali = sel("text", "train"), sel("intercol", "train"), sel("text", "held"), \
        sel("intercol", "held"), sel("intercol", None)
    best = None
    curve = []
    for t in TS:
        F = qinv(tri[:, t], 0.95)
        rec = float((trt[:, t] > F).mean())
        curve.append({"T": t, "F": F, "train_recall": rec, "train_fpr": float((tri[:, t] > F).mean())})
        if best is None or rec > best[1]:
            best = (t, rec, F)
    td, trec, F = best
    hrec = float((hot[:, td] > F).mean())
    hfpr = float((hoi[:, td] > F).mean())
    p99 = qinv(ali[:, td], 0.99)
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "declaration": "RULES.md DECL-P4-17 item 2 (depth: L2S slab 48..60, +-14.4 um about the mesh)",
           "n_tiles": {"text": int(sum(x["class"] == "text" for x in tiles.values())),
                       "intercol": int(sum(x["class"] == "intercol" for x in tiles.values()))},
           "n_cells": {"train_text": len(trt), "train_intercol": len(tri), "held_text": len(hot),
                       "held_intercol": len(hoi)},
           "T_d": td, "F_cell_fraction": F, "train_recall": trec,
           "held_out_recall": hrec, "held_out_fpr": hfpr,
           "bar": "held-out recall >= 0.90 and FPR <= 0.05",
           "verdict": "PASS" if (hrec >= 0.90 and hfpr <= 0.05) else "FAIL",
           "title_zone_P99_intercol": p99,
           "split": {f"{k[0]},{k[1]}": v for k, v in sorted(split.items())}, "curve": curve}
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("n_tiles", "n_cells", "T_d", "F_cell_fraction", "train_recall",
                                          "held_out_recall", "held_out_fpr", "verdict", "title_zone_P99_intercol")}))


if __name__ == "__main__":
    main()
