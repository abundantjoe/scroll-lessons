#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 stage X2 (item 4, as amended by the orchestrator): fused-lamina count by the along-stacking density
periodicity, at the scan's native 8.64 um (OME level 0; DECL-UNR-1-A1).

On a 16-section y-slab: stripe removal per xz section; 3-D structure tensor at the layering scales
(derivative sigma 2, integration sigma 16 voxels = one pitch, integrated over the 16 sections) for the local layering normal; a
normal is reliable where coherent (>= 0.3) and carrying gradient energy (fused interiors and gaps have none); the slab
is tiled 64 x 64 (z, x); a tile is admissible only where its reliable normals vary < 15 deg (p95) and the y-tilt (angle
between the normal and the section plane) is <= 15 deg. Rays are cast in the section plane along the projected tile
normal from every section and every 8th x of each admissible tile and are cut where a reliable local normal departs
> 15 deg from the ray (ray-normal angle) or the mask ends; widths and periods are multiplied by cos(y-tilt).
Runs of material (lamina peaks of prominence >= 3 MAD on the survey's definition, merged across valleys that do not
reach the gap level, extent at half contrast) are classed against the census single-sheet width w_s (14 voxels =
122 um): SHEET <= 1.4 w_s, PAIR 1.4-2.5 w_s, FUSED > 2.5 w_s; a run touching a ray end is not a whole run and is dropped.
Rays through one physical run are pooled by z-interval overlap between neighbouring rays (any tile).
Periodicity per group of rays (one section; wide runs also split into 128-voxel x-blocks): the analysed signal is the
interface-energy profile |d/ds G_1(density)| of the run with its end transitions trimmed (dips and level steps at the
sheet contacts both become pulses; the sheet-to-sheet density staircase, whose spectrum has a null at the sheet period
and a bump near twice it, disappears; in-sheet half-layer and fibre textures move to half their period); the
periodograms and autocorrelations of the group's rays are averaged (phase-free). Candidate periods = maxima of the mean
periodogram in [3 vox, T/1.5]; periods < 0.8 w_s (half-layer ~35 um and fibre-bundle 50-100 um harmonics) and > 2 w_s
(a single sheet inside a run is narrower than the PAIR limit) are REJECTED and recorded with their relative power; the
pitch = the shortest accepted line carrying >= 0.5 of the strongest accepted line and standing >= 1.5 above the local
broadband floor (the fundamental is the shortest member of its harmonic series). Per pooled run: pitch p10/p50/p90 over
the groups; count = T_p50 / pitch_p50, range [T_p50 / pitch_p90, T_p50 / pitch_p10], error = half the range; an
integer is claimed only when the error < 1 sheet AND the run is anchored on both sides by a gap-resolved SHEET-class
run (its first gap-resolved neighbour); no sheet index is given across a PAIR/FUSED run. The internal peak count of the
run (n_peaks) is recorded as an independent cross-check, never as the count.

Self-test (bar W1 of DECL-UNR-1 item 4): synthetic fused slabs, k = 2..8 sheets of thickness 10-18 voxels at zero gap,
with half-layer periodicity (4 vox), fibre-bundle texture (6-12 vox, in-plane and along the normal), per-sheet density
variation, a declared interface-contrast range, tilt, undulation, partial-volume blur and noise, embedded between
gap-resolved sheets; PASS = count within +-1 of k on >= 90 % of slabs; plus an interface-contrast sensitivity sweep and
a y-tilt negative control. The same code path runs on the synthetic slabs and on the real slab. A phantom pass is
evidence about the code path only, never about PHerc0268. No letters, no readings, no sheet index are claimed.

usage: fused_count.py selftest <out_dir> [--n_per_k 30 --seed 1]
       fused_count.py real <out_dir> --npy <slab.npy> [--meta <slab.npy.json>]
       fused_count.py real <out_dir> --src s3://.../0 --y 5820 --z 7936 8704 --x 1280 2304
