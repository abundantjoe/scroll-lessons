# Provenance: Project HERCULES | owner the owner | [id removed]
"""Depth (along-normal) correspondence between the 8.64 um and 2.401 um surface volumes of a segment.
CT only. I9 = 8.64 um level 1 (17.28 um px), slices 14..16 mean (centre 15).
Each 2.401 um level-3 slice k in [K0, K1) (19.208 um px) is resampled onto the 9 um level-1 grid
through the corrected label map (global shift from reg.py), band-passed, and compared with I9 per tile
(128 x 128 L1 px ~ 2.2 mm) by NCC maximised over +-3 px in-plane.
Per tile: best k (parabolic sub-slice), NCC at best k and at the nominal centre k = 54.
Depth offset in 8.64 um vox = (k_best - 54) * 2.401 / 8.64 (positive = towards higher 2.4 um slice index).
Also: I9 slices 11 and 19 vs the 2.4 stack, giving the slope dk/ds9 (expected +3.6 if the two
normal directions agree, -3.6 if flipped)."""
import json, os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from svband import band
from reg import bandpass, SV9, SV2, ROOT, OUT

K0, K1, T, RR = 24, 85, 128, 3


def run(seg):
    of = f'{OUT}/{seg}.depth.json'
    if os.path.exists(of): return json.load(open(of))
    r = json.load(open(f'{OUT}/{seg}.json'))
    N9, N2 = r['N9'], r['N2']; d = r.get('global_shift_median', [0.0, 0.0])
    s9, za9, st9 = band(f'{ROOT}{seg}/{SV9}', 1, 10, 21)
    s2, za2, st2 = band(f'{ROOT}{seg}/{SV2}', 3, K0, K1)
    H1, W1 = s9.shape[1:]
    # L1 pixel centre in L0 canvas px = 2 x + 0.5; corrected map c2 = (c9 - d + 10) N2/N9 - 10; L3 index = (c2 - 3.5) / 8
    x9 = 2 * np.arange(W1) + 0.5 - d[0]; y9 = 2 * np.arange(H1) + 0.5 - d[1]
    mx = (((x9 + 10) * N2[0] / N9[0] - 10 - 3.5) / 8).astype(np.float32)
    my = (((y9 + 10) * N2[1] / N9[1] - 10 - 3.5) / 8).astype(np.float32)
    MX, MY = np.meshgrid(mx, my)
    v2 = (s2 > 0).all(0).astype(np.float32)
    vB = cv2.remap(v2, MX, MY, cv2.INTER_LINEAR) > 0.999
    v9 = (s9 > 0).all(0)
    B = [bandpass(cv2.remap(s2[i].astype(np.float32), MX, MY, cv2.INTER_LINEAR), vB) for i in range(K1 - K0)]
    out = dict(segment=seg, K=[K0, K1], shift_used=d, stream=dict(sv9=st9, sv2=st2), per_s9={})
    for s9i in (1, 5, 9):  # 9 um slices 11, 15, 19
        A = bandpass(s9[s9i - 1:s9i + 2].mean(0).astype(np.float32), v9)
        rows = []
        for y0 in range(RR, H1 - T - RR, T):
            for x0 in range(RR, W1 - T - RR, T):
                if v9[y0:y0 + T, x0:x0 + T].mean() < 0.98 or vB[y0 - RR:y0 + T + RR, x0 - RR:x0 + T + RR].mean() < 0.98: continue
                a = A[y0:y0 + T, x0:x0 + T]
                prof = np.array([cv2.matchTemplate(b[y0 - RR:y0 + T + RR, x0 - RR:x0 + T + RR], a, cv2.TM_CCOEFF_NORMED).max() for b in B])
                k = int(np.argmax(prof)); kk = float(k)
                if 0 < k < len(prof) - 1:
                    den = prof[k - 1] - 2 * prof[k] + prof[k + 1]
                    if den < 0: kk = k + 0.5 * (prof[k - 1] - prof[k + 1]) / den
                rows.append((x0, y0, kk + K0, float(prof[k]), float(prof[54 - K0]), k in (0, len(prof) - 1)))
        R = np.array(rows, dtype=float) if rows else np.zeros((0, 6))
        g = R[:, 3] >= 0.3 if len(R) else np.zeros(0, bool)
        out['per_s9'][str(10 + s9i)] = dict(n_tiles=len(R), n_good=int(g.sum()),
            k_best_median=float(np.median(R[g, 2])) if g.any() else None,
            k_best_p10_p90=np.percentile(R[g, 2], [10, 90]).tolist() if g.any() else None,
            ncc_best_median=float(np.median(R[g, 3])) if g.any() else None,
            ncc_at_k54_median=float(np.median(R[g, 4])) if g.any() else None,
            frac_at_stack_edge=float(R[g, 5].mean()) if g.any() else None,
            tiles=[[int(a), int(b), round(c, 2), round(e, 4), round(f, 4)] for a, b, c, e, f, _ in R])
    ks = [(int(s), v['k_best_median']) for s, v in out['per_s9'].items() if v['k_best_median'] is not None]
    if len(ks) >= 2:
        sl = np.polyfit([a for a, _ in ks], [b for _, b in ks], 1)
        out['slope_dk_ds9'] = float(sl[0]); out['k_at_s9_15'] = float(np.polyval(sl, 15))
        out['depth_offset_9vox_at_centre'] = float((np.polyval(sl, 15) - 54) * 2.401 / 8.64)
    json.dump(out, open(of, 'w'), indent=1)
    return out


if __name__ == '__main__':
    for s in sys.argv[1:]:
        o = run(s)
        print(s[:14], o.get('slope_dk_ds9'), o.get('k_at_s9_15'), o.get('depth_offset_9vox_at_centre'),
              {k: (v['n_good'], v['k_best_median'], v['ncc_best_median'], v['ncc_at_k54_median']) for k, v in o['per_s9'].items()}, flush=True)
