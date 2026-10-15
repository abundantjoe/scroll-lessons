# Provenance: Project HERCULES | owner the owner | [id removed]
"""Crop the organizer 9.362 um surface volume (official SV, 28 slices) of clean PHerc0139 w053 around the two D1
blank windows (DECL-D1-A4: blank_w053_y256_x1536, blank_w053_y256_x7168; 2136 px, organizer canvas) plus a
128 px context margin, streamed chunk-wise from the official bucket (never the whole SV), into local zarr v2
arrays that the official infer CLI reads. Numbers only; nothing is displayed.
Output: /work/rc2/noise/<win>.zarr and /work/rc2/noise/crop_<win>.json (sha256 of the uint8 array)."""
import hashlib
import json
import os
import sys

import numpy as np
import s3fs
import zarr

SEG = '20260220000000-w053_2026022021'
SV = f'vesuvius-challenge-open-data/PHerc0139/segments/{SEG}/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr'
WINDOWS = {'blank_w053_y256_x1536': (256, 1536), 'blank_w053_y256_x7168': (256, 7168)}
WIN, MARGIN = 2136, 128
OUT = '/work/rc2/noise'


def main():
    os.makedirs(OUT, exist_ok=True)
    fs = s3fs.S3FileSystem(anon=True)
    arr = zarr.open(s3fs.S3Map(SV + '/0', s3=fs, check=False), mode='r')
    Z, H, W = arr.shape
    for name, (y0, x0) in WINDOWS.items():
        ya, yb = max(0, y0 - MARGIN), min(H, y0 + WIN + MARGIN)
        xa, xb = max(0, x0 - MARGIN), min(W, x0 + WIN + MARGIN)
        sub = np.asarray(arr[:, ya:yb, xa:xb])
        dst = zarr.open(f'{OUT}/{name}.zarr', mode='w', shape=sub.shape, chunks=(Z, 128, 128), dtype='u1',
                        compressor=None, fill_value=0)
        dst[:] = sub
        rec = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]',
                   source=f's3://{SV}/0', sv_shape=[Z, H, W], window=dict(y0=y0, x0=x0, h=WIN, w=WIN),
                   crop=dict(y=[ya, yb], x=[xa, xb]), window_in_crop=dict(y0=y0 - ya, x0=x0 - xa),
                   sha256_uint8=hashlib.sha256(np.ascontiguousarray(sub).tobytes()).hexdigest(),
                   valid_frac_any_slice=float((sub > 0).any(0).mean()))
        json.dump(rec, open(f'{OUT}/crop_{name}.json', 'w'), indent=1)
        print(json.dumps(rec))


if __name__ == '__main__':
    main()