"""
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '3')      # at most 3 threads
import argparse, json, sys, time, hashlib
import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from scipy.signal.windows import tukey
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb'))
from st_axis import stripe_removal

VOX = 8.64
P = {'w_s': 14.0, 'reject_below_ws': 0.8, 'accept_max_ws': 2.0, 'class_sheet': 1.4, 'class_pair': 2.5, 'sd': 2.0, 'si': 16.0, 'coh_min': 0.3, 'energy_min': 0.2, 'stride': 4, 'tile': 64,
     'tile_dev_deg': 15.0, 'ytilt_deg': 15.0, 'ray_dev_deg': 15.0, 'ray_len': 320, 'ray_dx': 8, 'min_run': 3, 'dip_mad': 3.0,
     'gap_frac': 0.30, 'width_frac': 0.5, 'min_rays': 6, 'group_dx': 128, 'min_group_rays': 3, 'min_groups': 6, 'min_cycles': 1.5, 'line_contrast': 1.5, 'edge_sigma': 1.0, 'edge_trim': 4, 'taper': 0.5, 'line_frac': 0.5, 'smooth': 1.5}

# ----------------------------------------------------------------------------------------------------- normal field
def normal_field(stack, p):
    """3-D structure tensor of the (n, Z, X) uint8 slab (y, z, x order), derivative sigma sd = 2 (the 4-voxel half-layer
    and most of the 6-12 voxel fibre texture are suppressed) and integration sigma si = 16 voxels (one pitch: the in-sheet
    fibre texture, whose phase is random from sheet to sheet, averages out over a pitch while the sheet/gap layering,
    coherent over several sheets, survives; at si = 8 the oriented fibre texture inside a fused block passed as a
    "reliable" normal and cut the rays there). Returns per stride-grid point the unit normal (n_y, n_z, n_x) with n_z >= 0, the
    coherence (l1 - l2) / (l1 + l2), the in-mask flag and the reliable-normal flag."""
    n, Z, X = stack.shape; s = p['stride']; mask = (stack > 0).mean(0) > 0.5
    v = np.empty(stack.shape, np.float32)
    for i in range(n): v[i] = stripe_removal(stack[i].astype(np.float32) / 255.0, mask)
    g = [ndi.gaussian_filter(v, p['sd'], order=o) for o in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]; del v
    J = np.zeros((Z // s, X // s, 3, 3), np.float32)
    for a in range(3):
        for b in range(a, 3):
            prod = ndi.gaussian_filter(g[a] * g[b], (p['si'] / 2.0, p['si'], p['si'])).mean(0)          # integrate over the 16 sections
            J[..., a, b] = J[..., b, a] = prod[s // 2::s, s // 2::s][:Z // s, :X // s]
    del g; w, e = np.linalg.eigh(J); nrm = e[..., :, 2]; nrm = nrm * np.where(nrm[..., 1:2] < 0, -1.0, 1.0)
    coh = (w[..., 2] - w[..., 1]) / (w[..., 2] + w[..., 1] + 1e-12); mg = mask[s // 2::s, s // 2::s][:Z // s, :X // s]; l1 = w[..., 2]
    rel = mg & (coh >= p['coh_min']) & (l1 >= p['energy_min'] * (np.median(l1[mg]) if mg.any() else 0))     # reliable layering normal: coherent AND gradient energy (fused interiors and gaps have none)
    return nrm.astype(np.float32), coh.astype(np.float32), mg, mask, rel

def mean_axis(vecs):
    """mean of axial (sign-free) unit vectors: principal eigenvector of the scatter matrix."""
    S = vecs.T @ vecs; w, e = np.linalg.eigh(S); m = e[:, -1]; return m * (1.0 if m[1] >= 0 else -1.0)

def admissible_tiles(nrm, coh, mgrid, rel, p):
    """per 64 x 64 (z, x) tile: mean normal, p95 angular deviation, y-tilt; admissible flags."""
    s, T = p['stride'], p['tile']; ts = T // s; gz, gx = nrm.shape[:2]; tiles = []
    for tz in range(0, gz - ts + 1, ts):
        for tx in range(0, gx - ts + 1, ts):
            m = mgrid[tz:tz + ts, tx:tx + ts]; c = coh[tz:tz + ts, tx:tx + ts]; sel = rel[tz:tz + ts, tx:tx + ts]
            rec = {'tz': tz * s, 'tx': tx * s, 'mask_frac': round(float(m.mean()), 3), 'n_pts': int(sel.sum()), 'reliable_frac': round(float(sel.mean()), 3)}
            if m.mean() < 0.6 or sel.sum() < 0.15 * ts * ts: rec['admissible'] = False; rec['why'] = 'mask'; tiles.append(rec); continue
            V = nrm[tz:tz + ts, tx:tx + ts][sel]; mn = mean_axis(V); dev = np.degrees(np.arccos(np.clip(np.abs(V @ mn), 0, 1)))
            ytilt = float(np.degrees(np.arcsin(min(1.0, abs(mn[0])))))
            rec.update({'normal_yzx': [round(float(q), 4) for q in mn], 'dev_p95_deg': round(float(np.percentile(dev, 95)), 2), 'ytilt_deg': round(ytilt, 2), 'coh_median': round(float(np.median(c[sel])), 3)})
            ok = rec['dev_p95_deg'] < p['tile_dev_deg'] and ytilt <= p['ytilt_deg']; rec['admissible'] = bool(ok)
            if not ok: rec['why'] = 'normal varies >= %g deg' % p['tile_dev_deg'] if rec['dev_p95_deg'] >= p['tile_dev_deg'] else 'y-tilt > %g deg' % p['ytilt_deg']
            tiles.append(rec)
    return tiles

# ------------------------------------------------------------------------------------------------------------- rays
def cast_ray(sec_s, sec_raw, mask, nrm, rel, z0, x0, mn, p):
    """profile along the in-plane projected normal through (z0, x0) of one smoothed section; cut where a reliable local
    3-D normal departs > ray_dev_deg from the tile normal or the mask ends. Returns samples, their (z, x) and the cos(y-tilt)."""
    dz, dx = mn[1], mn[2]; nn = np.hypot(dz, dx) + 1e-12; dz, dx = dz / nn, dx / nn; cosy = float(nn)       # |n_y| = sin(y-tilt)
    L = p['ray_len']; t = np.arange(-L // 2, L // 2, dtype=np.float32); zz, xx = z0 + t * dz, x0 + t * dx; Z, X = mask.shape
    inside = (zz >= 0) & (zz <= Z - 1) & (xx >= 0) & (xx <= X - 1)
    zi, xi = np.clip(zz, 0, Z - 1).astype(int), np.clip(xx, 0, X - 1).astype(int); s = p['stride']
    gi, gk = np.clip(zi // s, 0, nrm.shape[0] - 1), np.clip(xi // s, 0, nrm.shape[1] - 1)
    ok = inside & mask[zi, xi] & (~rel[gi, gk] | (np.abs(nrm[gi, gk] @ mn) >= np.cos(np.radians(p['ray_dev_deg']))))
    c = L // 2; lo = c
    while lo > 0 and ok[lo - 1]: lo -= 1
    hi = c
    while hi < L - 1 and ok[hi + 1]: hi += 1
    if not ok[c] or hi - lo < 4 * p['w_s']: return None
    prof = ndi.map_coordinates(sec_s, [zz[lo:hi + 1], xx[lo:hi + 1]], order=1, mode='nearest'); raw = ndi.map_coordinates(sec_raw, [zz[lo:hi + 1], xx[lo:hi + 1]], order=1, mode='nearest')
    return prof.astype(np.float32), zz[lo:hi + 1], xx[lo:hi + 1], cosy, raw.astype(np.float32)

def segment_runs(prof, p):
    """material runs along one ray. Lamina peaks on the survey's definition (UNR-X0-SURVEY-RESULT, core_native.py):
    prominence >= dip_mad x MAD (MAD of the profile), width >= min_run. Two adjacent peaks are MERGED into one run when
    the valley between them does not reach the gap level thr_gap = lo + gap_frac (hi - lo) (lo = median of the lowest
    10 %, hi = median of the highest 30 % of the ray): the merged run keeps its internal peak count (n_peaks, an
    independent cross-check of the periodicity count). A run's extent is where the profile crosses thr_w = lo +
    width_frac (hi - lo) outward from its first and last peak (width_frac 0.5: the full width at half contrast, the
    survey's half-prominence width for a single resolved sheet). A run is gap-resolved on a side when it has a
    neighbour there and the valley between them reaches the gap level.
    Returns (runs, thr_w, mad); run = {a, b (sample index, [a, b)), n_peaks, resolved_lo, resolved_hi}."""
    q = np.sort(prof); n = len(q); lo, hi = float(np.median(q[:max(3, int(0.1 * n))])), float(np.median(q[-max(3, int(0.3 * n)):]))
    thr_g, thr_w = lo + p['gap_frac'] * (hi - lo), lo + p['width_frac'] * (hi - lo); mad = float(np.median(np.abs(prof - np.median(prof)))) + 1e-6
    pk, pr = find_peaks(prof, prominence=p['dip_mad'] * mad, width=p['min_run']); runs = []
    for k in pk:                                                                                          # merge over unresolved valleys
        k = int(k)
        if runs and float(prof[runs[-1]['k_last']:k + 1].min()) > thr_g: runs[-1]['n_peaks'] += 1; runs[-1]['k_last'] = k; continue
        runs.append({'n_peaks': 1, 'k_first': k, 'k_last': k})
    for run in runs:
        a = run['k_first']
        while a > 0 and prof[a - 1] >= thr_w: a -= 1
        b = run['k_last'] + 1
        while b < n and prof[b] >= thr_w: b += 1
        run['a'], run['b'] = a, b
    runs = [r for r in runs if r['b'] - r['a'] >= p['min_run']]
    for i, run in enumerate(runs):
        run['resolved_lo'] = bool(i > 0 and run['a'] >= runs[i - 1]['b']); run['resolved_hi'] = bool(i + 1 < len(runs) and runs[i + 1]['a'] >= run['b'])
    return runs, thr_w, mad

def classify(width_true, p):
    w = p['w_s']
    if width_true <= p['class_sheet'] * w: return 'SHEET'
    if width_true <= p['class_pair'] * w: return 'PAIR'
    return 'FUSED'

def acf_unbiased(x, maxlag):
    n = len(x); nf = 1 << int(np.ceil(np.log2(2 * n))); F = np.fft.rfft(x, nf); r = np.fft.irfft(F * np.conj(F), nf)[:maxlag + 1]
    r = r / (n - np.arange(maxlag + 1)); return r / (r[0] + 1e-12)

def edge_signal(seg, p):
    """the analysed interface-energy signal of one run segment (true-voxel samples): detrended, tapered |d/ds G_1(seg)|.
    The edge_trim samples at each end (the run's own sheet/gap transitions, whose two large pulses would ripple the
    spectrum at integer fractions of the run thickness) are removed. A sheet-to-sheet contact is where the density
    changes, as a dip or as a level step, so both become pulses at the interfaces, the sheet-to-sheet density staircase (whose spectrum has a null at the sheet period and a bump near
    twice it) disappears, and the in-sheet half-layer and fibre textures move to half their period, deeper into the
    rejected band."""
    e = np.abs(np.gradient(ndi.gaussian_filter1d(np.asarray(seg, np.float64), p['edge_sigma'])))[p['edge_trim']:len(seg) - p['edge_trim']]   # the run's own end transitions are trimmed
    N = len(e); t = np.arange(N, dtype=np.float64); return (e - np.polyval(np.polyfit(t, e, 1), t)) * tukey(N, p['taper'])

NFFT = 4096

def periodicity(segs, p):
    """period analysis of one group of rays through the same PAIR/FUSED run (segs = unsmoothed density samples along
    each ray, resampled to true voxels). Per ray: the interface-energy signal, its periodogram (normalised to unit power
    in the candidate band) and its unbiased autocorrelation; both are averaged over the rays (phase-free, no alignment
    needed). Candidates = maxima of the mean periodogram in [3 vox, T / min_cycles]; score = log P(f) + 0.5 log P(2f)
    (a fundamental carries its second harmonic, a sub-harmonic does not); periods < 0.8 w_s and > accept_max_ws x w_s are
    REJECTED and recorded with their relative power; the best accepted candidate is refined on the mean autocorrelation
    peak (+-20 %), which must exceed acf_min. Cross-checks recorded: the first autocorrelation maximum above the
    rejected band (acf_first_peak) and the plain periodogram maximum (spectral_max_period)."""
    segs = [np.asarray(q, np.float64) for q in segs if len(q) >= 8 + 2 * p['edge_trim']]
    if not segs: return {'pitch': None, 'why': 'short', 'candidates': [], 'rejected': [], 'n_rays': 0}
    Ns = np.array([len(q) for q in segs]); T = float(np.median(Ns)); Ne = Ns - 2 * p['edge_trim']; f = np.fft.rfftfreq(NFFT, 1.0)
    with np.errstate(divide='ignore'): per = np.where(f > 0, 1.0 / np.maximum(f, 1e-12), np.inf)
    band = (per >= 3.0) & (per <= T / p['min_cycles']); idx = np.nonzero(band)[0]
    if len(idx) < 3: return {'pitch': None, 'why': 'no band', 'candidates': [], 'rejected': [], 'n_rays': len(segs)}
    maxlag = int(min(Ne.max() - 2, np.ceil(T / p['min_cycles']))); Pm = np.zeros(len(f)); rm = np.zeros(maxlag + 1); rc = np.zeros(maxlag + 1); nr = 0
    for q in segs:
        x = edge_signal(q, p)
        if np.std(x) < 1e-9: continue
        Pw = np.abs(np.fft.rfft(x, NFFT)) ** 2; Pm += Pw / (Pw[idx].sum() + 1e-20); ml = min(maxlag, len(x) - 2); rm[:ml + 1] += acf_unbiased(x, ml); rc[:ml + 1] += 1; nr += 1
    if nr == 0: return {'pitch': None, 'why': 'flat', 'candidates': [], 'rejected': [], 'n_rays': len(segs)}
    Pm /= nr; r = rm / np.maximum(rc, 1); r[rc < max(1, nr // 2)] = 0.0; Pb = Pm[idx]; pk, _ = find_peaks(Pb); cands = []
    if len(pk) == 0: pk = np.array([int(np.argmax(Pb))])
    pmax = float(Pb.max()) + 1e-20; ptot = float(Pb.sum()) + 1e-20; floor = 1e-6 * pmax
    for k in pk:
        i = idx[k]; i2 = min(2 * i, len(Pm) - 1); score = float(np.log(Pm[i] + floor) + 0.5 * np.log(Pm[i2] + floor))
        cands.append({'period': round(float(per[i]), 2), 'rel_power': round(float(Pm[i] / pmax), 4), 'frac_power': round(float(Pm[i] / ptot), 4), 'score': round(score, 3)})
    cands.sort(key=lambda d: -d['rel_power']); rej_lim = p['reject_below_ws'] * p['w_s']; acc_max = p['accept_max_ws'] * p['w_s']
    rejected = [dict(d, why='< 0.8 w_s') for d in cands if d['period'] < rej_lim] + [dict(d, why='> %g w_s' % p['accept_max_ws']) for d in cands if d['period'] > acc_max]
    accepted = [d for d in cands if rej_lim <= d['period'] <= acc_max]; lags = np.arange(maxlag + 1, dtype=float)
    Ne_med = float(np.median(Ne))
    def contrast_of(period):                                                                              # line contrast over the local broadband floor: median of the mean periodogram within a factor 3 of the line, the line excluded over one resolution cell (+-max(12 %, period / N) of the period)
        i = int(np.argmin(np.abs(per - period))); ex = max(0.12, period / Ne_med); fl = (per >= period / 3.0) & (per <= period * 3.0) & (np.abs(per - period) > ex * period) & band
        floor_v = float(np.median(Pm[fl])) if fl.sum() >= 5 else float(np.median(Pb)); return float(Pm[i] / (floor_v + 1e-20))
    for d in cands: d['contrast'] = round(contrast_of(d['period']), 3)
    if accepted:                                                                                          # the fundamental is the shortest member of its harmonic series: the shortest accepted line with >= line_frac of the strongest accepted line AND >= line_contrast over its local floor
        amax = max(d['rel_power'] for d in accepted); strong = [d for d in accepted if d['rel_power'] >= p['line_frac'] * amax and d['contrast'] >= p['line_contrast']]
        accepted = sorted(strong, key=lambda d: d['period']) + sorted([d for d in accepted if d not in strong], key=lambda d: -d['rel_power'])
    apk, _ = find_peaks(r); apk = [int(q) for q in apk if lags[q] >= rej_lim and r[q] > 0]
    out = {'n_rays': nr, 'T_true': round(T, 2), 'candidates': cands[:8], 'rejected': rejected[:8], 'n_rejected': len(rejected), 'acf_first_peak': round(float(lags[apk[0]]), 2) if apk else None, 'spectral_max_period': round(float(per[idx[int(np.argmax(Pb))]]), 2)}
    if not accepted: out.update({'pitch': None, 'why': 'no accepted period'}); return out
    best = accepted[0]; i0 = int(np.argmin(np.abs(per - best['period'])))                                       # line position: parabolic interpolation of the mean periodogram in frequency
    if 0 < i0 < len(Pm) - 1:
        y0, y1, y2 = np.log(Pm[i0 - 1] + floor), np.log(Pm[i0] + floor), np.log(Pm[i0 + 1] + floor); den = y0 - 2 * y1 + y2; d = (y0 - y2) / (2 * den) if den != 0 else 0.0; f0 = f[i0] + float(np.clip(d, -1, 1)) * (f[1] - f[0])
    else: f0 = f[i0]
    pitch = 1.0 / max(f0, 1e-9)
    contrast = best['contrast']
    lag = int(round(pitch)); acf_v = float(r[lag]) if 0 <= lag <= maxlag else float('nan')
    out.update({'pitch_spectral': round(float(best['period']), 2), 'line_contrast': round(contrast, 3), 'acf_at_pitch': round(acf_v, 3), 'rel_power': best['rel_power'], 'frac_power': best['frac_power'], 'score': best['score']})
    if contrast < p['line_contrast']: out.update({'pitch': None, 'why': 'line contrast %.2f < %g over the local floor' % (contrast, p['line_contrast'])}); return out
    sub = [d for d in rejected if d['period'] < rej_lim and d['rel_power'] > best['rel_power'] and any(abs(pitch / d['period'] - m) < 0.1 * m for m in (2, 3))]
    out['subharmonic_of_rejected'] = round(float(sub[0]['period']), 2) if sub else None                      # a STRONGER rejected-band line at 1/2 or 1/3 of the pitch: a periodic signal has harmonics, never sub-harmonics, so the pitch is then likely an artefact of a rejected fundamental (a true fundamental's own harmonic at half its period is the weaker line)
    out.update({'pitch': round(float(pitch), 3), 'acf': [round(float(v), 4) for v in r], 'spectrum_band': [[round(float(per[i]), 2), round(float(Pm[i] / pmax), 4)] for i in idx[::max(1, len(idx) // 200)]]})
    return out

# -------------------------------------------------------------------------------------------------------- the stage
def analyse_slab(stack, p, keep_examples=6):
    """X2 on one (n, Z, X) uint8 slab. Returns the record: tiles, runs (pooled), sheet-width statistics, examples."""
    t0 = time.time(); n, Z, X = stack.shape; nrm, coh, mgrid, mask, rel = normal_field(stack, p); tiles = admissible_tiles(nrm, coh, mgrid, rel, p)
    raws = [stripe_removal(stack[i].astype(np.float32) / 255.0, mask) for i in range(n)]; secs = [ndi.gaussian_filter(r_, p['smooth']) for r_ in raws]   # segmentation on the smoothed section, periodicity on the unsmoothed one
    recs = []; sheet_w = []; n_rays = 0; n_rays_cut = 0; n_trunc = 0; examples = []
    for ti, tile in enumerate(tiles):
        if not tile['admissible']: continue
        mn = np.array(tile['normal_yzx'], np.float32); zc = tile['tz'] + p['tile'] // 2
        for xo in range(p['ray_dx'] // 2, p['tile'], p['ray_dx']):
            x0 = tile['tx'] + xo
            for i in range(n):
                ray = cast_ray(secs[i], raws[i], mask, nrm, rel, zc, x0, mn, p)
                if ray is None: n_rays_cut += 1; continue
                prof, zz, xx, cosy, raw = ray; n_rays += 1; runs, thr, mad = segment_runs(prof, p)
                n_trunc += int(bool(runs) and runs[0]['a'] == 0) + int(bool(runs) and runs[-1]['b'] == len(prof)); runs = [q for q in runs if q['a'] > 0 and q['b'] < len(prof)]   # a run touching a ray end is not a whole run
                for r, run in enumerate(runs):
                    wt = (run['b'] - run['a']) * cosy; cls = classify(wt, p); run['class'] = cls; run['w_true'] = wt
                    if cls == 'SHEET' and run['resolved_lo'] and run['resolved_hi']: sheet_w.append(wt)
                for r, run in enumerate(runs):
                    if run['class'] == 'SHEET': continue
                    nb_lo = runs[r - 1]['class'] if r > 0 else None; nb_hi = runs[r + 1]['class'] if r + 1 < len(runs) else None
                    segm = raw[run['a']:run['b']].astype(np.float64); n_true = int(np.floor((len(segm) - 1) * cosy)) + 1
                    seg_true = np.interp(np.arange(n_true, dtype=np.float64), np.arange(len(segm)) * cosy, segm)                  # resampled to true voxels (cos y-tilt)
                    zm, xm = float(zz[(run['a'] + run['b']) // 2]), float(xx[(run['a'] + run['b']) // 2])
                    rec = {'tile': ti, 'sec': i, 'x0': x0, 'z_mid': zm, 'x_mid': xm, 'za': float(zz[run['a']]), 'zb': float(zz[run['b'] - 1]), 'T': run['w_true'], 'class': run['class'], 'resolved': [run['resolved_lo'], run['resolved_hi']],
                           'nb': [nb_lo, nb_hi], 'anchored': bool(run['resolved_lo'] and run['resolved_hi'] and nb_lo == 'SHEET' and nb_hi == 'SHEET'), 'seg': seg_true, 'cosy': cosy, 'n_peaks': run['n_peaks']}
                    recs.append(rec)
                    if len(examples) < keep_examples and rec['anchored'] and run['class'] == 'FUSED' and i == n // 2:
                        examples.append({'prof': prof.tolist(), 'raw': raw.tolist(), 'thr': thr, 'a': run['a'], 'b': run['b'], 'runs': [(q['a'], q['b'], q['class']) for q in runs], 'cosy': cosy, 'tile': ti, 'sec': i, 'x0': x0, 'z_mid': zm})
    pooled = pool_runs(recs, p)
    for ex in examples:                                                                                   # attach the pooled run and its group periodicity to each example profile
        cand = [r for r in pooled if abs(r['z_mid'] - ex['z_mid']) < 0.5 * r['T_vox']['p50'] + 8]
        if cand:
            run_ = max(cand, key=lambda r: r['n_rays']); ex['run'] = {k_: v_ for k_, v_ in run_.items() if k_ != 'groups'}
            gr = [r for r in recs if r['sec'] == ex['sec'] and int(r['x0'] // p['group_dx']) == int(ex['x0'] // p['group_dx']) and abs(r['z_mid'] - ex['z_mid']) < 0.5 * run_['T_vox']['p50'] + 8]
            ex['per'] = periodicity([r['seg'] for r in gr], p) if gr else {}
    sw = np.array(sheet_w) if sheet_w else np.zeros(0)
    out = {'secs': round(time.time() - t0, 1), 'shape': [n, Z, X], 'n_tiles': len(tiles), 'n_tiles_admissible': int(sum(t['admissible'] for t in tiles)), 'tiles': tiles, 'n_rays': n_rays, 'n_rays_cut': n_rays_cut, 'n_runs_truncated': n_trunc,
           'sheet_width_vox': {'n': int(sw.size), 'p10': round(float(np.percentile(sw, 10)), 2) if sw.size else None, 'p50': round(float(np.median(sw)), 2) if sw.size else None, 'p90': round(float(np.percentile(sw, 90)), 2) if sw.size else None},
           'n_ray_runs': {c: int(sum(r['class'] == c for r in recs)) for c in ('PAIR', 'FUSED')}, 'runs': pooled, 'examples': [e for e in examples if e.get('per', {}).get('pitch')]}
    return out

def pool_runs(recs, p):
    """union-find over ray runs: neighbouring rays (the same section and x from any tile, the adjacent section at the
    same x, or the adjacent x in the same section), z-interval IoU >= 0.5 -> one physical run."""
    n = len(recs); par = list(range(n))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    key = {}
    for i, r in enumerate(recs): key.setdefault((r['sec'], r['x0']), []).append(i)
    def iou(a, b):
        lo, hi = max(a['za'], b['za']), min(a['zb'], b['zb']); return max(0.0, hi - lo) / (max(a['zb'], b['zb']) - min(a['za'], b['za']) + 1e-9)
    for i, r in enumerate(recs):
        for nb in ((r['sec'], r['x0']), (r['sec'] + 1, r['x0']), (r['sec'], r['x0'] + p['ray_dx'])):
            for j in key.get(nb, []):
                if j != i and iou(r, recs[j]) >= 0.5: par[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    out = []
    for g in groups.values():
        rs = [recs[i] for i in g]; T = np.array([r['T'] for r in rs]); obs = [r for r in rs if r['nb'][0] is not None and r['nb'][1] is not None]
        grp = {}; xs_ = sorted(set(r['x0'] for r in rs)); wide = (xs_[-1] - xs_[0]) >= 2 * p['group_dx']       # groups: one section (all x of the run); a run wider than 2 group_dx is also split into group_dx x-blocks
        for r in rs: grp.setdefault((r['sec'], int(r['x0'] // p['group_dx']) if wide else 0), []).append(r)
        gres = []
        for gk, gr in grp.items():
            if len(gr) < p['min_group_rays']: continue
            pr = periodicity([r['seg'] for r in gr], p); gres.append({'sec': gk[0], 'xblock': gk[1], 'n_rays': len(gr), 'T': round(float(np.median([r['T'] for r in gr])), 2), 'pitch': pr.get('pitch'), 'acf_at_pitch': pr.get('acf_at_pitch'), 'line_contrast': pr.get('line_contrast'), 'rel_power': pr.get('rel_power'), 'score': pr.get('score'), 'why': pr.get('why'), 'acf_first_peak': pr.get('acf_first_peak'), 'spectral_max_period': pr.get('spectral_max_period'), 'subharmonic_of_rejected': pr.get('subharmonic_of_rejected'), 'rejected': pr.get('rejected', []), 'candidates': pr.get('candidates', [])})
        pit = np.array([q['pitch'] for q in gres if q['pitch']])
        anch = float(np.mean([r['anchored'] for r in obs])) if len(obs) >= p['min_rays'] else 0.0                   # anchoring is voted only by rays that observe a whole neighbour run on both sides
        rej = [d for q in gres for d in q['rejected']]; rej_p = np.array([d['period'] for d in rej]) if rej else np.zeros(0)
        cls_vote = max(('PAIR', 'FUSED'), key=lambda c: sum(r['class'] == c for r in rs)); T50 = float(np.median(T))
        rec = {'tiles': sorted(set(r['tile'] for r in rs)), 'n_rays': len(rs), 'n_groups': len(gres), 'n_groups_with_pitch': int(pit.size), 'z_mid': round(float(np.median([r['z_mid'] for r in rs])), 1), 'x_mid': round(float(np.median([r['x_mid'] for r in rs])), 1),
               'secs': [int(min(r['sec'] for r in rs)), int(max(r['sec'] for r in rs))], 'class': cls_vote, 'T_vox': {'p10': round(float(np.percentile(T, 10)), 2), 'p50': round(T50, 2), 'p90': round(float(np.percentile(T, 90)), 2)},
               'T_um': round(T50 * VOX, 1), 'n_peaks_p50': float(np.median([r['n_peaks'] for r in rs])), 'anchored_frac': round(anch, 2), 'n_rays_both_neighbours': len(obs), 'nb_classes': {c: int(sum((r['nb'][0] == c) + (r['nb'][1] == c) for r in obs)) for c in ('SHEET', 'PAIR', 'FUSED')}, 'T_over_ws': round(T50 / p['w_s'], 2),
               'rejected_periods': {'n': int(rej_p.size), 'p50': round(float(np.median(rej_p)), 2) if rej_p.size else None, 'p10': round(float(np.percentile(rej_p, 10)), 2) if rej_p.size else None, 'p90': round(float(np.percentile(rej_p, 90)), 2) if rej_p.size else None,
                                    'rel_power_p50': round(float(np.median([d['rel_power'] for d in rej])), 3) if rej else None}}
        rec['groups'] = [{k_: v_ for k_, v_ in q.items() if k_ not in ('candidates',)} for q in gres]
        if pit.size < p['min_groups']: rec.update({'count': None, 'status': 'UNRESOLVED', 'why': 'fewer than %d ray groups with an accepted period (%d of %d groups, %d rays)' % (p['min_groups'], pit.size, len(gres), len(rs))}); out.append(rec); continue
        p10, p50, p90 = (float(np.percentile(pit, q)) for q in (10, 50, 90)); cnt = T50 / p50; lo, hi = T50 / p90, T50 / p10; err = 0.5 * (hi - lo)
        rec.update({'pitch_vox': {'p10': round(p10, 2), 'p50': round(p50, 2), 'p90': round(p90, 2)}, 'pitch_um': round(p50 * VOX, 1), 'count': round(cnt, 2), 'count_range': [round(lo, 2), round(hi, 2)], 'count_err': round(err, 2),
                    'count_per_group': {'p10': round(float(np.percentile([q['T'] / q['pitch'] for q in gres if q['pitch']], 10)), 2), 'p50': round(float(np.median([q['T'] / q['pitch'] for q in gres if q['pitch']])), 2), 'p90': round(float(np.percentile([q['T'] / q['pitch'] for q in gres if q['pitch']], 90)), 2)},
                    'acf_at_pitch_p50': round(float(np.median([q['acf_at_pitch'] for q in gres if q['pitch']])), 3), 'line_contrast_p50': round(float(np.median([q['line_contrast'] for q in gres if q['pitch']])), 3)})
        subf = float(np.mean([q['subharmonic_of_rejected'] is not None for q in gres if q['pitch']])); rec['subharmonic_flag_frac'] = round(subf, 2)
        if anch < 0.5: rec.update({'integer': None, 'status': 'UNANCHORED', 'why': 'no gap-resolved SHEET neighbour on both sides for most rays'})
        elif subf >= 0.5: rec.update({'integer': None, 'status': 'SUBHARMONIC_RISK', 'why': 'a stronger rejected-band period (< 0.8 w_s) lies at 1/2 or 1/3 of the pitch in >= 50 %% of the groups (rejected p50 %s vox): the pitch may be its sub-harmonic, no integer' % rec['rejected_periods']['p50']})
        elif err >= 1.0: rec.update({'integer': None, 'status': 'NO_INTEGER', 'why': 'error >= 1 sheet'})
        else: rec.update({'integer': int(round(cnt)), 'status': 'COUNTED'})
        out.append(rec)
    out.sort(key=lambda r: (r['x_mid'] // p['tile'], r['z_mid'])); return out

# ---------------------------------------------------------------------------------------------------- synthetic slabs
GEN = {'n_sec': 16, 'Z': 384, 'X': 192, 't_range': [10.0, 18.0], 't_jitter': 0.5, 'k_range': [2, 8], 'n_embed': [1, 3], 'gap_range': [6, 40], 'gap_level': [0.12, 0.28],
       'sheet_level': [0.55, 0.80], 'sheet_var': 0.06, 'half_layer_period': 4.0, 'half_layer_amp': [0.02, 0.08], 'fibre_period': [6.0, 12.0], 'fibre_amp_inplane': [0.03, 0.10], 'fibre_amp_normal': [0.02, 0.08],
       'iface_depth': [0.10, 0.50], 'iface_width': [1.5, 3.0], 'tilt_x_deg': 12.0, 'tilt_y_deg': 12.0, 'undulation_amp': [0.0, 4.0], 'undulation_lambda': [150.0, 400.0], 'blur_sigma': [0.6, 1.2], 'noise': [0.03, 0.10], 'offset': 0.08}

def make_slab(rng, k, g=GEN, t_fixed=None, iface_fixed=None, tilt_y_fixed=None):
    """one synthetic fused slab (n_sec, Z, X) uint8 + truth. Stacking along z; k sheets at zero gap in the middle,
    gap-resolved sheets above and below."""
    n, Z, X = g['n_sec'], g['Z'], g['X']; fine = 4
    t_nom = float(rng.uniform(*g['t_range'])) if t_fixed is None else float(t_fixed); ts = np.clip(t_nom + rng.uniform(-g['t_jitter'], g['t_jitter'], k), 8, 20)
    n_up, n_dn = int(rng.integers(g['n_embed'][0], g['n_embed'][1] + 1)), int(rng.integers(g['n_embed'][0], g['n_embed'][1] + 1))
    gaps_up, gaps_dn = rng.uniform(*g['gap_range'], n_up), rng.uniform(*g['gap_range'], n_dn); emb_t = np.clip(t_nom + rng.uniform(-1.5, 1.5, n_up + n_dn), 8, 20)
    gap_lv = float(rng.uniform(*g['gap_level'])); sh_lv = float(rng.uniform(*g['sheet_level'])); a_h = float(rng.uniform(*g['half_layer_amp'])); P_fn = float(rng.uniform(*g['fibre_period'])); a_n = float(rng.uniform(*g['fibre_amp_normal']))
    a_f = float(rng.uniform(*g['fibre_amp_inplane'])); P_fx, P_fy = rng.uniform(*g['fibre_period'], 2); blur = float(rng.uniform(*g['blur_sigma'])); noise = float(rng.uniform(*g['noise']))
    # 1-D template along the true normal coordinate u (fine grid), sheets listed bottom to top
    sheets = []; u = 0.0; order = []
    for j in range(n_dn): u += gaps_dn[j]; sheets.append((u, u + emb_t[j], 'embed')); u += emb_t[j]
    u += gaps_dn[-1] if n_dn else 10.0; run_a = u
    for j in range(k): sheets.append((u, u + ts[j], 'fused')); u += ts[j]
    run_b = u; u += gaps_up[0] if n_up else 10.0
    for j in range(n_up): sheets.append((u, u + emb_t[n_dn + j], 'embed')); u += emb_t[n_dn + j]; u += gaps_up[j] if j + 1 < n_up else 0.0
    total = u + 10.0; z_off = (Z - total) / 2.0 + rng.uniform(-10, 10); margin = 16.0; U = np.arange(0, int((total + 2 * margin) * fine)) / fine - margin   # template over u in [-margin, total + margin]; z = u + z_off + h(x, y)
    dens = np.full(U.shape, gap_lv, np.float32); sid = np.full(U.shape, -1, np.int32); phase = []
    for j, (a, b, kind) in enumerate(sheets):
        sel = (U >= a) & (U < b); lv = sh_lv + rng.uniform(-g['sheet_var'], g['sheet_var']); ph_h, ph_n = rng.uniform(0, 2 * np.pi, 2)
        dens[sel] = lv * (1 + a_h * np.cos(2 * np.pi * U[sel] / g['half_layer_period'] + ph_h) + a_n * np.cos(2 * np.pi * U[sel] / P_fn + ph_n)); sid[sel] = j; phase.append(rng.uniform(0, 2 * np.pi, 2))
    ifaces = []; depths = []                                                                                 # contact interfaces inside the fused run: a narrow density dip (surface roughness, partial volume)
    for j in range(n_dn, n_dn + k - 1):
        ub = sheets[j][1]; depth = float(rng.uniform(*g['iface_depth'])) if iface_fixed is None else float(iface_fixed); wid = float(rng.uniform(*g['iface_width'])); ifaces.append(round(ub, 2)); depths.append(depth)
        dens -= depth * (sh_lv - gap_lv) * np.exp(-0.5 * ((U - ub) / (wid / 2.355)) ** 2).astype(np.float32)
    # geometry: u = z - h(x, y); h = tilt_x (x - X/2) + A sin(2 pi x / lambda + phi) + tilt_y (y - n/2)
    th_x = np.radians(rng.uniform(-g['tilt_x_deg'], g['tilt_x_deg'])); th_y = np.radians(rng.uniform(-g['tilt_y_deg'], g['tilt_y_deg'])) if tilt_y_fixed is None else np.radians(tilt_y_fixed)
    A = float(rng.uniform(*g['undulation_amp'])); lam = float(rng.uniform(*g['undulation_lambda'])); ph0 = rng.uniform(0, 2 * np.pi)
    yy, zz, xx = np.meshgrid(np.arange(n, dtype=np.float32), np.arange(Z, dtype=np.float32), np.arange(X, dtype=np.float32), indexing='ij')
    h = np.tan(th_x) * (xx - X / 2) + A * np.sin(2 * np.pi * xx / lam + ph0) + np.tan(th_y) * (yy - n / 2); uu = zz - z_off - h
    fi = np.clip(((uu + margin) * fine).round().astype(np.int64), 0, len(U) - 1); vol = dens[fi]; s_id = sid[fi]
    ph = np.array(phase, np.float32); phx = np.where(s_id >= 0, ph[np.clip(s_id, 0, len(ph) - 1), 0], 0.0); phy = np.where(s_id >= 0, ph[np.clip(s_id, 0, len(ph) - 1), 1], 0.0)
    tex = 1 + a_f * (np.cos(2 * np.pi * xx / P_fx + phx) + np.cos(2 * np.pi * yy / P_fy + phy)) * (s_id >= 0)                   # in-plane fibre bundles, decorrelated across sheets
    vol = vol * tex; del tex, uu, h, fi, s_id, phx, phy
    vol = ndi.gaussian_filter(vol, blur) + rng.normal(0, noise, vol.shape).astype(np.float32) + g['offset']
    st = np.clip(vol * 255, 1, 255).astype(np.uint8)
    truth = {'k': k, 't_nominal': round(t_nom, 2), 't_sheets': [round(float(q), 2) for q in ts], 'T_true': round(float(run_b - run_a), 2), 'run_u': [round(run_a, 2), round(run_b, 2)], 'ifaces_u': ifaces, 'n_embed': [n_dn, n_up],
             'gap_level': round(gap_lv, 3), 'sheet_level': round(sh_lv, 3), 'half_layer_amp': round(a_h, 3), 'fibre_period_normal': round(P_fn, 2), 'fibre_amp_normal': round(a_n, 3), 'fibre_amp_inplane': round(a_f, 3), 'fibre_period_inplane': [round(float(P_fx), 2), round(float(P_fy), 2)],
             'iface_depth_mean': round(float(np.mean(depths)), 3) if depths else None, 'tilt_x_deg': round(float(np.degrees(th_x)), 2), 'tilt_y_deg': round(float(np.degrees(th_y)), 2), 'undulation': [round(A, 2), round(lam, 1)], 'blur': round(blur, 2), 'noise': round(noise, 3),
             'z_run_centre': round(float(z_off + 0.5 * (run_a + run_b)), 1)}
    return st, truth

def selftest(out, n_per_k, seed, p, sweep_n=36, control_n=20):
    os.makedirs(out, exist_ok=True); gen_hash = hashlib.sha256(json.dumps({'GEN': GEN, 'P': p, 'seed': seed, 'n_per_k': n_per_k, 'sweep_n': sweep_n, 'control_n': control_n}, sort_keys=True).encode()).hexdigest()
    rng = np.random.default_rng(seed); rows = []; ex_fig = []; t0 = time.time()
    def run_one(st, truth, tag, extra=None):
        rec = analyse_slab(st, p, keep_examples=1); zc = truth['z_run_centre']
        cand = [r for r in rec['runs'] if abs(r['z_mid'] - zc) < 0.6 * truth['T_true'] + 8]                  # the run at the injected position (any tile, any x)
        cand.sort(key=lambda r: -r['n_rays']); best = cand[0] if cand else None
        row = {'tag': tag, 'k': truth['k'], 't': truth['t_nominal'], 'T_true': truth['T_true'], 'tilt_y': truth['tilt_y_deg'], 'noise': truth['noise'], 'blur': truth['blur'], 'half_layer_amp': truth['half_layer_amp'], 'fibre_amp_normal': truth['fibre_amp_normal'], 'fibre_period_normal': truth['fibre_period_normal'],
               'n_tiles_adm': rec['n_tiles_admissible'], 'n_runs_found': len(rec['runs']), 'sheet_w_p50': rec['sheet_width_vox']['p50'], 'secs': rec['secs']}
        if extra: row.update(extra)
        if best is None: row.update({'found': False, 'count': None, 'integer': None, 'status': 'NOT_FOUND', 'ok': False}); return row, rec
        row.update({'found': True, 'class': best['class'], 'T_meas': best['T_vox']['p50'], 'n_rays': best['n_rays'], 'n_groups': best['n_groups'], 'n_groups_with_pitch': best['n_groups_with_pitch'], 'count': best.get('count'), 'count_err': best.get('count_err'), 'count_range': best.get('count_range'), 'integer': best.get('integer'), 'status': best['status'],
                    'pitch_p50': best.get('pitch_vox', {}).get('p50'), 'rejected_n': best['rejected_periods']['n'], 'rejected_p50': best['rejected_periods']['p50'], 'anchored_frac': best['anchored_frac'], 'n_peaks_p50': best.get('n_peaks_p50'), 'subharmonic_flag_frac': best.get('subharmonic_flag_frac'), 'why': best.get('why')})
        row['ok'] = bool(best.get('count') is not None and abs(best['count'] - truth['k']) <= 1.0); row['ok_integer'] = bool(best.get('integer') is not None and abs(best['integer'] - truth['k']) <= 1)
        return row, rec
    # main suite: k = 2..8, n_per_k slabs each, every parameter drawn from GEN
    for k in range(GEN['k_range'][0], GEN['k_range'][1] + 1):
        for j in range(n_per_k):
            st, truth = make_slab(rng, k); row, rec = run_one(st, truth, 'main'); rows.append(row)
            if rec['examples'] and len(ex_fig) < 4 and k in (2, 4, 6, 8) and all(e['k'] != k for e in ex_fig): ex_fig.append(dict(rec['examples'][0], k=k, t=truth['t_nominal']))
            print(json.dumps({q: row.get(q) for q in ('tag', 'k', 't', 'count', 'count_err', 'integer', 'status', 'ok', 'secs')}), flush=True)
    # interface-contrast sensitivity sweep (reported, no bar): fixed dip depth, everything else random
    sweep = []
    for depth in (0.02, 0.05, 0.08, 0.12, 0.20, 0.30):
        for j in range(sweep_n):
            k = int(rng.integers(2, 9)); st, truth = make_slab(rng, k, iface_fixed=depth); row, _ = run_one(st, truth, 'iface_sweep', {'iface_depth': depth}); sweep.append(row)
    # negative control: y-tilt 18-28 deg -> rays inadmissible -> no count may be claimed
    neg = []
    for j in range(control_n):
        k = int(rng.integers(2, 9)); st, truth = make_slab(rng, k, tilt_y_fixed=float(rng.uniform(18, 28)) * rng.choice([-1, 1])); row, _ = run_one(st, truth, 'ytilt_control'); neg.append(row)
    main = rows; ok = np.array([r['ok'] for r in main]); thin = np.array([r['t'] < p['reject_below_ws'] * p['w_s'] for r in main])
    def rate(sel): return round(float(np.mean([r['ok'] for r in sel])), 3) if sel else None
    summary = {'generator_hash': gen_hash, 'seed': seed, 'n_main': len(main), 'bar_W1': {'rule': 'count within +-1 of k on >= 90 % of slabs', 'pass_frac': round(float(ok.mean()), 3), 'PASS': bool(ok.mean() >= 0.9)},
               'pass_frac_integer_claimed_and_correct': round(float(np.mean([r['ok_integer'] for r in main])), 3),
               'status_counts': {s: int(sum(r['status'] == s for r in main)) for s in ('COUNTED', 'NO_INTEGER', 'SUBHARMONIC_RISK', 'UNANCHORED', 'UNRESOLVED', 'NOT_FOUND')},
               'pass_by_k': {k: rate([r for r in main if r['k'] == k]) for k in range(2, 9)},
               'pass_by_thickness': {'t < 0.8 w_s (%.1f vox)' % (p['reject_below_ws'] * p['w_s']): {'n': int(thin.sum()), 'pass_frac': rate([r for r, s in zip(main, thin) if s])}, 't >= 0.8 w_s': {'n': int((~thin).sum()), 'pass_frac': rate([r for r, s in zip(main, thin) if not s])}},
               'pass_by_noise': {'noise < 0.065': rate([r for r in main if r['noise'] < 0.065]), 'noise >= 0.065': rate([r for r in main if r['noise'] >= 0.065])},
               'count_error_stats': {'abs_err_p50': round(float(np.median([abs(r['count'] - r['k']) for r in main if r['count'] is not None])), 3) if any(r['count'] is not None for r in main) else None, 'abs_err_p90': round(float(np.percentile([abs(r['count'] - r['k']) for r in main if r['count'] is not None], 90)), 3) if any(r['count'] is not None for r in main) else None,
                                     'claimed_err_p50': round(float(np.median([r['count_err'] for r in main if r.get('count_err') is not None])), 3) if any(r.get('count_err') is not None for r in main) else None},
               'calibration': {'frac_true_k_inside_count_range': round(float(np.mean([r['count_range'][0] - 0.5 <= r['k'] <= r['count_range'][1] + 0.5 for r in main if r.get('count_range')])), 3) if any(r.get('count_range') for r in main) else None},
               'iface_sweep': {str(d): {'n': int(sum(r['iface_depth'] == d for r in sweep)), 'pass_frac': rate([r for r in sweep if r['iface_depth'] == d]), 'claimed_frac': round(float(np.mean([r['count'] is not None for r in sweep if r['iface_depth'] == d])), 3)} for d in (0.02, 0.05, 0.08, 0.12, 0.20, 0.30)},
               'ytilt_control': {'n': len(neg), 'n_counts_claimed': int(sum(r['count'] is not None for r in neg)), 'n_integers_claimed': int(sum(r.get('integer') is not None for r in neg)), 'PASS': bool(sum(r.get('integer') is not None for r in neg) == 0)},
               'secs_total': round(time.time() - t0, 1)}
    json.dump({'vox_um': VOX, 'params': p, 'generator': GEN, 'summary': summary, 'main': main, 'iface_sweep': sweep, 'ytilt_control': neg}, open(os.path.join(out, 'selftest.json'), 'w'), indent=1)
    plot_examples(ex_fig, os.path.join(out, 'selftest_profiles.png'), 'X2 self-test: synthetic fused slabs (density along the local normal)', p)
    print(json.dumps(summary, indent=1)); return summary

# ------------------------------------------------------------------------------------------------------------ plots
def plot_examples(examples, path, title, p):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    if not examples: return
    n = len(examples); fig, axes = plt.subplots(n, 2, figsize=(13, 2.6 * n), gridspec_kw={'width_ratios': [2.2, 1]}); axes = np.atleast_2d(axes)
    C = {'SHEET': '#4C78A8', 'PAIR': '#F58518', 'FUSED': '#E45756'}
    for r, ex in enumerate(examples):
        prof = np.array(ex['prof']); x = np.arange(len(prof)) * ex['cosy']; ax = axes[r, 0]; ax.plot(x, ex['raw'], color='#BBBBBB', lw=0.6); ax.plot(x, prof, color='#333333', lw=0.9)
        ax.axhline(ex['thr'], color='#999999', lw=0.7, ls='--')
        for a, b, cls in ex['runs']: ax.axvspan(a * ex['cosy'], b * ex['cosy'], color=C[cls], alpha=0.18, lw=0)
        per = ex['per']; lab = 'k=%s t=%s: ' % (ex.get('k'), ex.get('t')) if 'k' in ex else 'tile %s sec %s x %s: ' % (ex['tile'], ex['sec'], ex['x0'])
        run_ = ex.get('run', {}); ax.set_title(lab + 'run T = %.1f vox, group pitch %.2f vox (line contrast %.2f, acf %.2f, %d rays); run count %s +- %s [%s], internal peaks p50 %s; rejected periods: %s' % (per['T_true'], per['pitch'], per['line_contrast'], per['acf_at_pitch'], per['n_rays'], run_.get('count'), run_.get('count_err'), run_.get('status'), run_.get('n_peaks_p50'), ', '.join('%.1f (%.2f)' % (d['period'], d['rel_power']) for d in per['rejected'][:3]) or 'none'), fontsize=7)
        ax.set_xlabel('true distance along the normal (vox, cos y-tilt applied)'); ax.set_ylabel('density (stripe-removed)')
        rr = np.array(per['acf']); ax2 = axes[r, 1]; ax2.plot(np.arange(len(rr)), rr, color='#333333', lw=0.9)
        ax2.axvspan(0, p['reject_below_ws'] * p['w_s'], color='#E45756', alpha=0.12, lw=0); ax2.axvline(per['pitch'], color='#4C78A8', lw=1.0); ax2.axhline(0, color='#999999', lw=0.5)
        ax2.set_title('mean autocorrelation over the group of rays of |d/ds G1(density)| in the run; red = rejected band', fontsize=7); ax2.set_xlabel('lag (vox)')
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)

# ------------------------------------------------------------------------------------------------------------- real
def real(out, a, p):
    os.makedirs(out, exist_ok=True); meta = {}
    if a.npy:
        st = np.load(a.npy); meta = json.load(open(a.meta)) if a.meta and os.path.exists(a.meta) else {}
    else:
        from core_native import L0; src = L0(a.src, threads=3); st, ft = src.slab(a.y, a.n_sec, a.z[0], a.z[1], a.x[0], a.x[1]); meta = {'fetch': ft, 'shape': src.shape, 'chunks': src.chunks, 'window': {'y': [a.y, a.y + a.n_sec], 'z': list(a.z), 'x': list(a.x)}}
    sha = hashlib.sha256(st.tobytes()).hexdigest(); rec = analyse_slab(st, p, keep_examples=8); ex = rec.pop('examples')
    plot_examples(ex, os.path.join(out, 'real_profiles.png'), 'X2 on PHerc0268 level 0, window %s' % json.dumps(meta.get('window')), p)
    runs = rec['runs']; summ = {'window': meta.get('window'), 'slab_sha256': sha, 'fetch': meta.get('fetch'), 'n_tiles': rec['n_tiles'], 'n_tiles_admissible': rec['n_tiles_admissible'], 'tile_rejections': {w: int(sum(t.get('why') == w for t in rec['tiles'])) for w in set(t.get('why') for t in rec['tiles'] if not t['admissible'])},
            'n_rays': rec['n_rays'], 'n_rays_cut': rec['n_rays_cut'], 'sheet_width_vox': rec['sheet_width_vox'], 'n_ray_runs': rec['n_ray_runs'], 'n_pooled_runs': len(runs), 'n_pooled_runs_ge_min_rays': int(sum(r['n_rays'] >= p['min_rays'] for r in runs)),
            'status_counts': {s: int(sum(r['status'] == s for r in runs if r['n_rays'] >= p['min_rays'])) for s in ('COUNTED', 'NO_INTEGER', 'SUBHARMONIC_RISK', 'UNANCHORED', 'UNRESOLVED')}, 'secs': rec['secs']}
    json.dump({'vox_um': VOX, 'params': p, 'summary': summ, 'tiles': rec['tiles'], 'runs': runs}, open(os.path.join(out, 'real_%s.json' % (('y%d' % meta['window']['y'][0]) if meta.get('window') else 'slab')), 'w'), indent=1)
    print(json.dumps(summ, indent=1))
    for r in runs:
        if r['n_rays'] >= p['min_rays'] and r['status'] != 'UNRESOLVED': print(json.dumps({q: r.get(q) for q in ('tiles', 'z_mid', 'x_mid', 'class', 'n_rays', 'n_groups_with_pitch', 'T_um', 'pitch_um', 'count', 'count_err', 'integer', 'status', 'anchored_frac', 'n_peaks_p50', 'subharmonic_flag_frac')}))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['selftest', 'real']); ap.add_argument('out'); ap.add_argument('--n_per_k', type=int, default=30); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--sweep_n', type=int, default=36); ap.add_argument('--control_n', type=int, default=20)
    ap.add_argument('--npy', default=None); ap.add_argument('--meta', default=None); ap.add_argument('--src', default='s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/0')
    ap.add_argument('--y', type=int, default=5820); ap.add_argument('--n_sec', type=int, default=16); ap.add_argument('--z', type=int, nargs=2, default=[7936, 8704]); ap.add_argument('--x', type=int, nargs=2, default=[1280, 2304]); ap.add_argument('--w_s', type=float, default=14.0)
    a = ap.parse_args(); p = dict(P); p['w_s'] = a.w_s
    if a.mode == 'selftest': selftest(a.out, a.n_per_k, a.seed, p, a.sweep_n, a.control_n)
    else: real(a.out, a, p)

if __name__ == '__main__': main()
