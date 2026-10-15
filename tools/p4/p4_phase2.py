# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-B phase 2 confirmation (RULES.md DECL-P4-2 item 6, amendments A1-A3). Numbers only; no image is opened for
viewing and no letter identity or position leaves this script.

select  <out.json> <census_summary.json>[,<census_summary.json>...]
        Union of the candidates of the census summaries (each already scored with its own variant's N0 p99 and with
        the labelled-adjacency flags of its strip applied by score_p4.py), ranked by n_letters descending, then
        uuid; at most 20 (DECL-P4-2 item 5). Positive-control pool: the positive tiles of the largest 4-connected
        positive cluster of strip w028-037.
build   <batch> <select.json> [<pool_batch>,...]
        (METRIC-HASH-32: with pool batches, N0 is drawn only from those census batches, i.e. the same material.)
        N0: 4 x ceil(candidates / 4) tiles (4 new N0 tiles in every session, DECL-P4-2 item 6; DECL-P4-2-A4), drawn
        without replacement from all phase-1 census tiles (rot 0, both
        strips) that are neither a candidate nor in the PC pool, by random.Random(20260926 + batch index), shown
        rotated 90 degrees clockwise (np.rot90(k=-1)). Candidates are copied unchanged. Each candidate and N0 tile
        is one new uuid file read in 3 sessions. Sessions: 3 replicates; in each, candidates and N0 tiles are
        shuffled (secrets.SystemRandom) into groups of 4; session = candidate group + N0 group + 1 positive
        control (drawn from the pool without replacement while possible, a new uuid file per session), in random
        order, key sheet v2 first, frozen task text v2 (DECL-P4-2-A2). Key /srv/scorer/p4p2_key_<batch>.json
        (O_EXCL, 0400). Jobs /work/p4/jobs_<batch>.json.
rerun   <batch> <session> <new_batch>
        One re-run of a void or invalid session: identical image list, fresh job and reader (DECL-P4-2-A3 item 6).
score   <jobs.json>[,<jobs.json>...] <out.json>
        Per session, the first valid attempt whose positive control is read rows Y (at most 2 attempts). Per tile:
        letters = known-kind namings (hercules.scorer.letters); pair agreement = maximum one-to-one matching of
        same-kind namings with centre distance <= 150 px (hercules.scorer.matching.max_matching_size). Candidate
        test (item 6): >= 2 valid readers each name >= 5 letters; best pair among those agrees on >= 5; and that
        count exceeds the maximum best-pair agreement over every phase-2 N0 tile (all reader pairs, no letter
        filter).
"""
import hashlib
import itertools
import json
import math
import os
import random
import secrets
import sys
import uuid

sys.path.insert(0, 'src')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

IMG = '/work/p4/img'
SCORER = '/srv/scorer'
JOBS = '/work/jobs'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
NULL_SEED = 20260926
MAX_CAND = 20
GROUP = 4
REPS = 3
MIN_LETTERS = 5
MIN_AGREE = 5
RADIUS = 150.0
MAX_ATTEMPTS = 2


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def _bidx(name):
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16) % 100000


# ---------------------------------------------------------------- scoring core (pure; tested)

def known_letters(letters):
    """[(x, y, kind_code)] of the known-kind namings in a reader's letter list."""
    from hercules.scorer.matching import named_arrays
    ok = [x for x in (letters or []) if isinstance(x, dict) and x.get('ch') is not None
          and isinstance(x.get('x'), (int, float)) and isinstance(x.get('y'), (int, float))]
    xy, kinds, _ = named_arrays(ok)
    return xy, kinds


def pair_agreement(a, b, radius=RADIUS):
    """Maximum one-to-one matching of same-kind namings within radius px. a, b: (xy, kinds)."""
    from hercules.scorer.matching import distance_matrix, max_matching_size
    (axy, ak), (bxy, bk) = a, b
    if len(ak) == 0 or len(bk) == 0:
        return 0
    allowed = (ak[:, None] == bk[None, :]) & (distance_matrix(axy, bxy) <= radius)
    return max_matching_size(allowed)


