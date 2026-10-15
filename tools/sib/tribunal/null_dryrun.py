# Provenance: Project HERCULES | owner the owner | [id removed]
"""REAL-TRIB-2 (ii): empirical-null dry run on clean PHerc0139 (coordinates only; PREREG.md).
Geometry, the official m7 surface prediction (sampled along R's normals only) and window lists;
no CT, no ink map, no image.

    python tools/sib/tribunal/null_dryrun.py MESH_ROOT meshes_fetched.json DEV_REGISTRY.json OUT_DIR
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from hercules.geometry.tifxyz import densify, read_tifxyz, sample_grid, valid_mask
from hercules.tribunal import empnull as E

VOL_ID = "20250728140407"
M7 = "vesuvius-challenge-open-data/PHerc0139/representations/predictions/surfaces/" \
     "20250728140407-surface-20260413222639-surface-m7-L0-th0.2.zarr"
BASE = ["w028", "w029", "w030", "w035", "w039", "w040", "w041", "w043", "w044", "w045", "w046"]
R_ORDER = ["w024", "w053", "w047"]
WIN, STRIDE, HALO = 2136, 1068, 64
NEAR = 2.0 + 2.0 * math.sqrt(2.0)
DEV_SEP = 192.0
SAMPLE_PX = 20                      # band-candidate cloud sampling (canvas px)
PAD = SAMPLE_PX * math.sqrt(2) / 2  # max point-to-surface under-estimate from that sampling (fail closed)
SEED = 20260926


def tag_of(sid):
    return sid.split("-")[1].split("_")[0]


def canvas_cloud(p, y0, x0, h, w, step):
    rows = (np.arange(y0, y0 + h, step, dtype=np.float64) + 0.5) / 20.0
    cols = (np.arange(x0, x0 + w, step, dtype=np.float64) + 0.5) / 20.0
    R, Cc = np.meshgrid(rows, cols, indexing="ij")
    g = sample_grid(p, R, Cc)
    v = valid_mask(g)
    return g[v], float(v.mean())


def overlaps(y0, x0, h, w, wins, halo):
    return any(abs((y0 + h / 2) - (a + s / 2)) < (h + s) / 2 + halo and abs((x0 + w / 2) - (b + s / 2)) < (w + s) / 2 + halo
               for a, b, s in wins)


def main():
    root, fetched_p, reg_p, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    fetched = json.loads(fetched_p.read_text())
    ids = {k.split("/")[1]: Path(v["mesh"]) for k, v in fetched["segments"].items()
           if k.startswith("PHerc0139/") and "mesh" in v}
    meshes = {sid: read_tifxyz(p) for sid, p in ids.items()}
    by_tag = {}
    for sid in meshes:
        by_tag.setdefault(tag_of(sid), []).append(sid)
    reg = json.loads(reg_p.read_text())
    sc = reg["scrolls"]["PHerc0139"]
    d1 = json.loads(Path("logs/d1/d1_build_prep.json").read_text())["windows"]
    used = {}  # tag -> [(y0, x0, size)]
    for w in reg["used_windows_0139"]:
        used.setdefault(w["segment"], []).append((w["y0"], w["x0"], w["size"]))
    dev = []
    for w in sc["windows"] + sc["blanks"]:
        used.setdefault(w["segment"], []).append((w["y0"], w["x0"], max(w["h"], w["w"])))
        dev.append(w)
    for k, w in d1.items():
        if w["scroll"] == "PHerc0139":
            ow = w["organizer_window"]
            used.setdefault(w["segment_short"], []).append((ow["y0"], ow["x0"], max(ow["h"], ow["w"])))
    # DEV window clouds (8 px sampling; 3-D check uses DEV_SEP + 8 px bound: fail closed)
    dev_pts = np.concatenate([canvas_cloud(meshes[w["segment_id"]].points.astype(np.float64), w["y0"], w["x0"],
                                           w["h"], w["w"], 8)[0] for w in dev])
    dev_tree = cKDTree(dev_pts)
    dev_pad = 8 * math.sqrt(2) / 2
    base_ids = [s for t in BASE for s in by_tag.get(t, [])]
    base_tree = cKDTree(np.concatenate([(lambda d: d[valid_mask(d)])(densify(meshes[s].points.astype(np.float64), 5))
                                        for s in base_ids]))
    log = {"base_training_traces": base_ids, "n_used_windows": sum(len(v) for v in used.values()),
           "n_dev_windows": len(dev)}
    # ---- mock R (pre-registered rule)
    R = None
    for tag in R_ORDER:
        sid = by_tag[tag][0]
        p = meshes[sid].points.astype(np.float64)
        dn = densify(p, 5)
        vd = valid_mask(dn)
        d, _ = base_tree.query(dn[vd], k=1, distance_upper_bound=NEAR + 1e-9, workers=3)
        rr, cc = np.nonzero(vd)
        bad = np.stack([rr[np.isfinite(d)] * 4.0 - 0.5, cc[np.isfinite(d)] * 4.0 - 0.5], 1)
        Hc, Wc = p.shape[0] * 20, p.shape[1] * 20
        for y0 in range(0, Hc - WIN + 1, STRIDE):
            for x0 in range(0, Wc - WIN + 1, STRIDE):
                if overlaps(y0, x0, WIN, WIN, used.get(tag, []), HALO):
                    continue
                cl, vf = canvas_cloud(p, y0, x0, WIN, WIN, 8)
                if vf < 0.95:
                    continue
                if len(bad) and np.any((bad[:, 0] >= y0 - HALO) & (bad[:, 0] < y0 + WIN + HALO) &
                                       (bad[:, 1] >= x0 - HALO) & (bad[:, 1] < x0 + WIN + HALO)):
                    continue
                if dev_tree.query(cl, k=1)[0].min() < DEV_SEP + dev_pad:
                    continue
                R = {"segment": sid, "tag": tag, "y0": y0, "x0": x0}
                break
            if R:
                break
        if R:
            break
    if R is None:
        raise SystemExit("no mock R satisfies the pre-registered rule")
    p = meshes[R["segment"]].points.astype(np.float64)
    r0 = max(0, int(math.floor((R["y0"] + 0.5) / 20.0)) - 2)
    c0 = max(0, int(math.floor((R["x0"] + 0.5) / 20.0)) - 2)
    r1 = min(p.shape[0], int(math.ceil((R["y0"] + WIN + 0.5) / 20.0)) + 3)
    c1 = min(p.shape[1], int(math.ceil((R["x0"] + WIN + 0.5) / 20.0)) + 3)
    R_pts = p[r0:r1, c0:c1]
    win = {"y0": R["y0"] - 20 * r0, "x0": R["x0"] - 20 * c0, "h": WIN, "w": WIN}  # sub-grid canvas: exact shift
    # ---- centre curve (geometry only) and band candidates
    centre, cdiag = E.centre_from_normals([meshes[s].points for s in meshes], z_band=200.0, stride=4)
    cands = []
    for sid, m in meshes.items():
        if sid in base_ids:
            continue
        tag = tag_of(sid)
        for c in E.grid_tiles(sid, VOL_ID, m.points.astype(np.float64), m.scale, (WIN, WIN), stride_px=STRIDE,
                              min_valid=0.9, sample_px=SAMPLE_PX):
            w = c["window"]
            if overlaps(w["y0"], w["x0"], WIN, WIN, used.get(tag, []), HALO):
                continue
            if dev_tree.query(c["cloud"], k=1)[0].min() < DEV_SEP + dev_pad + PAD:
                continue
            cands.append(c)
    import s3fs
    import zarr
    m7 = zarr.open(s3fs.S3Map(root=M7 + "/0", s3=s3fs.S3FileSystem(anon=True), check=False), mode="r")
    Rspec = {"candidate_id": f"mockR_{R['tag']}_y{R['y0']}_x{R['x0']}", "volume_id": VOL_ID, "segment_id": R["segment"],
             "window": win, "text_direction": "forward"}
    ns = E.build_null_set(Rspec, R_points=R_pts, scale=meshes[R["segment"]].scale, voxel_um=9.362, m7=m7,
                          centre=centre, band_candidates=cands, out_dir=out / "offsheet_meshes", m7_scale=1.0,
                          seed=SEED, pitch_stride=4)
    for t in ns["tiles"]:
        if t["segment_id"] == R["segment"] and t["kind"] != "band_nontext_order":
            t["window_on_organizer_canvas"] = {"y0": R["y0"], "x0": R["x0"], "h": WIN, "w": WIN}
    res = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "rule": "REAL-TRIB-2 (ii), PREREG.md", "not_used": "no CT, no ink map, no image",
           "mock_R": {**R, "subgrid_origin_rc": [r0, c0], "window_on_subgrid_canvas": win},
           "centre_curve": {"method": "least-squares xy normal-line intersection per 200-vox z-band, 3-band median",
                            "bands": len(cdiag), "median_line_dist_vox_median": float(np.median(
                                [d["median_line_dist_vox"] for d in cdiag]))},
           "band_candidates_after_exclusions": len(cands),
           "sampling_note": f"band clouds sampled every {SAMPLE_PX} px; the 192-vox DEV separation is padded by "
                            f"{PAD:.2f} + {dev_pad:.2f} vox (fail closed); separations inside build_null_set use "
                            f"its declared values on these samples",
           **log, "null_set": ns, "seconds": round(time.time() - t0, 1)}
    (out / "null_dryrun.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=float) + "\n")
    print(json.dumps({"status": ns["status"], "n_tiles": ns["n_tiles"], "n_band": ns["n_band"],
                      "pitch": ns["pitch"].get("pitch_vox"), "pitch_n": ns["pitch"].get("n_used"),
                      "mock_R": R, "cands": len(cands), "sec": res["seconds"]}))


if __name__ == "__main__":
    main()
