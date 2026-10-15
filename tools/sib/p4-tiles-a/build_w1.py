"""DECL-P4-17-A1 P4-W "block" windows on M1 (batch w1). Numbers and PNG bytes only.

Provenance: Project HERCULES | owner the owner | [id removed]

Never opens, views or prints image pixels.
- Grid: strip-a (20260701183124-w010-027 canvas, T = 8343, origin (0,0)).
- Window (r, c) = tiles (r..r+1, c..c+1) = canvas rows [rT, (r+2)T), cols [cT, (c+2)T) = 4 x 4 cm.
- Display: raw uint8 prediction, 0 outside mesh-valid (grid mask from z.tif != -1, nearest neighbour
  x20), builder.area_downscale (cv2.INTER_AREA) to 1068 x 1068, builder.png_bytes (IHDR/IDAT/IEND).
- Files: tiles/<uuid4>.png; the uuid -> (r, c) key is this manifest (builder file).
- frac_valid: mesh-valid fraction of the window's canvas pixels.
- Labelled distance: min over the window's 4 tiles of p4-excl excl_a.json (npz points and the
  all-vertex check); labelled_adjacent = union flag of any tile (fail-closed), i.e. min < 1.2 mm.

Usage: python build_w1.py <prediction.tif> <z.tif> <excl_a.json> <out_dir> <excl_a_sha256>
"""
import hashlib
import json
import os
import struct
import sys
import uuid

import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from hercules.display import builder  # noqa: E402
from tile_w010_027 import TiledReader, canvas_mask  # noqa: E402

PROV = "Project HERCULES | owner the owner | [id removed]"
T = 8343
PX_PER_MM = 417.1314650253318
WINDOWS = [((0, 15), "title"), ((0, 16), "title"), ((2, 15), "title"), ((3, 12), "title"),
           ((1, 15), "title"), ((2, 16), "title"), ((0, 18), "title"), ((4, 15), "title"),
           ((0, 5), "control"), ((2, 5), "control"), ((0, 7), "control"), ((2, 7), "control"),
           ((4, 3), "control"), ((4, 5), "control"), ((4, 18), "blank_end_null")]


def chunks(b):
    i, out = 8, []
    while i < len(b):
        n = struct.unpack(">I", b[i:i + 4])[0]
        out.append((b[i + 4:i + 8].decode(), b[i + 8:i + 8 + n]))
        i += 12 + n
    return out


def main():
    pred, zt, exclp, out, excl_sha = sys.argv[1:6]
    rd = TiledReader(pred)
    Z = tifffile.imread(zt)
    valid = Z != -1
    excl = json.load(open(exclp))["tiles"]
    os.makedirs(os.path.join(out, "tiles"), exist_ok=True)
    tiles = []
    for order, ((r, c), role) in enumerate(WINDOWS):
        y0, y1, x0, x1 = r * T, (r + 2) * T, c * T, (c + 2) * T
        m = canvas_mask(valid, rd.H, rd.W, y0, y1, x0, x1)
        crop = builder.model_map_u8(rd.read(y0, y1, x0, x1))
        nz_out = float((crop[~m] > 0).mean()) if (~m).any() else 0.0
        vals = crop[m]
        crop[~m] = 0
        disp = builder.area_downscale(crop, 1068 / (2 * T))
        assert disp.shape == (1068, 1068) and disp.dtype == np.uint8
        b = builder.png_bytes(disp)
        ch = chunks(b)
        assert b[:8] == b"\x89PNG\r\n\x1a\n" and {k for k, _ in ch} <= {"IHDR", "IDAT", "IEND"}
        assert struct.unpack(">IIBB", ch[0][1][:10]) == (1068, 1068, 8, 0)
        name = "%s.png" % uuid.uuid4()
        with open(os.path.join(out, "tiles", name), "xb") as f:
            f.write(b)
        ts = ["r%d_c%d" % (r + a, c + bb) for a in (0, 1) for bb in (0, 1)]
        d = []
        for k in ts:
            e = excl[k]
            d.append(min(e["min_mm"], (e.get("all_vertex") or {}).get("min_mm", np.inf)))
        adj = any(excl[k].get("labelled_adjacent_union", excl[k]["labelled_adjacent"]) for k in ts)
        tiles.append({"r": r, "c": c, "order": order, "role": role, "file": "tiles/" + name,
                      "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                      "valid_fraction": float(m.mean()), "frac_valid": float(m.mean()),
                      "canvas_rows": [y0, y1], "canvas_cols": [x0, x1], "tiles_covered": ts,
                      "min_dist_labelled_mm": float(min(d)),
                      "min_dist_labelled_mm_per_tile": dict(zip(ts, [float(v) for v in d])),
                      "labelled_adjacent": bool(adj or min(d) < 1.2),
                      "stats": {"mean_valid": float(vals.mean()), "std_valid": float(vals.std()),
                                "frac_ge_150_valid": float((vals >= 150).mean()),
                                "raw_nonzero_outside_valid_frac": nz_out}})
        print(r, c, role, "vf=%.3f" % m.mean(), "d=%.3f" % min(d), "adj=%s" % tiles[-1]["labelled_adjacent"], flush=True)
    man = {"provenance": PROV, "batch": "w1", "declaration": "RULES.md DECL-P4-17-A1",
           "segment": "20260701183124-w010-027",
           "material": "M1: official 20260417190342 prediction on 20260411134726 (sha256 in downloads.jsonl)",
           "grid": "strip-a (T 8343, origin (0,0)); window = 2 x 2 tiles = 16686 canvas px = 4 x 4 cm",
           "px_per_mm": PX_PER_MM, "T_px": T, "window_px": 2 * T, "display_px": 1068,
           "display_px_per_mm": 1068 / (2 * T / PX_PER_MM),
           "display": "raw uint8 prediction, 0 outside mesh-valid, cv2.INTER_AREA to 1068 x 1068 (builder.area_downscale), builder.png_bytes; IHDR/IDAT/IEND only",
           "naming": "tiles/<uuid4>.png; key uuid -> (r, c) is this manifest only",
           "labelled_distance_source": "origin/claude/gifted-bell-gavnl5-sib-p4-excl logs/sib/p4-excl/excl_a.json sha256 %s (per tile: min of npz-point and all-vertex min_mm; flag = any tile labelled_adjacent_union or window min < 1.2 mm)" % excl_sha,
           "null_note": "rot-90 null copies are drawn by the harness (DECL-P4-17-A1 item 1, seed 20260927); (4,18) is the blank-end descriptive null window",
           "tiles": tiles}
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print("DONE", len(tiles), "unique sha", len({t["png_sha256"] for t in tiles}))


if __name__ == "__main__":
    main()
