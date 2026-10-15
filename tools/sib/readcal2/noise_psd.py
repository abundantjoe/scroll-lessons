# Provenance: Project HERCULES | owner the owner | [id removed]
"""Noise model for the READCAL-2 exemplar/placebo sheets: power spectrum of blank 9 um base maps (C2-NT: official
infer, base ink_9um step-075000, no TTA) of the two SEAL-J-D1 blank windows on clean PHerc0139 w053, computed from
the organizer surface volume (official SV, 28 slices; the official infer takes the centred 17 of them, slices 6..22).
Numbers only: the maps are decoded to arrays, never displayed; no pixel array is printed or committed.

Text order = forward (TEXT-ORDER-D1). Valid = the 2136 px window where the two SV slices around the surface (13, 14)
are nonzero, eroded by 64 px (half the model patch: mesh edges and their blending excluded).
PRIMARY estimator: full-window masked periodogram (rc2lib.periodogram_masked, Gaussian validity taper 32 px), pooled
over both blanks weighted by sum(w^2); it resolves letter-scale frequencies (1/2136 cycles/px and up).
CROSS-CHECK: Welch periodogram on fully valid 256 px tiles (step 128, Hann); both radially averaged in bins. Output:
logs/sib/readcal2/noise_psd.json (radial PSD, moments, provenance hashes) and noise_psd_2d.npz (256 x 256 float32).
Run with /opt/hv-ink/bin/python (tifffile + imagecodecs for the LZW TIFFs)."""
import hashlib
import json
import os
import sys

import cv2
import numpy as np
import tifffile
import zarr
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import rc2lib as R  # noqa: E402

N = '/work/rc2/noise'
WINDOWS = ['blank_w053_y256_x1536', 'blank_w053_y256_x7168']
CKPT_SHA = 'e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    rec = {'provenance': R.PROV, 'serves': 'READCAL-2 exemplar/placebo noise model (task readcal2 item 1)',
           'viewing': 'no image opened, displayed or described; arrays decoded for statistics only',
           'model': {'checkpoint': 'scrollprize/ink_9um hybrid_3d2d-seed42 step-075000', 'sha256': CKPT_SHA,
                     'command': 'vesuvius.ink_detection.inference.infer <crop.zarr> CKPT OUT.tif --direction both '
                                '--batch-size 4 --num-workers 1 --no-compile (no TTA; CPU, 3 threads)'},
           'input': 'organizer SV 9.362um-1.2m-113keV-volume-20250728140407.zarr of 20260220000000-w053_2026022021, '
                    'window + 128 px, 28 slices; infer centre-crops 17 (slices 6..22, centre 14 vs surface 13.5: a '
                    'half-voxel offset from the -n 31 render path of D1, disclosed)',
           'windows': {}}
    acc = {'fwd': [], 'rev': []}
    accm = {'fwd': [], 'rev': []}
    vals = {'fwd': [], 'rev': []}
    for w in WINDOWS:
        crop = json.load(open(f'{N}/crop_{w}.json'))
        oy, ox = crop['window_in_crop']['y0'], crop['window_in_crop']['x0']
        sv = zarr.open(f'{N}/{w}.zarr', mode='r')[:]
        valid_full = (sv[13] > 0) & (sv[14] > 0)
        valid = valid_full[oy:oy + R.WINDOW_PX, ox:ox + R.WINDOW_PX]
        valid = ndimage.binary_erosion(valid, np.ones((129, 129), bool), border_value=0)
        wr = {'crop_sha256_uint8': crop['sha256_uint8'], 'valid_frac_eroded': float(valid.mean())}
        for order, suf in (('fwd', ''), ('rev', '_reverse')):
            p = f'{N}/infer/{w}/{w}{suf}.tif'
            a = tifffile.imread(p)
            a = np.asarray(a, np.float64)
            if a.max() <= 1.0 + 1e-9:
                a = a * 255.0
            win = a[oy:oy + R.WINDOW_PX, ox:ox + R.WINDOW_PX]
            p2 = R.periodogram_tiles(win, valid, 256, 128)
            pm = R.periodogram_masked(win, valid)
            wv = R.taper_weights(valid, 32.0)
            accm[order].append((pm, float((wv ** 2).sum())))
            ntile = sum(1 for y in range(0, R.WINDOW_PX - 255, 128) for x in range(0, R.WINDOW_PX - 255, 128)
                        if valid[y:y + 256, x:x + 256].all())
            acc[order].append((p2, ntile))
            v = win[valid]
            vals[order].append(v)
            wr[order] = {'tif_sha256': sha(p), 'shape': list(a.shape), 'dtype_decoded': str(tifffile.imread(p).dtype),
                         'mean': float(v.mean()), 'std': float(v.std()),
                         'p01_p50_p99': [float(x) for x in np.percentile(v, [1, 50, 99])],
                         'frac_ge_150': float((v >= 150).mean()), 'n_tiles': ntile}
        rec['windows'][w] = wr
    out = {}
    for order in ('fwd', 'rev'):
        tot = sum(n for _, n in acc[order])
        p2 = sum(p * n for p, n in acc[order]) / tot
        f, pr = R.radial_average(p2, 64)
        v = np.concatenate(vals[order])
        wsum = sum(w for _, w in accm[order])
        pm = sum(p * w for p, w in accm[order]) / wsum
        fm, prm = R.radial_average(pm, 256)
        # cross-check on the tile band: ratio masked / tiles in the bins both resolve (0.02 .. 0.45 cycles/px)
        sel = (f >= 0.02) & (f <= 0.45)
        ratio = np.interp(f[sel], fm, prm) / pr[sel]
        out[order] = {'n_tiles': tot, 'mean': float(v.mean()), 'var_pixels': float(v.var()),
                      'var_psd_mean_masked': float(pm.mean()), 'var_psd_mean_tiles': float(p2.mean()),
                      'radial_f_cycles_per_canvas_px': [float(x) for x in fm], 'radial_psd_u8sq': [float(x) for x in prm],
                      'tiles_radial_f': [float(x) for x in f], 'tiles_radial_psd_u8sq': [float(x) for x in pr],
                      'crosscheck_masked_over_tiles_0.02_0.45': {'median': float(np.median(ratio)),
                                                                'min': float(ratio.min()), 'max': float(ratio.max())},
                      'power_frac_below_0.01_cyc_px': float(pm[np.sqrt(np.fft.fftfreq(pm.shape[0])[:, None] ** 2 +
                                                            np.fft.fftfreq(pm.shape[1])[None, :] ** 2) < 0.01].sum() / pm.sum())}
        if order == 'fwd':
            np.savez_compressed(os.path.join(REPO, 'logs/sib/readcal2/noise_psd_2d.npz'), psd2_tiles256=p2.astype(np.float32),
                                radial_f=fm.astype(np.float32), radial_psd=prm.astype(np.float32))
    rec['pooled'] = out
    rec['model_for_sheets'] = ('fwd (text order), masked estimator: NoiseModel(radial_f_cycles_per_canvas_px, '
                               'radial_psd_u8sq, mean, var=var_psd_mean_masked)')
    t = json.dumps(rec, indent=1) + '\n'
    open(os.path.join(REPO, 'logs/sib/readcal2/noise_psd.json'), 'w').write(t)
    print(json.dumps({o: {k: out[o][k] for k in ('n_tiles', 'mean', 'var_pixels', 'var_psd_mean_masked',
                                                 'var_psd_mean_tiles', 'crosscheck_masked_over_tiles_0.02_0.45',
                                                 'power_frac_below_0.01_cyc_px')} for o in out}))


if __name__ == '__main__':
    main()
