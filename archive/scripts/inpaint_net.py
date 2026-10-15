#!/usr/bin/env python3
"""5.4 second model: self-supervised inpainting U-Net (< 1 M params) trained on face-intensity maps S of the
TARGET scroll's own renders (no labels, no ink prior). a = |S - S_hat| with S_hat the inpainting of a 24x24
hole centred on each pixel (4-phase hole grid so every pixel is inside exactly one hole).
Architecture / schedule are FIXED (METHOD.md). Standardisation: (S - median)/MAD over on-sheet pixels.
usage: inpaint_net.py train <out.pt> <derived_dir> [<derived_dir> ...]
       inpaint_net.py predict <model.pt> <derived_dir> [--faces top,bot]"""
import sys, os, json, time, argparse, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
torch.set_num_threads(max(1, os.cpu_count() - 1))
CFG = dict(crop=64, hole=24, batch=64, steps=6000, lr=1e-3, chans=(16, 32, 64), seed=0)

class Block(nn.Module):
    def __init__(s, i, o): super().__init__(); s.c = nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.ReLU(), nn.Conv2d(o, o, 3, padding=1), nn.ReLU())
    def forward(s, x): return s.c(x)
class UNet(nn.Module):
    def __init__(s, ch=CFG["chans"]):
        super().__init__(); c1, c2, c3 = ch
        s.e1 = Block(2, c1); s.e2 = Block(c1, c2); s.e3 = Block(c2, c3)
        s.u2 = nn.ConvTranspose2d(c3, c2, 2, stride=2); s.d2 = Block(2 * c2, c2)
        s.u1 = nn.ConvTranspose2d(c2, c1, 2, stride=2); s.d1 = Block(2 * c1, c1); s.o = nn.Conv2d(c1, 1, 1)
    def forward(s, x):
        e1 = s.e1(x); e2 = s.e2(F.max_pool2d(e1, 2)); e3 = s.e3(F.max_pool2d(e2, 2))
        d2 = s.d2(torch.cat([s.u2(e3), e2], 1)); d1 = s.d1(torch.cat([s.u1(d2), e1], 1)); return s.o(d1)

def standardise(S, m):
    v = S[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826
    return ((S - med) / max(mad, 1e-6)).astype(np.float32)

def load_face(d, face):
    S = np.load(os.path.join(d, f"S_{face}.npy")).astype(np.float32); m = np.load(os.path.join(d, "onsheet.npy")) if os.path.exists(os.path.join(d, "onsheet.npy")) else np.load(os.path.join(d, "valid.npy")) > 0
    return standardise(S, m), m

def train(out, dirs):
    rng = np.random.default_rng(CFG["seed"]); torch.manual_seed(CFG["seed"])
    srcs = []
    for d in dirs:
        for face in ("top", "bot"):
            Z, m = load_face(d, face); srcs.append((Z, m))
    net = UNet(); print("params", sum(p.numel() for p in net.parameters())); opt = torch.optim.Adam(net.parameters(), CFG["lr"])
    c, h, B = CFG["crop"], CFG["hole"], CFG["batch"]; t0 = time.time(); losses = []
    for step in range(CFG["steps"]):
        xs = np.zeros((B, 2, c, c), np.float32); ys = np.zeros((B, 1, c, c), np.float32); hm = np.zeros((B, 1, c, c), np.float32)
        b = 0
        while b < B:
            Z, m = srcs[rng.integers(len(srcs))]; y0 = rng.integers(0, Z.shape[0] - c); x0 = rng.integers(0, Z.shape[1] - c)
            if m[y0:y0 + c, x0:x0 + c].mean() < 0.95: continue
            patch = Z[y0:y0 + c, x0:x0 + c]; hy = rng.integers(0, c - h); hx = rng.integers(0, c - h)
            mask = np.zeros((c, c), np.float32); mask[hy:hy + h, hx:hx + h] = 1
            xs[b, 0] = patch * (1 - mask); xs[b, 1] = mask; ys[b, 0] = patch; hm[b, 0] = mask; b += 1
        xt, yt, mt = torch.from_numpy(xs), torch.from_numpy(ys), torch.from_numpy(hm)
        pred = net(xt); loss = ((pred - yt) ** 2 * mt).sum() / mt.sum()
        opt.zero_grad(); loss.backward(); opt.step(); losses.append(loss.item())
        if step % 500 == 0: print(f"step {step} loss {np.mean(losses[-500:]):.4f} {time.time()-t0:.0f}s", flush=True)
    torch.save(dict(state=net.state_dict(), cfg=CFG, dirs=dirs, final_loss=float(np.mean(losses[-500:]))), out)
    json.dump(dict(cfg=CFG, dirs=dirs, loss_curve=losses[::50], seconds=time.time() - t0), open(out + ".json", "w"))

@torch.no_grad()
def predict(model, d, faces):
    ck = torch.load(model, map_location="cpu"); net = UNet(ck["cfg"]["chans"]); net.load_state_dict(ck["state"]); net.eval()
    h = ck["cfg"]["hole"]; T = 512; halo = 32
    for face in faces:
        Z, m = load_face(d, face); H, W = Z.shape; A = np.zeros((H, W), np.float32); t0 = time.time()
        for phase in range(4):
            py, px = (phase // 2) * h, (phase % 2) * h
            hole = np.zeros((H, W), np.float32)
            gy = ((np.arange(H) - py) // h) % 2 == 0; gx = ((np.arange(W) - px) // h) % 2 == 0
            hole[np.ix_(gy, gx)] = 1                                   # checkerboard of 24x24 holes; 4 phases tile the plane
            for y0 in range(0, H, T):
                for x0 in range(0, W, T):
                    ya, yb = max(0, y0 - halo), min(H, y0 + T + halo); xa, xb = max(0, x0 - halo), min(W, x0 + T + halo)
                    z = Z[ya:yb, xa:xb]; hk = hole[ya:yb, xa:xb]
                    ph, pw = (-z.shape[0]) % 4, (-z.shape[1]) % 4
                    x = np.stack([z * (1 - hk), hk])[None]; x = np.pad(x, ((0, 0), (0, 0), (0, ph), (0, pw)), mode="reflect")
                    out = net(torch.from_numpy(x.astype(np.float32)))[0, 0].numpy()[:z.shape[0], :z.shape[1]]
                    err = np.abs(out - z) * hk
                    A[y0:min(H, y0 + T), x0:min(W, x0 + T)] += err[y0 - ya:y0 - ya + min(T, H - y0), x0 - xa:x0 - xa + min(T, W - x0)]
            print(f"{face} phase {phase} {time.time()-t0:.0f}s", flush=True)
        np.save(os.path.join(d, f"a_{face}.npy"), A.astype(np.float16))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode"); ap.add_argument("a"); ap.add_argument("b", nargs="+"); ap.add_argument("--faces", default="top,bot")
    ar = ap.parse_args()
    if ar.mode == "train": train(ar.a, ar.b)
    else:
        for d in ar.b: predict(ar.a, d, ar.faces.split(","))
