"""Write the arm lists of the PHerc0343 positive-control strip experiment and the displaced (negative) surface copy.

  python make_arms.py --erwin <pherc343-first-letters checkout> --out <dir>

Source: Erwin Nieuwlaar's public First Letters segment concat_w047-w048_R5B2_z9500-11000.tifxyz (128 x 336 nodes,
20 px per node). All arms use node cols 34:166 (letters 6-18). Arms (REF, Z13, Z20, P13, D8 pre-registered in docs/prereg/DECL-FL-STRIP.md; F13 and FD8 exploratory):
  REF  rows 40:110, full context            Z13  13-row strips 42:55 ... 94:107 (mass-run geometry, blank margins)
  Z20  20-row strips 42:62, 62:82, 82:102   P13  the Z13 rows + 2 real node rows each side (score target rows only)
  D8   the Z13 strips on a copy moved +8 vox along the outward normal (window centre between sheets: the negative arm)
  F13  the Z13 strips with the blank render margin reflect-filled for the ink models (RENDER_FILL=reflect)
  FD8  the D8 strips with the fill: the fill's floor on the negative arm
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stripqc import geometry, tifxyz  # noqa: E402

SEG = 'outputs/concat_w047-w048_R5B2_z9500-11000.tifxyz'
UMB = 'inputs/umbilicus_PHerc0343.json'
COLS = '34:166'
Z13 = [(42, 55), (55, 68), (68, 81), (81, 94), (94, 107)]
Z20 = [(42, 62), (62, 82), (82, 102)]

ap = argparse.ArgumentParser()
ap.add_argument('--erwin', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
src = os.path.join(a.erwin, SEG)
os.makedirs(a.out, exist_ok=True)
P, ok, meta = tifxyz.load(src)
Q, okq, frac = geometry.displace(P, ok, tifxyz.load_umbilicus(os.path.join(a.erwin, UMB)), d=8.0)
plus8 = os.path.join(a.out, 'plus8.tifxyz')
tifxyz.save(plus8, Q, okq, meta, uuid='ctrl343_plus8', name='ctrl343_plus8',
            source=f'{SEG} displaced +8 vox along the outward normal (stripqc.geometry.displace)')
plain = [f'ctrlS_REF_r40-110 {src} scroll=PHerc0343 rows=40:110 cols={COLS} depths=1']
plain += [f'ctrlS_Z13_r{x}-{y} {src} scroll=PHerc0343 rows={x}:{y} cols={COLS} depths=1' for x, y in Z13]
plain += [f'ctrlS_Z20_r{x}-{y} {src} scroll=PHerc0343 rows={x}:{y} cols={COLS} depths=1' for x, y in Z20]
plain += [f'ctrlS_P13_r{x}-{y} {src} scroll=PHerc0343 rows={x - 2}:{y + 2} cols={COLS} depths=1' for x, y in Z13]
plain += [f'ctrlS_D8_r{x}-{y} {plus8} scroll=PHerc0343 rows={x}:{y} cols={COLS} depths=1' for x, y in Z13]
fill = [f'ctrlS_F13_r{x}-{y} {src} scroll=PHerc0343 rows={x}:{y} cols={COLS} depths=1' for x, y in Z13]
fill += [f'ctrlS_FD8_r{x}-{y} {plus8} scroll=PHerc0343 rows={x}:{y} cols={COLS} depths=1' for x, y in Z13]
open(os.path.join(a.out, 'plain.list'), 'w').write('\n'.join(plain) + '\n')
open(os.path.join(a.out, 'fill.list'), 'w').write('\n'.join(fill) + '\n')
print(json.dumps(dict(source=src, outward_majority=round(frac, 4), plain=len(plain), fill=len(fill))))
