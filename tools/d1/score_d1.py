# Provenance: Project HERCULES | owner the owner | [id removed]
"""D1 scoring (RULES.md DECL-D1, -A1 .. -A5; hercules.scorer.d1drive + score_decision, METRIC-HASH-0).

Stage "ref": decision D1-REF, arms REF0/REF015/REF030/REF045 (state A) on the gated J windows + both blanks.
  VOID check: REF0 summed mean C_all (R250) < 0.5 S' (S' = seal letters on gated J windows). sigma_crit from
  the ladder's summed mean C_net.
Stage "model" (args: text_order fwd|rev, raw_text_side F|B, as recorded in RULES.md): decisions D1-FAMILY
  (BASE-A, BASE-B, RAW-A, RAW-B; p_max = max-T over these 4) and D1-CHANCE (CHANCE-A, CHANCE-B). Best family arm =
  highest summed mean C_net (ties: arm id). Outcome by d1drive.d1_outcome with C_all(CHANCE) of the same state.
Only audited-valid, schema-valid readers are scored (others are discarded and listed). Canary items are removed
and counted. n_perm 5000, seed 20260924. Full scorer outputs are age-encrypted to the scorer recipient
(/work/d1/results_<stage>.age, for the auditor); logs/d1/d1_<stage>_summary.json holds numbers only.
Usage: python tools/d1/score_d1.py ref | model <text_order> <raw_text_side>
"""
import json
import os
import sys

sys.path.insert(0, 'src')
from hercules.harness.collect import load_answer  # noqa: E402
from hercules.scorer.d1drive import (  # noqa: E402
    blank_namings_mean, d1_outcome, display_maps_for_job, filter_answer, max_mean_fb, seals_by_state,
    sigma_crit, state_window_id, void_check)
from hercules.scorer.keyaccess import decrypt_logged  # noqa: E402
from hercules.scorer.schema import validate_reader_output  # noqa: E402
from hercules.scorer.score import radius_key, score_decision  # noqa: E402
from hercules.scorer.seal import seal_encrypt  # noqa: E402

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
R250 = radius_key(250.0)
SIGMA = {'REF0': 0.0, 'REF015': 0.15, 'REF030': 0.30, 'REF045': 0.45}
# Paths and crypto are module attributes so the synthetic test can redirect them.
D1 = '/work/d1'
SCORER = '/srv/scorer'
JOBS = '/work/jobs'
SEALED = '/work/sealed_io'
SEAL_PATH = '/work/jseal/seal_J.age'
LOGS = 'logs/d1'
N_PERM = 5000


def _arm_summary(res, aid):
    a = res['arms'][aid]
    return {'n_readers': a['n_readers'], 'readers_missing': a['readers_missing'],
            'summed_mean_C_all_R250': a['summed_mean_C_all'][R250], 'summed_mean_C_net': a['summed_mean_C_net'],
            'summed_mean_C_firm_R250': a['summed_mean_C_firm'][R250], 'p': a['p'], 'p_exact': a['p_exact'],
            'F_B_mean_per_reader': a['F_B_mean_per_reader'], 'n_named_total': a['n_named_total'],
            'blank_namings_mean': blank_namings_mean(res, aid), 'max_window_mean_F_B': max_mean_fb(res, aid),
            'per_window_mean_C_all_R250': {w: (lambda v: sum(v) / len(v) if v else None)(
                [res['windows'][w]['readers'][r]['C_all'][R250] for r in a['readers_scored']
                 if res['windows'][w]['readers'][r]['status'] == 'scored']) for w in a['windows']}}


