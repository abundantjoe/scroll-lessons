# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch organizer tifxyz meshes (x/y/z.tif + meta.json; geometry only, no
image, render or ink product) from the official open-data bucket
(anonymous), recording sha256 and size of every object.

Usage: python fetch_meshes.py OUT_DIR MANIFEST_JSON PREFIX [PREFIX ...]
Each PREFIX is an S3 key prefix of a ``*.tifxyz/`` folder. Only objects whose
name ends in x.tif, y.tif, z.tif, mask.tif or meta.json are fetched.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "vesuvius-challenge-open-data"
KEEP = ("x.tif", "y.tif", "z.tif", "meta.json")


def s3():
    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16,
                                            retries={"max_attempts": 6, "mode": "standard"}))


def list_prefix(c, prefix: str) -> list[dict]:
    out, tok = [], None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=prefix)
        if tok:
            kw["ContinuationToken"] = tok
        r = c.list_objects_v2(**kw)
        out += r.get("Contents", [])
        if not r.get("IsTruncated"):
            return out
        tok = r["NextContinuationToken"]


def main() -> int:
    out_dir, manifest, prefixes = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
    c = s3()
    old = json.loads(manifest.read_text()) if manifest.exists() else {"objects": {}}
    objs = []
    for p in prefixes:
        p = p if p.endswith("/") else p + "/"
        for o in list_prefix(c, p):
            name = o["Key"].rsplit("/", 1)[-1]
            if name in KEEP and o["Key"][len(p):].count("/") == 0:
                objs.append(o)

    def get(o):
        key = o["Key"]
        dst = out_dir / key
        if key in old["objects"] and dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest() == old["objects"][key]["sha256"]:
            return key, old["objects"][key]
        dst.parent.mkdir(parents=True, exist_ok=True)
        for i in range(4):
            try:
                b = c.get_object(Bucket=BUCKET, Key=key)["Body"].read()
                break
            except Exception:  # network retry with backoff
                time.sleep(2 ** (i + 1))
        else:
            return key, {"error": "download failed"}
        dst.write_bytes(b)
        return key, {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
                     "etag": o.get("ETag", "").strip('"'), "last_modified": o["LastModified"].isoformat()}

    with ThreadPoolExecutor(8) as ex:
        for k, v in ex.map(get, objs):
            old["objects"][k] = v
    old["bucket"] = f"s3://{BUCKET} (anonymous)"
    manifest.write_text(json.dumps(old, indent=1, sort_keys=True))
    n_err = sum("error" in v for v in old["objects"].values())
    print(f"objects={len(objs)} total_in_manifest={len(old['objects'])} errors={n_err} "
          f"bytes={sum(v.get('bytes', 0) for v in old['objects'].values())}")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
