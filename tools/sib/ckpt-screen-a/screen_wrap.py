# Provenance: Project HERCULES | owner the owner | [id removed]
"""Official-checkpoint screen wrapper (task ckpt-screen-a; RULES.md DECL-DEVLOOP-SCREEN). Numbers only: maps are
handled as arrays and summarised by hashes and counts; nothing is written for viewing, opened or displayed.

Input: a devloop DEV render (render.zarr, group with array '0', uint8 Z,Y,X, 31 slices at the scroll's 9 um voxel
size, --flip-normals, slice k at normal offset (k - 15) x voxel, vc_render_tifxyz convention (k - (n-1)/2) x step).
Output (devloop map format, evaluate.py load_map): <out>/<wid>.tif (forward) and <out>/<wid>_reverse.tif (reverse),
2-D uint8 TIFF in the render's Y,X frame, plus <out>/wrap.json (commands, seconds, threads, sha256 of every file).

  ink9    official villa `vesuvius.ink_detection.inference.infer <render.zarr> <ckpt> <out.tif> --direction both
          --batch-size 4 --num-workers 1 --no-compile` (the exact command of devloop evaluate.py infer_window). The
          checkpoint's embedded config fixes the model, the 17-slice centre crop (indices 7..23 of 31) and robust_mad
          normalisation. Nothing is resampled.
  hecate  official scrollprize/hecate hecate.py, run unchanged (its sha256 is checked before each run) as
          `hecate.py --checkpoint <ckpt> --input <in.npy> --spacing-um 9.6 --output <out.png> --device cpu
          [--reverse]`. The card requires 9.6 um sampling in all three axes and the script does not resample, so the
          wrapper builds the 16-plane 9.6 um input a native `vc_render_tifxyz -n 16 --slice-step 9.6 um` render
          would hold: plane j at normal offset (j - 7.5) x 9.6 um = render slice 15 + (j - 7.5) x 9.6 / v, in-plane
          pixel (q + 0.5) x 9.6 / v - 0.5 of the render (pixel-centre convention), trilinear (separable linear) from
          the render, rounded to uint8. The 2-D probability PNG (round(255 p)) is mapped back to the render's grid
          with the inverse pixel-centre map (bilinear) and rounded to uint8. Reverse = hecate.py --reverse on the
          same input (it flips the full depth before taking the central 16 planes; the 16 planes are symmetric
          about slice 15, so reverse is the exact depth mirror of forward).
Usage: screen_wrap.py {ink9|hecate} --render R.zarr --ckpt C --out DIR --wid ID [--threads 4]
       screen_wrap.py selftest
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

PY_INK = os.environ.get('CKSA_PY_INK', '/opt/hv-ink/bin/python')
HECATE_PY = os.environ.get('CKSA_HECATE_PY', '/work/ckpt/hecate/hecate.py')
HECATE_PY_SHA256 = 'c232c18a1a86cfb91257a00db13288202bb8ae33732ba26f7291a9b8adb8da59'
HECATE_UM = 9.6
N_RENDER, CENTRE = 31, 15
N_HECATE = 16


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def arr_sha(a):
    a = np.ascontiguousarray(a)
    return hashlib.sha256(str((a.dtype.str, a.shape)).encode() + a.tobytes()).hexdigest()


def env_threads(threads):
    t = str(int(threads))
    env = dict(os.environ, OMP_NUM_THREADS=t, MKL_NUM_THREADS=t, OPENBLAS_NUM_THREADS=t,
               PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    return env


def load_render(path):
    import zarr
    z = zarr.open(path, mode='r')
    a = z['0'] if not hasattr(z, 'shape') else z
    a = np.asarray(a[:])
    assert a.dtype == np.uint8 and a.ndim == 3 and a.shape[0] == N_RENDER, (a.dtype, a.shape)
    return a


def render_voxel_um(path, default):
    """Voxel size recorded by vc_render_tifxyz in the render's attributes, else the registry value passed in."""
    for name in ('.zattrs', 'zarr.json', 'meta.json'):
        p = os.path.join(path, name)
        if os.path.exists(p):
            try:
                j = json.load(open(p))
            except ValueError:
                continue
            s = json.dumps(j)
            for key in ('voxel_size', 'voxelsize', 'voxel_um'):
                if key in s:
                    return default, f'{name} has {key}; registry value used'
    return default, 'registry value'


