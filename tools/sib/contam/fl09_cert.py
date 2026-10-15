# Provenance: Project HERCULES | owner the owner | [id removed]
"""FL-09 certificate generator (SG item 8) and registry builder.

  make-registry: write a training-patch registry JSON. Patches are given as
      segment[:x0,y0,x1,y1] (canvas px; no rect = the whole segment, the
      conservative superset when a checkpoint's patch-level registry is not
      available) with a label source (human:<set> or model:<id>).
  cert: certify a candidate rectangle R against a registry; writes JSON with
      the 3-D KD-tree distances (raw and certified), offending points, the
      registry sha256 and every mesh sha256.

Mesh geometry only; nothing else is read.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam3d as C  # noqa: E402


def make_registry(a) -> int:
    man = json.loads(Path(a.manifest).read_text())
    vox = float(man["volume_metadata"]["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    root = Path(a.meshes) / man["scroll"]
    extra = dict(e.split("=", 1) for e in a.extra)
    patches = []
    for i, spec in enumerate(a.patch):
        seg, _, rect = spec.partition(":")
        full = [s for s in list(man["segments"]) + list(extra) if seg in s]
        if len(full) != 1:
            raise SystemExit(f"segment '{seg}' matches {full}")
        name = full[0]
        mdir = Path(extra[name]) if name in extra else root / name
        patches.append(dict(id=f"p{i:04d}_{seg}", segment=name, mesh_dir=str(mdir),
                            mesh_sha256=C.mesh_hashes(mdir),
                            rect_px=[float(v) for v in rect.split(",")] if rect else None,
                            label_source=a.label_source[i] if i < len(a.label_source) else a.label_source[-1]))
    reg = {"provenance": C.PROVENANCE, "checkpoint": a.checkpoint,
           "frame": {"scroll": man["scroll"], "volume_id": man["canvas_volume"], "voxel_size_mm": vox},
           "note": a.note, "patches": patches}
    Path(a.out).write_text(json.dumps(reg, indent=1) + "\n")
    print("registry", a.out, "sha256", C.sha256_file(a.out), "patches", len(patches))
    return 0


def cert(a) -> int:
    t0 = time.time()
    reg = json.loads(Path(a.registry).read_text())
    rect = [float(v) for v in a.rect.split(",")]
    region = {"segment": a.segment, "mesh_dir": a.mesh_dir, "rect_px": rect, "volume_id": reg["frame"]["volume_id"]}
    retr = None
    if a.retrace_manifest:
        man = json.loads(Path(a.retrace_manifest).read_text())
        root = Path(a.meshes) / man["scroll"]
        retr = {s: str(root / s) for s, r in man["segments"].items() if r["status"] == "ok"}
        retr.update(dict(e.split("=", 1) for e in a.extra))
    out = C.fl09_certificate(a.registry, region, min_vox=a.min_vox, halo_px=a.halo_px, k=a.k, workers=a.workers,
                             retrace_meshes=retr, base_dir="/", slab_region_vox=a.slab_region,
                             slab_train_vox=a.slab_train)
    out["label"] = a.label
    out["elapsed_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    p, q = out["primary_halo_inplane"], out["alt_scalar_min_plus_halo"]
    print(json.dumps(dict(label=a.label, passed=out["passed"], raw_min=p["raw_min"], certified_min=p["certified_min"],
                          n_offending=p["n_offending_train_samples"], alt_passed=out["passed_alt_scalar"],
                          alt_certified=q["certified_min"], elapsed_s=round(out["elapsed_s"], 1))))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("make-registry")
    r.add_argument("--manifest", required=True)
    r.add_argument("--meshes", default="/work/sib_contam/meshes")
    r.add_argument("--extra", action="append", default=[])
    r.add_argument("--patch", action="append", required=True)
    r.add_argument("--label-source", action="append", required=True)
    r.add_argument("--checkpoint", required=True)
    r.add_argument("--note", default="")
    r.add_argument("--out", required=True)
    c = sub.add_parser("cert")
    c.add_argument("--registry", required=True)
    c.add_argument("--segment", required=True)
    c.add_argument("--mesh-dir", required=True)
    c.add_argument("--rect", required=True, help="x0,y0,x1,y1 canvas px")
    c.add_argument("--min-vox", type=float, default=128.0)
    c.add_argument("--halo-px", type=float, default=64.0)
    c.add_argument("--k", type=int, default=5)
    c.add_argument("--slab-region", type=float, default=0.0, help="render half-depth of R (vox)")
    c.add_argument("--slab-train", type=float, default=0.0, help="render half-depth of training patches (vox)")
    c.add_argument("--workers", type=int, default=4)
    c.add_argument("--retrace-manifest", default="")
    c.add_argument("--meshes", default="/work/sib_contam/meshes")
    c.add_argument("--extra", action="append", default=[])
    c.add_argument("--label", default="")
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return make_registry(a) if a.cmd == "make-registry" else cert(a)


if __name__ == "__main__":
    sys.exit(main())
