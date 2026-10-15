# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-1 benchmark driver (geometry only; no volume, image or ink model).

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/flat1_run.py [select|all] [9um|2p4um]

Variant 9um (PRIMARY, the adoption rule applies here): organizer meshes on
the 9.362 um volume 20250728140407. Variant 2p4um (SECONDARY resolution
check, declared after the first 9um mesh finished and before any 2p4um mesh
was downloaded): the organizer meshes of the SAME five segments on the
2.399 um volume 20260102150214 (same 20-voxel grid step, so 4x finer quads,
48 um instead of 187 um); rectangle drawn by the same rule on that mesh.

Fixed rules (in code before any flattening was run on real data):
* Candidates: every PHerc0139 segment folder on s3://vesuvius-challenge-open-data
  except the flatboi title segment, sorted; mesh = the organizer tifxyz
  ``<ts>-on-20250728140407-9.362um.tifxyz`` (the 9.362 um volume of our chain).
* Order: numpy default_rng(SEED).permutation(candidates); the first N_MESH
  segments that host a feasible rectangle are used.
* Levelling: hercules.geometry.level_mesh.level_mesh(points, step_vox=20,
  method="median") on the whole mesh (one rotation per mesh).
* Rectangle: flatlib.choose_rectangle with rng default_rng([SEED, crc32(id)]),
  4.00 cm^2 +-1 % 3-D area, aspect in [1, 2], every quad valid.
* Methods, in adoption order: vc_flatten (official ABF++, defaults:
  10 iterations, scale to 3-D area), SLIM (symmetric Dirichlet), ARAP.
  SLIM and ARAP start from the levelled grid itself (flip-free); Tutte
  starts are run as a sensitivity check. GRID (the levelled tifxyz as is,
  nominal step) is reported as a baseline.
* Adopt: first method with >= 93.1 % of quads within +-5 % on >= 4 of 5.
* Fallback (always computed, used only if nothing is adopted): R + 2 mm
  margin (ceil(2 mm / quad side) quads), connected component of valid quads
  containing R, SLIM; then up to 3 rounds of: drop margin quads with any
  edge outside +-5 %, keep the component containing R, re-flatten. Quads of
  R are never trimmed.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import tifffile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import flatlib as FL  # noqa: E402
from hercules.geometry import level_mesh as LM  # noqa: E402
from hercules.geometry import tifxyz as T  # noqa: E402
from hercules.pipeline.window import voxel_size_from_metadata  # noqa: E402

SEED = 20260925
N_MESH = 5
STEP_VOX = 20.0
TARGET_CM2 = 4.0
ADOPT_PCT = 93.1
ADOPT_MIN_MESHES = 4
MARGIN_MM = 2.0
TRIM_ROUNDS = 3
BUCKET = "vesuvius-challenge-open-data"
SCROLL = "PHerc0139"
VARIANTS = {  # metadata sha256 from data/catalogue/known_text.md
    "9um": ("20250728140407", "9.362um", "20250728140407-9.362um-1.2m-113keV-masked.zarr",
            "95917633ca11a1ddff2e6b7d66360c508f8158bbe05be277c8d51477befb5bae"),
    "2p4um": ("20260102150214", "2.399um", "20260102150214-2.399um-0.2m-78keV-masked.zarr",
              "c788219f290b15ba7648eba2814964a887a895f5526fd5c027a5c8fae13b56bc"),
}
VARIANT = sys.argv[2] if (__name__ == "__main__" and len(sys.argv) > 2) else "9um"
VOL_ID, VOL_TAG, _VOL_ZARR, VOL_META_SHA = VARIANTS[VARIANT]
VOL_META_KEY = f"{SCROLL}/volumes/{_VOL_ZARR}/metadata.json"
SFX = "" if VARIANT == "9um" else "_" + VARIANT
EXCLUDE = ("title_",)  # flatboi title segment: already a flattened product, 1.67 cm tall

WORK = Path("/work/flat1") if VARIANT == "9um" else Path("/work/flat1") / VARIANT
OUT = REPO / "logs/sib/flat1"
RUN_ABF = Path(__file__).resolve().parent / "run_abf.sh"
METHODS = ("vc_flatten", "slim", "arap")


