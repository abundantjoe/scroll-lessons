# Provenance: Project HERCULES | owner the owner | [id removed]
"""PHercParis4 reading orientation of the organizer canvases (DECL-HANDED-GEOM rule). Numbers only.

Canvas convention: canvas pixel (row, col) <-> grid g = (c + 0.5) * scale (monotone), so a tile
"as rendered" (canvas row down, column right) has u = grid column, v = grid row.
Per mesh: the packaged rule (hercules.geometry.handed_rule.orient_for_reading) with r_out from the
official umbilicus (native on 20260411134726; mapped to 20260608103018 by the organizer affine,
det > 0) and the normal-line centre; the F5 winding check; per-tile chirality on the canvas tile
grid (T px; tile (r, c) = canvas [r T, (r+1) T) x [c T, (c+1) T)); row-0 z and column-0 radius.
Usage: p4orient.py OUT_JSON [FRAME_JSON ...]  (ct_occupancy.py outputs; 2.4 um and 1.129 um)
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
import hercules.geometry  # noqa: E402,F401

spec = importlib.util.spec_from_file_location("hercules.geometry.handed_rule",
                                              HERE / "pkg/src/hercules/geometry/handed_rule.py")
HR = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = HR
spec.loader.exec_module(HR)
from hercules.geometry.level_mesh import CentreCurve, chirality_map  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

S3 = Path("/work/handed/s3/PHercParis4/segments")
META = Path("/work/handed/meta/p4")
UMB = Path("/work/handed/s3/PHercParis4/umb/20260411134726-umbilicus-20260524235033.json")
ROOTMETA = json.loads(Path("/work/handed/root_metadata.json").read_text())["samples"]["PHercParis4"]
V24, V11 = "20260411134726", "20260608103018"
T24 = 8343  # strip-a tile (RULES: T = 8343 on the 20260701183124 canvas)
MESHES = [  # (role, segment, volume, tile px, grid decimation k: every k-th row and column, memory only)
    ("strip-a (P4-B strip a / E2 grid)", "20260701183124-w010-027", V24, T24, 1),
    ("M2a / E1 grid", "20260623141924-w010-027", V11, None, 3),
    ("M2a segment on the 2.4 um frame (cross-check)", "20260623141924-w010-027", V24, None, 1),
    ("known-text control w028-037", "20260701183125-w028-037", V24, T24, 1),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def affine(frm: str, to: str) -> np.ndarray:
    for vt in ROOTMETA["sample"]["properties"]["volume_transforms"]:
        if vt["from_volume_id"] == frm:
            for t in vt["transforms"]:
                if t["to_volume_id"] == to:
                    return np.array(t["matrix"], float)
    raise KeyError((frm, to))


def voxel_um(vol: str) -> float:
    """samplePixelSize (mm) from the volume's metadata.json (the first one found), in um."""
    def find(o):
        if isinstance(o, dict):
            if "samplePixelSize" in o:
                return o["samplePixelSize"]
            for k, v in o.items():
                if k != "mosaic_tiles" and (x := find(v)) is not None:
                    return x
        return None
    return float(find(json.loads((META / f"{vol}_metadata.json").read_text()))) * 1000.0


def read_scale(d: Path) -> float:
    return float(json.loads((d / "meta.json").read_text())["scale"][0])


def umbilicus(vol: str):
    cp = json.loads(UMB.read_text())["control_points"]
    P = np.array([[c["x"], c["y"], c["z"]] for c in cp], float)
    info = dict(file=UMB.name, sha256=sha(UMB), annotated_on=V24, n_points=len(cp))
    if vol != V24:
        A = affine(V24, vol)
        P = P @ A[:, :3].T + A[:, 3]
        info.update(mapped_to=vol, affine_det=float(np.linalg.det(A[:, :3])))
    o = np.argsort(P[:, 2])
    return CentreCurve(z=P[o, 2], x=P[o, 0], y=P[o, 1]), info