def main(stage, text_order='fwd', raw_side='F'):
    jl = json.load(open(f'{D1}/jobs_{stage}.json'))
    items = json.load(open(f'{SCORER}/d1_items_{stage}.json'))
    key = json.load(open(f'{SCORER}/d1_key.json'))
    seal = decrypt_logged(SEAL_PATH, f'd1-score-{stage}')
    gated = jl['gated_J']
    blanks = sorted(w for w, v in key['windows'].items() if v['set'] == 'blank')
    s_prime = sum(len(seal['windows'][w]['letters']) for w in gated)
    seals = seals_by_state({w: seal['windows'][w] for w in gated + blanks})
    outputs, dms, discarded, canary = {}, [], [], {}
    for j in jl['jobs']:
        job = j['job']
        rec = json.load(open(f'{JOBS}/{job}.json'))
        if rec.get('valid') is not True:
            discarded.append((j['arm'], j['reader'], 'invalid or not audited'))
            continue
        ans = load_answer(f'{SEALED}/{job}.age', f'd1-score-{stage}')
        filt, cnt = filter_answer(ans, items[job])
        ok, _ = validate_reader_output(filt)
        if not ok:
            discarded.append((j['arm'], j['reader'], 'malformed'))
            continue
        outputs[job] = filt
        canary[f"{j['arm']}_r{j['reader']}"] = cnt
        dms += display_maps_for_job(job, items[job], key['images'], text_order, raw_side)

    def decide(did, arms):
        decl = {'decision_id': did, 'arms': []}
        for aid in arms:
            st = 'B' if aid.endswith('-B') else 'A'
            readers = [j['job'] for j in jl['jobs'] if j['arm'] == aid]
            decl['arms'].append({'arm_id': aid, 'readers': readers,
                                 'windows': [state_window_id(w, st) for w in gated + blanks]})
        my = {d['reader_id'] for d in dms if any(d['reader_id'] in a['readers'] for a in decl['arms'])}
        return score_decision(decl, seals, {k: v for k, v in outputs.items() if k in my},
                              [d for d in dms if d['reader_id'] in my], n_perm=N_PERM)

    summary = {'provenance': PROV, 'stage': stage, 'gated_J': gated, 'S_prime_gated': s_prime,
               'discarded': discarded, 'canary_and_foreign': canary}
    full = {}
    if stage == 'ref':
        res = decide('D1-REF', list(SIGMA))
        full['D1-REF'] = res
        arms = {a: _arm_summary(res, a) for a in SIGMA}
        ladder = {SIGMA[a]: arms[a]['summed_mean_C_net'] for a in SIGMA}
        summary.update({'arms': arms, 'void': void_check(arms['REF0']['summed_mean_C_all_R250'], s_prime),
                        'void_rule': "REF0 summed mean C_all (R250) < 0.5 S'", 'sigma_crit_mm': sigma_crit(ladder),
                        'p_max_ref': res['decision']['p_max']})
    else:
        fam = decide('D1-FAMILY', ['BASE-A', 'BASE-B', 'RAW-A', 'RAW-B'])
        cha = decide('D1-CHANCE', ['CHANCE-A', 'CHANCE-B'])
        full.update({'D1-FAMILY': fam, 'D1-CHANCE': cha})
        arms = {a: _arm_summary(fam, a) for a in fam['arms']}
        carms = {a: _arm_summary(cha, a) for a in cha['arms']}
        best = max(sorted(arms), key=lambda a: arms[a]['summed_mean_C_net'])
        st = 'B' if best.endswith('-B') else 'A'
        out = d1_outcome(arms[best]['summed_mean_C_net'], arms[best]['summed_mean_C_all_R250'],
                         carms[f'CHANCE-{st}']['summed_mean_C_all_R250'], fam['decision']['p_max'],
                         arms[best]['max_window_mean_F_B'], arms[best]['blank_namings_mean'], s_prime)
        summary.update({'text_order': text_order, 'raw_text_side': raw_side, 'family_arms': arms, 'chance_arms': carms,
                        'best_family_arm': best, 'p_max_family': fam['decision']['p_max'],
                        'p_max_family_exact': fam['decision']['p_max_exact'], 'outcome': out})
    enc = f'{D1}/results_{stage}.age'
    assert not os.path.exists(enc)
    summary['full_results_sha256'] = seal_encrypt(full, open(f'{SCORER}/seal.agekey.pub').read().strip(), enc)
    os.makedirs(LOGS, exist_ok=True)
    json.dump(summary, open(f'{LOGS}/d1_{stage}_summary.json', 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    if sys.argv[1] == 'ref':
        main('ref')
    else:
        main('model', sys.argv[2], sys.argv[3])
