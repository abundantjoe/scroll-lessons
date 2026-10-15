import os, sys, json, numpy as np, cv2, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ringstrip import unroll, stitch

def _patch(d, R, th0, th1, z0, z1, n=40, px=20):
    th = np.linspace(th0, th1, n); z = np.linspace(z0, z1, n); T, Zg = np.meshgrid(th, z)
    os.makedirs(os.path.join(d, "tifxyz"), exist_ok=True)
    for c, a in zip("xyz", (R * np.cos(T), R * np.sin(T), Zg)): tifffile.imwrite(os.path.join(d, "tifxyz", c + ".tif"), a.astype(np.float32))
    m = np.full((n * px, n * px), 60, np.uint8); m[(n * px) // 2 - 6:(n * px) // 2 + 6, :] = 250   # one bright 'text line' at mid-z
    cv2.imwrite(os.path.join(d, "map.png"), m)

def test_two_adjacent_patches_unroll_into_one_continuous_line(tmp_path):
    R = 500.0; a = str(tmp_path / "a"); b = str(tmp_path / "b")
    _patch(a, R, 0.00, 0.40, 100, 300); _patch(b, R, 0.38, 0.78, 100, 300)      # overlap in azimuth, same z range
    img, meta = unroll.unroll([a, b], 0.0, 0.0, R, "map.png")
    assert len(meta["patches"]) == 2
    rows = np.where((img > 180).sum(1) > 0.5 * img.shape[1])[0]                   # the bright line spans most of the width...
    assert len(rows) >= 1
    row = img[rows[len(rows) // 2]]; assert (row[img.shape[1] // 10: -img.shape[1] // 10] > 180).mean() > 0.9   # ...continuously across the seam

def test_stitch_reproduces_a_gradient_from_overlapping_tiles(tmp_path):
    px = 20; H, W = 6, 10; full = np.tile(np.linspace(10, 240, W * px).astype(np.uint8), (H * px, 1)); tiles = []
    for x0 in (0, 4, 8):
        w = min(4 + 1, W - x0); f = f"t{x0}.png"; cv2.imwrite(str(tmp_path / f), full[:, x0 * px:(x0 + w) * px]); tiles.append({"file": f, "y0": 0, "x0": x0})
    meta = {"grid": [H, W], "px_per_cell": px, "tiles": tiles}; img, n = stitch.stitch(meta, str(tmp_path))
    assert n == 3 and np.abs(img.astype(int) - full.astype(int)).max() <= 2
