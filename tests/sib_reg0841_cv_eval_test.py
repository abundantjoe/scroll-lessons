# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic end-to-end check of tools/sib/reg0841/chainvalid/cv_eval.py: crop stitching, E masking, bar logic."""
import json, os, subprocess, sys
import numpy as np


def test_cv_eval_synthetic(tmp_path):
    import zarr, tifffile
    H, W = 600, 700
    rng = np.random.default_rng(0)
    ink = np.zeros((H, W), bool); ink[200:400, 200:260] = True; ink[250:300, 300:500] = True
    sup = np.zeros((H, W), bool); sup[150:450, 150:550] = True
    org = (ink * 200 + rng.integers(0, 40, (H, W))).astype(np.uint8)
    R = np.zeros((H, W), bool); R[100:500, 100:600] = True
    s = "20260220214732-auto_grown_20260220144552896"
    for name, arr in (("inklabels", ink), ("supervision", sup)):
        z = zarr.create_array(str(tmp_path / f"org/{s}/{name}.zarr/0"), shape=(H, W), dtype="uint8", chunks=(H, W))
        z[:] = arr.astype(np.uint8) * 255
    tifffile.imwrite(tmp_path / f"org/{s}/inkmap.tif", org)
    np.save(tmp_path / "area_214732.npy", R)
    good = np.clip(ink * 0.8 + rng.normal(0.1, 0.05, (H, W)), 0, 1).astype(np.float32)
    bad = rng.uniform(0, 1, (H, W)).astype(np.float32)
    for o, m in (("reverse", good), ("forward", bad)):
        for y, x in [(y, x) for y in range(-128, H, 272) for x in range(-128, W, 272)]:
            d = tmp_path / f"maps/{o}/214732/{y}_{x}"; d.mkdir(parents=True)
            crop = np.zeros((528, 528), np.float32)
            ys, xs = max(y, 0), max(x, 0); ye, xe = min(y + 528, H), min(x + 528, W)
            crop[ys - y:ye - y, xs - x:xe - x] = m[ys:ye, xs:xe]
            np.savez(d / "map.npz", map=crop)
    tool = os.path.join(os.path.dirname(__file__), "..", "tools", "sib", "reg0841", "chainvalid", "cv_eval.py")
    out = tmp_path / "res.json"
    subprocess.run([sys.executable, tool, str(tmp_path / "maps"), str(out), "--org-root", str(tmp_path / "org"),
                    "--area-root", str(tmp_path)], check=True, capture_output=True)
    r = json.load(open(out))
    assert r["pooled"]["reverse"]["auc"] > 0.99 and r["pooled"]["reverse"]["r_org_E"] > 0.6
    assert 0.4 < r["pooled"]["forward"]["auc"] < 0.6
    assert r["bar"]["winning_order"] == "reverse" and r["bar"]["verdict"] == "PASS"
    assert r["pooled"]["reverse"]["n_E"] == int((R & sup).sum())
