#!/usr/bin/env python3
"""bi_mirror.py: copy the exact level-0 CT chunks a render needs (chunks.json from crop_and_chunks.py) from anonymous S3
into a local raw zarr v2 mirror, then keep that mirror under a size cap.

  python bi_mirror.py CHUNKS.json --scroll PHerc0268 [--dst MIRROR.zarr] [--threads 32] [--cap-gb 2.5] [--keep-min 45]

Copies raw chunks byte-identically and keeps existing files. The chunks of this job are
touched (mtime = now). Eviction (only when the mirror exceeds --cap-gb): delete the oldest-mtime chunk files that are not
in this job and older than --keep-min minutes (default 120), until the mirror is under the cap. Eviction is skipped
entirely while any process other than this job's own ancestors could be reading the mirror or be between a mirror and a
render step (vc_render_tifxyz, render66.sh, poc_chain.sh, mirror.py, mirror_any.py, another batch_ink.sh / bi_mirror.py,
or any command line naming the mirror); mirror.py keeps old mtimes, so this closes the mirror-then-render race of those
tools. Evicted chunks are re-fetched on demand next time (tile_gate / sheetio readers fall back to S3).
Prints one JSON line.
"""
import argparse, json, os, sys, time, subprocess
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vol  # noqa: E402
import bi_common as C  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('chunks'); ap.add_argument('--scroll', default='PHerc0268'); ap.add_argument('--dst')
ap.add_argument('--threads', type=int, default=32); ap.add_argument('--cap-gb', type=float, default=2.5)
ap.add_argument('--keep-min', type=float, default=120.0); ap.add_argument('--dry-run', action='store_true', help='report the eviction, delete nothing')
a = ap.parse_args()
dst = a.dst or C.SCROLLS[a.scroll]['mirror']; base = C.SCROLLS[a.scroll]['ct'] + '/0'
keys = [tuple(k) for k in json.load(open(a.chunks))]
fs = vol.fs()
os.makedirs(f'{dst}/0', exist_ok=True)
if not os.path.exists(f'{dst}/.zgroup'): open(f'{dst}/.zgroup', 'w').write('{"zarr_format": 2}')
za = fs.cat_file(f'{base}/.zarray')
if os.path.exists(f'{dst}/0/.zarray'):
    a0, a1 = json.loads(open(f'{dst}/0/.zarray', 'rb').read()), json.loads(za)
    if a0['shape'] != a1['shape']: raise SystemExit(f'mirror {dst} holds another volume (shape {a0["shape"]} vs {a1["shape"]})')
else:
    open(f'{dst}/0/.zarray', 'wb').write(za)


def get(k):
    i, j, l = k; p = f'{dst}/0/{i}/{j}/{l}'
    if os.path.exists(p):
        os.utime(p, None); return 0, 0, 1
    for att in range(6):
        try: b = fs.cat_file(f'{base}/{i}/{j}/{l}'); break
        except FileNotFoundError: return 0, 1, 0
        except Exception:
            if att == 5: raise
            time.sleep(1 + att)
    os.makedirs(os.path.dirname(p), exist_ok=True); tmp = p + f'.tmp{os.getpid()}'
    open(tmp, 'wb').write(b); os.replace(tmp, p); return len(b), 0, 0


t = time.time()
with ThreadPoolExecutor(a.threads) as ex: r = list(ex.map(get, keys))
dt = time.time() - t; nb = sum(x[0] for x in r); miss = sum(x[1] for x in r); hit = sum(x[2] for x in r)

# ---- size cap
files = []
for root, _, fl in os.walk(f'{dst}/0'):
    for f in fl:
        if f.startswith('.'): continue
        p = os.path.join(root, f); st = os.stat(p); files.append((st.st_mtime, st.st_size, p))
tot = sum(f[1] for f in files); cap = int(a.cap_gb * 1e9); ev = 0; evb = 0; skipped = None
if tot > cap:
    # my own ancestors (batch_ink.sh, its shells) never count as readers
    anc, p_ = set(), os.getpid()
    while p_ > 1:
        anc.add(p_)
        try: p_ = int(open(f'/proc/{p_}/stat').read().rsplit(')', 1)[1].split()[1])
        except Exception: break
    busy = []
    pats = ('vc_render_tifxyz', 'render66.sh', 'poc_chain.sh', '/mirror.py', 'mirror_any.py', 'batch_ink.sh', 'bi_mirror.py',
            os.path.basename(dst))      # tools that mirror then render: never evict between their two steps
    for line in subprocess.run(['ps', '-eo', 'pid=,args='], capture_output=True, text=True).stdout.splitlines():
        pid, _, args = line.strip().partition(' ')
        if int(pid) in anc: continue
        if any(q in args for q in pats): busy.append(pid)
    if busy:
        skipped = f'{len(busy)} process(es) may read the mirror (pids {busy[:5]}); eviction deferred'
    else:
        mine = {f'{dst}/0/{i}/{j}/{l}' for i, j, l in keys}; now = time.time()
        for mt, sz, p in sorted(files):
            if tot <= cap: break
            if p in mine or now - mt < a.keep_min * 60: continue
            if a.dry_run:
                tot -= sz; ev += 1; evb += sz; continue
            try: os.remove(p); tot -= sz; ev += 1; evb += sz
            except FileNotFoundError: pass
print(json.dumps({'mirror': dst, 'chunks': len(keys), 'cached': hit, 'fetched_bytes': nb, 'absent_on_s3': miss,
                  'seconds': round(dt, 1), 'MB_per_s': round(nb / 1e6 / max(dt, 1e-3), 1), 'mirror_gb': round(tot / 1e9, 3),
                  'cap_gb': a.cap_gb, 'dry_run': a.dry_run, 'evicted_chunks': ev, 'evicted_gb': round(evb / 1e9, 3), 'eviction_skipped': skipped}))
