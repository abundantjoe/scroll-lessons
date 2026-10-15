# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-C extended confirmation of a P4 CANDIDATE (RULES.md DECL-P4-3). Numbers only; no image is opened for viewing
and no letter identity or position leaves this script.

build  <batch> <p2_key_batch> <cand_uuid_in_p2_key>
       Upright candidate U = the phase-2 candidate file (unchanged). Self-null R = np.rot90(U, k=-1) (90 degrees
       clockwise). N0: 48 tiles drawn without replacement from all phase-1 census tiles (rot 0) that are not the
       candidate's source, not in the PC pool and not a phase-2 N0 source, by random.Random(20260927 + batch index),
       rotated 90 degrees clockwise. 18 sessions: 9 hold U and 9 hold R (never both); each holds 8 N0 tiles (each
       N0 tile appears in exactly 3 sessions, never twice in one) and 1 positive control from the phase-2 pool; order
       random; key sheet v2 first; frozen task text v2. Key /srv/scorer/p4ext_key_<batch>.json (O_EXCL 0400).
score  <jobs.json>[,<jobs.json>...] <out.json>
       Sessions used as in DECL-P4-2-A3 item 6 (first valid attempt whose PC is read rows Y; at most 2 attempts).
       Triple score = best-pair agreement (all pairs, 150 px, same kind, one-to-one) among 3 reads. U and R reads are
       grouped into triples in session-index order; each N0 tile's reads form its triple. Criteria (DECL-P4-3):
       (i) median U triple > max N0 triple; (ii) every U triple >= 5; (iii) mean pairwise agreement over all U read
       pairs exceeds that over all R read pairs with a one-sided label-permutation p < 0.01 (20000 permutations of
       the U/R labels over the pooled reads, seed 20260927). EXT-CONFIRMED iff (i), (ii) and (iii).
