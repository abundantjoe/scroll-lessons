# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 LABEL-EQUIV (RULES.md DECL-D3-A1 item 7, DECL-D3-A3 item 6; reported, never deciding). Numbers only; no image or
pixel array is displayed.

Tiles     the 288 fold-A pool tiles (/work/d3/pool_fa/manifest.json tiles, asserted equal to the ge144 tiles of
          /work/d3/work/fa_tiles.json) and all 306 PRIMARY text tiles (fa_tiles.json, D3-FEAS-RESULT), 128 x 128 px at
          (y0, x0) on the bank 9.366 um organizer canvas of their PHerc0841 segment (/work/bank/0841/canvas9/<seg>).
Teacher   ink = ref9 >= 150 AND valid9, blank = ref9 <= 100 AND valid9, rest ignored (the build_pools.py build_fa
          lines); for the 288 pool tiles asserted equal to /work/d3/pool_fa/inklabels.npy and supervision.npy.
Human     the official human labels, label set 20260918 (2.403 um inklabels / supervision area-averaged to the 9 um
          canvas: bank lab9_inklabels.npz / lab9_supervision.npz 'frac'). PRIMARY rule = the D3-FEAS count-A literal
          reading of 'label > 0 inside supervision': ink = inkfrac > 0 AND supfrac > 0, blank = supfrac > 0 without ink.
          Also reported (extra, not declared): the majority-footprint variant of count A (inkfrac >= 0.5 AND supfrac >=
          0.5 = ink, supfrac >= 0.5 without ink = blank).
Compared  on pixels where both labels are defined: overlap px, 2 x 2 confusion (teacher x human), agreement fraction,
          Cohen's kappa; summed over tiles (overlapping tiles counted once per tile, as the pool stores them) and over
          unique canvas pixels (union of the tiles); per segment and total.
