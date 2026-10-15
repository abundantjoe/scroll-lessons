# Provenance: Project HERCULES | [id removed]
"""Training data at PHerc0268's scan setting. For each organizer segment that has BOTH an 8.64 um (or 9.36 um) surface
volume and a 2.4 um ink prediction (organizers' 2026 recipe), download the coarse surface volume (level 0, all layers),
downsample the fine prediction to the coarse canvas (INTER_AREA, factor = fine_um / coarse_um ... computed from the two
canvases), and write crops: stacks (D,64,64) uint8 + 2-D soft labels (64,64) uint8 into an npz shard.
usage: build_data.py <scroll> <segment> <coarse_sv_name> <out.npz> [--stride 48] [--max 4000] [--level 0]
Labels are the organizers' predictions, not human marks: they are pseudo-labels; a held-out scroll is used for validation."""
import argparse, io, json, numpy as np, zarr, s3fs, cv2, tifffile

B = 'vesuvius-challenge-open-data'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('scroll'); ap.add_argument('segment'); ap.add_argument('coarse_sv'); ap.add_argument('out')
    ap.add_argument('--stride', type=int, default=48); ap.add_argument('--max', type=int, default=4000); ap.add_argument('--level', type=int, default=0); ap.add_argument('--size', type=int, default=64)
    a = ap.parse_args(); fs = s3fs.S3FileSystem(anon=True); base = f'{B}/{a.scroll}/segments/{a.segment}'
    preds = [p for p in fs.ls(f'{base}/ink-detection') if p.endswith('.tif')]; assert preds, 'no ink prediction'
    pred_path = sorted(preds)[-1]  # newest recipe
    with fs.open(pred_path, 'rb') as f: pred = tifffile.imread(io.BytesIO(f.read()))
    if pred.ndim == 3: pred = pred[0]
    pred = pred.astype(np.float32); pred = pred / (255.0 if pred.max() > 1.5 else 1.0)
    sv = zarr.open(zarr.storage.FSStore(f's3://{base}/surface-volumes/{a.coarse_sv}/{a.level}', fs=fs, mode='r'), mode='r')
    D, H, W = sv.shape; print('coarse sv', sv.shape, 'fine pred', pred.shape)
    lab = cv2.resize(pred, (W, H), interpolation=cv2.INTER_AREA)  # same mesh, same UV canvas: pure rescale
    stack = np.asarray(sv[:]); valid = stack[D // 2] > 0; S = a.size
    cand = [(y, x) for y in range(0, H - S + 1, a.stride) for x in range(0, W - S + 1, a.stride) if valid[y:y + S, x:x + S].mean() >= 0.9]
    rng = np.random.default_rng(0); pos = [c for c in cand if lab[c[0]:c[0] + S, c[1]:c[1] + S].max() > 0.5]; ps = set(pos); neg = [c for c in cand if c not in ps]
    rng.shuffle(pos); rng.shuffle(neg); npos = min(len(pos), a.max // 2); sel = pos[:npos] + neg[:a.max - npos]   # balanced: half the crops contain ink
    X = [stack[:, y:y + S, x:x + S] for y, x in sel]; Y = [lab[y:y + S, x:x + S] for y, x in sel]; M = sel
    print('candidates', len(cand), 'with ink', len(pos), 'selected', len(sel))
    X = np.stack(X).astype(np.uint8); Y = (np.stack(Y) * 255).astype(np.uint8)
    np.savez_compressed(a.out, x=X, y=Y, pos=np.array(M), meta=json.dumps({'scroll': a.scroll, 'segment': a.segment, 'coarse_sv': a.coarse_sv, 'pred': pred_path, 'D': D, 'H': H, 'W': W, 'label_mean': float(Y.mean() / 255)}))
    print('wrote', a.out, X.shape, 'label mean', round(float(Y.mean() / 255), 4), 'frac crops with ink>0.5 anywhere', round(float((Y.max((1, 2)) > 127).mean()), 3))

if __name__ == '__main__': main()
