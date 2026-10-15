# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-B census scoring and candidate rule (RULES.md DECL-P4-2 items 3-5). Counts only; no letter identity or position
leaves this script.

census  <jobs_json>[,<jobs_json>...] <excl_json>[,<excl_json>...] <out_json>
    For every job: decrypt the sealed answer (purpose 'score-p4-census'), validate it, and for each image uuid in the
    job read its LEFT answer: rows (Y/N), n_letters, n_firm. N0 (rot 90) tiles give the null distribution;
    p99 = numpy.percentile(N0 letter counts, 99) (linear interpolation). A census tile is positive iff rows == 'Y' and
    n_letters >= max(5, p99). Positive tiles form 4-connected clusters on each segment's (r, c) grid. Candidates:
    every positive tile of strip w010-027 (name 'w010-027' or '<segment ts>-w010-027'), and every positive tile of strip w028-037 in a cluster of <= 4 tiles that
    is separated from every larger cluster (no 4-neighbour of the small cluster belongs to a larger cluster: the
    clusters are 4-connected components, so this holds by construction; separation by >= 1 non-positive tile is
    therefore the component boundary). Labelled-adjacent tiles (excl json flag) never become candidates. At most 20
    candidates, ranked by n_letters descending, then uuid.
    Block variant (DECL-P4-17, METRIC-HASH-38): when the jobs files were built with brief variant 'block', answers are
    validated against configs/reader_output_block.schema.json (tools/p4/block_schema.py), each tile also records
    n_marks and lines, and the count used everywhere above (N0 distribution, threshold, ranking) is n_letters + n_marks.
    All jobs files of one call must share one variant. Option --cand-cmin=N (any variant): tiles with c < N never
    become candidates (DECL-P4-17 known-text control windows c0-c8; the gate is read from the summary).