def volume_info(vol: str, uc) -> tuple:
    zattrs = json.loads((META / f"{vol}_zattrs").read_text())
    props = dict(ROOTMETA["volumes"][vol]["properties"])
    carried = None
    if props.get("z_direction_is_top_to_bottom") is None and vol != V24:
        A = affine(vol, V24)[:, :3]
        ez = A @ np.array([0, 0, 1.0])
        ez /= np.linalg.norm(ez)
        tb24 = ROOTMETA["volumes"][V24]["properties"]["z_direction_is_top_to_bottom"]
        if abs(ez[2]) > 0.9 and tb24 is not None:
            props["z_direction_is_top_to_bottom"] = bool(tb24) if ez[2] > 0 else (not bool(tb24))
            carried = dict(from_volume=V24, tb_source=tb24, plus_z_maps_to_unit=ez.tolist(),
                           det_affine=float(np.linalg.det(A)), note="MEDIUM, carried through the organizer affine")
    vi = HR.VolumeInfo.from_metadata(zattrs, props, sample_type="scroll", umbilicus=uc, name=f"PHercParis4/{vol}")
    return vi, dict(left_handed_coordinates=props.get("left_handed_coordinates"),
                    z_direction_is_top_to_bottom=props.get("z_direction_is_top_to_bottom"),
                    tb_carried=carried, axes=[a["name"] for a in zattrs["multiscales"][0]["axes"]],
                    parity=vi.parity, voxel_um_metadata_json=voxel_um(vol))


