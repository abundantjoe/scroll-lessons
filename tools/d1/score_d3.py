# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 scoring (RULES.md DECL-D3D4, DECL-D3-A1; d1drive + d3drive + score_decision, METRIC-HASH-0/16).

Decisions: D3-FA (FA-A, FA-B; p_max = max-T over these two), D3-CTRL, D3-NULLA, D3-REVA (each both states).
Seal SEAL-J-D1 (state B mirrored); text order forward (TEXT-ORDER-D1); canary items removed and counted.
Blob-f180 values of FA's text-order map on the blanks come from the D3 build record (argument).
Full outputs age-encrypted (/work/d3/results_d3.age); counts-only summary logs/d1/d3_summary.json.
Usage: python tools/d1/score_d3.py <blob_json>   (blob_json: {"<blank window>": value, ...})
"""
import json
import os
import sys

sys.path.insert(0, 'src')
from hercules.harness.collect import load_answer  # noqa: E402
from hercules.scorer.d1drive import (  # noqa: E402
    blank_namings_mean, display_maps_for_job, filter_answer, max_mean_fb, seals_by_state, state_window_id)
from hercules.scorer.d3drive import d3_outcome, window_mean_c_net  # noqa: E402
from hercules.scorer.keyaccess import decrypt_logged  # noqa: E402
from hercules.scorer.schema import validate_reader_output  # noqa: E402
from hercules.scorer.score import radius_key, score_decision  # noqa: E402
from hercules.scorer.seal import seal_encrypt  # noqa: E402

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
R250 = radius_key(250.0)
D3 = '/work/d3'
SCORER = '/srv/scorer'
JOBS = '/work/jobs'
SEALED = '/work/sealed_io'
SEAL_PATH = '/work/jseal/seal_J.age'
LOGS = 'logs/d1'
N_PERM = 5000


def main(blob_path):
    blob = json.load(open(blob_path))
    jl = json.load(open(f'{D3}/jobs_d3.json'))
    items = json.load(open(f'{SCORER}/d3_items.json'))
    key = json.load(open(f'{SCORER}/d3_key.json'))
    seal = decrypt_logged(SEAL_PATH, 'd3-score')
    gated = jl['gated_J']
    blanks = sorted(w for w, v in key['windows'].items() if v['set'] == 'blank')
    assert set(blob) == set(blanks), (sorted(blob), blanks)
    s_prime = sum(len(seal['windows'][w]['letters']) for w in gated)
    seals = seals_by_state({w: seal['windows'][w] for w in gated + blanks})
    outputs, dms, discarded, canary = {}, [], [], {}
    for j in jl['jobs']:
        job = j['job']
        if json.load(open(f'{JOBS}/{job}.json')).get('valid') is not True:
            discarded.append((j['arm'], j['reader'], 'invalid or not audited'))
            continue
        filt, cnt = filter_answer(load_answer(f'{SEALED}/{job}.age', 'd3-score'), items[job])
        if not validate_reader_output(filt)[0]:
            discarded.append((j['arm'], j['reader'], 'malformed'))
            continue
        outputs[job] = filt
        canary[f"{j['arm']}_r{j['reader']}"] = cnt
        dms += display_maps_for_job(job, items[job], key['images'], 'fwd', 'F')

    def decide(did, arms):
        decl = {'decision_id': did, 'arms': []}
        for aid in arms:
            st = aid[-1]
            decl['arms'].append({'arm_id': aid, 'readers': [j['job'] for j in jl['jobs'] if j['arm'] == aid],
                                 'windows': [state_window_id(w, st) for w in gated + blanks]})
        my = {r for a in decl['arms'] for r in a['readers']}
        return score_decision(decl, seals, {k: v for k, v in outputs.items() if k in my},
                              [d for d in dms if d['reader_id'] in my], n_perm=N_PERM)

    full, arms, per_window = {}, {}, {}
    for name in ('FA', 'CTRL', 'NULLA', 'REVA'):
        res = decide(f'D3-{name}', [f'{name}-A', f'{name}-B'])
        full[f'D3-{name}'] = res
        for aid, a in res['arms'].items():
            arms[aid] = {'n_readers': a['n_readers'], 'summed_mean_C_all_R250': a['summed_mean_C_all'][R250],
                         'summed_mean_C_net': a['summed_mean_C_net'], 'p': a['p'], 'p_exact': a['p_exact'],
                         'F_B_mean_per_reader': a['F_B_mean_per_reader'], 'n_named_total': a['n_named_total'],
                         'blank_namings_mean': blank_namings_mean(res, aid), 'max_window_mean_F_B': max_mean_fb(res, aid)}
            per_window[aid] = window_mean_c_net(res, aid)
    p_max_fa = full['D3-FA']['decision']['p_max']
    out = d3_outcome(arms, p_max_fa, per_window, blob, s_prime)
    summary = {'provenance': PROV, 'gated_J': gated, 'S_prime_gated': s_prime, 'discarded': discarded,
               'canary_and_foreign': canary, 'arms': arms, 'per_window_mean_C_net': per_window,
               'p_max_fa': p_max_fa, 'p_max_fa_exact': full['D3-FA']['decision']['p_max_exact'],
               'blob_f180': blob, 'outcome': out}
    enc = f'{D3}/results_d3.age'
    assert not os.path.exists(enc)
    summary['full_results_sha256'] = seal_encrypt(full, open(f'{SCORER}/seal.agekey.pub').read().strip(), enc)
    os.makedirs(LOGS, exist_ok=True)
    json.dump(summary, open(f'{LOGS}/d3_summary.json', 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