"""
import json
import os
import sys

sys.path.insert(0, 'src')

SCORER = '/srv/scorer'
SEALED = '/work/sealed_io'
JOBS = '/work/jobs'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
MIN_LETTERS = 5
MAX_CAND = 20


def load_keys():
    out = {}
    for f in sorted(os.listdir(SCORER)):
        if f.startswith('p4_key_') and f.endswith('.json'):
            out.update(json.load(open(f'{SCORER}/{f}')))
    return out


def tile_answer(ans_items, u):
    """(rows, n_letters, n_firm, right_nonempty) for image uuid u, or None if the reader gave no item for it."""
    a = tile_answer_full(ans_items, u)
    return None if a is None else a[:4]


def tile_answer_full(ans_items, u):
    """(rows, n_letters, n_firm, right_nonempty, n_marks, lines) for image uuid u, or None if no item for it."""
    for it in ans_items:
        if str(it.get('id', '')).strip() == u:
            left = it.get('left') or {}
            letters = [x for x in (left.get('letters') or []) if isinstance(x, dict) and x.get('ch')]
            marks = [x for x in (left.get('marks') or []) if isinstance(x, dict)]
            right = it.get('right') or {}
            return (left.get('rows'), len(letters), sum(1 for x in letters if x.get('conf') == 'firm'),
                    bool(right.get('letters')), len(marks), left.get('lines'))
    return None


def clusters(cells):
    """4-connected components of a set of (r, c)."""
    cells, comps = set(cells), []
    while cells:
        stack, comp = [cells.pop()], set()
        while stack:
            r, c = stack.pop()
            comp.add((r, c))
            for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if n in cells:
                    cells.remove(n)
                    stack.append(n)
        comps.append(comp)
    return comps


def candidates(census, p99, labelled, cand_cmin=None):
    """census: {uuid: {'strip','r','c','rows','n_letters'[,'n_count']}}; returns (positive uuids, candidate uuids).
    n_count (block variant) replaces n_letters when present."""
    thr = max(MIN_LETTERS, p99)
    cnt = {u: t.get('n_count', t['n_letters']) for u, t in census.items()}
    pos = {u for u, t in census.items() if t['rows'] == 'Y' and cnt[u] >= thr}
    cand = set()
    for strip in sorted({t['strip'] for t in census.values()}):
        at = {(census[u]['r'], census[u]['c']): u for u in pos if census[u]['strip'] == strip}
        if strip.startswith('w010') or '-w010-' in strip:  # 'w010-027' or '<segment ts>-w010-027' (DECL-P4-4)
            cand |= set(at.values())
            continue
        for comp in clusters(at.keys()):
            if len(comp) <= 4:
                cand |= {at[rc] for rc in comp}
    cand = [u for u in cand if not labelled.get(u, False)]
    if cand_cmin is not None:
        cand = [u for u in cand if census[u]['c'] >= cand_cmin]
    cand.sort(key=lambda u: (-cnt[u], u))
    return sorted(pos), cand[:MAX_CAND]


def cmd_census(jobs_files, excl_files, out, cand_cmin=None):
    import numpy as np
    from hercules.harness.collect import load_answer
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from block_schema import validate_for_variant
    variants = {json.load(open(jf)).get('variant', 'v1') for jf in jobs_files}
    assert len(variants) == 1, f'mixed brief variants {sorted(variants)}'
    variant = variants.pop()
    block = variant == 'block'
    keys = load_keys()
    labelled_rc = {}
    for f in excl_files:
        if f and os.path.exists(f):
            e = json.load(open(f))
            for k, v in e.get('tiles', {}).items():
                labelled_rc[(e.get('strip'), k)] = bool(v.get('labelled_adjacent'))
    census, null_counts, stats = {}, [], {'jobs': 0, 'valid': 0, 'invalid': 0, 'missing_items': 0, 'right_nonempty': 0}
    for jf in jobs_files:
        for j in json.load(open(jf))['jobs']:
            stats['jobs'] += 1
            rec = json.load(open(f"{JOBS}/{j['job']}.json"))
            if not rec.get('valid') or not os.path.exists(rec['out']):
                stats['invalid'] += 1
                continue
            ans = load_answer(rec['out'], 'score-p4-census')
            ok, _ = validate_for_variant(ans, variant)
            if not ok:
                stats['invalid'] += 1
                continue
            stats['valid'] += 1
            for p in rec['images'][1:]:
                u = os.path.basename(p)[:-4]
                k = keys[u]
                a = tile_answer_full(ans.get('items', []), u)
                if a is None:
                    stats['missing_items'] += 1
                    continue
                rows, n, nf, rn, nm, lines = a
                stats['right_nonempty'] += int(rn)
                cnt = n + nm if block else n
                if k['rot'] == 90:
                    null_counts.append(cnt)
                else:
                    census[u] = {'strip': k['strip'], 'r': k['r'], 'c': k['c'], 'rows': rows, 'n_letters': n,
                                 'n_firm': nf}
                    if block:
                        census[u].update(n_marks=nm, lines=lines, n_count=cnt)
    p99 = float(np.percentile(null_counts, 99)) if null_counts else float('nan')
    labelled = {u: labelled_rc.get((t['strip'], f"r{t['r']}_c{t['c']}"), False) for u, t in census.items()}
    pos, cand = candidates(census, p99 if null_counts else float('inf'), labelled, cand_cmin)
    res = {'provenance': PROV, 'serves': 'RULES.md DECL-P4-2 items 3-5' + (', DECL-P4-17' if block else ''),
           'variant': variant, 'count': 'n_letters + n_marks' if block else 'n_letters', 'cand_cmin': cand_cmin,
           'stats': stats,
           'n_census_tiles': len(census), 'n_null_tiles': len(null_counts), 'null_letter_counts': sorted(null_counts),
           'null_p99': p99, 'threshold': max(MIN_LETTERS, p99) if null_counts else None,
           'n_rows_Y': sum(1 for t in census.values() if t['rows'] == 'Y'),
           'n_positive': len(pos), 'n_labelled_adjacent': sum(labelled.values()),
           'tiles': {u: dict(t, labelled_adjacent=labelled[u]) for u, t in sorted(census.items())},
           'positive': pos, 'candidates': cand}
    with open(out, 'w') as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: res[k] for k in ('stats', 'n_census_tiles', 'n_null_tiles', 'null_p99', 'threshold',
                                         'n_rows_Y', 'n_positive', 'n_labelled_adjacent')}))
    print(json.dumps({'n_candidates': len(cand)}))


if __name__ == '__main__':
    if sys.argv[1] == 'census':
        opts = [a for a in sys.argv[5:] if a.startswith('--cand-cmin=')]
        cmd_census(sys.argv[2].split(','), sys.argv[3].split(','), sys.argv[4],
                   int(opts[0].split('=', 1)[1]) if opts else None)
