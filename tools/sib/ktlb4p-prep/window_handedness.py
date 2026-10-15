# Provenance: Project HERCULES | owner the owner | [id removed]
"""Chirality of each independent window's mesh region (9.362 um frame) under two sources:
(a) organizer text_side of the 4.317 um volume ('-y'), carried to the 9.362 um frame as a normal
    (inverse-transpose of the organizer affine 20250528085330 -> 20250820143440; det > 0);
(b) the window's own normal-line centre (handed_rule.normal_line_centre; valid iff cond <= 10).
Decision per the packaged rule is reported (numbers only). Usage: window_handedness.py CERT_JSON OUT_JSON"""
import importlib.util, json, sys
import numpy as np
REPO = "/home/user/dominion"; sys.path.insert(0, f"{REPO}/src")
import hercules.geometry  # noqa: F401
spec = importlib.util.spec_from_file_location("hercules.geometry.handed_rule", f"{REPO}/tools/sib/handed/pkg/src/hercules/geometry/handed_rule.py")
HR = importlib.util.module_from_spec(spec); sys.modules[spec.name] = HR; spec.loader.exec_module(HR)
from hercules.geometry.level_mesh import chirality_map  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402
import os
S3 = "/work/handed/s3/PHerc0500P2/segments"
d = json.load(open("/work/handed/root_metadata.json"))["samples"]["PHerc0500P2"]
T = next(t for vt in d["sample"]["properties"]["volume_transforms"] if vt["from_volume_id"] == "20250528085330"
         for t in vt["transforms"] if t["to_volume_id"] == "20250820143440")
L = np.array(T["matrix"])[:, :3]
n4 = np.array([0, -1.0, 0])  # text_side '-y' of the 4.317 um volume
n9 = np.linalg.inv(L).T @ n4; n9 /= np.linalg.norm(n9)
cert = json.load(open(sys.argv[1]))
rows = []
for w in cert["independent_windows"]:
    seg = w["segment"]
    d9 = [x for x in os.listdir(f"{S3}/{seg}/mesh") if x.endswith("9.362um.tifxyz")][0]
    m = read_tifxyz(f"{S3}/{seg}/mesh/{d9}"); s = m.scale[0]
    g0, g1 = int(np.floor(w["y0"] * s)), int(np.ceil((w["y0"] + w["h"]) * s)) + 1
    h0, h1 = int(np.floor(w["x0"] * s)), int(np.ceil((w["x0"] + w["w"]) * s)) + 1
    p = m.points[g0:g1, h0:h1].astype(np.float64)
    out = {}
    for name, src in (("text_side", -n9),):
        c = chirality_map(p, src); c = c[np.isfinite(c) & (np.abs(np.nan_to_num(c)) > 0.1)]
        out[name] = dict(sign=int(np.sign(np.sum(np.sign(c)))) if c.size else 0, agreement=float(max((c > 0).mean(), (c < 0).mean())) if c.size else None)
    gc, cond = HR.normal_line_centre(p)
    if gc is not None:
        c = chirality_map(p, gc); c = c[np.isfinite(c) & (np.abs(np.nan_to_num(c)) > 0.1)]
        out["normal_line_centre"] = dict(cond=cond, valid=bool(cond <= HR.COND_MAX), sign=int(np.sign(np.sum(np.sign(c)))) if c.size else 0,
                                         agreement=float(max((c > 0).mean(), (c < 0).mean())) if c.size else None)
    rows.append(dict(segment=seg, y0=w["y0"], x0=w["x0"], **out))
    print(seg[:28], w["y0"], w["x0"], out, flush=True)
json.dump(dict(text_side_normal_9um=n9.tolist(), rows=rows), open(sys.argv[2], "w"), indent=1)
