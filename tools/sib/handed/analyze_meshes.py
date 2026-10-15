# Provenance: Project HERCULES | owner the owner | [id removed]
"""Per-mesh geometry-predicted mirror state for organizer tifxyz meshes
(geometry + metadata + CT-mask centroid only; no image, render or ink map).

For every mesh: frame parity (root catalogue + zarr axes), r_out from
(a) the CT-mask centroid track (level 4, outlier-rejected, smoothed in z),
(b) the mesh's own normal-line centre (no CT), (c) -text_side for fragments;
chirality vote per source, per-vertex agreement between sources, winding
sense, and the predicted state (native organizer grid legible or not;
orient_for_reading flips). PHerc0841: vertices within 159 vox (144 + one
grid step margin) of any J-window point never vote.

Usage: python analyze_meshes.py OUT_JSON
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import handed as H  # noqa: E402
from hercules.geometry import level_mesh as L  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402
from hercules.pipeline.centre import geometric_centre_curve  # noqa: E402

S3 = Path("/work/handed/s3")
CEN = Path("/work/handed/centroids")
ROOTMETA = json.loads(Path("/work/handed/root_metadata.json").read_text())["samples"]
J_RADIUS = 159.0
META = Path("/work/handed/meta")
# official umbilicus JSONs (volume they were annotated on)
UMB = {("PHerc0139", "20260102150214"): META / "0139_2399.umbilicus.json",
       ("PHerc0125", "20250821151825"): META / "20250821151825-umbilicus-20260808111524.json",
       ("PHerc0211", "20250821151803"): META / "20250821151803-umbilicus-20260808112626.json",
       ("PHerc0826", "20250821151701"): META / "20250821151701-umbilicus-20260808113303.json"}


def affine(scroll: str, frm: str, to: str) -> np.ndarray | None:
    for vt in (ROOTMETA[scroll]["sample"]["properties"].get("volume_transforms") or []):
        if vt["from_volume_id"] == frm:
            for t in vt["transforms"]:
                if t["to_volume_id"] == to:
                    return np.array(t["matrix"], float)
    return None


def umbilicus_curve(scroll: str, vol_id: str) -> tuple[L.CentreCurve | None, dict]:
    """Official umbilicus on vol_id: native, or mapped from another volume of
    the same scroll by the organizer affine (x, y, z, 1) -> (x', y', z')."""
    for (sc, v), f in UMB.items():
        if sc != scroll:
            continue
        cp = json.loads(f.read_text())["control_points"]
        P = np.array([[c["x"], c["y"], c["z"]] for c in cp], float)
        info = dict(file=f.name, annotated_on=v, n_points=len(cp))
        if v != vol_id:
            A = affine(scroll, v, vol_id)
            if A is None:
                continue
            P = P @ A[:, :3].T + A[:, 3]
            info.update(mapped_to=vol_id, affine_det=float(np.linalg.det(A[:, :3])))
        o = np.argsort(P[:, 2])
        return L.CentreCurve(z=P[o, 2], x=P[o, 0], y=P[o, 1]), info
    return None, {}


def vol_props(scroll: str, vol_id: str) -> dict:
    return (ROOTMETA[scroll]["volumes"][vol_id].get("properties") or {})


def centroid_curve(scroll: str, sigma: float = 256.0) -> tuple[L.CentreCurve | None, dict]:
    f = CEN / f"{scroll}.json"
    if not f.exists():
        return None, {"error": "no centroid track"}
    d = json.loads(f.read_text())
    sl = [s for s in d["slices"] if s["cx"] is not None and s["n"] > 0]
    area = np.array([s["n"] for s in sl], float)
    med = np.median(area)
    keep = (area > 0.2 * med) & (area < 2.5 * med)  # drop unmasked full-FOV and near-empty end slices
    z = np.array([s["z"] for s in sl], float)[keep]
    cx = np.array([s["cx"] for s in sl], float)[keep]
    cy = np.array([s["cy"] for s in sl], float)[keep]
    ar = np.array([s["axis_ratio"] for s in sl], float)[keep]
    sx, sy = H.gauss_smooth(z, cx, sigma), H.gauss_smooth(z, cy, sigma)
    jit = np.hypot(cx - sx, cy - sy)
    info = dict(volume=d["volume"], voxel_um_metadata=d["voxel_size_um_from_metadata"], n_slices=int(len(sl)),
                n_used=int(keep.sum()), n_rejected_area=int((~keep).sum()), level=d["level"], zstride_level=d["zstride"],
                sigma_vox=sigma, axis_ratio_median=float(np.median(ar)), axis_ratio_p10=float(np.percentile(ar, 10)),
                jitter_median_vox=float(np.median(jit)), jitter_p90_vox=float(np.percentile(jit, 90)),
                mask_radius_median_vox=float(np.median(np.sqrt(area[keep] / np.pi)) * 2 ** d["level"]),
                z_range=[float(z.min()), float(z.max())], hashes=d["hashes"], excluded=d.get("exclude"),
                n_excluded_pixels=int(sum(s.get("n_excluded", 0) for s in d["slices"])))
    return L.CentreCurve(z=z, x=sx, y=sy), info


def best_winding(points, centre, keep):
    a = H.winding_sense(points, centre, keep=keep)
    b = H.winding_sense(np.ascontiguousarray(np.swapaxes(points, 0, 1)), centre,
                        keep=None if keep is None else np.ascontiguousarray(keep.T))
    a["axis"], b["axis"] = "rows(u)", "cols(v)"
    return a if a["max_row_span_turns"] >= b["max_row_span_turns"] else b


def analyze(scroll: str, seg: str, tif_dir: Path, vol_id: str, jtree=None) -> dict:
    m = read_tifxyz(tif_dir)
    p = m.points.astype(np.float64)
    ok = valid_mask(p)
    props = vol_props(scroll, vol_id)
    zattrs = {"multiscales": [{"axes": [{"name": "z"}, {"name": "y"}, {"name": "x"}]}]}
    cinfo_path = CEN / f"{scroll}.json"
    if cinfo_path.exists() and vol_id in json.loads(cinfo_path.read_text())["volume"]:
        zattrs = json.loads(cinfo_path.read_text())["zattrs"]
    fi = H.frame_info(zattrs, props)
    sample_type = ROOTMETA[scroll]["sample"]["properties"].get("type")
    keep = None
    rec = dict(scroll=scroll, segment=seg, tifxyz=str(tif_dir.relative_to(S3)), volume_id=vol_id, sample_type=sample_type,
               grid_shape=list(p.shape[:2]), scale=list(m.scale), n_valid=int(ok.sum()),
               frame=dict(parity=fi.parity, axes=fi.axes, left_handed=fi.left_handed_flag,
                          z_top_to_bottom=fi.z_top_to_bottom, text_side=props.get("text_side"), notes=fi.notes))
    if jtree is not None:
        d, _ = jtree.query(np.where(ok[..., None], p, 1e9).reshape(-1, 3), distance_upper_bound=J_RADIUS)
        keep = (~np.isfinite(d)).reshape(ok.shape) & ok
        rec["j_exclusion"] = dict(radius_vox=J_RADIUS, n_kept=int(keep.sum()), frac_kept=float(keep.sum() / max(ok.sum(), 1)))
        if keep.sum() == 0:
            rec["flags"] = ["all vertices within the J exclusion"]
            return rec
    sources = {}
    cc, cinfo = centroid_curve(scroll)
    if cc is not None and vol_id in cinfo.get("volume", ""):
        sources["centroid"] = cc
    elif cc is not None:
        cinfo = {"note": f"centroid track is for {cinfo.get('volume')}, not volume {vol_id}; not used"}
    try:
        pp = p if keep is None else np.where(keep[..., None], p, -1.0)
        gc, ginfo = geometric_centre_curve(pp.astype(np.float32), z_bin_vox=400.0, min_vertices=50, stride=2)
        sources["geometric"] = gc
        rec["geometric_centre"] = dict(n_bands=len(ginfo["z"]), cond_median=float(np.median(ginfo["cond"])))
    except Exception as e:  # noqa: BLE001
        rec["geometric_centre"] = dict(error=repr(e))
    uc, uinfo = umbilicus_curve(scroll, vol_id)
    if uc is not None:
        sources["umbilicus"] = uc
        rec["umbilicus_info"] = uinfo
    ts = H.text_side_vector(props.get("text_side"))
    if ts is not None:
        sources["text_side"] = -ts
    rec["centroid_info"] = cinfo
    rec["chirality"] = {k: H.chirality_stats(p, v, keep=keep) for k, v in sources.items()}
    agree = {}
    names = [k for k in ("umbilicus", "centroid", "geometric") if k in sources]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            agree[f"{names[i]}_vs_{names[j]}"] = H.sign_agreement(p, sources[names[i]], sources[names[j]], keep=keep)
    rec["source_agreement"] = agree
    # primary source: fragments -> text_side; scrolls -> centroid, else geometric
    if sample_type == "fragment" and "text_side" in sources:
        prim = "text_side"
    elif "umbilicus" in sources:
        prim = "umbilicus"
    elif "centroid" in sources:
        prim = "centroid"
    elif "geometric" in sources:
        prim = "geometric"
    else:
        prim = None
    if prim is None:
        rec["flags"] = ["no r_out source"]
        return rec
    pred = H.predict_mesh(seg, p, sources[prim], fi, r_out_source=prim, keep=keep)
    ag = [a["agree"] for a in agree.values() if a.get("n", 0) > 0]
    # cross-source sign consistency of the whole-mesh votes
    # a fragment has no umbilicus: centroid / normal-line centres are informational only there
    voting = ["text_side"] if prim == "text_side" else [k for k in ("umbilicus", "centroid", "geometric") if k in sources]
    rec["voting_sources"] = voting
    votes = {k: v["sign"] for k, v in rec["chirality"].items() if v["sign"] != 0 and k in voting}
    if len(set(votes.values())) > 1:
        pred.flags.append(f"sources disagree on chirality: {votes}")
    conf = H.confidence(pred, ag if prim != "text_side" else [])
    if prim == "text_side" and conf == "HIGH":
        conf = "MEDIUM"  # single declared source (organizer text_side), no independent geometric check
    if len(set(votes.values())) > 1:
        conf = "FLAG"
    rec["prediction"] = pred.to_json()
    rec["confidence"] = conf
    if prim != "text_side":
        rec["winding"] = best_winding(p, sources[prim], keep)
        w = rec["winding"]["w"]
        if w and fi.parity:
            rec["winding"]["predicts_top_at_low_z"] = bool(w * fi.parity == 1)
            rec["winding"]["metadata_top_at_low_z"] = fi.z_top_to_bottom
    return rec


def main() -> int:
    out = []
    jt = cKDTree(np.load("/work/handed/j_points_0841.npy"))
    for tif_dir in sorted(S3.glob("*/segments/*/mesh/*.tifxyz")):
        scroll = tif_dir.parts[len(S3.parts)]
        seg = tif_dir.parts[len(S3.parts) + 2]
        vol_id = tif_dir.name.split("-on-")[1].split("-")[0]
        if scroll == "PHerc0009B" and "2.401um" in tif_dir.name:
            continue  # analysed on the 8.64 um frame; the 2.401 um copy differs by a det > 0 affine
        try:
            r = analyze(scroll, seg, tif_dir, vol_id, jtree=jt if scroll == "PHerc0841" else None)
        except Exception as e:  # noqa: BLE001
            r = dict(scroll=scroll, segment=seg, error=repr(e))
        out.append(r)
        pr = r.get("prediction", {})
        print(scroll, seg[:40], r.get("confidence"), pr.get("native_legible"), pr.get("mirror_u_needed"),
              {k: (v["sign"], round(v["agreement"], 3) if v["agreement"] == v["agreement"] else None)
               for k, v in r.get("chirality", {}).items()}, r.get("error", ""), flush=True)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
