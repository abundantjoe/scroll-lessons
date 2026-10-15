# Provenance: Project HERCULES | owner the owner | [id removed]
"""Stream a band of slices [z0, z1) of one level of an official surface-volume zarr
(zarr v2, uncompressed, C-order chunks (Z, cy, cx)) by S3 byte ranges.
Only the requested slice bytes are transferred. Missing chunks are fill_value."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from botocore.exceptions import ClientError
sys.path.insert(0, os.path.dirname(__file__))
from s3ls import s3, B


def zarray(prefix, level):
    return json.loads(s3.get_object(Bucket=B, Key=f'{prefix}/{level}/.zarray')['Body'].read())


def band(prefix, level, z0, z1, threads=32):
    za = zarray(prefix, level)
    assert za['compressor'] is None and za['order'] == 'C' and za['dtype'] == '|u1' and za['filters'] is None
    Z, H, W = za['shape']; cz, cy, cx = za['chunks']
    assert cz == Z and 0 <= z0 < z1 <= Z
    sep = za.get('dimension_separator', '.')
    ny, nx = -(-H // cy), -(-W // cx)
    out = np.full((z1 - z0, H, W), za['fill_value'] or 0, np.uint8)
    plane = cy * cx
    rng = f'bytes={z0 * plane}-{z1 * plane - 1}'
    stats = {'requests': 0, 'missing': 0, 'bytes': 0}

    def one(ij):
        i, j = ij
        key = f'{prefix}/{level}/0{sep}{i}{sep}{j}'
        for attempt in range(5):
            try:
                b = s3.get_object(Bucket=B, Key=key, Range=rng)['Body'].read()
                break
            except ClientError as e:
                if e.response['Error']['Code'] in ('NoSuchKey', '404'):
                    return ij, None
                if attempt == 4: raise
            except Exception:
                if attempt == 4: raise
        a = np.frombuffer(b, np.uint8).reshape(z1 - z0, cy, cx)
        return ij, a

    with ThreadPoolExecutor(threads) as ex:
        for (i, j), a in ex.map(one, [(i, j) for i in range(ny) for j in range(nx)]):
            stats['requests'] += 1
            if a is None:
                stats['missing'] += 1; continue
            stats['bytes'] += a.nbytes
            y0, x0 = i * cy, j * cx
            hh, ww = min(cy, H - y0), min(cx, W - x0)
            out[:, y0:y0 + hh, x0:x0 + ww] = a[:, :hh, :ww]
    return out, za, stats
