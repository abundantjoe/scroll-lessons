#!/usr/bin/env python
"""R-CREST-CT: crest pre-check of a tifxyz trace directly in the CT, before any render.

At every `every`-th valid grid cell the CT (one pyramid level of the volume, fetched chunk-wise into a local cache) is
sampled at the trace point and at +-half voxels along the local surface normal (cross product of the grid edge
vectors). The mean profile over the cells gives the crest ratio = max over the central half of the offsets divided by
the mean of the three outermost offsets on each side; the crest must lie within the central half. This is the render
crest check of read_chart.crest_check transposed onto the CT so that a cross-cutting trace is recognised without a
render. Nothing is written to the trace; the maps are never involved.

Usage: ct_at_points.py PATCH_DIR --volume-url URL --level L --coord-div F [--half N] [--every K] [--cache DIR] [--out JSON]
  coord-div: tifxyz coordinate units per voxel of the chosen level (e.g. 4 for a level-0 trace read at level 2,
             2 for a level-2 trace read at level 3).
  half:      profile half-width in voxels of that level; use ~300 um / voxel size so runs at different pitches compare.
"""
import argparse, json, os, sys, urllib.request, concurrent.futures as cf
import numpy as np
import tifffile

MIN_CREST = 1.20   # same bar as R-CREST on the render
MAX_CREST_OFFSET = 4   # voxels: the crest must lie inside the half-depth of the render window that follows (62 layers at 2.403 um = +-75 um = +-3.9 voxels at level 3; 28 slices at 9.36 um = +-131 um = +-3.5 voxels at level 2)


def otsu(vals):
    h = np.bincount(vals.astype(int), minlength=256).astype(float)
    w = np.cumsum(h); m = np.cumsum(h * np.arange(256)); tot = w[-1]; mt = m[-1]
    with np.errstate(all='ignore'):
        var = (mt * w - m * tot) ** 2 / (w * (tot - w) * tot * tot)
    if not np.isfinite(var).any():          # a single grey level: everything non-zero counts as above threshold
        return int(vals.min()) - 1
    return int(np.nanargmax(var))


def load_chunk(cache, key, cs):
    f = os.path.join(cache, *map(str, key))
    if os.path.exists(f) and os.path.getsize(f) == cs ** 3:
        return np.fromfile(f, dtype=np.uint8).reshape(cs, cs, cs)
    return None   # missing = all-zero chunk (the bucket omits them) or outside the volume


def fetch_chunks(cache, url, level, keys, cs, threads=16):
    """Fetch the raw uint8 chunks `keys` (z,y,x chunk indices) of `url/level/` that are not yet in the cache.
    A 404 leaves a zero-length marker so it is not refetched."""
    todo = [k for k in keys if not os.path.exists(os.path.join(cache, *map(str, k)))]
    def one(k):
        f = os.path.join(cache, *map(str, k)); os.makedirs(os.path.dirname(f), exist_ok=True)
        try:
            with urllib.request.urlopen(f"{url}/{level}/{k[0]}/{k[1]}/{k[2]}", timeout=120) as r:
                data = r.read()
            if len(data) != cs ** 3: data = b''
        except urllib.error.HTTPError as e:
            if e.code != 404: raise
            data = b''
        with open(f + '.part', 'wb') as fh: fh.write(data)
        os.replace(f + '.part', f)
    if todo:
        with cf.ThreadPoolExecutor(threads) as ex:
            list(ex.map(one, todo))
    return len(todo)


