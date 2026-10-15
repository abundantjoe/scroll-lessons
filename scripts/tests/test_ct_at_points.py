import os, sys, numpy as np, tifffile, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ct_at_points as C

def _world(tmp, cs=128):
    """One 128^3 chunk world (chunk key 0/0/0): a slab of value 120 at z in [60, 70) in an air background of 40."""
    vol = np.full((cs, cs, cs), 40, np.uint8); vol[60:70] = 120
    os.makedirs(os.path.join(tmp, 'cache', '0', '0'), exist_ok=True)
    vol.tofile(os.path.join(tmp, 'cache', '0', '0', '0'))
    return os.path.join(tmp, 'cache')

def _patch(tmp, zfun, name):
    g = np.arange(20, 108, 4, dtype=np.float64)          # 22 x 22 grid, 4-voxel spacing
    yy, xx = np.meshgrid(g, g, indexing='ij')
    zz = zfun(yy, xx)
    d = os.path.join(tmp, name); os.makedirs(d)
    for c, arr in zip('xyz', (xx, yy, zz)): tifffile.imwrite(os.path.join(d, f'{c}.tif'), arr.astype(np.float32))
    return d

def test_planar_trace_on_the_slab_passes():
    with tempfile.TemporaryDirectory() as tmp:
        cache = _world(tmp); p = _patch(tmp, lambda y, x: np.full_like(y, 64.5), 'on')
        r = C.run(p, coord_div=1, half=8, every=1, cache=cache)
        assert r['verdict'] == 'PASS', r
        assert r['crest_ratio'] >= 2.5 and abs(r['crest_offset']) <= 2, r

def test_oblique_cross_cutting_trace_is_void():
    with tempfile.TemporaryDirectory() as tmp:
        cache = _world(tmp); p = _patch(tmp, lambda y, x: 20 + (x - 20) * (88 / 88), 'cut')   # z from 20 to 108 across x
        r = C.run(p, coord_div=1, half=8, every=1, cache=cache)
        assert r['verdict'] == 'VOID-CT', r
        assert r['crest_ratio'] < 1.15, r

def test_coord_div_scales_coordinates():
    with tempfile.TemporaryDirectory() as tmp:
        cache = _world(tmp); p = _patch(tmp, lambda y, x: np.full_like(y, 129.0), 'div')    # 129/2 = 64.5 at coord_div 2
        r2 = C.run(p, coord_div=2, half=8, every=1, cache=cache)
        assert r2['verdict'] == 'PASS', r2