# separable linear resampling (numpy only; pixel-centre convention; edge samples clamped)
# ---------------------------------------------------------------------------------------------------------------

def _lin_weights(pos, n):
    pos = np.clip(np.asarray(pos, np.float64), 0.0, n - 1.0)
    i0 = np.floor(pos).astype(np.int64)
    i0 = np.minimum(i0, n - 2) if n > 1 else np.zeros_like(i0)
    f = (pos - i0).astype(np.float32)
    return i0, np.minimum(i0 + 1, n - 1), f


def resample_axis(a, pos, axis):
    """Linear interpolation of float32 array a along `axis` at fractional indices pos."""
    i0, i1, f = _lin_weights(pos, a.shape[axis])
    shp = [1] * a.ndim
    shp[axis] = -1
    f = f.reshape(shp)
    return np.take(a, i0, axis=axis) * (1 - f) + np.take(a, i1, axis=axis) * f


def centres(n_out, ratio):
    """Input-pixel coordinate of output pixel centres when output spacing = ratio x input spacing."""
    return (np.arange(n_out) + 0.5) * ratio - 0.5


def to_hecate_grid(render, vox_um):
    """(31, H, W) render at vox_um -> (16, H', W') uint8 at 9.6 um, as a native 9.6 um render would sample it."""
    r = HECATE_UM / vox_um
    z = CENTRE + (np.arange(N_HECATE) - (N_HECATE - 1) / 2.0) * r
    H, W = render.shape[1:]
    Ho, Wo = int(np.floor(H / r)), int(np.floor(W / r))
    a = render.astype(np.float32)
    a = resample_axis(a, z, 0)
    a = resample_axis(a, centres(Ho, r), 1)
    a = resample_axis(a, centres(Wo, r), 2)
    return np.clip(np.rint(a), 0, 255).astype(np.uint8), dict(ratio=r, z_index=[round(float(v), 4) for v in z],
                                                              shape_in=list(render.shape), shape_out=[N_HECATE, Ho, Wo])


def from_hecate_grid(m, H, W, vox_um):
    """2-D uint8 map on the 9.6 um grid -> render grid (H, W): inverse pixel-centre map, bilinear, uint8."""
    r = HECATE_UM / vox_um
    a = m.astype(np.float32)
    a = resample_axis(a, centres(H, 1.0 / r), 0)
    a = resample_axis(a, centres(W, 1.0 / r), 1)
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def read_png(path):
    from PIL import Image
    with Image.open(path) as im:
        a = np.asarray(im)
    assert a.dtype == np.uint8 and a.ndim == 2, (a.dtype, a.shape)
    return a


def write_tif(path, a):
    import tifffile
    tifffile.imwrite(path, a, compression='zlib')


def map_stats(a):
    return dict(shape=list(a.shape), sha256=arr_sha(a), nonzero_frac=round(float((a > 0).mean()), 6),
                mean=round(float(a.mean()), 4), p50=int(np.percentile(a, 50)), p99=int(np.percentile(a, 99)))


# runners
# ---------------------------------------------------------------------------------------------------------------

def run_ink9(render, ckpt, out, wid, threads):
    os.makedirs(out, exist_ok=True)
    fwd, rev = f'{out}/{wid}.tif', f'{out}/{wid}_reverse.tif'
    cmd = [PY_INK, '-m', 'vesuvius.ink_detection.inference.infer', render, ckpt, fwd,
           '--direction', 'both', '--batch-size', '4', '--num-workers', '1', '--no-compile']
    t0, start = time.time(), utc()
    with open(f'{out}/infer.log', 'w') as lf:
        pr = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env_threads(threads), cwd=out)
    rec = dict(kind='ink9', command=' '.join(cmd), threads=int(threads), start_utc=start, end_utc=utc(),
               seconds=round(time.time() - t0, 1), returncode=pr.returncode, ckpt_sha256=sha256(ckpt))
    if pr.returncode == 0:
        import tifffile
        rec['outputs'] = {os.path.basename(p): dict(file_sha256=sha256(p), **map_stats(tifffile.imread(p)))
                          for p in (fwd, rev)}
    return rec


