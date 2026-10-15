# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic check of the levelled-canvas scoring path: levelmap round trip, cv_eval_lev.py sampling and bar logic.
A map made on the organizer canvas is resampled onto a rotated/scaled levelled canvas; scoring must recover it."""
import json, os, subprocess, sys
import numpy as np
from scipy.ndimage import map_coordinates
D = os.path.join(os.path.dirname(__file__), "..", "tools", "sib", "reg0841", "chainvalid")
sys.path.insert(0, D)
from levelmap import org_px_to_lev_px, lev_px_to_org_px


def test_levelmap_roundtrip():
    th = np.radians(81.9); T = dict(e_u=[np.sin(th), -np.cos(th)], e_v=[np.cos(th), np.sin(th)], origin=[-40.0, 3.0], du=1.02, dv=0.97)
    r = np.array([0.0, 100.5, 3000.0]); c = np.array([5.0, 700.0, 1234.25])
    rp, cp = org_px_to_lev_px(T, r, c); r2, c2 = lev_px_to_org_px(T, rp, cp)
    assert np.allclose(r2, r) and np.allclose(c2, c)


def test_cv_eval_lev_synthetic(tmp_path):
    import tifffile
    rng = np.random.default_rng(1)
    H, W = 800, 900
    th = np.radians(81.9); T = dict(e_u=[np.sin(th), -np.cos(th)], e_v=[np.cos(th), np.sin(th)], origin=[-45.0, 0.0], du=1.0, dv=1.0)
    k, s = "214732", "20260220214732-auto_grown_20260220144552896"
    ink = np.zeros((H, W), bool); ink[300:500, 300:360] = True; ink[380:420, 400:650] = True
    org = (ink * 200 + rng.integers(0, 40, (H, W))).astype(np.uint8)
    (tmp_path / f"mesh_lev/{k}").mkdir(parents=True); (tmp_path / f"org/{s}").mkdir(parents=True)
    json.dump(T, open(tmp_path / f"mesh_lev/{k}/level_transform.json", "w")); tifffile.imwrite(tmp_path / f"org/{s}/inkmap.tif", org)
    good_org = np.clip(ink * 0.8 + rng.normal(0.1, 0.05, (H, W)), 0, 1).astype(np.float32)
    # levelled canvas extent
    er, ec = np.nonzero(np.ones((H, W), bool)[250:550, 250:700]); er += 250; ec += 250
    rp, cp = org_px_to_lev_px(T, er, ec)
    y0, x0 = int(np.floor(rp.min())) - 4, int(np.floor(cp.min())) - 4; y1, x1 = int(np.ceil(rp.max())) + 4, int(np.ceil(cp.max())) + 4
    LH, LW = y1 + 10, x1 + 10
    RL = np.zeros((LH, LW), bool); RL[max(y0, 0):y1, max(x0, 0):x1] = True
    np.save(tmp_path / f"area_lev_{k}.npy", RL)
    np.savez(tmp_path / f"lev_E_{k}.npz", r=er, c=ec, rp=rp, cp=cp, ink=ink[er, ec])
    ly, lx = np.mgrid[0:LH, 0:LW]; ro, co = lev_px_to_org_px(T, ly.ravel(), lx.ravel())
    lev_good = map_coordinates(good_org, np.stack([ro, co]), order=1, cval=0).reshape(LH, LW).astype(np.float32)
    lev_bad = rng.uniform(0, 1, (LH, LW)).astype(np.float32)
    crop = dict(segment=k, segment_id=s, ry=0, rx=0, rh=LH, rw=LW, core=[0, LH, 0, LW])
    json.dump({"crops_primary": [crop]}, open(tmp_path / "plan.json", "w"))
    for o, m in (("reverse", lev_good), ("forward", lev_bad)):
        d = tmp_path / f"maps/{o}/{k}/0_0"; d.mkdir(parents=True); np.savez(d / "map.npz", map=m)
    out = tmp_path / "res.json"
    subprocess.run([sys.executable, os.path.join(D, "cv_eval_lev.py"), str(tmp_path / "plan.json"), "crops_primary", str(tmp_path / "maps"),
                    str(out), "--work", str(tmp_path)], check=True, capture_output=True)
    r = json.load(open(out))
    assert r["pooled"]["reverse"]["auc"] > 0.99 and r["pooled"]["reverse"]["r_org_E"] > 0.8, r["pooled"]
    assert 0.4 < r["pooled"]["forward"]["auc"] < 0.6
    assert r["bar"]["winning_order"] == "reverse"
