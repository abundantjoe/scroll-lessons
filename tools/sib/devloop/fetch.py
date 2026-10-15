# Provenance: Project HERCULES | owner the owner | [id removed]
"""DEV-LOOP fetcher (task devloop). Official bucket only (s3://vesuvius-challenge-open-data, anonymous).
Every downloaded object is recorded in logs/sib/devloop/downloads.jsonl (key, bytes, etag, sha256, utc).
Whole volumes are never downloaded; surface-volume zarrs are read chunk-wise elsewhere (streamed, not stored).
Usage: python fetch.py meshes9 PHerc0139 | inkmap PHerc0139 <segment_long_id> | meta <key> ...
"""
import hashlib, json, os, sys, time, datetime
import boto3
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = 'vesuvius-challenge-open-data'
ROOT = os.environ.get('DEVLOOP_S3', '/work/devloop/s3')
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LOG = os.path.join(REPO, 'logs/sib/devloop/downloads.jsonl')
NINE = {'PHerc0139': '20250728140407', 'PHerc0814': '20250804134230'}
S3 = boto3.client('s3', config=Config(signature_version=UNSIGNED, retries={'max_attempts': 8, 'mode': 'adaptive'}))


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ls(prefix, delim=None):
    kw = dict(Bucket=BUCKET, Prefix=prefix)
    if delim:
        kw['Delimiter'] = delim
    out, pre = [], []
    for page in S3.get_paginator('list_objects_v2').paginate(**kw):
        out += page.get('Contents', [])
        pre += [c['Prefix'] for c in page.get('CommonPrefixes', [])]
    return out, pre


def get(key, size=None, etag=None):
    dst = os.path.join(ROOT, key)
    if os.path.exists(dst) and (size is None or os.path.getsize(dst) == size):
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for i in range(5):
        try:
            S3.download_file(BUCKET, key, dst + '.part')
            break
        except Exception as e:  # network retry with backoff
            if i == 4:
                raise
            time.sleep(2 ** (i + 1))
    os.replace(dst + '.part', dst)
    rec = dict(utc=utc(), bucket=BUCKET, key=key, bytes=os.path.getsize(dst), etag=etag, sha256=sha256(dst), local=dst)
    with open(LOG, 'a') as f:
        f.write(json.dumps(rec) + '\n')
    return dst


def segments(scroll):
    _, pre = ls(f'{scroll}/segments/', '/')
    return [p.split('/')[-2] for p in pre if not p.endswith('raw/')]


def meshes9(scroll):
    vol = NINE[scroll]
    n = 0
    for sid in segments(scroll):
        ts = sid.split('-')[0]
        objs, _ = ls(f'{scroll}/segments/{sid}/mesh/{ts}-on-{vol}-')
        for o in objs:
            get(o['Key'], o['Size'], o['ETag']); n += 1
    print('meshes9', scroll, n, 'files')


def inkmap(scroll, sid):
    objs, _ = ls(f'{scroll}/segments/{sid}/ink-detection/')
    ks = [o for o in objs if '2.399um' in o['Key'] and o['Key'].endswith('.tif') and '20260417190342' in o['Key']]
    assert len(ks) == 1, [o['Key'] for o in ks]
    p = get(ks[0]['Key'], ks[0]['Size'], ks[0]['ETag'])
    print(p)


def meta(*keys):
    for k in keys:
        o = S3.head_object(Bucket=BUCKET, Key=k)
        print(get(k, o['ContentLength'], o['ETag']))


if __name__ == '__main__':
    cmd, *a = sys.argv[1:]
    {'meshes9': meshes9, 'inkmap': inkmap, 'meta': meta}[cmd](*a)
