# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch 4 organizer reference ink maps of PHerc0139 (model 20260417190342, 2.399 um; segments with
official human labels w035 w039 w041 w044) as a known-text comparison for blob metrics. sha256 logged."""
import hashlib, json, sys
import boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
out = {}
for line in open("/work/k4p/ref0139.txt"):
    seg, key = line.split()
    b = s3.get_object(Bucket="vesuvius-challenge-open-data", Key=key)["Body"].read()
    open(f"/work/k4p/ref0139/{seg}.tif", "wb").write(b)
    out[seg] = dict(key=key, bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(len(out))
