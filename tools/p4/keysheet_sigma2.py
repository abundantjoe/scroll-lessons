# Provenance: Project HERCULES | owner the owner | [id removed]
"""Key sheet v2 (RULES.md DECL-P4-2-A2): the METRIC-HASH-12 key-sheet spec (1068 x 1068 px, Greek capitals rendered in
DejaVu Serif Bold, black on white, each labelled below with its Latin name in DejaVu Sans) with BOTH sigma forms:
the 24 capitals of the original sheet (lunate sigma in sigma's place) plus the four-bar capital sigma, 25 glyphs on a
5 x 5 grid in Greek alphabetical order, the two sigma forms side by side. Deterministic; written with
hercules.display.builder.png_bytes (IHDR/IDAT/IEND only). The generator never displays the sheet.
Usage: python tools/p4/keysheet_sigma2.py <out.png>
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, 'src')
from hercules.display.builder import png_bytes  # noqa: E402

SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
GLYPHS = [('Α', 'alpha'), ('Β', 'beta'), ('Γ', 'gamma'), ('Δ', 'delta'), ('Ε', 'epsilon'),
          ('Ζ', 'zeta'), ('Η', 'eta'), ('Θ', 'theta'), ('Ι', 'iota'), ('Κ', 'kappa'),
          ('Λ', 'lambda'), ('Μ', 'mu'), ('Ν', 'nu'), ('Ξ', 'xi'), ('Ο', 'omicron'),
          ('Π', 'pi'), ('Ρ', 'rho'), ('Ϲ', 'sigma (lunate)'), ('Σ', 'sigma (four-bar)'),
          ('Τ', 'tau'), ('Υ', 'upsilon'), ('Φ', 'phi'), ('Χ', 'chi'), ('Ψ', 'psi'),
          ('Ω', 'omega')]
SIZE, N = 1068, 5


def render():
    img = Image.new('L', (SIZE, SIZE), 255)
    d = ImageDraw.Draw(img)
    fg, fn = ImageFont.truetype(SERIF, 120), ImageFont.truetype(SANS, 22)
    cell = SIZE // N
    for i, (ch, name) in enumerate(GLYPHS):
        r, c = divmod(i, N)
        cx, cy = c * cell + cell // 2, r * cell + cell // 2
        d.text((cx, cy - 18), ch, font=fg, fill=0, anchor='mm')
        d.text((cx, cy + 72), name, font=fn, fill=0, anchor='mm')
    a = np.asarray(img, dtype=np.uint8)
    assert a.shape == (SIZE, SIZE)
    return a


if __name__ == '__main__':
    b = png_bytes(render())
    with open(sys.argv[1], 'xb') as fh:
        fh.write(b)
    import hashlib
    print(hashlib.sha256(b).hexdigest())
