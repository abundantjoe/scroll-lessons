# Provenance: Project HERCULES | owner the owner | [id removed]
"""Level the three mapped meshes and verify the canvas correspondence geometrically on the real meshes:
for 20000 seeded random organizer-canvas px inside the renderable area, the 3-D point from the organizer-grid mesh
(bilinear) and from the levelled mesh at the mapped levelled px (bilinear) must agree. Also edge-length stats."""
import json, sys
import numpy as np, tifffile
sys.path.insert(0, "/home/user/dominion/src"); sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841/chainvalid")
from hercules.geometry.tifxyz import sample_grid
from levelmap import level_segment, org_px_to_lev_px, lev_px_to_org_px
out = {}
rng = np.random.default_rng(20260926)
for key in ("w00", "214732", "022814"):
    L, T = level_segment(key)
    P = np.stack([tifffile.imread(f"/work/cv/mesh/{key}/{a}.tif") for a in "xyz"], -1).astype(np.float64)
    R = np.load(f"/work/cv/area_{key}.npy")
    rr, cc = np.nonzero(R); k = rng.choice(len(rr), 20000, replace=False); r, c = rr[k], cc[k]
    a = sample_grid(P, (r + 0.5) / 20, (c + 0.5) / 20)
    rp, cp = org_px_to_lev_px(T, r, c)
    b = sample_grid(L.points.astype(np.float64), (rp + 0.5) / 20, (cp + 0.5) / 20)
    ok = (a[:, 0] != -1) & (b[:, 0] != -1)
    d = np.linalg.norm(a[ok] - b[ok], axis=1)
    r2, c2 = lev_px_to_org_px(T, rp, cp)
    e = L.points.astype(np.float64); okq = e[..., 0] != -1
    hs = np.linalg.norm(e[:, 1:] - e[:, :-1], axis=-1)[okq[:, 1:] & okq[:, :-1]]
    vs = np.linalg.norm(e[1:] - e[:-1], axis=-1)[okq[1:] & okq[:-1]]
    out[key] = dict(T=T, n_test=20000, n_both_valid=int(ok.sum()), dist_median=float(np.median(d)), dist_p99=float(np.percentile(d, 99)),
                    dist_max=float(d.max()), roundtrip_px_max=float(max(np.abs(r2 - r).max(), np.abs(c2 - c).max())),
                    edge_h_median=float(np.median(hs)), edge_v_median=float(np.median(vs)),
                    edge_within_10pct=float(np.mean(np.r_[np.abs(hs / 20 - 1) <= 0.1, np.abs(vs / 20 - 1) <= 0.1])),
                    levelled_shape=T["shape"], levelled_valid_nodes=int(okq.sum()))
    print(key, json.dumps({kk: v for kk, v in out[key].items() if kk != "T"}), round(T["angle_deg"], 2), round(T["spread_deg"], 2), flush=True)
json.dump(out, open("/home/user/dominion/logs/sib/reg0841/chainvalid/level_check.json", "w"), indent=1)
