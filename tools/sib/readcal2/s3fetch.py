# Provenance: Project HERCULES | owner the owner | [id removed]
"""Official-bucket fetcher (task readcal2). s3://vesuvius-challenge-open-data only, anonymous.
Every downloaded object is recorded in logs/sib/readcal2/downloads.jsonl (key, bytes, etag, sha256, utc).
Whole volumes are never downloaded; zarr chunks are streamed elsewhere and never stored whole.
Usage: python s3fetch.py ls <prefix> | get <key> ...
"""
import datetime
import hashlib
import json
import os
import sys
import time

import boto3
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = 'vesuvius-challenge-open-data'
ROOT = os.environ.get('RC2_S3', '/work/rc2/s3')
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LOG = os.path.join(REPO, 'logs/sib/readcal2/downloads.jsonl')
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
        except Exception:
            if i == 4:
                raise
            time.sleep(2 ** (i + 1))
    os.replace(dst + '.part', dst)
    rec = dict(utc=utc(), bucket=BUCKET, key=key, bytes=os.path.getsize(dst), etag=etag, sha256=sha256(dst), local=dst)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a') as f:
        f.write(json.dumps(rec) + '\n')
    return dst


def get_prefix(prefix, max_bytes=400 * 2 ** 20):
    objs, _ = ls(prefix)
    out = []
    for o in objs:
        if o['Size'] > max_bytes:
            raise SystemExit(f'refused (> {max_bytes} bytes): {o["Key"]} {o["Size"]}')
        out.append(get(o['Key'], o['Size'], o['ETag']))
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'ls':
        objs, pre = ls(sys.argv[2], '/')
        for p in pre:
            print('PRE', p)
        for o in objs:
            print(o['Size'], o['Key'])
    elif cmd == 'get':
        for k in sys.argv[2:]:
            print(get(k))
    elif cmd == 'getp':
        for p in get_prefix(sys.argv[2]):
            print(p)
