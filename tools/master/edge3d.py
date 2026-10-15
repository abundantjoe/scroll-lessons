# Provenance: Project HERCULES | [id removed]
"""Strategy 3: fixed 3D gradient filter bank (Sobel x/y/z, gradient magnitude, Laplacian) applied to a CT sub-volume.
Phase-contrast scans put a halo at material boundaries; these channels expose high-frequency boundary structure
independent of absolute density. Output channels: [raw, |grad|, laplacian, gz] (gz = along-normal gradient)."""
import torch, torch.nn as nn, torch.nn.functional as F

def _sobel3d():
    s = torch.tensor([1., 2., 1.]); d = torch.tensor([-1., 0., 1.])
    kz = d[:, None, None] * s[None, :, None] * s[None, None, :]
    ky = s[:, None, None] * d[None, :, None] * s[None, None, :]
    kx = s[:, None, None] * s[None, :, None] * d[None, None, :]
    return torch.stack([kz, ky, kx]) / 32.0            # (3,3,3,3)

def _laplacian3d():
    k = torch.zeros(3, 3, 3); k[1, 1, 1] = -6; k[0, 1, 1] = k[2, 1, 1] = k[1, 0, 1] = k[1, 2, 1] = k[1, 1, 0] = k[1, 1, 2] = 1
    return k

class EdgeBank(nn.Module):
    """x: (B,1,D,H,W) float in [0,1] -> (B,4,D,H,W). Non-trainable."""
    def __init__(self):
        super().__init__()
        self.register_buffer('sobel', _sobel3d()[:, None])            # (3,1,3,3,3)
        self.register_buffer('lap', _laplacian3d()[None, None])        # (1,1,3,3,3)
    def forward(self, x):
        g = F.conv3d(F.pad(x, (1,) * 6, mode='replicate'), self.sobel)   # (B,3,D,H,W) = gz, gy, gx
        mag = torch.sqrt((g * g).sum(1, keepdim=True) + 1e-8)
        lap = F.conv3d(F.pad(x, (1,) * 6, mode='replicate'), self.lap)
        return torch.cat([x, mag, lap, g[:, :1]], 1)
