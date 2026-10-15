# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-O model-input surface stacks (RULES.md DECL-P4-14 item 2), streamed from the official organizer surface volume.

Source (anonymous, official): s3://vesuvius-challenge-open-data/PHercParis4/segments/20260701183124-w010-027/
  surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr  (zarr v2, level 0 shape (109, 69760, 170000) uint8,
  chunks (109, 128, 128), no compressor; voxel 2.400 um from the volume metadata.json samplePixelSize 0.0024 mm).
The SV canvas IS the strip-a canvas (grid.json of p4-tiles-a: canvas 69760 x 170000, T = 8343, tile (r, c) =
rows [r*T, (r+1)*T), cols [c*T, (c+1)*T) from (0, 0), c0 = outer end; pixels beyond the canvas are 0).

Slab convention (verified, see logs/sib/chain2um/p4o/README.md):
- SV slice 54 (= (109-1)/2) is the mesh surface. The SV slice order equals official vc_render_tifxyz --flip-normals
  order (slice index grows along the negated mesh normal).
- A model with D layers "centred on the mesh" takes SV slices [54 - D//2, 54 - D//2 + D). For D = 62 that is [23, 85),
  identical to the chain2um-validated 2.4 um chain (render -n 63 centred at 31, layers [0, 62)), which reproduced the
  organizer canonical map at r = 0.99999 on PHerc0139 w043.
- Returned stacks are in SV order ("forward"). Reverse order = stack[..., ::-1]. The text order of a given checkpoint
  is the consumer's responsibility (both orders are mapped under DECL-DEVLOOP-SCREEN / DECL-P4-14).
- level 0 = native 2.400 um (the PHerc1667 ResNet3D-50 family's ruled geometry). level 2 = the organizer's XY 4x mean
  pyramid (9.6 um in XY, z unchanged); zpool=4 additionally mean-pools z in blocks of 4 (ink_9um-style 9.6 um isotropic).

API:   read_stack(y0, y1, x0, x1, z0=23, nz=62, level=0, zpool=1) -> (H, W, nz // zpool) uint8   (canvas px of `level`)
       tile_bounds(r, c, level=0) -> (y0, y1, x0, x1)
CLI:   python p4o_stack.py --tile r c [--roi y0 y1 x0 x1 (tile-relative)] [--z0 23 --nz 62 --level 0 --zpool 1] --out f.npz
Numbers only: nothing is displayed.
"""
import argparse, hashlib, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np

BASE = ('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/segments/20260701183124-w010-027/'
        'surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr')
NZ_SV, CH, T = 109, 128, 8343
SHAPES = {0: (69760, 170000), 1: (34880, 85000), 2: (17440, 42500)}
SURFACE_SLICE = 54
CACHE = os.environ.get('P4O_CHUNK_CACHE', '')  # optional local chunk cache directory


def _fetch(level, cy, cx):
    key = f'{level}/0/{cy}/{cx}'
    if CACHE:
        p = os.path.join(CACHE, key.replace('/', '_'))
        if os.path.exists(p):
            return np.fromfile(p, np.uint8).reshape(NZ_SV, CH, CH)
    for i in range(5):
        try:
            b = urllib.request.urlopen(f'{BASE}/{key}', timeout=60).read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None  # missing chunk = fill_value 0
            if i == 4:
                raise
        except Exception:
            if i == 4:
                raise
        time.sleep(2 ** i)
    a = np.frombuffer(b, np.uint8).reshape(NZ_SV, CH, CH)
    if CACHE:
        os.makedirs(CACHE, exist_ok=True); a.tofile(os.path.join(CACHE, key.replace('/', '_')))
    return a


def tile_bounds(r, c, level=0):
    s = 2 ** level
    return (r * T) // s, ((r + 1) * T) // s, (c * T) // s, ((c + 1) * T) // s


def read_stack(y0, y1, x0, x1, z0=23, nz=62, level=0, zpool=1, workers=16):
    H, W = SHAPES[level]
    assert 0 <= z0 and z0 + nz <= NZ_SV and nz % zpool == 0
    out = np.zeros((y1 - y0, x1 - x0, nz), np.uint8)
    cys = range(max(0, y0) // CH, (min(H, y1) - 1) // CH + 1) if min(H, y1) > max(0, y0) else []
    cxs = range(max(0, x0) // CH, (min(W, x1) - 1) // CH + 1) if min(W, x1) > max(0, x0) else []
    jobs = [(cy, cx) for cy in cys for cx in cxs]

    def put(job):
        cy, cx = job
        a = _fetch(level, cy, cx)
        if a is None:
            return 0
        gy0, gx0 = cy * CH, cx * CH
        sy0, sy1 = max(y0, gy0), min(y1, gy0 + CH, H); sx0, sx1 = max(x0, gx0), min(x1, gx0 + CH, W)
        blk = a[z0:z0 + nz, sy0 - gy0:sy1 - gy0, sx0 - gx0:sx1 - gx0]
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, :] = np.transpose(blk, (1, 2, 0))
        return 1

    with ThreadPoolExecutor(workers) as ex:
        n = sum(ex.map(put, jobs))
    if zpool > 1:
        out = np.rint(out.reshape(out.shape[0], out.shape[1], nz // zpool, zpool).mean(-1)).astype(np.uint8)
    return out


def stack_sha256(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tile', type=int, nargs=2, required=True, metavar=('R', 'C'))
    ap.add_argument('--roi', type=int, nargs=4, metavar=('Y0', 'Y1', 'X0', 'X1'), help='tile-relative, level px')
    ap.add_argument('--z0', type=int, default=23); ap.add_argument('--nz', type=int, default=62)
    ap.add_argument('--level', type=int, default=0); ap.add_argument('--zpool', type=int, default=1)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    ty0, ty1, tx0, tx1 = tile_bounds(*a.tile, level=a.level)
    y0, y1, x0, x1 = (ty0, ty1, tx0, tx1) if not a.roi else (ty0 + a.roi[0], ty0 + a.roi[1], tx0 + a.roi[2], tx0 + a.roi[3])
    s = read_stack(y0, y1, x0, x1, a.z0, a.nz, a.level, a.zpool)
    meta = dict(tile=a.tile, canvas_yx=[y0, y1, x0, x1], level=a.level, z0=a.z0, nz=a.nz, zpool=a.zpool,
                order='SV (forward); reverse = [..., ::-1]', shape=list(s.shape), sha256_uint8=stack_sha256(s))
    np.savez_compressed(a.out, stack=s, meta=json.dumps(meta))
    print(json.dumps(meta))


if __name__ == '__main__':
    main()
