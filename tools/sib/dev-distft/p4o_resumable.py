# Provenance: Project HERCULES | owner the owner | [id removed]
"""Within-tile resume for the UNCHANGED P4-O builder (container reclaims kill multi-hour tiles).
Patches infer_1667.card_tiling with a copy that is statement-for-statement the card's loop, plus: every EVERY windows
the running sums (mask_pred, mask_count float32), the window counter and the loop position are saved atomically to
/work/p4o_ckpt/<key>.npz; on start, a matching save is restored and the loop skips the windows already added. The
windows are visited in the same order and added to the same float32 arrays, so a resumed tile is bitwise identical
to an uninterrupted one (tested: tests/test_p4o_resumable.py). key = sha256(H, W, fmask bytes, precision tag,
P4O_WORK). The save is deleted when the tile's loop finishes.
Usage (fp32): p4o_resumable.py <p4o_tiles.py arguments>; bf16: p4o_bf16.py imports this module first."""
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import infer_1667 as I  # noqa: E402

EVERY = int(os.environ.get("P4O_CKPT_EVERY", "200"))
CKDIR = os.environ.get("P4O_CKPT_DIR", "/work/p4o_ckpt")
TAG = {"tag": "fp32"}
_orig = I.card_tiling


def resumable_card_tiling(model, H, W, fmask, tile_fn, norm_fn, progress=None):
    import torch
    import torch.nn.functional as F
    WINDOW, STRIDE = I.WINDOW, I.STRIDE
    key = hashlib.sha256(f"{H},{W},{TAG['tag']},{os.environ.get('P4O_WORK', '')}".encode()
                         + np.ascontiguousarray(fmask).tobytes()).hexdigest()[:24]
    os.makedirs(CKDIR, exist_ok=True)
    ck = os.path.join(CKDIR, key + ".npz")
    mask_pred = np.zeros((H, W), dtype=np.float32)
    mask_count = np.zeros((H, W), dtype=np.float32)
    n, pos0 = 0, 0
    if os.path.exists(ck):
        with np.load(ck) as z:
            mask_pred, mask_count = z["mask_pred"].copy(), z["mask_count"].copy()
            n, pos0 = int(z["n"]), int(z["pos"])
        print(f'{{"resume_within_tile": "{key}", "windows_done": {n}, "pos": {pos0}}}', flush=True)
    pos = 0
    with torch.no_grad():
        for y in range(0, H - WINDOW + 1, STRIDE):
            for x in range(0, W - WINDOW + 1, STRIDE):
                pos += 1
                if pos <= pos0:
                    continue
                if np.any(fmask[y:y + WINDOW, x:x + WINDOW] == 0):
                    continue
                tile = tile_fn(y, x)                                # (256,256,62)
                t = torch.from_numpy(tile).permute(2, 0, 1)         # (62,256,256)
                t = norm_fn(t.unsqueeze(0).unsqueeze(0).float())    # (1,1,62,256,256)
                logits = model(t).logits                            # (1,1,64,64)
                prob = torch.sigmoid(logits)
                prob = F.interpolate(prob, scale_factor=4,
                                     mode="bilinear").squeeze().cpu().numpy()
                mask_pred[y:y + WINDOW, x:x + WINDOW] += prob
                mask_count[y:y + WINDOW, x:x + WINDOW] += 1.0
                n += 1
                if progress:
                    progress(n)
                if n % EVERY == 0:
                    tmp = ck + ".tmp.npz"
                    np.savez(tmp, mask_pred=mask_pred, mask_count=mask_count, n=n, pos=pos)
                    os.replace(tmp, ck)
    pred = np.divide(mask_pred, mask_count,
                     out=np.zeros_like(mask_pred),
                     where=mask_count != 0)
    if os.path.exists(ck):
        os.remove(ck)
    return pred, mask_count


I.card_tiling = resumable_card_tiling

if __name__ == "__main__":
    import p4o_tiles as P
    assert P.I is I
    print('{"precision": "fp32", "within_tile_resume": true}', flush=True)
    P.main()
