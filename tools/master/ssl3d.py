# Provenance: Project HERCULES | [id removed]
"""Strategy 1: DINO-style self-distillation on 3-D CT chunks. Student/teacher (EMA) see different augmented views of the
same 64^3 papyrus chunk; the loss is cross-entropy between sharpened, centred teacher assignments and student outputs
(equivalently it maximises agreement / cosine similarity of the views). Encoder: a 3-D CNN by default (CPU-feasible,
~0.6M params); a small 3-D ViT is available with --vit (same objective, far slower on CPU)."""
import math, copy, torch, torch.nn as nn, torch.nn.functional as F
from torch.nn.utils import parametrizations as _P

class CNNEncoder3D(nn.Module):
    def __init__(self, in_ch=1, width=24, out_dim=256):
        super().__init__()
        c = [width, width * 2, width * 4, width * 8]; layers = []; i = in_ch
        for o in c: layers += [nn.Conv3d(i, o, 3, stride=2, padding=1), nn.GroupNorm(8, o), nn.GELU(), nn.Conv3d(o, o, 3, padding=1), nn.GroupNorm(8, o), nn.GELU()]; i = o
        self.body = nn.Sequential(*layers); self.head = nn.Linear(c[-1], out_dim); self.out_dim = out_dim
    def forward(self, x):                                   # (B,1,D,H,W) -> (B,out_dim)
        return self.head(self.body(x).mean((2, 3, 4)))
    def feature_map(self, x):                               # (B,C,D/16,H/16,W/16) dense features for downstream fusion
        return self.body(x)

class ViT3D(nn.Module):
    def __init__(self, in_ch=1, vol=64, patch=8, dim=192, depth=4, heads=3, out_dim=256):
        super().__init__(); n = (vol // patch) ** 3
        self.patch = nn.Conv3d(in_ch, dim, patch, stride=patch); self.pos = nn.Parameter(torch.zeros(1, n + 1, dim)); self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(dim, heads, dim * 4, batch_first=True, norm_first=True), depth); self.norm = nn.LayerNorm(dim); self.head = nn.Linear(dim, out_dim); self.out_dim = out_dim
        nn.init.trunc_normal_(self.pos, std=.02); nn.init.trunc_normal_(self.cls, std=.02)
    def forward(self, x):
        t = self.patch(x).flatten(2).transpose(1, 2); t = torch.cat([self.cls.expand(t.shape[0], -1, -1), t], 1) + self.pos[:, :t.shape[1] + 0]
        return self.head(self.norm(self.enc(t))[:, 0])

class DINOHead(nn.Module):
    def __init__(self, in_dim, out_dim=1024, hidden=512, bottleneck=128):
        super().__init__(); self.mlp = nn.Sequential(nn.Linear(in_dim, hidden), nn.GELU(), nn.Linear(hidden, bottleneck)); self.last = _P.weight_norm(nn.Linear(bottleneck, out_dim, bias=False), name='weight', dim=0)
        with torch.no_grad(): self.last.parametrizations.weight.original0.fill_(1)
        self.last.parametrizations.weight.original0.requires_grad = False
    def forward(self, x): return self.last(F.normalize(self.mlp(x), dim=-1))

class DINO3D(nn.Module):
    def __init__(self, encoder, out_dim=1024, teacher_temp=0.04, student_temp=0.1, center_m=0.9, ema=0.996):
        super().__init__(); self.student = nn.Sequential(encoder, DINOHead(encoder.out_dim, out_dim))
        self.teacher = nn.Sequential(copy.deepcopy(encoder), DINOHead(encoder.out_dim, out_dim)); self.teacher.load_state_dict(self.student.state_dict())
        for p in self.teacher.parameters(): p.requires_grad = False
        self.register_buffer('center', torch.zeros(1, out_dim)); self.tt, self.st, self.cm, self.ema = teacher_temp, student_temp, center_m, ema
    @torch.no_grad()
    def update_teacher(self):
        for ps, pt in zip(self.student.parameters(), self.teacher.parameters()): pt.mul_(self.ema).add_(ps.detach(), alpha=1 - self.ema)
    def loss(self, global_views, local_views):
        """global_views: list of (B,1,64,64,64) tensors (2); local_views: list of smaller crops (resized to 32^3 or same size)."""
        with torch.no_grad():
            t_raw = [self.teacher(v).float() for v in global_views]                       # fp32: the softmax at temperature 0.04 is not bf16-safe
            t_out = [F.softmax((t - self.center) / self.tt, -1) for t in t_raw]
            self.center.mul_(self.cm).add_(torch.cat(t_raw).mean(0, keepdim=True), alpha=1 - self.cm)
        s_out = [F.log_softmax(self.student(v).float() / self.st, -1) for v in global_views + local_views]
        total, n = 0.0, 0
        for it, t in enumerate(t_out):
            for is_, s in enumerate(s_out):
                if is_ == it: continue
                total = total + (-(t * s).sum(-1)).mean(); n += 1
        return total / n

def augment3d(x, g):
    """Random flips/rotations within the sheet plane, intensity jitter, small Gaussian noise, random crop-resize. x: (B,1,D,H,W)."""
    if g.random() < 0.5: x = x.flip(-1)
    if g.random() < 0.5: x = x.flip(-2)
    k = int(g.random() * 4); x = torch.rot90(x, k, dims=(-2, -1))
    x = x * (0.8 + 0.4 * g.random()) + (g.random() - 0.5) * 0.1 + torch.randn_like(x) * 0.02 * g.random()
    return x.clamp(0, 1)
