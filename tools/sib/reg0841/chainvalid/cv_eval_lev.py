# Provenance: Project HERCULES | owner the owner | [id removed]
"""CHAIN VALID metrics for maps rendered on the LEVELLED canvas, scored on the organizer canvas (numbers only).
Crop records (plan): render origin (ry, rx), size (rh, rw), core [y0, y1, x0, x1] on the levelled canvas.
E: the E_org px from lev_E_<seg>.npz whose levelled px falls in an evaluated core; the prediction is the levelled
map bilinearly sampled at that levelled px. ALL: every 4th levelled renderable px in the evaluated cores, mapped to
the organizer canvas; the organizer map is sampled bilinearly there. Metrics: hercules.metrics.pixel (auc, pearson).
Bar (pooled): one order r_org_E >= 0.60 and AUC >= 0.90, the other order AUC <= 0.60.
Usage: cv_eval_lev.py plan.json crops_key maps_root out.json [--work /work/cv]"""
import argparse, json, os, sys
import numpy as np
from scipy.ndimage import map_coordinates
sys.path.insert(0, "/home/user/dominion/src"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hercules.metrics.pixel import auc, pearson
from levelmap import lev_px_to_org_px


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("plan"); ap.add_argument("crops_key"); ap.add_argument("maps_root"); ap.add_argument("out")
    ap.add_argument("--work", default="/work/cv"); a = ap.parse_args()
    import tifffile
    plan = json.load(open(a.plan)); crops = plan[a.crops_key]
    res = {"per_crop": [], "pooled": {}}
    pool = {o: dict(pE=[], oE=[], lE=[], pA=[], oA=[]) for o in ("reverse", "forward")}
    for cr in crops:
        k, s = cr["segment"], cr["segment_id"]
        T = json.load(open(f"{a.work}/mesh_lev/{k}/level_transform.json"))
        E = np.load(f"{a.work}/lev_E_{k}.npz")
        org = tifffile.imread(f"{a.work}/org/{s}/inkmap.tif").astype(np.float32) / 255.0
        RL = np.load(f"{a.work}/area_lev_{k}.npy")
        y0, y1, x0, x1 = cr["core"]
        inE = (E["rp"] >= y0) & (E["rp"] < y1) & (E["cp"] >= x0) & (E["cp"] < x1)
        rr, cc = np.nonzero(RL[y0:y1:4, x0:x1:4]); rr = rr * 4 + y0; cc = cc * 4 + x0
        ro, co = lev_px_to_org_px(T, rr, cc)
        okA = (ro >= 0) & (co >= 0) & (ro <= org.shape[0] - 1) & (co <= org.shape[1] - 1)
        oA = map_coordinates(org, np.stack([ro[okA], co[okA]]), order=1)
        oE = org[E["r"][inE], E["c"][inE]]; lE = E["ink"][inE].astype(np.uint8)
        for o in pool:
            m = np.load(f"{a.maps_root}/{o}/{k}/{cr['ry']}_{cr['rx']}/map.npz")["map"]
            pE = map_coordinates(m, np.stack([E["rp"][inE] - cr["ry"], E["cp"][inE] - cr["rx"]]), order=1)
            pA = m[rr[okA] - cr["ry"], cc[okA] - cr["rx"]]
            pool[o]["pE"].append(pE); pool[o]["oE"].append(oE); pool[o]["lE"].append(lE); pool[o]["pA"].append(pA); pool[o]["oA"].append(oA)
            res["per_crop"].append(dict(segment=k, ry=cr["ry"], rx=cr["rx"], order=o, n_E=int(inE.sum()),
                                        auc=auc(pE, lE) if inE.any() else None, r_org_E=pearson(pE, oE) if inE.any() else None,
                                        r_org_all=pearson(pA, oA)))
    for o, d in pool.items():
        pE, oE, lE, pA, oA = (np.concatenate(d[x]) for x in ("pE", "oE", "lE", "pA", "oA"))
        res["pooled"][o] = dict(n_E=int(len(pE)), n_ink_E=int(lE.sum()), auc=auc(pE, lE) if len(pE) else None,
                                r_org_E=pearson(pE, oE) if len(pE) else None, r_lab_E=pearson(pE, lE) if len(pE) else None,
                                r_org_all=pearson(pA, oA), n_all=int(len(pA)))
    P = res["pooled"]; win = None
    for o, other in (("reverse", "forward"), ("forward", "reverse")):
        if P[o]["auc"] is not None and P[o]["r_org_E"] >= 0.60 and P[o]["auc"] >= 0.90 and P[other]["auc"] <= 0.60:
            win = o
    res["bar"] = dict(winning_order=win, verdict="PASS" if win else "FAIL")
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res["pooled"]), json.dumps(res["bar"]))


if __name__ == "__main__":
    main()
