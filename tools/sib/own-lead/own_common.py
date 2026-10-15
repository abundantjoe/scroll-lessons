# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN (RULES.md DECL-P4-23) shared code: input, model, display. Numbers only; nothing here renders or views pixels
except the declared PNG encoder of the display (bytes are hashed, never opened).

Input (DECL-P4-23 item 3): organizer surface volume 2.4um-0.22m-78keV-volume-20260411134726 of the segment, level 0,
slices 23..84 forward, clip(0,200)/255, mesh-valid mask. The chunk reader, stack reader and canvas-mask rule are
ckpt-screen-b's p4o_tiles.py at 98cd075 (sha256 checked below), imported verbatim; only its segment globals
(SEG, SV, MESH, H0, W0) are set per segment, so w028-037 uses the identical code path.
Display (identical to P4-O): u8 = clip(p*255) truncated at full canvas resolution, 0 outside mesh-valid,
cv2.INTER_AREA 8343 -> 1068, PNG via hercules.display.builder.png_bytes (IHDR/IDAT/IEND only)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CKB = os.path.join(REPO, 'tools', 'sib', 'ckpt-screen-b')
sys.path.insert(0, CKB)
sys.path.insert(0, os.path.join(REPO, 'src'))
PROV = 'Project HERCULES | owner the owner | [id removed]'
CKB_COMMIT = '98cd075'
CKB_SHA = {'p4o_tiles.py': 'a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371',
           'infer_1667.py': '29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12'}
HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
VOL = '2.4um-0.22m-78keV-volume-20260411134726'
SEGS = {  # canvas shapes = level-0 zarr (109, H, W) shapes, read from .zarray
    '20260701183124-w010-027': (69760, 170000),
    '20260701183125-w028-037': (71600, 174640),
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
}
X_SEG = '20260701183124-w010-027'
T_TILE, OUT_SIDE = 8343, 1068
TILE_PX = {'20260701183124-w010-027': 8343,   # strip-a grid (pairs0814b e2/grid.json T_canvas_px)
           '20260701183125-w028-037': 8301,   # strip-b grid (p4-excl T_cert.json strips.w028-037.T_px)
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]


def tile_px(seg):
    return TILE_PX.get(seg, T_TILE)
Z0, Z1 = 23, 85                 # slices 23..84, forward
NZ = Z1 - Z0                    # 62
STRIDE_OUT = 4                  # model output stride (px)
WORK = os.environ.get('OWN_WORK', '/work/own')


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def arr_sha(a):
    a = np.ascontiguousarray(a)
    return sha_bytes(str(a.dtype).encode() + str(a.shape).encode() + a.tobytes())


def in_x_zone(seg, r, c):
    """DECL-P4-23 item 1: X = strip-a tiles c9-c19 (all rows) of w010-027."""
    return seg == X_SEG and 9 <= c <= 19


def check_ckb():
    for n, want in CKB_SHA.items():
        got = sha256_file(os.path.join(CKB, n))
        if got != want:
            raise SystemExit(f'ckpt-screen-b {n} sha256 {got} != {want} (need commit {CKB_COMMIT})')


_P = None


def p4o(seg):
    """ckpt-screen-b's p4o_tiles module with its segment globals set to `seg` (reader code itself unchanged)."""
    global _P
    if _P is None:
        check_ckb()
        import p4o_tiles
        _P = p4o_tiles
    _P.SEG = seg
    _P.SV = f'PHercParis4/segments/{seg}/surface-volumes/{VOL}.zarr'
    _P.MESH = f'PHercParis4/segments/{seg}/mesh/{seg.split("-")[0]}-on-20260411134726-2.4um.tifxyz'
    _P.H0, _P.W0 = SEGS[seg]
    assert (_P.Z0, _P.Z1) == (Z0, Z1)
    return _P


