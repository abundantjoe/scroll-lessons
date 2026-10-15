"""DECL-P4-18 item 3: numbers-only pre-gate of L4- and L4+ on the CONTROL strip. Writes PREGATE_L4.json.

Provenance: Project HERCULES | owner the owner | [id removed]
Per face:
- sensitivity: block_freeze.py rules verbatim (tile split seed 20260928, T 140..254, F = train intercol p95,
  T_d = argmax train recall, ties lowest; held-out recall >= 0.90 and FPR <= 0.05);
- specificity rot-90: the frozen (T_d, F) applied to the cells of the rot-90 copies of all control tiles (the 4 x 4 cell
  lattice rotates with the tile; the statistic is a per-cell pixel fraction), flagged <= 5 %;
- specificity synthetic: 100 synthetic no-ink sheets (512 x 512 px = one cell each, level-1 grid), voxel values drawn
  from the control's empirical per-class histograms (sheet interior; 0-8 slices outside either face; air beyond),
  estimated on 48 control chunks (seed 20260929) with the same face rule; sheet centre = 54 + smooth field (amplitude
  drawn from the control's s_minus/s_plus spread), thickness drawn from the control's s_plus - s_minus; L4 by the
  production code; flagged <= 5 %.
PASS per face iff all three hold.
Usage: pregate_l4.py <l4ctl_dir> <out_json>
"""
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402
import l4  # noqa: E402
import block_ctl  # noqa: E402

SPLIT_SEED, SYN_SEED, CH_SEED = 20260928, 20260930, 20260929
TS = range(140, 255)


def qinv(v, q):
    v = np.sort(np.asarray(v))
    return float(v[max(0, math.ceil(q * len(v)) - 1)])


def frac_gt(h, n):
    above = np.asarray(h, np.int64)[::-1].cumsum()[::-1]
    return np.array([above[t + 1] / n for t in range(255)])


