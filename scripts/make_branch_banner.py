"""Render the banner of one Dominion experiment branch: the branch's title and status over the PHerc0343 CT slice of the
main banner, in the colour of the branch's experiment family. CT only, no ink shown.

  python make_branch_banner.py --title T --family KEY --subtitle S --status S --verdict V --branch B --out banner.jpg
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_banner import LEVEL, UM_PX, Z0, fetch_fonts, fetch_slice, render_ct  # noqa: E402

W, H = 1600, 533
# family: (label, ramp stops black -> light, accent for text and rim)
FAMILIES = {
    'p4': ('PARIS-4 investigations', [[5, 5, 10], [36, 10, 48], [112, 40, 150], [196, 110, 232], [244, 214, 255]], (206, 150, 255)),
    'train': ('ink-model training', [[4, 8, 10], [6, 38, 44], [20, 118, 128], [96, 212, 210], [224, 255, 250]], (110, 225, 220)),
    'fl': ('First Letters push', [[5, 5, 8], [40, 8, 6], [150, 40, 10], [236, 128, 36], [255, 236, 196]], (240, 170, 80)),
    'own': ('own-model experiments', [[4, 8, 5], [14, 44, 20], [48, 128, 60], [150, 222, 120], [236, 255, 222]], (160, 230, 130)),
    'misc': ('geometry, reading and records', [[5, 6, 10], [14, 28, 60], [48, 98, 172], [140, 190, 242], [230, 240, 255]], (150, 196, 246)),
}
CHIP = {'PASSED': (60, 170, 90), 'FAILED': (200, 70, 60), 'NULL': (120, 120, 128), 'INCONCLUSIVE': (210, 150, 50),
        'VOID': (110, 110, 118), 'NONE': (95, 95, 105), 'UNKNOWN': (95, 95, 105)}


def ramp_from(stops):
    st = np.array([0.0, 0.30, 0.58, 0.82, 1.0])
    cols = np.array(stops, float)
    return lambda x: np.stack([np.interp(x, st, cols[:, c]) for c in range(3)], -1)


def fit_font(path, text, maxw, start, stop, draw):
    """Largest size in [stop, start] at which text fits maxw; below stop, scaled down to fit."""
    for size in range(start, stop - 1, -2):
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= maxw:
            return f
    f = ImageFont.truetype(path, stop)
    return ImageFont.truetype(path, max(12, int(stop * maxw / draw.textlength(text, font=f))))


def fit_title(path, text, maxw, draw):
    """One line at 74-44 px; else two lines split at the space nearest the middle, at 56-36 px; else one line scaled."""
    for size in range(74, 43, -2):
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= maxw:
            return f, [text]
    words = text.split()
    splits = sorted(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(text) / 2))
    for size in range(56, 35, -2):
        f = ImageFont.truetype(path, size)
        for i in splits:
            lines = [' '.join(words[:i]), ' '.join(words[i:])]
            if max(draw.textlength(t, font=f) for t in lines) <= maxw:
                return f, lines
    return fit_font(path, text, maxw, 44, 44, draw), [text]


def main():
    ap = argparse.ArgumentParser()
    for k in ('title', 'family', 'subtitle', 'status', 'verdict', 'branch', 'out'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--cache', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.banner_cache'))
    a = ap.parse_args()
    label, stops, accent = FAMILIES[a.family]
    ct = fetch_slice(a.cache)
    fonts = fetch_fonts(a.cache)
    img, mask = render_ct(ct, ramp_from(stops), rim=accent)
    s = 0.41
    img = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    m = Image.fromarray((mask * 255).astype(np.uint8)).resize(img.size, Image.LANCZOS)
    base = np.array([6, 6, 9], float)
    canvas = Image.new('RGB', (W, H), tuple(int(c) for c in base))
    cx, cy = W - img.width // 2 - 30, H // 2 + 6
    x0, y0 = cx - img.width // 2, cy - img.height // 2
    haze = Image.new('L', (W, H), 0)
    ImageDraw.Draw(haze).ellipse([cx - 380, cy - 290, cx + 380, cy + 290], fill=70)
    haze = haze.filter(ImageFilter.GaussianBlur(110))
    canvas = Image.composite(Image.new('RGB', (W, H), tuple(int(c * 0.35) for c in accent)), canvas, haze)
    glow = Image.new('RGB', (W, H), 0)
    glow.paste(img, (x0, y0), m)
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    canvas = Image.fromarray(np.clip(np.asarray(canvas, float) + np.asarray(glow, float) * 0.8, 0, 255).astype(np.uint8))
    canvas.paste(img, (x0, y0), m)
    arr = np.asarray(canvas, float)
    fade = np.clip((np.arange(W) - (x0 - 30)) / 300.0, 0, 1) ** 1.4
    arr = base + (arr - base) * fade[None, :, None]
    canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    d = ImageDraw.Draw(canvas)
    tx, maxw = 64, x0 - 64 - 30
    over = ImageFont.truetype(fonts[('Inter', 600)], 19)
    d.text((tx, 132), f'DOMINION  ·  {label.upper()}', font=over, fill=accent)
    tf, lines = fit_title(fonts[('Cinzel', 700)], a.title, maxw, d)
    lh = int(tf.size * 1.12)
    tm = Image.new('L', (W, H), 0)
    for i, line in enumerate(lines):
        ImageDraw.Draw(tm).text((tx, 168 + i * lh), line, font=tf, fill=255)
    top = np.array([250, 244, 232], float)
    g = np.clip((np.arange(H)[:, None] - 168) / (110.0 + lh * (len(lines) - 1)), 0, 1)
    rows = top * (1 - g) + np.array(accent, float) * g
    grad = Image.fromarray(np.broadcast_to(rows[:, None, :], (H, W, 3)).astype(np.uint8))
    canvas = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), canvas, tm.filter(ImageFilter.GaussianBlur(9)).point(lambda p: int(p * 0.6)))
    canvas = Image.composite(grad, canvas, tm)
    d = ImageDraw.Draw(canvas)
    ty = 168 + lh * (len(lines) - 1) + tf.size + 26
    d.line([(tx + 2, ty), (tx + min(maxw, max(d.textlength(t, font=tf) for t in lines)), ty)], fill=accent, width=2)
    sub = fit_font(fonts[('Inter', 400)], a.subtitle, maxw, 26, 16, d)
    d.text((tx + 2, ty + 20), a.subtitle, font=sub, fill=(214, 206, 196))
    chip_f = ImageFont.truetype(fonts[('Inter', 600)], 18)
    cx0, cy0 = tx + 2, ty + 74
    for text, col in ((a.status, (70, 74, 86)), (a.verdict, CHIP.get(a.verdict, (95, 95, 105)))):
        w = d.textlength(text, font=chip_f) + 28
        d.rounded_rectangle([cx0, cy0, cx0 + w, cy0 + 34], radius=17, fill=col)
        d.text((cx0 + 14, cy0 + 17), text, font=chip_f, fill=(250, 250, 250), anchor='lm')
        cx0 += w + 10
    small = ImageFont.truetype(fonts[('Inter', 400)], 13)
    d.text((tx + 2, H - 70), f'branch {a.branch}', font=small, fill=(130, 124, 116))
    d.text((tx + 2, H - 51), f'CT only, no ink shown: PHerc0343, axial slice z ≈ {Z0} (level {LEVEL}, {UM_PX:.2f} µm/px).',
           font=small, fill=(110, 104, 98))
    d.text((tx + 2, H - 32), 'Data: Vesuvius Challenge - CT Scans of Herculaneum Papyri (Angelotti et al.), CC BY-NC 4.0.',
           font=small, fill=(110, 104, 98))
    L = 5000 / UM_PX * s
    d.rectangle([W - L - 40, H - 40, W - 40, H - 36], fill=(240, 236, 228))
    d.text((W - 40 - L / 2, H - 30), '5 mm', font=small, fill=(220, 214, 204), anchor='mt')
    canvas.save(a.out, quality=88, optimize=True)


if __name__ == '__main__':
    main()
