# Provenance: Project HERCULES | owner the owner | [id removed]
"""Inventory + fetch of PHerc0009B segment meshes (both frames), 2.401 um ink maps and labels.
Anonymous S3 (official bucket). Records key, size and sha256 of every downloaded object.
Surface volumes are NOT downloaded (streamed later by byte-range)."""
import hashlib, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from s3ls import ls, s3, B

ROOT = 'PHerc0009B/segments/'
DST = sys.argv[1] if len(sys.argv) > 1 else '/work/reg0009b/data'
V9, V2 = '20250521125136', '20250820154339'

def walk(p, acc):
    pre, obj = ls(p)
    acc += obj
    for q in pre:
        if q.endswith('.zarr/') and 'surface-volumes' in q:
            acc.append((q, None)); continue
        walk(q, acc)

def fetch(key):
    dst = os.path.join(DST, key[len(ROOT):])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        b = s3.get_object(Bucket=B, Key=key)['Body'].read()
        with open(dst + '.part', 'wb') as f: f.write(b)
        os.replace(dst + '.part', dst)
    h = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
    return key, os.path.getsize(dst), h

segs, _ = ls(ROOT)
inv = {'bucket': B, 'root': ROOT, 'segments': {}}
want = []
for s in segs:
    sid = s[len(ROOT):-1]
    acc = []
    walk(s, acc)
    keys = [k for k, _ in acc]
    rec = {'n_objects': len(acc), 'total_bytes_listed': sum(z for _, z in acc if z),
           'mesh9': [k for k in keys if f'-on-{V9}-8.64um.tifxyz/' in k],
           'mesh2': [k for k in keys if f'-on-{V2}-2.401um.tifxyz/' in k],
           'ink2': [(k, z) for k, z in acc if '/ink-detection/' in k and k.endswith('.tif')],
           'labels2': [(k, z) for k, z in acc if '/ink-labels/' in k],
           'sv': [k for k, z in acc if z is None],
           'obj': [(k, z) for k, z in acc if k.endswith('.obj')],
           'other': [(k, z) for k, z in acc if z is not None and not any(t in k for t in ('.tifxyz/', '/ink-detection/', '/ink-labels/', '.obj'))]}
    rec['both_frames'] = bool(rec['mesh9']) and bool(rec['mesh2'])
    inv['segments'][sid] = rec
    if rec['both_frames']:
        want += rec['mesh9'] + rec['mesh2'] + [k for k, _ in rec['ink2']] + [k for k, _ in rec['labels2']]
with ThreadPoolExecutor(16) as ex:
    got = list(ex.map(fetch, want))
inv['downloads'] = [{'key': k, 'bytes': n, 'sha256': h} for k, n, h in sorted(got)]
json.dump(inv, open(os.path.join(DST, 'inventory_raw.json'), 'w'), indent=1)
print('segments', len(segs), 'both_frames', sum(r['both_frames'] for r in inv['segments'].values()),
      'downloaded', len(got), 'bytes', sum(n for _, n, _ in got))
