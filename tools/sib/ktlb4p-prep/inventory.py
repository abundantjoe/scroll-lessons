# Provenance: Project HERCULES | owner the owner | [id removed]
"""Inventory of PHerc0500P2 organizer data products (paths, sizes, ETags,
last-modified) from the root catalogue + S3 listings. No image content is
read. Usage: python inventory.py ROOT_METADATA OUT_JSON"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16))
d = json.load(open(sys.argv[1]))["samples"]["PHerc0500P2"]


def listing(prefix):
    out, tok = [], None
    while True:
        kw = dict(Bucket=B, Prefix=prefix)
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        out += r.get("Contents", [])
        if not r.get("IsTruncated"):
            return out
        tok = r["NextContinuationToken"]


def summarize(path):
    objs = listing(path)
    tot = sum(o["Size"] for o in objs)
    one = objs[0] if len(objs) == 1 else None
    return dict(path=path, n_objects=len(objs), bytes=tot,
                etag=(one["ETag"].strip('"') if one else None),
                last_modified=(max(o["LastModified"] for o in objs).isoformat() if objs else None),
                files=([o["Key"][len(path):] for o in objs] if len(objs) <= 12 else None))


jobs = []
for sid, s in d["segments"].items():
    for dd in s.get("data", []):
        for o in dd.get("origins", []) or []:
            jobs.append((s["long_id"], dd["type"], o["path"], dd.get("properties"), dd.get("parameters")))
with ThreadPoolExecutor(12) as ex:
    res = list(ex.map(lambda j: (j, summarize(j[2])), jobs))
segs = {}
for (lid, typ, path, props, params), summ in res:
    e = segs.setdefault(lid, dict(original_volume_id=d["segments"][lid.split("-")[0]]["original_volume_id"]
                                  if lid.split("-")[0] in d["segments"] else None, products=[]))
    summ.update(type=typ, properties=props, parameters=params)
    e["products"].append(summ)
vols = {vid: dict(long_id=v.get("long_id"), properties={k: v.get("properties", {}).get(k) for k in (
    "pixel_size_um", "energy_keV", "detector_distance_mm", "z_direction_is_top_to_bottom",
    "left_handed_coordinates", "text_side", "shape")}) for vid, v in d["volumes"].items()}
top = {p: summarize(p) for p in ("PHerc0500P2/representations/", "PHerc0500P2/photos/")}
json.dump(dict(sample="PHerc0500P2", sample_type=d["sample"]["properties"].get("type"), volumes=vols,
               n_segments=len(segs), segments=segs, top_level=top), open(sys.argv[2], "w"), indent=1, default=str)
print(len(segs), sum(len(v["products"]) for v in segs.values()))
