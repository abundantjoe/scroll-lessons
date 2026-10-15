# Provenance: Project HERCULES | owner the owner | [id removed]
import sys, boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
def ls(p, maxkeys=None):
    kw = dict(Bucket='vesuvius-challenge-open-data', Prefix=p, Delimiter='/')
    n = 0
    while True:
        r = s3.list_objects_v2(**kw)
        for c in r.get('CommonPrefixes', []): print('P', c['Prefix'])
        for o in r.get('Contents', []): print('O', o['Key'], o['Size'], o['LastModified'], o.get('ETag'))
        n += len(r.get('CommonPrefixes', [])) + len(r.get('Contents', []))
        if not r.get('IsTruncated') or (maxkeys and n >= maxkeys): break
        kw['ContinuationToken'] = r['NextContinuationToken']
for p in sys.argv[1:]:
    ls(p)