Output    /home/user/dominion/logs/d1/d3_label_equiv.json.
"""
import sys
sys.dont_write_bytecode = True
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import json, time, hashlib, datetime
import numpy as np

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
BANK = '/work/bank/0841'
FA_TILES = '/work/d3/work/fa_tiles.json'
POOL = '/work/d3/pool_fa'
OUT = '/home/user/dominion/logs/d1/d3_label_equiv.json'
T = 128
RULES = {'primary_gt0': 0.0, 'extra_ge0p5': 0.5}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def teacher(ref, val):
    r = np.asarray(ref, np.float32); v = np.asarray(val).astype(bool)
    return (r >= 150) & v, (r <= 100) & v


def human(inkf, supf, rule):
    if rule == 'primary_gt0':
        sup = supf > 0; ink = (inkf > 0) & sup
    else:
        sup = supf >= 0.5; ink = (inkf >= 0.5) & sup
    return ink, sup & ~ink


def conf(ti, tb, hi, hb):
    return np.array([int((ti & hi).sum()), int((ti & hb).sum()), int((tb & hi).sum()), int((tb & hb).sum()),
                     int((ti | tb).sum()), int((hi | hb).sum())], np.int64)


def stats(c):
    a, b, cc, d, nt, nh = (int(x) for x in c)
    n = a + b + cc + d
    out = dict(teacher_defined_px=nt, human_defined_px=nh, overlap_px=n,
               confusion=dict(teacher_ink_human_ink=a, teacher_ink_human_blank=b, teacher_blank_human_ink=cc,
                              teacher_blank_human_blank=d),
               agreement=None, cohen_kappa=None)
    if n:
        po = (a + d) / n
        pe = ((a + b) * (a + cc) + (cc + d) * (b + d)) / float(n * n)
        out.update(agreement=po, expected_agreement=pe, cohen_kappa=((po - pe) / (1 - pe) if pe < 1 else None),
                   teacher_ink_frac_in_overlap=(a + b) / n, human_ink_frac_in_overlap=(a + cc) / n)
    return out


def main():
    t0 = time.time()
    fl = json.load(open(FA_TILES))
    man = json.load(open(f'{POOL}/manifest.json'))
    for f, h in man['files_sha256'].items():
        assert sha256(f'{POOL}/{f}') == h, f
    assert sha256(FA_TILES) in man['meta']['source']
    prim = [(t['segment'], t['y0'], t['x0']) for t in fl['tiles']]
    ge144 = [(t['segment'], t['y0'], t['x0']) for t in fl['tiles'] if t['ge144']]
    pool = [(t['segment'], t['y0'], t['x0']) for t in man['tiles']]
    assert len(prim) == fl['n_text'] == 306 and len(set(prim)) == 306
    assert pool == ge144 and len(pool) == man['n_tiles'] == 288
    pool_set = set(pool)
    p_ink = np.load(f'{POOL}/inklabels.npy'); p_sup = np.load(f'{POOL}/supervision.npy')
    pidx = {k: i for i, k in enumerate(pool)}
    segs = sorted({t[0] for t in prim})
    res = {r: {s: {'pool288': dict(tiles=np.zeros(6, np.int64), unique=None, n_tiles=0, n_tiles_with_overlap=0),
                   'primary306': dict(tiles=np.zeros(6, np.int64), unique=None, n_tiles=0, n_tiles_with_overlap=0)}
               for s in segs} for r in RULES}
    pool_label_equal, files = 0, {}
    for s in segs:
        d = f'{BANK}/canvas9/{s}'
        ref = np.load(f'{d}/ref9.npy', mmap_mode='r'); val = np.load(f'{d}/valid9.npy', mmap_mode='r')
        inkf = np.load(f'{d}/lab9_inklabels.npz')['frac']; supf = np.load(f'{d}/lab9_supervision.npz')['frac']
        assert inkf.shape == supf.shape == ref.shape == val.shape, (s, inkf.shape, ref.shape)
        files[s] = {f: sha256(f'{d}/{f}') for f in ('ref9.npy', 'valid9.npy', 'lab9_inklabels.npz', 'lab9_supervision.npz')}
        unions = {'pool288': np.zeros(ref.shape, bool), 'primary306': np.zeros(ref.shape, bool)}
        for (sg, y, x) in prim:
            if sg != s:
                continue
            ti, tb = teacher(ref[y:y + T, x:x + T], val[y:y + T, x:x + T])
            sets = ['primary306'] + (['pool288'] if (sg, y, x) in pool_set else [])
            if (sg, y, x) in pool_set:
                i = pidx[(sg, y, x)]
                pool_label_equal += int(np.array_equal(ti.astype(np.uint8), p_ink[i]) and
                                        np.array_equal((ti | tb).astype(np.uint8), p_sup[i]))
            for st in sets:
                unions[st][y:y + T, x:x + T] = True
            for r in RULES:
                hi, hb = human(inkf[y:y + T, x:x + T], supf[y:y + T, x:x + T], r)
                c = conf(ti, tb, hi, hb)
                for st in sets:
                    e = res[r][s][st]
                    e['tiles'] += c; e['n_tiles'] += 1; e['n_tiles_with_overlap'] += int(c[:4].sum() > 0)
        tia, tba = teacher(ref, val)
        for r in RULES:
            hia, hba = human(inkf, supf, r)
            for st, u in unions.items():
                res[r][s][st]['unique'] = conf(tia & u, tba & u, hia & u, hba & u)
                res[r][s][st]['unique_px'] = int(u.sum())
        del ref, val, inkf, supf, tia, tba, unions
    assert pool_label_equal == 288, pool_label_equal
    out = dict(generated_utc=utc(), rule='DECL-D3-A3 item 6 (LABEL-EQUIV, reported, never deciding)',
               viewing='no image or pixel array was opened, displayed or described; numbers only',
               teacher='ref9 >= 150 AND valid9 = ink; ref9 <= 100 AND valid9 = blank; rest ignored (build_pools.py build_fa)',
               human=dict(label_set='20260918 (official 2.403 um inklabels/supervision, area-averaged to the 9.366 um canvas: '
                                    'bank lab9_*.npz frac)',
                          primary_gt0='ink = inkfrac > 0 AND supfrac > 0; blank = supfrac > 0 without ink (D3-FEAS count A '
                                      'text_lab_gt0 literal reading)',
                          extra_ge0p5='ink = inkfrac >= 0.5 AND supfrac >= 0.5; blank = supfrac >= 0.5 without ink (count A '
                                      'text_lab_ge0p5; extra, not declared)'),
               tiles=dict(pool288=len(pool), primary306=len(prim), pool_teacher_labels_equal_pool_arrays=pool_label_equal,
                          fa_tiles=FA_TILES, fa_tiles_sha256=sha256(FA_TILES), pool_manifest_sha256=sha256(f'{POOL}/manifest.json')),
               counting=dict(tile_summed='per tile, as the pool stores the labels (overlapping stride-64 tiles counted once '
                                         'per tile)', unique_px='union of the tiles on each segment canvas'),
               input_sha256=files, bank_0841_json_sha256=sha256(f'{BANK}/bank_0841.json'), results={})
    for r in RULES:
        rr = {}
        for st in ('pool288', 'primary306'):
            tot_t = sum(res[r][s][st]['tiles'] for s in segs)
            tot_u = sum(res[r][s][st]['unique'] for s in segs)
            rr[st] = dict(tile_summed=stats(tot_t), unique_px=stats(tot_u),
                          n_tiles=sum(res[r][s][st]['n_tiles'] for s in segs),
                          n_tiles_with_overlap=sum(res[r][s][st]['n_tiles_with_overlap'] for s in segs),
                          n_unique_px_in_tiles=sum(res[r][s][st]['unique_px'] for s in segs),
                          per_segment={s: dict(n_tiles=res[r][s][st]['n_tiles'],
                                               n_tiles_with_overlap=res[r][s][st]['n_tiles_with_overlap'],
                                               tile_summed=stats(res[r][s][st]['tiles']),
                                               unique_px=stats(res[r][s][st]['unique'])) for s in segs})
        out['results'][r] = rr
    out['seconds'] = round(time.time() - t0, 1)
    out['script'] = dict(path=os.path.abspath(__file__), sha256=sha256(os.path.abspath(__file__)))
    d = {'provenance': PROV}
    d.update(out)
    with open(OUT + '.tmp', 'w', encoding='ascii') as fh:
        fh.write(json.dumps(d, indent=1) + '\n')
    os.replace(OUT + '.tmp', OUT)
    for r in RULES:
        for st in ('pool288', 'primary306'):
            x = out['results'][r][st]['tile_summed']
            print(r, st, 'overlap', x['overlap_px'], 'conf', list(x['confusion'].values()), 'agree', x['agreement'],
                  'kappa', x['cohen_kappa'], 'tiles_with_overlap', out['results'][r][st]['n_tiles_with_overlap'])


if __name__ == '__main__':
    main()
