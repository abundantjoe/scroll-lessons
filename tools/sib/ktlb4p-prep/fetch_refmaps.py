# Provenance: Project HERCULES | owner the owner | [id removed]
"""Download the organizer reference ink maps of PHerc0500P2 (model 20260417190342 on the
2.215 um volume) with sha256 and size; also the one human-label set's array metadata.
Files go to /work/k4p/ref/ (never committed, never viewed). Usage: fetch_refmaps.py OUT_JSON"""
import hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore import UNSIGNED
from botocore.config import Config
B = "vesuvius-challenge-open-data"
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=12))
I = json.load(open("/home/user/dominion/logs/sib/ktlb4p-prep/inventory.json"))
jobs = []
for seg, e in I["segments"].items():
    for p in e["products"]:
        if p["type"] == "ink-detection" and "20260417190342" in p["path"]:
            jobs.append((seg, p["path"]))
os.makedirs("/work/k4p/ref", exist_ok=True)


def get(j):
    seg, key = j
    dst = f"/work/k4p/ref/{seg}.tif"
    for i in range(5):
        try:
            b = s3.get_object(Bucket=B, Key=key)["Body"].read(); break
        except Exception:
            time.sleep(2 ** (i + 1))
    open(dst, "wb").write(b)
    return seg, dict(key=key, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), local=dst)


with ThreadPoolExecutor(8) as ex:
    res = dict(ex.map(get, jobs))
json.dump(res, open(sys.argv[1], "w"), indent=1)
print(len(res), sum(v["bytes"] for v in res.values()))
