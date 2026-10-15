# Provenance: Project HERCULES | owner the owner | [id removed]
"""Double-check of the PHerc1447 flags with the STANDALONE handcheck package (not the
hercules package): same inputs (centroid track, frame checks), decisions compared with
logs/sib/handed/h2/rule_applied.json. A frame check (level 3, +-1 voxel dilation) is
recomputed independently when FRAME2 is given. Numbers only.
Usage: pp_1447_check.py OUT_JSON FRAME_JSON [FRAME2_JSON]"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "handcheck"))
from handcheck import rule as HR  # noqa: E402
from handcheck.level_mesh import CentreCurve  # noqa: E402
from handcheck.tifxyz import read_tifxyz  # noqa: E402
sys.path.insert(0, str(HERE.parents[2] / "src")); sys.path.insert(0, str(HERE))
import analyze_meshes as A  # noqa: E402  (catalogue + centroid track only)

prev = {x["segment"]: x for x in json.load(open(HERE.parents[2] / "logs/sib/handed/h2/rule_applied.json")) if x["scroll"] == "PHerc1447"}
fr = {m["segment"]: m for m in json.load(open(sys.argv[2]))["meshes"]}
fr2 = {m["segment"]: m for m in json.load(open(sys.argv[3]))["meshes"]} if len(sys.argv) > 3 else {}
cc, ci = A.centroid_curve("PHerc1447")
cc = CentreCurve(z=cc.z, x=cc.x, y=cc.y)
cj = json.loads((A.CEN / "PHerc1447.json").read_text())
out = []
for d in sorted(A.S3.glob("PHerc1447/segments/*/mesh/*.tifxyz")):
    seg = d.parts[len(A.S3.parts) + 2]; vol = d.name.split("-on-")[1].split("-")[0]
    vi = HR.VolumeInfo.from_metadata(cj["zattrs"], A.vol_props("PHerc1447", vol), sample_type="scroll",
                                     centroid=cc if vol in ci.get("volume", "") else None)
    f = fr[seg]
    dec = HR.orient_for_reading(read_tifxyz(d).points.astype(np.float64), vi, frame=HR.FrameCheck(f["frac_zero_ct"], f["frac_outside"]))
    p = prev[seg]
    g2 = fr2.get(seg)
    out.append(dict(segment=seg, state=dec.state, confidence=dec.confidence, mirror_u=dec.mirror_u,
                    prev_state=p["state"], prev_confidence=p["confidence"], prev_mirror_u=p["mirror_u"],
                    same=bool(dec.state == p["state"] and dec.confidence == p["confidence"] and dec.mirror_u == p["mirror_u"]),
                    frame_L4=dict(zero=f["frac_zero_ct"], outside=f["frac_outside"]),
                    frame_recheck=(dict(zero=g2["frac_zero_ct"], zero_dilated=g2.get("frac_zero_ct_dilated"), outside=g2["frac_outside"],
                                        gate_fails=bool(g2["frac_zero_ct"] > 0.05 or g2["frac_outside"] > 0.01),
                                        gate_fails_dilated=bool((g2.get("frac_zero_ct_dilated") or 0) > 0.05 or g2["frac_outside"] > 0.01))
                                   if g2 else None), flags=dec.flags))
    r = out[-1]; print(seg[:14], r["state"], r["confidence"], r["mirror_u"], "same" if r["same"] else "DIFF", r["frame_recheck"])
flagged = [r for r in out if r["state"] != "OK"]
summary = dict(n=len(out), n_flagged=len(flagged), n_frame_unverified=sum(r["state"] == "FRAME_UNVERIFIED" for r in out),
               n_chirality_flag=sum(r["state"] == "FLAG" for r in out), n_ok=sum(r["state"] == "OK" for r in out),
               all_same_as_previous=all(r["same"] for r in out),
               frame_recheck_agrees=(all(r["frame_recheck"]["gate_fails"] == (r["state"] == "FRAME_UNVERIFIED") for r in out) if fr2 else None),
               frame_recheck_dilated_agrees=(all(r["frame_recheck"]["gate_fails_dilated"] == (r["state"] == "FRAME_UNVERIFIED") for r in out) if fr2 else None))
print(summary)
json.dump(dict(summary=summary, meshes=out), open(sys.argv[1], "w"), indent=1, default=float)
