# Provenance: Project HERCULES | owner the owner | [id removed]
"""PROBE-3 scoring driver (RULES.md DECL-READCAL-PROBE3). Written and committed before any PROBE-3 answer is decrypted.

Audited-valid jobs only; answers decrypted with hercules.harness.collect.load_answer (logged); scorer
hercules.scorer.probe1 (METRIC-HASH-11) unchanged. PRIMARY: arm K_D2_A_fable, >= 5 agreed letters in at least
one window with identity-shuffle p < 0.05 there -> REPLICATED, else NOT REPLICATED. Other arms and the mirror
check (A > B summed per model) are reported only. Output: logs/readcal/probe3_results.json (statistics only;
no answer text is printed or stored).
Usage: python tools/readcal/score_probe3.py
"""
import json
import sys
from fractions import Fraction

sys.path.insert(0, 'src')
from hercules.harness.collect import load_answer, validate_reader  # noqa: E402
from hercules.scorer.probe1 import map_namings, score_arm  # noqa: E402

PRIMARY = 'K_D2_A_fable'
BAR_AGREED = 5
BAR_P = Fraction(1, 20)


def main():
    arms = json.load(open('/work/probe3/arms.json'))
    key = json.load(open('/srv/scorer/probe3_key.json'))
    imgs = key['images']
    windows = sorted({v['window'] for v in imgs.values()})
    per, bad, ks = {}, [], {}
    for a in arms:
        j = a['job']
        rec = json.load(open(f'/work/jobs/{j}.json'))
        if not rec.get('valid'):
            bad.append((a['arm'], a['reader'], 'invalid or not audited'))
            continue
        ans = load_answer(f'/work/sealed_io/{j}.age', 'probe3-final-scoring')
        if not validate_reader(ans):
            bad.append((a['arm'], a['reader'], 'malformed'))
            continue
        ks[f"{a['arm']}_r{a['reader']}"] = sum(len((it.get('left') or {}).get('letters', []))
                                               for it in ans.get('items', []) if it.get('id') not in imgs)
        per.setdefault(a['arm'], {})[f"r{a['reader']}"] = map_namings(ans, imgs)
    out = {}
    for arm in sorted(per):
        s = score_arm(per[arm], windows)
        out[arm] = {'n_readers': len(per[arm]), **s['total'],
                    'max_agreed_in_window': max(s['per_window'][w]['agreed'] for w in windows),
                    'per_window': {w: s['per_window'][w] for w in windows}}
    prim = out.get(PRIMARY)
    cells = []
    if prim and prim['n_readers'] == 3:
        cells = [w for w in windows if prim['per_window'][w]['agreed'] >= BAR_AGREED
                 and prim['per_window'][w]['shuffle_p'] is not None
                 and Fraction(prim['per_window'][w]['shuffle_p']) < BAR_P]
    verdict = 'REPLICATED' if cells else 'NOT REPLICATED'
    mirror = {m: (out.get(f'K_D2_A_{m}', {}).get('agreed'), out.get(f'K_D2_B_{m}', {}).get('agreed')) for m in ('opus', 'fable')}
    res = {'provenance': 'Provenance: Project HERCULES | owner the owner | [id removed]',
           'declaration': 'DECL-READCAL-PROBE3', 'scorer': 'hercules.scorer.probe1 (METRIC-HASH-11)',
           'windows': windows, 'invalid_or_malformed': bad, 'arms': out, 'primary_arm': PRIMARY,
           'primary_n_readers': prim['n_readers'] if prim else 0, 'primary_pass_windows': cells, 'verdict': verdict,
           'mirror_check_A_B': mirror, 'keysheet_item_namings': ks}
    json.dump(res, open('logs/readcal/probe3_results.json', 'w'), indent=1)
    for arm, v in out.items():
        print(f"{arm:14s} readers {v['n_readers']} named {v['named']:3d} agreed {v['agreed']:2d} firm {v['agreed_firm']} "
              f"per-window {[v['per_window'][w]['agreed'] for w in windows]} p {[v['per_window'][w]['shuffle_p'] for w in windows]}")
    print('windows', windows)
    print('invalid/malformed', bad)
    print('key-sheet namings', ks)
    print('mirror (A, B)', mirror)
    print('PRIMARY', PRIMARY, 'pass windows', cells, '->', verdict)


if __name__ == '__main__':
    main()
