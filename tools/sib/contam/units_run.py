# Provenance: Project HERCULES | owner the owner | [id removed]
"""Same-papyrus table and papyrus units for every organizer segment of one
scroll (mesh geometry only; no ink map, label image or volume is read).

Input: the meshes fetched by fetch_meshes.py and its manifest (sha256 of
every object). Dense 5 x 5 samples are cached as .npy under --cache (not
committed). Output JSON: per-segment stats, every tested pair (both
directions, with the canvas bbox of the shared strip), the units, and the
label sources attached to each unit.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam3d as C  # noqa: E402

from hercules.geometry.tifxyz import read_tifxyz  # noqa: E402


def k_for(mesh, k_nominal: int, nominal_step: float = 20.0) -> int:
    """Densification factor giving the same sample spacing as k_nominal on the
    organizers' 20-vox grids (4 vox for 5 x 5): ceil(k_nominal * step / 20)."""
    step = max(1.0 / mesh.scale[0], 1.0 / mesh.scale[1])
    return max(1, int(np.ceil(k_nominal * step / nominal_step - 1e-9)))


class LazyDense:
    """Mapping name -> DenseSurface, cached on disk, small LRU in memory."""

    def __init__(self, dirs: dict, cache: Path, k: int, keep: int = 3):
        self.dirs, self.cache, self.k, self.keep = dirs, cache, k, keep
        self.mem: OrderedDict = OrderedDict()
        cache.mkdir(parents=True, exist_ok=True)

    def _paths(self, n):
        return {f: self.cache / f"{n}.k{self.k}.{f}.npy" for f in ("points", "normals", "canvas", "area", "h", "k")}

    def __getitem__(self, n):
        if n in self.mem:
            self.mem.move_to_end(n)
            return self.mem[n]
        ps = self._paths(n)
        if all(p.exists() for f, p in ps.items() if f != "k"):
            D = C.DenseSurface(np.load(ps["points"]).astype(np.float64), np.load(ps["normals"]).astype(np.float64),
                               np.load(ps["canvas"]).astype(np.float64), np.load(ps["area"]).astype(np.float64),
                               float(np.load(ps["h"])), self.k, n)
            D.k = int(np.load(ps["k"])) if ps["k"].exists() else self.k
        else:
            m = read_tifxyz(self.dirs[n])
            D = C.dense_from_mesh(m, k_for(m, self.k), name=n)
            for f in ("points", "normals", "canvas", "area"):
                np.save(ps[f], getattr(D, f).astype(np.float32))
            np.save(ps["h"], np.float64(D.h))
            np.save(ps["k"], np.int64(D.k))
            # float32 storage: reload so that every use sees identical values
            D = C.DenseSurface(*(np.load(ps[f]).astype(np.float64) for f in ("points", "normals", "canvas", "area")),
                               float(np.load(ps["h"])), self.k, n)
        self.mem[n] = D
        while len(self.mem) > self.keep:
            self.mem.popitem(last=False)
        return D


