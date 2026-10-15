# Provenance: Project HERCULES | owner the owner | [id removed]
"""Sync a band of official normal-grid slice files to local disk (anonymous S3), resumable,
with one sha256 line per file. Usage:
  sync_normalgrids.py <s3 prefix of .normal-grids/> <local root> <manifest.jsonl> xy:Z0-Z1 xz:Y0-Y1 yz:X0-X1
The tracer queries plane xy at slice z, xz at slice y, yz at slice x (NormalGridVolume.cpp)."""
import hashlib, json, os, sys, concurrent.futures as cf
import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
pfx, root, manifest = sys.argv[1].rstrip("/") + "/", sys.argv[2], sys.argv[3]
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=32), region_name="us-east-1")
done = set()
if os.path.exists(manifest):
    for l in open(manifest):
        done.add(json.loads(l)["key"])
jobs = [pfx + "metadata.json"]
for spec in sys.argv[4:]:
    plane, rng = spec.split(":")
    a, b = map(int, rng.split("-"))
    jobs += [f"{pfx}{plane}/{i:06d}.grid" for i in range(a, b + 1)]
jobs = [k for k in jobs if f"s3://{B}/{k}" not in done]

def get(k):
    dst = os.path.join(root, k[len(pfx):])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for attempt in range(5):
        try:
            b = s3.get_object(Bucket=B, Key=k)["Body"].read()
            break
        except s3.exceptions.NoSuchKey:
            return {"key": f"s3://{B}/{k}", "missing": True}
        except Exception as e:  # network retry with backoff
            import time; time.sleep(2 ** attempt)
    else:
        return {"key": f"s3://{B}/{k}", "error": "failed after 5 attempts"}
    tmp = dst + ".tmp"
    open(tmp, "wb").write(b); os.replace(tmp, dst)
    return {"key": f"s3://{B}/{k}", "size": len(b), "sha256": hashlib.sha256(b).hexdigest()}

with open(manifest, "a") as mf, cf.ThreadPoolExecutor(16) as ex:
    for n, r in enumerate(ex.map(get, jobs)):
        mf.write(json.dumps(r) + "\n")
        if n % 500 == 0:
            mf.flush(); print(n, len(jobs), flush=True)
print("done", len(jobs))
