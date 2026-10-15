"""Unit tests (PROTOCOL section 7), synthetic arrays only. Provenance: Project HERCULES | owner the owner | [id removed]"""
import json
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mo  # noqa: E402

res = {}
rng = np.random.default_rng(1)
# 1. sub-voxel faces on synthetic sheets (void 60, papyrus 140, edge blurred by sigma 1 slice PSF), noise SD 8
n = 4000
zt_p = 54 + rng.uniform(8, 30, n)
zt_m = 54 - rng.uniform(8, 30, n)
k = np.arange(mo.NZ)[:, None]
fine = np.linspace(-0.5, 0.5, 21)
prof = np.zeros((mo.NZ, n))
for f in fine:  # voxel integration of the step
    prof += np.where((k + f <= zt_p) & (k + f >= zt_m), 140.0, 60.0)
prof /= len(fine)
prof = gaussian_filter1d(prof, 1.0, axis=0)
# the 4x4 block mean of 16 px with SD 8 each gives SD 2 per block voxel
P = gaussian_filter1d(prof + rng.normal(0, 8 / 4, prof.shape), 1.0, axis=0, mode="nearest").astype(np.float32)
hp, hm, zp, zm, okc = mo.faces(P, 100.0, anchor=False)
ep = np.abs((zp - zt_p) * mo.UM)
em = np.abs((zm - zt_m) * mo.UM)
res["face_err_um_median_plus"] = float(np.nanmedian(ep))
res["face_err_um_median_minus"] = float(np.nanmedian(em))
res["face_found_frac"] = float(np.isfinite(zp).mean())
res["face_ok"] = bool(res["face_err_um_median_plus"] < 0.5 and res["face_err_um_median_minus"] < 0.5)
# 2. a 1-slice pore inside the sheet is rejected by 2-slice persistence
p = np.full((mo.NZ, 1), 140.0, np.float32)
p[70:, 0] = 60.0
p[60, 0] = 60.0
hp1, _, zp1, _, _ = mo.faces(p, 100.0, anchor=False)
res["pore_z_plus"] = float(zp1[0])
res["pore_ok"] = bool(abs(zp1[0] - 69.5) < 1e-6)
# 3. AUC
a = rng.normal(0, 1, 20000)
b = rng.normal(0, 1, 20000)
res["auc_identical"] = mo.auc_float(a, b)
d = 0.8
res["auc_shift"] = mo.auc_float(a + d, b)
res["auc_shift_analytic"] = float(norm.cdf(d / np.sqrt(2)))
edges = np.quantile(np.concatenate([a + d, b]), np.linspace(0, 1, 4097)[1:-1])
res["auc_hist_shift"] = mo.auc_hist(np.bincount(np.searchsorted(edges, a + d), minlength=4096),
                                    np.bincount(np.searchsorted(edges, b), minlength=4096))
res["auc_ok"] = bool(abs(res["auc_identical"] - 0.5) < 0.01 and abs(res["auc_shift"] - res["auc_shift_analytic"]) < 0.01
                     and abs(res["auc_hist_shift"] - res["auc_shift"]) < 0.001)
# 4. rot90 round trip
x = rng.normal(size=(1038, 1038))
res["rot_ok"] = bool(np.array_equal(np.rot90(np.rot90(x, 1), -1), x))
# 5. T_face on a bimodal histogram
hh = np.bincount(np.concatenate([rng.normal(60, 8, 50000), rng.normal(140, 10, 80000)]).clip(0, 255).astype(int),
                 minlength=256)
res["tface_synth"] = mo.tface_from_hist(hh)
res["tface_ok"] = bool(abs(res["tface_synth"]["T_face"] - 100) < 4)
# 6. energy_at window mean
E = np.tile(np.arange(mo.NZ, dtype=np.float32)[:, None], (1, 3))
z = np.array([54.2, 3.0, np.nan], np.float32)
ea = mo.energy_at(E, z)
res["energy_at"] = [float(v) for v in ea]
res["energy_ok"] = bool(abs(ea[0] - 54) < 1e-5 and abs(ea[1] - np.mean(np.arange(0, 8))) < 1e-5 and np.isnan(ea[2]))
# 7. amendment A1: anchor inside a sheet displaced from slice 54 (mesh in void), and anchor=False equivalence
zt_p2, zt_m2 = 54 + rng.uniform(15, 25, n), 54 + rng.uniform(2, 8, n)  # sheet entirely on '+' side of the mesh
pr2 = np.zeros((mo.NZ, n))
for f in fine:
    pr2 += np.where((k + f <= zt_p2) & (k + f >= zt_m2), 140.0, 60.0)
pr2 = gaussian_filter1d(pr2 / len(fine), 1.0, axis=0)
P2 = gaussian_filter1d(pr2 + rng.normal(0, 2, pr2.shape), 1.0, axis=0, mode="nearest").astype(np.float32)
hpa, hma, zpa, zma, _ = mo.faces(P2, 100.0, anchor=True)
res["anchor_err_um_median_plus"] = float(np.nanmedian(np.abs((zpa - zt_p2) * mo.UM)))
res["anchor_err_um_median_minus"] = float(np.nanmedian(np.abs((zma - zt_m2) * mo.UM)))
res["anchor_found_frac"] = float(np.isfinite(zpa).mean())
hpo = mo.faces(P, 100.0, anchor=False)
res["anchor_ok"] = bool(res["anchor_err_um_median_plus"] < 0.5 and res["anchor_err_um_median_minus"] < 0.5
                        and res["anchor_found_frac"] > 0.99 and np.allclose(hpo[2], zp, equal_nan=True))
res["ALL_PASS"] = all(v for k_, v in res.items() if k_.endswith("_ok"))
print(json.dumps(res, indent=1))
json.dump({"provenance": mo.PROV, **res}, open(sys.argv[1], "w"), indent=1) if len(sys.argv) > 1 else None