def empirical_classes(tiles):
    """Per-class uint8 histograms from 48 control chunks (text tiles), with the production face rule."""
    rng = np.random.default_rng(CH_SEED)
    tx = [t for t in tiles.values() if t["class"] == "text"]
    hist = {k: np.zeros(256, np.int64) for k in ("interior", "near", "air")}
    th, amp = [], []
    for n in range(48):
        t = tx[rng.integers(len(tx))]
        y0, y1 = t["l1_rows"]
        x0, x1 = t["l1_cols"]
        cy, cx = rng.integers(y0 // 128, (y1 - 1) // 128 + 1), rng.integers(x0 // 128, (x1 - 1) // 128 + 1)
        d, _ = l4.get_full(l2.CTL, int(cy), int(cx))
        if d is None:
            continue
        f = d.reshape(109, -1)
        sm, sp, ok = l4.faces(f)
        z = np.arange(109)[:, None]
        ok2 = ok[None]
        inter = (z >= sm) & (z <= sp) & ok2
        near = (((z >= sm - 8) & (z < sm)) | ((z > sp) & (z <= sp + 8))) & ok2
        air = ~inter & ~near & ok2 & (f > 0)
        for k, msk in (("interior", inter), ("near", near), ("air", air)):
            hist[k] += np.bincount(f[msk], minlength=256)
        th += list((sp - sm)[ok])
        amp += list(((sm + sp) / 2 - 54)[ok])
    return hist, np.array(th), np.array(amp)


def synth_sheet(rng, hist, th, amp, n=512):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    a = float(np.percentile(np.abs(amp), 90))
    ph = rng.uniform(0, 2 * np.pi, 4)
    cen = 54 + a * 0.5 * (np.sin(xx / rng.uniform(40, 160) + ph[0]) + np.cos(yy / rng.uniform(40, 160) + ph[1]))
    t = rng.choice(th)
    tt = t + 2 * np.sin(xx / rng.uniform(30, 90) + ph[2])
    lo = np.rint(cen - tt / 2).astype(int)
    hi = np.rint(cen + tt / 2).astype(int)
    p = {k: v / v.sum() for k, v in hist.items()}
    z = np.arange(109)[:, None, None]
    cls = np.full((109, n, n), 2, np.int8)
    cls[((z >= lo - 8) & (z < lo)) | ((z > hi) & (z <= hi + 8))] = 1
    cls[(z >= lo) & (z <= hi)] = 0
    v = np.empty((109, n, n), np.uint8)
    for k, name in enumerate(("interior", "near", "air")):
        m = cls == k
        v[m] = rng.choice(256, size=int(m.sum()), p=p[name]).astype(np.uint8)
    return v


def main():
    d, out = sys.argv[1:3]
    tiles = {}
    for fn in glob.glob(os.path.join(d, "ctl_l4_w*.jsonl")):
        for l in open(fn):
            x = json.loads(l)
            tiles[(x["r"], x["c"])] = x
    assert len(tiles) == 64, len(tiles)
    rng = np.random.default_rng(SPLIT_SEED)
    split = {}
    for cls in ("text", "intercol"):
        ks = sorted(k for k, x in tiles.items() if x["class"] == cls)
        perm = rng.permutation(len(ks))
        ntr = math.ceil(len(ks) / 2)
        for n, i in enumerate(perm):
            split[ks[i]] = "train" if n < ntr else "held"
    hist, th, amp = empirical_classes(tiles)
    srng = np.random.default_rng(SYN_SEED)
    syn = {"m": [], "p": []}
    for s in range(100):
        v = synth_sheet(srng, hist, th, amp)
        b = l4.l4_block(v)
        for face in ("m", "p"):
            vals = b[face][b["ok"]]
            syn[face].append((np.bincount(vals, minlength=256), int(vals.size)))
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "declaration": "RULES.md DECL-P4-18 item 3", "level": 1, "n_tiles": {
               c: sum(x["class"] == c for x in tiles.values()) for c in ("text", "intercol")},
           "synthetic": {"n": 100, "thickness_slices_p10_50_90": np.percentile(th, [10, 50, 90]).tolist(),
                         "centre_offset_abs_p90_slices": float(np.percentile(np.abs(amp), 90)),
                         "class_voxel_medians": {k: l2.q_hist(v, 0.5) for k, v in hist.items()},
                         "class_voxel_p999": {k: l2.q_hist(v, 0.999) for k, v in hist.items()}},
           "faces": {}}
    for face, hk in (("L4-", "hist_m"), ("L4+", "hist_p")):
        cells = []
        for k, x in sorted(tiles.items()):
            for c in x["cells"]:
                if c["n_valid"] >= 0.5 * c["n_px"] and c["n_pos"] >= 0.5 * c["n_px"]:
                    cells.append((x["class"], split[k], frac_gt(c[hk], c["n_pos"])))
        sel = lambda cl, sp: np.array([f for a, s, f in cells if a == cl and (sp is None or s == sp)])  # noqa
        trt, tri, hot, hoi = sel("text", "train"), sel("intercol", "train"), sel("text", "held"), sel("intercol", "held")
        best = None
        for t in TS:
            F = qinv(tri[:, t], 0.95)
            rec = float((trt[:, t] > F).mean())
            if best is None or rec > best[1]:
                best = (t, rec, F)
        td, trec, F = best
        hrec, hfpr = float((hot[:, td] > F).mean()), float((hoi[:, td] > F).mean())
        allc = np.array([f for _, _, f in cells])
        rot = float((allc[:, td] > F).mean())  # rot-90 copies: same per-cell fractions (lattice rotates with tile)
        sk = "m" if face == "L4-" else "p"
        synf = float(np.mean([frac_gt(h, n)[td] > F for h, n in syn[sk] if n > 0]))
        ok = hrec >= 0.90 and hfpr <= 0.05 and rot <= 0.05 and synf <= 0.05
        res["faces"][face] = {"T_d": td, "F_cell_fraction": F, "train_recall": trec, "held_out_recall": hrec,
                              "held_out_fpr": hfpr, "rot90_flagged": rot, "synthetic_flagged": synf,
                              "n_cells": {"train_text": len(trt), "train_intercol": len(tri), "held_text": len(hot),
                                          "held_intercol": len(hoi)},
                              "verdict": "PASS" if ok else "FAIL"}
    offs = {k: [x["offsets_um"][k] for x in tiles.values() if x["offsets_um"][k]] for k in ("s_minus", "s_plus", "thickness")}
    res["face_offsets_um_median_of_tile_p10_p50_p90"] = {k: np.median(np.array(v), 0).tolist() for k, v in offs.items()}
    res["frac_l4_valid_median"] = float(np.median([x["frac_l4_valid"] for x in tiles.values()]))
    res["note_rot90"] = ("the cell statistic is a per-cell pixel fraction, invariant under rotating the tile with its cell "
                         "lattice; the rot-90 flagged rate therefore equals the flagged rate over ALL control cells (text "
                         "and intercolumn), so a detector with high text recall cannot pass it. Computed as declared; "
                         "raised in ASK.md.")
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res["faces"]), json.dumps(res["synthetic"]))


if __name__ == "__main__":
    main()