def run_hecate(render, ckpt, out, wid, threads, vox_um):
    os.makedirs(out, exist_ok=True)
    got = sha256(HECATE_PY)
    if got != HECATE_PY_SHA256:
        raise SystemExit(f'hecate.py sha256 {got} != official {HECATE_PY_SHA256}')
    rnd = load_render(render)
    H, W = rnd.shape[1:]
    vox, vox_src = render_voxel_um(render, vox_um)
    t0 = time.time()
    h16, geo = to_hecate_grid(rnd, vox)
    rec = dict(kind='hecate', hecate_py_sha256=got, ckpt_sha256=sha256(ckpt), threads=int(threads),
               render_voxel_um=vox, render_voxel_source=vox_src, resample=geo,
               resample_seconds=round(time.time() - t0, 1), input_sha256=arr_sha(h16), start_utc=utc(), runs={})
    with tempfile.TemporaryDirectory(prefix='cksa-', dir=out) as tmp:
        inp = f'{tmp}/in96.npy'
        np.save(inp, h16)
        del h16
        for order, flag, dst in (('forward', [], f'{out}/{wid}.tif'), ('reverse', ['--reverse'], f'{out}/{wid}_reverse.tif')):
            png = f'{tmp}/{order}.png'
            cmd = [PY_INK, HECATE_PY, '--checkpoint', ckpt, '--input', inp, '--spacing-um', f'{HECATE_UM:g}',
                   '--output', png, '--device', 'cpu', *flag]
            t1 = time.time()
            with open(f'{out}/hecate_{order}.log', 'w') as lf:
                pr = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=dict(env_threads(threads), TMPDIR=tmp),
                                    cwd=tmp)
            r = dict(command=' '.join(cmd), returncode=pr.returncode, seconds=round(time.time() - t1, 1))
            if pr.returncode == 0:
                m96 = read_png(png)
                r['png_sha256'] = sha256(png)
                r['map96'] = map_stats(m96)
                r['hecate_meta'] = json.load(open(png[:-4] + '.json'))
                m = from_hecate_grid(m96, H, W, vox)
                write_tif(dst, m)
                r['output'] = dict(file=os.path.basename(dst), file_sha256=sha256(dst), **map_stats(m))
            rec['runs'][order] = r
    rec['end_utc'] = utc()
    rec['seconds'] = round(time.time() - t0, 1)
    rec['returncode'] = max(r['returncode'] for r in rec['runs'].values())
    return rec


# self-test of the geometry (synthetic arrays only)
# ---------------------------------------------------------------------------------------------------------------