def best_pair(reads, min_letters=0):
    """Best pair agreement among reads with >= min_letters known letters; 0 if fewer than 2 such reads."""
    rs = [r for r in reads if len(r[1]) >= min_letters]
    return max((pair_agreement(p, q) for p, q in itertools.combinations(rs, 2)), default=0)


def candidate_decision(reads, n0_max):
    n_ge5 = sum(1 for r in reads if len(r[1]) >= MIN_LETTERS)
    agreed = best_pair(reads, MIN_LETTERS)
    a, b, c = n_ge5 >= 2, agreed >= MIN_AGREE, agreed > n0_max
    return {'n_readers': len(reads), 'letters_per_reader': sorted((len(r[1]) for r in reads), reverse=True),
            'n_readers_ge5': n_ge5, 'best_pair_agreed': agreed, 'crit_a_2of3_ge5': a, 'crit_b_agree_ge5': b,
            'crit_c_gt_n0max': c, 'P4_CANDIDATE': bool(a and b and c)}


# ---------------------------------------------------------------- select / build

def cmd_select(out, summaries):
    from score_p4 import clusters
    cand, pc_pool, srcs = [], [], []
    for f in summaries:
        s = json.load(open(f))
        srcs.append({'file': f, 'sha256': _sha(f), 'null_p99': s['null_p99'], 'n_candidates': len(s['candidates']),
                     'n_labelled_adjacent': s['n_labelled_adjacent']})
        t = s['tiles']
        for u in s['candidates']:
            assert not t[u]['labelled_adjacent']
            cand.append(dict(t[u], uuid=u))
        pos_b = {(t[u]['r'], t[u]['c']): u for u in s['positive']
                 if t[u]['strip'] == 'w028-037' or t[u]['strip'].endswith('-w028-037')}  # METRIC-HASH-32
        if pos_b:
            big = max(clusters(pos_b.keys()), key=lambda c: (len(c), sorted(c)))
            pc_pool += sorted(pos_b[rc] for rc in big)
    cand.sort(key=lambda d: (-d['n_letters'], d['uuid']))
    res = {'provenance': PROV, 'serves': 'RULES.md DECL-P4-2 items 5-6, DECL-P4-2-A3', 'sources': srcs,
           'n_union': len(cand), 'candidates': cand[:MAX_CAND], 'dropped_by_cap': [d['uuid'] for d in cand[MAX_CAND:]],
           'pc_pool': pc_pool}
    with open(out, 'x') as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({'n_union': len(cand), 'n_candidates': len(res['candidates']), 'n_pc_pool': len(pc_pool),
                      'strips': sorted({d['strip'] for d in res['candidates']})}))


def _write_key(batch, key):
    path = f'{SCORER}/p4p2_key_{batch}.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(fd, 'w') as fh:
        json.dump(key, fh, indent=1)
    return path


def _copy(src_uuid):
    u = str(uuid.uuid4())
    with open(f'{IMG}/{u}.png', 'xb') as fh:
        fh.write(open(f'{IMG}/{src_uuid}.png', 'rb').read())
    return u


def _brief(paths, variant='sigma2'):
    from hercules.harness.jobs import make
    from p4_jobs import task_variant
    ks, ks_sha, single, single_sha = task_variant(variant)  # METRIC-HASH-35 (sigma2 unchanged by default)
    assert variant in ('sigma2', 'sigma2t', 'block') and _sha(ks) == ks_sha
    task = open(single, encoding='utf-8').read()
    assert hashlib.sha256(task.encode()).hexdigest() == single_sha
    job, brief = make('reader', task, [ks] + paths)
    with open(f'/work/p4/brief_{job}.txt', 'x', encoding='utf-8') as fh:
        fh.write(brief)
    return job


