# Provenance: Project HERCULES | owner the owner | [id removed]
"""Aggregate census outputs into logs/sib/census/census.json (+ per-volume
seeds and sync plans). REPORT.md is written by hand from census.json."""
from __future__ import annotations

import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from centre import centroid_curve, interp_curve, load_shape, reliability, scroll_z_extent, umbilicus_curve  # noqa: E402
from sync_plan import plan as sync_plan  # noqa: E402

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
VOLS = ["0125", "0191", "0211", "0257", "0358", "0813", "0826", "0846A", "0846B", "1203", "1545"]
W = "/work/census"
OUT = "logs/sib/census"
RESCAN = {"1203", "0846A"}


def lin(v, lo, hi):
    return float(np.clip((v - lo) / (hi - lo), 0, 1))


def main():
    cat = json.load(open("data/catalogue/eligible_products.json"))
    prod = json.load(open(f"{W}/products/products.json"))
    umbidx = json.load(open(f"{W}/umb/umbilicus_index.json"))
    os.makedirs(f"{OUT}/seeds", exist_ok=True)
    os.makedirs(f"{OUT}/sync", exist_ok=True)
    res = dict(provenance=PROV, volumes={})
    # centroid calibration against official umbilici
    calib = {}
    for k, u in umbidx.items():
        scroll = k.split("/")[0]
        sh = load_shape(f"{W}/mask", scroll)
        uz, ux, uy, _ = umbilicus_curve(f"{W}/umb/" + k.rsplit("/", 1)[-1])
        zc, xc, yc, ok = centroid_curve(sh)
        sel = (uz >= zc[0]) & (uz <= zc[-1])
        cx, cy = interp_curve(zc, xc, yc, uz[sel])
        e = np.hypot(cx - ux[sel], cy - uy[sel])
        req = np.interp(uz[sel], sh["z"], sh["r_eq"])
        calib[scroll] = dict(n_points=int(sel.sum()), err_vox_p50=float(np.median(e)), err_vox_p90=float(np.percentile(e, 90)),
                             err_vox_max=float(e.max()), err_rel_req_p50=float(np.median(e / req)),
                             err_rel_req_p90=float(np.percentile(e / req, 90)), umbilicus_sha256=u["sha256"])
    res["centroid_vs_umbilicus"] = calib
    res["m7_normal_line_centre_negative_result"] = {}
    for scroll in ("PHerc0125", "PHerc0211"):
        for L in (3, 2):
            fn = f"{W}/m7c/{scroll}_m7centre_L{L}.npz"
            if not os.path.exists(fn):
                continue
            d = np.load(fn)
            k = [kk for kk in umbidx if kk.startswith(scroll)][0]
            uz, ux, uy, _ = umbilicus_curve(f"{W}/umb/" + k.rsplit("/", 1)[-1])
            sel = (d["z"] >= uz[0]) & (d["z"] <= uz[-1])
            e = np.hypot(d["cx"][sel] - np.interp(d["z"][sel], uz, ux), d["cy"][sel] - np.interp(d["z"][sel], uz, uy))
            res["m7_normal_line_centre_negative_result"][f"{scroll}_L{L}"] = dict(n=int(sel.sum()), err_vox_p50=float(np.median(e)),
                                                                             err_vox_p90=float(np.percentile(e, 90)))
    for f, key in (("valwalk_h4.json", "walker_v1"), ("valwalk_v2.json", "walker_v2_step4_shift3"),
                   ("valwalk_v2s2.json", "walker_v2_step2_shift1")):
        if os.path.exists(f"{W}/{f}"):
            d = json.load(open(f"{W}/{f}"))
            P = np.array([abs(p["pos_dr"]) for p in d["pairs"] if p["pos_dr"] is not None])
            N = np.array([abs(p["neg_dr"]) for p in d["pairs"] if p.get("neg_dr") is not None])
            auc = float(np.mean([[1.0 if p < n else 0.5 if p == n else 0.0 for n in N] for p in P])) if len(P) and len(N) else None
            s = {k: v for k, v in d["summary"].items()}
            s["auc_pos_smaller_absdr"] = auc
            res.setdefault("walker_validation", {})[key] = s
            shutil.copy(f"{W}/{f}", f"{OUT}/{f}")
    arc = json.load(open(f"{W}/team1203_dev_meta.json"))
    res["archive_1203_dev_segments"] = {s: dict(sha256_meta=v["sha256"], max_gen=v["meta"].get("max_gen"),
                                                elapsed_time_s=v["meta"].get("elapsed_time_s"), area_cm2=v["meta"].get("area_cm2"),
                                                mode=v["meta"].get("vc_gsfs_mode"), thread_limit=v["meta"].get("vc_gsfs_params", {}).get("thread_limit"),
                                                bbox=v["meta"].get("bbox"), seed=v["meta"].get("seed")) for s, v in arc.items()}
    shutil.copy(f"{W}/team1203_dev_meta.json", f"{OUT}/archive_1203_dev_meta.json")
    rows = []
    for vol in VOLS:
        v = next(x for x in cat["volumes"] if x["scroll"] == "PHerc" + vol)
        scroll = v["scroll"]
        p = prod[vol]
        sh = load_shape(f"{W}/mask", scroll)
        z0, z1, thr = scroll_z_extent(sh)
        zc, xc, yc, ok = centroid_curve(sh)
        rel = reliability(sh, ok)
        kf = v["key_fields"]
        e = dict(scroll=scroll, volume_id=v["volume_id"], voxel_um=kf["samplePixelSize_mm"] * 1000.0,
                 shape_zyx=p["shape_zyx"], m7_zarr=p["m7_zarr"], m7_bytes_total=p["m7_bytes_total"],
                 m7_levels={L: dict(objects=d["objects"], bytes=d["bytes"], shape=d["zarray"]["shape"], chunks=d["zarray"]["chunks"])
                            for L, d in p["m7_levels"].items()},
                 m7_metadata_sha256=p["m7_top_files"].get("metadata.json", {}).get("sha256"),
                 normal_grids=p["normal_grids"], ngrid_bytes_total=p["ngrid_bytes_total"], ngrid_objects=p["ngrid_objects_total"],
                 ngrid_planes=p["ngrid_planes"], ngrid_preview_dirs=p["ngrid_other_dirs"], ngrid_metadata=p["ngrid_metadata"],
                 ngrid_metadata_sha256=p["ngrid_metadata_sha256"],
                 xy_bytes_per_500_band=p["xy_bytes_per_500_band"],
                 lasagna=[dict(prefix=l["prefix"], same_volume=l["same_volume"], ome_zarrs=l["ome_zarrs"], files=l["files"]) for l in p["lasagna"]],
                 umbilicus=p["umbilicus"],
                 axis=dict(z_start_mm=kf["z_start"], z_end_mm=kf["z_end"], z_step=kf["z_step"],
                           acquisition_z=("descending" if kf["z_start"] > kf["z_end"] else "ascending"),
                           root_catalogue_z_direction_is_top_to_bottom=kf.get("root_catalogue_z_direction_is_top_to_bottom")),
                 mask=dict(scroll_z_extent_vox=[z0, z1], **rel))
        # seeds
        sf = f"{W}/seeds/{scroll}_seeds.json"
        if os.path.exists(sf):
            sj = json.load(open(sf))
            shutil.copy(sf, f"{OUT}/seeds/{scroll}_seeds.json")
            shutil.copy(f"{W}/seeds/{scroll}_dup_pairs.json", f"{OUT}/seeds/{scroll}_dup_pairs.json")
            placed = [s for s in sj["seeds"] if s.get("seed_xyz")]
            snaps = np.array([s["snap_dist_vox"] for s in placed])
            allchk = sum(1 for s in placed if all(s["checks"].values()))
            e["seeds"] = dict(file=f"{OUT}/seeds/{scroll}_seeds.json", centre_source=sj["centre_source"], planned=len(sj["seeds"]),
                              placed=len(placed), all_checks_pass=allchk,
                              failed=[s["id"] for s in sj["seeds"] if not s.get("seed_xyz")],
                              snap_vox_p50=float(np.median(snaps)), snap_vox_p90=float(np.percentile(snaps, 90)), snap_vox_max=float(snaps.max()),
                              nudged_fraction=sum(1 for s in placed if s.get("f_nudge") or s.get("theta_nudge_deg")),
                              f_seed_range=[min(s["f_seed"] for s in placed if s.get("f_seed")), max(s["f_seed"] for s in placed if s.get("f_seed"))],
                              duplicates=sj["duplicates"])
            sp = sync_plan(sf, f"{W}/products/{scroll}_ngrid_sizes.npz", f"{W}/team1203_dev_meta.json")
            json.dump(sp, open(f"{OUT}/sync/{scroll}_sync.json", "w"), indent=1)
            e["sync"] = {g: {k: val for k, val in d.items() if k != "per_seed"} for g, d in sp["per_gen"].items()}
            e["sync"]["archive_t75_median_s"] = sp["archive_t75_median_s"]
        res["volumes"][vol] = e
        # ranking components (declared in REPORT.md)
        s = e.get("seeds", {})
        comp = dict(shape=lin(rel["axis_ratio_median"], 0.45, 0.80), crushing=lin(rel["solidity_p10"], 0.60, 0.93),
                    centre=1.0 if any(u["same_volume"] for u in p["umbilicus"]) else (0.5 if rel["axis_ratio_median"] >= 0.7 else 0.25),
                    data=0.5 * (1.0 if any(l["same_volume"] for l in p["lasagna"]) else 0.0)
                    + 0.5 * (1.0 if kf.get("root_catalogue_z_direction_is_top_to_bottom") is not None else 0.0),
                    seeding=(s.get("all_checks_pass", 0) / 60.0) if s else 0.0)
        rows.append(dict(vol=vol, score=float(np.mean(list(comp.values()))), rescan=vol in RESCAN, **comp))
    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows):
        r["rank_raw"] = i + 1
    final = [r for r in rows if not r["rescan"]] + [r for r in rows if r["rescan"]]
    for i, r in enumerate(final):
        r["rank_final"] = i + 1
    res["ranking"] = final
    json.dump(res, open(f"{OUT}/census.json", "w"), indent=1)
    for r in final:
        print(r["rank_final"], r["vol"], round(r["score"], 3), {k: round(r[k], 2) for k in ("shape", "crushing", "centre", "data", "seeding")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
