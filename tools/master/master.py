# Provenance: Project HERCULES | [id removed]
"""The Master model: EdgeBank channels (strategy 3) -> UNet3D depth-profile reader (strategy 2), with the frozen DINO-3D
encoder's dense features (strategy 1) injected at the bottleneck. Emits a 2-D ink logit map and a 3-D per-voxel logit map."""
import torch, torch.nn as nn, torch.nn.functional as F
from edge3d import EdgeBank
from unet3d import UNet3D, dice_bce

class Master(nn.Module):
    def __init__(self, ssl_encoder=None, base=16, ssl_dim=192):
        super().__init__(); self.edge = EdgeBank(); self.unet = UNet3D(in_ch=4, base=base); self.ssl = ssl_encoder
        if ssl_encoder is not None:
            for p in self.ssl.parameters(): p.requires_grad = False
            self.ssl_proj = nn.Conv3d(ssl_dim, base * 8, 1)
    def forward(self, x, return_3d=False):
        f = self.edge(x)
        if self.ssl is None: return self.unet(f, return_3d)
        # inject frozen SSL features at the U-Net bottleneck
        u = self.unet; e1 = u.e1(f); e2 = u.e2(F.max_pool3d(e1, 2)); e3 = u.e3(F.max_pool3d(e2, 2)); e4 = u.e4(F.max_pool3d(e3, 2))
        with torch.no_grad(): s = self.ssl.feature_map(x)
        e4 = e4 + F.interpolate(self.ssl_proj(s), size=e4.shape[2:], mode='trilinear', align_corners=False)
        up = lambda t, ref: F.interpolate(t, size=ref.shape[2:], mode='trilinear', align_corners=False)
        d3 = u.d3(torch.cat([up(e4, e3), e3], 1)); d2 = u.d2(torch.cat([up(d3, e2), e2], 1)); d1 = u.d1(torch.cat([up(d2, e1), e1], 1))
        v = u.vox(d1); a = u.att(d1); D = v.shape[2]; lo, hi = max(0, D // 2 - max(2, D // 3)), min(D, D // 2 + max(2, D // 3) + 1)
        w = torch.softmax(a[:, :, lo:hi], dim=2); out2d = (torch.sigmoid(v[:, :, lo:hi]) * w).sum(2); logit2d = torch.logit(out2d.clamp(1e-4, 1 - 1e-4))
        return (logit2d, v) if return_3d else logit2d
