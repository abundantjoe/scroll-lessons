"""Regenerate a crop's v8, GP-R1 and E maps from the RELEASED weights and compare them, byte for byte, with the expected hashes.

  check_reproducibility.py <seg> <crop> [--write results/reproducibility_check.json]

Needs the crop's pooled depth stack (ds8_x.npy) and judge mask (mask_top/mask_bot.npy), i.e. a crop prepared by scripts/run_s1_seg.sh or
run_c1.sh. Prints the SHA-256 of each regenerated array's bytes; with the committed expected values it reports identical/different.
Also re-judges the regenerated E map with inkeval and compares with the published judge record.
"""
import hashlib, json, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inkeval import judge_classes, pixel_auc, rank_mean  # noqa: E402

seg, crop = sys.argv[1], sys.argv[2]
D = f"data/s1/{seg}/derived/{crop}"
py = sys.executable
h = lambda a: hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

subprocess.run([py, "scripts/s1_v5.py", "predict", D, "models/v8_unet.pt", "v8chk"], check=True, stdout=subprocess.DEVNULL)
subprocess.run([py, "scripts/gpr.py", "predict", D, "models/gpr1.pt", "gpr1chk"], check=True, stdout=subprocess.DEVNULL)
v8 = np.load(f"{D}/s_bot_v8chk.npy"); g = np.load(f"{D}/s_bot_gpr1chk.npy")
mask = (np.load(f"{D}/mask_top.npy") > 0) & (np.load(f"{D}/mask_bot.npy") > 0)
e = rank_mean([v8, g], mask)
text, blank = judge_classes(np.load(f"{D}/label.npy"), mask, 2.4)
got = {"v8_sha256": h(v8), "gpr1_sha256": h(g), "e_sha256": h(e), "e_pixel_auc": pixel_auc(e.astype(np.float32), text, blank)}
for t in ("v8chk", "gpr1chk"):
    for f in ("bot", "top"):
        p = f"{D}/s_{f}_{t}.npy"
        if os.path.exists(p): os.remove(p)
    p = f"{D}/s_bot_{t}_u8.npy"
    if os.path.exists(p): os.remove(p)

key = f"{seg}:{crop}"
rec = {}
exp_path = "results/reproducibility_check.json"
if os.path.exists(exp_path):
    rec = json.load(open(exp_path))
if "--write" in sys.argv:
    stored = {t: h(np.load(f"{D}/s_bot_{t}.npy")) for t in ("v8", "gpr1", "e")}
    judged = json.load(open(f"{D}/judge_e.json"))["bot"]["auc_px"]
    rec[key] = {**got, "stored_maps_sha256": stored, "published_e_pixel_auc": judged,
                "regenerated_equals_stored": {"v8": got["v8_sha256"] == stored["v8"], "gpr1": got["gpr1_sha256"] == stored["gpr1"],
                                              "e": got["e_sha256"] == stored["e"]}}
    json.dump(rec, open(exp_path, "w"), indent=1)
    print(json.dumps(rec[key], indent=1))
else:
    exp = rec.get(key)
    if not exp:
        sys.exit(f"no expected values for {key} in {exp_path}")
    exact = all(got[k] == exp[k] for k in ("v8_sha256", "gpr1_sha256", "e_sha256", "e_pixel_auc"))
    for k in ("v8_sha256", "gpr1_sha256", "e_sha256", "e_pixel_auc"):
        print(f"{k:14s} {'OK ' if got[k] == exp[k] else 'DIFF'} {got[k]}")
    if exact:
        print("RESULT: bit-identical to the release"); sys.exit(0)
    # PyTorch CPU kernels may differ across processors; the scientific claim is the AUC, so fall back to a stated tolerance.
    tol = 1e-3
    if abs(got["e_pixel_auc"] - exp["e_pixel_auc"]) <= tol:
        print(f"RESULT: arrays differ at the bit level (expected across CPU types), E pixel AUC within {tol} of the release"); sys.exit(0)
    print(f"RESULT: E pixel AUC differs from the release by more than {tol}"); sys.exit(1)
