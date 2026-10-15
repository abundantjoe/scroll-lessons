# Provenance: Project HERCULES | owner the owner | [id removed]
"""List (recursively) and optionally download public keys from s3://vesuvius-challenge-open-data into
/work/d3/data/s3/<key>; prints key, size, sha256 (after download). Usage: s3_fetch.py [--get] PREFIX..."""
import sys, os, hashlib, boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
B = 'vesuvius-challenge-open-data'
ROOT = '/work/d3/data/s3'
get = '--get' in sys.argv
for p in [a for a in sys.argv[1:] if a != '--get']:
    kw = dict(Bucket=B, Prefix=p)
    while True:
        r = s3.list_objects_v2(**kw)
        for o in r.get('Contents', []):
            k = o['Key']
            if get:
                dst = os.path.join(ROOT, k)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst) or os.path.getsize(dst) != o['Size']:
                    s3.download_file(B, k, dst)
                print(k, o['Size'], hashlib.sha256(open(dst, 'rb').read()).hexdigest(), flush=True)
            else:
                print(k, o['Size'])
        if not r.get('IsTruncated'):
            break
        kw['ContinuationToken'] = r['NextContinuationToken']
