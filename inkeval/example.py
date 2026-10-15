"""The bundled real example and the demo.

``inkeval/data/example_scroll1.npz`` holds two HELD-OUT Scroll 1 (PHerc.Paris.4) crops, each 15 mm square, mean-pooled 8x from
2.4 um to 19.2 um so the package stays small:
    seg 20231005123336 crop held2 and seg 20231210121321 crop held1 (crop coordinates in stats/s1_crops_<seg>.json)
with, per crop: the registered Grand-Prize hand label, the judge mask, and three score maps -
    e     the release's best detector (rank-mean ensemble of v8 and GP-R1; no team-model veto or scores in its training data;
          labels placed against the team model, see README Limitations)
    v7    the best hand-built physics baseline
    team  the Vesuvius Challenge team's published 2.4 um ink prediction (POSITIVE control; its training labels are not known to us)
Data: derived from Vesuvius Challenge data, CC BY-NC 4.0 - see DATA_NOTICE.md. Because of the pooling, the demo's numbers are close to
but not equal to the published 2.4 um numbers; exact reproduction is tested in tests/test_published.py when the full data are present.
"""
from __future__ import annotations

import json
import os

import numpy as np

from .metrics import judge, judge_classes
from .stats import bootstrap_ci, label_swap_null, trunc

HERE = os.path.dirname(__file__)
EXAMPLE = os.path.join(HERE, "data", "example_scroll1.npz")
CROPS = [("20231005123336", "held2"), ("20231210121321", "held1")]
TAGS = ("e", "v7", "team")
POOL = 8
PITCH_UM = 2.4 * POOL


def _pool(a, f, mode):
    h, w = a.shape[0] // f * f, a.shape[1] // f * f
    b = a[:h, :w].reshape(h // f, f, w // f, f)
    return b.mean(axis=(1, 3)) if mode == "mean" else (b.astype(np.float32).mean(axis=(1, 3)) > 0.5)


def build(root="data/s1", out=EXAMPLE):
    """Rebuild the example from the full crops (needs the research data on disk)."""
    arrs = {}
    for seg, crop in CROPS:
        d = os.path.join(root, seg, "derived", crop); k = f"{seg}_{crop}"
        mask = (np.load(f"{d}/mask_top.npy") > 0) & (np.load(f"{d}/mask_bot.npy") > 0)
        label = np.load(f"{d}/label.npy")
        pm = _pool(mask, POOL, "bool"); pl = _pool(label, POOL, "bool")
        arrs[f"{k}_mask_bits"] = np.packbits(pm); arrs[f"{k}_label_bits"] = np.packbits(pl)
        arrs[f"{k}_shape"] = np.array(pm.shape)
        for t in TAGS:
            s = np.load(f"{d}/s_bot_{t}.npy").astype(np.float32)
            arrs[f"{k}_{t}"] = np.where(pm, _pool(s, POOL, "mean"), 0).astype(np.float16)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, **arrs)
    return out


def load():
    """Return {crop_key: {'label', 'mask', 'e', 'v7', 'team'}} from the bundled file."""
    z = np.load(EXAMPLE)
    out = {}
    for seg, crop in CROPS:
        k = f"{seg}_{crop}"; shape = tuple(z[f"{k}_shape"])
        n = shape[0] * shape[1]
        rec = {"mask": np.unpackbits(z[f"{k}_mask_bits"])[:n].reshape(shape).astype(bool),
               "label": np.unpackbits(z[f"{k}_label_bits"])[:n].reshape(shape).astype(bool)}
        for t in TAGS:
            rec[t] = z[f"{k}_{t}"].astype(np.float32)
        out[k] = rec
    return out


def run_demo(verbose=True):
    data = load()
    results = {}
    for k, rec in data.items():
        results[k] = {t: judge(rec[t], rec["label"], rec["mask"], PITCH_UM) for t in TAGS}
    keys = list(data)
    cls = [judge_classes(data[k]["label"], data[k]["mask"], PITCH_UM) for k in keys]
    null = {t: label_swap_null([data[k][t] for k in keys], [c[0] for c in cls], [c[1] for c in cls],
                               [data[k]["mask"] for k in keys], subsample=None) for t in TAGS}
    if verbose:
        print(f"inkeval demo - two held-out Scroll 1 crops pooled to {PITCH_UM} um (bundled; CC BY-NC 4.0 data)\n")
        print(f"{'crop':28s} {'method':6s} {'pixel':>7s} {'stroke':>7s} {'local L':>8s}")
        for k in keys:
            for t in TAGS:
                r = results[k][t]
                f = lambda v: f"{trunc(v, 3):7.3f}" if v is not None else "   none"
                print(f"{k:28s} {t:6s} {f(r['pixel_auc'])} {f(r['stroke_auc'])} {f(r['local_L']):>8s}")
        print("\nnegative control - label swap between the two crops (should sit near 0.5):")
        for t in TAGS:
            print(f"  {t:5s} mean {trunc(null[t]['mean'], 3):.3f} over {null[t]['pairs']} ordered pairs")
        print("\nNote: a single crop is not a sample size. Put intervals on crops, e.g.")
        print("  inkeval bootstrap results/per_crop_evaluation7.csv --column e_pixel")
    return {"judge": results, "null": null}