def run(patch_dir, coord_div, half=8, every=3, cache=None, volume_url=None, level=None, cs=128, max_offset=MAX_CREST_OFFSET):
    x, y, z = [tifffile.imread(os.path.join(patch_dir, f'{c}.tif')).astype(np.float64) for c in 'xyz']
    valid = (x > -1) & (y > -1) & (z > -1)
    pts = np.stack([x, y, z], -1) / float(coord_div)
    du = pts[1:, :-1] - pts[:-1, :-1]; dv = pts[:-1, 1:] - pts[:-1, :-1]
    n = np.cross(du, dv); n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    cv = valid[1:, :-1] & valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, 1:]
    ii, jj = np.nonzero(cv); ii, jj = ii[::every], jj[::every]
    offs = np.arange(-half, half + 1)
    # all sample positions (cells, offsets, xyz) -> rounded voxel indices
    pos = pts[ii, jj][:, None, :] + offs[None, :, None] * n[ii, jj][:, None, :]
    idx = np.rint(pos).astype(np.int64)                     # (C, O, 3) as x,y,z
    inside = (idx >= 0).all(-1)
    keys = set(map(tuple, np.unique(np.stack([idx[..., 2] // cs, idx[..., 1] // cs, idx[..., 0] // cs], -1)[inside], axis=0)))
    fetched = 0
    if volume_url is not None:
        fetched = fetch_chunks(cache, volume_url, level, sorted(keys), cs)
    chunks = {k: load_chunk(cache, k, cs) for k in keys}
    vals = np.full(idx.shape[:2], np.nan)
    for c_i in range(idx.shape[0]):
        for o_i in range(idx.shape[1]):
            if not inside[c_i, o_i]: continue
            px, py, pz = idx[c_i, o_i]
            ch = chunks.get((pz // cs, py // cs, px // cs))
            if ch is not None: vals[c_i, o_i] = ch[pz % cs, py % cs, px % cs]
    prof = np.nanmean(vals, 0)
    q = half // 2                                         # central half of the offsets: [-q, +q]
    centre = prof[half - q: half + q + 1]
    ends = (prof[:3].mean() + prof[-3:].mean()) / 2
    crest_ratio = float(centre.max() / ends) if ends > 0 else (float('inf') if centre.max() > 0 else float('nan'))
    top = np.nonzero(centre >= centre.max() * 0.995)[0]          # plateau-safe: midpoint of the (near-)maximal offsets
    crest_off = int(offs[half - q: half + q + 1][int(round(top.mean()))])
    reg = np.concatenate([c.ravel()[::89] for c in chunks.values() if c is not None]) if any(c is not None for c in chunks.values()) else np.zeros(1, np.uint8)
    regnz = reg[reg > 0]; thr = otsu(regnz) if regnz.size else 0
    cen = vals[:, half]; ok = ~np.isnan(cen)
    pk = np.nanargmax(np.nan_to_num(vals, nan=-1), 1) - half
    verdict = 'PASS' if (crest_ratio >= MIN_CREST and abs(crest_off) <= max_offset) else 'VOID-CT'
    return dict(patch_dir=patch_dir, level=level, coord_div=coord_div, half=half, every=every, n_cells=int(len(ii)),
                n_chunks=len(keys), n_fetched=fetched, chunks_missing=int(sum(c is None for c in chunks.values())),
                profile=[round(float(v), 2) for v in prof], crest_ratio=round(crest_ratio, 4), crest_offset=crest_off,
                min_crest=MIN_CREST, max_crest_offset=max_offset, verdict=verdict,
                point_mean=round(float(np.nanmean(cen)), 2), region_nonzero_mean=round(float(regnz.mean()), 2) if regnz.size else None,
                otsu_thr=thr, frac_points_above_otsu=round(float((cen[ok] > thr).mean()), 4) if ok.any() else None,
                region_frac_above_otsu=round(float((reg > thr).mean()), 4), frac_cell_peak_within_2=round(float((np.abs(pk) <= 2).mean()), 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('patch_dir'); ap.add_argument('--volume-url', help='OME-Zarr root URL (omit to use the cache only)')
    ap.add_argument('--level', type=int, required=True); ap.add_argument('--coord-div', type=float, required=True)
    ap.add_argument('--half', type=int, default=8); ap.add_argument('--every', type=int, default=3)
    ap.add_argument('--cache', help='chunk cache dir (default <patch_dir>/../ct_points_cache/level<L>)')
    ap.add_argument('--out', help='JSON output (default <patch_dir>/ct_points_check.json)')
    ap.add_argument('--crest-max-offset', type=int, default=MAX_CREST_OFFSET, help='largest |crest offset| in voxels that still passes (render half-depth)')
    a = ap.parse_args()
    cache = a.cache or os.path.join(os.path.dirname(os.path.abspath(a.patch_dir.rstrip('/'))), 'ct_points_cache', f'level{a.level}')
    os.makedirs(cache, exist_ok=True)
    r = run(a.patch_dir, a.coord_div, a.half, a.every, cache, a.volume_url, a.level, max_offset=a.crest_max_offset)
    out = a.out or os.path.join(a.patch_dir, 'ct_points_check.json')
    json.dump(r, open(out, 'w'), indent=1)
    print(f"R-CREST-CT {r['verdict']}: crest ratio {r['crest_ratio']:.3f} at offset {r['crest_offset']:+d} (bar >= {MIN_CREST}, |offset| <= {a.crest_max_offset}); "
          f"cells {r['n_cells']}, chunks {r['n_chunks']} ({r['n_fetched']} fetched, {r['chunks_missing']} absent); profile {r['profile']}")
    print(f"  point mean {r['point_mean']} vs region non-zero mean {r['region_nonzero_mean']}; above-Otsu({r['otsu_thr']}) fraction {r['frac_points_above_otsu']} vs region {r['region_frac_above_otsu']}; -> {out}")


if __name__ == '__main__':
    main()
