# Provenance: Project HERCULES | owner the owner | [id removed]
"""CHAIN VALID metrics (DECL-CHAINVALID), numbers only; nothing is displayed.
Per order (reverse, forward): the map of each evaluated crop contributes its inner core (crop minus the 128 px
margin) to a canvas-size array; only renderable px (area_<seg>.npy) inside evaluated cores count.
 E   = renderable & supervision (label_set 20260918): AUC vs ink labels (ink = inklabels 255, blank = 0),
       r_org_E = Pearson with the organizer map, r_lab_E = point-biserial Pearson with the labels.
 ALL = renderable px in evaluated cores: r_org_all = Pearson with the organizer map.
Metrics: src/hercules/metrics/pixel.py (auc, pearson), as chain2um's eval2um.py.
Bar (DECL-CHAINVALID, primary r = r_org_E): one order r >= 0.60 and AUC >= 0.90, the other order AUC <= 0.60.
Usage: cv_eval.py maps_root out.json [--org-root /work/cv/org] [--area-root /work/cv]
maps_root/<order>/<seg>/<y>_<x>/map.npz (infer2um.py output) for every evaluated crop."""
import argparse, glob, json, os, sys
import numpy as np
sys.path.insert(0, "/home/user/dominion/src")
from hercules.metrics.pixel import auc, pearson

SEG = {"w00": "20260220213127-w00", "214732": "20260220214732-auto_grown_20260220144552896", "022814": "20260221022814-auto_grown_20260220174252405"}
M = 128


def load_labels(org_root, s, shape):
    import zarr, tifffile
    ink = zarr.open_array(f"{org_root}/{s}/inklabels.zarr/0", mode="r")[:] > 0
    sup = zarr.open_array(f"{org_root}/{s}/supervision.zarr/0", mode="r")[:] > 0
    org = tifffile.imread(f"{org_root}/{s}/inkmap.tif").astype(np.float32) / 255.0
    assert ink.shape == sup.shape == org.shape == shape
    return ink, sup, org


def stitch(order_dir, shape):
    m = np.zeros(shape, np.float32); cov = np.zeros(shape, bool); crops = []
    for f in sorted(glob.glob(f"{order_dir}/*_*/map.npz")):
        y, x = [int(v) for v in os.path.basename(os.path.dirname(f)).split("_")]
        a = np.load(f)["map"]
        ys, xs = max(y + M, 0), max(x + M, 0); ye, xe = min(y + a.shape[0] - M, shape[0]), min(x + a.shape[1] - M, shape[1])
        m[ys:ye, xs:xe] = a[ys - y:ye - y, xs - x:xe - x]; cov[ys:ye, xs:xe] = True; crops.append([y, x])
    return m, cov, crops


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("maps_root"); ap.add_argument("out")
    ap.add_argument("--org-root", default="/work/cv/org"); ap.add_argument("--area-root", default="/work/cv")
    a = ap.parse_args()
    res = {"segments": {}, "pooled": {}}
    pool = {o: dict(m=[], org=[], lab=[], E=[]) for o in ("reverse", "forward")}
    for k, s in SEG.items():
        if not os.path.isdir(f"{a.maps_root}/reverse/{k}"):
            continue
        R = np.load(f"{a.area_root}/area_{k}.npy")
        ink, sup, org = load_labels(a.org_root, s, R.shape)
        res["segments"][k] = {}
        for o in ("reverse", "forward"):
            m, cov, crops = stitch(f"{a.maps_root}/{o}/{k}", R.shape)
            A = R & cov; E = A & sup; lab = ink.astype(np.uint8)
            res["segments"][k][o] = dict(crops=crops, n_all=int(A.sum()), n_E=int(E.sum()), n_ink_E=int((E & ink).sum()),
                                         auc=auc(m, lab, E) if E.any() else None, r_org_E=pearson(m, org, E) if E.any() else None,
                                         r_lab_E=pearson(m, lab, E) if E.any() else None, r_org_all=pearson(m, org, A))
            pool[o]["m"].append(m[A]); pool[o]["org"].append(org[A]); pool[o]["lab"].append(lab[A]); pool[o]["E"].append(E[A])
        res["segments"][k]["organizer_map_on_E"] = dict(auc=auc(org, ink.astype(np.uint8), R & sup) if (R & sup).any() else None)
    for o in pool:
        m = np.concatenate(pool[o]["m"]); org = np.concatenate(pool[o]["org"]); lab = np.concatenate(pool[o]["lab"]); E = np.concatenate(pool[o]["E"])
        res["pooled"][o] = dict(n_all=int(len(m)), n_E=int(E.sum()), auc=auc(m, lab, E) if E.any() else None,
                                r_org_E=pearson(m, org, E) if E.any() else None, r_lab_E=pearson(m, lab, E) if E.any() else None,
                                r_org_all=pearson(m, org))
    P = res["pooled"]
    win = None
    for o, other in (("reverse", "forward"), ("forward", "reverse")):
        if P[o]["auc"] is not None and P[o]["r_org_E"] >= 0.60 and P[o]["auc"] >= 0.90 and P[other]["auc"] <= 0.60:
            win = o
    res["bar"] = dict(winning_order=win, verdict="PASS" if win else "FAIL",
                      rule="one order r_org_E >= 0.60 and AUC >= 0.90, other order AUC <= 0.60 (pooled over evaluated crops)")
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res["pooled"], indent=1), json.dumps(res["bar"]))


if __name__ == "__main__":
    main()