def cmd_build(batch, sel_file, pool_batches=None, variant='sigma2'):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    from p4_jobs import _keys
    sel = json.load(open(sel_file))
    cands = sel['candidates']
    pool = list(sel['pc_pool'])
    assert cands and pool
    excluded = {d['uuid'] for d in cands} | set(pool)
    keys = _keys()
    src = [keys[b] for b in pool_batches] if pool_batches else list(keys.values())  # METRIC-HASH-32: same-material N0
    census = sorted((u, v) for k in src for u, v in k.items() if v['rot'] == 0 and u not in excluded)
    seed = NULL_SEED + _bidx(batch)
    draw = random.Random(seed).sample(census, GROUP * math.ceil(len(cands) / GROUP))
    key = {}
    cand_u, n0_u = [], []
    for d in cands:
        u = _copy(d['uuid'])
        key[u] = {'role': 'cand', 'src': d['uuid'], 'strip': d['strip'], 'r': d['r'], 'c': d['c'], 'rot': 0,
                  'census_letters': d['n_letters']}
        cand_u.append(u)
    for u0, v in draw:
        a = cv2.imread(f'{IMG}/{u0}.png', cv2.IMREAD_UNCHANGED)
        assert a is not None and a.dtype == np.uint8 and a.ndim == 2, u0
        u = str(uuid.uuid4())
        with open(f'{IMG}/{u}.png', 'xb') as fh:
            fh.write(png_bytes(np.ascontiguousarray(np.rot90(a, k=-1))))
        key[u] = {'role': 'n0', 'src': u0, 'strip': v['strip'], 'r': v['r'], 'c': v['c'], 'rot': 90}
        n0_u.append(u)
    rng = secrets.SystemRandom()
    groups = []
    for _ in range(REPS):
        cs, ns = cand_u[:], n0_u[:]
        rng.shuffle(cs)
        rng.shuffle(ns)
        groups += list(zip([cs[i:i + GROUP] for i in range(0, len(cs), GROUP)],
                           [ns[i:i + GROUP] for i in range(0, len(ns), GROUP)]))
    pcs = []
    while len(pcs) < len(groups):
        p = pool[:]
        rng.shuffle(p)
        pcs += p
    jobs = []
    for s, ((cg, ng), pc_src) in enumerate(zip(groups, pcs)):
        pu = _copy(pc_src)
        key[pu] = {'role': 'pc', 'src': pc_src, 'strip': 'w028-037', 'rot': 0, 'session': s}
        items = cg + ng + [pu]
        rng.shuffle(items)
        paths = [f'{IMG}/{u}.png' for u in items]
        job = _brief(paths, variant)
        jobs.append({'job': job, 'session': s, 'attempt': 1, 'n_cand': len(cg), 'n_n0': len(ng), 'pc': pu,
                     'model': 'opus', 'n_images': len(paths) + 1})
    kpath = _write_key(batch, key)
    out = f'/work/p4/jobs_{batch}.json'
    with open(out, 'x') as fh:
        json.dump({'batch': batch, 'select': sel_file, 'select_sha256': _sha(sel_file), 'n0_seed': seed,
                   'variant': variant, 'jobs': jobs}, fh, indent=1)
    print(json.dumps({'sessions': len(jobs), 'candidates': len(cand_u), 'n0': len(n0_u), 'n0_seed': seed,
                      'key_sha256': _sha(kpath), 'out': out}))


def cmd_rerun(batch, session, new_batch):
    jf = json.load(open(f'/work/p4/jobs_{batch}.json'))
    old = [j for j in jf['jobs'] if j['session'] == int(session)]
    assert len(old) == 1 and old[0]['attempt'] == 1
    rec = json.load(open(f"{JOBS}/{old[0]['job']}.json"))
    paths = rec['images'][1:]
    variant = jf.get('variant', 'sigma2')  # a re-run uses the original batch's task text
    job = _brief(paths, variant)
    out = f'/work/p4/jobs_{new_batch}.json'
    with open(out, 'x') as fh:
        json.dump({'batch': new_batch, 'rerun_of': batch, 'variant': variant,
                   'jobs': [dict(old[0], job=job, attempt=2, replaces=old[0]['job'])]}, fh, indent=1)
    print(json.dumps({'rerun_job': job, 'session': int(session), 'out': out}))


