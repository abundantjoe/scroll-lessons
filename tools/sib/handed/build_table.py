# Provenance: Project HERCULES | owner the owner | [id removed]
"""Per-volume handedness table (numbers and metadata only).

Columns: acquisition z direction (z_start vs z_end), root-catalogue
z_direction_is_top_to_bottom, zarr axis order, left_handed flag -> parity,
CT-mask centroid reliability (ovality, jitter; offset from the official
umbilicus where one exists, and the fraction of the papyrus cross-section
where the centroid r_out deviates > 60 / > 90 deg from the umbilicus r_out),
mesh-level results, predicted rule and confidence.

Usage: python build_table.py MESH_PRED_JSON OUT_JSON OUT_MD
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_meshes as A  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ELIG = json.loads((ROOT / "data/catalogue/eligible_products.json").read_text())
KNOWN = {"PHerc0139": "20250728140407", "PHerc0841": "20250821151531", "PHerc0009B": "20250521125136"}


def acq(scroll: str, vol_id: str) -> dict:
    v = A.ROOTMETA[scroll]["volumes"][vol_id]
    scan_id = ((v.get("creation") or {}).get("derived_from") or {}).get("id")
    sc = A.ROOTMETA[scroll].get("scans", {}).get(scan_id, {})
    # acquisition block may sit in the scan properties; fall back to the eligible catalogue
    s = json.dumps(sc)
    out = {}
    for k in ("z_start", "z_end", "z_step"):
        i = s.find(f'"{k}": ')
        if i >= 0:
            try:
                out[k] = float(s[i + len(k) + 4:].split(",")[0].split("}")[0])
            except ValueError:
                pass
    return out


def centroid_vs_umbilicus(scroll: str, vol_id: str) -> dict | None:
    cc, info = A.centroid_curve(scroll)
    uc, uinfo = A.umbilicus_curve(scroll, vol_id)
    if cc is None or uc is None or vol_id not in info.get("volume", ""):
        return None
    z0, z1 = max(cc.z.min(), uc.z.min()), min(cc.z.max(), uc.z.max())
    zs = np.linspace(z0, z1, 200)
    ax, ay = cc(zs)
    bx, by = uc(zs)
    d = np.hypot(ax - bx, ay - by)
    R = info["mask_radius_median_vox"]
    rng = np.random.default_rng(0)
    # papyrus cross-section model: uniform in an annulus 0.15 R .. R about the umbilicus
    n = 20000
    rr = R * np.sqrt(rng.uniform(0.15 ** 2, 1.0, n))
    th = rng.uniform(0, 2 * np.pi, n)
    zi = rng.integers(0, zs.size, n)
    px, py = bx[zi] + rr * np.cos(th), by[zi] + rr * np.sin(th)
    u = np.stack([px - bx[zi], py - by[zi]], 1)
    c = np.stack([px - ax[zi], py - ay[zi]], 1)
    cosang = np.sum(u * c, 1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(c, axis=1))
    ang = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
    return dict(z_overlap=[float(z0), float(z1)], offset_median_vox=float(np.median(d)), offset_p90_vox=float(np.percentile(d, 90)),
                offset_over_radius_median=float(np.median(d) / R), frac_area_err_gt60=float((ang > 60).mean()),
                frac_area_err_gt90=float((ang > 90).mean()), umbilicus=uinfo)


def main() -> int:
    mp = json.loads(Path(sys.argv[1]).read_text())
    rows = []
    vols = [(v["scroll"], v["volume_id"], True) for v in ELIG["volumes"]] + [(s, v, False) for s, v in KNOWN.items()]
    for scroll, vol_id, eligible in vols:
        props = A.vol_props(scroll, vol_id)
        cpath = A.CEN / f"{scroll}.json"
        cj = json.loads(cpath.read_text()) if cpath.exists() else {}
        fi = A.H.frame_info(cj.get("zattrs"), props)
        a = acq(scroll, vol_id)
        if not a and eligible:
            kf = next(v for v in ELIG["volumes"] if v["volume_id"] == vol_id)["key_fields"]
            a = {k: kf.get(k) for k in ("z_start", "z_end", "z_step")}
        zdir = None
        if a.get("z_start") is not None and a.get("z_end") is not None:
            zdir = "ascending" if a["z_end"] > a["z_start"] else "descending"
        _, cinfo = A.centroid_curve(scroll)
        cu = centroid_vs_umbilicus(scroll, vol_id)
        has_umb = any(sc == scroll for (sc, _v) in A.UMB)
        meshes = [m for m in mp if m["scroll"] == scroll and vol_id in m.get("tifxyz", "")]
        conf_counts = {}
        for m in meshes:
            conf_counts[m.get("confidence")] = conf_counts.get(m.get("confidence"), 0) + 1
        leg = sorted({str(m.get("prediction", {}).get("native_legible")) for m in meshes})
        wind = [m["winding"] for m in meshes if m.get("winding", {}).get("w")]
        wcons = [w["predicts_top_at_low_z"] == w["metadata_top_at_low_z"] for w in wind if w.get("metadata_top_at_low_z") is not None]
        ar = cinfo.get("axis_ratio_median")
        # centroid reliability class
        if cu is not None:
            rel = "validated vs umbilicus" + (" (GOOD)" if cu["frac_area_err_gt60"] < 0.05 else " (POOR)")
        elif ar is None:
            rel = "no centroid"
        else:
            rel = "LOW (oval/crushed)" if ar < 0.5 or scroll in ("PHerc0846A", "PHerc0125") else ("MEDIUM" if ar < 0.75 else "GOOD (round)")
        sample_type = A.ROOTMETA[scroll]["sample"]["properties"].get("type")
        if sample_type == "fragment":
            r_src = f"-text_side ({props.get('text_side')})" if props.get("text_side") else "none (fragment without text_side): FLAG"
        else:
            r_src = "official umbilicus" if has_umb else ("CT-mask centroid L4 (z-smoothed) + mesh normal-line centre cross-check")
        up = {True: "image top = low z", False: "image top = high z", None: "up/down UNKNOWN (180 deg ambiguity only)"}[fi.z_top_to_bottom]
        rule = (f"convention_sign = {fi.parity:+d} (orient_for_reading: det[dP/du, dP/dv, r_out] = {fi.parity:+d}); {up}"
                if fi.parity else "parity unknown: FLAG")
        # confidence of the RULE for this volume (mesh-independent)
        if fi.parity == 0:
            conf = "FLAG"
        elif sample_type == "fragment":
            conf = "MEDIUM" if props.get("text_side") else "FLAG"
        elif has_umb:
            conf = "HIGH"
        elif rel.startswith("LOW"):
            conf = "LOW (centroid unreliable: per-mesh cross-check required; flag disagreeing meshes)"
        else:
            conf = "MEDIUM (centroid; per-mesh cross-check with the mesh normal-line centre)"
        rows.append(dict(scroll=scroll, volume_id=vol_id, eligible=eligible, sample_type=sample_type,
                         voxel_um_metadata=cj.get("voxel_size_um_from_metadata"), acquisition=a, z_direction_acq=zdir,
                         z_top_to_bottom=fi.z_top_to_bottom, axes=fi.axes, left_handed=fi.left_handed_flag, parity=fi.parity,
                         text_side=props.get("text_side"), has_umbilicus=has_umb, centroid=dict(
                             axis_ratio_median=ar, axis_ratio_p10=cinfo.get("axis_ratio_p10"),
                             jitter_median_vox=cinfo.get("jitter_median_vox"), n_used=cinfo.get("n_used"),
                             n_rejected=cinfo.get("n_rejected_area"), mask_radius_vox=cinfo.get("mask_radius_median_vox"),
                             n_excluded_pixels=cinfo.get("n_excluded_pixels")),
                         centroid_vs_umbilicus=cu, centroid_reliability=rel, r_out_source=r_src, rule=rule,
                         rule_confidence=conf, n_meshes=len(meshes), mesh_confidence=conf_counts,
                         meshes_native_legible=leg, winding_checks=len(wind), winding_consistent=int(sum(wcons)),
                         winding_inconsistent=int(len(wcons) - sum(wcons))))
    Path(sys.argv[2]).write_text(json.dumps(rows, indent=1, default=float))
    L = ["| Scroll | Volume | Elig. | z acq. | top-to-bottom | axes / left-handed -> parity | centroid reliability | r_out source | predicted rule | rule confidence | organizer meshes (confidence) | winding check |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cu = r["centroid_vs_umbilicus"]
        crel = r["centroid_reliability"]
        if cu:
            crel += f"; offset/R {cu['offset_over_radius_median']:.3f}, area err>60deg {cu['frac_area_err_gt60']:.3f}"
        elif r["centroid"]["axis_ratio_median"] is not None:
            crel += f"; axis ratio {r['centroid']['axis_ratio_median']:.2f}"
        mc = ", ".join(f"{k} {v}" for k, v in sorted(r["mesh_confidence"].items(), key=lambda kv: str(kv[0]))) or "none"
        wc = f"{r['winding_consistent']}/{r['winding_checks']} consistent" if r["winding_checks"] else "n/a (< 1 turn)" if r["n_meshes"] else "n/a"
        L.append(f"| {r['scroll']} | {r['volume_id']} | {'yes' if r['eligible'] else 'no'} | {r['z_direction_acq']} | {r['z_top_to_bottom']} | "
                 f"{','.join(r['axes'])} / {r['left_handed']} -> {r['parity']:+d} | {crel} | {r['r_out_source']} | {r['rule']} | "
                 f"{r['rule_confidence']} | {r['n_meshes']}: {mc} | {wc} |")
    Path(sys.argv[3]).write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
