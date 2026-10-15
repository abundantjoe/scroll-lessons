import torch, time, random, sys; sys.path.insert(0, '.')
from edge3d import EdgeBank; from unet3d import UNet3D, dice_bce; from ssl3d import CNNEncoder3D, DINO3D, augment3d; from master import Master
torch.manual_seed(0); g = random.Random(0)
x = torch.rand(2, 1, 16, 64, 64)                      # surface-aligned stack: 16 layers x 64 x 64
assert EdgeBank()(x).shape == (2, 4, 16, 64, 64)
u = UNet3D(in_ch=4, base=16); n = sum(p.numel() for p in u.parameters()); t = time.time(); y, v = u(EdgeBank()(x), return_3d=True); dt = time.time() - t
assert y.shape == (2, 1, 64, 64) and v.shape == (2, 1, 16, 64, 64); print(f'UNet3D params {n/1e6:.2f}M, fwd 2x16x64x64 {dt:.2f}s')
loss = dice_bce(y, (torch.rand(2, 1, 64, 64) > 0.9).float()); loss.backward(); print('dice+bce', float(loss))
enc = CNNEncoder3D(width=16, out_dim=128); dino = DINO3D(enc, out_dim=256); c = torch.rand(2, 1, 64, 64, 64)
t = time.time(); l = dino.loss([augment3d(c, g), augment3d(c, g)], [augment3d(c[:, :, 16:48, 16:48, 16:48], g)]); l.backward(); dino.update_teacher(); print(f'DINO3D params {sum(p.numel() for p in enc.parameters())/1e6:.2f}M, loss {float(l):.3f}, step {time.time()-t:.2f}s')
with torch.autocast('cpu', dtype=torch.bfloat16):
    m = Master(ssl_encoder=enc, base=16, ssl_dim=128); y2, v2 = m(x, return_3d=True)
assert y2.shape == (2, 1, 64, 64); print('Master fused OK (bf16 autocast)')
