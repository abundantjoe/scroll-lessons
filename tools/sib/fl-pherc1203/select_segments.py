# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-FL-1 step 1 for PHerc1203: list organizer tifxyz segments (anonymous S3), verify each
belongs to the 9.362 um volume (implied voxel from area_cm2/area_vx2, bbox inside the level-0
shape), pick the N largest by area_cm2, and download their top-level tifxyz files.
Usage: select_segments.py OUT_JSON SEG_ROOT [N]"""
import hashlib, json, math, sys
from pathlib import Path
import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
PREFIX = "PHerc1203/segments/raw/"
VOX_UM = 9.362
SHAPE_ZYX = (18977, 6844, 6844)  # eligible_products.json level 0
# RULES.md T0 tracer test set (never used as material here; excluded defensively)
T0 = {"auto_grown_20250923163217042", "auto_grown_20250923163219195", "auto_grown_20250923163223390",
      "auto_grown_20250923163227956", "auto_grown_20250923163230146"}
FILES = ("meta.json", "x.tif", "y.tif", "z.tif")

out_json, seg_root = Path(sys.argv[1]), Path(sys.argv[2])
n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 8}))

cands, rejected = [], []
pages = s3.get_paginator("list_objects_v2").paginate(Bucket=B, Prefix=PREFIX, Delimiter="/")
for pg in pages:
    for cp in pg.get("CommonPrefixes", []):
        sid = cp["Prefix"].rstrip("/").split("/")[-1]
        try:
            m = json.loads(s3.get_object(Bucket=B, Key=cp["Prefix"] + "meta.json")["Body"].read())
        except Exception as e:  # no meta.json -> not a tifxyz segment
            rejected.append({"segment": sid, "why": f"meta.json: {e!r}"}); continue
        why = []
        if m.get("format") != "tifxyz":
            why.append(f"format={m.get('format')}")
        a_cm2, a_vx2 = float(m.get("area_cm2") or 0), float(m.get("area_vx2") or 0)
        vox = math.sqrt(a_cm2 / a_vx2) * 1e4 if a_cm2 > 0 and a_vx2 > 0 else float("nan")
        if not abs(vox - VOX_UM) / VOX_UM < 0.005:
            why.append(f"implied voxel {vox:.4f} um != {VOX_UM}")
        (x0, y0, z0), (x1, y1, z1) = m["bbox"]
        if min(x0, y0, z0) < 0 or x1 >= SHAPE_ZYX[2] or y1 >= SHAPE_ZYX[1] or z1 >= SHAPE_ZYX[0]:
            why.append("bbox outside 9.362 um volume")
        if sid in T0:
            why.append("T0 tracer test set")
        rec = {"segment": sid, "area_cm2": a_cm2, "implied_voxel_um": round(vox, 5), "bbox_xyz": m["bbox"],
               "scale": m.get("scale"), "source_app": m.get("source")}
        (rejected if why else cands).append({**rec, **({"why": why} if why else {})})

cands.sort(key=lambda r: -r["area_cm2"])
picked = cands[:n]
for r in picked:
    d = seg_root / r["segment"]; d.mkdir(parents=True, exist_ok=True)
    r["files_sha256"] = {}
    for f in FILES:
        k = f"{PREFIX}{r['segment']}/{f}"
        obj = s3.get_object(Bucket=B, Key=k)
        data = obj["Body"].read()
        (d / f).write_bytes(data)
        r["files_sha256"][f] = hashlib.sha256(data).hexdigest()
        r.setdefault("s3_etag", {})[f] = obj["ETag"].strip('"')
    r["source"] = "organizer"
out = {"scroll": "PHerc1203", "bucket_prefix": f"s3://{B}/{PREFIX}", "voxel_um": VOX_UM,
       "rule": f"organizer tifxyz, {n} largest by meta.json area_cm2", "n_candidates": len(cands),
       "picked": picked, "rejected": rejected}
out_json.write_text(json.dumps(out, indent=1))
print(json.dumps({"n_candidates": len(cands), "n_rejected": len(rejected),
                  "picked": [(r["segment"], r["area_cm2"]) for r in picked]}))
sys.exit(0 if picked else 3)
