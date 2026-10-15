"""Reassemble overlapping tiles of one flat grid into one image (feathered overlaps).
tiles.json: {"grid": [H_cells, W_cells], "px_per_cell": 20, "tiles": [{"file": ..., "y0": cells, "x0": cells}, ...]}"""
import sys, json, os, numpy as np, cv2

def stitch(meta, root="", feather=160):
    H, W = meta["grid"]; px = meta.get("px_per_cell", 20); acc = np.zeros((H * px, W * px), np.float32); wt = np.zeros_like(acc); n = 0
    for t in meta["tiles"]:
        f = os.path.join(root, t["file"]);
        if not os.path.exists(f): continue
        im = cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32); h, w = im.shape; y0, x0 = t["y0"] * px, t["x0"] * px
        h = min(h, acc.shape[0] - y0); w = min(w, acc.shape[1] - x0); im = im[:h, :w]
        ry = np.minimum(np.arange(h) + 1, np.arange(h)[::-1] + 1); rx = np.minimum(np.arange(w) + 1, np.arange(w)[::-1] + 1)
        f2 = np.minimum.outer(np.minimum(ry, feather), np.minimum(rx, feather)).astype(np.float32)
        acc[y0:y0 + h, x0:x0 + w] += im * f2; wt[y0:y0 + h, x0:x0 + w] += f2; n += 1
    img = np.where(wt > 0, acc / np.maximum(wt, 1e-6), 0).astype(np.uint8); return img, n

if __name__ == "__main__":
    meta = json.load(open(sys.argv[1])); img, n = stitch(meta, os.path.dirname(sys.argv[1])); cv2.imwrite(sys.argv[2], img); print(n, "tiles ->", sys.argv[2], img.shape)
