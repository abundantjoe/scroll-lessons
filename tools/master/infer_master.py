# Provenance: Project HERCULES | [id removed]
"""Sliding-window inference of the Master model over a surface-aligned stack (a render or organizer surface volume,
zarr with layers x H x W) -> 2-D ink probability PNG, 3-D per-voxel probability (optional zarr), and the gold overlay:
the render's centre layer with predicted ink painted gold. usage: infer_master.py <ckpt> <stack.zarr> <out_prefix> [--tile 64 --stride 32 --depth 16 --thr 0.5 --no3d]"""
import argparse, json, numpy as np, torch, zarr, cv2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ssl3d import CNNEncoder3D; from master import Master
torch.set_num_threads(max(1, os.cpu_count() or 4))

def load_model(ckpt):
    ck = torch.load(ckpt); enc = None
    if ck.get('ssl'):
        c2 = torch.load(ck['ssl']); enc = CNNEncoder3D(width=c2['width'], out_dim=c2['out_dim']); enc.load_state_dict(c2['encoder'])
    m = Master(ssl_encoder=enc, base=ck['base'], ssl_dim=(enc.body[-3].num_channels if enc else 192) if False else (torch.load(ck['ssl'])['width'] * 8 if ck.get('ssl') else 192)); m.load_state_dict(ck['model']); m.eval(); return m

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ckpt'); ap.add_argument('stack'); ap.add_argument('out'); ap.add_argument('--tile', type=int, default=64); ap.add_argument('--stride', type=int, default=32)
    ap.add_argument('--depth', type=int, default=16); ap.add_argument('--thr', type=float, default=0.5); ap.add_argument('--no3d', action='store_true'); ap.add_argument('--bs', type=int, default=8)
    a = ap.parse_args(); m = load_model(a.ckpt); g = zarr.open(a.stack, mode='r'); z = g['0'] if isinstance(g, zarr.Group) and '0' in g else g; D, H, W = z.shape
    c = D // 2; d0 = max(0, c - a.depth // 2); stack = np.asarray(z[d0:d0 + a.depth]); valid = stack[a.depth // 2] > 0
    acc = np.zeros((H, W), np.float32); wt = np.zeros((H, W), np.float32); vox = None if a.no3d else np.zeros((a.depth, H, W), np.float32)
    win = np.outer(np.hanning(a.tile), np.hanning(a.tile)).astype(np.float32) + 1e-3; tiles = [(y, x) for y in range(0, H - a.tile + 1, a.stride) for x in range(0, W - a.tile + 1, a.stride) if valid[y:y + a.tile, x:x + a.tile].mean() > 0.5]
    with torch.no_grad():
        for i in range(0, len(tiles), a.bs):
            bt = tiles[i:i + a.bs]; x = torch.from_numpy(np.stack([stack[:, y:y + a.tile, xx:xx + a.tile] for y, xx in bt])).float().unsqueeze(1) / 255.0
            with torch.autocast('cpu', dtype=torch.bfloat16): l2, v3 = m(x, return_3d=True)
            p2 = torch.sigmoid(l2.float()).numpy()[:, 0]; p3 = torch.sigmoid(v3.float()).numpy()[:, 0]
            for k, (y, xx) in enumerate(bt):
                acc[y:y + a.tile, xx:xx + a.tile] += p2[k] * win; wt[y:y + a.tile, xx:xx + a.tile] += win
                if vox is not None: vox[:, y:y + a.tile, xx:xx + a.tile] += p3[k] * win
    prob = np.where(wt > 0, acc / np.maximum(wt, 1e-6), 0); cv2.imwrite(a.out + '_ink.png', (prob * 255).astype(np.uint8))
    centre = stack[a.depth // 2].astype(np.float32); nz = centre[valid]; lo, hi = np.percentile(nz, [1, 99]) if nz.size else (0, 1); gray = np.clip((centre - lo) / max(hi - lo, 1) * 255, 0, 255).astype(np.uint8)
    gold = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR); mask = prob > a.thr; gold[mask] = (0.35 * gold[mask] + 0.65 * np.array([0, 215, 255])).astype(np.uint8)   # BGR gold
    cv2.imwrite(a.out + '_gold.png', gold, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    if vox is not None: zarr.save(a.out + '_ink3d.zarr', (np.where(wt > 0, vox / np.maximum(wt, 1e-6), 0) * 255).astype(np.uint8))
    json.dump({'stack': a.stack, 'shape': [D, H, W], 'tiles': len(tiles), 'frac_ge_thr': float(mask[valid].mean()) if valid.any() else 0, 'mean': float(prob[valid].mean()) if valid.any() else 0}, open(a.out + '_ink.json', 'w'), indent=1)
    print('done', a.out, 'tiles', len(tiles), 'frac>=thr', round(float(mask[valid].mean()), 4))

if __name__ == '__main__': main()