def selftest():
    res = {}
    v = 9.362
    r = HECATE_UM / v
    # 1. an affine field is reproduced exactly by linear resampling at the planned sample positions
    Z, H, W = N_RENDER, 97, 131
    zz, yy, xx = np.meshgrid(np.arange(Z), np.arange(H), np.arange(W), indexing='ij')
    f = (2.0 * zz + 0.5 * yy + 0.25 * xx).astype(np.float32)
    zq = CENTRE + (np.arange(N_HECATE) - 7.5) * r
    yq, xq = centres(int(H / r), r), centres(int(W / r), r)
    got = resample_axis(resample_axis(resample_axis(f, zq, 0), yq, 1), xq, 2)
    want = 2.0 * zq[:, None, None] + 0.5 * yq[None, :, None] + 0.25 * xq[None, None, :]
    inner = (slice(None), slice(1, -1), slice(1, -1))
    res['affine_max_abs_err'] = float(np.abs(got - want)[inner].max())
    # 2. the 16 planes are symmetric about slice 15 and span +-72 um
    res['z_index_first_last'] = [float(zq[0]), float(zq[-1])]
    res['z_symmetric_err'] = float(np.abs(zq + zq[::-1] - 2 * CENTRE).max())
    res['z_offsets_um'] = [round(float((zq[0] - CENTRE) * v), 3), round(float((zq[-1] - CENTRE) * v), 3)]
    # 3. depth mirror: resampling a z-flipped render gives the plane-reversed input (so hecate --reverse on the
    #    input equals the forward pass on the mirrored render)
    rng = np.random.default_rng(20260926)
    rend = rng.integers(0, 256, size=(Z, 64, 80), dtype=np.uint8)
    a, _ = to_hecate_grid(rend, v)
    b, _ = to_hecate_grid(rend[::-1].copy(), v)
    d = np.abs(a[::-1].astype(int) - b.astype(int))
    res['mirror_max_abs_diff_u8'] = int(d.max())  # float rounding at .5 only
    res['mirror_frac_diff'] = float((d > 0).mean())
    # 4. 9.362 -> 9.6 -> 9.362 round trip of a smooth 2-D field: centroid shift and error (px of the render grid)
    H2, W2 = 512, 512
    yy, xx = np.meshgrid(np.arange(H2), np.arange(W2), indexing='ij')
    g = 128 + 100 * np.exp(-(((yy - 250.3) ** 2 + (xx - 260.7) ** 2) / (2 * 20.0 ** 2)))
    g8 = np.clip(np.rint(g), 0, 255).astype(np.uint8)
    down = resample_axis(resample_axis(g8.astype(np.float32), centres(int(H2 / r), r), 0), centres(int(W2 / r), r), 1)
    down8 = np.clip(np.rint(down), 0, 255).astype(np.uint8)
    back = from_hecate_grid(down8, H2, W2, v).astype(np.float64)
    w0, w1 = g8.astype(np.float64) - 128, back - 128
    w0[w0 < 0], w1[w1 < 0] = 0, 0
    cy0, cx0 = (w0 * yy).sum() / w0.sum(), (w0 * xx).sum() / w0.sum()
    cy1, cx1 = (w1 * yy).sum() / w1.sum(), (w1 * xx).sum() / w1.sum()
    res['roundtrip_centroid_shift_px'] = [round(cy1 - cy0, 4), round(cx1 - cx0, 4)]
    core = (slice(8, H2 - 16), slice(8, W2 - 16))
    res['roundtrip_max_abs_err_u8'] = float(np.abs(back - g8)[core].max())
    ok = (res['affine_max_abs_err'] < 1e-3 and res['z_symmetric_err'] < 1e-9 and res['mirror_max_abs_diff_u8'] <= 1
          and res['mirror_frac_diff'] < 1e-3
          and max(abs(x) for x in res['roundtrip_centroid_shift_px']) < 0.05 and res['roundtrip_max_abs_err_u8'] <= 2)
    res['pass'] = bool(ok)
    print(json.dumps(res, indent=1))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=['ink9', 'hecate', 'selftest'])
    ap.add_argument('--render')
    ap.add_argument('--ckpt')
    ap.add_argument('--out')
    ap.add_argument('--wid')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--voxel-um', type=float, default=9.362)
    a = ap.parse_args()
    if a.kind == 'selftest':
        return selftest()
    if a.kind == 'ink9':
        rec = run_ink9(a.render, a.ckpt, a.out, a.wid, a.threads)
    else:
        rec = run_hecate(a.render, a.ckpt, a.out, a.wid, a.threads, a.voxel_um)
    rec.update(wid=a.wid, render=a.render, wrapper_sha256=sha256(os.path.abspath(__file__)))
    with open(f'{a.out}/wrap.json', 'w') as f:
        json.dump(rec, f, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps({k: rec[k] for k in ('kind', 'wid', 'seconds', 'returncode')}))
    return 0 if rec['returncode'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
