"""Rebuild ds8_y (19.2 um class map) from the full-resolution class masks, without the raw depth stacks."""
import sys, os, numpy as np
F = 8
for d in sys.argv[1:]:
    X = np.load(os.path.join(d, "ds8_x.npy"), mmap_mode="r"); H8, W8 = X.shape[1], X.shape[2]
    t = np.load(os.path.join(d, "cls_text.npy")).astype(np.float32)[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
    b = np.load(os.path.join(d, "cls_blank.npy")).astype(np.float32)[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
    y = np.full((H8, W8), -1, np.int8); y[b > 0.5] = 0; y[t > 0.5] = 1
    np.save(os.path.join(d, "ds8_y.npy"), y); print(d, "text", int((y == 1).sum()), "blank", int((y == 0).sum()), flush=True)
