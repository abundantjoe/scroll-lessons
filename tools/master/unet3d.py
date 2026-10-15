# Provenance: Project HERCULES | [id removed]
"""Strategy 2: a native 3D U-Net that reads the whole depth profile of a surface-aligned stack and emits a 2D ink map
by a learned soft aggregation over the central depth slices (robust to the surface sitting a few slices off).
Input (B,C,D,H,W); output (B,1,H,W) logits. Small enough for CPU (base=16: ~1.1M params)."""
import torch, torch.nn as nn, torch.nn.functional as F

def block(i, o):
    return nn.Sequential(nn.Conv3d(i, o, 3, padding=1), nn.InstanceNorm3d(o, affine=True), nn.GELU(),
                         nn.Conv3d(o, o, 3, padding=1), nn.InstanceNorm3d(o, affine=True), nn.GELU())

class UNet3D(nn.Module):
    def __init__(self, in_ch=4, base=16, depth_center=None):
        super().__init__()
        c = [base, base * 2, base * 4, base * 8]
        self.e1, self.e2, self.e3, self.e4 = block(in_ch, c[0]), block(c[0], c[1]), block(c[1], c[2]), block(c[2], c[3])
        self.d3, self.d2, self.d1 = block(c[3] + c[2], c[2]), block(c[2] + c[1], c[1]), block(c[1] + c[0], c[0])
        self.vox = nn.Conv3d(c[0], 1, 1)                  # per-voxel ink logit (3-D map, useful on its own)
        self.att = nn.Conv3d(c[0], 1, 1)                  # per-voxel depth-attention logit
        self.depth_center = depth_center
    def forward(self, x, return_3d=False):
        e1 = self.e1(x); e2 = self.e2(F.max_pool3d(e1, 2)); e3 = self.e3(F.max_pool3d(e2, 2)); e4 = self.e4(F.max_pool3d(e3, 2))
        u = lambda t, ref: F.interpolate(t, size=ref.shape[2:], mode='trilinear', align_corners=False)
        d3 = self.d3(torch.cat([u(e4, e3), e3], 1)); d2 = self.d2(torch.cat([u(d3, e2), e2], 1)); d1 = self.d1(torch.cat([u(d2, e1), e1], 1))
        v = self.vox(d1); a = self.att(d1)                              # (B,1,D,H,W)
        D = v.shape[2]; k = D // 2 if self.depth_center is None else self.depth_center
        lo, hi = max(0, D // 2 - max(2, D // 3)), min(D, D // 2 + max(2, D // 3) + 1)   # central band of slices
        vf, af = v.float(), a.float()                                   # fp32: under bf16 autocast sigmoid saturates to exactly 1.0 and logit() is inf
        w = torch.softmax(af[:, :, lo:hi], dim=2)                      # soft depth weights over the central band
        out2d = (torch.sigmoid(vf[:, :, lo:hi]) * w).sum(2)            # (B,1,H,W) soft probability
        logit2d = torch.logit(out2d.clamp(1e-4, 1 - 1e-4))
        return (logit2d, v) if return_3d else logit2d

def dice_bce(logits, target, eps=1.0):
    p = torch.sigmoid(logits); inter = (p * target).sum((1, 2, 3)); dice = 1 - (2 * inter + eps) / (p.sum((1, 2, 3)) + target.sum((1, 2, 3)) + eps)
    return F.binary_cross_entropy_with_logits(logits, target) + dice.mean()
