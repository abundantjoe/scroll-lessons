# Provenance: Project HERCULES | owner the owner | [id removed]
"""Planted-fault test on real organizer meshes (task contam item 4).

For each archive-known re-trace (training segment T, other segment E), the
evaluation rectangle R (2136 x 2136 canvas px = 2 x 2 cm at 9.362 um) is
placed BY CODE on E, centred on the strip of E that the same-papyrus table
(units JSON) found shared with T. A FL-09 certificate of R against a registry
holding T must FAIL; a patch-level variant (one 128 x 128 px training patch
inside T's side of the strip) must FAIL too. A control R on the segment
farthest (3-D) from T must PASS. Mesh geometry only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam3d as C  # noqa: E402

from hercules.geometry.tifxyz import read_tifxyz  # noqa: E402

SIDE = 2136.0  # 2 cm at 9.362 um (canvas px)
CASES = [("w045", "w046"), ("w025", "w024"), ("w047", "w048"), ("w052", "w053")]


def find(names, key):
    m = [n for n in names if f"-{key}_" in n]
    if len(m) != 1:
        raise SystemExit(f"{key}: {m}")
    return m[0]


def square_at(cx, cy, W, H, side=SIDE):
    x0 = min(max(0.0, cx - side / 2), max(0.0, W - side))
    y0 = min(max(0.0, cy - side / 2), max(0.0, H - side))
    return [round(x0), round(y0), round(x0 + side), round(y0 + side)]


def canvas_wh(mdir):
    m = read_tifxyz(mdir)
    return m.shape[1] / m.scale[0], m.shape[0] / m.scale[1], m


def write_registry(path, man, patches, checkpoint):
    vox = float(man["volume_metadata"]["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    reg = {"provenance": C.PROVENANCE, "checkpoint": checkpoint,
           "frame": {"scroll": man["scroll"], "volume_id": man["canvas_volume"], "voxel_size_mm": vox},
           "patches": patches}
    Path(path).write_text(json.dumps(reg, indent=1) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--units", required=True)
    ap.add_argument("--meshes", default="/work/sib_contam/meshes")
    ap.add_argument("--work", default="/work/sib_contam/planted")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--with-retraces", action="store_true", help="also run case 1 with all re-traces expanded")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    man = json.loads(Path(a.manifest).read_text())
    units = json.loads(Path(a.units).read_text())
    root = Path(a.meshes) / man["scroll"]
    names = [s for s, r in man["segments"].items() if r["status"] == "ok"]
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    pairs = {(p["a"], p["b"]): p for p in units["pairs_tested"]}
    results = []

    def run(label, reg_path, seg, rect, expect_pass, retr=None):
        region = {"segment": seg, "mesh_dir": str(root / seg), "rect_px": rect, "volume_id": man["canvas_volume"]}
        t0 = time.time()
        c = C.fl09_certificate(reg_path, region, workers=a.workers, base_dir="/", retrace_meshes=retr)
        p = c["primary_halo_inplane"]
        r = dict(label=label, region_segment=seg, rect_px=rect, expect_pass=expect_pass, passed=c["passed"],
                 caught=(c["passed"] == expect_pass), raw_min=p["raw_min"], certified_min=p["certified_min"],
                 n_offending=p["n_offending_train_samples"], alt_scalar_passed=c["passed_alt_scalar"],
                 registry_sha256=c["registry_sha256"], region_mesh_sha256=c["region"]["mesh_sha256"],
                 n_training_surfaces=c["n_training_surfaces"], first_offending=p["offending"][:3],
                 elapsed_s=round(time.time() - t0, 1))
        print(json.dumps({k: r[k] for k in ("label", "passed", "caught", "raw_min", "certified_min", "n_offending",
                                             "elapsed_s")}), flush=True)
        results.append(r)

    for tkey, ekey in CASES:
        T, E = find(names, tkey), find(names, ekey)
        pr = pairs.get((T, E)) or pairs.get((E, T))
        # FL-09 is a distance test: the pair need not be SAME, only close; R goes on the
        # strip of E within 2 vox (normal distance) of T
        if pr is None or not (pr["a_in_b"].get("strip_canvas_bbox_on_a") and pr["b_in_a"].get("strip_canvas_bbox_on_b")):
            results.append(dict(label=f"{tkey}->{ekey}", error="no shared/contact strip in units table"))
            print("SKIP", tkey, ekey, "no strip", flush=True)
            continue
        # R centre = median canvas position of E's samples on T's papyrus (normal
        # distance < 2 vox within 6 vox), i.e. on the strip itself, not its bbox centre
        Tfull = C.dense_from_mesh(read_tifxyz(root / T), 5)
        Efull = C.dense_from_mesh(read_tifxyz(root / E), 5)
        lo, hi = Tfull.points.min(0) - 6, Tfull.points.max(0) + 6
        m = np.all((Efull.points >= lo) & (Efull.points <= hi), axis=1)
        Es = Efull.subset(m)
        ndE = C.normal_distances(Es, Tfull, workers=a.workers)
        on = ndE < 2.0
        if not on.any():
            results.append(dict(label=f"{tkey}->{ekey}", error="no E sample within 2 vox (normal) of T"))
            continue
        cx, cy = np.median(Es.canvas[on], axis=0)
        W, H, _ = canvas_wh(root / E)
        rect = square_at(cx, cy, W, H)
        # (a) whole training segment
        rp = work / f"reg_{tkey}_whole.json"
        write_registry(rp, man, [dict(id=f"{tkey}_whole", segment=T, mesh_dir=str(root / T),
                                      mesh_sha256=C.mesh_hashes(root / T), rect_px=None,
                                      label_source="planted-fault")], f"planted {tkey} whole")
        run(f"{tkey}(whole, training) -> R on {ekey} strip [pair SAME(nd)={pr['same']}]", rp, E, rect,
            expect_pass=False)
        # (b) one 128 px training patch: T's samples on the papyrus of R (normal
        # distance < 2 vox), patch centred at their median canvas position
        Ed = C.dense_from_mesh(read_tifxyz(root / E), 5, rect_px=rect)
        lo, hi = Ed.points.min(0) - 6, Ed.points.max(0) + 6
        mT = np.all((Tfull.points >= lo) & (Tfull.points <= hi), axis=1)
        Ts = Tfull.subset(mT)
        ndT = C.normal_distances(Ts, Ed, workers=a.workers)
        cand = ndT < 2.0
        if not cand.any():
            results.append(dict(label=f"{tkey} patch -> {ekey}", error="no T sample within 2 vox (normal) of R"))
        else:
            cx, cy = np.median(Ts.canvas[cand], axis=0)
            prect = [round(cx - 64), round(cy - 64), round(cx + 64), round(cy + 64)]
            rp2 = work / f"reg_{tkey}_patch.json"
            write_registry(rp2, man, [dict(id=f"{tkey}_patch", segment=T, mesh_dir=str(root / T),
                                           mesh_sha256=C.mesh_hashes(root / T), rect_px=prect,
                                           label_source="planted-fault")], f"planted {tkey} 128px patch")
            run(f"{tkey}(128px patch {prect}) -> R on {ekey} strip", rp2, E, rect, expect_pass=False)
        del Tfull, Efull, Es, Ts, Ed
    # control: the segment farthest from w045 (raw vertices), R at its valid centre
    T = find(names, "w045")
    rawT = C.raw_vertices(read_tifxyz(root / T).points)
    tT = cKDTree(rawT)
    best = None
    for s in names:
        if s == T:
            continue
        rs = C.raw_vertices(read_tifxyz(root / s).points)
        dmin = float(tT.query(rs, k=1, eps=0.0, distance_upper_bound=600.0)[0].min())
        if best is None or dmin > best[1]:
            best = (s, dmin)
    s, dmin = best
    W, H, m = canvas_wh(root / s)
    rr, cc = np.nonzero(m.valid)
    rect = square_at(cc.mean() / m.scale[0], rr.mean() / m.scale[1], W, H)
    run(f"control: w045(whole) -> R on farthest segment {s.split('-')[1][:4]} (raw min {dmin:.0f} vox)",
        work / "reg_w045_whole.json", s, rect, expect_pass=True)
    if a.with_retraces:
        retr = {x: str(root / x) for x in names}
        c1 = [r for r in results if r["label"].startswith("w045(whole")][0]
        run("w045(whole)+all re-traces -> R on w046 strip", work / "reg_w045_whole.json",
            c1["region_segment"], c1["rect_px"], expect_pass=False, retr=retr)
        run("control w045(whole)+all re-traces -> farthest", work / "reg_w045_whole.json", s, rect,
            expect_pass=True, retr=retr)
    out = {"provenance": C.PROVENANCE, "manifest_sha256": C.sha256_file(a.manifest),
           "units_sha256": C.sha256_file(a.units), "rule": "FL-09 primary (R + 64 px halo >= 128 vox, certified)",
           "results": results,
           "all_caught": all(r.get("caught", False) for r in results)}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print("all_caught", out["all_caught"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