def s3():
    import boto3
    import botocore

    return boto3.client("s3", config=botocore.config.Config(signature_version=botocore.UNSIGNED))


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def list_segments(c) -> list[str]:
    out, tok = [], None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=f"{SCROLL}/segments/", Delimiter="/")
        if tok:
            kw["ContinuationToken"] = tok
        r = c.list_objects_v2(**kw)
        out += [p["Prefix"].split("/")[-2] for p in r.get("CommonPrefixes", [])]
        if not r.get("IsTruncated"):
            return sorted(out)
        tok = r["NextContinuationToken"]


def fetch_mesh(c, seg: str, downloads: list) -> Path | None:
    ts = seg.split("-")[0]
    name = f"{ts}-on-{VOL_ID}-{VOL_TAG}.tifxyz"
    key = f"{SCROLL}/segments/{seg}/mesh/{name}/"
    d = WORK / "s3" / SCROLL / seg / name
    files = ("meta.json", "x.tif", "y.tif", "z.tif")
    r = c.list_objects_v2(Bucket=BUCKET, Prefix=key)
    have = {o["Key"][len(key):]: o["Size"] for o in r.get("Contents", [])}
    if not all(f in have for f in files):
        return None
    d.mkdir(parents=True, exist_ok=True)
    for f in files:
        p = d / f
        if not p.exists() or p.stat().st_size != have[f]:
            for i in range(5):
                try:
                    c.download_file(BUCKET, key + f, str(p))
                    break
                except Exception:  # network retry
                    time.sleep(2 ** i)
        downloads.append({"key": key + f, "size": p.stat().st_size, "sha256": sha256_file(p)})
    return d


def voxel_um(c) -> tuple[float, str]:
    p = WORK / "s3" / f"vol0139_{VOL_ID}_metadata.json"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(c.get_object(Bucket=BUCKET, Key=VOL_META_KEY)["Body"].read())
    h = sha256_file(p)
    if h != VOL_META_SHA:
        raise RuntimeError(f"volume metadata sha256 {h} != catalogue {VOL_META_SHA}")
    return voxel_size_from_metadata(p), h


# ---------------------------------------------------------------------------
# stage 1: selection
# ---------------------------------------------------------------------------

def select() -> dict:
    c = s3()
    vox, vh = voxel_um(c)
    segs = list_segments(c)
    cands = [s for s in segs if not any(e in s for e in EXCLUDE)]
    order = [cands[i] for i in np.random.default_rng(SEED).permutation(len(cands))]
    if VARIANT != "9um":  # secondary: exactly the primary's five segments, same order
        order = [c["segment"] for c in json.loads((OUT / "selection.json").read_text())["chosen"]]
    downloads, chosen, skipped = [], [], []
    for seg in order:
        if len(chosen) == N_MESH:
            break
        d = fetch_mesh(c, seg, downloads)
        if d is None:
            skipped.append({"segment": seg, "reason": f"no {VOL_TAG} tifxyz"})
            continue
        m = T.read_tifxyz(d)
        lev = LM.level_mesh(m.points, step_vox=STEP_VOX, method="median")
        rng = np.random.default_rng([SEED, zlib.crc32(seg.encode())])
        rect = FL.choose_rectangle(lev.points, vox, STEP_VOX, rng, target_cm2=TARGET_CM2)
        if rect is None:
            skipped.append({"segment": seg, "reason": "no feasible 4 cm^2 rectangle"})
            continue
        lp = WORK / "levelled" / f"{seg}.npy"
        lp.parent.mkdir(parents=True, exist_ok=True)
        np.save(lp, lev.points)
        src_area = T.area_cm2(m.points, vox)
        chosen.append({
            "segment": seg, "mesh_dir": str(d), "source_grid_shape": list(m.points.shape[:2]),
            "source_scale": list(m.scale), "source_area_cm2": src_area,
            "level_angle_deg": lev.angle_deg, "level_spread_deg": lev.spread_deg,
            "level_metric_vox_per_unit": list(lev.metric), "levelled_grid_shape": list(lev.points.shape[:2]),
            "levelled_npy": str(lp), "levelled_npy_sha256": sha256_file(lp), "rect": rect,
        })
    sel = {"seed": SEED, "voxel_um": vox, "volume_metadata_sha256": vh, "volume_metadata_key": VOL_META_KEY,
           "n_segments_listed": len(segs), "candidates": cands, "order": order, "chosen": chosen,
           "skipped": skipped, "downloads": downloads}
    (OUT / f"selection{SFX}.json").write_text(json.dumps(sel, indent=1))
    return sel


