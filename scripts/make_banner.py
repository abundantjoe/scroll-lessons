"""Render figures/dominion_banner.png: an axial CT slice of PHerc0343 (the public positive-control scroll) in ember tones,
with the programme title. CT only: no ink prediction is shown, and no image of any unread scroll is used.

  python make_banner.py [--cache DIR]

Fetches one axial slice at pyramid level 2 (34.56 um/px, about 260 MB of uncompressed chunks) anonymously from the
Vesuvius Challenge open data, and the Cinzel and Inter fonts (SIL Open Font License) from Google Fonts.
Needs numpy, scipy, pillow, zarr<3, s3fs, matplotlib.
"""
import argparse
import json
import os
import re
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = 'vesuvius-challenge-open-data/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr'
LEVEL, Z0 = 2, 10250                  # level-0 z of the slice (the height band of the published control letters)
UM_PX = 8.64 * 2 ** LEVEL             # 34.56 um per pixel at level 2
CROP = (slice(480, 1760), slice(340, 2000))
W, H = 2400, 800
FONTS = {'Cinzel': '400;700;900', 'Inter': '400;600'}


def fetch_slice(cache):
    p = os.path.join(cache, f'PHerc0343_L{LEVEL}_z{Z0}.npy')
    if not os.path.exists(p):
        import s3fs
        import zarr
        fs = s3fs.S3FileSystem(anon=True)
        z = zarr.open(s3fs.S3Map(f'{VOL}/{LEVEL}', s3=fs), mode='r')
        np.save(p, z[Z0 // 2 ** LEVEL, CROP[0], CROP[1]])
    return np.load(p)


def fetch_fonts(cache):
    out = {}
    for fam, w in FONTS.items():
        css = urllib.request.urlopen(urllib.request.Request(
            f'https://fonts.googleapis.com/css2?family={fam}:wght@{w}', headers={'User-Agent': 'curl/8'})).read().decode()
        for weight, url in re.findall(r'font-weight: (\d+);.*?url\((https://[^)]+\.ttf)\)', css, re.S):
            f = os.path.join(cache, f'{fam}-{weight}.ttf')
            if not os.path.exists(f):
                urllib.request.urlretrieve(url, f)
            out[(fam, int(weight))] = f
    return out


def ember(x):
    """0..1 -> RGB on a black, oxblood, ember, gold, ivory ramp."""
    stops = np.array([0.0, 0.30, 0.55, 0.78, 0.92, 1.0])
    cols = np.array([[5, 5, 8], [40, 8, 6], [150, 40, 10], [236, 128, 36], [252, 204, 120], [255, 244, 222]], float)
    return np.stack([np.interp(x, stops, cols[:, c]) for c in range(3)], -1)


def render_ct(ct, ramp=None, rim=(255, 170, 80)):
    mask = ct > 0
    v = ct.astype(np.float32)
    lo, hi = np.percentile(v[mask], [1, 99.5])
    v = np.clip((v - lo) / (hi - lo), 0, 1)
    local = v - ndimage.gaussian_filter(v, 10) * 0.8             # bring out the wound layers
    local = ndimage.gaussian_filter(local, 0.6)
    lo2, hi2 = np.percentile(local[mask], [3, 99.8])
    local = np.clip((local - lo2) / (hi2 - lo2), 0, 1)
    body = 0.6 * local + 0.4 * v                                    # layer detail plus raw density
    cy, cx = ndimage.center_of_mass(mask)
    yy, xx = np.mgrid[0:ct.shape[0], 0:ct.shape[1]]
    core = np.exp(-(((yy - cy) / (0.55 * ct.shape[0])) ** 2 + ((xx - cx) / (0.55 * ct.shape[1])) ** 2))
    t = np.where(mask, np.clip((0.10 + 0.95 * body ** 1.35) * (0.78 + 0.42 * core), 0, 1), 0)   # brighter toward the core
    rgb = (ramp or ember)(t)
    edge = ndimage.binary_dilation(mask, iterations=3) & ~ndimage.binary_erosion(mask, iterations=2)
    rgb[edge] = rgb[edge] * 0.5 + np.array(rim) * 0.5   # thin hot rim on the scroll's outline
    return Image.fromarray(rgb.astype(np.uint8)), mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache', default=os.path.join(REPO, '.banner_cache'))
    ap.add_argument('--out', default=os.path.join(REPO, 'figures', 'dominion_banner.png'))
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    ct = fetch_slice(a.cache)
    fonts = fetch_fonts(a.cache)

    img, mask = render_ct(ct)
    s = 0.62
    img = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    m = Image.fromarray((mask * 255).astype(np.uint8)).resize(img.size, Image.LANCZOS)

    canvas = Image.new('RGB', (W, H), (6, 6, 9))
    # faint warm haze behind the scroll
    haze = Image.new('L', (W, H), 0)
    hd = ImageDraw.Draw(haze)
    cx, cy = W - img.width // 2 - 60, H // 2 + 10
    hd.ellipse([cx - 560, cy - 430, cx + 560, cy + 430], fill=70)
    haze = haze.filter(ImageFilter.GaussianBlur(160))
    canvas = Image.composite(Image.new('RGB', (W, H), (90, 28, 10)), canvas, haze)
    # glow: blurred copy of the scroll, screened in
    x0, y0 = cx - img.width // 2, cy - img.height // 2
    glow = Image.new('RGB', (W, H), 0)
    glow.paste(img, (x0, y0), m)
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    canvas = Image.fromarray(np.clip(np.asarray(canvas, float) + np.asarray(glow, float) * 0.9, 0, 255).astype(np.uint8))
    canvas.paste(img, (x0, y0), m)
    # fade the left part of the scroll into the dark so the title reads cleanly
    fade = np.clip((np.arange(W) - (x0 - 40)) / 420.0, 0, 1) ** 1.4
    arr = np.asarray(canvas, float)
    base = np.array([6, 6, 9], float)
    arr = base + (arr - base) * fade[None, :, None]
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    canvas = Image.fromarray(np.clip(base + (arr - base) * vig[..., None], 0, 255).astype(np.uint8))

    d = ImageDraw.Draw(canvas)
    # title with wide tracking and a gold gradient
    title, tf = 'DOMINION', ImageFont.truetype(fonts[('Cinzel', 900)], 168)
    track = 26
    widths = [d.textlength(ch, font=tf) for ch in title]
    tw = sum(widths) + track * (len(title) - 1)
    tx, ty = 110, 170
    tm = Image.new('L', (W, H), 0)
    tdm = ImageDraw.Draw(tm)
    x = tx
    for ch, w in zip(title, widths):
        tdm.text((x, ty), ch, font=tf, fill=255)
        x += w + track
    g = np.clip((np.arange(H)[:, None] - ty) / 190.0, 0, 1)                    # (H, 1): 0 at the cap line, 1 below
    rows = np.array([255, 236, 190]) * (1 - g) + np.array([214, 140, 52]) * g   # (H, 3)
    grad = np.broadcast_to(rows[:, None, :], (H, W, 3))
    shadow = tm.filter(ImageFilter.GaussianBlur(14))
    canvas = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), canvas, shadow.point(lambda p: int(p * 0.6)))
    canvas = Image.composite(Image.fromarray(grad.astype(np.uint8)), canvas, tm)
    d = ImageDraw.Draw(canvas)
    # rule, tagline, stats, credit
    d.line([(tx + 4, ty + 215), (tx + tw, ty + 215)], fill=(196, 128, 52), width=3)
    n = json.load(open(os.path.join(REPO, 'results', 'experiments', 'experiment_map.json')))['n_experiments']
    d.text((tx + 4, ty + 245), f'{n} experiments on finding ink inside carbonized Herculaneum scrolls',
           font=ImageFont.truetype(fonts[('Inter', 600)], 36), fill=(240, 228, 210))
    fam = ImageFont.truetype(fonts[('Inter', 400)], 27)
    d.text((tx + 4, ty + 305), 'blind reading   ·   fine-tuned ink models   ·   geometry',
           font=fam, fill=(196, 176, 150))
    d.text((tx + 4, ty + 345), 'a First Letters push on 22 volumes',
           font=fam, fill=(196, 176, 150))
    small = ImageFont.truetype(fonts[('Inter', 400)], 17)
    zt = f'{Z0:,}'.replace(',', ' ')
    d.text((tx + 4, H - 74), f'CT only, no ink shown: PHerc0343, axial slice at z ≈ {zt} (level {LEVEL}, {UM_PX:.2f} µm/px).',
           font=small, fill=(120, 110, 100))
    d.text((tx + 4, H - 48), 'Data: Vesuvius Challenge - CT Scans of Herculaneum Papyri (Angelotti et al.), CC BY-NC 4.0.',
           font=small, fill=(120, 110, 100))
    # 5 mm scale bar under the scroll
    L = 5000 / UM_PX * s
    bx, by = W - L - 70, H - 58
    d.rectangle([bx, by, bx + L, by + 6], fill=(255, 236, 200))
    d.text((bx + L / 2, by + 12), '5 mm', font=small, fill=(230, 214, 190), anchor='mt')
    canvas.save(a.out, optimize=True)
    print(a.out, canvas.size, os.path.getsize(a.out) // 1024, 'KB')


if __name__ == '__main__':
    main()
