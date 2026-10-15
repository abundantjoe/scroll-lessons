#!/usr/bin/env python
"""extract_w040_window.py -- write the committed w040 known-text window out as the three arrays the reader takes.

Source: packages/DRYRUN_PHerc0139_w040/ (built 2026-09-17, RULES.md P-DRY). Its PNGs hold the model's maps losslessly:
rows 0..2135 of each PNG are the uint8 map (grey, R = G = B); the rows below are a 1 cm scale bar and are dropped.
  mesh.png            forward map   = Gate A map of the w040 native stack, crop [1500:3636, 2000:4136]
  reverse_window.png  reverse map   = the same crop of the reverse-order map
  ct_window.png       CT            = slice 14 of the public w040 native stack, same crop
[line withheld: prize-candidate detail under review]

Every array is checked against a pixel SHA-256 before it is written. The forward and reverse values are the
`forward_window_sha256` / `reverse_window_sha256` recorded in package.json in September; the CT value equals
sha256(stack['0'][14, 1500:3636, 2000:4136]) of the public stack (re-verified 2026-10-15). A mismatch is a hard error.

usage: extract_w040_window.py <out_dir> [--truncate]
  writes <out_dir>/forward.tif, reverse.tif, ct_mid.tif (uint8);
  --truncate also writes reverse_truncated.tif: the reverse map with all but its top-left quadrant zeroed, which is
  exactly the failure found on 2026-09-19 (an inference that exited 0 having written one quadrant).
"""
import argparse, hashlib, os, sys
import numpy as np, tifffile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(os.path.dirname(HERE), "packages", "DRYRUN_PHerc0139_w040")
SIDE = 2136
EXPECTED = {
    "forward": ("mesh.png", "4eced8f47248bc97917fde970faf912c2f2f0f2fc4e7ca77cdbe60b752c443a2"),
    "reverse": ("reverse_window.png", "2522e6827513f358270a5b2fc72d70565a6239cf940357ceb47a747d276630f5"),
    "ct_mid": ("ct_window.png", "7d62c816e04126ba28c2a9f2379764c2de81b38762a46b44c76270a8728ae8dc"),
}


def load(name):
    png, want = EXPECTED[name]
    a = np.asarray(Image.open(os.path.join(PKG, png)))[:SIDE, :SIDE]
    if a.ndim == 3:
        if not ((a[..., 0] == a[..., 1]).all() and (a[..., 0] == a[..., 2]).all()):
            raise SystemExit("%s: map area is not grey; this is not the committed package file" % png)
        a = a[..., 0]
    a = np.ascontiguousarray(a, dtype=np.uint8)
    got = hashlib.sha256(a.tobytes()).hexdigest()
    if got != want:
        raise SystemExit("%s: pixel sha256 %s != recorded %s" % (png, got, want))
    return a, got


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--truncate", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    arrs = {}
    for name in EXPECTED:
        arrs[name], h = load(name)
        tifffile.imwrite(os.path.join(a.out, name + ".tif"), arrs[name])
        print("PASS %-8s %s  pixel sha256 %s... matches the record" % (name, arrs[name].shape, h[:16]))
    if a.truncate:
        t = np.zeros_like(arrs["reverse"])
        t[: SIDE // 2, : SIDE // 2] = arrs["reverse"][: SIDE // 2, : SIDE // 2]
        tifffile.imwrite(os.path.join(a.out, "reverse_truncated.tif"), t)
        print("wrote reverse_truncated.tif: non-zero fraction %.4f (forward %.4f)"
              % ((t > 0).mean(), (arrs["forward"] > 0).mean()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