def strip_bbox(D: C.DenseSurface, mask) -> list | None:
    """Canvas bbox (x0, y0, x1, y1; 0.5/99.5 percentiles) of the flagged samples."""
    if mask is None or not mask.any():
        return None
    c = D.canvas[mask]
    lo, hi = np.percentile(c, 0.5, axis=0), np.percentile(c, 99.5, axis=0)
    return [round(float(lo[0])), round(float(lo[1])), round(float(hi[0])), round(float(hi[1]))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--meshes", default="/work/sib_contam/meshes")
    ap.add_argument("--cache", default="/work/sib_contam/dense")
    ap.add_argument("--extra", action="append", default=[], help="name=mesh_dir (e.g. transformed mesh-only traces)")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="comma list of segment substrings (debug)")
    a = ap.parse_args(argv)
    man = json.loads(Path(a.manifest).read_text())
    scroll = man["scroll"]
    vox_mm = float(man["volume_metadata"]["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    vox2_to_cm2 = (vox_mm / 10.0) ** 2
    dirs = {s: Path(a.meshes) / scroll / s for s, r in man["segments"].items() if r["status"] == "ok"}
    for e in a.extra:
        n, d = e.split("=", 1)
        dirs[n] = Path(d)
    if a.only:
        keys = a.only.split(",")
        dirs = {n: d for n, d in dirs.items() if any(k in n for k in keys)}
    names = sorted(dirs)
    t0 = time.time()
    raw, hraw, seg = {}, {}, {}
    for n in names:
        m = read_tifxyz(dirs[n])
        raw[n] = C.raw_vertices(m.points)
        hraw[n] = C.quad_sampling_bound(m.points)
        seg[n] = dict(grid_hw=list(m.shape), scale=list(m.scale), n_raw=int(raw[n].shape[0]), h_raw=hraw[n],
                      mesh_sha256=C.mesh_hashes(dirs[n]))
    lazy = LazyDense(dirs, Path(a.cache), a.k)
    for n in names:
        D = lazy[n]
        seg[n].update(densify_k=D.k, n_dense=D.n, h_dense=D.h, area_vox2=float(D.area.sum()),
                      area_cm2=float(D.area.sum()) * vox2_to_cm2)
        print(f"[{time.time() - t0:7.1f}s] dense {n} n={D.n} h={D.h:.3f}", flush=True)

    pairs_out = []

    def log(pr):
        print(f"[{time.time() - t0:7.1f}s] {pr.a[:32]:32s} {pr.b[:32]:32s} same={pr.same} "
              f"a_in_b={pr.ab.frac_of_a:.4f} b_in_a={pr.ba.frac_of_a:.4f} "
              f"counts={pr.ab.counts}/{pr.ba.counts}", flush=True)

    pairs = C.pairwise_same_papyrus(lazy, raw, hraw, workers=a.workers, log=log)
    # strip bboxes for SAME pairs (second pass with masks)
    for pr in pairs:
        d = pr.as_dict()
        d["a_in_b"]["area_cm2"] = pr.ab.area_within_2_vox2 * vox2_to_cm2
        d["b_in_a"]["area_cm2"] = pr.ba.area_within_2_vox2 * vox2_to_cm2
        if pr.same or pr.ab.n_within_2 > 0 or pr.ba.n_within_2 > 0:
            A, B = lazy[pr.a], lazy[pr.b]
            q = C.pair_same_papyrus(A, B, raw[pr.a], raw[pr.b], hraw[pr.a], hraw[pr.b], workers=a.workers,
                                    names=(pr.a, pr.b), keep_mask=True)
            d["a_in_b"]["strip_canvas_bbox_on_a"] = strip_bbox(A, q.ab.mask)
            d["b_in_a"]["strip_canvas_bbox_on_b"] = strip_bbox(B, q.ba.mask)
        pairs_out.append(d)
    units = C.papyrus_units(names, pairs)
    lab = {s: r.get("label_sources", {}) for s, r in man["segments"].items()}
    units_out = []
    for i, u in enumerate(units):
        hum = sorted({f"human:{x['label_set']}@{x['target']}:{m}" for m in u for x in lab.get(m, {}).get("human_ink_labels", [])})
        mod = sorted({f"model:{x['model_id']}" for m in u for x in lab.get(m, {}).get("model_ink_maps", [])})
        units_out.append(dict(unit=f"U{i:02d}", members=u, human_label_sources=hum, model_map_sources=mod,
                              area_cm2_sum=float(sum(seg[m]["area_cm2"] for m in u))))
    out = {
        "provenance": C.PROVENANCE,
        "scroll": scroll, "canvas_volume": man["canvas_volume"], "voxel_size_mm": vox_mm,
        "voxel_size_source": "volume metadata.json scan.tomo.acquisition.detector.samplePixelSize",
        "manifest_sha256": C.sha256_file(a.manifest),
        "rule": dict(densify_k=a.k, radius_vox=C.SP_RADIUS_VOX, normal_dist_vox=2.0, min_within_2=C.SP_MIN_WITHIN_2,
                     ratio_c01_over_c23=C.SP_RATIO, units="connected components of SAME (either direction); "
                     "geometry only, never segment names"),
        "segments": seg, "pairs_tested": pairs_out, "units": units_out,
        "n_pairs_tested": len(pairs_out), "n_pairs_same": int(sum(p.same for p in pairs)),
        "elapsed_s": time.time() - t0,
    }
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print("units:", len(units), "pairs tested:", len(pairs_out), "same:", out["n_pairs_same"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
