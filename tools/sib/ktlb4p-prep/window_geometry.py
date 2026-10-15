# Provenance: Project HERCULES | owner the owner | [id removed]
"""Geometry package for the 20 independent 0500P2 windows (numbers only; no render read).
Per window: segment tifxyz (9.362 um) and file sha256s, organizer-canvas box, grid sub-box, 3-D bbox and
centre, levelling (level_mesh angle / spread), flips for BOTH declared mirror states (A: organizer
text_side convention, chirality +1 w.r.t. n_out = -text_side carried to 9 um; B: A mirrored in u), up/down
(image top = low z, carried from 4.317 um), and the mapped box on the 2.215 um reference canvas under the
frozen registration (model_final.json affine + field_final.json linear RBF). Usage: window_geometry.py OUT_JSON"""
import hashlib, json, os, sys
import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
REPO = "/home/user/dominion"; sys.path.insert(0, f"{REPO}/src")
from hercules.geometry import level_mesh as L  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask, sample_grid, densify  # noqa: E402
S3 = "/work/handed/s3"; R = f"{REPO}/logs/sib/ktlb4p-prep"
cert = json.load(open("/work/k4p/certify.json"))
dl = json.load(open(f"{R}/downloads_meshes.json"))["objects"]
wh = {(r["segment"], r["y0"], r["x0"]): r for r in json.load(open(f"{R}/window_handedness.json"))["rows"]}
n9 = np.array(json.load(open(f"{R}/window_handedness.json"))["text_side_normal_9um"])
mod = json.load(open(f"{R}/reg/model_final.json")); A = np.array(mod["A"]); c = np.array(mod["c"])
fld = json.load(open(f"{R}/reg/field_final.json"))
rbf = RBFInterpolator(np.array(fld["points_p9"]) / 1000.0, np.array(fld["displacements_u9"]), kernel=fld["kind"], degree=1, smoothing=fld["smoothing"])
f = lambda P: (P + rbf(P / 1000.0)) @ A.T + c  # noqa: E731
out = dict(map=dict(model_sha256=hashlib.sha256(open(f"{R}/reg/model_final.json", "rb").read()).hexdigest(),
                    field_sha256=hashlib.sha256(open(f"{R}/reg/field_final.json", "rb").read()).hexdigest()),
           states={"A": "text_side convention: chirality +1 w.r.t. n_out = -text_side (9 um)", "B": "A mirrored in u"},
           updown="image top = low z (carried from 4.317 um, MEDIUM)", mirror_status="FLAG: both states are declared arms", windows=[])
for k, w in enumerate(cert["independent_windows"]):
    seg = w["segment"]; mdir = f"PHerc0500P2/segments/{seg}/mesh/"
    t9 = [d for d in os.listdir(f"{S3}/{mdir}") if d.endswith("9.362um.tifxyz")][0]
    t2 = [d for d in os.listdir(f"{S3}/{mdir}") if d.endswith("2.215um.tifxyz")][0]
    m = read_tifxyz(f"{S3}/{mdir}{t9}"); s = m.scale[0]
    g0, g1 = int(np.floor(w["y0"] * s)), int(np.ceil((w["y0"] + w["h"]) * s)) + 1
    h0, h1 = int(np.floor(w["x0"] * s)), int(np.ceil((w["x0"] + w["w"]) * s)) + 1
    p = m.points[g0:g1, h0:h1].astype(np.float64); ok = valid_mask(p)
    lv = L.level_mesh(p, step_vox=20.0)
    chi = L.chirality(p, -n9)
    z = np.where(ok, p[..., 2], np.nan); trend = float(np.nanmedian(np.diff(z, axis=0)))
    flip_v = bool(trend < 0)  # image top = low z: rows must run with increasing z
    cur = -chi if flip_v else chi
    mirror_A = bool(cur != 1)
    # reference-canvas box under the frozen map (8-px samples of the window)
    cy, cx = np.mgrid[w["y0"] + 4:w["y0"] + w["h"]:8, w["x0"] + 4:w["x0"] + w["w"]:8]
    P = sample_grid(m.points.astype(np.float64), (cy + 0.5) * s, (cx + 0.5) * s); v = valid_mask(P)
    m2 = read_tifxyz(f"{S3}/{mdir}{t2}"); s2 = m2.scale[0]
    d2 = densify(m2.points.astype(np.float64), 5).astype(np.float64); v2 = valid_mask(d2); iy, ix = np.nonzero(v2)
    dist, idx = cKDTree(d2[v2]).query(f(P[v]), distance_upper_bound=8.0); okm = np.isfinite(dist)
    ry = iy[idx[okm]] / (s2 * 5) - 0.5; rx = ix[idx[okm]] / (s2 * 5) - 0.5
    hashes = {fn: dl.get(f"{mdir}{t9}/{fn}", {}).get("sha256") for fn in ("x.tif", "y.tif", "z.tif", "meta.json")}
    out["windows"].append(dict(
        id=f"K4P-{k:02d}", segment=seg, tifxyz_9um=f"{mdir}{t9}", tifxyz_sha256=hashes, canvas_box=dict(y0=w["y0"], x0=w["x0"], h=w["h"], w=w["w"]),
        grid_box=[g0, g1, h0, h1], bbox3d=[p[ok].min(0).tolist(), p[ok].max(0).tolist()], centre3d=p[ok].mean(0).tolist(),
        level_angle_deg=lv.angle_deg, level_spread_deg=lv.spread_deg, z_trend_per_row=trend,
        chirality_textside=int(chi), textside_agreement=wh[(seg, w["y0"], w["x0"])]["text_side"]["agreement"],
        normal_line_centre=wh[(seg, w["y0"], w["x0"])].get("normal_line_centre"),
        orient=dict(A=dict(flip_v=flip_v, mirror_u=mirror_A), B=dict(flip_v=flip_v, mirror_u=not mirror_A)),
        ref_2215um=dict(tifxyz=f"{mdir}{t2}", canvas_bbox_yx=[float(ry.min()), float(rx.min()), float(ry.max()), float(rx.max())] if okm.any() else None,
                        frac_mapped=float(okm.sum() / max(v.sum(), 1)), map_dist_median_2um_vox=float(np.median(dist[okm])) if okm.any() else None),
        coverage=dict(mesh_valid=w["mesh_valid"], ref_mapped=w["ref_mapped"], zero_ct_frac=w["zero_ct_frac"]), unit=w["unit"]))
    r = out["windows"][-1]; print(r["id"], seg[:22], r["orient"], round(r["level_spread_deg"], 1), round(r["ref_2215um"]["frac_mapped"], 3), flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
