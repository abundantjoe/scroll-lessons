# Provenance: Project HERCULES | owner the owner | [id removed]
"""LC384: frozen-encoder letter-context head on the official base ink model (task devloop-r1). Numbers only.

Base: official ink_9um hybrid_3d2d seed42 step-075000 (sha256 e635558a...9cab), built by villa 41701aa make_model.
  encoder = depth_fusion (3-D stem) + network.shared_encoder (2-D), FROZEN, run in eval mode;
  per 128 px tile it yields six skips (32x128^2, 64x64^2, 128x32^2, 256x16^2, 320x8^2, 320x4^2).
Context block (new): the level-4 and level-5 skips of the 3 x 3 neighbourhood of 128 px tiles (neighbour origins at
  +-128 px, i.e. 384 px = 3.6 mm of context) are stitched into 320 x 24^2 and 320 x 12^2 mosaics; a neighbour that
  does not exist (outside the image, all-zero raw input, or not available in the training pool) is replaced by a
  learned per-level token (one C-vector broadcast over the tile). At each level: two residual 3x3 conv blocks
  (dilation 1 and 2; InstanceNorm2d, LeakyReLU 0.01 as the base model); at level 5 also one pre-norm multi-head
  self-attention layer over the 144 mosaic cells (learned position embedding). A ZERO-initialised 1x1 projection
  gives the centre-tile update, added to the centre tile's level-4/5 skips.
Heads:
  'basedec' : the base decoder + 1x1 head (copied from the checkpoint), fine-tuned, fed the updated skips.
  'light'   : the base decoder + head FROZEN (base decoder path intact), plus a light trainable correction: 1x1 convs
              of skip levels 0 (32@128), 2 (128@32) and updated level 4 (320@8) to 32 ch, bilinear upsampling to 128,
              sum, 3x3 conv + InstanceNorm + LeakyReLU, ZERO-initialised 1x1 conv to one logit channel, added to the
              base logits.
Both variants are an exact identity to the base model at initialisation (zero-init projections; tested)."""
from __future__ import annotations

import copy
import hashlib

import torch
from torch import nn
import torch.nn.functional as F

BASE_CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
BASE_SHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
OFFSETS = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]  # row-major 3 x 3, centre index 4
CENTRE = 4


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_base(path=BASE_CK, verify=True):
    """Official base model (strict load) and its embedded config dict."""
    from vesuvius.ink_detection.config import InkConfig
    from vesuvius.ink_detection.models.model import make_model
    from vesuvius.ink_detection.models.checkpoint import load_checkpoint
    if verify:
        assert sha256_file(path) == BASE_SHA, "base checkpoint hash mismatch"
    ck = load_checkpoint(path)
    ink = InkConfig.from_mapping(ck["config"])
    m = make_model(ink)
    m.load_state_dict(ck["model"], strict=True)
    m.eval()
    return m, ck["config"], ink


class ResConv(nn.Module):
    def __init__(self, c, dil):
        super().__init__()
        self.conv = nn.Conv2d(c, c, 3, padding=dil, dilation=dil)
        self.norm = nn.InstanceNorm2d(c, affine=True)
        self.act = nn.LeakyReLU(0.01, inplace=True)

    def forward(self, x):
        return x + self.act(self.norm(self.conv(x)))


def mosaic(t):
    """(B, 9, C, h, w), row-major 3 x 3 -> (B, C, 3h, 3w)."""
    B, n, C, h, w = t.shape
    assert n == 9
    return t.view(B, 3, 3, C, h, w).permute(0, 3, 1, 4, 2, 5).reshape(B, C, 3 * h, 3 * w)


