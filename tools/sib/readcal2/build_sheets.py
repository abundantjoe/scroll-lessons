# Provenance: Project HERCULES | owner the owner | [id removed]
"""Build the READCAL-2 sheets (deterministic; the builder never opens or views them):
  key sheet (regenerated; must equal METRIC-HASH-12), EX exemplar sheets at sigma 0.15 / 0.30 / 0.45 mm, and the
  EXPL placebo sheets (random stroke blobs of matched ink area and stroke width, the SAME noise field per sigma and
  the same labels). Noise: logs/sib/readcal2/noise_psd.json (fwd, masked estimator). Voxel size from the PHerc0139
  9.362 um volume metadata.json (I9).
Output: <out>/<uuid>.png (flat folder, uuid names from a seeded stream, no text chunks) and a manifest
  logs/sib/readcal2/sheets_manifest.json {uuid: kind, sigma, sha256} (the mapping is not secret: sheets are the same
  for every reader of an arm and carry no answer). Usage: python build_sheets.py [--seed 20260925] [--out DIR]"""
import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import rc2lib as R  # noqa: E402


def voxel_um():
    p = glob.glob('/work/rc2/s3/PHerc0139/volumes/20250728140407-*/metadata.json')
    md = json.load(open(p[0]))
    return float(md['scan']['tomo']['acquisition']['detector']['samplePixelSize']) * 1000.0


def noise_model():
    d = json.load(open(os.path.join(REPO, 'logs/sib/readcal2/noise_psd.json')))['pooled']['fwd']
    return R.NoiseModel(radial_f=np.array(d['radial_f_cycles_per_canvas_px']), radial_psd=np.array(d['radial_psd_u8sq']),
                        mean=float(d['mean']), var=float(d['var_psd_mean_masked']))


def main(seed, out):
    os.makedirs(out, exist_ok=True)
    vox = voxel_um()
    nm = noise_model()
    names = R.UuidStream(seed, 'sheets')
    man = {'provenance': R.PROV, 'seed': seed, 'voxel_um': vox, 'cap_height_mm': R.CAP_HEIGHT_MM,
           'ink_level': R.INK_LEVEL, 'noise_mean': nm.mean, 'noise_var': nm.var, 'sheets': {}}
    ks = R.keysheet()
    b = R.png_bytes(ks)
    assert R.sha256(b) == R.KEYSHEET_SHA256
    items = [('KEY', None, b, {})]
    covs, fpx = R.glyph_covs(vox)
    blobs, binfo = R.placebo_covs(covs, seed)
    man['font_px_canvas'] = fpx
    man['placebo_blobs'] = binfo
    for s in R.EXEMPLAR_MM:
        ex, st = R.render_sheet(covs, s, nm, vox, seed)
        pl, stp = R.render_sheet(blobs, s, nm, vox, seed)
        items.append(('EX', s, R.png_bytes(ex), st))
        items.append(('EXPL', s, R.png_bytes(pl), stp))
    for kind, s, png, st in items:
        u = names.next()
        with open(os.path.join(out, u + '.png'), 'wb') as f:
            f.write(png)
        man['sheets'][u] = {'kind': kind, 'sigma_mm': s, 'sha256': R.sha256(png), 'bytes': len(png), 'stats': st}
    t = json.dumps(man, indent=1) + '\n'
    open(os.path.join(REPO, 'logs/sib/readcal2/sheets_manifest.json'), 'w').write(t)
    print(json.dumps({u: (v['kind'], v['sigma_mm'], v['sha256'][:16]) for u, v in man['sheets'].items()}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=20260925)
    ap.add_argument('--out', default='/work/rc2/sheets')
    a = ap.parse_args()
    main(a.seed, a.out)
