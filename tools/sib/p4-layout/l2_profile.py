"""DECL-P4-13 P4-M item 1, channel 3: P4-L thin-slab max (p4-l2 L2 tiles) accumulated into the same 1 mm bins.

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only: each PNG is decoded to a uint8 array in memory and reduced to bin sums; nothing is displayed.
The L2 display value is clip(255 (max - 93) / (203 - 93), 0, 255), area-downscaled 8343 -> 1068 (p4-l2
params.json), 0 outside mesh-valid. PNG px (y, x) of tile (r, c) is centred at canvas
(r T + (y + 0.5) T/1068, c T + (x + 0.5) T/1068); its value is added to that canvas point's 1 mm bin with weight
(T/1068)^2 canvas px. The mean per bin divides by the M1 run's mesh-valid canvas px count N of the same bin
(identical canvas and mask rule), so the channel is comparable across bins, though clipped below T_mid.
Usage: python l2_profile.py <git ref> <manifest path in ref> <m1 npz (for N and px_per_mm)> <out.npz>
"""
import json, subprocess, sys
import numpy as np
import imagecodecs


def main(ref, man, m1npz, out):
    z = np.load(m1npz)
    N, px, T = z["N"], float(z["px_per_mm"]), int(z["T"])
    S = np.zeros(N.shape, np.float64)
    M = json.loads(subprocess.check_output(["git", "show", f"{ref}:{man}"]))
    tiles = M["tiles"] if isinstance(M, dict) and "tiles" in M else M
    base = man.rsplit("/", 1)[0]
    n = 0
    for t in tiles:
        f = t.get("file") or t.get("png")
        if not f:
            continue
        b = subprocess.check_output(["git", "show", f"{ref}:{base}/{f}"])
        a = imagecodecs.png_decode(b)
        assert a.dtype == np.uint8 and a.ndim == 2, a.shape
        H = a.shape[0]
        s = T / H
        r, c = t["r"], t["c"]
        yc = r * T + (np.arange(H) + 0.5) * s
        xc = c * T + (np.arange(a.shape[1]) + 0.5) * s
        rb = np.minimum((yc / px).astype(int), S.shape[0] - 1)
        cb = np.minimum((xc / px).astype(int), S.shape[1] - 1)
        ids = (rb[:, None] * S.shape[1] + cb[None, :]).ravel()
        S.flat[:] += np.bincount(ids, weights=a.ravel().astype(np.float64) * s * s, minlength=S.size)
        n += 1
    np.savez_compressed(out, S=S, N=N, px_per_mm=px, H=z["H"], W=z["W"], T=T, n_tiles=n)
    print("tiles", n)


if __name__ == "__main__":
    main(*sys.argv[1:])
