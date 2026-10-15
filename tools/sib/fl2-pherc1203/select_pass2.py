# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-FL-1 extra pass 2, PHerc1203 (tools/fl/BRIEF_PASS.md at dcb6a6ba): list the organizer tifxyz segments
(anonymous S3), apply the same validity checks as tools/sib/fl-pherc1203/select_segments.py (format tifxyz,
implied voxel 9.362 um from area_cm2/area_vx2, bbox inside the level-0 shape, T0 tracer ids excluded), rank by
meta.json area_cm2 and report ranks 4-9 against the brief's keep rule (area >= 16 cm^2 and 0 self-intersections).
Metadata only: no tifxyz, CT or ink data is downloaded. Usage: select_pass2.py OUT_JSON"""
import hashlib, json, math, sys, datetime
import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
PREFIX = "PHerc1203/segments/raw/"
VOX_UM = 9.362
SHAPE_ZYX = (18977, 6844, 6844)
T0 = {"auto_grown_20250923163217042", "auto_grown_20250923163219195", "auto_grown_20250923163223390",
      "auto_grown_20250923163227956", "auto_grown_20250923163230146"}
MIN_CM2 = 16.0
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 8}))
cands, rejected, n_prefix = [], [], 0
for pg in s3.get_paginator("list_objects_v2").paginate(Bucket=B, Prefix=PREFIX, Delimiter="/"):
    for cp in pg.get("CommonPrefixes", []):
        n_prefix += 1
        sid = cp["Prefix"].rstrip("/").split("/")[-1]
        try:
            raw = s3.get_object(Bucket=B, Key=cp["Prefix"] + "meta.json")["Body"].read(); m = json.loads(raw)
        except Exception as e:
            rejected.append({"segment": sid, "why": [f"meta.json: {type(e).__name__}"]}); continue
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
        rec = {"segment": sid, "area_cm2": a_cm2, "implied_voxel_um": round(vox, 5),
               "meta_json_sha256": hashlib.sha256(raw).hexdigest()}
        (rejected if why else cands).append({**rec, **({"why": why} if why else {})})
cands.sort(key=lambda r: -r["area_cm2"])
for i, r in enumerate(cands):
    r["rank"] = i + 1
rng = [r for r in cands if 4 <= r["rank"] <= 9]
for r in rng:
    r["keep"] = r["area_cm2"] >= MIN_CM2
    r["drop_reason"] = None if r["keep"] else f"area {r['area_cm2']:.3f} cm^2 < {MIN_CM2}"
kept = [r for r in rng if r["keep"]]
out = {"utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "scroll": "PHerc1203", "pass": 2, "bucket_prefix": f"s3://{B}/{PREFIX}", "n_prefixes": n_prefix,
       "n_valid": len(cands), "rank_range": [4, 9], "keep_rule": "area >= 16 cm^2 and 0 self-intersections",
       "ranked": cands, "rejected": rejected, "in_range": rng, "kept": kept,
       "auto_grow": "not applicable: the scroll has organizer segments (brief: auto-grow only if the scroll has none)"}
open(sys.argv[1], "w").write(json.dumps(out, indent=1))
print(json.dumps({"n_prefixes": n_prefix, "n_valid": len(cands), "in_range": [(r["rank"], r["segment"], round(r["area_cm2"], 3)) for r in rng], "n_kept": len(kept)}))
