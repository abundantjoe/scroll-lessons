#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 stage X0: level-2 census along the stacking direction of PHerc0268 on N xz sections spread over y (one
chunk-aligned y-row of 128 sections per sample; the row is the minimum read). Per section: stripe removal, 3-D structure
tensor on a 16-section sub-slab (|n_z|, y-tilt, |n_y|), rays along the local layering normal on a 256^2 tile grid, raw-CT
lamina peaks (prominence >= 3 MAD), peak widths (sheet thickness), gaps and pitches with the two-peak/one-voxel-dip
separability test; region class per tile from the level-3 defect density (defects.json mapped x2). Records the m7
level-2 .zarray, a timed m7 chunk-column read, `free -m` before/after every row, and the fetch timing of every CT row.
Writes <out>/census.json and per-section histograms. usage: census.py <out_dir> [--rows 3 5 7 ...] [--n_rows 20]
"""
import argparse, json, os, sys, time, subprocess, numpy as np, s3fs
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb')); from st_axis import stripe_removal

B = 'vesuvius-challenge-open-data/PHerc0268'; CT = f'{B}/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/2'
M7 = f'{B}/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr/2'
VOX = 34.56; mm = 1000.0 / VOX

def free_mb():
    try: return int(subprocess.run(['free', '-m'], capture_output=True, text=True).stdout.split('\n')[1].split()[6])
    except Exception: return -1

def fetch_row(fs, key, za, j, threads=32):
    """y chunk-row j of a (z,y,x) zarr level as (Y_row, Z, X) uint8 (sections along y)."""
    Z, Y, X = za['shape']; cz, cy, cx = za['chunks']; sep = za.get('dimension_separator', '.'); comp = za.get('compressor'); dec = None
    if comp: from numcodecs import get_codec; dec = get_codec(comp)
    ny = min(cy, Y - j * cy); out = np.zeros((ny, Z, X), np.uint8); keys = [(i, k) for i in range((Z - 1) // cz + 1) for k in range((X - 1) // cx + 1)]
    def get(ik):
        i, k = ik
        try: raw = fs.cat_file(f'{key}/{i}{sep}{j}{sep}{k}')
        except FileNotFoundError: return ik, None
        return ik, np.frombuffer(dec.decode(raw) if dec else raw, np.uint8).reshape((cz, cy, cx))
    t0 = time.time(); n = 0
    with ThreadPoolExecutor(threads) as ex:
        for (i, k), a in ex.map(get, keys):
            if a is None: continue
            n += 1; zs, ze = i * cz, min((i + 1) * cz, Z); xs, xe = k * cx, min((k + 1) * cx, X); out[:, zs:ze, xs:xe] = a[:ze - zs, :ny, :xe - xs].transpose(1, 0, 2)
    return out, {'chunks_present': n, 'chunks_total': len(keys), 'secs': round(time.time() - t0, 1), 'MB': round(out.nbytes / 1e6)}

def section_census(stack, defects_xz, tile=256):
    """stack: (16, Z, X) uint8 sub-slab; the middle section is analysed with rays along the local normal."""
    n, Z, X = stack.shape; mask = (stack > 0).mean(0) > 0.5; img = stack[n // 2].astype(np.float32) / 255.0; img = stripe_removal(img, mask)
    v = stack.astype(np.float32) / 255.0; g = [ndi.gaussian_filter(v, 1.0, order=o) for o in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]]   # (y, z, x) derivative order
    J = np.zeros((Z // 8, X // 8, 3, 3), np.float32)
    for a in range(3):
        for b in range(a, 3): J[..., a, b] = J[..., b, a] = ndi.gaussian_filter(g[a] * g[b], 2.0)[n // 2, ::8, ::8][:Z // 8, :X // 8]
    w, e = np.linalg.eigh(J); nrm = e[..., :, 2]; coh = (w[..., 2] - w[..., 1]) / (w[..., 2] + 1e-12)
    ny_, nz_, nx_ = np.abs(nrm[..., 0]), np.abs(nrm[..., 1]), np.abs(nrm[..., 2]); m8 = mask[::8, ::8][:Z // 8, :X // 8]
    tiles = []; sm = ndi.gaussian_filter(img, 0.8)
    for tz in range(0, Z - tile + 1, tile):
        for tx in range(0, X - tile + 1, tile):
            tm = mask[tz:tz + tile, tx:tx + tile]
            if tm.mean() < 0.5: continue
            cz_, cx_ = tz // 8 + tile // 16, tx // 8 + tile // 16; nz0, ny0, nx0, c0 = float(nz_[cz_, cx_]), float(ny_[cz_, cx_]), float(nx_[cz_, cx_]), float(coh[cz_, cx_])
            # rays along the local in-plane normal (z-dominant): direction (dz, dx) = (nz, nx) normalised in the section
            dz, dx = nz0, np.sign(nrm[cz_, cx_, 2]) * nx0 if nz0 > 0 else 1.0; nn = np.hypot(dz, dx) + 1e-9; dz, dx = dz / nn, dx / nn
            widths, gaps, pitches, sep_rays, rays = [], [], [], 0, 0
            for s in range(8):
                x0 = tx + tile * (s + 0.5) / 8; z0 = tz; L = np.arange(0, tile, 0.5); zs, xs = z0 + L * dz, x0 + L * dx
                ok = (zs >= 0) & (zs < Z - 1) & (xs >= 0) & (xs < X - 1); zs, xs = zs[ok], xs[ok]
                if len(zs) < 40: continue
                prof = ndi.map_coordinates(sm, [zs, xs], order=1); inm = ndi.map_coordinates(mask.astype(np.float32), [zs, xs], order=0) > 0.5; prof[~inm] = np.nan
                p = prof[np.isfinite(prof)]
                if len(p) < 40: continue
                mad = np.median(np.abs(p - np.median(p))) + 1e-6; pk, pr = find_peaks(p, prominence=3 * mad, width=1); rays += 1
                if len(pk) < 2: continue
                wd = pr['widths'] * 0.5; pitches += np.diff(pk * 0.5).tolist(); widths += wd.tolist()
                for a, b in zip(pk[:-1], pk[1:]):
                    dip = p[a:b].min(); sep = (p[a] - dip >= 1 / 255.0 * 3) and (p[b] - dip >= 3 / 255.0) and (b - a >= 2); gaps.append(float((b - a) * 0.5 - (wd[0] if len(wd) else 0)))
                    sep_rays += int(sep)
            dens = defects_xz(tz + tile // 2, tx + tile // 2)
            tiles.append({'tz': tz, 'tx': tx, 'n_z': round(nz0, 3), 'n_y': round(ny0, 3), 'coh': round(c0, 3), 'rays': rays, 'n_peaks_pairs': len(pitches), 'separable_frac': round(sep_rays / max(len(pitches), 1), 3),
                          'width_vox_p10_50_90': np.percentile(widths, [10, 50, 90]).round(2).tolist() if widths else None, 'pitch_vox_p10_50_90': np.percentile(pitches, [10, 50, 90]).round(2).tolist() if pitches else None,
                          'gap_vox_p50': round(float(np.median(gaps)), 2) if gaps else None, 'defect_density_per_cm2': round(dens, 1), 'region_class': 'fold_band' if dens > 8 else ('edge' if (tx < X * 0.2 or tx > X * 0.8) else 'flat')})
    return {'n_tiles': len(tiles), 'tiles': tiles, 'nz_median_mask': round(float(np.median(nz_[m8])), 3) if m8.any() else None, 'ny_median_mask': round(float(np.median(ny_[m8])), 3) if m8.any() else None, 'coh_median_mask': round(float(np.median(coh[m8])), 3) if m8.any() else None}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--rows', type=int, nargs='*', default=None); ap.add_argument('--n_rows', type=int, default=20); ap.add_argument('--defects', default='logs/umb/PHerc0268/defects.json')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); fs = s3fs.S3FileSystem(anon=True); za = json.loads(fs.cat_file(CT + '/.zarray')); zm = json.loads(fs.cat_file(M7 + '/.zarray'))
    rec = {'ct_zarray': {k: za.get(k) for k in ['shape', 'chunks', 'dtype', 'compressor', 'dimension_separator']}, 'm7_zarray': {k: zm.get(k) for k in ['shape', 'chunks', 'dtype', 'compressor', 'dimension_separator']}, 'vox_um': VOX, 'rows': []}
    Z, Y, X = za['shape']; cy = za['chunks'][1]; nrows = (Y - 1) // cy + 1; rows = a.rows if a.rows else [int(round(r)) for r in np.linspace(3, nrows - 4, a.n_rows)]
    D = json.load(open(a.defects)); per = D['per_section']; zmid3 = [16 * i + 7.5 for i in range(len(per))]
    def defects_xz_factory(y2):
        y3 = y2 / 2.0; i = int(np.argmin(np.abs(np.array(zmid3) - y3))); pts = per[i]
        def dens(z2, x2):
            z3, x3 = z2 / 2.0, x2 / 2.0; r = 5.0 * (1000 / 69.12); k = sum(1 for d in pts if (d['x'] - x3) ** 2 + (d['z'] - z3) ** 2 <= r * r); return k / (np.pi * 25) * 100   # per cm^2
        return dens
    # timed m7 chunk column (one chunk row of m7, same geometry) for the resident-budget record
    t0 = time.time(); fm = free_mb(); m7row, m7t = fetch_row(fs, M7, zm, rows[0]); rec['m7_timed_row'] = {'row': rows[0], **m7t, 'free_mb_before': fm, 'free_mb_after': free_mb(), 'nonzero_frac': round(float((m7row > 0).mean()), 4), 'value_hist_top': np.argsort(np.bincount(m7row[::4, ::4, ::4].ravel(), minlength=256))[-4:][::-1].tolist()}; del m7row
    print(json.dumps(rec['m7_timed_row']), flush=True)
    for j in rows:
        fm = free_mb(); row, ft = fetch_row(fs, CT, za, j); y0 = j * cy; print(f'row {j} y {y0}-{y0 + row.shape[0]} fetched {ft} free_mb {fm}->{free_mb()}', flush=True)
        sec = row.shape[0] // 2; sub = row[sec - 8:sec + 8]; c = section_census(sub, defects_xz_factory(y0 + sec)); c.update({'row': j, 'y_section': y0 + sec, 'fetch': ft, 'free_mb_before': fm, 'free_mb_after': free_mb()}); rec['rows'].append(c)
        json.dump(rec, open(os.path.join(a.out, 'census.json'), 'w'), indent=1); del row
        print(json.dumps({k: c[k] for k in ['row', 'y_section', 'n_tiles', 'nz_median_mask', 'ny_median_mask', 'coh_median_mask']}), flush=True)
    # scroll-wide summary per region class
    allt = [t for r in rec['rows'] for t in r['tiles']]; summ = {}
    for cls in ['flat', 'fold_band', 'edge']:
        tt = [t for t in allt if t['region_class'] == cls and t['pitch_vox_p10_50_90']]
        if not tt: continue
        summ[cls] = {'tiles': len(tt), 'separable_frac_median': round(float(np.median([t['separable_frac'] for t in tt])), 3), 'width_vox_median_of_p50': round(float(np.median([t['width_vox_p10_50_90'][1] for t in tt])), 2), 'pitch_vox_p10_of_tiles': round(float(np.percentile([t['pitch_vox_p10_50_90'][0] for t in tt], 50)), 2), 'pitch_vox_median': round(float(np.median([t['pitch_vox_p10_50_90'][1] for t in tt])), 2)}
    rec['summary'] = summ; json.dump(rec, open(os.path.join(a.out, 'census.json'), 'w'), indent=1); print('SUMMARY', json.dumps(summ), flush=True)

if __name__ == '__main__': main()
