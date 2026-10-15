# Provenance: Project HERCULES | owner the owner | [id removed]
"""Anonymous download of named keys (or all keys under a prefix) from the official bucket
s3://vesuvius-challenge-open-data into /work/factory/s3/<key>; appends key, bytes, sha256 to
logs/sib/factory/downloads.jsonl. Refuses image-pixel extensions other than tifxyz coordinate TIFFs
(x/y/z.tif), metadata JSON and zarr metadata. Usage: s3get.py PREFIX_OR_KEY..."""
import hashlib, json, os, sys, datetime
import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
ROOT = "/work/factory/s3"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG = os.path.join(REPO, "logs", "sib", "factory", "downloads.jsonl")
ALLOWED = ("/x.tif", "/y.tif", "/z.tif", "meta.json", "metadata.json", ".zattrs", ".zgroup", ".zarray")


def main(args):
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    for p in args:
        kw = dict(Bucket=B, Prefix=p)
        while True:
            r = s3.list_objects_v2(**kw)
            for o in r.get("Contents", []):
                k = o["Key"]
                if not k.endswith(ALLOWED):
                    print("skip (not allowed):", k)
                    continue
                dst = os.path.join(ROOT, k)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst) or os.path.getsize(dst) != o["Size"]:
                    s3.download_file(B, k, dst)
                sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
                rec = dict(utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                           key=f"s3://{B}/{k}", bytes=o["Size"], etag=o["ETag"].strip('"'),
                           last_modified=o["LastModified"].strftime("%Y-%m-%dT%H:%M:%SZ"), sha256=sha)
                with open(LOG, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
                print(k, o["Size"], sha, flush=True)
            if not r.get("IsTruncated"):
                break
            kw["ContinuationToken"] = r["NextContinuationToken"]


if __name__ == "__main__":
    main(sys.argv[1:])
