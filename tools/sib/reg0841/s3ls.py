# Provenance: Project HERCULES | owner the owner | [id removed]
"""Anonymous S3 listing helper: python s3ls.py PREFIX [--recursive]"""
import sys, boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED), region_name="us-east-1")
B = "vesuvius-challenge-open-data"
pre = sys.argv[1]; rec = "--recursive" in sys.argv
kw = dict(Bucket=B, Prefix=pre)
if not rec: kw["Delimiter"] = "/"
n = 0
for page in s3.get_paginator("list_objects_v2").paginate(**kw):
    for p in page.get("CommonPrefixes", []): print("PRE", p["Prefix"])
    for o in page.get("Contents", []):
        print(o["Key"], o["Size"]); n += 1
        if n > 400: sys.exit(0)