class LetterContext(nn.Module):
    def __init__(self, c4=320, c5=320, heads=8):
        super().__init__()
        self.miss4 = nn.Parameter(torch.zeros(c4))
        self.miss5 = nn.Parameter(torch.zeros(c5))
        self.l4 = nn.Sequential(ResConv(c4, 1), ResConv(c4, 2))
        self.l5 = nn.Sequential(ResConv(c5, 1), ResConv(c5, 2))
        self.pos5 = nn.Parameter(torch.zeros(1, 144, c5))
        self.ln = nn.LayerNorm(c5)
        self.attn = nn.MultiheadAttention(c5, heads, batch_first=True)
        self.out4 = nn.Conv2d(c4, c4, 1)
        self.out5 = nn.Conv2d(c5, c5, 1)
        for m in (self.out4, self.out5):
            nn.init.zeros_(m.weight)
            nn.init.zeros_(m.bias)

    @staticmethod
    def fill(n, present, token):
        """n (B, 9, C, h, w); present (B, 9) bool -> missing tiles replaced by the broadcast token."""
        tok = token.to(n.dtype).view(1, 1, -1, 1, 1).expand_as(n)
        return torch.where(present.view(*present.shape, 1, 1, 1), n, tok)

    def forward(self, n4, n5, present):
        m4 = self.l4(mosaic(self.fill(n4, present, self.miss4)))
        m5 = self.l5(mosaic(self.fill(n5, present, self.miss5)))
        B, C, H, W = m5.shape
        tok = m5.flatten(2).transpose(1, 2) + self.pos5.to(m5.dtype)
        q = self.ln(tok)
        tok = tok + self.attn(q, q, q, need_weights=False)[0]
        m5 = tok.transpose(1, 2).reshape(B, C, H, W)
        h4, h5 = n4.shape[-1], n5.shape[-1]
        return self.out4(m4)[..., h4:2 * h4, h4:2 * h4], self.out5(m5)[..., h5:2 * h5, h5:2 * h5]


class LightHead(nn.Module):
    def __init__(self, c0=32, c2=128, c4=320, mid=32):
        super().__init__()
        self.p0, self.p2, self.p4 = nn.Conv2d(c0, mid, 1), nn.Conv2d(c2, mid, 1), nn.Conv2d(c4, mid, 1)
        self.mix = nn.Sequential(nn.Conv2d(mid, mid, 3, padding=1), nn.InstanceNorm2d(mid, affine=True), nn.LeakyReLU(0.01, inplace=True))
        self.out = nn.Conv2d(mid, 1, 1)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, s0, s2, s4):
        size = s0.shape[-2:]
        x = self.p0(s0) + F.interpolate(self.p2(s2), size=size, mode="bilinear", align_corners=False) \
            + F.interpolate(self.p4(s4), size=size, mode="bilinear", align_corners=False)
        return self.out(self.mix(x))


class LC384(nn.Module):
    """forward(centre_skips, n4, n5, present) -> logits (B, 1, 128, 128). Encoder is separate (encode())."""

    def __init__(self, base, variant="basedec"):
        super().__init__()
        assert variant in ("basedec", "light")
        self.variant = variant
        net = base.network
        self.base_stem = base.depth_fusion
        self.base_encoder = net.shared_encoder
        for p in list(self.base_stem.parameters()) + list(self.base_encoder.parameters()):
            p.requires_grad_(False)
        self.decoder = copy.deepcopy(net.shared_decoder)
        self.head = copy.deepcopy(net.task_heads["ink"])
        self.context = LetterContext()
        if variant == "light":
            for p in list(self.decoder.parameters()) + list(self.head.parameters()):
                p.requires_grad_(False)
            self.light = LightHead()

    def train(self, mode=True):
        super().train(mode)
        self.base_stem.eval()
        self.base_encoder.eval()
        if self.variant == "light":
            self.decoder.eval()
            self.head.eval()
        return self

    @torch.no_grad()
    def encode(self, x):
        """x (B, 1, 17, 128, 128) normalised -> list of 6 skips (frozen base encoder)."""
        return self.base_encoder(self.base_stem(x))

    def trainable_state(self):
        keep = ("context.",) + (("decoder.", "head.") if self.variant == "basedec" else ("light.",))
        return {k: v for k, v in self.state_dict().items() if k.startswith(keep)}

    def forward(self, skips, n4, n5, present):
        d4, d5 = self.context(n4, n5, present)
        f = list(skips)
        f[4] = f[4] + d4.to(f[4].dtype)
        f[5] = f[5] + d5.to(f[5].dtype)
        logits = self.head(self.decoder(f))
        if self.variant == "light":
            logits = logits + self.light(f[0], f[2], f[4]).to(logits.dtype)
        return logits


def build(variant="basedec", base_path=BASE_CK):
    base, cfg, ink = load_base(base_path)
    return LC384(base, variant), cfg, ink


def save_ckpt(path, model, meta):
    torch.save(dict(lc_state=model.trainable_state(), variant=model.variant, base_ckpt=BASE_CK,
                    base_sha256=BASE_SHA, meta=meta), path)


def load_ckpt(path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    model, cfg, ink = build(ck["variant"], ck.get("base_ckpt", BASE_CK))
    missing, unexpected = model.load_state_dict(ck["lc_state"], strict=False)
    assert not unexpected, unexpected
    trainable_missing = [k for k in missing if k.startswith(tuple(model.trainable_state().keys()))]
    assert not trainable_missing, trainable_missing
    model.eval()
    return model, ck, cfg, ink
