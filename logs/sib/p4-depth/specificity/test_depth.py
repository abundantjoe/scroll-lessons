"""Unit tests for P4-L3 depth calibration (DECL-P4-12-A3; task item 3). Synthetic data only, no CT, no pixels viewed.

Provenance: Project HERCULES | owner the owner | [id removed]

(a) A synthetic sheet (109 slices at 2.4 um, papyrus body around the mesh, noise) with a bright 15 um layer at a known
    offset, blurred along depth by a Gaussian CT point-spread function (sigma 1 slice = 2.4 um), must give PASS with d*
    within 5 um of that offset, for several offsets on both sides and several seeds (ASSERTED).
    a_sharp: the same without blur (a flat-topped layer) is REPORTED, not asserted: the declared argmax rule then picks a
    random slice of the plateau, so |d* - offset| can reach half the layer thickness (7.2 um at 2.4 um steps).
(b) No layer must give STOP.
    b0: a noise-free uniform sheet (f(o) constant over offsets), ASSERTED STOP.
    b1: a uniform noisy sheet filling all 109 offsets (no body/gap contrast), REPORTED over 100 seeds: the declared rule
        takes the MAXIMUM over 109 offsets against a single 3-robust-SD bar, so iid noise alone passes it at a rate
        of order 1 - (1 - 0.00135)^109 ~ 14 % (more with MAD estimation noise). The z of the max of iid offsets is
        independent of the noise scale, so real voxel counts do not remove this.
    b2: a sheet body (+-50 um) between darker gaps, no ink layer: REPORTED. Under the declared rule (median over all 109
        offsets) the body itself exceeds the gap-dominated median by many robust SD, so the rule gives PASS: a finding
        about the declared rule's specificity, written to ASK.md, not a bug in this implementation.
(c) rot90 counting equals direct counting; l3_slices gives +-4 slices; f_from_hist matches a direct count.
Run: python3 tools/sib/p4-depth/test_depth.py [out.json]
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import depth  # noqa: E402

T_HI = 203


def synth_hist(layer_um, seed, n_px=40000, layer_um_thick=15.0, psf_sigma_slices=1.0, gaps=True, cover=0.05):
    """Per-slice histograms of a synthetic sheet: papyrus body (+-50 um, mean 110) and air/gaps (mean 40; or body
    everywhere if gaps=False), Gaussian noise SD 30 with rare bright speckle; optional ink layer (15 um thick,
    mean 215, covering `cover` of the area), whose depth weight is a box of the layer thickness convolved with a
    Gaussian PSF of psf_sigma_slices (0 = sharp)."""
    rng = np.random.default_rng(seed)
    off = depth.offsets_um()
    fine = np.arange(-200.0, 200.0, 0.1)
    hist = np.zeros((depth.NZ, 256), np.int64)
    for z, o in enumerate(off):
        mu = 110.0 if (abs(o) <= 50 or not gaps) else 40.0
        v = rng.normal(mu, 30.0, n_px)
        spk = rng.random(n_px) < 0.0005
        v[spk] = rng.uniform(150, 255, spk.sum())
        if layer_um is not None:
            box = (np.abs(fine - layer_um) <= layer_um_thick / 2).astype(float)
            if psf_sigma_slices > 0:
                s = psf_sigma_slices * depth.UM
                w = float((box * np.exp(-0.5 * ((fine - o) / s) ** 2)).sum() * 0.1 / (s * np.sqrt(2 * np.pi)))
            else:
                w = float(abs(o - layer_um) <= layer_um_thick / 2)
            ink = rng.random(n_px) < cover
            v[ink] = (1 - w) * v[ink] + w * rng.normal(215.0, 20.0, ink.sum())
        hist[z] = np.bincount(np.clip(np.rint(v), 0, 255).astype(np.int64), minlength=256)
    return hist


def main():
    res = {"a_layer": [], "a_sharp_reported": [], "b1_uniform_no_layer": [], "b2_sheet_gap_no_layer_reported": [],
           "c_misc": {}}
    ok = True
    off = depth.offsets_um()
    for layer in (-60.0, -30.0, -12.0, 0.0, 19.0, 45.0, 84.0):
        for seed in (1, 2, 3):
            pv = depth.peak_verdict(depth.f_from_hist(synth_hist(layer, seed), T_HI), off)
            good = pv["verdict"] == "PASS" and abs(pv["d_star_um"] - layer) <= 5.0
            ok &= good
            res["a_layer"].append({"layer_um": layer, "seed": seed, "d_star_um": pv["d_star_um"],
                                   "z_peak": round(pv["z_peak"], 2), "verdict": pv["verdict"], "pass": good})
            pv = depth.peak_verdict(depth.f_from_hist(synth_hist(layer, seed, psf_sigma_slices=0), T_HI), off)
            res["a_sharp_reported"].append({"layer_um": layer, "seed": seed, "d_star_um": pv["d_star_um"],
                                            "abs_err_um": round(abs(pv["d_star_um"] - layer), 2),
                                            "verdict": pv["verdict"]})
    b0 = depth.peak_verdict(np.full(depth.NZ, 0.001), off)["verdict"] == "STOP"
    res["b0_noise_free_uniform_stops"] = b0
    ok &= b0
    for seed in range(1, 101):
        pv = depth.peak_verdict(depth.f_from_hist(synth_hist(None, seed, gaps=False, n_px=20000), T_HI), off)
        res["b1_uniform_no_layer"].append({"seed": seed, "d_star_um": pv["d_star_um"], "z_peak": round(pv["z_peak"], 2),
                                           "verdict": pv["verdict"]})
    for seed in range(1, 11):
        pv = depth.peak_verdict(depth.f_from_hist(synth_hist(None, seed), T_HI), off)
        res["b2_sheet_gap_no_layer_reported"].append({"seed": seed, "d_star_um": pv["d_star_um"],
                                                      "z_peak": round(pv["z_peak"], 2), "verdict": pv["verdict"]})
    # a layer outside +-100 um must STOP even if strong
    pv = depth.peak_verdict(depth.f_from_hist(synth_hist(115.0, 5), T_HI), off)
    res["c_misc"]["layer_at_115um_stops"] = pv["verdict"] == "STOP"
    ok &= pv["verdict"] == "STOP"
    # f_from_hist vs direct count; rot90 identity
    rng = np.random.default_rng(7)
    vol = rng.integers(0, 256, (depth.NZ, 64, 48), dtype=np.uint8)
    m = rng.random((64, 48)) < 0.7
    h = np.stack([np.bincount(vol[z][m], minlength=256) for z in range(depth.NZ)])
    direct = (vol[:, m] > T_HI).sum(1) / m.sum()
    rot = (np.rot90(vol, axes=(1, 2))[:, np.rot90(m)] > T_HI).sum(1) / m.sum()
    res["c_misc"]["f_from_hist_equals_direct"] = bool(np.array_equal(depth.f_from_hist(h, T_HI), direct))
    res["c_misc"]["rot90_equals_direct"] = bool(np.array_equal(rot, direct))
    res["c_misc"]["l3_slices_z54"] = depth.l3_slices(54)
    res["c_misc"]["l3_slices_z2"] = depth.l3_slices(2)
    ok &= res["c_misc"]["f_from_hist_equals_direct"] and res["c_misc"]["rot90_equals_direct"]
    ok &= depth.l3_slices(54) == (50, 58) and depth.l3_slices(2) == (0, 6)
    res["all_asserted_pass"] = bool(ok)
    res["a_sharp_max_abs_err_um"] = max(x["abs_err_um"] for x in res["a_sharp_reported"])
    res["b2_n_pass_of_10"] = sum(x["verdict"] == "PASS" for x in res["b2_sheet_gap_no_layer_reported"])
    res["b1_n_pass_of_100"] = sum(x["verdict"] == "PASS" for x in res["b1_uniform_no_layer"])
    res["finding"] = ("declared rule gives PASS on %d/100 iid-noise uniform sheets (b1) and on %d/10 no-ink sheets with "
                      "body/gap contrast (b2): a PASS alone does not show an ink layer"
                      % (res["b1_n_pass_of_100"], res["b2_n_pass_of_10"]))
    print(json.dumps({"all_asserted_pass": ok,
                      "a": [(x["layer_um"], x["d_star_um"], x["z_peak"], x["verdict"]) for x in res["a_layer"]],
                      "a_sharp_max_abs_err_um": res["a_sharp_max_abs_err_um"],
                      "b0": b0, "b1_n_pass_of_100": res["b1_n_pass_of_100"],
                      "b2": [(x["d_star_um"], x["z_peak"], x["verdict"]) for x in res["b2_sheet_gap_no_layer_reported"]],
                      "finding": res["finding"]}))
    if len(sys.argv) > 1:
        json.dump(res, open(sys.argv[1], "w"), indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
