"""Unit tests for the P4-L channel (tools/sib/p4-l2/l2.py). Synthetic data only; numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

1. A synthetic 15 um (6 slices at 2.4 um) bright layer on the recto surface of a synthetic sheet appears in the
   production +-15 um slab-max channel.
2. The E2 display (+-53 um slab mean, 45 slices, 1-99 % stretch) dilutes the same layer.
3. Null: with no layer, the 'letter' region is indistinguishable from background.
4. Production stitching (l2.region) equals a direct max on a chunked synthetic volume, incl. 404 chunks and edges.
5. q_hist equals numpy's inverted-CDF percentile; display is 0 outside mesh-valid.
Usage: python3 test_l2.py [out_json]
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402

RNG = np.random.default_rng(12345)
NZ, C = 109, 54


def structure(h, w, target_std):
    """Smooth in-plane papyrus structure (fibres, density), scaled so that the +-53 um slab mean of the sheet has
    std = target_std (E2 measured slab-mean std per tile: 16.5-21.3, median 18.3; pairs0814b REPORT)."""
    f = cv2.GaussianBlur(RNG.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 3)
    f = (f - f.mean()) / f.std()
    return f * target_std * 45 / 21  # 21 sheet slices of 45 in the mean slab


def synth(h=256, w=256, layer=True, amp=70.0, struct_std=0.0):
    """(109, h, w) uint8. Sheet: slices 44..64 (+-24 um around the mesh) papyrus N(90, 12) (+ optional in-plane
    structure); air elsewhere N(30, 8); bright layer: slices 55..60 (6 x 2.4 = 14.4 um, just recto-side of the
    mesh) + amp inside 'strokes'."""
    v = RNG.normal(30, 8, (NZ, h, w))
    v[C - 10:C + 11] = RNG.normal(90, 12, (21, h, w))
    if struct_std:
        v[C - 10:C + 11] += structure(h, w, struct_std)[None]
    strokes = np.zeros((h, w), bool)
    for x0 in range(20, w - 20, 48):  # vertical bars 16 px wide
        strokes[20:h - 20, x0:x0 + 16] = True
    strokes[h // 2 - 8:h // 2 + 8, 20:w - 20] = True  # a horizontal bar
    if layer:
        v[C + 1:C + 7][:, strokes] += amp
    return np.clip(np.rint(v), 0, 255).astype(np.uint8), strokes


def cohen_d(a, b):
    return float((a.mean() - b.mean()) / np.sqrt(0.5 * (a.var() + b.var())))


def test_layer(res, struct_std, key):
    vol, s = synth(struct_std=struct_std)
    ctl, _ = synth(layer=False, struct_std=struct_std)  # threshold "control": same sheet, no layer (thresholds from in-sheet voxels)
    h = np.bincount(ctl[l2.Z0:l2.Z1].ravel(), minlength=256)
    t_mid, t_hi = l2.q_hist(h, 0.5), l2.q_hist(h, 0.999)
    valid = np.ones(s.shape, bool)
    mx = l2.slab_max_from_stack(vol[l2.Z0:l2.Z1])
    d_max = l2.display_from_max(mx, valid, t_mid, t_hi).astype(float)
    mean = vol[32:77].mean(0)  # E2: slices 32..76, 45 slices
    lo, hi = np.percentile(mean, [1, 99])
    d_mean = np.clip(np.rint((mean - lo) / (hi - lo) * 255), 0, 255)
    bg = ~cv2.dilate(s.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    r = {"T_mid": t_mid, "T_hi": t_hi,
         "max_disp_stroke_mean": float(d_max[s].mean()), "max_disp_bg_mean": float(d_max[bg].mean()),
         "max_cohen_d": cohen_d(d_max[s], d_max[bg]),
         "mean_raw_delta": float(mean[s].mean() - mean[bg].mean()),
         "max_raw_delta": float(mx[s].astype(float).mean() - mx[bg].astype(float).mean()),
         "mean_disp_delta": float(d_mean[s].mean() - d_mean[bg].mean()),
         "mean_cohen_d_disp": cohen_d(d_mean[s], d_mean[bg])}
    # after the production downscale (factor ~7.8 here 256 -> 33) the strokes remain separable
    small = cv2.resize(l2.display_from_max(mx, valid, t_mid, t_hi), (33, 33), interpolation=cv2.INTER_AREA)
    ss = cv2.resize(s.astype(np.float32), (33, 33), interpolation=cv2.INTER_AREA)
    r["downscaled_stroke_minus_bg_u8"] = float(small[ss > 0.9].mean() - small[ss < 0.05].mean())
    r["struct_std_target"] = struct_std
    r["mean_slab_bg_std"] = float(mean[bg].std())
    # the layer appears in the channel
    assert r["max_disp_stroke_mean"] - r["max_disp_bg_mean"] >= 60, r
    assert r["max_cohen_d"] >= 1.5, r
    assert r["downscaled_stroke_minus_bg_u8"] >= 40, r
    # dilution: the +-53 um mean carries <= 1/4 of the raw step of the max channel (6 of 45 slices ~ 0.13)
    assert r["mean_raw_delta"] <= 0.25 * r["max_raw_delta"], r
    if struct_std:  # with realistic papyrus structure, the diluted step is buried: separability >= 2x lower
        assert r["max_cohen_d"] >= 2 * r["mean_cohen_d_disp"], r
    res[key] = r


def test_null(res):
    vol, s = synth(layer=False)
    h = np.bincount(vol[l2.Z0:l2.Z1].ravel(), minlength=256)
    t_mid, t_hi = l2.q_hist(h, 0.5), l2.q_hist(h, 0.999)
    d = l2.display_from_max(l2.slab_max_from_stack(vol[l2.Z0:l2.Z1]), np.ones(s.shape, bool), t_mid, t_hi)
    dd = cohen_d(d[s].astype(float), d[~s].astype(float))
    assert abs(dd) < 0.1, dd
    res["null_no_layer_cohen_d"] = dd


def test_region_and_quantiles(res):
    Hh, Ww = 300, 420  # not multiples of 128
    vol = RNG.integers(0, 256, (NZ, Hh, Ww), dtype=np.uint8)
    missing = {(1, 2)}

    def fake(seg, cy, cx):
        if (cy, cx) in missing:
            return None, {"k": f"0/0/{cy}/{cx}", "status": 404}
        blk = np.zeros((NZ, 128, 128), np.uint8)
        sub = vol[:, cy * 128:(cy + 1) * 128, cx * 128:(cx + 1) * 128]
        blk[:, :sub.shape[1], :sub.shape[2]] = sub
        return blk[l2.Z0:l2.Z1].copy(), {"k": f"0/0/{cy}/{cx}", "status": 206}

    ref = vol.copy()
    ref[:, 128:256, 256:384] = 0
    orig = l2.get_chunk
    l2.get_chunk = fake
    try:
        import concurrent.futures as cf
        ex = cf.ThreadPoolExecutor(4)
        y0, y1, x0, x1 = 50, 350, 100, 460  # runs past the array edge in both axes
        m = np.zeros((y1 - y0, x1 - x0), bool)
        m[:Hh - y0, :Ww - x0] = RNG.random((Hh - y0, Ww - x0)) < 0.7
        out, hist, n_hi, recs = l2.region("x", y0, y1, x0, x1, (Hh, Ww), m, ex, t_hi=200)
        ex.shutdown()
    finally:
        l2.get_chunk = orig
    exp = np.zeros_like(out)
    exp[:Hh - y0, :Ww - x0] = ref[l2.Z0:l2.Z1, y0:, x0:].max(0)
    assert np.array_equal(out, exp)
    sl = ref[l2.Z0:l2.Z1, y0:Hh, x0:Ww][:, m[:Hh - y0, :Ww - x0]]
    assert np.array_equal(hist, np.bincount(sl.ravel(), minlength=256))
    assert n_hi == int((sl > 200).sum())
    for q in (0.5, 0.999, 0.01):
        assert l2.q_hist(hist, q) == int(np.percentile(sl.ravel(), q * 100, method="inverted_cdf"))
    d = l2.display_from_max(out, m, 80, 200)
    assert (d[~m] == 0).all()
    res["region_stitch_404_edges_hist_quantiles_mask"] = "pass"


def test_order(res):
    el = [(r, c) for r in range(8) for c in range(20)]
    o = l2.order_tiles(el)
    assert all(t[0] <= 1 for t in o[:40]) and len(o) == 160
    assert o[0::4][:10] == [(0, 0), (0, 4), (0, 8), (0, 12), (0, 16), (1, 0), (1, 4), (1, 8), (1, 12), (1, 16)]
    res["order_r0_r1_first"] = "pass"


if __name__ == "__main__":
    res = {"provenance": l2.PROV}
    test_layer(res, 18.3, "layer_E2_calibrated_structure")
    test_layer(res, 0.0, "layer_no_structure_disclosure")
    for f in (test_null, test_region_and_quantiles, test_order):
        f(res)
    res["note"] = ("Raw-step dilution (mean/max) is asserted in both scenarios. Separability loss of the +-53 um "
                   "mean is asserted only with in-plane structure calibrated to E2's measured slab-mean std; without "
                   "structure a stretched mean still separates the layer (disclosed, not asserted).")
    res["all_pass"] = True
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1:
        json.dump(res, open(sys.argv[1], "w"), indent=1)