"""
import hashlib
import itertools
import json
import os
import random
import secrets
import sys
import uuid

sys.path.insert(0, 'src')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from p4_phase2 import (IMG, JOBS, PROV, SCORER, _bidx, _brief, _item, _sha, best_pair, known_letters,  # noqa: E402
                       pair_agreement)

SEED = 20260927
N_N0 = 48
N_SESS = 18
PER_N0 = 8
READS_PER_N0 = 3
PERMS = 20000
MIN_TRIPLE = 5
MAX_ATTEMPTS = 2


# ---------------------------------------------------------------- pure scoring (tested)

def triples(reads):
    return [reads[i:i + 3] for i in range(0, len(reads) - len(reads) % 3, 3)]


def mean_pairwise(reads):
    ps = [pair_agreement(a, b) for a, b in itertools.combinations(reads, 2)]
    return sum(ps) / len(ps) if ps else 0.0


def perm_p(u_reads, r_reads, n=PERMS, seed=SEED):
    obs = mean_pairwise(u_reads) - mean_pairwise(r_reads)
    pool = list(u_reads) + list(r_reads)
    k = len(u_reads)
    # pair agreements once; a permutation only relabels reads
    m = len(pool)
    agree = [[0] * m for _ in range(m)]
    for i, j in itertools.combinations(range(m), 2):
        agree[i][j] = agree[j][i] = pair_agreement(pool[i], pool[j])

    def stat(idx_u):
        su = set(idx_u)
        iu = sorted(su)
        ir = [i for i in range(m) if i not in su]
        mu = sum(agree[a][b] for a, b in itertools.combinations(iu, 2)) / max(1, len(iu) * (len(iu) - 1) / 2)
        mr = sum(agree[a][b] for a, b in itertools.combinations(ir, 2)) / max(1, len(ir) * (len(ir) - 1) / 2)
        return mu - mr
    rng = random.Random(seed)
    ge = 0
    for _ in range(n):
        idx = rng.sample(range(m), k)
        if stat(idx) >= obs - 1e-12:
            ge += 1
    return obs, (ge + 1) / (n + 1)


def decide(u_reads, r_reads, n0_triple_scores):
    import statistics
    ut = [best_pair(t) for t in triples(u_reads)]
    rt = [best_pair(t) for t in triples(r_reads)]
    n0max = max(n0_triple_scores, default=0)
    obs, p = perm_p(u_reads, r_reads) if u_reads and r_reads else (0.0, 1.0)
    c1 = bool(ut) and statistics.median(ut) > n0max
    c2 = bool(ut) and all(x >= MIN_TRIPLE for x in ut)
    c3 = p < 0.01 and obs > 0
    return {'u_triples': ut, 'r_triples': rt, 'n0_max': n0max, 'u_minus_r_mean_pairwise': obs, 'perm_p': p,
            'crit_i_median_u_gt_n0max': c1, 'crit_ii_every_u_triple_ge5': c2, 'crit_iii_u_gt_r_p001': c3,
            'EXT_CONFIRMED': bool(c1 and c2 and c3)}


# ---------------------------------------------------------------- build

def _write_key(batch, key):
    path = f'{SCORER}/p4ext_key_{batch}.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(fd, 'w') as fh:
        json.dump(key, fh, indent=1)
    return path


def _assign_n0(n0_u, rng):
    """Each N0 tile in exactly READS_PER_N0 sessions, PER_N0 per session, never twice in one session: each of the
    READS_PER_N0 replicates is an independent shuffle of all N0 tiles cut into sessions of PER_N0."""
    assert len(n0_u) * READS_PER_N0 == N_SESS * PER_N0 and len(n0_u) % PER_N0 == 0
    sess = []
    for _ in range(READS_PER_N0):
        p = n0_u[:]
        rng.shuffle(p)
        sess += [p[i:i + PER_N0] for i in range(0, len(p), PER_N0)]
    rng.shuffle(sess)
    return sess


def cmd_build(batch, p2_batch, cand_u, pool_batches=None, variant=None):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    from p4_jobs import _keys
    p2 = json.load(open(f'{SCORER}/p4p2_key_{p2_batch}.json'))
    assert p2[cand_u]['role'] == 'cand'
    cand_src = p2[cand_u]['src']
    p2jobs = json.load(open(f'/work/p4/jobs_{p2_batch}.json'))
    sel = json.load(open(p2jobs['select']))
    variant = variant or p2jobs.get('variant', 'sigma2')  # METRIC-HASH-35: same task text as its phase 2
    pool = list(sel['pc_pool'])
    used_n0 = {v['src'] for v in p2.values() if v['role'] == 'n0'}
    excluded = {cand_src} | set(pool) | used_n0
    keys = _keys()
    src = [keys[b] for b in pool_batches] if pool_batches else list(keys.values())  # METRIC-HASH-32: same-material N0
    census = sorted((u, v) for k in src for u, v in k.items() if v['rot'] == 0 and u not in excluded)
    seed = SEED + _bidx(batch)
    draw = random.Random(seed).sample(census, N_N0)
    key = {}
    a = cv2.imread(f'{IMG}/{cand_u}.png', cv2.IMREAD_UNCHANGED)
    assert a is not None and a.dtype == np.uint8 and a.ndim == 2
    r_u = str(uuid.uuid4())
    with open(f'{IMG}/{r_u}.png', 'xb') as fh:
        fh.write(png_bytes(np.ascontiguousarray(np.rot90(a, k=-1))))
    key[cand_u] = {'role': 'U', 'src': cand_src, 'strip': p2[cand_u]['strip'], 'r': p2[cand_u]['r'],
                   'c': p2[cand_u]['c'], 'rot': 0}
    key[r_u] = dict(key[cand_u], role='R', rot=90)
    n0_u = []
    for u0, v in draw:
        b = cv2.imread(f'{IMG}/{u0}.png', cv2.IMREAD_UNCHANGED)
        assert b is not None and b.dtype == np.uint8 and b.ndim == 2, u0
        u = str(uuid.uuid4())
        with open(f'{IMG}/{u}.png', 'xb') as fh:
            fh.write(png_bytes(np.ascontiguousarray(np.rot90(b, k=-1))))
        key[u] = {'role': 'n0', 'src': u0, 'strip': v['strip'], 'r': v['r'], 'c': v['c'], 'rot': 90}
        n0_u.append(u)
    rng = secrets.SystemRandom()
    n0_sess = _assign_n0(n0_u, rng)
    ur = ['U'] * (N_SESS // 2) + ['R'] * (N_SESS // 2)
    rng.shuffle(ur)
    pcs = []
    while len(pcs) < N_SESS:
        p = pool[:]
        rng.shuffle(p)
        pcs += p
    jobs = []
    for s in range(N_SESS):
        pu = str(uuid.uuid4())
        with open(f'{IMG}/{pu}.png', 'xb') as fh:
            fh.write(open(f'{IMG}/{pcs[s]}.png', 'rb').read())
        key[pu] = {'role': 'pc', 'src': pcs[s], 'strip': 'w028-037', 'rot': 0, 'session': s}
        items = [cand_u if ur[s] == 'U' else r_u] + n0_sess[s] + [pu]
        rng.shuffle(items)
        job = _brief([f'{IMG}/{u}.png' for u in items], variant)
        jobs.append({'job': job, 'session': s, 'attempt': 1, 'arm': ur[s], 'pc': pu, 'model': 'opus',
                     'n_images': len(items) + 1})
    kpath = _write_key(batch, key)
    out = f'/work/p4/jobs_{batch}.json'
    with open(out, 'x') as fh:
        json.dump({'batch': batch, 'p2_batch': p2_batch, 'n0_seed': seed, 'variant': variant, 'jobs': jobs}, fh,
                  indent=1)
    print(json.dumps({'sessions': len(jobs), 'U': ur.count('U'), 'R': ur.count('R'), 'n0': len(n0_u),
                      'n0_seed': seed, 'key_sha256': _sha(kpath), 'out': out}))


# ---------------------------------------------------------------- score

def cmd_score(jobs_files, out):
    from hercules.harness.collect import load_answer
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from block_schema import validate_for_variant  # METRIC-HASH-38: the pinned schema unless variant 'block'
    variants = {json.load(open(jf)).get('variant', 'sigma2') for jf in jobs_files}
    assert len(variants) == 1, f'mixed brief variants {sorted(variants)}'
    variant = variants.pop()
    key = {}
    for f in sorted(os.listdir(SCORER)):
        if f.startswith('p4ext_key_') and f.endswith('.json'):
            key.update(json.load(open(f'{SCORER}/{f}')))
    by_s = {}
    for jf in jobs_files:
        for j in json.load(open(jf))['jobs']:
            by_s.setdefault(j['session'], []).append(j)
    stats = {'sessions': len(by_s), 'attempts': 0, 'used': 0, 'void_pc': 0, 'invalid': 0, 'missing_items': 0,
             'dropped_sessions': 0}
    u_reads, r_reads, n0 = [], [], {}
    for s, js in sorted(by_s.items()):
        used = False
        for j in sorted(js, key=lambda j: j['attempt'])[:MAX_ATTEMPTS]:
            stats['attempts'] += 1
            rec = json.load(open(f"{JOBS}/{j['job']}.json"))
            if not rec.get('valid') or not os.path.exists(rec['out']):
                stats['invalid'] += 1
                continue
            ans = load_answer(rec['out'], 'score-p4-ext')
            ok, _ = validate_for_variant(ans, variant)
            if not ok:
                stats['invalid'] += 1
                continue
            pc = _item(ans, j['pc'])
            if pc is None or pc.get('rows') != 'Y':
                stats['void_pc'] += 1
                continue
            for p in rec['images'][1:]:
                u = os.path.basename(p)[:-4]
                role = key[u]['role']
                if role == 'pc':
                    continue
                left = _item(ans, u)
                if left is None:
                    stats['missing_items'] += 1
                    continue
                kl = known_letters(left.get('letters'))
                if role == 'U':
                    u_reads.append(kl)
                elif role == 'R':
                    r_reads.append(kl)
                else:
                    n0.setdefault(u, []).append(kl)
            stats['used'] += 1
            used = True
            break
        stats['dropped_sessions'] += int(not used)
    n0_scores = sorted(best_pair(r) for r in n0.values() if len(r) >= 2)
    import numpy as np
    d = decide(u_reads, r_reads, n0_scores)
    p99 = float(np.percentile(n0_scores, 99, method='higher')) if n0_scores else None
    res = {'provenance': PROV, 'serves': 'RULES.md DECL-P4-3', 'stats': stats, 'n_u_reads': len(u_reads),
           'n_r_reads': len(r_reads), 'u_letters_per_read': sorted(len(x[1]) for x in u_reads),
           'r_letters_per_read': sorted(len(x[1]) for x in r_reads), 'n0_triple_scores': n0_scores,
           'n0_tiles_with_ge2_reads': len(n0_scores), 'n0_p99_higher': p99,
           'sg1c_spirit_agreed_minus_p99': (max(d['u_triples']) - p99) if d['u_triples'] and p99 is not None else None,
           **d}
    with open(out, 'w') as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: res[k] for k in ('stats', 'u_triples', 'r_triples', 'n0_max', 'perm_p', 'EXT_CONFIRMED')}))


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'build':
        cmd_build(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] != '-' else None,
                  sys.argv[6] if len(sys.argv) > 6 else None)
    elif c == 'score':
        cmd_score(sys.argv[2].split(','), sys.argv[3])
