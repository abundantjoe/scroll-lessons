# Provenance: Project HERCULES | owner the owner | [id removed]
# Mirror every object under an S3 prefix of vesuvius-challenge-open-data (anonymous) into /work/c3/data/s3/<key>.
# Writes a manifest "<sha256>  <key>  <size>  <etag>" to argv[2].
import sys, os, hashlib, boto3, concurrent.futures as cf
from botocore import UNSIGNED
from botocore.config import Config
B = 'vesuvius-challenge-open-data'
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED, max_pool_connections=16, retries={'max_attempts': 10}))
prefix, manifest = sys.argv[1], sys.argv[2]
keys = []
kw = dict(Bucket=B, Prefix=prefix)
while True:
    r = s3.list_objects_v2(**kw)
    keys += [(o['Key'], o['Size'], o['ETag']) for o in r.get('Contents', [])]
    if not r.get('IsTruncated'): break
    kw['ContinuationToken'] = r['NextContinuationToken']
print('objects', len(keys), 'bytes', sum(k[1] for k in keys), flush=True)
def get(item):
    key, size, etag = item
    dst = os.path.join('/work/c3/data/s3', key)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not (os.path.exists(dst) and os.path.getsize(dst) == size):
        s3.download_file(B, key, dst + '.part'); os.replace(dst + '.part', dst)
    h = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
    assert os.path.getsize(dst) == size, key
    return f'{h}  {key}  {size}  {etag}'
with cf.ThreadPoolExecutor(8) as ex:
    lines = sorted(ex.map(get, keys), key=lambda s: s.split('  ')[1])
open(manifest, 'w').write('\n'.join(lines) + '\n')
print('done', len(lines))