# ---------------------------------------------------------------- score

def _load_key():
    out = {}
    for f in sorted(os.listdir(SCORER)):
        if f.startswith('p4p2_key_') and f.endswith('.json'):
            out.update(json.load(open(f'{SCORER}/{f}')))
    return out


def _item(ans, u):
    for it in ans.get('items', []) or []:
        if str(it.get('id', '')).strip() == u:
            return it.get('left') or {}
    return None


def cmd_score(jobs_files, out):
    from hercules.harness.collect import load_answer
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from block_schema import validate_for_variant  # METRIC-HASH-38: the pinned schema unless variant 'block'
    variants = {json.load(open(jf)).get('variant', 'sigma2') for jf in jobs_files}
    assert len(variants) == 1, f'mixed brief variants {sorted(variants)}'
    variant = variants.pop()
    key = _load_key()
    by_session = {}
    for jf in jobs_files:
        for j in json.load(open(jf))['jobs']:
            by_session.setdefault(j['session'], []).append(j)
    reads = {}
    stats = {'sessions': len(by_session), 'attempts': 0, 'used': 0, 'void_pc': 0, 'invalid': 0, 'missing_items': 0,
             'dropped_sessions': 0}
    for s, js in sorted(by_session.items()):
        used = False
        for j in sorted(js, key=lambda j: j['attempt'])[:MAX_ATTEMPTS]:
            stats['attempts'] += 1
            rec = json.load(open(f"{JOBS}/{j['job']}.json"))
            if not rec.get('valid') or not os.path.exists(rec['out']):
                stats['invalid'] += 1
                continue
            ans = load_answer(rec['out'], 'score-p4-phase2')
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
                if key[u]['role'] == 'pc':
                    continue
                left = _item(ans, u)
                if left is None:
                    stats['missing_items'] += 1
                    continue
                reads.setdefault(u, []).append(known_letters(left.get('letters')))
            stats['used'] += 1
            used = True
            break
        stats['dropped_sessions'] += int(not used)
    n0 = {u: best_pair(r) for u, r in reads.items() if key[u]['role'] == 'n0'}
    n0_max = max(n0.values(), default=0)
    cands = {}
    for u, v in key.items():
        if v['role'] != 'cand':
            continue
        d = candidate_decision(reads.get(u, []), n0_max)
        cands[u] = dict(d, strip=v['strip'], r=v['r'], c=v['c'], census_letters=v['census_letters'])
    res = {'provenance': PROV, 'serves': 'RULES.md DECL-P4-2 item 6, DECL-P4-2-A3', 'stats': stats,
           'n0_best_pair_agreed': sorted(n0.values()), 'n0_max': n0_max,
           'n0_readers_per_tile': sorted(len(reads.get(u, [])) for u, v in key.items() if v['role'] == 'n0'),
           'candidates': cands, 'n_P4_CANDIDATE': sum(d['P4_CANDIDATE'] for d in cands.values())}
    with open(out, 'w') as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: res[k] for k in ('stats', 'n0_max', 'n_P4_CANDIDATE')}))


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'select':
        cmd_select(sys.argv[2], sys.argv[3].split(','))
    elif c == 'build':
        cmd_build(sys.argv[2], sys.argv[3], sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] != '-' else None,
                  sys.argv[5] if len(sys.argv) > 5 else 'sigma2')
    elif c == 'rerun':
        cmd_rerun(sys.argv[2], sys.argv[3], sys.argv[4])
    elif c == 'score':
        cmd_score(sys.argv[2].split(','), sys.argv[3])
