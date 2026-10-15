#!/usr/bin/env python
"""contact_sheet.py -- pixel-exact panel drawing shared by the read step (5.10) and review sheets (5.12).

A panel shows a map AS STORED (uint8 grey 0..255, no stretch); large maps are shown 1:f by an integer-factor area
resample and the factor is stated. The footer of every panel carries a 1 cm bar of exactly round(10000 / um_shown)
px in a unique colour (BAR_BGR) and the um/px text, so a reader (or a test) can measure it in the PNG.
"""
import math
import numpy as np
import cv2

BAR_BGR = (0, 200, 255)       # amber; not producible by grey panels, the +-margin ramp, circles or white text
TEXT_BGR = (255, 255, 255)
CIRCLE_BGR = (0, 255, 0)
INVALID_BGR = (80, 80, 80)
BG = (20, 20, 20)
HEADER_H, FOOTER_H, GAP, TITLE_H = 36, 48, 12, 60
FONT = cv2.FONT_HERSHEY_SIMPLEX


def bar_px(um):
    """1 cm in pixels at `um` micrometres per pixel: round(10000 / um)."""
    return int(round(10000.0 / float(um)))


def downsample_factor(shape, max_panel_px):
    """Smallest integer f with max(H, W) / f <= max_panel_px."""
    return max(1, int(math.ceil(max(shape[0], shape[1]) / float(max_panel_px))))


def shown(img, f):
    """Display copy at 1:f (integer f) by area resample; f = 1 returns the array unchanged."""
    if f == 1:
        return img
    h, w = img.shape[:2]
    return cv2.resize(img, (max(1, int(round(w / f))), max(1, int(round(h / f)))), interpolation=cv2.INTER_AREA)


def gray_to_bgr(g):
    return cv2.cvtColor(np.ascontiguousarray(g, dtype=np.uint8), cv2.COLOR_GRAY2BGR)


def put(img, text, x, y, scale=0.55, color=TEXT_BGR):
    cv2.putText(img, text, (int(x), int(y)), FONT, scale, color, 1, cv2.LINE_AA)


def margin_image(table, map_shape, f, vmax=0.20):
    """Per-unit forward - reverse as blocks (blue < 0 < red, +-vmax, invalid grey) at 1:f, flagged units circled."""
    side, margin, valid, flagged = table["side"], table["margin"], table["valid"], table["flagged"]
    oy, ox = table.get("origin", (0, 0))
    R, C = margin.shape
    blocks = np.zeros((max(R, 1), max(C, 1), 3), np.uint8)
    blocks[:] = INVALID_BGR
    for r in range(R):
        for c in range(C):
            if not valid[r, c]:
                continue
            v = float(np.clip(margin[r, c] / vmax, -1.0, 1.0))
            g = int(round(255 * (1 - abs(v))))
            blocks[r, c] = (g, g, 255) if v >= 0 else (255, g, g)   # BGR: red for positive, blue for negative
    h, w = int(round(map_shape[0] / f)), int(round(map_shape[1] / f))
    img = np.zeros((h, w, 3), np.uint8)
    if R and C:
        bh, bw = int(round(R * side / f)), int(round(C * side / f))
        y0, x0 = int(round(oy / f)), int(round(ox / f))
        tile = cv2.resize(blocks, (bw, bh), interpolation=cv2.INTER_NEAREST)[:max(h - y0, 0), :max(w - x0, 0)]
        img[y0:y0 + tile.shape[0], x0:x0 + tile.shape[1]] = tile
        for r in range(R):
            for c in range(C):
                if flagged[r, c]:
                    cv2.circle(img, (int((ox + (c + 0.5) * side) / f), int((oy + (r + 0.5) * side) / f)), int(0.45 * side / f), CIRCLE_BGR, 2)
    return img


def panel(img_bgr, header, um, f):
    """Header + image + footer with the 1 cm bar. Returns (panel, bar length in PNG px)."""
    h, w = img_bgr.shape[:2]
    b = bar_px(float(um) * f)
    W = max(w, b + 16, 520)
    out = np.zeros((HEADER_H + h + FOOTER_H, W, 3), np.uint8)
    out[:] = BG
    out[HEADER_H:HEADER_H + h, :w] = img_bgr
    put(out, header, 6, 24)
    y = HEADER_H + h + 12
    cv2.rectangle(out, (8, y), (8 + b - 1, y + 7), BAR_BGR, -1)   # inclusive corners: exactly b px wide
    txt = "1 cm = %d px @ %.3f um/px" % (b, float(um) * f)
    if f != 1:
        txt += "  (map %.3f um/px, shown 1:%d)" % (float(um), f)
    put(out, txt, 8, HEADER_H + h + 38, 0.5)
    return out, b


def assemble(panels, title_lines):
    """Panels side by side under a title strip."""
    H = max(p.shape[0] for p in panels)
    W = sum(p.shape[1] for p in panels) + GAP * (len(panels) - 1)
    sheet = np.zeros((TITLE_H + H, W, 3), np.uint8)
    sheet[:] = BG
    x = 0
    for p in panels:
        sheet[TITLE_H:TITLE_H + p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + GAP
    for i, line in enumerate(title_lines):
        put(sheet, line, 8, 24 + 26 * i, 0.7)
    return sheet


def bar_run_lengths(png_path):
    """Longest horizontal run of BAR_BGR pixels in each image row that has one (for verifying a sheet)."""
    img = cv2.imread(png_path, cv2.IMREAD_COLOR)
    hit = np.all(img == np.array(BAR_BGR, np.uint8), axis=2)
    runs = []
    for row in hit:
        if not row.any():
            continue
        padded = np.concatenate(([0], row.astype(np.int8), [0]))
        d = np.diff(padded)
        runs.append(int((np.nonzero(d == -1)[0] - np.nonzero(d == 1)[0]).max()))
    return runs
