"""Build ds8_y_noveto.npy: the same class rule as the judge but with NO team-model veto on the negatives (control v6c).

blank = not label, 0.3 mm to 5.0 mm from any label, inside the judge mask. text = label inside the judge mask.
Pooled to the 19.2 um grid by the same >0.5 area rule the judge uses.
"""
import sys, os, numpy as np
from scipy.ndimage import distance_transform_edt

F, PITCH = 8, 2.4

for d in sys.argv[1:]:
    X = np.load(os.path.join(d, "ds8_x.npy"), mmap_mode="r"); H8, W8 = X.shape[1], X.shape[2]
    lab = np.load(os.path.join(d, "label.npy"))
    mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
    dout = distance_transform_edt(~lab) * PITCH / 1000.0
    text = lab & mask
    blank = (~lab) & (dout >= 0.3) & (dout <= 5.0) & mask
    def pool(a):
        return a.astype(np.float32)[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
    t, b = pool(text), pool(blank)
    y = np.full((H8, W8), -1, np.int8); y[b > 0.5] = 0; y[t > 0.5] = 1
    np.save(os.path.join(d, "ds8_y_noveto.npy"), y)
    old = np.load(os.path.join(d, "ds8_y.npy"))
    print(f"{d}  text {int((y==1).sum())} blank {int((y==0).sum())}   (with veto: {int((old==1).sum())}/{int((old==0).sum())})", flush=True)
