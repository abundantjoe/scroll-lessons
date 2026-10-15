#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 item 5, stage X3 gate 0: EXISTENCE TEST, before any operator, of a recto/verso fibre-orientation alternation
inside single papyrus sheets of PHerc0268 at the scan's native 8.64 um (OME level 0, uint8, chunks 128^3).
Per declared window (128 y-sections x 1024 z x 1024 x = 134 MB, class L0.slab of tools/umb/core_native.py):
 1. background: the per-(y, x) z-median of the window is subtracted (ring artefacts of a z-reconstruction are z-invariant);
    its own orientation statistic is recorded.
 2. sheets: seeded on 24 x 24-column mean z-profiles at 8 x positions (raw-CT lamina peaks, prominence >= 3 MAD of the
    detrended profile, FWHM 10-18 vox, nearest neighbouring peak >= 24 vox away on both sides); each seed is tracked over
    the whole (y, x) plane by region growing on a stride-4 grid (local maximum of the lightly smoothed CT within +-12 vox
    of the tracked neighbours' median, parabolic refinement); jumps (> 4 vox between adjacent cells) cut the track to the
    seed's connected component; duplicates (median |dh| < 3 vox) merged.
 3. per column at full resolution: height h, FWHM, local prominence, half-prominence crossings on both sides (the gap);
    a column is clean if |h - smooth(h)| <= 2, 8 <= FWHM <= 20, prominence >= 3 MAD and both crossings exist; a 128 x 128
    (y, x) tile is clean if >= 90 % of its columns are; a sheet is clean if >= 2 of its 8 tiles are.
 4. bands of a clean sheet, w = its median FWHM: the four depth quartiles of [h - w/2, h + w/2] (q0 = z-negative outer,
    q1 = z-negative inner, q2 = z-positive inner, q3 = z-positive outer; 3 depths per quartile, linear interpolation along
    z following h) and the gaps 5 vox outside each face (g0, g1) as controls.
 5. orientation per tile: Hann-windowed periodogram; per sheet and band the tile-mean periodogram's double-angle moment
    over the annulus of wavelengths 4-32 vox (35-277 um): anisotropy A = |sum P e^{2i phi} / sum P| and the real-space
    orientation theta = arg/2 + 90 (0 deg = along x, around the roll; 90 deg = along y, the roll axis).
 6. nulls on the same tiles through the same pipeline: (a) ISOTROPISED phase-randomised surrogates (random phases,
    amplitude replaced by its azimuthal mean: same radial power spectrum, no orientation) give the p95 of A and of the
    outer-quartile angle difference under 'no in-plane orientation'; (b) the literal phase-randomised surrogate (same
    |F(k)|, random phases) is recorded to show it preserves the second-order orientation statistic by construction
    (A and theta equal the data's up to windowing) and is therefore not a test of anisotropy on its own.
Gate statistic, declared before data: ALTERNATION on a sheet = A above the isotropised null p95 in BOTH outer quartiles
AND |dtheta - 90| <= 20 deg, dtheta = outer-quartile angle difference folded to [0, 90]. The gate opens only if >= 20
clean sheets exist, alternation holds on > 50 % of them and the median dtheta over clean sheets exceeds the null p95 of
that median. Also reported: adjacent-quartile agreement on the same half (q0 vs q1, q2 vs q3), gap controls, and the
literal null. Phantom mode (--phantom bilayer|same|iso) runs the identical pipeline on a synthetic slab with known
textures: positive control (0 deg over 90 deg), negative control (same angle both halves), isotropic control.
The reconstruction's phase-retrieval parameters are read from the volume's metadata.json and recorded.
Writes <out>/gate0.json (or phantom_<kind>.json) and a PNG montage of 4 sheets (quartile tiles and spectra).
usage: x3_gate0.py <out_dir> [--windows y0,z0,x0 ...] [--threads 3] [--n_null 200] [--phantom bilayer]
"""
import argparse, json, os, sys, time, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from scipy.special import erf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb'))

VOX = 8.64
VOL = 's3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr'
TILE = 128; STRIDE = 4; SEARCH = 6; WIN = 14; SEEDHALF = 4; T = 64; K_LO, K_HI = T / 32.0, T / 4.0        # TILE = slab sections (y); T = spectral tile; annulus = wavelengths 4-32 vox
P = dict(seed_width=(10, 18), seed_gap_min=4, col_width=(5, 20), col_resid_max=2.0, prom_mad=3.0, col_prom_mad=1.5, tile_clean_frac=0.8, spec_tile=T,
         sheet_min_tiles=4, masked_tile_min_frac=0.3, min_clean_sheets=20, dtheta_tol=20.0, jump_cut=4.0, gap_offset=5, depths_per_band=3)

CALIBRATION = {'pre_declared': {'col_width': [8, 20], 'col_prom_mad': 3.0, 'spec_tile': 128, 'tile_clean_frac': 0.9, 'sheet_min_tiles': 2, 'seed_neighbour_centre_distance_min': 24, 'height_map': 'stride-4 track, 5x5 median + gaussian 1.5 cells'},
               'measured_on_first_window_before_any_spectrum': 'laminae at y5760 z7888 x5488: 8x8-column mean profiles give FWHM median 11.4 vox and spacing median 32.5 vox (peaks >= 3 MAD); single-column FWHM median 7-9 vox and prominence 2-4.5 x the 8x8 MAD; the lamina height is rough (rms step 1.5 vox at 1-vox lag rising monotonically to 9-27 vox at 64-vox lag), so a 6-vox smooth map leaves |resid| > 2 on half the columns; with the pre-declared column class no 128-tile reached 60 % clean columns on any of 35 tracked laminae',
               'changed_before_any_spectrum_was_computed': {'col_width': [5, 20], 'col_prom_mad': 1.5, 'spec_tile': 64, 'tile_clean_frac': 0.8, 'sheet_min_tiles': 4, 'seed_gap_min_edge_to_edge': 4, 'height_map': 'two-pass: smooth track, then a 5x5 median of the per-column midpoints that the bands follow'},
               'unchanged': 'the orientation statistic, the annulus, the nulls, the gate rule (alternation on > 50 % of >= 20 clean sheets and the median dtheta above its null p95), the quartile definition, the controls'}

# ------------------------------------------------------------------ data
def fetch_window(y0, z0, x0, threads, cache='/dev/shm'):
    path = f'{cache}/x3_slab_y{y0}_z{z0}_x{x0}.npy'
    if os.path.exists(path): return np.load(path), {'cached': path}
    from core_native import L0
    src = L0(VOL + '/0', threads=threads); v, ft = src.slab(y0, TILE, z0, z0 + 1024, x0, x0 + 1024); np.save(path + '.tmp.npy', v); os.replace(path + '.tmp.npy', path); return v, ft

def read_phase_metadata():
    """metadata.json next to the volume's .zattrs (the .zattrs itself carries only the multiscale axes)."""
    try:
        import s3fs; fs = s3fs.S3FileSystem(anon=True); m = json.loads(fs.cat_file(VOL[5:] + '/metadata.json'))
        proc = m.get('scan', {}).get('tomo', {}).get('processing', {}); ph = proc.get('preprocessing', {}).get('phase'); acq = m.get('scan', {}).get('tomo', {}).get('acquisition', {})
        out = {'source': VOL + '/metadata.json', 'zattrs': 'multiscale axes and scales only (no reconstruction parameters)', 'phase_retrieval': ph if ph else 'not exposed',
               'reconstruction': proc.get('reconstruction', 'not exposed'), 'energy_keV': acq.get('energy'), 'sample_detector_distance_mm': acq.get('sampleDetectorDistance'), 'sample_pixel_size_mm': acq.get('detector', {}).get('samplePixelSize')}
        if ph and ph.get('delta_beta') and acq.get('energy') and acq.get('sampleDetectorDistance'):                       # derived: Paganin low-pass length sqrt(lambda z delta/beta / 4 pi)
            lam = 12.398 / acq['energy'] * 1e-10; z = acq['sampleDetectorDistance'] * 1e-3; L = (lam * z * ph['delta_beta'] / (4 * np.pi)) ** 0.5
            out['derived_paganin_length_um'] = round(L * 1e6, 1); out['derived_paganin_length_vox'] = round(L * 1e6 / VOX, 2); out['derived_note'] = 'sqrt(lambda*z*delta_beta/(4 pi)) with the recorded energy and distance; textures finer than this are attenuated by the phase filter before the recorded unsharp mask'
        return out
    except Exception as e: return {'source': VOL + '/metadata.json', 'phase_retrieval': 'not exposed', 'error': repr(e)[:200]}

# ------------------------------------------------------------------ sheets
def prep(slab):
    """slab (y, z, x) uint8 -> V (z, y, x) float32 minus its per-(y, x) z-median, the median map, the lightly smoothed G, the mask."""
    V = slab.transpose(1, 0, 2).astype(np.float32) / 255.0; mask = V > 0
    flat = np.median(V, axis=0).astype(np.float32); V -= flat[None]
    G = ndi.gaussian_filter(V, (1.0, 2.0, 2.0)); return V, flat, G, mask

def detrended_mad(prof): return float(np.median(np.abs(prof - ndi.median_filter(prof, 61, mode='nearest')))) + 1e-6

def seeds_on_profile(prof, mad):
    """raw-CT lamina peaks: prominence >= 3 MAD, FWHM 10-18 vox, and a gap >= seed_gap_min vox between its half-prominence edges and those of the nearest peak (prominence >= 1 MAD) on both sides."""
    allp, ap = find_peaks(prof, prominence=1.0 * mad, width=(0, None), rel_height=0.5); out = []
    for i, p in enumerate(allp):
        wd, pr = float(ap['widths'][i]), float(ap['prominences'][i])
        if not (P['seed_width'][0] <= wd <= P['seed_width'][1] and pr >= P['prom_mad'] * mad): continue
        gl = ap['left_ips'][i] - ap['right_ips'][i - 1] if i > 0 else ap['left_ips'][i]; gr = ap['left_ips'][i + 1] - ap['right_ips'][i] if i + 1 < len(allp) else len(prof) - ap['right_ips'][i]
        if min(gl, gr) >= P['seed_gap_min']: out.append((int(p), wd, pr, float(min(gl, gr))))
    return out

def lamina_census(prof, mad):
    pk, pr = find_peaks(prof, prominence=P['prom_mad'] * mad, width=(0, None), rel_height=0.5); w = pr['widths']; sp = np.diff(pk)
    return {'n_peaks': int(len(pk)), 'fwhm_p10_50_90': [round(float(v), 1) for v in np.percentile(w, [10, 50, 90])] if len(w) else None, 'spacing_p10_50_90': [round(float(v), 1) for v in np.percentile(sp, [10, 50, 90])] if len(sp) else None, 'n_fwhm_10_18': int(((w >= 10) & (w <= 18)).sum())}

def midpoint(prof, c=None, search=None):
    """lamina centre on a 1-D profile: the midpoint of the half-prominence crossings around the maximum (restricted to c +- search when given; robust to a flat top); None if a crossing is missing."""
    n = len(prof); k = int(np.argmax(prof)) if c is None else int(np.argmax(prof[max(0, c - search):c + search + 1])) + max(0, c - search)
    if k == 0 or k == n - 1: return None
    pk = prof[k]; prom = pk - max(prof[:k].min(), prof[k + 1:].min()); half = pk - 0.5 * prom
    li = np.nonzero(prof[:k] < half)[0]; ri = np.nonzero(prof[k + 1:] < half)[0]
    if li.size == 0 or ri.size == 0: return None
    l = int(li.max()); r = int(ri.min()) + k + 1
    xl = l + (half - prof[l]) / max(prof[l + 1] - prof[l], 1e-9); xr = r - (half - prof[r]) / max(prof[r - 1] - prof[r], 1e-9); return 0.5 * (xl + xr)

def track(G, z_seed, yc, xc):
    """region growing on the stride grid from the seed cell: lamina midpoint within +-SEARCH of the tracked neighbours' median."""
    Z, Y, X = G.shape; gy = np.arange(0, Y, STRIDE); gx = np.arange(0, X, STRIDE); H = np.full((len(gy), len(gx)), np.nan, np.float32)
    iy, ix = min(yc // STRIDE, len(gy) - 1), min(xc // STRIDE, len(gx) - 1); dy = np.abs(np.arange(len(gy)) - iy)[:, None]; dx = np.abs(np.arange(len(gx)) - ix)[None, :]
    order = np.argsort(np.maximum(dy, dx), axis=None, kind='stable'); ncol = len(gx)
    for f in order:
        i, j = divmod(int(f), ncol); nb = H[max(0, i - 1):i + 2, max(0, j - 1):j + 2]; nbv = nb[np.isfinite(nb)]
        pred = float(z_seed) if nbv.size == 0 else float(np.median(nbv)); z0 = int(round(pred)); lo, hi = max(0, z0 - WIN), min(Z, z0 + WIN + 1)
        if hi - lo < 2 * WIN + 1: continue
        m = midpoint(G[lo:hi, gy[i], gx[j]], WIN, SEARCH)
        if m is not None: H[i, j] = lo + m
    # cut at jumps: flood fill from the seed cell over edges whose height step is <= jump_cut (a jumping cell is excluded, its neighbours are kept)
    comp = np.zeros(H.shape, bool); ny, nx = H.shape
    if np.isfinite(H[iy, ix]):
        comp[iy, ix] = True; stack = [(iy, ix)]
        while stack:
            i, j = stack.pop(); h0 = H[i, j]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < ny and 0 <= b < nx and not comp[a, b] and np.isfinite(H[a, b]) and abs(H[a, b] - h0) <= P['jump_cut']: comp[a, b] = True; stack.append((a, b))
    Hc = np.where(comp, H, np.nan); return Hc, comp

def smooth_height(H, comp):
    """nan-aware: nearest fill, 5x5 median, gaussian 1.5; returns the full-resolution height map and validity mask."""
    if comp.sum() < 10: return None, None
    idx = ndi.distance_transform_edt(~comp, return_distances=False, return_indices=True); Hf = H[idx[0], idx[1]]
    Hs = ndi.gaussian_filter(ndi.median_filter(Hf, 5, mode='nearest'), 1.5, mode='nearest')
    h_full = ndi.zoom(Hs, STRIDE, order=1); v_full = ndi.zoom(comp.astype(np.float32), STRIDE, order=0) > 0.5
    return h_full.astype(np.float32), v_full

def _measure(G, h_ref, mad):
    Z, Y, X = G.shape; zc = np.clip(np.round(h_ref).astype(int), WIN, Z - WIN - 1); off = np.arange(-WIN, WIN + 1)
    yy, xx = np.mgrid[0:Y, 0:X]; W = G[zc[None] + off[:, None, None], yy[None], xx[None]]                         # (2W+1, Y, X)
    c = WIN; sub = W[c - SEARCH:c + SEARCH + 1]; k = np.argmax(sub, 0) + c - SEARCH; idx = off[:, None, None] + WIN
    pk = np.take_along_axis(W, k[None], 0)[0]
    lmin = np.where(idx < k[None], W, np.inf).min(0); rmin = np.where(idx > k[None], W, np.inf).min(0); prom = pk - np.maximum(lmin, rmin); half = pk - 0.5 * prom
    below = W < half[None]; lc = np.where((idx < k[None]) & below, idx, -1).max(0); rc = np.where((idx > k[None]) & below, idx, 99).min(0)
    has = (lc >= 0) & (rc <= 2 * WIN)
    def frac_cross(i0, i1):                                                                                   # crossing position between i0 (below half) and i1 (above half)
        a = np.take_along_axis(W, np.clip(i0, 0, 2 * WIN)[None], 0)[0]; b = np.take_along_axis(W, np.clip(i1, 0, 2 * WIN)[None], 0)[0]; den = np.where(np.abs(b - a) < 1e-9, 1e-9, b - a); return (half - a) / den
    xl = lc + frac_cross(lc, lc + 1); xr = rc - frac_cross(rc, rc - 1); width = np.where(has, xr - xl, np.nan)
    h_meas = np.where(has, zc - WIN + 0.5 * (xl + xr), zc + (k - WIN)).astype(np.float32)
    return {'width': width, 'prom': prom, 'h_meas': h_meas, 'has_gap': has}

def measure_columns(G, h_full, mad):
    """two-pass per-column lamina measurement: pass 1 around the smooth tracked map, pass 2 around the local reference
    h_ref = 5x5 median of the pass-1 midpoints (the surface is rough at the 10-100 um scale: the bands follow h_ref)."""
    m1 = _measure(G, h_full, mad); h_ref = ndi.median_filter(np.where(m1['has_gap'] & (np.abs(m1['h_meas'] - h_full) <= 2 * P['col_resid_max']), m1['h_meas'], h_full), 5, mode='nearest').astype(np.float32)
    m = _measure(G, h_ref, mad); resid = m['h_meas'] - h_ref
    clean = m['has_gap'] & (m['width'] >= P['col_width'][0]) & (m['width'] <= P['col_width'][1]) & (m['prom'] >= P['col_prom_mad'] * mad) & (np.abs(resid) <= P['col_resid_max'])
    return {'width': m['width'], 'prom': m['prom'], 'resid': resid, 'clean': clean, 'has_gap': m['has_gap'], 'h_ref': h_ref, 'resid_pass1_rms': float(np.sqrt(np.nanmean((m1['h_meas'] - h_full)[m1['has_gap']] ** 2)))}

# ------------------------------------------------------------------ spectra
HANN = np.outer(np.hanning(T), np.hanning(T)).astype(np.float32)
KY, KX = np.meshgrid(np.fft.fftfreq(T) * T, np.fft.fftfreq(T) * T, indexing='ij'); KR = np.hypot(KY, KX); ANN = (KR >= K_LO) & (KR <= K_HI); PHI = np.arctan2(KY, KX); E2 = np.exp(2j * PHI)[ANN]
RB = np.round(KR).astype(int); RBC = np.bincount(RB.ravel()).astype(np.float32)

def periodogram(t): t = (t - t.mean()) * HANN; F = np.fft.fft2(t); return (F.real ** 2 + F.imag ** 2).astype(np.float32)

def orient(Pm):
    """double-angle moment of the periodogram over the annulus: anisotropy A, real-space orientation theta in [0, 180)."""
    p = Pm[ANN].astype(np.float64); C = (p * E2).sum() / max(p.sum(), 1e-30); return float(abs(C)), float((np.degrees(np.angle(C)) / 2 + 90.0) % 180.0)

def fold(d): d = np.abs(np.asarray(d, float)) % 180.0; return np.minimum(d, 180.0 - d)

def surrogates(tiles, rng, n, iso, masks=None):
    """n surrogate draws of the tile-mean periodogram: random phases from real white noise; amplitude = |F| (literal) or its azimuthal mean (isotropised)."""
    amps = []
    for t in tiles:
        F = np.fft.fft2(t - t.mean()); amp = np.abs(F)
        if iso: prof = np.bincount(RB.ravel(), amp.ravel()) / RBC; amp = prof[RB]
        amps.append(amp.astype(np.float32))
    out = np.empty((n, 2), np.float32)
    for s in range(n):
        Pm = np.zeros((T, T), np.float32)
        for ti, amp in enumerate(amps):
            N = np.fft.fft2(rng.standard_normal((T, T)).astype(np.float32)); S = np.fft.ifft2(amp * N / (np.abs(N) + 1e-12)).real
            if masks is not None: S = S * masks[ti]
            Pm += periodogram(S)
        out[s] = orient(Pm / len(amps))
    return out

def sample_band(V, h_full, depths):
    Z, Y, X = V.shape; yy, xx = np.mgrid[0:Y, 0:X].astype(np.float32); acc = np.zeros((Y, X), np.float32)
    for d in depths: acc += ndi.map_coordinates(V, [np.clip(h_full + d, 0, Z - 1), yy, xx], order=1, mode='nearest')
    return acc / len(depths)

# ------------------------------------------------------------------ phantom
def make_phantom(kind, rng, Z=512, Y=TILE, X=1024, n_sheets=10, w=13.0, contrast=0.08, noise=0.05, blur=1.0):
    yy, xx = np.mgrid[0:Y, 0:X].astype(np.float32); V = np.full((Z, Y, X), 0.35, np.float32); truth = []
    def tex(sig): t = ndi.gaussian_filter(rng.standard_normal((Y, X)).astype(np.float32), sig); return t / t.std()
    for k in range(n_sheets):
        zc = 40 + 44 * k + rng.uniform(-4, 4); tilt = 0.10 + rng.uniform(-0.02, 0.02); tilty = 0.20 + rng.uniform(-0.03, 0.03)   # common tilt plus per-sheet variation small enough that sheets never cross
        h = zc + tilt * (xx - X / 2) + tilty * (yy - Y / 2) + 5.0 * np.sin(2 * np.pi * xx / 400.0 + k)
        if kind == 'bilayer': t_top, t_bot = tex((0.7, 5.0)), tex((5.0, 0.7))                                  # top (z-negative) fibres along x, bottom along y
        elif kind == 'same': t_top, t_bot = tex((0.7, 5.0)), tex((0.7, 5.0))
        else: t_top, t_bot = tex((2.0, 2.0)), tex((2.0, 2.0))
        z0, z1 = max(0, int(h.min()) - 12), min(Z, int(h.max()) + 13)
        for z in range(z0, z1):
            dist = z - h; s = 0.5 * (erf((dist + w / 2) / 1.0) - erf((dist - w / 2) / 1.0)); t = np.where(dist < 0, t_top, t_bot); V[z] += s * (0.3 + contrast * t)
        truth.append({'k': k, 'zc': float(zc), 'tilt_x': float(tilt), 'tilt_y': float(tilty), 'h': h.astype(np.float32)})
    V = ndi.gaussian_filter(V, blur) + noise * rng.standard_normal(V.shape).astype(np.float32)
    slab = np.clip(V * 255, 1, 255).astype(np.uint8).transpose(1, 0, 2); return slab, truth

# ------------------------------------------------------------------ main analysis of one window
def analyse_window(slab, tag, rng, n_null, n_pr, truth=None, log=print):
    t0 = time.time(); V, flat, G, mask = prep(slab); Z, Y, X = V.shape; rec = {'tag': tag, 'shape_zyx': [Z, Y, X], 'mask_frac': round(float(mask.mean()), 4)}
    rec['flat_background'] = dict(zip(['A', 'theta'], orient(np.mean([periodogram(flat[i:i + T, j:j + T]) for i in range(0, Y, T) for j in range(0, X, T)], 0))))
    # seeds at 8 x positions, y centre
    seeds = []; mads = []; census = []
    for xc in range(TILE // 2, X, TILE):
        prof = G[:, Y // 2 - SEEDHALF:Y // 2 + SEEDHALF, xc - SEEDHALF:xc + SEEDHALF].mean((1, 2)); mad = detrended_mad(prof); mads.append(mad); census.append(lamina_census(prof, mad))
        for (p, wd, pr, gp) in seeds_on_profile(prof, mad): seeds.append({'z': p, 'x': xc, 'width': wd, 'prom': pr, 'gap': gp})
    mad = float(np.median(mads)); rec['mad'] = round(mad, 5); rec['n_seeds'] = len(seeds); rec['lamina_census_per_profile'] = census
    allw = [c['fwhm_p10_50_90'][1] for c in census if c['fwhm_p10_50_90']]; alls = [c['spacing_p10_50_90'][1] for c in census if c['spacing_p10_50_90']]
    rec['lamina_census_summary'] = {'profiles': f'{2 * SEEDHALF}x{2 * SEEDHALF}-column mean z-profiles at 8 x positions, peaks with prominence >= 3 MAD', 'median_of_median_fwhm_vox': round(float(np.median(allw)), 1) if allw else None, 'median_of_median_spacing_vox': round(float(np.median(alls)), 1) if alls else None, 'n_peaks_total': int(sum(c['n_peaks'] for c in census)), 'n_fwhm_10_18_total': int(sum(c['n_fwhm_10_18'] for c in census))}
    log(f'[{tag}] prep {time.time() - t0:.0f}s, seeds {len(seeds)}, MAD {mad:.4f}, census {rec["lamina_census_summary"]}')
    # track, dedupe
    sheets = []
    for sd in sorted(seeds, key=lambda s: (s['z'], s['x'])):
        H, comp = track(G, sd['z'], Y // 2, sd['x'])
        if comp.sum() < 64: continue
        dup = False; ci, cj = Y // 2 // STRIDE, min(sd['x'] // STRIDE, comp.shape[1] - 1)
        for sh in sheets:
            both = comp & sh['comp']; on_track = sh['comp'][ci, cj] and abs(sh['H'][ci, cj] - sd['z']) < 3.0
            if on_track or (both.sum() >= 32 and np.nanmedian(np.abs(H[both] - sh['H'][both])) < 3.0): sh['comp'] |= comp; sh['H'] = np.where(np.isfinite(sh['H']), sh['H'], H); dup = True; break
        if not dup: sheets.append({'seed': sd, 'H': H, 'comp': comp})
    log(f'[{tag}] tracked {len(sheets)} distinct laminae from {len(seeds)} seeds')
    out_sheets = []; n_mont = 0; n_mont_m = 0
    for si, sh in enumerate(sheets):
        h_full, v_full = smooth_height(sh['H'], sh['comp'])
        if h_full is None: continue
        m = measure_columns(G, h_full, mad); h_ref = m['h_ref']; clean = m['clean'] & v_full & (h_ref > WIN + 10) & (h_ref < Z - WIN - 10)
        tij = [(i, j) for i in range(0, Y, T) for j in range(0, X, T)]; tiles_clean = [bool(clean[i:i + T, j:j + T].mean() >= P['tile_clean_frac']) for i, j in tij]; n_tiles = int(sum(tiles_clean))
        w = float(np.nanmedian(m['width'][clean])) if clean.sum() > 100 else float('nan')
        s = {'sheet': si, 'seed_z': sh['seed']['z'], 'seed_x': sh['seed']['x'], 'z_mean': round(float(np.nanmean(h_full[v_full])), 1), 'tracked_frac': round(float(v_full.mean()), 3), 'clean_col_frac': round(float(clean.mean()), 3),
             'n_tiles_clean': n_tiles, 'n_tiles': len(tij), 'fwhm_vox': round(w, 2) if w == w else None, 'tilt_dh_dx': round(float(np.nanmedian(np.gradient(h_full, axis=1)[v_full])), 4), 'tilt_dh_dy': round(float(np.nanmedian(np.gradient(h_full, axis=0)[v_full])), 4),
             'height_resid_pass1_rms_vox': round(m['resid_pass1_rms'], 2), 'col_clean_breakdown': {'has_gap': round(float(m['has_gap'][v_full].mean()), 3), 'width_in_class': round(float(((m['width'] >= P['col_width'][0]) & (m['width'] <= P['col_width'][1]))[v_full].mean()), 3), 'prom_ok': round(float((m['prom'] >= P['col_prom_mad'] * mad)[v_full].mean()), 3), 'resid_ok': round(float((np.abs(m['resid']) <= P['col_resid_max'])[v_full].mean()), 3)},
             'is_clean': n_tiles >= P['sheet_min_tiles'] and w == w}
        if truth is not None:
            errs = [float(np.median(np.abs(h_ref - t['h'])[v_full])) for t in truth]; s['truth_sheet'] = int(np.argmin(errs)); s['truth_err_median_vox'] = round(float(np.median(np.abs(h_ref - truth[s['truth_sheet']]['h'])[clean])), 2) if clean.sum() else round(min(errs), 2)
        def band_stats(jt, masks, nn_full, keep_imgs):
            bands = {}; depth = {'q0': -w / 2 + w / 8, 'q1': -w / 8, 'q2': w / 8, 'q3': w / 2 - w / 8, 'g0': -(w / 2 + P['gap_offset']), 'g1': w / 2 + P['gap_offset']}
            for b, d0 in depth.items():
                img = sample_band(V, h_ref, [d0 - w / 12, d0, d0 + w / 12]); tiles = [img[i:i + T, j:j + T] for i, j in jt]
                if masks is not None: tiles = [(t - t[mk > 0].mean()) * mk for t, mk in zip(tiles, masks)]
                Pm = np.mean([periodogram(t) for t in tiles], 0); A, th = orient(Pm)
                nn = nn_full if b in ('q0', 'q3') else max(nn_full // 4, 25); iso = surrogates(tiles, rng, nn, True, masks); pr = surrogates(tiles, rng, n_pr, False, masks) if b in ('q0', 'q3') else None
                bands[b] = {'A': round(A, 4), 'theta': round(th, 1), 'n_tiles': len(tiles), 'null_iso_A_p50': round(float(np.percentile(iso[:, 0], 50)), 4), 'null_iso_A_p95': round(float(np.percentile(iso[:, 0], 95)), 4), 'A_above_null': bool(A > np.percentile(iso[:, 0], 95)), '_iso': iso}
                if pr is not None: bands[b].update({'null_pr_A_p50': round(float(np.percentile(pr[:, 0], 50)), 4), 'null_pr_theta_median': round(float(np.degrees(np.angle(np.mean(np.exp(2j * np.radians(pr[:, 1]))))) / 2 % 180), 1)})
                if b in ('q0', 'q3') and keep_imgs: bands[b]['_tile'] = tiles[0]; bands[b]['_P'] = Pm
            dth = float(fold(bands['q0']['theta'] - bands['q3']['theta'])); dnull = fold(bands['q0']['_iso'][:, 1] - bands['q3']['_iso'][:, 1])
            return {'dtheta_outer': round(dth, 1), 'dtheta_outer_null_p95': round(float(np.percentile(dnull, 95)), 1), 'dtheta_outer_exceeds_null_p95': bool(dth > np.percentile(dnull, 95)), '_dnull': dnull,
                    'dtheta_q0_q1': round(float(fold(bands['q0']['theta'] - bands['q1']['theta'])), 1), 'dtheta_q2_q3': round(float(fold(bands['q2']['theta'] - bands['q3']['theta'])), 1), 'dtheta_inner': round(float(fold(bands['q1']['theta'] - bands['q2']['theta'])), 1),
                    'dtheta_pr_null': round(float(fold(bands['q0']['null_pr_theta_median'] - bands['q3']['null_pr_theta_median'])), 1),
                    'alternation': bool(bands['q0']['A_above_null'] and bands['q3']['A_above_null'] and abs(dth - 90.0) <= P['dtheta_tol']), 'bands': bands}
        def fmt(r, pre):
            b = r['bands']; return f"{pre} q0 A {b['q0']['A']:.3f} (p95 {b['q0']['null_iso_A_p95']:.3f}) th {b['q0']['theta']:.0f} | q3 A {b['q3']['A']:.3f} (p95 {b['q3']['null_iso_A_p95']:.3f}) th {b['q3']['theta']:.0f} | dth {r['dtheta_outer']:.0f} (null p95 {r['dtheta_outer_null_p95']:.0f}) alt {r['alternation']} | g0 A {b['g0']['A']:.3f} g1 A {b['g1']['A']:.3f}"
        tile_frac = [float(clean[i:i + T, j:j + T].mean()) for i, j in tij]; s['tile_clean_frac_max'] = round(max(tile_frac), 3)
        if s['is_clean']:
            jt = [ij for ij, ok in zip(tij, tiles_clean) if ok]; s.update(band_stats(jt, None, n_null, n_mont < 4))
            log(f"[{tag}] sheet {si} z~{s['z_mean']} w {w:.1f} tiles {n_tiles}: " + fmt(s, 'CLEAN'))
            if n_mont < 4: n_mont += 1; yc0 = jt[0][0] + T // 2; s['_xz'] = V[max(0, int(s['z_mean']) - 48):int(s['z_mean']) + 48, yc0, :512].copy(); s['_h'] = h_ref[yc0, :512].copy() - max(0, int(s['z_mean']) - 48); s['_yc'] = yc0
        # secondary, masked analysis: every tile with >= masked_tile_min_frac clean columns, unclean columns zeroed in data and surrogates alike
        jm = [ij for ij, f in zip(tij, tile_frac) if f >= P['masked_tile_min_frac']]; s['n_tiles_masked'] = len(jm); s['is_masked_usable'] = bool(len(jm) >= P['sheet_min_tiles'] and w == w)
        if s['is_masked_usable']:
            masks = [clean[i:i + T, j:j + T].astype(np.float32) for i, j in jm]; s['masked'] = band_stats(jm, masks, max(n_null // 2, 50), n_mont_m < 4); s['masked']['n_tiles'] = len(jm); s['masked']['clean_frac_mean'] = round(float(np.mean([mk.mean() for mk in masks])), 3)
            log(f"[{tag}] sheet {si} z~{s['z_mean']} w {w:.1f} masked tiles {len(jm)} (clean frac {s['masked']['clean_frac_mean']:.2f}): " + fmt(s['masked'], 'MASKED'))
            if n_mont_m < 4: n_mont_m += 1; yc0 = jm[0][0] + T // 2; s['masked']['_xz'] = V[max(0, int(s['z_mean']) - 48):int(s['z_mean']) + 48, yc0, :512].copy(); s['masked']['_h'] = h_ref[yc0, :512].copy() - max(0, int(s['z_mean']) - 48); s['masked']['_yc'] = yc0; s['masked']['_clean'] = clean[yc0, :512].copy()
        if not s['is_clean']: log(f"[{tag}] sheet {si} z~{s['z_mean']} NOT clean: tiles {n_tiles} (best tile clean frac {s['tile_clean_frac_max']:.2f}), clean cols {s['clean_col_frac']}, fwhm {s['fwhm_vox']}, breakdown {s['col_clean_breakdown']}")
        out_sheets.append(s)
    rec['sheets'] = out_sheets; rec['secs'] = round(time.time() - t0, 1); return rec

def aggregate(recs, masked=False):
    get = (lambda s: s.get('masked')) if masked else (lambda s: s if s['is_clean'] else None)
    cs = [get(s) for r in recs for s in r['sheets'] if get(s) is not None]; n = len(cs)
    agg = {'mode': 'masked secondary (tiles with >= %.0f %% clean columns, unclean columns zeroed in data and nulls)' % (100 * P['masked_tile_min_frac']) if masked else 'primary (clean tiles only)', 'n_sheets_tracked': sum(len(r['sheets']) for r in recs), 'n_clean_sheets': n, 'min_clean_sheets': P['min_clean_sheets']}
    if n == 0: agg.update({'gate': 'CLOSED', 'reason': 'no usable sheets'}); return agg
    dth = np.array([s['dtheta_outer'] for s in cs]); alt = np.array([s['alternation'] for s in cs]); D = np.stack([s['_dnull'] for s in cs], 1)   # (n_null, n_sheets)
    med_null = np.median(D, 1); agg.update({'alternation_fraction': round(float(alt.mean()), 3), 'alternation_count': int(alt.sum()),
        'median_dtheta_outer': round(float(np.median(dth)), 1), 'median_dtheta_outer_null_p50': round(float(np.percentile(med_null, 50)), 1), 'median_dtheta_outer_null_p95': round(float(np.percentile(med_null, 95)), 1),
        'median_dtheta_exceeds_null_p95': bool(np.median(dth) > np.percentile(med_null, 95)), 'frac_sheets_dtheta_exceeds_own_null_p95': round(float(np.mean([s['dtheta_outer_exceeds_null_p95'] for s in cs])), 3),
        'frac_q0_A_above_null': round(float(np.mean([s['bands']['q0']['A_above_null'] for s in cs])), 3), 'frac_q3_A_above_null': round(float(np.mean([s['bands']['q3']['A_above_null'] for s in cs])), 3),
        'frac_gap_A_above_null': round(float(np.mean([s['bands'][g]['A_above_null'] for s in cs for g in ('g0', 'g1')])), 3), 'frac_inner_A_above_null': round(float(np.mean([s['bands'][g]['A_above_null'] for s in cs for g in ('q1', 'q2')])), 3),
        'median_dtheta_q0_q1': round(float(np.median([s['dtheta_q0_q1'] for s in cs])), 1), 'median_dtheta_q2_q3': round(float(np.median([s['dtheta_q2_q3'] for s in cs])), 1), 'median_dtheta_inner': round(float(np.median([s['dtheta_inner'] for s in cs])), 1),
        'median_dtheta_pr_null': round(float(np.median([s['dtheta_pr_null'] for s in cs])), 1), 'median_A_q0': round(float(np.median([s['bands']['q0']['A'] for s in cs])), 4), 'median_A_q3': round(float(np.median([s['bands']['q3']['A'] for s in cs])), 4),
        'median_null_iso_A_p95': round(float(np.median([s['bands'][b]['null_iso_A_p95'] for s in cs for b in ('q0', 'q3')])), 4), 'theta_q0_list': [s['bands']['q0']['theta'] for s in cs], 'theta_q3_list': [s['bands']['q3']['theta'] for s in cs], 'dtheta_outer_list': [float(v) for v in dth]})
    enough = n >= P['min_clean_sheets']; majority = agg['alternation_fraction'] > 0.5; agg['gate'] = 'OPEN' if (enough and majority and agg['median_dtheta_exceeds_null_p95']) else 'CLOSED'
    agg['reason'] = ('; '.join([x for x, c in [('fewer than 20 clean sheets', not enough), ('alternation on <= 50 % of clean sheets', not majority), ('median dtheta not above its null p95', not agg['median_dtheta_exceeds_null_p95'])] if c]) or 'all three conditions met')
    return agg

def strip_private(o):
    if isinstance(o, dict): return {k: strip_private(v) for k, v in o.items() if not k.startswith('_')}
    if isinstance(o, list): return [strip_private(v) for v in o]
    if isinstance(o, (np.floating, np.integer)): return o.item()
    if isinstance(o, np.bool_): return bool(o)
    return o

def montage(recs, path, title, masked=False):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    get = (lambda s: s.get('masked')) if masked else (lambda s: s if s['is_clean'] else None)
    cs = [(s, get(s)) for r in recs for s in r['sheets'] if get(s) is not None and '_xz' in get(s)][:4]
    if not cs: return False
    fig, ax = plt.subplots(len(cs), 5, figsize=(22, 4.2 * len(cs)), squeeze=False)
    for i, (s, r) in enumerate(cs):
        b0, b3 = r['bands']['q0'], r['bands']['q3']; w = s['fwhm_vox']
        a = ax[i, 0]; a.imshow(r['_xz'], cmap='gray', aspect='auto'); x = np.arange(512); h = r['_h']
        for d, c in [(-w / 2, 'c'), (-w / 4, 'c'), (w / 4, 'm'), (w / 2, 'm')]: a.plot(x, h + d, c, lw=0.6)
        if '_clean' in r: a.plot(x[r['_clean']], np.full(int(r['_clean'].sum()), 2.0), 'y.', ms=2)
        a.set_title(f"sheet {s['sheet']} xz at y={r['_yc']} (z~{s['z_mean']}, FWHM {w}); q0 cyan, q3 magenta" + ('; clean columns yellow' if masked else ''), fontsize=9)
        for j, (b, nm) in enumerate([(b0, 'q0 (z-neg outer quartile)'), (b3, 'q3 (z-pos outer quartile)')]):
            t = b['_tile']; a = ax[i, 1 + j]; a.imshow(t, cmap='gray', vmin=np.percentile(t, 1), vmax=np.percentile(t, 99)); a.set_title(f"{nm} tile (y down, x right)", fontsize=9); a.set_xlabel('x (around roll)'); a.set_ylabel('y (roll axis)')
            Pm = np.fft.fftshift(np.log10(b['_P'] + 1e-12)); a = ax[i, 3 + j]; a.imshow(Pm, cmap='magma', vmin=np.percentile(Pm, 5), vmax=np.percentile(Pm, 99.5), extent=[-T / 2, T / 2, T / 2, -T / 2])
            for rr in (K_LO, K_HI): a.add_patch(plt.Circle((0, 0), rr, fill=False, ec='w', lw=0.6))
            th = np.radians(b['theta'] - 90); a.plot([-0.4 * T * np.cos(th), 0.4 * T * np.cos(th)], [-0.4 * T * np.sin(th), 0.4 * T * np.sin(th)], 'c--', lw=0.8)
            a.set_title(f"log P {nm[:2]}: A {b['A']:.3f} (null p95 {b['null_iso_A_p95']:.3f}) theta {b['theta']:.0f}", fontsize=9); a.set_xlabel('kx'); a.set_ylabel('ky')
        ax[i, 0].text(0.01, 0.02, f"dtheta {r['dtheta_outer']} (null p95 {r['dtheta_outer_null_p95']}) alternation {r['alternation']}", transform=ax[i, 0].transAxes, color='y', fontsize=9)
    fig.suptitle(title, fontsize=11); plt.tight_layout(); plt.savefig(path, dpi=80); plt.close(fig); return True

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--windows', nargs='*', default=['5760,7888,5488', '5760,8912,5488', '5760,6864,5488', '5760,7888,4464', '5760,7888,6512', '4736,7888,5488', '6784,7888,5488', '5760,9936,5488'], help='y0,z0,x0 of 128 x 1024 x 1024 level-0 windows, used in the declared order until >= 20 clean sheets')
    ap.add_argument('--threads', type=int, default=3); ap.add_argument('--n_null', type=int, default=200); ap.add_argument('--n_pr', type=int, default=20); ap.add_argument('--phantom', default=None, choices=[None, 'bilayer', 'same', 'iso']); ap.add_argument('--phantom_contrast', type=float, default=0.08); ap.add_argument('--phantom_w', type=float, default=13.0); ap.add_argument('--phantom_blur', type=float, default=1.0, help='isotropic gaussian sigma (vox) standing in for the Paganin low-pass; the scan has a 3.7-vox Paganin length partly undone by the unsharp mask'); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); rng = np.random.default_rng(a.seed); t0 = time.time()
    if a.phantom:
        tagp = f'phantom_{a.phantom}' + (f'_w{a.phantom_w:g}_blur{a.phantom_blur:g}_c{a.phantom_contrast:g}' if (a.phantom_w, a.phantom_blur, a.phantom_contrast) != (13.0, 1.0, 0.08) else ''); slab, truth = make_phantom(a.phantom, rng, w=a.phantom_w, contrast=a.phantom_contrast, blur=a.phantom_blur); rec = analyse_window(slab, tagp, rng, a.n_null, a.n_pr, truth=truth); recs = [rec]; agg = aggregate(recs); agg_m = aggregate(recs, masked=True)
        agg['phantom'] = {'kind': a.phantom, 'contrast': a.phantom_contrast, 'w_vox': a.phantom_w, 'blur_sigma_vox': a.phantom_blur, 'n_sheets_true': len(truth), 'expected': {'bilayer': 'dtheta ~90, both outer quartiles above null, q0 theta ~0 (along x), q3 theta ~90', 'same': 'dtheta ~0, both above null', 'iso': 'A at null level, gate closed'}[a.phantom]}
        agg['tracking_err_median_vox'] = [s.get('truth_err_median_vox') for s in rec['sheets']]
        res = {'provenance': 'Project HERCULES | [id removed]', 'stage': 'DECL-UNR-1 X3 gate 0 phantom control', 'params': P, 'annulus_cycles_per_tile': [K_LO, K_HI], 'aggregate': agg, 'aggregate_masked_secondary': agg_m, 'windows': recs, 'secs': round(time.time() - t0, 1)}
        json.dump(strip_private(res), open(os.path.join(a.out, f'{tagp}.json'), 'w'), indent=1); montage(recs, os.path.join(a.out, f'{tagp}_montage.png'), f'X3 gate 0 phantom control: {a.phantom} (w {a.phantom_w:g} vox, blur {a.phantom_blur:g}, contrast {a.phantom_contrast})'); montage(recs, os.path.join(a.out, f'{tagp}_montage_masked.png'), f'X3 gate 0 phantom control, masked analysis: {a.phantom}', masked=True)
        print(json.dumps(strip_private(agg), indent=1)); return
    meta = read_phase_metadata(); print('phase retrieval:', json.dumps(meta)[:400]); recs = []
    for wtxt in a.windows:
        y0, z0, x0 = [int(v) for v in wtxt.split(',')]; slab, ft = fetch_window(y0, z0, x0, a.threads); print(f'window y{y0} z{z0} x{x0}: fetch {ft}', flush=True)
        rec = analyse_window(slab, f'y{y0}_z{z0}_x{x0}', rng, a.n_null, a.n_pr); rec.update({'y0': y0, 'z0': z0, 'x0': x0, 'fetch': ft}); recs.append(rec); del slab
        n_clean = sum(s['is_clean'] for r in recs for s in r['sheets']); n_m = sum(s.get('is_masked_usable', False) for r in recs for s in r['sheets']); print(f'clean sheets so far {n_clean} (masked-usable {n_m})', flush=True)
        json.dump(strip_private({'partial': True, 'windows': recs}), open(os.path.join(a.out, 'gate0_partial.json'), 'w'))
        if n_clean >= P['min_clean_sheets'] and n_m >= P['min_clean_sheets']: break
    agg = aggregate(recs); agg_m = aggregate(recs, masked=True)
    res = {'provenance': 'Project HERCULES | [id removed]', 'stage': 'DECL-UNR-1 item 5, X3 gate 0 (existence test)', 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'volume': VOL + '/0', 'vox_um': VOX, 'phase_retrieval_metadata': meta,
           'params': P, 'annulus_cycles_per_tile': [K_LO, K_HI], 'annulus_wavelength_um': [round(T / K_HI * VOX, 1), round(T / K_LO * VOX, 1)], 'calibration_record': CALIBRATION, 'n_null': a.n_null, 'n_pr': a.n_pr, 'threads': a.threads, 'aggregate': agg, 'aggregate_masked_secondary': agg_m, 'windows': recs, 'secs': round(time.time() - t0, 1),
           'claims': 'measurement only: no letters, no readings, no recto/verso naming; angles are relative to the volume axes (0 = x, 90 = y)'}
    json.dump(strip_private(res), open(os.path.join(a.out, 'gate0.json'), 'w'), indent=1); montage(recs, os.path.join(a.out, 'gate0_montage.png'), 'X3 gate 0, PHerc0268 level 0: outer depth quartiles of 4 clean sheets and their periodograms')
    montage(recs, os.path.join(a.out, 'gate0_montage_masked.png'), 'X3 gate 0, PHerc0268 level 0, MASKED secondary analysis: outer depth quartiles of 4 laminae (unclean columns zeroed) and their periodograms', masked=True)
    if os.path.exists(os.path.join(a.out, 'gate0_partial.json')): os.remove(os.path.join(a.out, 'gate0_partial.json'))
    print(json.dumps(strip_private(agg), indent=1)); print(json.dumps(strip_private(agg_m), indent=1)); print('done', round(time.time() - t0), 's')

if __name__ == '__main__': main()
