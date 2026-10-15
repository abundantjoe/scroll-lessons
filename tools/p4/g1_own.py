# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN legibility gate G1 tally (RULES.md DECL-P4-23 item 6(b), DECL-P4-23-A1, DECL-P4-23-A2). Counts only.

usage: g1_own.py <out_json> <fold>:<sigma2t_census_summary>:<block_census_summary> [...]
  One argument per scored fold (f1, f2, f3); the summaries are tools/p4/score_p4.py census outputs of
  census_own_<fold> (sigma2t) and census_own_<fold>k (block).
  Non-blank denominator per fold (A2 item 1) = the census tiles in /srv/scorer/p4_key_own_<fold>{a,b}.json (rot 0);
  a tile without a valid answer counts as not rows Y.
  Per variant v (A2 item 2): Y_v = tiles with rows == 'Y' and n_letters >= 5 (block: n_marks NOT added).
  With all three folds: G1(v) PASS iff Y_v >= 0.30 x pooled non-blank. With fewer (A1 items 3-4): FAIL (futile) iff
  (Y_v + 24 u) < 0.30 x (NB + 24 u), u = number of unscored folds; otherwise PENDING (no early pass).
"""
import json
import os
import sys

BAR, MIN_LETTERS, MAXN = 0.30, 5, 24
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'


def census_uuids(fold):
    out = set()
    for x in ('a', 'b'):
        p = f'/srv/scorer/p4_key_own_{fold}{x}.json'
        if os.path.exists(p):
            out |= {u for u, v in json.load(open(p)).items() if v['rot'] == 0}
    return out


def main(out, *specs):
    folds = {}
    for s in specs:
        fold, sig, blk = s.split(':')
        assert fold in ('f1', 'f2', 'f3') and fold not in folds
        uu = census_uuids(fold)
        row = {'n_nonblank': len(uu)}
        for v, p in (('sigma2t', sig), ('block', blk)):
            d = json.load(open(p))
            assert d['variant'] == v, (p, d['variant'])
            t = d['tiles']
            assert set(t) <= uu, 'summary tile outside the fold keys'
            row[v] = {'n_answered': len(t),
                      'n_Y5': sum(1 for u in uu if u in t and t[u]['rows'] == 'Y' and t[u]['n_letters'] >= MIN_LETTERS)}
        folds[fold] = row
    u = 3 - len(folds)
    nb = sum(r['n_nonblank'] for r in folds.values())
    g1 = {}
    for v in ('sigma2t', 'block'):
        y = sum(r[v]['n_Y5'] for r in folds.values())
        if u == 0:
            verdict = 'PASS' if nb > 0 and y >= BAR * nb else 'FAIL'
        else:
            verdict = 'FAIL (futile)' if (y + MAXN * u) < BAR * (nb + MAXN * u) else 'PENDING'
        g1[v] = {'n_Y5': y, 'n_nonblank': nb, 'unscored_folds': u, 'fraction': (y / nb) if nb else None,
                 'verdict': verdict}
    res = {'provenance': PROV, 'serves': 'RULES.md DECL-P4-23 6(b), -A1, -A2', 'bar': BAR, 'folds': folds, 'G1': g1,
           'P4_OWN': ('informative in ' + ','.join(v for v in g1 if g1[v]['verdict'] == 'PASS')
                      if any(g1[v]['verdict'] == 'PASS' for v in g1) else
                      'uninformative' if all(g1[v]['verdict'].startswith('FAIL') for v in g1) else 'pending')}
    with open(out, 'w') as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({'G1': g1, 'P4_OWN': res['P4_OWN']}))


if __name__ == '__main__':
    main(*sys.argv[1:])