# ---------------------------------------------------------------------------
# stage 2: flattening
# ---------------------------------------------------------------------------

def geometry_diagnostics(points: np.ndarray) -> dict:
    """Intrinsic non-developability: angle defects at interior vertices
    (2 pi - angle sum) = discrete Gaussian curvature x area."""
    m = FL.grid_to_mesh(points)
    ang = FL._tri_angles(m.V[m.F])
    s = np.zeros(m.V.shape[0])
    for k in range(3):
        np.add.at(s, m.F[:, k], ang[:, k])
    H, W = points.shape[:2]
    interior = np.zeros((H, W), bool)
    interior[1:-1, 1:-1] = True
    idx = m.index[interior & (m.index >= 0)]
    defect = 2 * np.pi - s[idx]
    A = FL.tri_areas_3d(m.V, m.F).sum()
    return {"sum_angle_defect_rad": float(defect.sum()), "sum_abs_angle_defect_rad": float(np.abs(defect).sum()),
            "mean_abs_angle_defect_deg": float(np.degrees(np.abs(defect)).mean()),
            "area_vox2": float(A), "iso_z_tilt_deg": LM.iso_z_tilt_deg(points)}


def run_abf(patch: np.ndarray, name: str, vox: float, extra: tuple = ()) -> tuple[np.ndarray, dict]:
    d = WORK / "abf" / name
    src = d / "patch.tifxyz"
    outd = d / ("uv" + ("_" + "_".join(extra) if extra else ""))
    T.write_tifxyz(src, T.TifxyzMesh(points=patch.astype(np.float32), scale=(1 / STEP_VOX, 1 / STEP_VOX), uuid=name),
                   overwrite=True, voxel_size_um=vox)
    t = time.time()
    cmd = [str(REPO / "tools/sib/flat1/logrun.sh"), f"abf_{name}" + ("_" + "_".join(extra) if extra else ""),
           str(RUN_ABF), str(src), str(outd), *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = {"exit_code": r.returncode, "seconds": time.time() - t, "stdout_tail": r.stdout[-800:], "args": list(extra)}
    if r.returncode != 0:
        return np.full((*patch.shape[:2], 2), np.nan), info
    u = tifffile.imread(outd / "u.tif").astype(np.float64)
    v = tifffile.imread(outd / "v.tif").astype(np.float64)
    uv = np.stack([u, v], -1)
    uv[(u == -1) | (v == -1)] = np.nan
    info["u_sha256"] = sha256_file(outd / "u.tif")
    info["v_sha256"] = sha256_file(outd / "v.tif")
    return uv, info


def flatten_all(patch: np.ndarray, name: str, vox: float, quads_eval: np.ndarray, *, sensitivity: bool = True) -> dict:
    H, W = patch.shape[:2]
    mesh = FL.grid_to_mesh(patch)
    res = {}

    def rec(key, uv, info, t0):
        info = dict(info)
        info["seconds"] = info.get("seconds", time.time() - t0)
        res[key] = {"metrics": FL.evaluate(patch, uv, quads_eval), "info": info}

    t0 = time.time()
    uv, info = run_abf(patch, name, vox)
    rec("vc_flatten", uv, info, t0)
    UVg = FL.grid_init_uv(mesh, STEP_VOX)
    t0 = time.time()
    UV, info = FL.flatten_slim(mesh.V, mesh.F, UVg)
    info["init"] = "grid"
    rec("slim", FL.uv_to_grid(mesh, UV, (H, W)), info, t0)
    t0 = time.time()
    UV, info = FL.flatten_arap(mesh.V, mesh.F, UVg)
    info["init"] = "grid"
    rec("arap", FL.uv_to_grid(mesh, UV, (H, W)), info, t0)
    rec("grid_baseline", FL.uv_to_grid(mesh, UVg, (H, W)), {"init": "levelled grid, nominal step"}, time.time())
    if sensitivity:
        UVt = FL.tutte_init_uv(mesh)
        t0 = time.time()
        UV, info = FL.flatten_slim(mesh.V, mesh.F, UVt)
        info["init"] = "tutte"
        rec("slim_tutte_init", FL.uv_to_grid(mesh, UV, (H, W)), info, t0)
        t0 = time.time()
        UV, info = FL.flatten_arap(mesh.V, mesh.F, UVt)
        info["init"] = "tutte"
        rec("arap_tutte_init", FL.uv_to_grid(mesh, UV, (H, W)), info, t0)
        t0 = time.time()
        uv, info = run_abf(patch, name, vox, ("50",))
        rec("vc_flatten_50iter", uv, info, t0)
        t0 = time.time()
        uv, info = run_abf(patch, name, vox, ("10", "1"))
        rec("vc_flatten_lscm_only", uv, info, t0)
    return res


def _component(q: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
    from scipy import ndimage

    lab, _ = ndimage.label(q)
    keep = np.unique(lab[seed_mask & q])
    keep = keep[keep > 0]
    return np.isin(lab, keep)


def fallback(lev: np.ndarray, rect: dict, vox: float, r_only_pct: float) -> dict:
    mq = int(math.ceil(MARGIN_MM * 1000.0 / (STEP_VOX * vox)))
    r0, c0, h, w = rect["r0"], rect["c0"], rect["h_quads"], rect["w_quads"]
    R0, C0 = max(r0 - mq, 0), max(c0 - mq, 0)
    R1, C1 = min(r0 + h + mq, lev.shape[0] - 1), min(c0 + w + mq, lev.shape[1] - 1)
    sub = lev[R0:R1 + 1, C0:C1 + 1].astype(np.float64)
    Hq, Wq = sub.shape[0] - 1, sub.shape[1] - 1
    inR = np.zeros((Hq, Wq), bool)
    inR[r0 - R0:r0 - R0 + h, c0 - C0:c0 - C0 + w] = True
    q = _component(FL.quad_mask(sub), inR)
    rounds = []
    for k in range(TRIM_ROUNDS + 1):
        mesh = FL.grid_to_mesh(sub, q)
        UV, info = FL.flatten_slim(mesh.V, mesh.F, FL.grid_init_uv(mesh, STEP_VOX))
        uv = FL.uv_to_grid(mesh, UV, sub.shape[:2])
        mR = FL.evaluate(sub, uv, inR)
        mAll = FL.evaluate(sub, uv, q)
        ok = FL.quad_edge_ok(sub, uv, 0.05, mAll["area_scale_factor"])
        drop = q & ~inR & ~ok
        rounds.append({"round": k, "n_quads": int(q.sum()), "n_margin_quads": int((q & ~inR).sum()),
                       "pct_R_within_5pct": mR["pct_quads_within_5pct"], "pct_all_within_5pct": mAll["pct_quads_within_5pct"],
                       "R_flipped": mR["flipped_triangles"], "slim_iterations": info["iterations"],
                       "n_dropped_next": int(drop.sum()), "metrics_R": mR})
        if k == TRIM_ROUNDS or not drop.any():
            break
        q = _component(q & ~drop, inR)
    return {"margin_quads": mq, "margin_mm_realised": mq * STEP_VOX * vox / 1000.0, "crop_rows_cols": [R0, R1, C0, C1],
            "R_only_slim_pct": r_only_pct, "rounds": rounds,
            "before_pct": rounds[0]["pct_R_within_5pct"], "after_pct": rounds[-1]["pct_R_within_5pct"]}


def flatten_stage(sel: dict) -> list[dict]:
    vox = sel["voxel_um"]
    out = []
    only = sys.argv[3].split(",") if (__name__ == "__main__" and len(sys.argv) > 3) else None
    for ch in sel["chosen"]:
        seg = ch["segment"]
        if only and not any(t in seg for t in only):  # parallel workers on a subset
            continue
        cp = WORK / "results" / f"{seg}.json"
        if cp.exists():
            out.append(json.loads(cp.read_text()))
            continue
        lev = np.load(ch["levelled_npy"])
        r = ch["rect"]
        patch = lev[r["r0"]:r["r0"] + r["h_quads"] + 1, r["c0"]:r["c0"] + r["w_quads"] + 1].astype(np.float64)
        qe = FL.quad_mask(patch)
        res = {"segment": seg, "rect": r, "patch_shape": list(patch.shape[:2]),
               "patch_sha256": hashlib.sha256(np.ascontiguousarray(patch.astype(np.float32)).tobytes()).hexdigest(),
               "geometry": geometry_diagnostics(patch)}
        res["area_cm2_check"] = res["geometry"]["area_vox2"] * (vox * 1e-4) ** 2
        res["methods"] = flatten_all(patch, seg, vox, qe)
        res["fallback"] = fallback(lev, r, vox, res["methods"]["slim"]["metrics"]["pct_quads_within_5pct"])
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(res, indent=1))
        out.append(res)
        print(seg, {k: round(v["metrics"]["pct_quads_within_5pct"], 3) for k, v in res["methods"].items()},
              "fallback", round(res["fallback"]["before_pct"], 3), "->", round(res["fallback"]["after_pct"], 3), flush=True)
    return out


# ---------------------------------------------------------------------------
# stage 3: adoption rule and summary
# ---------------------------------------------------------------------------

def summary(sel: dict, results: list[dict]) -> dict:
    table = {}
    for m in list(results[0]["methods"].keys()):
        table[m] = [float(r["methods"][m]["metrics"]["pct_quads_within_5pct"]) for r in results]
    adopted = None
    for m in METHODS:
        n_pass = sum(p >= ADOPT_PCT for p in table[m])
        if n_pass >= ADOPT_MIN_MESHES:
            adopted = m
            break
    fb = [{"segment": r["segment"], "R_only_slim": float(r["fallback"]["R_only_slim_pct"]),
           "margin_before_trim": float(r["fallback"]["before_pct"]), "after_trim": float(r["fallback"]["after_pct"]),
           "rounds": len(r["fallback"]["rounds"]) - 1} for r in results]
    fb_pass = int(sum(x["after_trim"] >= ADOPT_PCT for x in fb))
    s = {"variant": VARIANT, "rule": f"first of {list(METHODS)} with >= {ADOPT_PCT} % quads within +-5 % on >= {ADOPT_MIN_MESHES} of {N_MESH}",
         "segments": [r["segment"] for r in results],
         "pct_quads_within_5pct": table,
         "n_meshes_passing": {m: int(sum(p >= ADOPT_PCT for p in v)) for m, v in table.items()},
         "adopted": adopted,
         "fallback_needed": adopted is None,
         "fallback": fb, "fallback_n_meshes_passing": fb_pass,
         "fallback_meets_rule": fb_pass >= ADOPT_MIN_MESHES}
    (OUT / f"flat1_summary{SFX}.json").write_text(json.dumps(s, indent=1))
    (OUT / f"flat1_results{SFX}.json").write_text(json.dumps({"selection": {k: v for k, v in sel.items() if k != "downloads"},
                                                        "results": results}, indent=1))
    return s


def main() -> None:
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    OUT.mkdir(parents=True, exist_ok=True)
    sp = OUT / f"selection{SFX}.json"
    if stage in ("select", "all") and not sp.exists():
        select()
    sel = json.loads(sp.read_text())
    if stage == "select":
        print(json.dumps([(c["segment"], c["rect"]) for c in sel["chosen"]], indent=1))
        return
    results = flatten_stage(sel)
    if len(sys.argv) > 3:  # subset worker: no summary
        return
    s = summary(sel, results)
    print(json.dumps({k: s[k] for k in ("pct_quads_within_5pct", "n_meshes_passing", "adopted", "fallback",
                                        "fallback_meets_rule")}, indent=1))


if __name__ == "__main__":
    main()
