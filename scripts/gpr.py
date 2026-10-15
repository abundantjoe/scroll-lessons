"""Baseline GP-R (RULES.md): a Grand-Prize-style ink detector - 3D encoder over the depth axis feeding a 2D decoder,
patch training with dihedral and intensity augmentation, BCE + soft Dice, dihedral TTA at inference.

  train   <dirs,comma-separated> <out.pt> [steps]
  predict <crop_dir> <model.pt> <tag>

Scale is set by the pooled stack it is given: ds8_x.npy (19.2 um) for GP-R1, ds4_x.npy (9.6 um) for GP-R2.
Environment: GPR_X (stack name), GPR_Y (label name), GPR_VAL_DIR (validation crop), GPR_LR, GPR_WD, GPR_PATCH, GPR_BATCH.
"""
import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as Fn
from scipy.stats import rankdata

torch.manual_seed(0); np.random.seed(0)
XNAME = os.environ.get("GPR_X", "ds8_x.npy")
YNAME = os.environ.get("GPR_Y", "ds8_y_noveto.npy")
PATCH = int(os.environ.get("GPR_PATCH", "128"))
BATCH = int(os.environ.get("GPR_BATCH", "8"))


class Enc3D(nn.Module):
    """3D convolutions over the depth axis, collapsing depth to a 2D feature map (the '3D-to-2D' pattern)."""
    def __init__(s, cout=32):
        super().__init__()
        # Scaled for CPU (RULES.md GP-R): the 3D-over-depth structure is kept, the widths are small and the first
        # convolution strides the depth axis, which keeps lateral resolution intact where the ink signal lives.
        s.b1 = nn.Sequential(nn.Conv3d(1, 8, 3, stride=(2, 1, 1), padding=1), nn.BatchNorm3d(8), nn.ReLU(),
                             nn.Conv3d(8, 8, 3, padding=1), nn.BatchNorm3d(8), nn.ReLU())
        s.b2 = nn.Sequential(nn.Conv3d(8, 16, 3, stride=(2, 1, 1), padding=1), nn.BatchNorm3d(16), nn.ReLU(),
                             nn.Conv3d(16, 16, 3, padding=1), nn.BatchNorm3d(16), nn.ReLU())
        s.b3 = nn.Sequential(nn.Conv3d(16, cout, 3, stride=(2, 1, 1), padding=1), nn.BatchNorm3d(cout), nn.ReLU())

    def forward(s, x):                                   # x: (B, 1, D, H, W)
        x = s.b1(x); x = s.b2(x); x = s.b3(x)
        return x.mean(dim=2)                             # collapse the remaining depth -> (B, C, H, W)


class Block(nn.Module):
    def __init__(s, i, o):
        super().__init__(); s.c = nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                                                nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU())
    def forward(s, x): return s.c(x)


class GPR(nn.Module):
    def __init__(s, c=(32, 64, 128)):
        super().__init__()
        s.enc3d = Enc3D(c[0])
        s.e2 = Block(c[0], c[1]); s.e3 = Block(c[1], c[2])
        s.d2 = Block(c[2] + c[1], c[1]); s.d1 = Block(c[1] + c[0], c[0]); s.out = nn.Conv2d(c[0], 1, 1)

    def forward(s, x):                                   # x: (B, D, H, W) - depth is a real axis, not channels
        a = s.enc3d(x[:, None])
        b = s.e2(Fn.max_pool2d(a, 2)); c = s.e3(Fn.max_pool2d(b, 2))
        c = Fn.interpolate(c, scale_factor=2, mode="bilinear", align_corners=False); b = s.d2(torch.cat([c, b], 1))
        b = Fn.interpolate(b, scale_factor=2, mode="bilinear", align_corners=False); a = s.d1(torch.cat([b, a], 1))
        return s.out(a)[:, 0]


def losses(logit, y):
    """BCE + soft Dice over the labelled pixels, as the winning solutions used."""
    w = (y >= 0).float(); yy = y.clamp(min=0)
    bce = (Fn.binary_cross_entropy_with_logits(logit, yy, reduction="none") * w).sum() / w.sum().clamp(min=1)
    p = torch.sigmoid(logit) * w
    inter = (p * yy * w).sum(); dice = 1 - (2 * inter + 1.0) / ((p * p).sum() + (yy * w).sum() + 1.0)
    return bce + dice


def dihedral(x, k):
    """k in 0..7: the eight symmetries of the square, applied to the trailing two axes."""
    if k >= 4: x = torch.flip(x, dims=[-1])
    return torch.rot90(x, k % 4, dims=[-2, -1])


def dihedral_inv(x, k):
    x = torch.rot90(x, -(k % 4), dims=[-2, -1])
    return torch.flip(x, dims=[-1]) if k >= 4 else x


