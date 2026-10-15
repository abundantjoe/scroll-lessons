"""S1-v5 surface-aligned small U-Net. train <train_dir> <out.pt> | predict <dir> <model.pt>"""
import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as Fn
from scipy.stats import rankdata
torch.manual_seed(0); np.random.seed(0)
class Block(nn.Module):
    def __init__(s, i, o): super().__init__(); s.c = nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU())
    def forward(s, x): return s.c(x)
class UNet(nn.Module):
    def __init__(s, cin=23, c=(24, 48, 96)):
        super().__init__(); s.e1 = Block(cin, c[0]); s.e2 = Block(c[0], c[1]); s.e3 = Block(c[1], c[2])
        s.d2 = Block(c[2] + c[1], c[1]); s.d1 = Block(c[1] + c[0], c[0]); s.out = nn.Conv2d(c[0], 1, 1)
    def forward(s, x):
        a = s.e1(x); b = s.e2(Fn.max_pool2d(a, 2)); c = s.e3(Fn.max_pool2d(b, 2))
        c = Fn.interpolate(c, scale_factor=2, mode="bilinear", align_corners=False); b = s.d2(torch.cat([c, b], 1))
        b = Fn.interpolate(b, scale_factor=2, mode="bilinear", align_corners=False); a = s.d1(torch.cat([b, a], 1)); return s.out(a)[:, 0]
YNAME = os.environ.get("V5_Y", "ds8_y.npy")   # control v6c trains on ds8_y_noveto.npy (no team-model veto)
SELECT = os.environ.get("V5_SELECT", "bce")   # v8 selects checkpoints by validation pixel AUC
mode = sys.argv[1]
if mode == "train":
    dirs, out = sys.argv[2].split(","), sys.argv[3]; STEPS = int(sys.argv[4]) if len(sys.argv) > 4 else 4000
    LR = float(os.environ.get("V5_LR", "1e-3")); WD = float(os.environ.get("V5_WD", "0"))   # defaults = the declared v5 recipe
    DS = [(np.load(os.path.join(d, "ds8_x.npy")), np.load(os.path.join(d, YNAME))) for d in dirs]
    X0, Y0 = DS[0]; H0 = Y0.shape[0]; val_rows = np.zeros(H0, bool); val_rows[int(0.85 * H0):] = True   # early-stopping band: bottom 15 % of the FIRST dir only
    net = UNet(); print("params", sum(p.numel() for p in net.parameters()), "dirs", len(dirs), "steps", STEPS); opt = torch.optim.Adam(net.parameters(), LR, weight_decay=WD); print("lr", LR, "wd", WD)
    P = 128; B = 16; t0 = time.time(); best = (1e9, None); hist = []; hist_val = []
    T = [(torch.from_numpy(X), torch.from_numpy(Y.astype(np.float32))) for X, Y in DS]
    def batch():
        xs, ys = [], []
        while len(xs) < B:
            j = np.random.randint(len(T)); Xt, Yt = T[j]; H, W = Yt.shape
            y0 = np.random.randint(0, H - P); x0 = np.random.randint(0, W - P)
            if j == 0 and val_rows[y0:y0 + P].any(): continue
            x = Xt[:, y0:y0 + P, x0:x0 + P]; y = Yt[y0:y0 + P, x0:x0 + P]
            if (y >= 0).float().mean() < 0.05: continue
            k = np.random.randint(4); x = torch.rot90(x, k, (1, 2)); y = torch.rot90(y, k, (0, 1))
            if np.random.rand() < 0.5: x = torch.flip(x, (2,)); y = torch.flip(y, (1,))
            xs.append(x); ys.append(y)
        return torch.stack(xs), torch.stack(ys)
    def loss_fn(logit, y):
        w = (y >= 0).float(); return (Fn.binary_cross_entropy_with_logits(logit, y.clamp(min=0), reduction="none") * w).sum() / w.sum().clamp(min=1)
    VAL_DIR = os.environ.get("V5_VAL_DIR")
    if VAL_DIR:   # v6: validate on a whole separate crop; no row band is excluded from training
        val_rows[:] = False; Xv = torch.from_numpy(np.load(os.path.join(VAL_DIR, "ds8_x.npy"))); Yv = torch.from_numpy(np.load(os.path.join(VAL_DIR, YNAME)).astype(np.float32))
        Hv, W0 = Yv.shape[0] // 4 * 4, Yv.shape[1] // 4 * 4; xv = Xv[None][:, :, :Hv, :W0]; yv = Yv[None][:, :Hv, :W0]; print("validation crop", VAL_DIR)
    else:
        Xv, Yv = T[0]; W0 = Yv.shape[1] // 4 * 4; Hv = int(val_rows.sum()) // 4 * 4; xv = Xv[:, val_rows][None][:, :, :Hv, :W0]; yv = Yv[val_rows][None][:, :Hv, :W0]
    for step in range(STEPS + 1):
        net.train(); x, y = batch(); opt.zero_grad(); l = loss_fn(net(x), y); l.backward(); opt.step(); hist.append(float(l))
        if step % 250 == 0:
            net.eval()
            with torch.no_grad(): logit = net(xv); lv = float(loss_fn(logit, yv))
            av = None
            if SELECT == "auc":                      # v8: select on the metric the bars use, not on BCE
                sc = logit.detach().numpy().ravel(); yy = yv.numpy().ravel()
                sel = yy >= 0; sc, yy = sc[sel], yy[sel]
                n1 = int((yy > 0).sum()); n0 = len(yy) - n1
                if n1 and n0:
                    rk = rankdata(sc); av = float((rk[yy > 0].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
            hist_val.append([step, float(np.mean(hist[-250:])), lv, av])
            print(f"step {step} train {np.mean(hist[-250:]):.4f} val {lv:.4f} auc {av if av is None else round(av,4)} {time.time()-t0:.0f}s", flush=True)
            crit = (-av if av is not None else lv) if SELECT == "auc" else lv
            if crit < best[0]: best = (crit, {k: v.clone() for k, v in net.state_dict().items()}); torch.save(best[1], out)
    json.dump({"select": SELECT, "best_criterion": best[0], "steps": STEPS, "dirs": dirs, "lr": LR, "wd": WD, "val_curve": hist_val}, open(out + ".json", "w"))
else:
    d, mp = sys.argv[2], sys.argv[3]; TAG = sys.argv[4] if len(sys.argv) > 4 else "v5"; X = np.load(os.path.join(d, "ds8_x.npy")); net = UNet(); net.load_state_dict(torch.load(mp)); net.eval()
    H, W = X.shape[1:]; H4, W4 = H // 4 * 4, W // 4 * 4
    with torch.no_grad(): p = torch.sigmoid(net(torch.from_numpy(X[:, :H4, :W4])[None]))[0].numpy()
    full = np.zeros((H, W), np.float32); full[:H4, :W4] = p
    m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
    up = torch.nn.functional.interpolate(torch.from_numpy(full)[None, None], scale_factor=8, mode="bilinear", align_corners=False)[0, 0].numpy()
    s = np.zeros(m.shape, np.float32); h, w = min(up.shape[0], m.shape[0]), min(up.shape[1], m.shape[1]); s[:h, :w] = up[:h, :w]; s = np.where(m, s, 0).astype(np.float16)
    np.save(os.path.join(d, f"s_bot_{TAG}.npy"), s); np.save(os.path.join(d, f"s_top_{TAG}.npy"), s); np.save(os.path.join(d, f"s_bot_{TAG}_u8.npy"), (255 * s.astype(np.float32)).astype(np.uint8)); print(d, TAG, "written")