def load_valid(seg):
    """Mesh-valid grid of the segment's 2.4 um tifxyz (strip-a rule: no -1 coordinate, all finite). For w010-027 the
    tif sha256 are checked against the pairs0814b e2 manifest (as p4o_tiles.load_valid); for other segments the
    sha256 are recorded in <WORK>/<seg>/mesh_sha256.json."""
    P = p4o(seg)
    d = f'{WORK}/{seg}'
    cache = f'{d}/mesh_valid.npy'
    if os.path.exists(cache):
        return np.load(cache)
    import tifffile
    os.makedirs(f'{d}/mesh', exist_ok=True)
    want = {}
    if seg == X_SEG:
        e2 = P.git_json(P.E2_MANIFEST_REF)
        want = {k.split('/')[-1]: v for k, v in e2['input_sha256'].items() if k.endswith('.tif')}
    arrs, shas = [], {}
    for n in ('x.tif', 'y.tif', 'z.tif'):
        p = f'{d}/mesh/{n}'
        if not os.path.exists(p):
            subprocess.run(['curl', '-fsSL', '--retry', '4', '-o', p, f'{HTTP}/{P.MESH}/{n}'], check=True)
        shas[n] = sha256_file(p)
        if n in want and shas[n] != want[n]:
            raise SystemExit(f'mesh {n} sha256 {shas[n]} != e2 manifest {want[n]}')
        arrs.append(tifffile.imread(p))
    A = np.stack(arrs, -1)
    valid = ~((A[..., 0] == -1) | (A[..., 1] == -1) | (A[..., 2] == -1))
    valid &= np.isfinite(A).all(-1)
    H, W = SEGS[seg]
    assert valid.shape == (H // 20, W // 20), valid.shape
    np.save(cache, valid)
    json.dump(dict(seg=seg, sha256=shas, checked_against_e2=bool(want)), open(f'{d}/mesh_sha256.json', 'w'))
    return valid


def canvas_mask(seg, valid, y0, y1, x0, x1):
    H, W = SEGS[seg]
    return p4o(seg).canvas_mask(valid, H, W, y0, y1, x0, x1)


def read_region(seg, y0, y1, x0, x1):
    """(h, w, 62) uint8 raw stack of canvas rows [y0,y1), cols [x0,x1) of `seg`, forward order; zeros outside the
    array and for missing chunks (p4o_tiles.read_stack), plus its chunk records."""
    P = p4o(seg)
    return P.read_stack(y0, y1, x0, x1, y1 - y0, x1 - x0, 'forward')


def norm(u8):
    """clip(0,200)/255 as float32 (P4-O / infer_1667.train_norm)."""
    return np.minimum(u8, 200).astype(np.float32) / 255.0


# ---------------------------------------------------------------- model
def build_model(cfg):
    """3-D-to-2-D CNN, random init. Input (B,1,62,P,P) in [0, 0.785]; output logits (B,1,P/4,P/4).
    cfg: dict(w=(c1,c2,c3), head=c_head, dil=(...)). 3-D encoder: stride (2,2,2) -> (2,2,2) -> (2,1,1) -> (2,1,1),
    each stage conv + one residual 3x3x3 block (optional); depth collapsed by concatenated max and mean; 2-D head of
    dilated residual 3x3 blocks at stride 4; 1x1 conv to one logit."""
    import torch
    import torch.nn as nn

    c1, c2, c3 = cfg['w']
    ch, dil = cfg['head'], cfg['dil']
    res3 = cfg.get('res3', (False, True, True, True))

    def cbr3(i, o, k, s, p):
        return nn.Sequential(nn.Conv3d(i, o, k, s, p, bias=False), nn.BatchNorm3d(o), nn.ReLU(inplace=True))

    class Res3(nn.Module):
        def __init__(self, c):
            super().__init__()
            self.a = cbr3(c, c, 3, 1, 1)
            self.b = nn.Sequential(nn.Conv3d(c, c, 3, 1, 1, bias=False), nn.BatchNorm3d(c))

        def forward(self, x):
            return torch.relu(x + self.b(self.a(x)))

    class Res2(nn.Module):
        def __init__(self, c, d):
            super().__init__()
            self.a = nn.Sequential(nn.Conv2d(c, c, 3, 1, d, d, bias=False), nn.BatchNorm2d(c), nn.ReLU(inplace=True))
            self.b = nn.Sequential(nn.Conv2d(c, c, 3, 1, d, d, bias=False), nn.BatchNorm2d(c))

        def forward(self, x):
            return torch.relu(x + self.b(self.a(x)))

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            st = [cbr3(1, c1, (5, 3, 3), (2, 2, 2), (2, 1, 1)),
                  cbr3(c1, c2, 3, (2, 2, 2), 1),
                  cbr3(c2, c3, 3, (2, 1, 1), 1),
                  cbr3(c3, c3, 3, (2, 1, 1), 1)]
            chans = (c1, c2, c3, c3)
            self.enc = nn.ModuleList(nn.Sequential(s, Res3(c)) if r else s for s, c, r in zip(st, chans, res3))
            self.proj = nn.Sequential(nn.Conv2d(2 * c3, ch, 1, bias=False), nn.BatchNorm2d(ch), nn.ReLU(inplace=True))
            self.head = nn.Sequential(*[Res2(ch, d) for d in dil])
            self.out = nn.Conv2d(ch, 1, 1)

        def forward(self, x):
            for m in self.enc:
                x = m(x)
            x = torch.cat([x.amax(2), x.mean(2)], 1)
            return self.out(self.head(self.proj(x)))

    return Net()


def n_params(model):
    return int(sum(p.numel() for p in model.parameters()))


# ---------------------------------------------------------------- display (identical to P4-O)
def to_u8(p):
    return np.clip(p * 255, 0, 255).astype(np.uint8)


def display_png(u8_full, m):
    """u8_full: (T,T) uint8 = clip(p*255) at canvas px; m: mesh-valid (T,T). Returns (png bytes, u8 with 0 outside
    mesh-valid, disp) using the P4-O rule and encoder."""
    import cv2
    from hercules.display import builder
    u8 = u8_full.copy()
    u8[~m] = 0
    disp = cv2.resize(u8, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
    b = builder.png_bytes(disp)
    return b, u8, disp


def jlog(path):
    def log(rec):
        line = json.dumps({**rec, 'log_utc': utc()})
        print(line, flush=True)
        with open(path, 'a') as f:
            f.write(line + '\n')
    return log