def auc_of(score, y):
    sel = y >= 0; s, yy = score[sel], y[sel]
    n1 = int((yy > 0.5).sum()); n0 = len(yy) - n1
    if not n1 or not n0: return None
    rk = rankdata(s)
    return float((rk[yy > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "train":
        dirs, out = sys.argv[2].split(","), sys.argv[3]
        STEPS = int(sys.argv[4]) if len(sys.argv) > 4 else 12000
        LR = float(os.environ.get("GPR_LR", "3e-4")); WD = float(os.environ.get("GPR_WD", "1e-4"))
        DS = []
        for d in dirs:
            X = np.load(os.path.join(d, XNAME)).astype(np.float32)
            Y = np.load(os.path.join(d, YNAME)).astype(np.float32)
            DS.append((X[:-1], X[-1], Y))                # depth channels, coverage, labels
        print(f"GP-R train: {len(DS)} crops, stack {XNAME} depth {DS[0][0].shape[0]}, patch {PATCH}, batch {BATCH}", flush=True)
        net = GPR(); opt = torch.optim.Adam(net.parameters(), lr=LR, weight_decay=WD)
        print("parameters", sum(p.numel() for p in net.parameters()), flush=True)
        rng = np.random.default_rng(0)

        def batch():
            xs, ys = [], []
            while len(xs) < BATCH:
                Xc, mc, Yc = DS[rng.integers(len(DS))]
                H, W = Yc.shape
                if H <= PATCH or W <= PATCH: continue
                y0 = int(rng.integers(0, H - PATCH)); x0 = int(rng.integers(0, W - PATCH))
                yp = Yc[y0:y0 + PATCH, x0:x0 + PATCH]
                if (yp >= 0).mean() < 0.25: continue      # skip patches that are almost entirely unlabelled
                xp = Xc[:, y0:y0 + PATCH, x0:x0 + PATCH].copy()
                xp = xp * float(rng.uniform(0.9, 1.1)) + float(rng.normal(0, 0.05))   # intensity augmentation
                if rng.random() < 0.3:                                                 # cutout
                    ch, cw = int(PATCH * 0.25), int(PATCH * 0.25)
                    cy, cx = int(rng.integers(0, PATCH - ch)), int(rng.integers(0, PATCH - cw))
                    xp[:, cy:cy + ch, cx:cx + cw] = 0.0
                xt = torch.from_numpy(xp); yt = torch.from_numpy(yp.copy())
                k = int(rng.integers(0, 8))                                            # dihedral augmentation
                xs.append(dihedral(xt, k)); ys.append(dihedral(yt, k))
            return torch.stack(xs), torch.stack(ys)

        VAL = os.environ.get("GPR_VAL_DIR")
        Xv = np.load(os.path.join(VAL, XNAME)).astype(np.float32); Yv = np.load(os.path.join(VAL, YNAME)).astype(np.float32)
        Hv, Wv = Yv.shape[0] // 4 * 4, Yv.shape[1] // 4 * 4
        xv = torch.from_numpy(Xv[:-1, :Hv, :Wv])[None]; yv_np = Yv[:Hv, :Wv]
        print("validation crop", VAL, flush=True)

        best = (-1e9, None); hist, curve = [], []; t0 = time.time()
        for step in range(STEPS + 1):
            net.train(); x, y = batch(); opt.zero_grad()
            l = losses(net(x), y); l.backward(); opt.step(); hist.append(float(l))
            if step % 250 == 0:
                net.eval()
                with torch.no_grad(): sv = net(xv)[0].numpy()
                a = auc_of(sv.ravel(), yv_np.ravel())
                curve.append([step, float(np.mean(hist[-250:])), a])
                print(f"step {step} train {np.mean(hist[-250:]):.4f} val_auc {a:.4f} {time.time()-t0:.0f}s", flush=True)
                if a is not None and a > best[0]:
                    best = (a, {k: v.clone() for k, v in net.state_dict().items()}); torch.save(best[1], out)
        json.dump({"best_val_auc": best[0], "steps": STEPS, "dirs": dirs, "stack": XNAME, "labels": YNAME,
                   "patch": PATCH, "batch": BATCH, "lr": LR, "wd": WD, "curve": curve}, open(out + ".json", "w"), indent=1)
        print("GPR_TRAIN_DONE best_val_auc", round(best[0], 4))
    else:
        d, mp, tag = sys.argv[2], sys.argv[3], sys.argv[4]
        X = np.load(os.path.join(d, XNAME)).astype(np.float32)
        net = GPR(); net.load_state_dict(torch.load(mp)); net.eval()
        H, W = X.shape[1:]; H4, W4 = H // 4 * 4, W // 4 * 4
        x = torch.from_numpy(X[:-1, :H4, :W4])[None]
        acc = np.zeros((H4, W4), np.float32)
        with torch.no_grad():
            for k in range(8):                                    # dihedral TTA
                acc += dihedral_inv(net(dihedral(x, k)), k)[0].numpy()
        sc = acc / 8.0
        m = X[-1, :H4, :W4] > 0.5
        v = sc[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6
        z = np.where(m, (sc - med) / mad, 0).astype(np.float32)
        F = int(round(6250 / H))                                   # 8 for ds8, 4 for ds4
        up = np.repeat(np.repeat(z, F, axis=0), F, axis=1)
        mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
        full = np.zeros(mask.shape, np.float32)
        h, w = min(up.shape[0], mask.shape[0]), min(up.shape[1], mask.shape[1])
        full[:h, :w] = up[:h, :w]
        np.save(os.path.join(d, f"s_bot_{tag}.npy"), np.where(mask, full, 0).astype(np.float16))
        print(d, tag, "written (8-fold TTA)")
