"""Command line: predict the reading orientation of every tifxyz mesh in a folder.

    handcheck MESH_FOLDER --left-handed false --top-to-bottom true [--umbilicus U.json] [--out out.json]

For each ``*.tifxyz`` directory (or any directory holding x.tif, y.tif, z.tif) under
MESH_FOLDER, it prints one JSON line. The line gives the decision for reading the grid as
stored (u = column right, v = row down): state, confidence, mirror_u (flip columns),
flip_v (flip rows) and the flags.

Volume facts come from the volume's catalogue entry. Pass them explicitly:
  --left-handed        the volume's ``left_handed_coordinates`` (true / false / unknown)
  --top-to-bottom      the volume's ``z_direction_is_top_to_bottom`` (true / false / unknown)
  --axes               the zarr axis order (default z,y,x)
  --umbilicus          JSON with ``control_points`` [{x, y, z}, ...] in the SAME volume frame
  --fragment-text-side for fragments: the ``text_side`` value (e.g. -y)

Without --umbilicus, only the mesh's own normal-line centre is used, which is valid only if
it is well conditioned. The frame check (is the mesh on the scroll in this volume?) needs CT
access, so it is not run here; the output carries the flag "frame not checked". Check it
before trusting a decision.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from . import rule as HR
from .level_mesh import CentreCurve
from .tifxyz import read_tifxyz


def _tri(s: str):
    s = s.strip().lower()
    return {"true": True, "false": False, "unknown": None, "null": None, "none": None}[s]


def find_meshes(root: Path) -> list[Path]:
    if (root / "x.tif").exists():
        return [root]
    return sorted({p.parent for p in root.rglob("x.tif") if (p.parent / "y.tif").exists() and (p.parent / "z.tif").exists()})


def load_umbilicus(path: Path) -> CentreCurve:
    cp = json.loads(path.read_text())["control_points"]
    P = np.array([[c["x"], c["y"], c["z"]] for c in cp], float)
    o = np.argsort(P[:, 2])
    return CentreCurve(z=P[o, 2], x=P[o, 0], y=P[o, 1])


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else round(float(o), 4)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def decide(mesh_dir: Path, volume: HR.VolumeInfo) -> dict:
    m = read_tifxyz(mesh_dir)
    d = HR.orient_for_reading(m.points.astype(np.float64), volume)
    return _clean(dict(mesh=mesh_dir.name, state=d.state, confidence=d.confidence, readable=d.readable,
                       convention_sign=d.convention_sign, chirality=d.chirality, mirror_u=d.mirror_u,
                       flip_v=d.flip_v, rot180_equivalent=d.rot180_equivalent, reversed_frac=d.reversed_frac,
                       sources=d.sources, flags=d.flags))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="handcheck", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--left-handed", type=_tri, required=True)
    ap.add_argument("--top-to-bottom", type=_tri, default=None)
    ap.add_argument("--axes", default="z,y,x")
    ap.add_argument("--umbilicus", type=Path)
    ap.add_argument("--fragment-text-side")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    zattrs = {"multiscales": [{"axes": [{"name": n.strip()} for n in a.axes.split(",")]}]}
    props = {"left_handed_coordinates": a.left_handed, "z_direction_is_top_to_bottom": a.top_to_bottom}
    frag = a.fragment_text_side is not None
    if frag:
        props["text_side"] = a.fragment_text_side
    vi = HR.VolumeInfo.from_metadata(zattrs, props, sample_type="fragment" if frag else "scroll",
                                     umbilicus=load_umbilicus(a.umbilicus) if a.umbilicus else None)
    meshes = find_meshes(a.folder)
    if not meshes:
        print(f"no tifxyz mesh under {a.folder}", file=sys.stderr)
        return 2
    rows = []
    for md in meshes:
        r = decide(md, vi)
        rows.append(r)
        print(json.dumps(r), flush=True)
    if a.out:
        a.out.write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
