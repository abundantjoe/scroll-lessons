#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Self-test assembly for tools/unr/hairpin_trace.py (DECL-UNR-1 item 3 hairpin trace operator at 8.64 um).
The three runs it summarises (each a hairpin_trace.py invocation, 3 threads):
  phantom : hairpin_trace.py <W>/phantom --phantom 1 --tag phantom --S_mm 2.0        (code-path check; never evidence about 0268)
  win16   : hairpin_trace.py <W>/win16 --y 5820 --n 16 --z0 7936 --z1 8704 --x0 1280 --x1 2304 --tag win16
  full    : hairpin_trace.py <W>/full  --y 5820 --n 16 --z0 2040 --z1 14832 --x0 1280 --x1 4080 --tag full --tile_z 1024 --tile_ov 256
Writes <out>/selftest.json and copies the overlay PNGs. Phantom scoring: a trace is correct when arm-A ordinal == arm-B
ordinal (the nests are concentric); the seam lamina (ordinal > seam_after) must be rejected for 'seam'.
usage: hairpin_selftest.py <W: dir holding phantom/ win16/ full/> <out_dir>
"""
import glob, json, os, shutil, sys

def load(p): return json.load(open(p)) if os.path.exists(p) else None

def summarise(d):
    if d is None: return None
    acc = [r for r in d['records'] if r['status'] == 'HAIRPIN-TRACED']
    return {'origin_zyx_l0': d['origin_zyx_l0'], 'shape_nZX': d['shape_nZX'], 'trace_y': d['trace_y'], 'defects_trace_section': d['defects_trace_section'], 'n_apexes': d['n_apexes_attempted'], 'n_trace_attempts': d['n_trace_attempts'], 'n_accepted': d['n_accepted'],
            'rejection_reasons': d['rejection_reasons'], 'noise_mad': d['noise_mad'], 'signal_mad_trace_section': d['signal_mad_trace_section'], 'secs_prep': d['secs_prep'], 'secs_trace': d['secs_trace'], 'overlay_png': d['overlay_png'],
            'per_section_defects': d['per_section_defects'], 'accepted': [trace_brief(r) for r in acc]}

def trace_brief(r):
    return {'apex_xz': r['apex_refined_xz'], 'open_dir': r['open_dir'], 'arm_A': r['arm_A'], 'arm_B': r['arm_B'], 'nesting_equal': r['nesting_equal'], 'enclosed_plus_half': r['enclosed_plus_half'], 'enclosed_plus_half_strict': r['enclosed_plus_half_strict'], 'enclosed_minus_half': r['enclosed_minus_half'],
            'seam_px_inner_region': r['seam_px_inner_region'], 'min_dist_minus_half_mm': r['min_dist_minus_half_mm'], 'ridge_frac': r['ridge_frac'], 'ridge_frac_3mad': r['ridge_frac_3mad'], 'continuity': r['continuity'], 'fwd_rev_offset_vox': r['fwd_rev_offset_vox'], 'trace_len_vox': r['trace_len_vox'], 'n_polyline_pts': len(r['polyline_xz'])}

def main():
    W, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); S = {}
    ph = load(os.path.join(W, 'phantom', 'phantom.json')); tr = load(os.path.join(W, 'phantom', 'phantom_truth.json'))
    if ph:
        att = [r for r in ph['records'] if 'arm_A' in r]; acc = [r for r in att if r['status'] == 'HAIRPIN-TRACED']; correct = [r for r in acc if r['arm_A']['ordinal'] == r['arm_B']['ordinal']]
        seam_rej = [r for r in att if r['status'] != 'HAIRPIN-TRACED' and 'seam' in r.get('reason', '')]; seam_ok = [r for r in seam_rej if r['arm_A']['ordinal'] > tr['seam_after_ordinal']]
        S['phantom'] = {'truth': tr, 'params': ph['params'], 'defects_trace_section': ph['defects_trace_section'], 'n_apexes': ph['n_apexes_attempted'], 'n_trace_attempts': len(att), 'n_accepted': len(acc), 'pairing_correct': len(correct), 'pairing_correct_frac': round(len(correct) / max(1, len(acc)), 3),
                        'seam_rejections': len(seam_rej), 'seam_rejections_on_seam_laminae': len(seam_ok), 'rejection_reasons': ph['rejection_reasons'], 'continuity_sections': [r['continuity']['n_consecutive_sections'] for r in acc], 'mean_offset_vox': [r['continuity']['mean_offset_vox'] for r in acc], 'injected_tilt_vox_per_section': tr['tilt_vox_per_section'],
                        'traces': [trace_brief(r) for r in acc], 'rejected': [{'arm_A': r['arm_A'], 'reason': r.get('reason')} for r in att if r['status'] != 'HAIRPIN-TRACED']}
        shutil.copy(os.path.join(W, 'phantom', ph['overlay_png']), os.path.join(out, 'phantom_overlay.png'))
    w16 = load(os.path.join(W, 'win16', 'win16.json'))
    if w16:
        S['win16'] = summarise(w16); S['win16']['params'] = w16['params']; S['win16']['attempts'] = [{k: r.get(k) for k in ('apex_refined_xz', 'open_dir', 'fit_res', 'n_A', 'n_B', 'arm_A', 'arm_B', 'trace_status', 'trace_len_vox', 'ridge_frac', 'reason', 'status')} for r in w16['records']]
        shutil.copy(os.path.join(W, 'win16', w16['overlay_png']), os.path.join(out, 'win16_overlay.png'))
    tiles = sorted(glob.glob(os.path.join(W, 'full', 'full_z*.json')))
    if tiles:
        T = []; tot = {'plus_half_R0.5': 0, 'minus_half_R0.5': 0, 'plus_half_R1.0': 0, 'minus_half_R1.0': 0}; att = 0; acc_all = []; reasons = {}
        for t in tiles:
            d = json.load(open(t)); s = summarise(d); T.append({k: s[k] for k in ('origin_zyx_l0', 'shape_nZX', 'defects_trace_section', 'n_apexes', 'n_trace_attempts', 'n_accepted', 'rejection_reasons', 'noise_mad', 'secs_prep', 'secs_trace', 'overlay_png')})
            for k in tot: tot[k] += d['defects_trace_section'].get(k, 0)
            att += d['n_trace_attempts']
            for r in d['records']:
                if r['status'] == 'HAIRPIN-TRACED': acc_all.append(dict(trace_brief(r), tile=os.path.basename(t), origin_zyx_l0=d['origin_zyx_l0']))
                else: reasons[r.get('reason', '?')] = reasons.get(r.get('reason', '?'), 0) + 1
        S['full'] = {'note': 'z-tiles of 1024 overlapping by 256: defects in an overlap are counted in both tiles', 'n_tiles': len(T), 'defects_trace_section_summed': tot, 'n_trace_attempts': att, 'n_accepted': len(acc_all), 'rejection_reasons': reasons, 'tiles': T, 'accepted': acc_all[:50]}
        best = max(tiles, key=lambda t: json.load(open(t))['n_accepted'])
        if json.load(open(best))['n_accepted'] > 0:
            d = json.load(open(best)); shutil.copy(os.path.join(W, 'full', d['overlay_png']), os.path.join(out, 'full_best_overlay.png')); S['full']['best_tile_overlay'] = 'full_best_overlay.png'
    json.dump(S, open(os.path.join(out, 'selftest.json'), 'w'), indent=1)
    print(json.dumps({k: {kk: v[kk] for kk in v if kk in ('n_apexes', 'n_trace_attempts', 'n_accepted', 'pairing_correct', 'seam_rejections_on_seam_laminae', 'defects_trace_section', 'defects_trace_section_summed', 'rejection_reasons')} for k, v in S.items()}, indent=1))

if __name__ == '__main__': main()