def main() -> None:
    frames = {}
    for fj in sys.argv[2:]:
        d = json.loads(Path(fj).read_text())
        vol = next(v for v in (V24, V11) if v in d["volume"])
        for m in d["meshes"]:
            frames[(m["segment"], vol)] = HR.FrameCheck(m.get("frac_zero_ct_inside", m["frac_zero_ct"]) if vol == V11
                                                        else m["frac_zero_ct"], m["frac_outside"])
    out = dict(rule="DECL-HANDED-GEOM (tools/sib/handed/pkg/src/hercules/geometry/handed_rule.py)",
               rule_sha256=sha(HERE / "pkg/src/hercules/geometry/handed_rule.py"), meshes=[])
    for role, seg, vol, T, k in MESHES:
        d = next((S3 / seg / "mesh").glob(f"{seg.split('-')[0]}-on-{vol}-*.tifxyz"))
        m = read_tifxyz(d)
        p = np.array(m.points[::k, ::k], np.float64)
        del m
        ok = valid_mask(p)
        s = float(read_scale(d))
        vox = None
        uc, uinfo = umbilicus(vol)
        vi, vinfo = volume_info(vol, uc)
        vox = vinfo["voxel_um_metadata_json"]
        # level-0 bounds (zarr axes z, y, x); the 1.129 um volume is an ROI mosaic that the mesh overhangs
        shp = json.loads((META / f"{vol}_0_zarray").read_text())["shape"]
        inside = ok & (p[..., 0] >= 0) & (p[..., 1] >= 0) & (p[..., 2] >= 0) & \
            (p[..., 0] < shp[2]) & (p[..., 1] < shp[1]) & (p[..., 2] < shp[0])
        frac_out = float(1 - inside.sum() / max(ok.sum(), 1))
        fr = frames.get((seg, vol))
        keep = None
        if vol == V11 and fr is not None:
            # deviation, declared: the whole-mesh outside gate is replaced by excluding the outside vertices
            # (keep); the zero-CT gate is applied to the inside vertices only (frac_zero_ct_inside)
            keep = inside
            fr = HR.FrameCheck(fr.frac_zero_ct, 0.0)
        dec = HR.orient_for_reading(p, vi, frame=fr, keep=keep)
        # geometry of the canvas axes
        H, W = p.shape[:2]
        rows = np.arange(H)
        zr = np.array([np.median(p[i, ok[i], 2]) if ok[i].any() else np.nan for i in rows])
        cx, cy = uc(p[..., 2])
        rad = np.where(ok, np.hypot(p[..., 0] - cx, p[..., 1] - cy), np.nan)
        rc = np.nanmedian(rad, axis=0)
        cols_ok = np.nonzero(np.isfinite(rc))[0]
        rows_ok = np.nonzero(np.isfinite(zr))[0]
        dzr = np.diff(zr)
        wind = HR.winding_sense(p, uc)
        up = HR.up_from_winding(wind["w"], vi.parity)
        # per-tile chirality on the canvas tile grid
        Tt = T or int(round(T24 * 2.4 / vox))
        cm = chirality_map(p, uc)
        cy_, cx_ = np.mgrid[0:H, 0:W]
        tr, tc = ((cy_ * k / s - 0.5) // Tt).astype(int), ((cx_ * k / s - 0.5) // Tt).astype(int)
        clear = ok & np.isfinite(cm) & (np.abs(np.nan_to_num(cm)) > HR.MIN_ABS_DET)
        tiles = []
        for (a, b) in sorted({(int(x), int(y)) for x, y in zip(tr[clear], tc[clear])}):
            sel = clear & (tr == a) & (tc == b)
            c = cm[sel]
            if c.size >= 50:
                tiles.append(dict(r=a, c=b, n=int(c.size), frac_pos=float((c > 0).mean())))
        fp = np.array([t["frac_pos"] for t in tiles])
        src = {k: ({kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} if isinstance(v, dict) else v)
               for k, v in dec.sources.items()}
        r = dict(role=role, segment=seg, volume=vol, mesh_dir=d.name, meta_sha256=sha(d / "meta.json"),
                 xyz_sha256={a: sha(d / f"{a}.tif") for a in "xyz"}, grid_hw_analysed=[H, W], scale=s,
                 canvas_hw=[int(round(H * k / s)), int(round(W * k / s))], tile_px=Tt, decimation=k,
                 tile_px_note=None if T else "T scaled from 8343 at 2.4 um by the metadata voxel ratio (approximate)",
                 volume_info=vinfo, umbilicus=uinfo,
                 frame=(vars(fr) if fr is not None else None), level0_shape_zyx=shp, frac_valid_outside_volume=frac_out,
                 keep_rule=("inside the level-0 volume bounds (ROI mosaic)" if keep is not None else None),
                 canvas_axes=dict(
                     row0_median_z_vox=float(zr[rows_ok[0]]), rowlast_median_z_vox=float(zr[rows_ok[-1]]),
                     row0_z_mm=float(zr[rows_ok[0]] * vox / 1000), rowlast_z_mm=float(zr[rows_ok[-1]] * vox / 1000),
                     frac_row_steps_z_decreasing=float((dzr[np.isfinite(dzr)] < 0).mean()),
                     col0_median_radius_mm=float(rc[cols_ok[0]] * vox / 1000),
                     collast_median_radius_mm=float(rc[cols_ok[-1]] * vox / 1000),
                     spearman_col_vs_radius=float(np.corrcoef(np.argsort(np.argsort(cols_ok)), np.argsort(np.argsort(rc[cols_ok])))[0, 1])),
                 decision=dict(state=dec.state, confidence=dec.confidence, convention_sign=dec.convention_sign,
                               chirality=dec.chirality, mirror_u=dec.mirror_u, flip_v=dec.flip_v,
                               rot180_equivalent=dec.rot180_equivalent, reversed_frac=dec.reversed_frac,
                               kept_frac=(float(dec.keep.sum() / max(ok.sum(), 1)) if dec.keep is not None else None),
                               sources=src, flags=dec.flags),
                 winding_F5=wind | dict(text_top_at_low_z_predicted=up,
                                        consistent_with_tb_flag=(None if up is None or vi.z_top_to_bottom is None
                                                                 else bool(up == vi.z_top_to_bottom))),
                 tiles=dict(n=len(tiles), n_majority_pos=int((fp > 0.5).sum()), n_majority_neg=int((fp < 0.5).sum()),
                            min_agreement_with_mesh_sign=(float(np.min(fp if dec.chirality > 0 else 1 - fp)) if len(fp) else None),
                            per_tile=tiles))
        out["meshes"].append(r)
        print(role, "|", dec.state, dec.confidence, "chir", dec.chirality, "conv", dec.convention_sign, "mirror_u", dec.mirror_u,
              "flip_v", dec.flip_v, "| rows z", round(r["canvas_axes"]["row0_z_mm"], 1), "->", round(r["canvas_axes"]["rowlast_z_mm"], 1),
              "| cols r", round(r["canvas_axes"]["col0_median_radius_mm"], 2), "->", round(r["canvas_axes"]["collast_median_radius_mm"], 2),
              "| F5", wind.get("w"), up, "| tiles", r["tiles"]["n"], r["tiles"]["min_agreement_with_mesh_sign"], "|", "; ".join(dec.flags)[:200],
              flush=True)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
