# Provenance: Project HERCULES | owner the owner | [id removed]
"""Apply the packaged rule (pkg/src/hercules/geometry/handed_rule.py) to the
organizer meshes, with the measured frame checks (logs/sib/handed/h2/
ct_occupancy_*.json). Numbers only. Usage: python apply_rule.py OUT_JSON"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import hercules.geometry  # noqa: E402,F401

spec = importlib.util.spec_from_file_location("hercules.geometry.handed_rule",
                                              HERE / "pkg/src/hercules/geometry/handed_rule.py")
HR = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = HR
spec.loader.exec_module(HR)
import analyze_meshes as A  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

def main() -> None:
    occ = {}
    for f in (ROOT / "logs/sib/handed/h2").glob("ct_occupancy_*.json"):
        d = json.loads(f.read_text())
        for m in d["meshes"]:
            occ[(d["scroll"], m["segment"])] = HR.FrameCheck(m["frac_zero_ct"], m["frac_outside"])
    jt = cKDTree(np.load("/work/handed/j_points_0841.npy"))
    out = []
    for d in sorted(A.S3.glob("*/segments/*/mesh/*.tifxyz")):
        scroll = d.parts[len(A.S3.parts)]
        seg = d.parts[len(A.S3.parts) + 2]
        vol = d.name.split("-on-")[1].split("-")[0]
        if "2.399um" in d.name or "2.401um" in d.name:
            continue
        p = read_tifxyz(d).points.astype(np.float64)
        props = A.vol_props(scroll, vol)
        cj = json.loads((A.CEN / f"{scroll}.json").read_text())
        cc, ci = A.centroid_curve(scroll)
        uc, _ = A.umbilicus_curve(scroll, vol)
        st = A.ROOTMETA[scroll]["sample"]["properties"].get("type") or "scroll"
        vi = HR.VolumeInfo.from_metadata(cj["zattrs"], props, sample_type=st, umbilicus=uc,
                                         centroid=cc if vol in ci.get("volume", "") else None, name=f"{scroll}/{vol}")
        keep = None
        if scroll == "PHerc0841":
            ok = valid_mask(p)
            dd, _ = jt.query(np.where(ok[..., None], p, 1e9).reshape(-1, 3), distance_upper_bound=159.0)
            keep = (~np.isfinite(dd)).reshape(ok.shape) & ok
        dec = HR.orient_for_reading(p, vi, frame=occ.get((scroll, seg)), keep=keep)
        src = {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} if isinstance(v, dict) else v
               for k, v in dec.sources.items()}
        out.append(dict(scroll=scroll, segment=seg, volume=vol, state=dec.state, confidence=dec.confidence,
                        convention_sign=dec.convention_sign, chirality=dec.chirality, mirror_u=dec.mirror_u,
                        flip_v=dec.flip_v, rot180_equivalent=dec.rot180_equivalent,
                        reversed_frac=dec.reversed_frac, frame=(vars(occ[(scroll, seg)]) if (scroll, seg) in occ else None),
                        kept_frac=(float(dec.keep.sum() / max(valid_mask(p).sum(), 1)) if dec.keep is not None else None),
                        sources=src, flags=dec.flags))
        r = out[-1]
        print(scroll, seg[:22], r["state"], r["confidence"], r["mirror_u"], r["flip_v"], round(r["reversed_frac"], 3) if r["reversed_frac"] == r["reversed_frac"] else None, "|", "; ".join(r["flags"])[:150], flush=True)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
