"""Reproduce the planted-glyph validation (numbers only).

A font glyph (R or K) is planted on the recto of one winding of a synthetic spiral scroll.
There are 32 cases: 2 glyphs x 4 volume frames (ascending, rotated 180 degrees about x,
reflected in z, reflected in x; the reflections flip the frame parity) x 4 grid
parameterisations (as traced, columns reversed, rows reversed, both).

For each case the mesh is levelled, the rule decides the flips, and a render along the normals
is scored against the glyph and its mirror image (normalised cross-correlation). The
wrong-sign control applies the opposite mirror decision to the same case.

    python -m handcheck.validate [--out validation.json]
"""
from __future__ import annotations

import argparse
import dataclasses
import json

import cv2
import numpy as np

from . import level_mesh as L
from . import render_synth as RS
from . import rule as HR
from . import synth as S
from . import tifxyz as T

SHAPE, CENTRE, PIX, Z_C, PHI_G, K_G, MARGIN = (110, 140, 140), (70.0, 70.0), 1.5, 55.0, np.radians(35.0), 1, 0.2
KINDS = ["ascending", "rot180x", "reflect_z", "reflect_x"]
PFLIPS = ["none", "u", "v", "uv"]


def _score(img, tpl):
    return float(cv2.matchTemplate(np.nan_to_num(np.asarray(img, np.float32)), tpl.astype(np.float32),
                                   cv2.TM_CCOEFF_NORMED).max())


def _grid(sp, n=44, angle_deg=30.0):
    a = np.radians(angle_deg)
    uc = vc = (n - 1) / 2
    s0 = -PIX * (uc * np.cos(a) - vc * np.sin(a))
    z0 = Z_C - PIX * (uc * np.sin(a) + vc * np.cos(a))
    return S.spiral_sheet_grid(sp, K_G, (n, n), PIX, angle_deg, s0=s0, z0=z0, phi_ref=PHI_G)


def run() -> dict:
    sp = S.Spiral(centre=CENTRE, r_outer=62.0, pitch=9.0, turns=4.5, phi_start=np.radians(-20.0), w=1)
    cases = []
    for ch in ("R", "K"):
        g = S.font_glyph(ch)
        sc = S.spiral_glyph_volume(SHAPE, sp, g, k_glyph=K_G, phi_g=PHI_G, z_c=Z_C, pix=PIX)
        for kind in KINDS:
            for pf in PFLIPS:
                src = _grid(sc.spiral)
                if "u" in pf:
                    src = np.ascontiguousarray(src[:, ::-1])
                if "v" in pf:
                    src = np.ascontiguousarray(src[::-1])
                vol, pts, props = S.transform_scene(sc.vol, src, kind)
                lv = L.level_mesh(pts, step_vox=PIX)
                vi = HR.VolumeInfo.from_metadata(S.ZATTRS_ZYX, props, centroid=S.centroid_curve_from_volume(vol))
                d = HR.orient_for_reading(lv.points, vi, frame=HR.FrameCheck(0.0, 0.0))
                row = dict(glyph=ch, frame=kind, grid_flip=pf, state=d.state, confidence=d.confidence,
                           mirror_u=d.mirror_u, flip_v=d.flip_v)
                for name, dec in (("rule", d), ("wrong_sign", dataclasses.replace(d, mirror_u=not d.mirror_u))):
                    p = dec.apply(lv.points)
                    img = RS.render_along_normals(vol, p, T.vertex_normals(p), n=5).mean(0)
                    s = dict(id=_score(img, g), lr=_score(img, np.fliplr(g)))
                    row[name] = dict(scores={k: round(v, 4) for k, v in s.items()},
                                     unmirrored=bool(s["id"] > s["lr"] + MARGIN),
                                     mirrored=bool(s["lr"] > s["id"] + MARGIN))
                cases.append(row)
    rule_ok = sum(c["rule"]["unmirrored"] for c in cases)
    wrong_mirrored = sum(c["wrong_sign"]["mirrored"] for c in cases)
    return dict(n_cases=len(cases), rule_reads_unmirrored=rule_ok, wrong_sign_reads_mirrored=wrong_mirrored,
                margin=MARGIN, min_rule_margin=round(min(c["rule"]["scores"]["id"] - c["rule"]["scores"]["lr"] for c in cases), 4),
                cases=cases)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    r = run()
    print(json.dumps({k: v for k, v in r.items() if k != "cases"}))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(r, f, indent=1)
    return 0 if r["rule_reads_unmirrored"] == r["n_cases"] and r["wrong_sign_reads_mirrored"] == r["n_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
