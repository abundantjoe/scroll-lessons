"""Register a 7.91 um GP ink label to the 2.4 um team ink overview (ds8): scale search + FFT offset search, correlation restricted to the labelled zone."""
import sys, json, numpy as np
from PIL import Image
from scipy.ndimage import zoom, gaussian_filter, binary_dilation
from numpy.fft import fft2, ifft2
Image.MAX_IMAGE_PIXELS = None
lab_p, ink_p, out, ovl = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
lab = np.asarray(Image.open(lab_p).convert("L")).astype(np.float32) / 255.0
ink = np.asarray(Image.open(ink_p).convert("L")).astype(np.float32) / 255.0
G = 32.0  # common grid um/px
L0 = zoom(lab, 7.91 / G, order=1); I = gaussian_filter(zoom(ink, 19.2 / G, order=1), 1.0)
best = None
S0, S1v = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (0.96, 1.06)
for s in np.arange(S0, S1v, 0.0025):
    L = gaussian_filter(zoom(L0, s, order=1), 1.0)
    zone = binary_dilation(L > 0.2, iterations=int(3000 / G))
    H, W = I.shape[0] + L.shape[0], I.shape[1] + L.shape[1]
    Lm = np.where(zone, L - L[zone].mean(), 0); Z = zone.astype(np.float32)
    FI = fft2(I, (H, W)); FL = fft2(Lm, (H, W)); FZ = fft2(Z, (H, W)); FI2 = fft2(I * I, (H, W))
    num = np.real(ifft2(FI * np.conj(FL)))           # sum over zone of I(x+d) * Lm(x)
    sI = np.real(ifft2(FI * np.conj(FZ))); sI2 = np.real(ifft2(FI2 * np.conj(FZ))); n = Z.sum()
    varI = np.maximum(sI2 - sI * sI / n, 1e-6); c = num / np.sqrt(varI * (Lm * Lm).sum())
    c = c[:I.shape[0], :I.shape[1]]; c[:5, :] = -1; c[:, :5] = -1
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    if best is None or c[iy, ix] > best[0]: best = (float(c[iy, ix]), float(s), int(iy), int(ix))
    print("scale %.4f corr %.3f at dy %d dx %d" % (s, c[iy, ix], iy, ix), flush=True)
c, s, dy, dx = best
dy = dy if dy < I.shape[0] // 2 else dy - I.shape[0]; dx = dx if dx < I.shape[1] // 2 else dx - I.shape[1]
scale_total = 7.91 / 2.4 * s; off_y = dy * G / 2.4; off_x = dx * G / 2.4
json.dump({"corr_zone": c, "scale_label_to_canvas": scale_total, "offset_canvas_y": off_y, "offset_canvas_x": off_x, "residual_scale": s, "grid_um": G}, open(out, "w"), indent=1)
print("BEST corr %.3f: canvas = label*%.4f + (%.1f, %.1f)" % (c, scale_total, off_y, off_x))
# overlay for visual check: ink overview (grey) with label edges (red) at the found transform, ds to 64 um
L = zoom(L0, s, order=1); can = np.zeros_like(I); y0, x0 = max(dy, 0), max(dx, 0)
h = min(L.shape[0] - max(-dy, 0), I.shape[0] - y0); w = min(L.shape[1] - max(-dx, 0), I.shape[1] - x0)
can[y0:y0 + h, x0:x0 + w] = L[max(-dy, 0):max(-dy, 0) + h, max(-dx, 0):max(-dx, 0) + w]
edge = (can > 0.5) & ~binary_dilation(~(can > 0.5), iterations=1) if False else (can > 0.5) ^ binary_dilation(can > 0.5, iterations=1)
rgb = np.stack([I, I, I], -1); rgb[edge] = [1, 0, 0]
Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(ovl)
