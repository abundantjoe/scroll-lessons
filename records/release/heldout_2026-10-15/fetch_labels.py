import os, boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED))
B = "vesuvius-challenge-open-data"
for seg in ["20260220213127-w00", "20260220214732-auto_grown_20260220144552896", "20260221022814-auto_grown_20260220174252405"]:
    pre = f"PHerc0841/segments/{seg}/ink-labels/2.403um-volume-20260319124803/20260918/"
    n = 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=B, Prefix=pre):
        for o in page["Contents"]:
            dst = os.path.join(seg, "labels", o["Key"][len(pre):])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            s3.download_file(B, o["Key"], dst); n += 1
    print(seg, n, "label files")
